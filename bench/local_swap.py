"""Local-only swap variants — validate the swap-matrix plumbing without spending Opus $.

The Opus swap matrix in ``bench/opus_swap.py`` is the headline pathway-3
experiment: replace one phase with frontier capability and watch the gap
collapse (or not). But running it requires lifting ``BENCH_BUDGET_USD``
from the default $0, which we hold deliberately. Before spending a
single Opus call, we want to confirm the end-to-end plumbing works:

  - Orchestrator routes per-phase via ``CabinetBackends``
  - Audit log captures ``cabinet_backends`` and per-turn ``backend`` tags
  - Results UI surfaces swap columns with the right badge / inspector data
  - Cost guard isn't accidentally tripped (we're not calling Opus)

This module provides three local-only swap variants. Each picks one
specialist seat (Healthcare, Legal, Finance) and serves it with the
Lead's Phi-4 14B model instead of the seat's normal fine-tune. Phi-4 is
already warm in Ollama for every run (it plays planner + synthesis), so
there's no model-download cost and the marginal load is one extra
inference per run.

Why Phi-4 specifically as the swap target:

  - Already loaded — no `ollama pull`, no disk hit
  - Honest framing — the audit log says ``ollama:phi4:14b`` for the
    swapped phase, so a reader sees what actually ran
  - NOT an Opus stand-in. The interpretive value of the Opus swap matrix
    lives in the frontier-vs-local capability delta; substituting a 14B
    local model for Opus would collapse that comparison and create a
    category mistake. These three modes are explicitly labeled as
    ``swap-<phase>-phi4`` (not ``-opus``) so no audit-log reader can
    confuse them.

The natural follow-up experiment IS interesting on its own, separately
from the plumbing-validation purpose: does swapping in a generic 14B
generalist for an 8B specialist seat help, hurt, or wash? That's a
genuinely useful ablation, but a small one — the headline experiment
remains the Opus swap matrix.
"""

from __future__ import annotations

from council.cabinet import LEAD, CabinetMember
from council.models import chat as local_chat
from council.orchestrator import (
    PHASE_IDS,
    CabinetBackends,
    ChatFn,
    DeliberationResult,
    deliberate,
)
from council.thermal import ThermalGuard


# Tag strings recorded in the audit log per phase. Kept short so per-turn
# `backend` fields read cleanly when displayed in the UI. The swap tag
# includes the ollama tag so a reader can identify the actual model that
# served the swapped phase without cross-referencing the cabinet.
DEFAULT_TAG = "ollama"


def _make_swap_chat(swap_member: CabinetMember) -> ChatFn:
    """Wrap ``local_chat`` so it routes to ``swap_member`` regardless of
    what CabinetMember the orchestrator passes in.

    The orchestrator's Phase 2 loop calls the chat fn with the *seat's*
    CabinetMember (e.g. HEALTHCARE / Med42). We need to override that
    routing so the actual inference happens against the swap member
    instead — but the seat's role (system prompt, sub-question) stays
    intact, since those are constructed upstream from the seat's identity.

    The result: the AgentTurn carries seat=healthcare and
    member_name="Med42" (the assigned role), and backend tag
    "ollama:phi4:14b" (what actually ran). The split is intentional —
    it lets the audit log express the experimental condition correctly.
    """
    async def swap_chat(_seat_member, messages, **kwargs):
        # Ignore the seat's member; route to the swap target. Pass through
        # all other kwargs (temperature, max_tokens, on_token) untouched.
        return await local_chat(swap_member, messages, **kwargs)
    return swap_chat


# The local-swap variants. Synthesis and planner are already served by
# Phi-4 in the local-council baseline (since LEAD plays both phases), so
# a "swap-synthesis-phi4" or "swap-planner-phi4" would be a no-op.
#
# swap-healthcare-phi4 was removed on user request after the plumbing
# validation run on case 4 confirmed CabinetBackends routing works end-
# to-end (commit 5a3c0dd → removed in a later commit). The two remaining
# variants stay as optional generalist-vs-specialist ablation probes for
# the legal and finance seats.
SWAP_VARIANTS: dict[str, str] = {
    "swap-legal-phi4": "legal",
    "swap-finance-phi4": "finance",
}


def is_local_swap_mode(mode: str) -> bool:
    """Return True iff ``mode`` is one of the local-only swap variants."""
    return mode in SWAP_VARIANTS


def list_local_swap_modes() -> list[str]:
    """Return the local-only swap mode names in canonical order."""
    return list(SWAP_VARIANTS.keys())


def make_local_swap_cabinet(
    swapped_phase: str,
    *,
    swap_member: CabinetMember = LEAD,
) -> CabinetBackends:
    """Build a ``CabinetBackends`` where ``swapped_phase`` is served by
    ``swap_member`` and every other phase uses its default Ollama backend.

    Defaults ``swap_member`` to ``LEAD`` (Phi-4 14B) because it's already
    loaded for the planner and synthesis phases — zero marginal cost,
    no model downloads, no new infra. Other members can be passed if you
    want to extend the experiment to a different local generalist (e.g.
    a generic Llama 3.1 8B Instruct, once pulled).
    """
    if swapped_phase not in PHASE_IDS:
        raise ValueError(
            f"swapped_phase={swapped_phase!r} is not a valid phase. "
            f"Allowed: {list(PHASE_IDS)}"
        )

    swap_chat = _make_swap_chat(swap_member)

    # Phase routing: every phase uses the default local chat (which reads
    # the model tag from the seat's CabinetMember at call time), EXCEPT
    # the swapped phase, which uses the override that pins the model to
    # `swap_member`. Tags follow the same shape so the audit log can be
    # read at a glance.
    phase_to_fn = {p: local_chat for p in PHASE_IDS}
    phase_to_tag = {p: DEFAULT_TAG for p in PHASE_IDS}
    phase_to_fn[swapped_phase] = swap_chat
    phase_to_tag[swapped_phase] = f"ollama:{swap_member.ollama_tag}"

    return CabinetBackends(
        planner=phase_to_fn["planner"],
        healthcare=phase_to_fn["healthcare"],
        legal=phase_to_fn["legal"],
        finance=phase_to_fn["finance"],
        synthesis=phase_to_fn["synthesis"],
        name=f"swap-{swapped_phase}-phi4",
        backend_tags=phase_to_tag,
    )


async def run_local_swap(
    mode: str,
    query: str,
) -> DeliberationResult:
    """Run the council with one specialist seat served by Phi-4 instead
    of its assigned fine-tune.

    Local-only — no cost guard, no Anthropic SDK, no network beyond the
    local Ollama daemon. Returns the same ``DeliberationResult`` shape as
    every other mode so the bench runner / Results UI / audit log all
    work unchanged.
    """
    if mode not in SWAP_VARIANTS:
        raise ValueError(
            f"Unknown local-swap mode {mode!r}. "
            f"Allowed: {list(SWAP_VARIANTS.keys())}"
        )
    swapped_phase = SWAP_VARIANTS[mode]
    cabinet = make_local_swap_cabinet(swapped_phase)
    thermal = ThermalGuard.from_env()
    return await deliberate(query, thermal=thermal, cabinet=cabinet)
