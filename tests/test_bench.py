"""Tests for the bench harness with mocked Anthropic responses.

Why mocked: at $0 budget the harness refuses any real call. To prove the
"happy path" works (response mapping, cost-guard recording, orchestrator
integration through opus_council), we have to simulate the Anthropic
response shape and inject it. That's what these tests do.

The mocks reproduce the SDK's real response shape — content blocks of type
"thinking" + "text", a usage object with the four token buckets, and the
.model_dump() method orchestrator code calls. If the SDK changes shape, these
tests break loudly, which is the right signal.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bench.anthropic_client import chat
from bench.cost_guard import BudgetExceeded, CallCost, CostGuard
from council.cabinet import LEAD


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


def _make_mock_response(
    text: str = "Hello world",
    thinking: str = "Let me think...",
    input_tokens: int = 100,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
    output_tokens: int = 50,
):
    """Build an object that quacks like ``anthropic.types.Message``.

    Mirrors only the fields ``bench/anthropic_client.py`` reads:
    ``content`` (list of blocks with ``.type``), ``usage`` (with the four
    token bucket fields), and ``model_dump()``.
    """
    thinking_block = SimpleNamespace(type="thinking", thinking=thinking)
    text_block = SimpleNamespace(type="text", text=text)

    usage = SimpleNamespace(
        input_tokens=input_tokens,
        cache_creation_input_tokens=cache_creation_tokens,
        cache_read_input_tokens=cache_read_tokens,
        output_tokens=output_tokens,
    )

    response = MagicMock()
    response.content = [thinking_block, text_block]
    response.usage = usage
    response.model_dump = MagicMock(return_value={"mocked": True, "text": text})
    return response


def _make_mock_token_count(input_tokens: int = 100):
    """Mimic the response of ``client.messages.count_tokens``."""
    return SimpleNamespace(input_tokens=input_tokens)


@pytest.fixture
def temp_cost_guard(tmp_path, monkeypatch):
    """A CostGuard with a generous budget and a temp-dir ledger.

    Generous budget so the test exercises the happy path; temp ledger so
    tests don't pollute the real ``bench/runs/cost.json``.
    """
    monkeypatch.setenv("BENCH_BUDGET_USD", "100.00")  # plenty of headroom
    return CostGuard(ledger_path=tmp_path / "cost.json")


# -----------------------------------------------------------------------------
# Cost guard fast-path
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_zero_budget_refuses_without_network(monkeypatch):
    """At $0 budget, chat() must raise before any client method is called."""
    monkeypatch.setenv("BENCH_BUDGET_USD", "0")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    # Patch the lazy client constructor — if it's ever invoked, the test fails
    # because the fast-path didn't fire.
    with patch("bench.anthropic_client._get_client") as mock_get:
        with pytest.raises(BudgetExceeded):
            await chat(
                LEAD,
                [{"role": "user", "content": "hi"}],
                cost_guard=CostGuard(),
            )
        mock_get.assert_not_called()


# -----------------------------------------------------------------------------
# Happy-path response mapping
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_maps_response_correctly(temp_cost_guard):
    """Verify ChatResponse fields land where they should from a mocked Opus call."""
    mock_client = MagicMock()
    mock_client.messages.count_tokens = AsyncMock(return_value=_make_mock_token_count(120))
    mock_client.messages.create = AsyncMock(
        return_value=_make_mock_response(
            text="The answer is 42.",
            input_tokens=120,
            cache_creation_tokens=10,
            cache_read_tokens=30,
            output_tokens=80,
        )
    )

    with patch("bench.anthropic_client._get_client", return_value=mock_client):
        response = await chat(
            LEAD,
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the meaning of life?"},
            ],
            cost_guard=temp_cost_guard,
        )

    # Content extracted from the text block; thinking block excluded.
    assert response.content == "The answer is 42."
    # eval_count = output_tokens
    assert response.eval_count == 80
    # prompt_eval_count = total input billed = uncached + cache_writes + cache_reads
    assert response.prompt_eval_count == 120 + 10 + 30
    # raw payload preserved for the audit log
    assert response.raw == {"mocked": True, "text": "The answer is 42."}


@pytest.mark.asyncio
async def test_chat_records_cost_after_call(temp_cost_guard):
    """The CostGuard ledger should reflect the real call's tokens after chat()."""
    mock_client = MagicMock()
    mock_client.messages.count_tokens = AsyncMock(return_value=_make_mock_token_count(1000))
    mock_client.messages.create = AsyncMock(
        return_value=_make_mock_response(
            input_tokens=1000,
            cache_creation_tokens=0,
            cache_read_tokens=0,
            output_tokens=500,
        )
    )

    spent_before = temp_cost_guard.spent_usd

    with patch("bench.anthropic_client._get_client", return_value=mock_client):
        await chat(
            LEAD,
            [{"role": "user", "content": "hi"}],
            cost_guard=temp_cost_guard,
        )

    # Expected billed cost on Opus 4.7 ($5/MTok input, $25/MTok output):
    # 1000 input × $5/1M + 500 output × $25/1M = $0.005 + $0.0125 = $0.0175
    expected_delta = 1000 / 1_000_000 * 5.00 + 500 / 1_000_000 * 25.00
    actual_delta = temp_cost_guard.spent_usd - spent_before
    assert abs(actual_delta - expected_delta) < 1e-9, (
        f"Expected delta {expected_delta:.6f}, got {actual_delta:.6f}"
    )


