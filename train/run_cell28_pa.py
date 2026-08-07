"""Cell 28 pre-analysis notes PA28.a / PA28.b — composition-law mechanism checks.

Registered in RUNBOOK_PAPER_HARDENING.md ("CELL 28 PRE-ANALYSIS NOTE")
BEFORE the Cell 28 measure stage ran. Mechanism checks, not verdict
criteria.

  PA28.a  Fit the two stages separately on stored ledger sections
          (l = w1*s + c1 on upstream->ledger; y = w2*l + c2 on
          ledger->answer; pooled compliant council-ledger runs from
          Cells 27 L1 + 28) and check the composite recovers the direct
          fit: w1*w2 inside the fitted w' CI, w2*c1 + c2 inside c' CI.
  PA28.b  Violation runs, scored on their un-delimited FULL text at zero
          supply, invent at the PROSE baseline rate (CI overlapping
          [0.27, 0.81]) rather than the ledger rate.

Run:  .venv/bin/python train/run_cell28_pa.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst.instruments import RegexInstrument               # noqa: E402
from gst.stats import bootstrap_ols, wilson_ci            # noqa: E402
from train.run_cell27_ledger import answer_of, ledger_of  # noqa: E402

MODES = ("c27-ledger", "c28-ledger-rep")
rx = RegexInstrument()


def load_runs():
    compliant, violations = [], []
    for p in sorted((ROOT / "bench/runs/imported").glob("*.json")):
        name = p.name
        if not any(f"__{m}.json" in name for m in MODES):
            continue
        d = json.loads(p.read_text())
        full = d.get("full_output") or d.get("final_output") or ""
        turns = (d.get("deliberation") or {}).get("turns") or []
        upstream = [t.get("output_text") or "" for t in turns]
        s = len(rx.families("\n\n".join(u for u in upstream if u)))
        if d.get("protocol_violation"):
            violations.append({"s": s, "full": full, "mode": d["mode"]})
            continue
        ans = answer_of(full)
        led = ledger_of(full)
        if ans is None or len(ans) < 500:
            continue
        compliant.append({"s": s, "l": len(rx.families(led)),
                          "y": len(rx.families(ans)), "mode": d["mode"]})
    return compliant, violations


def main() -> None:
    compliant, violations = load_runs()
    by_mode = {}
    for r in compliant:
        by_mode.setdefault(r["mode"], 0)
        by_mode[r["mode"]] += 1
    print(f"compliant runs: {len(compliant)} {by_mode}; "
          f"violation runs: {len(violations)}")

    print("=" * 74)
    print("PA28.a  STAGE DECOMPOSITION (pooled compliant council-ledger runs)")
    print("=" * 74)
    s = [float(r["s"]) for r in compliant]
    lv = [float(r["l"]) for r in compliant]
    y = [float(r["y"]) for r in compliant]
    try:
        f1 = bootstrap_ols(s, lv, seed=0)
        f2 = bootstrap_ols(lv, y, seed=0)
        fc = bootstrap_ols(s, y, seed=0)
    except ValueError as e:
        print(f"  stage fit unidentifiable: {e} — report and stop")
        return
    print(f"  stage 1 (upstream->ledger): w1={f1.slope:.3f} "
          f"[{f1.slope_ci[0]:.3f},{f1.slope_ci[1]:.3f}]  c1={f1.intercept:.3f} "
          f"[{f1.intercept_ci[0]:.3f},{f1.intercept_ci[1]:.3f}]")
    print(f"  stage 2 (ledger->answer):  w2={f2.slope:.3f} "
          f"[{f2.slope_ci[0]:.3f},{f2.slope_ci[1]:.3f}]  c2={f2.intercept:.3f} "
          f"[{f2.intercept_ci[0]:.3f},{f2.intercept_ci[1]:.3f}]")
    print(f"  direct composite:          w'={fc.slope:.3f} "
          f"[{fc.slope_ci[0]:.3f},{fc.slope_ci[1]:.3f}]  c'={fc.intercept:.3f} "
          f"[{fc.intercept_ci[0]:.3f},{fc.intercept_ci[1]:.3f}]")
    w_prod = f1.slope * f2.slope
    c_prod = f2.slope * f1.intercept + f2.intercept
    w_ok = fc.slope_ci[0] <= w_prod <= fc.slope_ci[1]
    c_ok = fc.intercept_ci[0] <= c_prod <= fc.intercept_ci[1]
    print(f"  predicted w1*w2 = {w_prod:.3f} -> inside w' CI: {w_ok}")
    print(f"  predicted w2*c1+c2 = {c_prod:.3f} -> inside c' CI: {c_ok}")
    print(f"  PA28.a: {'SUPPORTED' if w_ok and c_ok else 'FALSIFIED'}")

    print("=" * 74)
    print("PA28.b  VIOLATION MIXTURE (violation runs, full un-delimited text)")
    print("=" * 74)
    z = [(1 if rx.families(v["full"]) else 0) for v in violations if v["s"] == 0]
    if len(z) >= 5:
        ci = wilson_ci(sum(z), len(z))
        overlap = not (ci[1] < 0.27 or ci[0] > 0.81)
        print(f"  s=0 violation runs invent: {sum(z)}/{len(z)} "
              f"[{ci[0]:.2f},{ci[1]:.2f}] vs prose baseline [0.27,0.81] -> "
              f"{'SUPPORTED (reverts to prose register)' if overlap and sum(z) > 0 else ('overlap but zero events — inconclusive' if overlap else 'FALSIFIED')}")
    else:
        print(f"  s=0 violation runs n={len(z)} < 5 — NOT EVALUABLE (reported, "
              "not scored)")
    allv = [(len(rx.families(v['full'])), v['s']) for v in violations]
    if allv:
        print(f"  all violation runs (n={len(allv)}): mean emitted "
              f"{sum(a for a, _ in allv)/len(allv):.2f} families")


if __name__ == "__main__":
    main()
