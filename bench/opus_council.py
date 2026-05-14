"""Opus-as-council mode: Opus plays every seat in the council architecture.

This is where the orchestrator refactor pays off. We import the existing
``council.orchestrator.deliberate`` and inject our Anthropic-backed ``chat``
function via ``chat_fn``. The orchestration logic — step-back planning,
sub-question dispatch, per-seat consultation, tension-extraction synthesis —
is reused 1:1. The only thing that changes is the underlying model.

This isolates the "real fine-tunes vs prompted generalist" question: same
prompts, same architecture, same audit-log shape — only the backend differs.
"""

from __future__ import annotations

from functools import partial

from council.orchestrator import DeliberationResult, deliberate
from council.thermal import ThermalGuard

from .anthropic_client import chat as opus_chat
from .cost_guard import CostGuard


async def run_opus_council(query: str, *, cost_guard: CostGuard) -> DeliberationResult:
    """Run the council orchestrator with Opus playing every seat.

    The chat function is wrapped with ``functools.partial`` to bind the
    cost_guard, so the orchestrator's ``chat_fn(member, messages, ...)``
    invocation reaches an Anthropic call that's been gated for budget.

    Thermal guard is constructed but its inter-agent pause is functionally
    a no-op for cloud calls — the M5's thermal pressure doesn't apply to
    Opus. We keep the construction so the orchestrator's interface is
    consistent and the audit log shape doesn't drift between modes.
    """
    # Bind cost_guard into the chat_fn signature so the orchestrator
    # can call chat_fn(member, messages, *, temperature, max_tokens) without
    # knowing anything about budget enforcement.
    bound_chat = partial(opus_chat, cost_guard=cost_guard)

    thermal = ThermalGuard.from_env()
    return await deliberate(query, thermal=thermal, chat_fn=bound_chat)
