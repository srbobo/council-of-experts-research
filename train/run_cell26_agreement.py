"""Cell 26 — agreement-conditioned transport.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 26 PRE-REGISTRATION".
Estimator, population and predictions FROZEN there. Zero model calls.

Per family f: k = number of seat texts independently raising f.
  T_f(k=1)  = P(f in output | exactly one seat raised it)
  T_f(k>=2) = P(f in output | corroborated)
If the writer performs any reliability weighting, corroborated content
should transport at a higher rate.

Run:  .venv/bin/python train/run_cell26_agreement.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst.adapters.coe import from_ledger          # noqa: E402
from gst.instruments import RegexInstrument       # noqa: E402
from gst.stats import wilson_ci                   # noqa: E402

SEED = 0
DRAWS = 5000
FAMS = ("modeled", "cutoff", "jurisd", "hedging")
VALIDITY = {"modeled": "validated (.92/.92)", "cutoff": "undercount (0/3)",
            "jurisd": "undercount (.30)", "hedging": "undercount+FP (.25/.65)"}
SWEEP_ARMS = {"arch-council", "arch-flat", "c17-suppress", "c19-gated", "c20-decide"}
TRIGGER_LIGHT = {"case_7_trigger_free_hybrid_work", "case_8_trigger_light_hand_hygiene",
                 "case_9_trigger_light_nda_clauses", "case_10_trigger_light_depreciation"}
FLOOR = 500

rx = RegexInstrument()
rng = random.Random(SEED)


def boot_diff(a: list[float], b: list[float]) -> tuple[float, float]:
    ds = []
    for _ in range(DRAWS):
        ma = sum(rng.choice(a) for _ in a) / len(a)
        mb = sum(rng.choice(b) for _ in b) / len(b)
        ds.append(ma - mb)
    ds.sort()
    return ds[int(0.025 * DRAWS)], ds[int(0.975 * DRAWS)]


def analyze(records, label: str) -> dict[str, tuple]:
    print("=" * 78)
    print(f"{label}  (n={len(records)} runs)")
    print("=" * 78)
    print(f"{'family':<9}{'n(k=1)':>8}{'T(k=1)':>9}{'n(k>=2)':>9}{'T(k>=2)':>9}"
          f"{'diff':>8}{'diff CI':>20}")
    out = {}
    for f in FAMS:
        one, multi = [], []
        by_k: dict[int, list[float]] = {}
        for r in records:
            k = sum(1 for t in r.upstream if f in rx.families(t))
            if k == 0:
                continue
            present = 1.0 if f in rx.families(r.output) else 0.0
            (one if k == 1 else multi).append(present)
            by_k.setdefault(min(k, 3), []).append(present)
        if len(one) < 10 or len(multi) < 10:
            print(f"{f:<9}{len(one):>8}{'—':>9}{len(multi):>9}{'—':>9}"
                  f"   too thin to compare   ({VALIDITY[f]})")
            out[f] = None
            continue
        t1, t2 = sum(one) / len(one), sum(multi) / len(multi)
        lo, hi = boot_diff(multi, one)
        out[f] = (t1, t2, lo, hi, len(one), len(multi))
        w1 = wilson_ci(int(sum(one)), len(one))
        w2 = wilson_ci(int(sum(multi)), len(multi))
        print(f"{f:<9}{len(one):>8}{t1:>9.3f}{len(multi):>9}{t2:>9.3f}"
              f"{t2-t1:>+8.3f}{f'[{lo:+.3f},{hi:+.3f}]':>20}   ({VALIDITY[f]})")
        ks = sorted(by_k)
        if len(ks) >= 3:
            curve = "  ".join(f"k={k}:{sum(v)/len(v):.2f}(n={len(v)})"
                              for k, v in sorted(by_k.items()))
            mono = all(sum(by_k[a])/len(by_k[a]) <= sum(by_k[b])/len(by_k[b]) + 0.05
                       for a, b in zip(ks, ks[1:], strict=False))
            print(f"{'':9}dose: {curve}   monotone={mono}")
    print()
    return out


def main() -> None:
    recs = [r for r in from_ledger(ROOT / "bench/runs/imported")
            if len(r.output) >= FLOOR and len(r.upstream) >= 2]
    print(f"population: {len(recs)} usable multi-seat runs "
          f"(cell25 MoA excluded per registration)\n")

    primary = analyze(recs, "PRIMARY — all multi-seat runs")
    sweep = [r for r in recs if r.condition in SWEEP_ARMS]
    analyze(sweep, "SECONDARY (a) — 5-arm sweep population, single writer")
    heavy = [r for r in recs if r.prompt_id not in TRIGGER_LIGHT]
    light = [r for r in recs if r.prompt_id in TRIGGER_LIGHT]
    analyze(heavy, "SECONDARY (b1) — trigger-heavy cases")
    analyze(light, "SECONDARY (b2) — trigger-light cases")

    print("=" * 78)
    m = primary.get("modeled")
    if m is None:
        print("P26.1: NOT EVALUABLE — modeled strata too thin; report and stop")
        return
    t1, t2, lo, hi, n1, n2 = m
    if lo > 0:
        print(f"P26.1 SUPPORTED — corroborated modeled content transports at a "
              f"higher rate ({t2:.3f} vs {t1:.3f}, diff CI [{lo:+.3f},{hi:+.3f}]). "
              "The writer performs at least crude agreement weighting; amend "
              "'nothing sets the calibration' per the registered consequence.")
    elif hi < 0:
        print(f"P26.1 FALSIFIED, INVERTED — corroborated content transports at a "
              f"LOWER rate ({t2:.3f} vs {t1:.3f}, CI [{lo:+.3f},{hi:+.3f}]). "
              "Report as-is; do not narrativize beyond the registered options.")
    else:
        print(f"P26.1 FALSIFIED — no detectable agreement weighting "
              f"({t2:.3f} vs {t1:.3f}, diff CI [{lo:+.3f},{hi:+.3f}] includes 0). "
              "The writer ignores the one reliability signal the architecture "
              "uniquely provides; 'surfaces evidence it cannot use' is now a "
              "measurement, not rhetoric.")
    comp1, comp2 = [], []
    for f in FAMS:
        v = primary.get(f)
        if v:
            comp1 += [v[0]] * 0  # composite handled below from raw pools
    # P26.2 composite: pool per-run flags across families
    one_c, multi_c = [], []
    for r in recs:
        for f in FAMS:
            k = sum(1 for t in r.upstream if f in rx.families(t))
            if k == 0:
                continue
            present = 1.0 if f in rx.families(r.output) else 0.0
            (one_c if k == 1 else multi_c).append(present)
    lo, hi = boot_diff(multi_c, one_c)
    print(f"P26.2 (composite, secondary): T(k=1)={sum(one_c)/len(one_c):.3f} "
          f"(n={len(one_c)}), T(k>=2)={sum(multi_c)/len(multi_c):.3f} "
          f"(n={len(multi_c)}), diff CI [{lo:+.3f},{hi:+.3f}] — interpret only "
          "beside per-family validity.")


if __name__ == "__main__":
    main()
