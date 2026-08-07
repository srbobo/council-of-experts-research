"""Cell 28 — replication of the ledger's c->0 / w-preserved pattern.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 28 PRE-REGISTRATION".
Protocol BYTE-IDENTICAL to Cell 27 (imported, not copied): same
LEDGER_PROTOCOL constant, delimiter, path assertion, hygiene. Fresh seeds,
mode c28-ledger-rep.

Run:  .venv/bin/python train/run_cell28_ledger_rep.py runs
      .venv/bin/python train/run_cell28_ledger_rep.py measure
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import CASES                      # noqa: E402
from train.run_cell27_ledger import LEDGER_PROTOCOL, answer_of  # noqa: E402

MODE = "c28-ledger-rep"
SEEDS = 5
RUNS = ROOT / "bench" / "runs" / "imported"


async def _runs_async() -> None:
    from datetime import datetime, timezone

    from council.cabinet import CABINET, GPT_OSS_20B
    from council.models import chat as local_chat
    from council.orchestrator import PHASE_IDS, CabinetBackends, deliberate
    from council.thermal import ThermalGuard
    from examples.test_cases import get_case
    from gst.path import assert_path

    def uniform() -> CabinetBackends:
        async def fn(_m, messages, **kw):
            kw.pop("max_tokens", None)
            return await local_chat(GPT_OSS_20B, messages, max_tokens=8192, **kw)
        return CabinetBackends(**{p: fn for p in PHASE_IDS},
                               name="c28-gptoss-uniform",
                               backend_tags={p: f"ollama:{GPT_OSS_20B.ollama_tag}"
                                             for p in PHASE_IDS})

    thermal = ThermalGuard.from_env()
    for case in CASES:
        have = len(list(RUNS.glob(f"*__{case}__{MODE}.json")))
        for i in range(max(0, SEEDS - have)):
            print(f"=== {MODE} / {case} [{have+i+1}/{SEEDS}] ===", flush=True)
            try:
                d = await deliberate(get_case(case).prompt, thermal=thermal,
                                     cabinet=uniform(), cabinet_members=CABINET,
                                     synthesis_system_override=LEDGER_PROTOCOL)
            except Exception as e:  # noqa: BLE001
                print("  FAILED:", e, flush=True)
                continue
            syn = d.synthesis.input_messages if d.synthesis else []
            path = assert_path(d.plan.get("routes", []),
                               syn[0]["content"] if syn else "",
                               require_prompt_contains="EVIDENCE LEDGER")
            ans = answer_of(d.final_output or "")
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            (RUNS / f"{stamp}__{case}__{MODE}.json").write_text(json.dumps({
                "schema_version": 2, "imported": True, "source": "cell28",
                "captured_at": stamp, "case_id": case, "case_title": case,
                "mode": MODE, "model": GPT_OSS_20B.ollama_tag,
                "final_output": ans if ans is not None else (d.final_output or ""),
                "full_output": d.final_output,
                "protocol_violation": ans is None,
                "execution_path": {"routes": path.routes,
                                   "quarantined": path.quarantined,
                                   "reason": path.reason},
                "notes": "cell28 replication; ANSWER-only in final_output",
                "deliberation": d.to_dict()}, ensure_ascii=False))
            if path.quarantined or ans is None:
                print(f"  QUARANTINE/VIOLATION: {path.reason or 'no ANSWER delim'}",
                      flush=True)
    print("c28 runs complete", flush=True)


def stage_runs() -> None:
    import asyncio
    asyncio.run(_runs_async())


def stage_measure() -> None:
    from gst.adapters.coe import from_ledger
    from gst.card import measure_all
    from gst.instruments import RegexInstrument
    from gst.stats import wilson_ci

    rx = RegexInstrument()
    files = list(RUNS.glob(f"*__{MODE}.json"))
    viol = sum(1 for f in files if json.loads(f.read_text()).get("protocol_violation"))
    recs = [r for r in from_ledger(RUNS) if r.condition == MODE
            and len(r.output) >= 500]
    print(f"C28: {len(files)} runs, {viol} violations, {len(recs)} usable")
    card = measure_all(recs, system="council-ledger replication (cell 28)")
    print(card.render())

    sh = card.shrinkage
    print("=" * 74)
    if not (sh and sh.identifiable and sh.w_ci and sh.c_ci):
        print("P28.1/28.3: card unidentifiable — report and stop")
        return
    p281 = sh.c_ci[1] < 0.44
    print(f"P28.1 (prior fill): c={sh.c:.3f} [{sh.c_ci[0]:.3f},{sh.c_ci[1]:.3f}] "
          f"vs baseline [0.44,0.99] -> "
          f"{'SUPPORTED (disjoint below)' if p281 else 'FALSIFIED'}")

    z = [(1 if rx.families(r.output) else 0) for r in recs
         if not rx.families(r.upstream_text)]
    if len(z) >= 8:
        ci = wilson_ci(sum(z), len(z))
        p282 = ci[1] < 0.27
        print(f"P28.2 (s=0 invention): {sum(z)}/{len(z)} "
              f"[{ci[0]:.2f},{ci[1]:.2f}] vs baseline [0.27,0.81] -> "
              f"{'SUPPORTED (disjoint below)' if p282 else 'FALSIFIED'}")
    else:
        print(f"P28.2: NOT EVALUABLE — s=0 stratum n={len(z)} < 8 "
              "(registered evaluability floor; design shortfall reported)")

    overlap = not (sh.w_ci[1] < 0.291 or sh.w_ci[0] > 0.478)
    p283 = sh.w_ci[0] > 0.15 and overlap
    print(f"P28.3 (gain preserved): w={sh.w:.3f} [{sh.w_ci[0]:.3f},"
          f"{sh.w_ci[1]:.3f}]; excludes register corner={sh.w_ci[0] > 0.15}, "
          f"overlaps C27-L1 [0.291,0.478]={overlap} -> "
          f"{'SUPPORTED' if p283 else 'FALSIFIED'}")

    em = [len(rx.families(r.output)) for r in recs]
    zq = sum(1 for r in recs if not rx.families(r.output))
    print(f"COST ACCOUNTING (mandatory): mean emitted {sum(em)/len(em):.2f} "
          f"families; zero-qualification runs {zq}/{len(recs)}; "
          f"f={card.spans.f_median:.3f}; violation rate {viol}/{len(files)} "
          f"({viol/len(files):.1%})")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "runs"
    {"runs": stage_runs, "measure": stage_measure}[stage]()
