"""Cell 13 — per-clause isolation of the PRESERVE block.

Cell 6c dropped clauses in a FIXED order, so its monotone gain curve confounds
count with identity. Here each clause is tested ALONE against a true no-clause
baseline, with one Lead and everything else held fixed.

Arms (7 cases x 5 seeds x 6 = 210 runs):
  c13-none  no C1-C4          (NB: not byte-identical to cell6c-gain-k0,
                               which retains C1 — see runbook correction)
  c13-c1    C1 only  tension acknowledgment (no PRESERVE keyword)
  c13-c2    C2 only  PRESERVE numeric framing    -> modeled-assumptions
  c13-c3    C3 only  PRESERVE precise vocabulary -> vocabulary-precision
  c13-c4    C4 only  PRESERVE caveats            -> cutoff-disclosure
  c13-all   C1-C4    production prompt

Lead: gpt-oss-20B in every phase (widest Cell 6c dynamic range, 3.3x, so
per-clause differences have the most room to resolve; scoping caveat
registered). Clauses are removed with the Cell 6c regexes; surviving items
keep their original numbers, as in 6c.

Every variant asserts its exact retained-clause set before any run.
Idempotent. Run: .venv/bin/python train/run_cell13_clauses.py
"""
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from council.cabinet import CABINET, GPT_OSS_20B  # noqa: E402
from council.models import chat as local_chat  # noqa: E402
from council.orchestrator import PHASE_IDS, CabinetBackends, deliberate  # noqa: E402
from council.prompts import LEAD_SYNTHESIS_SYSTEM  # noqa: E402
from council.thermal import ThermalGuard  # noqa: E402
from examples.test_cases import get_case  # noqa: E402

CASES = ['case_1_clinical_decision_support', 'case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract', 'case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion', 'case_6_trigger_heavy_biotech_ma',
         'case_8_trigger_light_hand_hygiene', 'case_9_trigger_light_nda_clauses',
         'case_10_trigger_light_depreciation']
SEEDS = 5
OUT = Path('bench/runs/imported')

SUPPRESSION = """
6. DO NOT INTRODUCE qualifications, caveats, assumptions, or jurisdictional \
distinctions that no specialist raised. If the specialists did not flag \
uncertainty about something, state it plainly.
"""


def variant() -> str:
    """Production prompt + the suppression clause appended to STEP 2's list."""
    base = LEAD_SYNTHESIS_SYSTEM
    anchor = "5. Use whatever structure"
    k = base.index(anchor)
    end = base.index("\n", base.index("different shape.", k)) + 1
    out = base[:end] + SUPPRESSION + base[end:]
    assert "DO NOT INTRODUCE" in out and out.count("PRESERVE") == base.count("PRESERVE")
    return out


ARMS = [("c17-suppress", variant())]


def uniform_cabinet() -> CabinetBackends:
    async def chat_fn(_member, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(GPT_OSS_20B, messages, max_tokens=8192, **kw)
    fns = {p: chat_fn for p in PHASE_IDS}
    tags = {p: f"ollama:{GPT_OSS_20B.ollama_tag}" for p in PHASE_IDS}
    return CabinetBackends(**fns, name="c17-gptoss-uniform", backend_tags=tags)


async def main() -> None:
    built = {mode: v for mode, v in ARMS}
    for mode, v in ARMS:
        print(f"{mode}: PRESERVE clauses={v.count('PRESERVE')}, "
              f"suppression={'DO NOT INTRODUCE' in v}", flush=True)
    thermal = ThermalGuard.from_env()
    for mode, _v in ARMS:
        for case in CASES:
            have = len(list(OUT.glob(f"*__{case}__{mode}.json")))
            for i in range(max(0, SEEDS - have)):
                print(f"=== {mode} / {case} [{have + i + 1}/{SEEDS}] "
                      f"({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
                try:
                    r = await deliberate(get_case(case).prompt, thermal=thermal,
                                         cabinet=uniform_cabinet(),
                                         cabinet_members=CABINET,
                                         synthesis_system_override=built[mode])
                except Exception as e:  # noqa: BLE001
                    print("  FAILED:", e, flush=True)
                    continue
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                (OUT / f"{stamp}__{case}__{mode}.json").write_text(json.dumps({
                    "schema_version": 2, "imported": True, "source": "cell17",
                    "captured_at": stamp, "case_id": case, "case_title": case,
                    "mode": mode, "model": GPT_OSS_20B.ollama_tag,
                    "final_output": r.final_output, "notes": "production + suppression clause",
                    "deliberation": r.to_dict()}, ensure_ascii=False))
    total = len(list(OUT.glob("*__c17-*.json")))
    print(f"=== CELL 17 COMPLETE: {total}/45 ===", flush=True)


asyncio.run(main())
