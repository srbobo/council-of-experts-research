"""Three-phase deliberation loop.

Phase 1 — Lead plans which industry agents to consult (planner prompt → JSON)
Phase 2 — Each routed agent is consulted in turn (sequential per Q1)
Phase 3 — Lead synthesizes a final answer from the agent outputs

Every step is recorded in a ``DeliberationResult`` and persisted to
``runs/<timestamp>_<id>.json`` so a given input can be replayed and the
output reproduced bit-for-bit when models and prompts are pinned.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from .cabinet import CABINET, LEAD, CabinetMember, SeatRole
from .models import ChatResponse
from .models import chat as _default_chat  # Ollama-backed chat; injectable for benchmark backends
from .prompts import (
    FINANCE_SYSTEM,
    HEALTHCARE_SYSTEM,
    LEAD_DIRECT_ANSWER_SYSTEM,
    LEAD_PLANNER_SYSTEM,
    LEAD_SYNTHESIS_SYSTEM,
    LEGAL_SYSTEM,
)
from .thermal import ThermalGuard


# Chat backend signature. Local council uses Ollama; bench mode injects an Anthropic-backed
# implementation with the same shape so the orchestrator logic (planning, dispatch, synthesis)
# is shared 1:1 across both modes — apples-to-apples comparison on architecture, only the
# underlying model changes.
ChatFn = Callable[..., Awaitable[ChatResponse]]


# Map seats to system prompts. Single source of truth so the Phase 2 loop
# below is just data access, not a chain of if/elif.
SEAT_SYSTEM_PROMPTS: dict[str, str] = {
    "healthcare": HEALTHCARE_SYSTEM,
    "legal": LEGAL_SYSTEM,
    "finance": FINANCE_SYSTEM,
}

# Allowed routes — anything outside this set is silently dropped from the plan
# (defensive: planner sometimes hallucinates extra options).
VALID_SEATS: frozenset[str] = frozenset({"healthcare", "legal", "finance"})

# Phase identifiers used by CabinetBackends routing. Five distinct backends are
# possible per deliberation: planner (Lead's decomposition), each of the three
# specialist seats, and synthesis (Lead's final integration). Splitting planner
# from synthesis lets pathway-3 swap experiments isolate whether the gap is in
# *deciding which questions to ask* vs *combining the seats' answers*.
PHASE_IDS = ("planner", "healthcare", "legal", "finance", "synthesis")


@dataclass
class CabinetBackends:
    """Per-phase backend routing for the council.

    Each of the five phases (planner, three seats, synthesis) can be served by
    an independently chosen ``ChatFn``. The default constructor builds a uniform
    cabinet where every phase uses the same backend — that's how ``local-council``
    and ``opus-council`` both work today. Swap experiments override one phase
    at a time to isolate where capability gaps live.

    ``name`` is a short slug used to tag audit logs and surface the cabinet in
    UI (e.g. ``"local"``, ``"opus"``, ``"swap-legal-opus"``).

    ``backend_tags`` is a phase → human-readable backend label map for the
    audit log so a reader can see exactly which model played which seat.
    """

    planner: ChatFn
    healthcare: ChatFn
    legal: ChatFn
    finance: ChatFn
    synthesis: ChatFn
    name: str = "local"
    backend_tags: dict[str, str] = field(default_factory=dict)

    def for_phase(self, phase_id: str) -> ChatFn:
        """Return the ChatFn registered for ``phase_id``.

        Raises KeyError for unknown phases — the orchestrator only ever asks
        for the five canonical IDs in ``PHASE_IDS``, so a missing key here
        is a programming error worth surfacing loudly.
        """
        return getattr(self, phase_id)

    @classmethod
    def uniform(
        cls,
        chat_fn: ChatFn,
        *,
        name: str = "local",
        tag: str = "",
    ) -> "CabinetBackends":
        """Build a cabinet where every phase uses the same backend.

        This is the backward-compatible path: callers that only pass
        ``chat_fn`` to ``deliberate()`` get a uniform cabinet built from it,
        so ``local-council`` and ``opus-council`` modes work unchanged.
        """
        tag = tag or name
        return cls(
            planner=chat_fn,
            healthcare=chat_fn,
            legal=chat_fn,
            finance=chat_fn,
            synthesis=chat_fn,
            name=name,
            backend_tags={p: tag for p in PHASE_IDS},
        )


@dataclass
class AgentTurn:
    """One agent's contribution to a deliberation."""

    seat: str
    member_name: str                              # human-readable model name from cabinet
    ollama_tag: str                               # exact tag for replay
    input_messages: list[dict[str, str]]          # what we sent
    output_text: str                              # what we got back
    latency_ms: int
    eval_count: int                               # output tokens
    prompt_eval_count: int                        # input tokens
    raw_response: dict[str, Any] = field(default_factory=dict)
    # Which backend actually executed this turn — "ollama" for local, "opus"
    # for the Anthropic-backed wrapper, or any custom tag a swap config sets.
    # Defaulted so historical audit logs deserialized via dataclasses still load.
    backend: str = ""


