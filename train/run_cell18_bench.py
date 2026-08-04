"""Cell 11 stage 5 — bench the calibration-trained Lead. Three arms:

  cell11-cal-k3    trained Lead, production synthesis prompt
  cell11-cal-k0    trained Lead, PRESERVE stripped        <- decisive arm
  cell11-stock-k0  conversion-control Lead, PRESERVE stripped
                   (added baseline: Cell 6c's stock k=0 point is n=6 with
                   no case-7 runs, too weak to carry P11.1; this arm gives
                   the comparator the same 35-run protocol)

7 cases x 5 seeds x 3 arms = 105 runs. Existing baselines reused from the
ledger: cell6b-lead-repro (stock k=3) and cell6b-lead-orpo (P11.3).
k=0 strip is byte-identical to Cell 6c's preserve_variant(0).
Idempotent. Run: .venv/bin/python train/run_cell11_bench.py
"""
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from council.cabinet import CABINET, CabinetMember  # noqa: E402
from council.models import chat as local_chat  # noqa: E402
from council.orchestrator import PHASE_IDS, CabinetBackends, deliberate  # noqa: E402
from council.prompts import LEAD_SYNTHESIS_SYSTEM  # noqa: E402
from council.thermal import ThermalGuard  # noqa: E402
from examples.test_cases import get_case  # noqa: E402

CASES = ['case_1_clinical_decision_support', 'case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract', 'case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion', 'case_6_trigger_heavy_biotech_ma',
         'case_7_trigger_light_baseline']
SEEDS = 5
OUT = Path('bench/runs/imported')

# k=0 strip — byte-identical regex to train/run_cell6c.py.
FULLBLOCK = re.compile(
    r"2\. PRESERVE numeric framing[\s\S]*?4\. PRESERVE caveats[\s\S]*?into your synthesis\.\n")
K0_SYSTEM = FULLBLOCK.sub("2. Integrate the contributions faithfully.\n", LEAD_SYNTHESIS_SYSTEM)
assert "PRESERVE" not in K0_SYSTEM.split("STEP 2")[1], "k=0 strip failed"


def member(tag: str, name: str) -> CabinetMember:
    return CabinetMember(seat="lead", name=name, backbone="Qwen2.5 7B",
                         fine_tune_type="cell11", ollama_tag=tag,
                         quantization="Q4_K_M", memory_gb=4.7, license="Apache 2.0")


LEAD_PROV = member("qwen-lead-prov:coe", "Qwen2.5-7B Lead (provenance ORPO)")
LEAD_STOCK = member("qwen-lead-repro:coe", "Qwen2.5-7B Lead (A' conversion control)")

ARMS = [
    ("cell18-prov-k3", LEAD_PROV, None),
]


def lead_cabinet(lead: CabinetMember) -> CabinetBackends:
    async def lead_chat(_m, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(lead, messages, max_tokens=8192, **kw)
    fns = {p: local_chat for p in PHASE_IDS}
    tags = {p: "ollama" for p in PHASE_IDS}
    fns["planner"] = lead_chat
    fns["synthesis"] = lead_chat
    tags["planner"] = tags["synthesis"] = f"ollama:{lead.ollama_tag}"
    return CabinetBackends(**fns, name=f"cell11-{lead.ollama_tag}", backend_tags=tags)


async def main() -> None:
    thermal = ThermalGuard.from_env()
    for mode, lead, synth in ARMS:
        for case in CASES:
            have = len(list(OUT.glob(f"*__{case}__{mode}.json")))
            for i in range(max(0, SEEDS - have)):
                print(f"=== {mode} / {case} [{have + i + 1}/{SEEDS}] "
                      f"({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
                try:
                    r = await deliberate(get_case(case).prompt, thermal=thermal,
                                         cabinet=lead_cabinet(lead),
                                         cabinet_members=CABINET,
                                         synthesis_system_override=synth)
                except Exception as e:  # noqa: BLE001
                    print("  FAILED:", e, flush=True)
                    continue
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                (OUT / f"{stamp}__{case}__{mode}.json").write_text(json.dumps({
                    "schema_version": 2, "imported": True, "source": "cell18",
                    "captured_at": stamp, "case_id": case, "case_title": case,
                    "mode": mode, "model": lead.ollama_tag,
                    "final_output": r.final_output, "notes": "",
                    "deliberation": r.to_dict()}, ensure_ascii=False))
    total = len(list(OUT.glob("*__cell18-*.json")))
    print(f"=== CELL 18 BENCH COMPLETE: {total}/35 ===", flush=True)


asyncio.run(main())
