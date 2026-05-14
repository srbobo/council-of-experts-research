"""Anthropic SDK wrapper for the bench harness.

Provides a ``chat()`` function with the same shape as ``council/models.py``'s
Ollama-backed chat, so the council orchestrator can be injected with this
backend (via the ``chat_fn`` parameter on ``deliberate()``) and produce an
``opus-council`` benchmark mode without code duplication.

Key differences from the Ollama side:

- Anthropic uses a separate ``system`` parameter rather than ``role="system"``
  in the messages list. We extract any system-role messages from the input
  and pass them via ``system=`` (wrapped with ``cache_control``).
- Opus 4.7 removes ``temperature``/``top_p``/``top_k`` (returns 400 if sent).
  Our signature still accepts ``temperature`` for orchestrator-injection
  compatibility but silently ignores it on the Anthropic call.
- Adaptive thinking is enabled by default (fairness with the council's
  Phi-4 planning step). ``display="summarized"`` so the audit log can show
  what Opus thought.
- System prompts are cached via ``cache_control: {type: "ephemeral"}``,
  which cuts cost ~90% on repeated calls with the same system prompt across
  the benchmark suite (5 cases × 2 modes = up to 30 calls per sweep).

All calls are gated by ``cost_guard.check()`` BEFORE the SDK opens an HTTP
connection — at $0 budget the call is refused with no spend. Actual cost
is recorded after the call via ``cost_guard.record()``.
"""

from __future__ import annotations

import os
import time
from typing import Any

import anthropic  # Anthropic Python SDK — provides AsyncAnthropic client

from council.cabinet import CabinetMember
from council.models import ChatResponse

from .cost_guard import BudgetExceeded, CallCost, CostGuard


# Hard-coded model — bench mode is explicitly Opus-vs-council, not generic.
# When Anthropic releases a newer Opus, update this constant deliberately.
OPUS_MODEL = "claude-opus-4-7"

# Default output cap. Opus 4.7 uses adaptive thinking; thinking tokens count
# toward output_tokens, so we need headroom above the seat-level prose.
# Streaming would be required above ~16K (SDK timeout); 8K stays safely under.
DEFAULT_MAX_TOKENS = 8192

# Effort level — controls thinking depth and overall token spend.
# "high" balances quality vs cost; "xhigh"/"max" for harder coding/agentic
# work. For our benchmark, "high" matches the council's Phi-4 effort
# reasonably and keeps costs predictable.
DEFAULT_EFFORT = "high"


# Module-level lazy client. Constructing AsyncAnthropic at import time would
# require ANTHROPIC_API_KEY to be set just to import this module, which would
# break local-council use cases that never touch the bench harness.
_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    """Return a lazily-initialized AsyncAnthropic client.

    The SDK reads ``ANTHROPIC_API_KEY`` from the environment at construction.
    Failing here (rather than at import) lets the local-council CLI work
    without an API key.
    """
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


def _split_messages(
    messages: list[dict[str, str]],
) -> tuple[list[dict[str, Any]] | None, list[dict[str, str]]]:
    """Split an OpenAI-style messages list into Anthropic's (system, messages).

    Anthropic uses a separate top-level ``system`` parameter; only user/assistant
    messages go in the ``messages`` list. We wrap each system text as a single
    text block carrying ``cache_control`` so it gets cached across the
    benchmark suite's repeated calls (5 cases × 2 modes — same system prompt
    runs many times).
    """
    system_messages = [m for m in messages if m["role"] == "system"]
    chat_messages = [m for m in messages if m["role"] != "system"]

    if not system_messages:
        return None, chat_messages

    # In our orchestrator there's always exactly one system message per call,
    # but support multiple defensively (Anthropic accepts a list of text blocks).
    system_blocks = [
        {
            "type": "text",
            "text": m["content"],
            # Ephemeral cache (5-minute TTL by default) — long enough for a
            # full benchmark sweep (~30 min wall-clock with sequential cases),
            # short enough to not pin storage indefinitely.
            "cache_control": {"type": "ephemeral"},
        }
        for m in system_messages
    ]
    return system_blocks, chat_messages


