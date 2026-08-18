"""Cell 43-R — disjoint-family judge replication of Cell 43.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 43-R PRE-REGISTRATION".

  pilot    20 seeded C1 pairs x both orderings per candidate. Reports parse
           rate and decisive rate ONLY — deliberately never computes which
           side wins, so selection cannot be direction-shopping.
  full     all 378 pairs for the judge named in selected.json.
  measure  direction agreement with the primary judge (P43R.1) + P43R.2.

Run:  .venv/bin/python train/run_cell43R_replication.py pilot
      .venv/bin/python train/run_cell43R_replication.py full
      .venv/bin/python train/run_cell43R_replication.py measure
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell43_preference import (COMPARISONS, PAIR_ARMS, REPEATS,  # noqa: E402
                                         cases41, judge_pair, load_outputs,
                                         _decide, OUT)

R_OUT = ROOT / "bench" / "analysis" / "cell43R"
CANDIDATES = ["phi4:14b", "deepseek-r1:7b", "qwen3-vl:30b-a3b-instruct"]
PILOT_N, PARSE_GATE, DECISIVE_GATE = 20, 0.90, 0.20
PRIMARY = "gpt-oss:20b"


def pilot_pairs():
    rng = random.Random(431)
    all_pairs = [(c, r) for c in cases41() for r in range(REPEATS)]
    return rng.sample(all_pairs, PILOT_N)


def stage_pilot() -> None:
    from examples.test_cases import get_case
    R_OUT.mkdir(parents=True, exist_ok=True)
    outs = load_outputs()
    cpath = R_OUT / "pilot_cache.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    pairs = pilot_pairs()
    a1, a2 = PAIR_ARMS["C1"]
    results = {}
    for judge in CANDIDATES:
        t0 = time.time()
        parsed = dec = 0
        for c, r in pairs:
            q = get_case(c).prompt
            x, y = outs[(a1, c, r)], outs[(a2, c, r)]
            f = judge_pair(judge, q, x, y, cache, f"{judge}|P|{c}|{r}|fwd")
            v = judge_pair(judge, q, y, x, cache, f"{judge}|P|{c}|{r}|rev")
            cpath.write_text(json.dumps(cache))
            if f is not None and v is not None:
                parsed += 1
                # decisive = same SIDE both orderings; computed WITHOUT
                # recording which side, per the registered blinding rule
                dec += (f != v)
        el = time.time() - t0
        results[judge] = {"parse": parsed / PILOT_N, "decisive": dec / PILOT_N,
                          "sec_per_pair": el / PILOT_N}
        print(f"  {judge:<28} parse {parsed}/{PILOT_N}  decisive {dec}/{PILOT_N}"
              f"  ({el/PILOT_N:.0f}s/pair)", flush=True)

    eligible = {j: v for j, v in results.items()
                if v["parse"] >= PARSE_GATE and v["decisive"] >= DECISIVE_GATE}
    print()
    if not eligible:
        print("ALL CANDIDATES FAIL the registered gates — replication NOT "
              "EVALUABLE; Cell 43 remains single-judge.")
        (R_OUT / "selected.json").write_text(json.dumps({"selected": None,
                                                         "pilot": results}))
        return
    sel = max(eligible, key=lambda j: eligible[j]["decisive"])
    print(f"SELECTED (highest decisive rate, blind to direction): {sel}")
    (R_OUT / "selected.json").write_text(json.dumps({"selected": sel,
                                                     "pilot": results}))


def stage_full() -> None:
    from examples.test_cases import get_case
    sel = json.loads((R_OUT / "selected.json").read_text())["selected"]
    if not sel:
        raise SystemExit("No selected judge — pilot failed all candidates.")
    outs = load_outputs()
    cpath = R_OUT / "judgments.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    jobs = [(comp, c, r) for comp in COMPARISONS
            for c in cases41() for r in range(REPEATS)]
    print(f"cell43R full: judge {sel}, {len(jobs)} pairs x 2 orderings", flush=True)
    t0 = time.time()
    for i, (comp, c, r) in enumerate(jobs):
        a1, a2 = PAIR_ARMS[comp]
        q = get_case(c).prompt
        x, y = outs[(a1, c, r)], outs[(a2, c, r)]
        judge_pair(sel, q, x, y, cache, f"{sel}|{comp}|{c}|{r}|fwd")
        judge_pair(sel, q, y, x, cache, f"{sel}|{comp}|{c}|{r}|rev")
        cpath.write_text(json.dumps(cache))
        if (i + 1) % 20 == 0:
            el = time.time() - t0
            print(f"  {i+1}/{len(jobs)} {el:.0f}s "
                  f"~{el/(i+1)*(len(jobs)-i-1):.0f}s left", flush=True)
    print("cell43R full complete")


def stage_measure() -> None:
    rng = random.Random(0)
    sel = json.loads((R_OUT / "selected.json").read_text())["selected"]
    rc = json.loads((R_OUT / "judgments.json").read_text())
    pc = json.loads((OUT / "judgments.json").read_text())
    cs = cases41()

    def share_ci(cache, judge, comp):
        by = {}
        for c in cs:
            for r in range(REPEATS):
                d = _decide(cache, judge, comp, c, r)
                if d in ("S1", "S2"):
                    by.setdefault(c, []).append(d == "S1")
        pool = sorted(by)
        dec = [b for c in pool for b in by[c]]
        if not dec:
            return float("nan"), (float("nan"),) * 2, 0
        ds = []
        for _ in range(5000):
            s = [pool[rng.randrange(len(pool))] for _ in pool]
            w = [b for c in s for b in by[c]]
            if w:
                ds.append(sum(w) / len(w))
        ds.sort()
        return (sum(dec) / len(dec),
                (ds[int(.025 * len(ds))], ds[int(.975 * len(ds))]), len(dec))

    def side(ci):
        return "S1" if ci[0] > 0.5 else "S2" if ci[1] < 0.5 else "spans"

    print("=" * 78)
    print(f"CELL 43-R — replication judge: {sel}")
    print("=" * 78)
    labels = {"C1": "MoA vs direct", "C2": "form-X vs control",
              "C3": "form-Y vs control"}
    print("P43R.2 RAW TABLE (mandatory, before any verdict)")
    from collections import Counter
    raw = Counter(v for v in rc.values() if v)
    print(f"  raw position split: A {raw.get('A',0)} / B {raw.get('B',0)}")
    agree_all = True
    rows = []
    for comp in COMPARISONS:
        n_all = tie = quar = 0
        for c in cs:
            for r in range(REPEATS):
                d = _decide(rc, sel, comp, c, r)
                n_all += 1
                tie += (d == "TIE")
                quar += (d is None)
        pt, ci, n = share_ci(rc, sel, comp)
        ppt, pci, pn = share_ci(pc, PRIMARY, comp)
        s, ps = side(ci), side(pci)
        verdict = ("AGREES" if s == ps and s != "spans" else
                   "NOT REPLICATED AT THIS POWER" if s == "spans" else
                   "CONTRADICTS")
        agree_all &= (verdict == "AGREES")
        rows.append((comp, verdict))
        print(f"  {comp} {labels[comp]:<20} decisive {n:>3} tie {tie:>3} "
              f"quar {quar:>2}   share {pt:.3f} [{ci[0]:.3f},{ci[1]:.3f}]"
              f"   primary {ppt:.3f} [{pci[0]:.3f},{pci[1]:.3f}]  -> {verdict}")
    print()
    if any(v == "CONTRADICTS" for _, v in rows):
        print("P43R.1: FALSIFIED — at least one comparison lands on the "
              "opposite side of indifference.")
    elif agree_all:
        print("P43R.1: SUPPORTED — all three comparisons agree in direction "
              "across judge families.")
    else:
        part = [c for c, v in rows if v == "AGREES"]
        print(f"P43R.1: PARTIAL — direction agreement on {part or 'none'}; "
              f"the rest not replicated at this power (spans 0.5, distinct "
              f"from contradiction, as registered).")
    (R_OUT / "measured.json").write_text(json.dumps(
        {"judge": sel, "rows": rows}))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    {"pilot": stage_pilot, "full": stage_full, "measure": stage_measure}[stage]()
