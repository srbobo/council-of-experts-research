"""Cell 24 — per-family robustness re-analysis on the validated channel.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 24 PRE-REGISTRATION".
Estimator, populations, seeds and bars are FROZEN there. Zero model calls.

Per-family quantities (the composite OLS is unidentifiable per family):
  T_f = P(f in output | f raised upstream)      preservation probability
  I_f = P(f in output | f not raised)           invention probability
  D_f = T_f - I_f                               discrimination

Run:  .venv/bin/python train/run_cell24_family.py
"""
from __future__ import annotations

import collections
import json
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
FAMS = ("modeled", "cutoff", "jurisd", "hedging")   # modeled first: primary
VALIDITY = {"modeled": "sens .92 prec .92 (validated)",
            "cutoff": "sens 0/3 (undercount, unmeasurable)",
            "jurisd": "sens .30 (undercount)",
            "hedging": "sens .25 prec .65 (undercount + FP-prone)"}
SWEEP_ARMS = ["arch-council", "arch-flat", "c17-suppress", "c19-gated", "c20-decide"]
FLOOR = 500

rx = RegexInstrument()
rng = random.Random(SEED)


def boot_ci(vals: list[float], draws: int = DRAWS) -> tuple[float, float]:
    ms = []
    for _ in range(draws):
        ms.append(sum(rng.choice(vals) for _ in vals) / len(vals))
    ms.sort()
    return ms[int(0.025 * draws)], ms[int(0.975 * draws)]


def boot_diff(a: list[float], b: list[float], draws: int = DRAWS) -> tuple[float, float]:
    ds = []
    for _ in range(draws):
        ds.append(sum(rng.choice(a) for _ in a) / len(a)
                  - sum(rng.choice(b) for _ in b) / len(b))
    ds.sort()
    return ds[int(0.025 * draws)], ds[int(0.975 * draws)]


def fam_flags(rec) -> tuple[set[str], set[str]]:
    up = rx.families(rec.upstream_text)
    out = rx.families(rec.output)
    return up, out


# ---------------------------------------------------------------- P24.1
recs = [r for r in from_ledger(ROOT / "bench/runs/imported") if len(r.output) >= FLOOR]
print(f"population: {len(recs)} usable runs\n")
print("=" * 78)
print("P24.1  PER-FAMILY TRANSMISSION (full population)")
print("=" * 78)
print(f"{'family':<9}{'raised n':>9}{'T_f':>7}{'CI':>16}{'I_f':>7}{'CI':>16}{'D_f':>7}")
d_ci = {}
for f in FAMS:
    t_flags, i_flags = [], []
    for r in recs:
        up, out = fam_flags(r)
        (t_flags if f in up else i_flags).append(1.0 if f in out else 0.0)
    T = sum(t_flags) / len(t_flags) if t_flags else float("nan")
    Ival = sum(i_flags) / len(i_flags) if i_flags else float("nan")
    tci = wilson_ci(int(sum(t_flags)), len(t_flags))
    ici = wilson_ci(int(sum(i_flags)), len(i_flags))
    # bootstrap D
    ds = []
    for _ in range(DRAWS):
        tb = sum(rng.choice(t_flags) for _ in t_flags) / len(t_flags)
        ib = sum(rng.choice(i_flags) for _ in i_flags) / len(i_flags)
        ds.append(tb - ib)
    ds.sort()
    d_ci[f] = (ds[int(0.025 * DRAWS)], ds[int(0.975 * DRAWS)])
    print(f"{f:<9}{len(t_flags):>9}{T:>7.3f}"
          f"{f'[{tci[0]:.2f},{tci[1]:.2f}]':>16}{Ival:>7.3f}"
          f"{f'[{ici[0]:.2f},{ici[1]:.2f}]':>16}{T-Ival:>7.3f}")
    print(f"{'':9}D_f CI [{d_ci[f][0]:.3f},{d_ci[f][1]:.3f}]   ({VALIDITY[f]})")
dm_lo, dm_hi = d_ci["modeled"]
if dm_lo > 0.352 and (dm_lo + dm_hi) / 2 >= 0.50:
    verdict = "SUPPORTED (attenuation confirmed)"