async def chat(
    member: CabinetMember,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    cost_guard: CostGuard | None = None,
    on_token=None,  # accepted for orchestrator-injection parity; Opus streaming TBD
) -> ChatResponse:
    """Anthropic-backed chat call shaped like the Ollama-side ``chat()``.

    Parameters
    ----------
    member
        Ignored — Opus plays all seats in bench mode. Kept in the signature
        only so this function is interchangeable with ``council.models.chat``
        when injected as ``chat_fn``.
    messages
        OpenAI-style messages. Any ``role="system"`` entries are extracted
        and sent via Anthropic's ``system`` parameter, with prompt caching.
    temperature
        Ignored — Opus 4.7 removes sampling parameters. Accepted for signature
        compatibility with the Ollama-side chat.
    max_tokens
        Hard output cap. Includes thinking tokens.
    cost_guard
        Required gate. ``check()`` is called before any HTTP request so a $0
        budget refuses cleanly with no spend; ``record()`` is called after the
        response with actual usage. If omitted, a default ``CostGuard()`` is
        constructed, which reads ``BENCH_BUDGET_USD`` from env.

    Returns
    -------
    ChatResponse
        Same shape as the Ollama wrapper. ``raw`` carries the full Anthropic
        response (including thinking blocks) for the audit log.
    """
    if cost_guard is None:
        # Default guard reads BENCH_BUDGET_USD from env. With Sam's $0 directive
        # this refuses any non-zero call — which is the correct behavior.
        cost_guard = CostGuard()

    # ---- Fast-path refuse at $0 budget ----
    # If the cap is already zero or negative, refuse before doing anything that
    # touches the network — including count_tokens. This guarantees that the
    # current Sam-directive setting (BENCH_BUDGET_USD=0) makes ZERO API calls
    # of any kind, not even free ones.
    if cost_guard.cap_usd <= 0:
        raise BudgetExceeded(
            f"BENCH_BUDGET_USD={cost_guard.cap_usd:.2f}; refusing Opus call. "
            "Set BENCH_BUDGET_USD > 0 in .env to enable Opus benchmarking."
        )

    client = _get_client()
    system, chat_messages = _split_messages(messages)

    # ---- Pre-call cost estimate ----
    # Anthropic's count_tokens endpoint gives an exact input-token count
    # before we open the actual generation HTTP call. count_tokens is a free
    # endpoint, so this doesn't itself spend budget.
    count_kwargs: dict[str, Any] = {"model": OPUS_MODEL, "messages": chat_messages}
    if system is not None:
        count_kwargs["system"] = system
    token_count = await client.messages.count_tokens(**count_kwargs)
    estimated_input = token_count.input_tokens

    # Output is unknown until the call completes — assume worst case = max_tokens.
    # This makes the cost guard conservative: refuse at the cap rather than
    # discover post-hoc that a long response pushed us past it.
    projected = CallCost(
        input_tokens=estimated_input,
        cached_input_tokens=0,  # cache hits unknown pre-call; assume worst case
        output_tokens=max_tokens,
    )
    cost_guard.check(projected)  # raises BudgetExceeded if this would exceed cap

    # ---- Make the actual generation call ----
    create_kwargs: dict[str, Any] = {
        "model": OPUS_MODEL,
        "max_tokens": max_tokens,
        "messages": chat_messages,
        # Adaptive thinking — Opus 4.7 only supports adaptive (no budget_tokens).
        # display="summarized" so we can see Opus's reasoning in the audit log.
        "thinking": {"type": "adaptive", "display": "summarized"},
        # Effort knob — controls thinking depth and overall token spend.
        "output_config": {"effort": DEFAULT_EFFORT},
    }
    if system is not None:
        create_kwargs["system"] = system

    start = time.monotonic()
    response = await client.messages.create(**create_kwargs)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    # ---- Map response to our ChatResponse shape ----
    # Concatenate all `text` blocks. `thinking` blocks are kept in `raw` for
    # the audit log but are NOT included in `content` — that matches what the
    # synthesizer-input expects (we don't want Opus's reasoning fed back in
    # as a contribution).
    text_blocks = [b.text for b in response.content if b.type == "text"]
    content_text = "\n".join(text_blocks)

    # Token usage. Anthropic returns three input buckets:
    #   - input_tokens                : uncached, full price ($5/MTok on Opus 4.7)
    #   - cache_creation_input_tokens : tokens written to cache (1.25x = $6.25/MTok)
    #   - cache_read_input_tokens     : tokens served from cache (0.1x = $0.50/MTok)
    # Our CallCost has only two buckets (input_tokens, cached_input_tokens), so
    # we fold cache_creation into the full-price bucket. That under-prices cache
    # writes by 25% — small, and erring on the high side for a budget guard.
    usage = response.usage
    uncached = getattr(usage, "input_tokens", 0) or 0
    cache_writes = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cache_reads = getattr(usage, "cache_read_input_tokens", 0) or 0
    output = getattr(usage, "output_tokens", 0) or 0

    actual = CallCost(
        input_tokens=uncached + cache_writes + cache_reads,  # total billed input
        cached_input_tokens=cache_reads,
        output_tokens=output,
    )
    cost_guard.record(actual)

    # Anthropic responses are Pydantic models — model_dump gives a plain dict
    # for JSON serialization in the audit log.
    raw = response.model_dump()

    return ChatResponse(
        content=content_text,
        latency_ms=elapsed_ms,
        eval_count=output,
        prompt_eval_count=uncached + cache_writes + cache_reads,
        raw=raw,
    )
