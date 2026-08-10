"""Cell 30 — the de-scaffolded law, measured with the Cell IV instrument.

Deviation: same as Cell 31's (recorded 2026-08-09). Cell 30 registered
regex-free judge measurement at DOCUMENT level, which failed its own P30.0
gate. The validated replacement is batched SENTENCE judging, and the
measured variable is the count of qualification-bearing sentences. The
frozen bars survive as sign tests.

Run:  .venv/bin/python train/run_measure_c30_law.py
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst.instruments import RegexInstrument       # noqa: E402  (P30.4 only)
from gst.stats import bootstrap_ols, wilson_ci    # noqa: E402
from train.cell23_presence_calib import JUDGES     # noqa: E402
from train.run_cellIV_batchjudge import ALL_FAMS   # noqa: E402

OUT = ROOT / "bench" / "analysis" / "c30c31"
B = 10
SEED = 0
SCORED = ("modeled", "jurisd", "hedging")
rng = random.Random(SEED)


def main() -> None:
    units = json.loads((OUT / "units.json").read_text())
    cache = json.loads((OUT / "labels.json").read_text())
    flat = [(u["id"], i) for u in units for i in range(len(u["sentences"]))]

    # ---- P30.0: judge-judge agreement ON THIS CORPUS (pre both-agree rule)
    agree = tot = 0
    labels = {u["id"]: [None] * len(u["sentences"]) for u in units}
    for start in range(0, len(flat), B):
        chunk = flat[start:start + B]
        vs = [cache.get(f"{j}|{start}") for j in JUDGES]
        if any(v is None for v in vs):
            continue
        for k, (uid, idx) in enumerate(chunk):
            a, b = (v.get(str(k + 1)) for v in vs)
            if not a or not b:
                continue
            for f in SCORED:
                tot += 1
                agree += int(a[f] == b[f])
            labels[uid][idx] = {f: bool(a[f] and b[f]) for f in ALL_FAMS}
    jj = agree / tot if tot else float("nan")
    print("=" * 74)
    print(f"P30.0 judge-judge agreement on the Cell 30 corpus: {jj:.3f} "
          f"({agree}/{tot} scored-family decisions)")
    print(f"P30.0: {'PASS' if jj >= 0.70 else 'FAIL'} (bar 0.70) — the "
          "document-level protocol scored 0.622 and failed; this is the "
          "validated sentence-level protocol on the same corpus")
    if jj < 0.70:
        return

    def count(uid):
        lab = [x for x in labels[uid] if x is not None]
        return sum(1 for x in lab if any(x[f] for f in SCORED))

    supply = {tuple(u["key"]): count(u["id"])
              for u in units if u["kind"] == "upstream"}
    rows = []
    for u in units:
        if u["kind"] != "output" or u["arm"] != "P":
            continue
        s = supply.get(tuple(u["key"]))
        if s is None:
            continue
        rows.append({"s": float(s), "y": float(count(u["id"])),
                     "writer": u["writer"], "id": u["id"]})

    dist = {}
    for r in rows:
        dist[int(r["s"])] = dist.get(int(r["s"]), 0) + 1
    print()
    print("=" * 74)
    print("SUPPLY DISTRIBUTION under the validated instrument")
    print(f"  {dict(sorted(dist.items()))}")
    print(f"  distinct levels: {len(dist)}   n={len(rows)}")
    zero = [r for r in rows if r["s"] == 0]
    print(f"  ZERO-SUPPLY RUNS: {len(zero)}  (registration expected ~36 from "
          "regex-driven ablation)")

    # ---- P30.1 the law
    print()
    print("=" * 74)
    if len(dist) < 3:
        print("P30.1 NOT EVALUABLE — fewer than 3 supply levels")
        return
    f = bootstrap_ols([r["s"] for r in rows], [r["y"] for r in rows], seed=SEED)
    print(f"P30.1 w = {f.slope:.3f} [{f.slope_ci[0]:.3f},{f.slope_ci[1]:.3f}]   "
          f"c = {f.intercept:.3f} [{f.intercept_ci[0]:.3f},{f.intercept_ci[1]:.3f}]"
          f"   n={f.n}")
    print(f"P30.1: {'SUPPORTED (w CI excludes 0)' if f.slope_ci[0] > 0 else 'FALSIFIED (w CI includes 0)'}")

    # ---- P30.2 invention at zero supply
    print()
    print("=" * 74)
    if len(zero) >= 8:
        k = sum(1 for r in zero if r["y"] > 0)
        ci = wilson_ci(k, len(zero))
        print(f"P30.2 zero-supply invention {k}/{len(zero)} "
              f"[{ci[0]:.3f},{ci[1]:.3f}] -> "
              f"{'SUPPORTED' if ci[0] > 0 else 'FALSIFIED'}")
    else:
        print(f"P30.2 NOT EVALUABLE — {len(zero)} zero-supply runs, below any "
              "usable floor. The regex-driven ablation did NOT produce "
              "zero-supply text under the validated instrument.")

    # ---- P30.3 second writer
    print()
    print("=" * 74)
    for w in sorted({r["writer"] for r in rows}):
        sub = [r for r in rows if r["writer"] == w]
        lv = len({int(r["s"]) for r in sub})
        if lv < 3 or len(sub) < 10:
            print(f"P30.3 {w:<18} NOT EVALUABLE (levels={lv}, n={len(sub)})")
            continue
        fw = bootstrap_ols([r["s"] for r in sub], [r["y"] for r in sub], seed=SEED)
        z = [r for r in sub if r["s"] == 0]
        print(f"P30.3 {w:<18} w={fw.slope:.3f} "
              f"[{fw.slope_ci[0]:.3f},{fw.slope_ci[1]:.3f}]  c={fw.intercept:+.3f}"
              f"  n={len(sub)}  zero-supply runs={len(z)}")
    print("      (P30.3 required BOTH a w CI excluding 0 and a zero-supply "
          "invention CI excluding 0; the latter is unavailable — see P30.2)")

    # ---- P30.4 instrument divergence
    print()
    print("=" * 74)
    rx = RegexInstrument()
    raw = {json.loads(x)["run_id"]: json.loads(x) for x in
           (ROOT / "bench/runs/cell30_descaffold.jsonl").read_text().splitlines()
           if x.strip()}
    jr = rr = n = 0
    for r in rows:
        rid = r["id"].split("::", 1)[1]
        d = raw.get(rid)
        if not d:
            continue
        n += 1
        up = rx.families("\n\n".join(d["upstream"]))
        jr += int(r["y"] > 0)
        rr += int(bool(rx.families(d["output"]) - up))
    print(f"P30.4 emission/invention rate: regex {rr/n:.3f} vs judge "
          f"{jr/n:.3f}  (n={n})")
    print(f"P30.4: {'SUPPORTED (regex under-counts)' if rr < jr else 'FALSIFIED'}"
          "   [regex reported for this comparison only, as registered]")


if __name__ == "__main__":
    main()
