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


# -----------------------------------------------------------------------------
# Cabinet v2 — upgraded specialist seats (Path C of the specialist-upgrade
# search, mid-2026). Healthcare and Finance get newer/different fine-tunes;
# Legal stays unchanged (Saul-7B-Instruct-v1 remains the only US/UK/CA/AU
# common-law fine-tune at the 7-8B class — no upgrade exists at this size).
#
# Reasoning per seat:
#   - HEALTHCARE_V2 (Meditron3-Qwen2.5-7B, EPFL May 2026): newer backbone
#     (Qwen2.5 Sep 2024) than the v1 Med42's Llama 3.1 (Dec 2023). Trades
#     Med42's multi-stage preference alignment for a more recent world model.
#   - FINANCE_V2 (Hawkish-8B, mukaj Dec 2025): the first 8B model to pass
#     CFA Level 1 mock at 71.4%. Llama 3.1 base. Academic/research-only
#     license — acceptable for this research project. Trades the multi-
#     lingual finance corpus of Qwen-Open-Finance for documented benchmark
#     wins on quantitative finance reasoning.
#   - LEGAL stays as v1's Saul — no peer exists at this size.
# -----------------------------------------------------------------------------

HEALTHCARE_V2 = CabinetMember(
    seat="healthcare",
    name="Meditron3-Qwen2.5-7B (EPFL)",
    backbone="Qwen2.5 7B",
    fine_tune_type="continued pretrain + instruction tune on clinical corpus by EPFL; active maintenance",
    ollama_tag="huggingface.co/mradermacher/Meditron3-Qwen2.5-7B-GGUF:Q4_K_M",
    quantization="Q4_K_M",
    memory_gb=4.8,
    license="Qwen Research / permissive (review terms before production)",
)

FINANCE_V2 = CabinetMember(
    seat="finance",
    name="Llama-3.1-Hawkish-8B (mukaj)",
    backbone="Llama 3.1 8B",
    fine_tune_type="50M-token financial instruction tune; CFA Level 1 mock pass at 71.4% (first 8B to do so)",
    ollama_tag="huggingface.co/bartowski/Llama-3.1-Hawkish-8B-GGUF:Q4_K_M",
    quantization="Q4_K_M",
    memory_gb=5.0,
    license="Llama 3.1 + academic/research-only restriction (no production use)",
)

# v2 cabinet retains LEAD and LEGAL from v1; only HEALTHCARE and FINANCE swap.
CABINET_V2: dict[SeatRole, CabinetMember] = {
    "lead": LEAD,
    "healthcare": HEALTHCARE_V2,
    "legal": LEGAL,
    "finance": FINANCE_V2,
}


# -----------------------------------------------------------------------------
# DPO experiment cabinets (RUNBOOK_DPO_PROMPT_TRANSFER.md).
#
# LEGAL_REPRO — arm A': the SAME Saul weights re-converted through our own
# fp16 → GGUF → Q4_K_M pipeline (train/). Conversion control: the only
# delta vs LEGAL is the conversion path; the only delta vs LEGAL_DPO will
# be the LoRA weights. Template/params copied verbatim from the
# MaziyarPanahi tag.
#
# LEGAL_DPO — arm C: created in Phase 3 after training; tag reserved here
# so the bench mode can be wired before the model exists (the run fails
# loudly with a missing-model error if invoked early, which is the
# desired behavior).
# -----------------------------------------------------------------------------

LEGAL_REPRO = CabinetMember(
    seat="legal",
    name="Saul-7B-Instruct-v1 (repro conversion)",
    backbone="Mistral 7B",
    fine_tune_type="identical weights to LEGAL; re-converted via train/ pipeline (conversion control)",
    ollama_tag="saul-repro:coe",
    quantization="Q4_K_M",
    memory_gb=5.0,
    license="MIT",
)

LEGAL_DPO = CabinetMember(
    seat="legal",
    name="Saul-7B-DPO (behavior-targeted LoRA)",
    backbone="Mistral 7B",
    fine_tune_type="LoRA-DPO on ~400 content-controlled disposition preference pairs (arm C)",
    ollama_tag="saul-dpo:coe",
    quantization="Q4_K_M",
    memory_gb=5.0,
    license="MIT (derived)",
)

CABINET_REPRO: dict[SeatRole, CabinetMember] = {
    "lead": LEAD,
    "healthcare": HEALTHCARE,
    "legal": LEGAL_REPRO,
    "finance": FINANCE,
}

CABINET_DPO: dict[SeatRole, CabinetMember] = {
    "lead": LEAD,
    "healthcare": HEALTHCARE,
    "legal": LEGAL_DPO,
    "finance": FINANCE,
}