@dataclass
class DeliberationResult:
    """Full audit trail of a single deliberation."""

    query: str
    started_at: str                               # ISO-8601 UTC
    finished_at: str                              # ISO-8601 UTC
    plan: dict[str, Any]                          # parsed JSON from the planner
    plan_raw: str                                 # raw planner text (for debugging parse failures)
    plan_latency_ms: int
    turns: list[AgentTurn]                        # one entry per consulted industry agent
    synthesis: AgentTurn | None                   # Lead's final synthesis (None if off-topic + direct)
    final_output: str                             # what to show the user
    # Planner system prompt + user query, captured so the UI inspector can
    # surface what scaffolding the planner saw (parity with industry seats,
    # which already carry input_messages on their AgentTurn). Defaulted to
    # empty list so historical runs deserialized without this field still load.
    plan_input_messages: list[dict[str, str]] = field(default_factory=list)
    # Cabinet provenance — short name (e.g. "local", "opus", "swap-legal-opus")
    # plus the per-phase backend tag map. Lets pathway-3 swap analyses tell at
    # a glance which model played which phase. Both default-empty so older
    # audit logs (which lack these fields) round-trip cleanly.
    cabinet_name: str = ""
    cabinet_backends: dict[str, str] = field(default_factory=dict)

    @property
    def total_latency_ms(self) -> int:
        """Sum of all agent latencies (excludes thermal-guard pauses)."""
        synth_ms = self.synthesis.latency_ms if self.synthesis else 0
        return self.plan_latency_ms + sum(t.latency_ms for t in self.turns) + synth_ms

    def to_dict(self) -> dict[str, Any]:
        """Plain-dict form for JSON serialization (audit log)."""
        # Manual asdict so we can include @property values too.
        return {
            **asdict(self),
            "total_latency_ms": self.total_latency_ms,
        }


def _strip_thinking(text: str) -> str:
    """Remove ``<think>...</think>`` reasoning blocks from agent output.

    Qwen3-family models (e.g. our Finance seat) emit chain-of-thought wrapped in
    ``<think>...</think>`` tags. Useful in the audit log; noise for the synthesizer
    — Phi-4 doesn't need to wade through Qwen's reasoning to integrate the answer.
    Applied only when constructing the synthesis input; raw audit entries keep
    the thinking blocks intact for debugging.
    """
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()


def _parse_planner_output(raw_text: str) -> dict[str, Any]:
    """Extract the strict-JSON routing decision from the planner's response.

    Falls back through three defensive parses: pure JSON, fenced ```json``` block,
    then the LAST ``{...}`` span in the text. The "last" span matters now because
    the planner does step-back reasoning before emitting JSON; the first ``{`` may
    be inside the reasoning text. If all fail, returns an empty plan with a
    rationale that records the parse failure for the audit log.
    """
    # Pass 1: straight JSON parse.
    try:
        return json.loads(raw_text.strip())
    except json.JSONDecodeError:
        pass

    # Pass 2: ```json ... ``` fenced code block (model sometimes wraps despite instructions).
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # Pass 3: find the LAST balanced-looking { ... } span. The step-back planner
    # produces reasoning prose first and the JSON last, so we want the trailing block.
    spans = list(re.finditer(r"\{[\s\S]*?\}", raw_text))
    for match in reversed(spans):
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            continue

    # Wider net: greedy from first { to last } in case the JSON contains nested braces
    # that the non-greedy regex above couldn't span.
    first = raw_text.find("{")
    last = raw_text.rfind("}")
    if first != -1 and last != -1 and last > first:
        try:
            return json.loads(raw_text[first : last + 1])
        except json.JSONDecodeError:
            pass

    # All parsers failed — record the failure and route to no agents.
    return {
        "routes": [],
        "sub_questions": {},
        "rationale": f"[parse_failure] could not extract JSON from planner output: "
                     f"{raw_text[:200]!r}",
    }


