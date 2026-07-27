"""Cell 6c — gain curve + input additivity + order invariance. No training.

(a) GAIN CURVE: PRESERVE clause count k in {0,1,2,3} x 3 Leads x 6 cases = 72
    runs. Clauses are removed in a fixed documented order:
      k=3 : clauses 2,3,4 present (production prompt)
      k=2 : clauses 2,4 present (drop 3 = precise vocabulary)
      k=1 : clause 4 present     (drop 2 = numeric framing; keep caveats)
      k=0 : none (the cell-6 no-PRESERVE prompt)
    (k counts PRESERVE clauses; the neutral "integrate faithfully" line replaces
    the removed block at k=0, exactly as in cell 6.)

(b) ADDITIVITY: hot-seat count h in {0,1,2,3} x Phi-4 Lead x 6 cases = 24 runs.
    Hot seats are created with the behavior-spec prompt override (the same
    LEGAL_SPEC_SYSTEM-style addendum applied per seat), so h is comparable
    across domains without needing an SFT model per seat.

(c) Order-shuffle was dropped: dispatch order is planner-determined, not
    caller-settable, so it cannot be varied cleanly (documented, not run).

Idempotent: skips any (case, mode) already present in bench/runs/imported.
Run: .venv/bin/python train/run_cell6c.py
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

LEADS = {
    "phi4": None,
    "gptoss": CabinetMember(seat="lead", name="gpt-oss-20B as Lead", backbone="gpt-oss-20B",
        fine_tune_type="MoE lead ablation", ollama_tag="gpt-oss:20b", quantization="Q4_K_M",
        memory_gb=14.0, license="Apache 2.0"),
    "qwen": CabinetMember(seat="lead", name="Qwen2.5-7B as Lead", backbone="Qwen2.5 7B",
        fine_tune_type="dense lead ablation", ollama_tag="qwen2.5:7b-instruct", quantization="Q4_K_M",
        memory_gb=4.7, license="Apache 2.0"),
}

CLAUSE2 = re.compile(r"2\. PRESERVE numeric framing[\s\S]*?as a fact\.\n")
CLAUSE3 = re.compile(r"3\. PRESERVE precise vocabulary[\s\S]*?accessibility\.\n")
CLAUSE4 = re.compile(r"4\. PRESERVE caveats[\s\S]*?into your synthesis\.\n")
FULLBLOCK = re.compile(
    r"2\. PRESERVE numeric framing[\s\S]*?4\. PRESERVE caveats[\s\S]*?into your synthesis\.\n")


def preserve_variant(k: int) -> str | None:
    """k = number of PRESERVE clauses retained (3 -> production prompt)."""
    if k == 3:
        return None  # default prompt, unmodified
    if k == 0:
        s = FULLBLOCK.sub("2. Integrate the contributions faithfully.\n", LEAD_SYNTHESIS_SYSTEM)
        assert "PRESERVE" not in s.split("STEP 2")[1], "k=0 strip failed"
        return s
    if k == 2:      # drop clause 3 (precise vocabulary)
        s = CLAUSE3.sub("", LEAD_SYNTHESIS_SYSTEM)
    elif k == 1:    # drop clauses 2 and 3, keep caveats
        s = CLAUSE3.sub("", CLAUSE2.sub("", LEAD_SYNTHESIS_SYSTEM))
    else:
        raise ValueError(k)
    assert s.count("PRESERVE") == k, f"k={k}: got {s.count('PRESERVE')} PRESERVE clauses"
    return s


# Behavior-spec addendum used to make a seat "hot" (mirrors the arm-B2 spec).
HOT_ADDENDUM = """

ADDITIONAL DISCIPLINE REQUIREMENTS — apply wherever relevant:
1. Disclose training-cutoff uncertainty explicitly ("as of my training data...").
2. Label every estimate or assumed quantity as an assumption ("modeled at", "assuming").
3. Distinguish near-synonym terms of art explicitly.
4. Treat each jurisdiction or regulatory regime separately; never blend them.
5. State what would change your conclusion ("this may vary if...").
Do not force these where they are not warranted."""

SEATS = ("healthcare", "legal", "finance")
CASES = ['case_1_clinical_decision_support', 'case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract', 'case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion', 'case_6_trigger_heavy_biotech_ma']
OUT = Path('bench/runs/imported')


def lead_cabinet(lead_member):
    if lead_member is None:
        return None

    async def lead_chat(_m, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(lead_member, messages, max_tokens=8192, **kw)

    fns = {p: local_chat for p in PHASE_IDS}
    tags = {p: "ollama" for p in PHASE_IDS}
    fns["planner"] = lead_chat
    fns["synthesis"] = lead_chat
    tags["planner"] = tags["synthesis"] = f"ollama:{lead_member.ollama_tag}"
    return CabinetBackends(**fns, name=f"lead-{lead_member.ollama_tag}", backend_tags=tags)


async def run_one(mode: str, case: str, thermal, *, lead=None, synth=None, seat_prompts=None):
    if list(OUT.glob(f"*__{case}__{mode}.json")):
        return False
    print(f"=== {mode} / {case} ({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
    try:
        kw = {}
        if seat_prompts:
            kw["seat_system_prompts"] = seat_prompts
        r = await deliberate(get_case(case).prompt, thermal=thermal,
                             cabinet=lead_cabinet(lead), cabinet_members=CABINET,
                             synthesis_system_override=synth, **kw)
    except Exception as e:  # noqa: BLE001
        print("  FAILED:", e, flush=True)
        return False
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (OUT / f"{stamp}__{case}__{mode}.json").write_text(json.dumps({
        "schema_version": 2, "imported": True, "source": "cell6c",
        "captured_at": stamp, "case_id": case, "case_title": case, "mode": mode,
        "model": mode, "final_output": r.final_output, "notes": "",
        "deliberation": r.to_dict()}, ensure_ascii=False))
    return True


async def main():
    thermal = ThermalGuard.from_env()

    # (a) gain curve
    for lead_key, lead_m in LEADS.items():
        for k in (0, 1, 2, 3):
            synth = preserve_variant(k)
            for c in CASES:
                await run_one(f"cell6c-gain-k{k}-{lead_key}", c, thermal,
                              lead=lead_m, synth=synth)

    # (b) additivity: h hot seats (Phi-4 lead, production prompt)
    from council.prompts import HEALTHCARE_SYSTEM, LEGAL_SYSTEM, FINANCE_SYSTEM
    BASE = {"healthcare": HEALTHCARE_SYSTEM, "legal": LEGAL_SYSTEM, "finance": FINANCE_SYSTEM}
    for h in (0, 1, 2, 3):
        hot = SEATS[:h]
        prompts = {s: BASE[s] + HOT_ADDENDUM for s in hot} or None
        for c in CASES:
            await run_one(f"cell6c-hot{h}", c, thermal, seat_prompts=prompts)

    # (c) order shuffle: not runnable — dispatch order is planner-determined.
    print("=== CELL 6C COMPLETE ===", flush=True)


asyncio.run(main())
