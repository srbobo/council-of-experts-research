"""Cell 31 — the matched-baseline ledger test.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 31 PRE-REGISTRATION".
Paired design: the ledger protocol runs over the SAME de-scaffolded
variants, writers, and temperatures as Cell 30's plain-writer arm. The only
difference is the protocol, so the contrast isolates the ledger from the
clause removal that Cells 27/28 confounded it with.

Run:  .venv/bin/python train/run_cell31_matched_ledger.py runs
      .venv/bin/python train/run_cell31_matched_ledger.py measure
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                            # noqa: E402
from train.run_cell27_ledger import LEDGER_PROTOCOL, answer_of   # noqa: E402
from train.run_cell30_descaffold import WRITERS                  # noqa: E402

C30 = ROOT / "bench" / "analysis" / "cell30"
RUNS_L = ROOT / "bench" / "runs" / "cell31_matched_ledger.jsonl"
RUNS_P = ROOT / "bench" / "runs" / "cell30_descaffold.jsonl"
SEED = 0
DRAWS = 5000


def stage_runs() -> None:
    import time

    from examples.test_cases import get_case
    variants = json.loads((C30 / "variants.json").read_text())
    done = set()
    if RUNS_L.exists():
        for line in RUNS_L.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    todo = [(v, w, r) for v in variants for w, reps in WRITERS
            for r in range(reps)
            if f"{v['case']}__v{v['variant_id']}__{w}__r{r}" not in done]
    print(f"cell31: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0 = time.time()
    with RUNS_L.open("a") as fh:
        for i, (v, writer, rep) in enumerate(todo):
            rid = f"{v['case']}__v{v['variant_id']}__{writer}__r{rep}"
            body = "\n\n".join(f"--- SPECIALIST CONTRIBUTION ---\n{t}"
                               for t in v["upstream"] if t)
            user = f"{body}\n\nQuestion:\n{get_case(v['case']).prompt}"
            txt = chat(writer, LEDGER_PROTOCOL, user,
                       temperature=0.6, max_tokens=8192)
            if not txt or not txt.strip():
                print(f"  EMPTY {rid} — recorded failed, not scored", flush=True)
                continue
            ans = answer_of(txt)
            fh.write(json.dumps({
                "run_id": rid, "prompt_id": v["case"],
                "variant_id": v["variant_id"], "writer": writer, "repeat": rep,
                "upstream": [t for t in v["upstream"] if t],
                "full_output": txt,
                "output": ans if ans is not None else "",
                "protocol_violation": ans is None,
            }, ensure_ascii=False) + "\n")
            fh.flush()
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)} {rid[:56]}"
                  f"{'  [VIOLATION]' if ans is None else ''} {el:.0f}s "
                  f"~{el/(i+1)*(len(todo)-i-1):.0f}s left", flush=True)
    print("cell31 runs complete")


def _load(path: Path, ledger: bool):
    from gst.instruments import RegexInstrument
    rx = RegexInstrument()
    out = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if ledger and d.get("protocol_violation"):
            continue
        if len(d.get("output", "")) < 500:
            continue
        up = "\n\n".join(d["upstream"])
        out.append({"key": (d["prompt_id"], d["variant_id"]),
                    "s": float(len(rx.families(up))),
                    "y": float(len(rx.families(d["output"]))),
                    "inv": len(rx.families(d["output"]) - rx.families(up)),
                    "writer": d["writer"]})
    return out


def _ols(rows):
    n = len(rows)
    mx = sum(r["s"] for r in rows) / n
    my = sum(r["y"] for r in rows) / n
    sxx = sum((r["s"] - mx) ** 2 for r in rows)
    if sxx == 0:
        return None
    slope = sum((r["s"] - mx) * (r["y"] - my) for r in rows) / sxx
    return slope, my - slope * mx


def stage_measure() -> None:
    from gst.stats import wilson_ci
    rng = random.Random(SEED)
    L = _load(RUNS_L, ledger=True)
    P = _load(RUNS_P, ledger=False)
    raw_l = [json.loads(x) for x in RUNS_L.read_text().splitlines() if x.strip()]
    viol = sum(1 for d in raw_l if d.get("protocol_violation"))
    print(f"Arm L (ledger):  {len(L)} usable of {len(raw_l)} "
          f"({viol} protocol violations)")
    print(f"Arm P (plain):   {len(P)} usable")

    fl, fp = _ols(L), _ols(P)
    if not fl or not fp:
        print("unidentifiable — stop")
        return
    print(f"  L: w={fl[0]:.3f}  c={fl[1]:+.3f}")
    print(f"  P: w={fp[0]:.3f}  c={fp[1]:+.3f}")
    print(f"  point deltas: dw={fl[0]-fp[0]:+.3f}  dc={fl[1]-fp[1]:+.3f}")

    # cluster bootstrap over shared variants
    keys = sorted({r["key"] for r in L} & {r["key"] for r in P})
    byL, byP = {}, {}
    for r in L:
        byL.setdefault(r["key"], []).append(r)
    for r in P:
        byP.setdefault(r["key"], []).append(r)
    print(f"  shared variants: {len(keys)}")
    dws, dcs = [], []
    for _ in range(DRAWS):
        samp = [keys[rng.randrange(len(keys))] for _ in keys]
        rl = [r for k in samp for r in byL.get(k, [])]
        rp = [r for k in samp for r in byP.get(k, [])]
        a, b = _ols(rl), _ols(rp)
        if a and b:
            dws.append(a[0] - b[0])
            dcs.append(a[1] - b[1])
    dws.sort()
    dcs.sort()
    lo_c, hi_c = dcs[int(.025 * len(dcs))], dcs[int(.975 * len(dcs))]
    lo_w, hi_w = dws[int(.025 * len(dws))], dws[int(.975 * len(dws))]
    print()
    print("=" * 70)
    print(f"P31.1 delta-c = {fl[1]-fp[1]:+.3f} [{lo_c:+.3f},{hi_c:+.3f}] -> "
          f"{'SUPPORTED (entirely below 0)' if hi_c < 0 else 'FALSIFIED (includes 0)'}")
    print(f"P31.2 delta-w = {fl[0]-fp[0]:+.3f} [{lo_w:+.3f},{hi_w:+.3f}] -> "
          f"{'FALSIFIED (entirely below 0 — bought by silence)' if hi_w < 0 else 'SUPPORTED'}")
    print("=" * 70)
    for name, arm in (("L", L), ("P", P)):
        z = [r["inv"] for r in arm if r["s"] == 0]
        k = sum(1 for v in z if v > 0)
        em = sum(r["y"] for r in arm) / len(arm)
        ci = wilson_ci(k, len(z)) if z else (float("nan"),) * 2
        print(f"  arm {name}: zero-supply invention {k}/{len(z)} "
              f"[{ci[0]:.3f},{ci[1]:.3f}] (no bar, underpowered); "
              f"mean emitted {em:.2f}")
    print(f"  ledger protocol-violation rate: {viol}/{len(raw_l)} "
          f"({viol/max(len(raw_l),1):.1%})")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "runs"
    {"runs": stage_runs, "measure": stage_measure}[stage]()
