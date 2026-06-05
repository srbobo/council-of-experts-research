"""gpt-oss-20B single-shot mode — local MoE alternative to opus-single.

OpenAI's first open-weights release. 20B params total, ~3.6B active per
token (mixture-of-experts), reasoning-tuned, Apache 2.0. Runs via Ollama
in ~14 GB of RAM at Q4_K_M; fits comfortably alongside the Lead's Phi-4
14B on a 32 GB M5 in sequential mode.

The point of this mode is to give the bench harness a *local* comparison
column with frontier-lab provenance (and MoE architecture) instead of
requiring Anthropic API spend. It is NOT a substitute for opus-single —
gpt-oss-20B is a strong open-weights model, but it is not Opus-class
capability. The audit log records what actually ran via the ``backend``
field on each AgentTurn, and the Results UI surfaces gpt-oss in its own
column so no later reader can confuse the two.

The single-shot system prompt is reused verbatim from
``bench/opus_single.py`` — neutral framing, no council-style structural
enforcement (no Tensions block, no per-seat sections). The point is to
measure what a single capable model produces *without* the council
architecture, so the prompt has to be architecture-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from council.cabinet import GPT_OSS_20B
from council.models import chat as local_chat

# Reuse the exact prompt opus-single uses, so the comparison isn't muddled
# by a prompt difference between the two single-shot baselines.
from .opus_single import SINGLE_SHOT_SYSTEM


@dataclass
class GptOssSingleResult:
    """Result of a single gpt-oss-20B call. Mirrors ``OpusSingleResult``
    so the bench runner can persist it identically.
    """

    query: str
    final_output: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    system_prompt: str = ""
    # Full Ollama response payload — kept for parity with the Opus path,
    # though gpt-oss via Ollama doesn't surface structured thinking blocks
    # the way the Anthropic SDK does.
    raw: dict = field(default_factory=dict)


async def run_gptoss_single(query: str) -> GptOssSingleResult:
    """Run a single gpt-oss-20B call on the user's query.

    Local-only — no cost guard, no API spend, no Anthropic SDK. Returns a
    result with the same fields as ``OpusSingleResult`` so the bench
    runner can serialize either uniformly.
    """
    messages = [
        {"role": "system", "content": SINGLE_SHOT_SYSTEM},
        {"role": "user", "content": query},
    ]

    response = await local_chat(GPT_OSS_20B, messages)

    return GptOssSingleResult(
        query=query,
        final_output=response.content,
        latency_ms=response.latency_ms,
        input_tokens=response.prompt_eval_count,
        output_tokens=response.eval_count,
        system_prompt=SINGLE_SHOT_SYSTEM,
        raw=response.raw,
    )
