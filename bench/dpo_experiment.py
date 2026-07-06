"""Bench modes for the DPO + prompt-transfer experiment.

See RUNBOOK_DPO_PROMPT_TRANSFER.md for the full pre-registered design.
Four modes live here (arm A is the existing ``local-council`` data):

  - ``local-council-repro``  (A') — v1 cabinet with Saul re-converted
        through our own pipeline. Conversion control.
  - ``gptoss-single-spec``   (B1) — gpt-oss-20B single-shot with the
        behavior-spec addendum appended to the neutral system prompt.
  - ``local-council-spec``   (B2) — v1 cabinet; the addendum appended to
        the LEGAL seat's system prompt only. Clean prompting-vs-weights
        pairing with arm C.
  - ``local-council-dpo``    (C)  — v1 cabinet with the LoRA-DPO'd Saul
        (``saul-dpo:coe``; exists after Phase 3).

All local-only: no cost guard, no API spend.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from council.cabinet import CABINET_DPO, CABINET_REPRO, GPT_OSS_20B
from council.models import chat as local_chat
from council.orchestrator import DeliberationResult, deliberate
from council.prompts import BEHAVIOR_SPEC_ADDENDUM, LEGAL_SYSTEM
from council.thermal import ThermalGuard

from .opus_single import SINGLE_SHOT_SYSTEM


# Arm B prompts — composed once at import so every run sees identical bytes.
SINGLE_SHOT_SPEC_SYSTEM = SINGLE_SHOT_SYSTEM + BEHAVIOR_SPEC_ADDENDUM
LEGAL_SPEC_SYSTEM = LEGAL_SYSTEM + BEHAVIOR_SPEC_ADDENDUM


@dataclass
class GptOssSpecResult:
    """Mirrors GptOssSingleResult so the runner serializes it identically."""

    query: str
    final_output: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    system_prompt: str = ""
    raw: dict = field(default_factory=dict)


async def run_gptoss_single_spec(query: str) -> GptOssSpecResult:
    """Arm B1 — gpt-oss-20B single-shot with the behavior-spec addendum.

    Identical to ``run_gptoss_single`` except the system prompt carries the
    strong-dose disposition spec. max_tokens=8192 for the same
    reasoning-budget reason documented in bench/gptoss_single.py.
    """
    messages = [
        {"role": "system", "content": SINGLE_SHOT_SPEC_SYSTEM},
        {"role": "user", "content": query},
    ]
    response = await local_chat(GPT_OSS_20B, messages, max_tokens=8192)
    return GptOssSpecResult(
        query=query,
        final_output=response.content,
        latency_ms=response.latency_ms,
        input_tokens=response.prompt_eval_count,
        output_tokens=response.eval_count,
        system_prompt=SINGLE_SHOT_SPEC_SYSTEM,
        raw=response.raw,
    )


async def run_council_repro(query: str) -> DeliberationResult:
    """Arm A' — v1 cabinet, Saul re-converted through our pipeline."""
    thermal = ThermalGuard.from_env()
    return await deliberate(query, thermal=thermal, cabinet_members=CABINET_REPRO)


async def run_council_spec(query: str) -> DeliberationResult:
    """Arm B2 — v1 cabinet, behavior-spec addendum on the LEGAL seat only.

    Uses the ``seat_system_prompts`` override so the frozen module-level
    LEGAL_SYSTEM is untouched; other seats keep their defaults.
    """
    thermal = ThermalGuard.from_env()
    return await deliberate(
        query,
        thermal=thermal,
        seat_system_prompts={"legal": LEGAL_SPEC_SYSTEM},
    )


async def run_council_dpo(query: str) -> DeliberationResult:
    """Arm C — v1 cabinet with the LoRA-DPO'd Saul (saul-dpo:coe).

    Fails loudly with an Ollama missing-model error if invoked before
    Phase 3 produces the tag — intentional.
    """
    thermal = ThermalGuard.from_env()
    return await deliberate(query, thermal=thermal, cabinet_members=CABINET_DPO)