# -----------------------------------------------------------------------------
# Comparison-only models — not council members.
#
# These are CabinetMember records for models the bench harness uses as
# *alternatives* to the council, not as members of it. They live here so
# the bench modules can reuse the same model-metadata shape (name, tag,
# quantization, memory) the council uses, without complicating the
# council's CABINET dict — which the orchestrator iterates over as the
# canonical seat list.
#
# GPT_OSS_20B is the MoE local alternative to Opus 4.7 for benchmarking
# the council architecture. Picked over Qwen3-30B-A3B (~18 GB, tighter),
# Mixtral 8x7B (~26 GB at Q4, too large to comfortably share memory with
# Phi-4), and Gemma 4 26B MoE (~17 GB, weaker reasoning benchmarks than
# gpt-oss at the time of selection). gpt-oss-20B's ~3.6B active params
# (MoE design) keep per-token latency low while the 20B total capacity
# provides headroom for reasoning. OpenAI's first open-weights release;
# Apache 2.0; designed by OpenAI specifically for "lower latency, local,
# or specialized use-cases."
# -----------------------------------------------------------------------------

GPT_OSS_20B = CabinetMember(
    # `seat` is required by the Pydantic model; reuse "lead" since the
    # gpt-oss comparison modes use this member in lead-equivalent roles
    # (single-shot answer, or every phase of a uniform gpt-oss council).
    # The audit log distinguishes via the bench mode name + the per-turn
    # `backend` field on AgentTurn, not via `seat`.
    seat="lead",
    name="gpt-oss-20B (OpenAI, MoE)",
    backbone="gpt-oss-20B",
    fine_tune_type="mixture-of-experts; ~3.6B active params; reasoning-tuned",
    ollama_tag="gpt-oss:20b",
    quantization="Q4_K_M",
    memory_gb=14.0,
    license="Apache 2.0",
)


def all_industry_seats() -> list[CabinetMember]:
    """Return the three industry agents in deterministic order.

    Used by the orchestrator so audit logs show the same seat order across runs.
    """
    return [HEALTHCARE, LEGAL, FINANCE]


# Cell 1 of the paper-hardening matrix: SFT-on-chosen control seat.
# Same pairs' chosen responses, same LoRA config/seed as LEGAL_DPO —
# only the training objective differs (SFT vs ORPO). P1 comparator.
LEGAL_SFT = CabinetMember(
    seat="legal",
    name="Saul-7B-SFT-chosen (control)",
    backbone="Mistral 7B",
    fine_tune_type="LoRA SFT on the 91 chosen responses only (no preference signal) — P1 control",
    ollama_tag="saul-sft:coe",
    quantization="Q4_K_M",
    memory_gb=5.0,
    license="MIT (derived)",
)

CABINET_SFT: dict[SeatRole, CabinetMember] = {
    "lead": LEAD,
    "healthcare": HEALTHCARE,
    "legal": LEGAL_SFT,
    "finance": FINANCE,
}


LEGAL_DPO_V2 = CabinetMember(
    seat="legal", name="Saul-7B-ORPO-v2 (292 pairs, 16 epochs)", backbone="Mistral 7B",
    fine_tune_type="ORPO at 3.2x dose (dose-response cell), epoch-matched to v1",
    ollama_tag="saul-dpo-v2:coe", quantization="Q4_K_M", memory_gb=5.0, license="MIT (derived)")
CABINET_DPO_V2: dict[SeatRole, CabinetMember] = {
    "lead": LEAD, "healthcare": HEALTHCARE, "legal": LEGAL_DPO_V2, "finance": FINANCE}

# -----------------------------------------------------------------------------
# Cell 3 (healthcare seat, P3) — swaps ONLY the healthcare seat between the
# med42 conversion-control (A') and the ORPO-trained seat. Legal uses
# LEGAL_REPRO in both arms so the sole delta is the healthcare training. Both
# med42 tags carry the native Llama-3 template (built in run_cell3_health.sh),
# not the stock mismatched-ChatML GGUF.
HEALTH_REPRO = CabinetMember(
    seat="healthcare", name="Med42-8B (repro conversion)", backbone="Llama 3.1 8B",
    fine_tune_type="identical weights to HEALTHCARE; re-converted via train/ pipeline (conversion control)",
    ollama_tag="med42-repro:coe", quantization="Q4_K_M", memory_gb=5.0,
    license="Llama 3 Community License")
HEALTH_ORPO = CabinetMember(
    seat="healthcare", name="Med42-8B-ORPO (behavior-targeted LoRA)", backbone="Llama 3.1 8B",
    fine_tune_type="ORPO on 91 content-controlled disposition pairs (Cell 3, dose-matched to legal)",
    ollama_tag="med42-orpo:coe", quantization="Q4_K_M", memory_gb=5.0,
    license="Llama 3 Community License (derived)")
CABINET_HEALTH_REPRO: dict[SeatRole, CabinetMember] = {
    "lead": LEAD, "healthcare": HEALTH_REPRO, "legal": LEGAL_REPRO, "finance": FINANCE}
CABINET_HEALTH_ORPO: dict[SeatRole, CabinetMember] = {
    "lead": LEAD, "healthcare": HEALTH_ORPO, "legal": LEGAL_REPRO, "finance": FINANCE}
