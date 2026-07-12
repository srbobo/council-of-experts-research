"""Cell 6 — synthesizer-register ablation. 2 seat-arms x 3 Leads x
{PRESERVE, no-PRESERVE} x 6 trigger cases = 72 runs. Idempotent."""
import asyncio, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from council.cabinet import CABINET, CABINET_SFT, CabinetMember
from council.models import chat as local_chat
from council.orchestrator import PHASE_IDS, CabinetBackends, deliberate
from council.prompts import LEAD_SYNTHESIS_SYSTEM
from council.thermal import ThermalGuard
from examples.test_cases import get_case

LEADS = {
    "phi4": None,  # default path
    "gptoss": CabinetMember(seat="lead", name="gpt-oss-20B as Lead", backbone="gpt-oss-20B",
        fine_tune_type="MoE lead ablation", ollama_tag="gpt-oss:20b", quantization="Q4_K_M",
        memory_gb=14.0, license="Apache 2.0"),
    "qwen": CabinetMember(seat="lead", name="Qwen2.5-7B as Lead", backbone="Qwen2.5 7B",
        fine_tune_type="dense lead ablation", ollama_tag="qwen2.5:7b-instruct", quantization="Q4_K_M",
        memory_gb=4.7, license="Apache 2.0"),
}
# no-PRESERVE variant: drop items 2-4 (the PRESERVE instructions)
NOPRES = re.sub(r"2\. PRESERVE numeric framing[\s\S]*?4\. PRESERVE caveats[\s\S]*?into your synthesis\.\n",
                "2. Integrate the contributions faithfully.\n", LEAD_SYNTHESIS_SYSTEM)
assert "PRESERVE" not in NOPRES.split("STEP 2")[1], "strip failed"
CASES = ['case_1_clinical_decision_support','case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract','case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion','case_6_trigger_heavy_biotech_ma']
OUT = Path('bench/runs/imported')

def lead_cabinet(lead_member):
    if lead_member is None: return None
    async def lead_chat(_m, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(lead_member, messages, max_tokens=8192, **kw)
    fns = {p: local_chat for p in PHASE_IDS}; tags = {p: "ollama" for p in PHASE_IDS}
    fns["planner"] = lead_chat; fns["synthesis"] = lead_chat
    tags["planner"] = tags["synthesis"] = f"ollama:{lead_member.ollama_tag}"
    return CabinetBackends(**fns, name=f"lead-{lead_member.ollama_tag}", backend_tags=tags)

async def main():
    thermal = ThermalGuard.from_env()
    for arm, members in (("sft", CABINET_SFT), ("base", CABINET)):
        for lead_key, lead_m in LEADS.items():
            for pres_key, synth in (("pres", None), ("nopres", NOPRES)):
                mode = f"cell6-{arm}-{lead_key}-{pres_key}"
                for c in CASES:
                    if list(OUT.glob(f"*__{c}__{mode}.json")):
                        continue
                    print(f"=== {mode} / {c} ({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
                    try:
                        r = await deliberate(get_case(c).prompt, thermal=thermal,
                                             cabinet=lead_cabinet(lead_m), cabinet_members=members,
                                             synthesis_system_override=synth)
                    except Exception as e:
                        print("  FAILED:", e, flush=True); continue
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                    (OUT / f"{stamp}__{c}__{mode}.json").write_text(json.dumps({
                        "schema_version": 2, "imported": True, "source": "cell6",
                        "captured_at": stamp, "case_id": c, "case_title": c, "mode": mode,
                        "model": mode, "final_output": r.final_output, "notes": "",
                        "deliberation": r.to_dict()}, ensure_ascii=False))
    print("=== CELL 6 COMPLETE ===", flush=True)

asyncio.run(main())
