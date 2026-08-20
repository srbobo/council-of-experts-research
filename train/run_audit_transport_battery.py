"""Transport-coefficient archival battery — four descriptive tests.

Registered scope: RUNBOOK_PAPER_HARDENING.md "TRANSPORT-COEFFICIENT
ARCHIVAL BATTERY". Post-hoc on Cell 30's existing 60 runs; licenses no new
claim. No generation, no judging.

  T1 functional form   quadratic term CI — can DEMOTE the headline
  T2 attenuation       reliability from two judges' independent supply
                       counts; disattenuated w as a band
  T3 convergent c      Cell 30 intercept vs Cell 38's zero-supply invention
  T4 per-family w      is the aggregate carried by one family?

Run:  .venv/bin/python train/run_audit_transport_battery.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst.stats import (bootstrap_ols, bootstrap_quadratic_ci,     # noqa: E402
                       ols, quadratic_fit)

C30 = ROOT / "bench" / "analysis" / "c30c31"
JUDGES = ["gpt-oss:20b", "qwen2.5:7b-instruct"]
FAMS = ("cutoff", "modeled", "jurisd", "hedging")
CELL38_INVENTION = (0.333, 0.138, 0.609)     # independent estimate of c


def per_judge_supply() -> dict[tuple[str, int], dict[str, int]]:
    """{(case, variant): {judge: supply count}} from the raw sentence labels.

    Reconstructs each judge's INDEPENDENT count on the upstream units, so
    reliability is measured rather than approximated by an agreement rate.
    """
    units = json.loads((C30 / "units.json").read_text())
    lab = json.loads((C30 / "labels.json").read_text())
    flat, owner = [], []
    for u in units:
        for s in u["sentences"]:
            flat.append(s)
            owner.append(u)
    out: dict[tuple[str, int], dict[str, int]] = {}
    for off in sorted({int(k.split("|")[1]) for k in lab}):
        per = {j: lab.get(f"{j}|{off}") for j in JUDGES}
        if any(v is None for v in per.values()):
            continue
        for pos in range(1, 11):
            i = off + pos - 1
            if i >= len(flat):
                break
            u = owner[i]
            if u["kind"] != "upstream":
                continue
            key = (u["key"][0], u["key"][1])
            rec = out.setdefault(key, {j: 0 for j in JUDGES})
            for j in JUDGES:
                d = per[j].get(str(pos))
                if d and any(d.get(f) for f in FAMS):
                    rec[j] += 1
    return out


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else float("nan")


def main() -> None:
    m = json.loads((C30 / "measured.json").read_text())
    P = m["P"]
    xs = [r["s"] for r in P]
    ys = [r["y"] for r in P]

    print("=" * 76)
    print("TRANSPORT-COEFFICIENT ARCHIVAL BATTERY (descriptive; licenses no claim)")
    print("=" * 76)
    fit = bootstrap_ols(xs, ys, draws=5000)
    blo, bhi = fit.slope_ci
    clo, chi = fit.intercept_ci
    print(f"BASELINE (as recorded): w = {fit.slope:.3f} [{blo:.3f},{bhi:.3f}]   "
          f"c = {fit.intercept:.3f} [{clo:.3f},{chi:.3f}]   n={len(P)}")
    print(f"  emission (silence check): mean y = {sum(ys)/len(ys):.3f}, "
          f"runs with y=0: {sum(1 for y in ys if y==0)}/{len(ys)}")

    # ---- T1 functional form -------------------------------------------
    print()
    print("T1 FUNCTIONAL FORM — is the linear law adequate?")
    a, b, c0 = quadratic_fit(xs, ys)
    qlo, qhi = bootstrap_quadratic_ci(xs, ys, draws=5000)
    excl = qlo > 0 or qhi < 0
    print(f"  quadratic term = {a:+.4f}  CI [{qlo:+.4f},{qhi:+.4f}]")
    print("  -> " + ("LINEAR FORM INADEQUATE — w is a local slope, not a law"
                     if excl else
                     "linear form adequate; no curvature detected"))

    # ---- T2 attenuation ------------------------------------------------
    print()
    print("T2 ATTENUATION — s is judge-MEASURED, so the slope is attenuated")
    sup = per_judge_supply()
    pairs = [(v[JUDGES[0]], v[JUDGES[1]]) for v in sup.values()]
    if len(pairs) >= 8:
        r = pearson([a for a, _ in pairs], [b for _, b in pairs])
        # Spearman-Brown: reliability of the SUM/mean of two raters
        rel = 2 * r / (1 + r) if r > 0 else float("nan")
        print(f"  per-judge supply counts on {len(pairs)} upstream units; "
              f"inter-judge r = {r:.3f}")
        print(f"  reliability of the 2-judge measure (Spearman-Brown) = {rel:.3f}")
        if rel and rel == rel and rel > 0:
            print(f"  disattenuated w = {fit.slope:.3f} / {rel:.3f} = "
                  f"{fit.slope/rel:.3f}")
            print(f"  BAND: observed {fit.slope:.3f} (attenuated, a LOWER bound) "
                  f"to {fit.slope/rel:.3f} (disattenuated)")
    else:
        print(f"  only {len(pairs)} units reconstructed — NOT EVALUABLE; "
              f"no approximation substituted")

    # ---- T3 convergent validity of c -----------------------------------
    print()
    print("T3 CONVERGENT VALIDITY OF c — two cells, one parameter")
    p38, l38, h38 = CELL38_INVENTION
    inside = clo <= p38 <= chi
    print(f"  Cell 30 intercept c = {fit.intercept:.3f} [{clo:.3f},{chi:.3f}]")
    print(f"  Cell 38 zero-supply invention = {p38:.3f} [{l38:.3f},{h38:.3f}] "
          f"(independent construction, different cell)")
    print(f"  -> Cell 38's estimate falls {'INSIDE' if inside else 'OUTSIDE'} "
          f"Cell 30's interval; intervals "
          f"{'overlap' if not (h38 < clo or l38 > chi) else 'do NOT overlap'}")
    print("  Convergent, not confirmatory: c's own CI spans zero, so this "
          "corroborates\n  the parameter's magnitude without establishing it.")

    # ---- T4 per-family w -----------------------------------------------
    print()
    print("T4 PER-FAMILY SLOPE — is the aggregate carried by one family?")
    print(f"  {'family':<10}{'w':>9}{'CI':>22}{'mean y':>9}")
    have = [f for f in FAMS if f in P[0]["per"]]
    for f in have:
        fy = [r["per"].get(f, 0) for r in P]
        ff = bootstrap_ols(xs, fy, draws=5000)
        flo, fhi = ff.slope_ci
        print(f"  {f:<10}{ff.slope:>9.3f}   [{flo:+.3f},{fhi:+.3f}]"
              f"{sum(fy)/len(fy):>9.3f}")
    print("  (supply s is the ALL-FAMILY count; these are per-family emission "
          "slopes\n  against total supply, so they sum toward the aggregate.)")


if __name__ == "__main__":
    main()
