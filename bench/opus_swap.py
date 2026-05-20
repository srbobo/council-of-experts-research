"""Specialist-swap experiments: hybrid cabinets with one phase served by Opus.

Pathway-3 of the improvement roadmap. The local council loses to both Opus
modes — but where does the gap actually live? Is it the planner's
decomposition? One specific specialist seat? The synthesis step? Or is the
gap diffuse across every phase?

This module answers that question by running controlled ablations: a
hybrid cabinet where *one phase* is replaced with Opus while the other
four remain local. If swapping the Legal seat (and only the Legal seat)
closes most of the gap on the cross-border DTx case, that's strong
evidence the bottleneck is Saul's training corpus, not the architecture.

Five standard swap variants are defined here:

- ``swap-planner-opus``   — Opus plans, local seats execute, Phi-4 synthesizes
- ``swap-healthcare-opus`` — Opus plays Healthcare; everyone else local
- ``swap-legal-opus``     — Opus plays Legal; everyone else local
- ``swap-finance-opus``   — Opus plays Finance; everyone else local
- ``swap-synthesis-opus`` — Local seats, Opus synthesizes

Each variant uses exactly one Opus call per deliberation (the swapped
phase), so cost is bounded and predictable. The cost guard sees the same
gating regardless of which phase the Opus call serves.
"""

from __future__ import annotations

from functools import partial

from council.models import chat as local_chat
from council.orchestrator import (
    PHASE_IDS,
    CabinetBackends,
    DeliberationResult,
    deliberate,
)
from council.thermal import ThermalGuard

from .anthropic_client import chat as opus_chat
from .cost_guard import CostGuard


# Tag strings recorded in the audit log per phase. Kept short so per-turn
# `backend` fields read cleanly when displayed in the UI.
LOCAL_TAG = "ollama"
OPUS_TAG = "opus"


# The five canonical swap variants. Variant name is also the bench mode
# string and the audit-log slug, so a single source of truth.
SWAP_VARIANTS: dict[str, str] = {
    "swap-planner-opus": "planner",
    "swap-healthcare-opus": "healthcare",
    "swap-legal-opus": "legal",
    "swap-finance-opus": "finance",
    "swap-synthesis-opus": "synthesis",
}


def is_swap_mode(mode: str) -> bool:
    """Return True iff ``mode`` is one of the standard swap variants."""
    return mode in SWAP_VARIANTS


def list_swap_modes() -> list[str]:
    """Return the standard swap mode names in canonical order."""
    return list(SWAP_VARIANTS.keys())


def make_swap_cabinet(
    swapped_phase: str,
    *,
    cost_guard: CostGuard,
) -> CabinetBackends:
    """Build a ``CabinetBackends`` where ``swapped_phase`` uses Opus and the
    other four phases use local Ollama.

    The Opus chat callable is bound with ``cost_guard`` via ``functools.partial``
    so the orchestrator's per-phase invocation gets cost gating for free —
    same mechanism opus-council uses.
    """
    if swapped_phase not in PHASE_IDS:
        raise ValueError(
            f"swapped_phase={swapped_phase!r} is not a valid phase. "
            f"Allowed: {list(PHASE_IDS)}"
        )

    # Bind the cost guard once so each Opus call gets it without the
    # orchestrator having to know anything about budget enforcement.
    opus_bound = partial(opus_chat, cost_guard=cost_guard)

    # Start with every phase using local Ollama, then override the one
    # phase that gets the Opus treatment. Tags follow the same pattern so
    # the audit log can be read at a glance.
    phase_to_fn = {p: local_chat for p in PHASE_IDS}
    phase_to_tag = {p: LOCAL_TAG for p in PHASE_IDS}
    phase_to_fn[swapped_phase] = opus_bound
    phase_to_tag[swapped_phase] = OPUS_TAG

    return CabinetBackends(
        planner=phase_to_fn["planner"],
        healthcare=phase_to_fn["healthcare"],
        legal=phase_to_fn["legal"],
        finance=phase_to_fn["finance"],
        synthesis=phase_to_fn["synthesis"],
        name=f"swap-{swapped_phase}-opus",
        backend_tags=phase_to_tag,
    )


async def run_swap(
    mode: str,
    query: str,
    *,
    cost_guard: CostGuard,
) -> DeliberationResult:
    """Run the council with one phase swapped to Opus and the rest local.

    ``mode`` must be one of the standard ``swap-<phase>-opus`` names; this
    function looks up the swapped phase and dispatches through
    ``make_swap_cabinet``.

    Thermal guard is constructed so the four local Ollama calls still get
    the inter-agent pause they need on an M5 (the single Opus call
    contributes negligibly to thermal load, so the standard pause cadence
    is preserved).
    """
    if mode not in SWAP_VARIANTS:
        raise ValueError(
            f"Unknown swap mode {mode!r}. Allowed: {list(SWAP_VARIANTS.keys())}"
        )
    swapped_phase = SWAP_VARIANTS[mode]
    cabinet = make_swap_cabinet(swapped_phase, cost_guard=cost_guard)
    thermal = ThermalGuard.from_env()
    return await deliberate(query, thermal=thermal, cabinet=cabinet)