elif dm_hi < 0.352:
    verdict = ("FALSIFIED — REVERSED (validated channel shows LOWER "
               "discrimination than the composite; withdraw the caveat)")
else:
    verdict = "FALSIFIED (CI includes 0.352; attenuation not demonstrated)"
print(f"\nP24.1 (registered bar: D_modeled >= 0.50, CI excluding 0.352): {verdict}")
print(f"  D_modeled CI [{dm_lo:.3f},{dm_hi:.3f}] vs composite w=0.352")

# ---------------------------------------------------------------- P24.2/24.3
print()
print("=" * 78)
print("P24.2  SWEEP ARMS, MODELED-ONLY INVENTION (9 shared cases, n=45)")
print("=" * 78)
by = collections.defaultdict(list)
for r in recs:
    by[r.condition].append(r)
shared = set.intersection(*[{r.prompt_id for r in by[a]} for a in SWEEP_ARMS])
arm_flags = {}
arm_zero_flags = {}
for arm in SWEEP_ARMS:
    rs = [r for r in by[arm] if r.prompt_id in shared]
    inv, inv_zero = [], []
    for r in rs:
        up, out = fam_flags(r)
        if "modeled" not in up:
            v = 1.0 if "modeled" in out else 0.0
            inv.append(v)
            inv_zero.append(v)
        # runs where modeled WAS raised cannot invent modeled; excluded from I
    arm_flags[arm] = inv
    arm_zero_flags[arm] = inv_zero
base = arm_flags["arch-council"]
print(f"  arch-council   I_modeled = {sum(base)/len(base):.3f}  (n={len(base)} eligible)")
p242_ok = True
for arm in SWEEP_ARMS[1:]:
    v = arm_flags[arm]
    lo, hi = boot_diff(v, base)
    sep = lo > 0 or hi < 0
    if sep:
        p242_ok = False
    print(f"  {arm:<14} I_modeled = {sum(v)/len(v):.3f}  (n={len(v)})  "
          f"diff CI [{lo:+.3f},{hi:+.3f}]  {'SEPARATES' if sep else 'null holds'}")
print(f"P24.2: {'SUPPORTED (all nulls hold modeled-only)' if p242_ok else 'FALSIFIED'}")
lo, hi = boot_diff(arm_flags["c17-suppress"], base)
print(f"P24.3 (c17 vs council, modeled invention on eligible stratum): "
      f"diff CI [{lo:+.3f},{hi:+.3f}] -> "
      f"{'SUPPORTED (no separation)' if not (lo > 0 or hi < 0) else 'FALSIFIED'}")

# ---------------------------------------------------------------- P24.4
print()
print("=" * 78)
print("P24.4  CELL 14 DECOMPOSITION, MODELED PRESENCE (cases 8/9/10, raw ledger)")
print("=" * 78)
CASES14 = {"case_8_trigger_light_hand_hygiene", "case_9_trigger_light_nda_clauses",
           "case_10_trigger_light_depreciation"}
raw = collections.defaultdict(list)
for p in sorted((ROOT / "bench/runs/imported").glob("*.json")):
    try:
        d = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        continue
    if d.get("case_id") in CASES14 and d.get("source") == "cell14" and \
            d.get("mode") in ("arch-council", "arch-single-spec"):
        out = d.get("final_output") or ""
        if len(out) >= FLOOR:
            raw[d["mode"]].append(1.0 if "modeled" in rx.families(out) else 0.0)
for mode, v in sorted(raw.items()):
    ci = wilson_ci(int(sum(v)), len(v))
    print(f"  {mode:<18} modeled presence {sum(v)/len(v):.3f} "
          f"[{ci[0]:.2f},{ci[1]:.2f}]  (n={len(v)})")
if len(raw) == 2:
    lo, hi = boot_diff(raw["arch-council"], raw["arch-single-spec"])
    council_lower = hi < 0
    print(f"  council - single diff CI [{lo:+.3f},{hi:+.3f}]")
    print(f"P24.4: {'FALSIFIED (council separates BELOW)' if council_lower else 'SUPPORTED (council not better on the clean family)'}")
else:
    print("P24.4: population not found as registered — report and stop")
