"""Cell 8b (amended) — intrinsic register by alignment lineage.

Each candidate answers the seven bench cases directly under a MINIMAL neutral
instruction placed in the USER position, so system-blindness (see the runbook
amendment: OpenBioLLM and BioMistral ignore system prompts) does not
differentially penalize any candidate. This measures each model's
characteristic output band with no instruction gain applied.

Arms (7 cases x 5 seeds each = 140 runs):
  reg-med42      Med42-8B           Llama-3 base, preference-aligned lineage
                 (OpenBioLLM excluded: unbenchable GGUF, see runbook amendment #2)
  reg-biomistral BioMistral-7B      Mistral base, continued-pretrain lineage
  reg-mistral    Mistral-7B-Instr   generic instruct control (family split)
  reg-qwen       Qwen2.5-7B-Instr   scale anchor (production Lead band 1.03)

Idempotent. Run: .venv/bin/python train/run_cell8b_register.py
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from council.cabinet import CabinetMember  # noqa: E402
from council.models import chat as local_chat  # noqa: E402
from examples.test_cases import get_case  # noqa: E402

CASES = ['case_1_clinical_decision_support', 'case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract', 'case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion', 'case_6_trigger_heavy_biotech_ma',
         'case_7_trigger_light_baseline']
SEEDS = 5
OUT = Path('bench/runs/imported')

# Minimal, neutral, and IDENTICAL for every arm. Deliberately contains no
# disposition instruction of any kind — the point is the unconditioned band.
NEUTRAL = ("You are a senior cross-domain analyst. Answer the question "
           "directly and substantively.")


def m(name: str, tag: str, backbone: str, lineage: str) -> CabinetMember:
    return CabinetMember(seat="lead", name=name, backbone=backbone,
                         fine_tune_type=lineage, ollama_tag=tag,
                         quantization="Q4_K_M", memory_gb=5.0, license="see model card")


ARMS = [
    ("reg-med42", m("Med42-8B", "med42-repro:coe", "Llama-3 8B",
                    "preference-aligned (SFT+DPO) biomedical")),
    ("reg-biomistral", m("BioMistral-7B", "hf.co/MaziyarPanahi/BioMistral-7B-GGUF:Q4_K_M",
                         "Mistral 7B v0.1", "continued pretrain, no preference stage")),
    ("reg-mistral", m("Mistral-7B-Instruct-v0.3", "mistral:7b-instruct-v0.3-q4_K_M",
                      "Mistral 7B v0.3", "generic instruct control")),
    ("reg-qwen", m("Qwen2.5-7B-Instruct", "qwen2.5:7b-instruct", "Qwen2.5 7B",
                   "generic instruct anchor")),
]


async def main() -> None:
    for mode, member in ARMS:
        for case in CASES:
            have = len(list(OUT.glob(f"*__{case}__{mode}.json")))
            for i in range(max(0, SEEDS - have)):
                print(f"=== {mode} / {case} [{have + i + 1}/{SEEDS}] "
                      f"({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
                q = get_case(case).prompt
                try:
                    r = await local_chat(member,
                                         [{"role": "user", "content": f"{NEUTRAL}\n\n{q}"}],
                                         max_tokens=8192, temperature=0.2)
                except Exception as e:  # noqa: BLE001
                    print("  FAILED:", e, flush=True)
                    continue
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                (OUT / f"{stamp}__{case}__{mode}.json").write_text(json.dumps({
                    "schema_version": 2, "imported": True, "source": "cell8b",
                    "captured_at": stamp, "case_id": case, "case_title": case,
                    "mode": mode, "model": member.ollama_tag,
                    "final_output": r.content, "notes": member.fine_tune_type,
                    "deliberation": {}}, ensure_ascii=False))
    total = len(list(OUT.glob("*__reg-*.json")))
    print(f"=== CELL 8B COMPLETE: {total}/140 ===", flush=True)


asyncio.run(main())