def _validate_plan(plan: dict[str, Any], original_query: str) -> dict[str, Any]:
    """Sanitize a parsed plan so the orchestrator can rely on it downstream.

    - Drops routes outside ``VALID_SEATS``.
    - Ensures ``sub_questions`` exists, has one entry per route, and falls back to
      the original user query for any route the planner forgot. Falling back is
      important: the run continues, but the audit log records the failure clearly
      so we can spot when the planner is unreliable.
    - Strips routes for which both the planner-supplied sub_question and the
      fallback would be empty.
    """
    routes = [r for r in plan.get("routes", []) if r in VALID_SEATS]
    raw_subs = plan.get("sub_questions") or {}
    sub_questions: dict[str, str] = {}
    for seat in routes:
        sq = raw_subs.get(seat) if isinstance(raw_subs, dict) else None
        if isinstance(sq, str) and sq.strip():
            sub_questions[seat] = sq.strip()
        else:
            # Fallback: the planner failed to dispatch a sub-question for this seat.
            # Use the original user query so the run still produces output, and tag
            # the plan so the audit log shows the fallback occurred.
            sub_questions[seat] = original_query
            plan.setdefault("dispatch_fallbacks", []).append(seat)

    plan["routes"] = routes
    plan["sub_questions"] = sub_questions

    # Recency disclosure: when the planner flags the question as turning on recent
    # guidance / rates / rulings, append a deterministic directive to every dispatched
    # sub-question. The seats already have "flag training-cutoff uncertainty" in their
    # system prompts, but they don't always know to apply it for a given question;
    # putting the directive in the user message position raises its priority.
    requires_recency = bool(plan.get("requires_recency_disclosure", False))
    plan["requires_recency_disclosure"] = requires_recency
    plan["recency_notes"] = (plan.get("recency_notes") or "").strip()
    if requires_recency:
        notes = plan["recency_notes"]
        suffix = (
            "\n\nNote from the Lead: answering this depends on guidance, evidence, "
            "rates, or rulings that may have evolved since your training cutoff. "
            "Explicitly flag training-cutoff uncertainty wherever it applies in your answer."
        )
        if notes:
            suffix += f" Specifically, watch out for: {notes}."
        for seat in plan["routes"]:
            plan["sub_questions"][seat] = plan["sub_questions"][seat] + suffix

    return plan


def _build_turn(
    seat: str,
    member: CabinetMember,
    messages: list[dict[str, str]],
    response: ChatResponse,
    *,
    backend: str = "",
) -> AgentTurn:
    """Bundle a chat call into an AgentTurn for the audit log.

    ``backend`` is the cabinet's tag for which model actually served the call
    (e.g. ``"ollama"`` for the local Phi-4, ``"opus"`` for the Anthropic-backed
    wrapper). Captured here so swap experiments can be read off the audit log
    without re-running anything.
    """
    return AgentTurn(
        seat=seat,
        member_name=member.name,
        ollama_tag=member.ollama_tag,
        input_messages=messages,
        output_text=response.content,
        latency_ms=response.latency_ms,
        eval_count=response.eval_count,
        prompt_eval_count=response.prompt_eval_count,
        raw_response=response.raw,
        backend=backend,
    )


def _now_iso() -> str:
    """Timezone-aware ISO-8601 timestamp for audit logs."""
    return datetime.now(timezone.utc).isoformat()


