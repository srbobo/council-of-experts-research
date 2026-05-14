"""Single-shot Opus 4.7 mode: one prompt in, one response out.

Tests "raw frontier vs whole council" — Opus answers the user's query directly
without any of the council's planning / per-seat / synthesis structure. This
is the upper bound on "what would happen if you skipped the council entirely
and just asked the best generalist model."

The system prompt is intentionally minimal — we're testing what frontier
Opus does on its own, not what Opus does when prompted to act like a council.
That's what ``opus_council`` mode is for.

Run via the bench CLI; this module is not directly executed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .anthropic_client import chat
from .cost_guard import CostGuard

# A neutral frame — establishes that the model is acting as a thoughtful
# advisor on multi-domain business questions, but does NOT impose council-style
# structure (no tensions block, no per-seat sections). The council's
# tension-extraction synthesis prompt is reused only in `opus_council` mode.
SINGLE_SHOT_SYSTEM = """\
You are a thoughtful, careful advisor on complex business questions that span \
clinical, legal, and financial dimensions. Answer the user's question directly \
and substantively, drawing on whatever expertise the question requires.

When numbers, dates, regulations, or jurisdictional details might have evolved \
since your training cutoff, flag that uncertainty explicitly. When you state \
a specific number that is a modeled assumption rather than a fact, label it \
as such.
"""


@dataclass
class OpusSingleResult:
    """Result of a single-shot Opus call. Mirrors the orchestrator's structure
    so the bench runner can persist it the same way as a council deliberation.
    """

    query: str
    final_output: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    # System prompt sent to Opus — surfaced in the UI's inspector panel so
    # the user can see exactly what scaffolding the call carried.
    system_prompt: str = ""
    # Full Anthropic response payload (Pydantic model_dump'd to a dict).
    # Contains structured thinking blocks under raw["content"] when adaptive
    # thinking is enabled. The UI surfaces these in the inspector.
    raw: dict = field(default_factory=dict)


async def run_opus_single(query: str, *, cost_guard: CostGuard) -> OpusSingleResult:
    """Run a single Opus call on the user's query.

    Pre-condition: ``cost_guard.check()`` will be invoked inside ``chat()``
    before any network call; a $0 budget refuses cleanly with no spend.
    """
    # The Anthropic chat() expects OpenAI-style messages with the system
    # message included; it splits them internally for Anthropic's API shape.
    messages = [
        {"role": "system", "content": SINGLE_SHOT_SYSTEM},
        {"role": "user", "content": query},
    ]

    # `member` is ignored in opus mode — Opus plays whatever seat we name.
    # Pass a placeholder; the chat function doesn't use it.
    from council.cabinet import LEAD  # local import to avoid circular concerns

    response = await chat(LEAD, messages, cost_guard=cost_guard)

    return OpusSingleResult(
        query=query,
        final_output=response.content,
        latency_ms=response.latency_ms,
        input_tokens=response.prompt_eval_count,
        output_tokens=response.eval_count,
        system_prompt=SINGLE_SHOT_SYSTEM,
        raw=response.raw,
    )