@pytest.mark.asyncio
async def test_system_message_extracted_with_cache_control(temp_cost_guard):
    """The system message should be passed via Anthropic's `system` parameter
    (not in messages list) and carry cache_control."""
    mock_client = MagicMock()
    mock_client.messages.count_tokens = AsyncMock(return_value=_make_mock_token_count(50))
    mock_client.messages.create = AsyncMock(return_value=_make_mock_response())

    system_text = "You are a healthcare expert."
    with patch("bench.anthropic_client._get_client", return_value=mock_client):
        await chat(
            LEAD,
            [
                {"role": "system", "content": system_text},
                {"role": "user", "content": "What's a good differential?"},
            ],
            cost_guard=temp_cost_guard,
        )

    # Inspect the kwargs passed to messages.create
    create_kwargs = mock_client.messages.create.call_args.kwargs

    # System should be a list of text blocks, NOT a string in messages
    assert "system" in create_kwargs
    system_blocks = create_kwargs["system"]
    assert isinstance(system_blocks, list)
    assert len(system_blocks) == 1
    assert system_blocks[0]["type"] == "text"
    assert system_blocks[0]["text"] == system_text
    # The crucial bit: cache_control on every system block
    assert system_blocks[0]["cache_control"] == {"type": "ephemeral"}

    # Messages list should NOT contain the system message
    messages = create_kwargs["messages"]
    assert all(m["role"] != "system" for m in messages)
    assert messages == [{"role": "user", "content": "What's a good differential?"}]


@pytest.mark.asyncio
async def test_opus47_breaking_changes_respected(temp_cost_guard):
    """The call must use adaptive thinking + effort + must NOT pass temperature."""
    mock_client = MagicMock()
    mock_client.messages.count_tokens = AsyncMock(return_value=_make_mock_token_count(50))
    mock_client.messages.create = AsyncMock(return_value=_make_mock_response())

    with patch("bench.anthropic_client._get_client", return_value=mock_client):
        await chat(
            LEAD,
            [{"role": "user", "content": "hi"}],
            temperature=0.7,  # explicitly set; should be ignored by the wrapper
            cost_guard=temp_cost_guard,
        )

    create_kwargs = mock_client.messages.create.call_args.kwargs

    # Adaptive thinking, with summarized display so audit logs see reasoning
    assert create_kwargs["thinking"] == {"type": "adaptive", "display": "summarized"}
    # Effort knob inside output_config (Opus 4.7 shape, not top-level)
    assert create_kwargs["output_config"] == {"effort": "high"}
    # Sampling parameters MUST NOT be present (Opus 4.7 returns 400 if sent)
    assert "temperature" not in create_kwargs
    assert "top_p" not in create_kwargs
    assert "top_k" not in create_kwargs
    # Model is hardcoded to Opus 4.7
    assert create_kwargs["model"] == "claude-opus-4-7"


@pytest.mark.asyncio
async def test_budget_exceeded_blocks_call(temp_cost_guard, monkeypatch):
    """A pre-call estimate that would exceed the cap must abort before create."""
    # Set a tiny budget — even one call will exceed it
    monkeypatch.setenv("BENCH_BUDGET_USD", "0.001")
    tight_guard = CostGuard(ledger_path=temp_cost_guard.ledger_path)

    mock_client = MagicMock()
    # 100K input tokens × $5/1M = $0.50 — way over $0.001
    mock_client.messages.count_tokens = AsyncMock(return_value=_make_mock_token_count(100_000))
    mock_client.messages.create = AsyncMock(return_value=_make_mock_response())

    with patch("bench.anthropic_client._get_client", return_value=mock_client):
        with pytest.raises(BudgetExceeded):
            await chat(
                LEAD,
                [{"role": "user", "content": "hi"}],
                cost_guard=tight_guard,
            )

    # The actual generation must NOT have been called
    mock_client.messages.create.assert_not_called()
    # count_tokens IS called (it's how we estimated), but it's free
    mock_client.messages.count_tokens.assert_called_once()
