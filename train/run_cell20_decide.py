"""Cell 20 — the decision/attribution instruction: the one rendering-side
lever the programme never pulled.

Production synthesis prompt + a DECIDE clause (render an explicit
recommendation; attribute considerations to named specialists; acknowledge
and justify any overruled caveat; never present own judgment as a
specialist's). Writer gpt-oss-20B in every role; same 9 cases as Cell 19 so
existing corpora serve as baselines. NO runtime feedback of any kind
(registered guard — Cell 19 showed detector-visible revision teaches
evasion). Path asserted per run; provenance audit persisted for P20.4.

Run: .venv/bin/python train/run_cell20_decide.py
"""
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from council.cabinet import CABINET, GPT_OSS_20B  # noqa: E402
from council.models import chat as local_chat  # noqa: E402
from council.orchestrator import PHASE_IDS, CabinetBackends, deliberate  # noqa: E402
from council.thermal import ThermalGuard  # noqa: E402
from examples.test_cases import get_case  # noqa: E402
from council.prompts import LEAD_SYNTHESIS_SYSTEM  # noqa: E402
from harness import audit, assert_path  # noqa: E402

CASES = ['case_1_clinical_decision_support', 'case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract', 'case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion', 'case_6_trigger_heavy_biotech_ma',
         'case_8_trigger_light_hand_hygiene', 'case_9_trigger_light_nda_clauses',
         'case_10_trigger_light_depreciation']
SEEDS = 5
MODE = "c20-decide"
OUT = Path('bench/runs/imported')


DECIDE = """
6. RENDER A DECISION. End with an explicit recommendation. Attribute the key \
supporting and opposing considerations to the specialists who raised them, by \
name ("the finance contribution models...", "legal flags..."). Where you \
discount or overrule a specialist's caveat, say so explicitly and give your \
reason. Do not present your own judgment as a specialist's.
"""


def decide_variant() -> str:
    base = LEAD_SYNTHESIS_SYSTEM
    anchor = "5. Use whatever structure"
    k = base.index(anchor)
    end = base.index("\n", base.index("different shape.", k)) + 1
    out = base[:end] + DECIDE + base[end:]
    assert "RENDER A DECISION" in out and out.count("PRESERVE") == base.count("PRESERVE")
    return out


def uniform_cabinet() -> CabinetBackends:
    async def chat_fn(_member, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(GPT_OSS_20B, messages, max_tokens=8192, **kw)
    fns = {p: chat_fn for p in PHASE_IDS}
    tags = {p: f"ollama:{GPT_OSS_20B.ollama_tag}" for p in PHASE_IDS}
    return CabinetBackends(**fns, name="c20-gptoss-uniform", backend_tags=tags)


async def main() -> None:
    thermal = ThermalGuard.from_env()
    for case in CASES:
        have = len(list(OUT.glob(f"*__{case}__{MODE}.json")))
        for i in range(max(0, SEEDS - have)):
            print(f"=== {MODE} / {case} [{have + i + 1}/{SEEDS}] "
                  f"({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
            t0 = time.time()
            try:
                d = await deliberate(get_case(case).prompt, thermal=thermal,
                                     cabinet=uniform_cabinet(),
                                     cabinet_members=CABINET,
                                     synthesis_system_override=decide_variant())
            except Exception as e:  # noqa: BLE001
                print("  FAILED (deliberate):", e, flush=True)
                continue
            t_council = time.time() - t0

            seat_texts = [getattr(t, 'output_text', '') for t in d.turns]
            syn_msgs = d.synthesis.input_messages if d.synthesis else []
            path = assert_path(d.plan.get('routes', []),
                               syn_msgs[0]['content'] if syn_msgs else '',
                               require_min_routes=1,
                               require_prompt_contains="RENDER A DECISION")
            if path.quarantined:
                print(f"  QUARANTINED: {path.reason}", flush=True)
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                (OUT / f"{stamp}__{case}__{MODE}.json").write_text(json.dumps({
                    "schema_version": 2, "imported": True, "source": "cell20",
                    "captured_at": stamp, "case_id": case, "case_title": case,
                    "mode": MODE, "model": GPT_OSS_20B.ollama_tag,
                    "final_output": d.final_output, "notes": "QUARANTINED",
                    "execution_path": {"routes": path.routes, "quarantined": True,
                                       "reason": path.reason},
                    "deliberation": d.to_dict()}, ensure_ascii=False))
                continue

            rep = audit(seat_texts, d.final_output)
            print(f"    audit: raised={rep.supply} kept={len(rep.kept)} "
                  f"invented={sorted(rep.invented)}", flush=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            (OUT / f"{stamp}__{case}__{MODE}.json").write_text(json.dumps({
                "schema_version": 2, "imported": True, "source": "cell20",
                "captured_at": stamp, "case_id": case, "case_title": case,
                "mode": MODE, "model": GPT_OSS_20B.ollama_tag,
                "final_output": d.final_output,
                "provenance": {
                    "raised": sorted(rep.raised), "kept": sorted(rep.kept),
                    "invented": sorted(rep.invented), "supply": rep.supply,
                    "council_seconds": round(t_council, 1),
                },
                "execution_path": {"routes": path.routes, "quarantined": False},
                "notes": "DECIDE clause, no runtime feedback (registered guard)",
                "deliberation": d.to_dict()}, ensure_ascii=False))
    total = len(list(OUT.glob(f"*__{MODE}.json")))
    print(f"=== CELL 20 COMPLETE: {total}/45 ===", flush=True)


asyncio.run(main())
