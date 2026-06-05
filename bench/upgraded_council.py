"""local-council-v2 — the same orchestration with upgraded specialist seats.

Path C of the specialist-upgrade investigation (mid-2026). Two seats swap:

  - Healthcare:  Llama3-Med42-8B  →  Meditron3-Qwen2.5-7B (EPFL, May 2026)
  - Finance:     Qwen-Open-Finance-R-8B  →  Llama-3.1-Hawkish-8B (mukaj)
  - Legal:       Saul-7B-Instruct-v1  (unchanged — no peer at this size)
  - Lead:        Phi-4 14B  (unchanged)

The point is to test whether the article-level MoE finding
("specialists are the weak link, not the architecture") survives a
targeted specialist upgrade with documented improvements (Meditron3 has
active EPFL maintenance + newer Qwen2.5 backbone; Hawkish-8B is the
first 8B model to pass CFA Level 1 mock at 71.4%).

If local-council-v2's rubric coverage substantially improves over the
existing local-council, the article reframes around "the right
specialists at small scale can close the gap." If it doesn't, the MoE
finding holds: the limit is small-model capability, not specialist
freshness.
"""

from __future__ import annotations

from council.cabinet import CABINET_V2
from council.orchestrator import DeliberationResult, deliberate
from council.thermal import ThermalGuard


async def run_upgraded_council(query: str) -> DeliberationResult:
    """Run the council orchestrator with the v2 (upgraded specialist) cabinet.

    Identical orchestration to ``local-council``: same Lead (Phi-4), same
    planner prompt, same step-back decomposition, same per-seat system
    prompts, same tension-extraction synthesis. Only the Healthcare and
    Finance specialist models change.

    Local-only — no cost guard, no Anthropic SDK.
    """
    thermal = ThermalGuard.from_env()
    return await deliberate(
        query,
        thermal=thermal,
        cabinet_members=CABINET_V2,
    )
