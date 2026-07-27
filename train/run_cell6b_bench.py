"""Cell 6b bench — Lead-swap arms. All three seats stay at their PRODUCTION
(untrained) versions; only the synthesizer changes:

    cell6b-lead-repro : Qwen2.5-7B A' conversion control  (qwen-lead-repro:coe)
    cell6b-lead-orpo  : Qwen2.5-7B ORPO'd on synthesis pairs (qwen-lead-orpo:coe)

7 cases x 5 seeds x 2 arms = 70 runs. Endpoints are measured at the PIPELINE
MOUTH (final output) — that is the locus the register claim is about.
Idempotent: counts existing files per (case, mode) and runs only the shortfall.

Run: .venv/bin/python train/run_cell6b_bench.py
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from council.cabinet import CABINET, CabinetMember  # noqa: E402
from council.models import chat as local_chat  # noqa: E402
from council.orchestrator import PHASE_IDS, CabinetBackends, deliberate  # noqa: E402
from council.thermal import ThermalGuard  # noqa: E402
from examples.test_cases import get_case  # noqa: E402

ARMS = {
    "cell6b-lead-repro": CabinetMember(
        seat="lead", name="Qwen2.5-7B Lead (repro conversion)", backbone="Qwen2.5 7B",
        fine_tune_type="A' conversion control for the Lead-training arm",
        ollama_tag="qwen-lead-repro:coe", quantization="Q4_K_M",
        memory_gb=4.7, license="Apache 2.0"),
    "cell6b-lead-orpo": CabinetMember(
        seat="lead", name="Qwen2.5-7B Lead (ORPO on synthesis pairs)", backbone="Qwen2.5 7B",
        fine_tune_type="ORPO on 91 content-controlled SYNTHESIS-level pairs (Cell 6b)",
        ollama_tag="qwen-lead-orpo:coe", quantization="Q4_K_M",
        memory_gb=4.7, license="Apache 2.0 (derived)"),
}

CASES = ['case_1_clinical_decision_support', 'case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract', 'case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion', 'case_6_trigger_heavy_biotech_ma',
         'case_7_trigger_light_baseline']
SEEDS = 5
OUT = Path('bench/runs/imported')


def lead_cabinet(lead_member):
    async def lead_chat(_m, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(lead_member, messages, max_tokens=8192, **kw)

    fns = {p: local_chat for p in PHASE_IDS}
    tags = {p: "ollama" for p in PHASE_IDS}
    fns["planner"] = lead_chat
    fns["synthesis"] = lead_chat
    tags["planner"] = tags["synthesis"] = f"ollama:{lead_member.ollama_tag}"
    return CabinetBackends(**fns, name=f"lead-{lead_member.ollama_tag}", backend_tags=tags)


async def main():
    thermal = ThermalGuard.from_env()
    for mode, lead_m in ARMS.items():
        for case in CASES:
            have = len(list(OUT.glob(f"*__{case}__{mode}.json")))
            for i in range(max(0, SEEDS - have)):
                print(f"=== {mode} / {case} [{have + i + 1}/{SEEDS}] "
                      f"({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
                try:
                    r = await deliberate(get_case(case).prompt, thermal=thermal,
                                         cabinet=lead_cabinet(lead_m),
                                         cabinet_members=CABINET)
                except Exception as e:  # noqa: BLE001
                    print("  FAILED:", e, flush=True)
                    continue
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                (OUT / f"{stamp}__{case}__{mode}.json").write_text(json.dumps({
                    "schema_version": 2, "imported": True, "source": "cell6b",
                    "captured_at": stamp, "case_id": case, "case_title": case,
                    "mode": mode, "model": lead_m.ollama_tag,
                    "final_output": r.final_output, "notes": "",
                    "deliberation": r.to_dict()}, ensure_ascii=False))
    total = len(list(OUT.glob("*__cell6b-lead-*.json")))
    print(f"=== CELL 6B BENCH COMPLETE: {total}/70 ===", flush=True)


asyncio.run(main())
