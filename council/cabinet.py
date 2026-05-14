"""Cabinet definitions — the four models that make up the Council of Experts.

Each ``CabinetMember`` carries the metadata the orchestrator and CLI need to
locate the model in Ollama, surface it to the user, and reason about its
memory footprint when deciding whether to flush it in sequential mode.

Memory numbers are approximate resident size including KV cache for a typical
query; consult docs/QUANTIZATION.md in the source spec for the underlying math.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel  # Pydantic v2 — runtime-validated typed records


# Roles in the council. "lead" is the synthesizer; the three industry seats
# are domain specialists.
SeatRole = Literal["lead", "healthcare", "legal", "finance"]


class CabinetMember(BaseModel):
    """One member of the Council of Experts.

    ``ollama_tag`` is the exact string passed to the Ollama Python client.
    Industry agents pull from public HuggingFace mirrors; the Lead pulls from
    the Ollama Library directly.
    """

    seat: SeatRole
    name: str              # human-readable, shown in CLI + UI
    backbone: str          # base model this fine-tune derives from
    fine_tune_type: str    # short description (e.g. "continued pretrain on legal corpus")
    ollama_tag: str        # exact tag for `ollama pull` / Ollama Python client
    quantization: str      # Q4_K_M, Q8_0, etc.
    memory_gb: float       # approximate resident size including KV cache
    license: str           # license summary; consult upstream for full terms


# The Lead is intentionally a reasoning generalist (Phi-4). An industry-
# specialized Lead would bias synthesis toward whatever domain it was tuned on
# — see source docx Part 1 for the full rationale.
LEAD = CabinetMember(
    seat="lead",
    name="Phi-4 14B (Microsoft)",
    backbone="Phi-4 14B",
    fine_tune_type="reasoning generalist (synthetic instruction-following + chain-of-thought)",
    ollama_tag="phi4:14b",
    quantization="Q4_K_M",
    memory_gb=9.0,
    license="MIT",
)

HEALTHCARE = CabinetMember(
    seat="healthcare",
    # On HF this model is `Llama3-Med42-8B`. The source docx referred to "Med42-v2",
    # which appears to have been forward-looking; the actual current release is
    # `m42-health/Llama3-Med42-8B`. Pulled here via mradermacher's GGUF mirror,
    # the most-downloaded community quantization.
    name="Llama3-Med42-8B (m42-health)",
    backbone="Llama 3.1 8B",
    fine_tune_type="clinical fine-tune with multi-stage preference alignment",
    ollama_tag="huggingface.co/mradermacher/Llama3-Med42-8B-GGUF:Q4_K_M",
    quantization="Q4_K_M",
    memory_gb=5.0,
    license="Llama 3 Community License",
)

LEGAL = CabinetMember(
    seat="legal",
    # The source docx called this "SaulLM-7B-Instruct-v1"; the actual release name
    # from Equall.ai is `Saul-7B-Instruct-v1` (no "LM"). Same project, same model;
    # the docx just had the wrong name. Pulled here via MaziyarPanahi's GGUF mirror.
    name="Saul-7B-Instruct-v1 (Equall.ai)",
    backbone="Mistral 7B",
    fine_tune_type="continued pretrain on 30B+ tokens of US/UK/CA/AU legal text + instruction tune",
    ollama_tag="huggingface.co/MaziyarPanahi/Saul-Instruct-v1-GGUF:Q4_K_M",
    quantization="Q4_K_M",
    memory_gb=5.0,
    license="MIT",
)

# Finance ships at Q8_0 (per Sam's directive 2026-05-05 to use the larger model).
# The upstream HF GGUF (`pate2464/Qwen-Open-Finance-R-8B-FP8-Q8_0-GGUF`) arrived
# at Ollama with a passthrough chat template (just `{{ .Prompt }}`), which silently
# discarded system prompts and put the model in raw-completion mode. We rebuilt
# it locally with a proper ChatML template — see `modelfiles/qwen-finance.Modelfile`
# — and use the `qwen-finance-r:coe` tag below. The underlying weights are
# unchanged; only the template manifest differs.
#
# Optional Phase 1.3 step still applies if we later want to self-quantize to
# Q4_K_M and reclaim ~3.7 GB for parallel-mode headroom.
FINANCE = CabinetMember(
    seat="finance",
    name="Qwen-Open-Finance-R 8B (DragonLLM)",
    backbone="Qwen3-8B",
    fine_tune_type="instruction fine-tune on >50% finance-domain corpus (en/fr/de)",
    ollama_tag="qwen-finance-r:coe",
    quantization="Q8_0",
    memory_gb=8.7,
    license="Apache 2.0",
)


CABINET: dict[SeatRole, CabinetMember] = {
    "lead": LEAD,
    "healthcare": HEALTHCARE,
    "legal": LEGAL,
    "finance": FINANCE,
}


def all_industry_seats() -> list[CabinetMember]:
    """Return the three industry agents in deterministic order.

    Used by the orchestrator so audit logs show the same seat order across runs.
    """
    return [HEALTHCARE, LEGAL, FINANCE]
