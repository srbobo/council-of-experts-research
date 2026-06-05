"""gpt-oss-as-council mode — gpt-oss-20B plays every seat in the council.

Local MoE alternative to ``opus_council``. Mirrors that module's pattern
exactly: build a uniform ``CabinetBackends`` where every phase routes to
the same chat function, and pass it to the orchestrator. The
orchestration logic (step-back planning, sub-question dispatch,
tension-extraction synthesis) is reused 1:1; only the underlying model
changes.

Why this exists: the bench question "what does the council architecture
buy us?" can be answered by comparing a single-shot run against a
council run *of the same model*. We already do this for Opus
(opus-single vs opus-council). Adding gpt-oss versions of both lets us
do the same comparison locally, with $0 of API spend, and with a
genuinely different model lineage than Phi-4.

This is NOT pathway-3 — that's the swap matrix where ONE phase is served
by a different backend. This is the uniform-cabinet equivalent of
opus-council: every phase uses the same model.
"""

from __future__ import annotations

from council.cabinet import GPT_OSS_20B
from council.models import chat as local_chat
from council.orchestrator import (
    CabinetBackends,
    DeliberationResult,
    deliberate,
)
from council.thermal import ThermalGuard


def _make_gptoss_chat():
    """Build a chat function that always routes to gpt-oss-20B, regardless
    of what ``member`` the orchestrator passes in.

    The orchestrator's per-phase callsites pass the seat's CabinetMember
    (e.g. HEALTHCARE / Med42 when consulting the healthcare seat). We want
    those calls to land on gpt-oss-20B instead — same mechanism Opus uses
    to play every seat. The seat's role identity (system prompt,
    sub-question) flows through unchanged; only the underlying model
    differs.
    """
    async def gptoss_chat(_seat_member, messages, **kwargs):
        return await local_chat(GPT_OSS_20B, messages, **kwargs)
    return gptoss_chat


async def run_gptoss_council(query: str) -> DeliberationResult:
    """Run the council orchestrator with gpt-oss-20B playing every seat.

    Local-only — no cost guard, no Anthropic SDK, no API spend. Thermal
    guard is constructed for parity with the local-council baseline; on a
    fanless M5 the inter-agent pause still matters because gpt-oss is
    served by the same Metal stack as every other local model.
    """
    cabinet = CabinetBackends.uniform(
        _make_gptoss_chat(),
        name="gptoss-council",
        tag="ollama:gpt-oss:20b",
    )
    thermal = ThermalGuard.from_env()
    return await deliberate(query, thermal=thermal, cabinet=cabinet)