async def deliberate(
    query: str,
    *,
    thermal: ThermalGuard,
    on_phase: callable | None = None,  # optional progress callback: on_phase(stage, detail)
    chat_fn: ChatFn | None = None,  # uniform backend (back-compat); see also cabinet=
    cabinet: "CabinetBackends | None" = None,  # per-phase routing for swap experiments
    cabinet_members: dict[SeatRole, CabinetMember] | None = None,  # override CABINET dict per-call
    on_token: Callable[[str, str], None] | None = None,  # (phase_tag, delta)
) -> DeliberationResult:
    """Run the 3-phase council on a single user query.

    Sequential mode (per Q1): industry agents are called in series with a
    thermal-aware pause between calls. The Lead is reused for planning AND
    synthesis (Ollama keeps it warm in memory).

    ``on_phase`` is an optional callback for live CLI feedback; the orchestrator
    itself doesn't depend on rich/console output so the bench harness can drive
    it silently.

    ``chat_fn`` is the back-compat single-backend path: all five phases use
    the same chat callable (this is how ``local-council`` and ``opus-council``
    have always worked). Mutually exclusive with ``cabinet=``.

    ``cabinet`` enables per-phase backend routing — used by pathway-3 swap
    experiments to play one seat with a different backend (e.g. local Phi-4
    lead + local Med42 + Opus Legal + local Qwen-Finance). Each of the five
    phases (planner, three seats, synthesis) can be independently assigned.

    ``cabinet_members`` overrides the module-level ``CABINET`` dict, letting
    a caller swap in alternative ``CabinetMember`` records per seat for a
    single deliberation. The bench harness uses this for the
    ``local-council-v2`` mode (Path C of the specialist-upgrade
    investigation) so the upgraded cabinet doesn't bleed into other modes
    sharing the same process.

    ``on_token`` is an optional per-delta callback for live token streaming.
    The orchestrator tags each delta with the phase it came from (one of
    ``"planner"``, ``"healthcare"``, ``"legal"``, ``"finance"``, or
    ``"synthesis"``) so the consumer (typically the web server) can route
    deltas to per-phase live buffers. The chat backend must support an
    ``on_token`` kwarg — the local Ollama wrapper does; the Anthropic
    wrapper currently accepts and ignores it (streaming for Opus lands
    in a follow-up change).
    """
    # Resolve the cabinet. Precedence: explicit cabinet > chat_fn (wrapped into
    # uniform) > local default. Once resolved, every per-phase chat call goes
    # through cabinet.for_phase(...), so the rest of the body doesn't care
    # whether one model or five are in play.
    if cabinet is not None and chat_fn is not None:
        raise ValueError(
            "deliberate(): pass either chat_fn= (uniform backend) or cabinet= "
            "(per-phase routing), not both."
        )
    if cabinet is None:
        backend_fn = chat_fn if chat_fn is not None else _default_chat
        # Tag inference: a custom chat_fn coming from bench (Opus) won't be the
        # default; everything else is local Ollama. The bench harness sets a
        # better tag explicitly via cabinet=, so this inference only matters
        # for the chat_fn= back-compat path.
        inferred_tag = "ollama" if backend_fn is _default_chat else "custom"
        cabinet = CabinetBackends.uniform(backend_fn, name=inferred_tag, tag=inferred_tag)

    # Helper to bind a phase tag onto the user's on_token callback. Returns
    # None when no live-token consumer was supplied so the chat backend can
    # take its non-streaming fast path.
    def _phase_token_cb(phase_tag: str):
        if on_token is None:
            return None
        return lambda delta: on_token(phase_tag, delta)

    started_at = _now_iso()

    # -------------------------------------------------------------------------
    # Phase 1: Lead plans which industry agents to consult.
    # -------------------------------------------------------------------------
    if on_phase:
        on_phase("plan", "Lead planning routes...")
    planner_messages = [
        {"role": "system", "content": LEAD_PLANNER_SYSTEM},
        {"role": "user", "content": query},
    ]
    # Temperature 0.0 here — we want deterministic JSON, not creative routing.
    # max_tokens raised to 1024 because the planner now produces step-back reasoning
    # plus a multi-field JSON (core_question + sub_questions per route).
    planner_response = await cabinet.for_phase("planner")(
        LEAD, planner_messages,
        temperature=0.0, max_tokens=1024,
        on_token=_phase_token_cb("planner"),
    )
    plan = _parse_planner_output(planner_response.content)
    plan = _validate_plan(plan, original_query=query)
    routes = plan["routes"]

    if on_phase:
        if routes:
            recency_tag = " [recency-sensitive]" if plan.get("requires_recency_disclosure") else ""
            on_phase("plan_done", f"Routes: {', '.join(routes)}{recency_tag}")
            if plan.get("requires_recency_disclosure") and plan.get("recency_notes"):
                on_phase("dispatch", f"recency notes: {plan['recency_notes']}")
            for seat in routes:
                # Show only the original sub-question text in the CLI (strip the recency
                # suffix the orchestrator just appended); the audit log captures the full
                # augmented question via input_messages.
                shown = plan["sub_questions"][seat].split("\n\nNote from the Lead:", 1)[0]
                on_phase("dispatch", f"{seat}: {shown}")
        else:
            on_phase("plan_done", "No specialist consultation needed")

    # -------------------------------------------------------------------------
    # Phase 2: Consult each routed industry agent in turn (sequential).
    # -------------------------------------------------------------------------
    # Use the caller's cabinet override if provided (Path C v2 cabinet); fall
    # back to the module-level CABINET. The override is per-call so multiple
    # modes can share this orchestrator without their cabinets mutating
    # each other.
    members_map = cabinet_members if cabinet_members is not None else CABINET
    turns: list[AgentTurn] = []
    for i, seat in enumerate(routes):
        if i > 0:
            # Thermal-aware pause between consultations (skips before the first one).
            if on_phase:
                on_phase("pause", f"Thermal pause ({thermal.base_pause_seconds}s)")
            await thermal.between_agents()

        member = members_map[seat]
        if on_phase:
            on_phase("consult", f"Consulting {seat} ({member.name})")

        # Phase 2 now sends the Lead-DISPATCHED sub-question, NOT the original user
        # query. This is the architectural fix for the lane-bleed problem: each seat
        # only sees a focused, in-domain question, so it has nothing to drift toward.
        # The fallback to original query is handled in _validate_plan above.
        seat_query = plan["sub_questions"][seat]

        agent_messages = [
            {"role": "system", "content": SEAT_SYSTEM_PROMPTS[seat]},
            {"role": "user", "content": seat_query},
        ]
        # Stream this seat's output tokens tagged with the seat name so the
        # frontend can route them to the right live buffer.
        agent_response = await cabinet.for_phase(seat)(
            member, agent_messages,
            temperature=0.2,
            on_token=_phase_token_cb(seat),
        )
        turns.append(_build_turn(
            seat, member, agent_messages, agent_response,
            backend=cabinet.backend_tags.get(seat, ""),
        ))

    # -------------------------------------------------------------------------
    # Phase 3: Lead synthesizes (or answers directly if no routes).
    # -------------------------------------------------------------------------
    if on_phase:
        on_phase("synthesize", "Lead synthesizing final answer...")

    if routes:
        # Build the synthesis input: original question + each contribution clearly demarcated.
        # The Lead is told (in LEAD_SYNTHESIS_SYSTEM) to integrate, surface tensions, and
        # preserve caveats; the seats are clearly labeled so it can attribute when useful.
        sections = [f"USER QUESTION:\n{query}\n"]
        for turn in turns:
            # Strip <think>...</think> blocks (Qwen-family CoT) before passing
            # to the synthesizer; audit log retains the raw output via turn.output_text.
            cleaned = _strip_thinking(turn.output_text)
            sections.append(f"---\n{turn.seat.upper()} CONTRIBUTION:\n{cleaned}\n")
        synthesis_user = "\n".join(sections)
        synthesis_system = LEAD_SYNTHESIS_SYSTEM
    else:
        # Off-topic path: Lead answers directly without consultation.
        synthesis_user = query
        synthesis_system = LEAD_DIRECT_ANSWER_SYSTEM

    synthesis_messages = [
        {"role": "system", "content": synthesis_system},
        {"role": "user", "content": synthesis_user},
    ]
    synthesis_response = await cabinet.for_phase("synthesis")(
        LEAD, synthesis_messages,
        temperature=0.2,
        on_token=_phase_token_cb("synthesis"),
    )
    synthesis_turn = _build_turn(
        "lead", LEAD, synthesis_messages, synthesis_response,
        backend=cabinet.backend_tags.get("synthesis", ""),
    )

    finished_at = _now_iso()

    return DeliberationResult(
        query=query,
        started_at=started_at,
        finished_at=finished_at,
        plan=plan,
        plan_raw=planner_response.content,
        plan_latency_ms=planner_response.latency_ms,
        turns=turns,
        synthesis=synthesis_turn,
        final_output=synthesis_response.content,
        plan_input_messages=planner_messages,
        cabinet_name=cabinet.name,
        cabinet_backends=dict(cabinet.backend_tags),
    )


def save_audit_log(result: DeliberationResult, *, run_id: str, runs_dir: Path | None = None) -> Path:
    """Persist a DeliberationResult to ``runs/<timestamp>_<run_id>.json``.

    Returns the path written. Caller picks ``run_id`` (typically a case-id or
    a slug derived from the prompt). Timestamp prefix gives chronological sort.
    """
    runs_dir = runs_dir or Path("runs")
    runs_dir.mkdir(parents=True, exist_ok=True)
    # YYYYMMDDTHHMMSS — sorts lexically and is filesystem-safe everywhere.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = runs_dir / f"{stamp}_{run_id}.json"
    with path.open("w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)
    return path
