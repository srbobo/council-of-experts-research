"""Cell 19 — the runtime provenance gate, tested where instruction and
training failed.

Uses the harness (harness/) as the intervention: after the council writes its
draft, audit it against what the specialists actually raised; if invented
families are present, send evidence-specific feedback naming the exact
phrases and re-run ONLY the writing call (upstream frozen), max 2 retries;
annotate any residual.

Writer: gpt-oss-20B in every role, matching the arch-council baselines
(thin-supply invention 0.53 / 33% traceable; strict trigger battery 0.23 /
87%). 9 cases x 5 seeds = 45 runs, source cell19, mode c19-gated.

The verdict must use gate_record.post_* (pre-annotation): the annotation
itself names families and would contaminate the regex count. Both texts are
persisted. Idempotent.

Run: .venv/bin/python train/run_cell19_gate.py
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
from harness import audit, assert_path, gate  # noqa: E402

CASES = ['case_1_clinical_decision_support', 'case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract', 'case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion', 'case_6_trigger_heavy_biotech_ma',
         'case_8_trigger_light_hand_hygiene', 'case_9_trigger_light_nda_clauses',
         'case_10_trigger_light_depreciation']
SEEDS = 5
MODE = "c19-gated"
OUT = Path('bench/runs/imported')


def uniform_cabinet() -> CabinetBackends:
    async def chat_fn(_member, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(GPT_OSS_20B, messages, max_tokens=8192, **kw)
    fns = {p: chat_fn for p in PHASE_IDS}
    tags = {p: f"ollama:{GPT_OSS_20B.ollama_tag}" for p in PHASE_IDS}
    return CabinetBackends(**fns, name="c19-gptoss-uniform", backend_tags=tags)


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
                                     cabinet_members=CABINET)
            except Exception as e:  # noqa: BLE001
                print("  FAILED (deliberate):", e, flush=True)
                continue
            t_council = time.time() - t0

            seat_texts = [getattr(t, 'output_text', '') for t in d.turns]
            syn_msgs = d.synthesis.input_messages if d.synthesis else []
            path = assert_path(d.plan.get('routes', []),
                               syn_msgs[0]['content'] if syn_msgs else '',
                               require_min_routes=1,
                               require_prompt_contains="PRESERVE")
            if path.quarantined:
                print(f"  QUARANTINED: {path.reason}", flush=True)
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                (OUT / f"{stamp}__{case}__{MODE}.json").write_text(json.dumps({
                    "schema_version": 2, "imported": True, "source": "cell19",
                    "captured_at": stamp, "case_id": case, "case_title": case,
                    "mode": MODE, "model": GPT_OSS_20B.ollama_tag,
                    "final_output": d.final_output, "notes": "QUARANTINED",
                    "execution_path": {"routes": path.routes, "quarantined": True,
                                       "reason": path.reason},
                    "deliberation": d.to_dict()}, ensure_ascii=False))
                continue

            async def rewrite(draft: str, feedback: str) -> str:
                msgs = list(syn_msgs) + [
                    {"role": "assistant", "content": draft},
                    {"role": "user", "content": feedback},
                ]
                r = await local_chat(GPT_OSS_20B, msgs, max_tokens=8192,
                                     temperature=0.2)
                return r.content

            t1 = time.time()
            final_text, rec = await gate(seat_texts, d.final_output, rewrite,
                                         max_retries=2)
            t_gate = time.time() - t1

            print(f"    gate: invented {sorted(rec.pre.invented)} -> "
                  f"{sorted(rec.post.invented)} in {rec.retries} retries"
                  f"{' [annotated]' if rec.annotated else ''}", flush=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            (OUT / f"{stamp}__{case}__{MODE}.json").write_text(json.dumps({
                "schema_version": 2, "imported": True, "source": "cell19",
                "captured_at": stamp, "case_id": case, "case_title": case,
                "mode": MODE, "model": GPT_OSS_20B.ollama_tag,
                "final_output": final_text,
                "pre_gate_output": d.final_output,
                "post_gate_output_unannotated": final_text if not rec.annotated
                    else final_text[:final_text.rindex("\n\n---\n")],
                "gate": {
                    "pre_invented": sorted(rec.pre.invented),
                    "pre_kept": sorted(rec.pre.kept),
                    "post_invented": sorted(rec.post.invented),
                    "post_kept": sorted(rec.post.kept),
                    "supply": rec.pre.supply,
                    "retries": rec.retries,
                    "annotated": rec.annotated,
                    "council_seconds": round(t_council, 1),
                    "gate_seconds": round(t_gate, 1),
                },
                "execution_path": {"routes": path.routes, "quarantined": False},
                "notes": "runtime provenance gate, max 2 retries",
                "deliberation": d.to_dict()}, ensure_ascii=False))
    total = len(list(OUT.glob(f"*__{MODE}.json")))
    print(f"=== CELL 19 COMPLETE: {total}/45 ===", flush=True)


asyncio.run(main())
