"""Cell 29 — phenomena atlas: corpus-wide measurement of observed regularities.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 29 PRE-REGISTRATION".
Estimators and bars FROZEN there. Zero model calls.

Run:  .venv/bin/python train/run_cell29_atlas.py
"""
from __future__ import annotations

import collections
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst.adapters import FieldMap, from_jsonl             # noqa: E402
from gst.adapters.coe import from_ledger                  # noqa: E402
from gst.instruments import RegexInstrument               # noqa: E402
from gst.measure import shrinkage                         # noqa: E402

SEED = 0
FAMS = ("modeled", "cutoff", "jurisd", "hedging")
LEDGER_REGISTER = {"c27-ledger", "c28-ledger-rep"}
FLOOR = 500
rx = RegexInstrument()
rng = random.Random(SEED)


def load_all():
    recs = [r for r in from_ledger(ROOT / "bench/runs/imported")
            if len(r.output) >= FLOOR]
    fmap = FieldMap(upstream="upstream", output="output", prompt_id="prompt_id",
                    run_id="run_id", condition="condition", writer_id="writer_id")
    for path, cond in ((ROOT / "bench/runs/cell25_moa.jsonl", "moa-naive"),
                       (ROOT / "bench/runs/cell27_ledger_moa.jsonl", "moa-ledger")):
        if path.exists():
            for r in from_jsonl(path, fmap):
                if len(r.output) >= FLOOR and r.output.strip():
                    r.condition = cond
                    recs.append(r)
    return recs


def arm_fits(recs):
    """Per-arm shrinkage fits meeting the frozen inclusion rule."""
    by = collections.defaultdict(list)
    for r in recs:
        by[r.condition].append(r)
    out = {}
    for arm, rs in sorted(by.items()):
        if len(rs) < 30:
            continue
        sh = shrinkage(rs, seed=SEED)
        if not (sh.identifiable and sh.w_ci and sh.c_ci):
            continue
        se_w = (sh.w_ci[1] - sh.w_ci[0]) / 3.92
        se_c = (sh.c_ci[1] - sh.c_ci[0]) / 3.92
        out[arm] = {"w": sh.w, "se_w": se_w, "c": sh.c, "se_c": se_c,
                    "n": sh.n_runs, "weak": sh.weakly_identified,
                    "extrap": sh.c_extrapolated}
    return out


def dl_meta(ests, ses):
    """DerSimonian-Laird random effects: (mu, se_mu, tau, PI_lo, PI_hi)."""
    k = len(ests)
    v = [s * s for s in ses]
    w_fe = [1 / x for x in v]
    mu_fe = sum(wi * e for wi, e in zip(w_fe, ests, strict=True)) / sum(w_fe)
    q = sum(wi * (e - mu_fe) ** 2 for wi, e in zip(w_fe, ests, strict=True))
    c_denom = sum(w_fe) - sum(x * x for x in w_fe) / sum(w_fe)
    tau2 = max(0.0, (q - (k - 1)) / c_denom) if c_denom > 0 else 0.0
    w_re = [1 / (vi + tau2) for vi in v]
    mu = sum(wi * e for wi, e in zip(w_re, ests, strict=True)) / sum(w_re)
    se_mu = math.sqrt(1 / sum(w_re))
    pi_half = 1.96 * math.sqrt(tau2 + se_mu * se_mu)
    return mu, se_mu, math.sqrt(tau2), mu - pi_half, mu + pi_half


def inv_count(r) -> int:
    up = rx.families(r.upstream_text) if r.upstream else set()
    return len(rx.families(r.output) - up)


def main() -> None:
    recs = load_all()
    print(f"corpus: {len(recs)} usable runs\n")
    fits = arm_fits(recs)
    print(f"arms qualifying for meta-analysis: {len(fits)}")
    for a, f in sorted(fits.items()):
        print(f"  {a:<22} w={f['w']:+.3f}±{f['se_w']:.3f}  c={f['c']:+.3f}"
              f"±{f['se_c']:.3f}  n={f['n']}"
              f"{'  [weak]' if f['weak'] else ''}{'  [extrap]' if f['extrap'] else ''}")

    # ------------------------------------------------------------- P29.1
    print()
    print("=" * 74)
    print("P29.1  THE w-BAND (DerSimonian-Laird random effects, all arms)")
    print("=" * 74)
    ws = [f["w"] for f in fits.values()]
    ses = [f["se_w"] for f in fits.values()]
    mu, se_mu, tau, pi_lo, pi_hi = dl_meta(ws, ses)
    mu_lo, mu_hi = mu - 1.96 * se_mu, mu + 1.96 * se_mu
    print(f"  mu_w = {mu:.3f} [{mu_lo:.3f},{mu_hi:.3f}]   tau = {tau:.3f}")
    print(f"  95% prediction interval for a NEW arm: [{pi_lo:.3f},{pi_hi:.3f}]")
    ok_mu = 0.15 <= mu_lo and mu_hi <= 0.50
    ok_pi = pi_hi < 0.85
    print(f"  P29.1: mu CI within [0.15,0.50]: {ok_mu}; PI upper < 0.85: {ok_pi} "
          f"-> {'SUPPORTED' if ok_mu and ok_pi else 'FALSIFIED'}")

    # ------------------------------------------------------------- P29.2
    print()
    print("=" * 74)
    print("P29.2  PROMPT HETEROGENEITY (one-way ICC over repeated cells)")
    print("=" * 74)
    cells = collections.defaultdict(list)
    for r in recs:
        if r.prompt_id:
            cells[(r.prompt_id, r.condition, r.writer_id)].append(float(inv_count(r)))
    rep = {k: v for k, v in cells.items() if len(v) >= 2}

    def icc(groups):
        k = len(groups)
        ns = [len(g) for g in groups]
        n_tot = sum(ns)
        gm = sum(sum(g) for g in groups) / n_tot
        ss_b = sum(len(g) * (sum(g) / len(g) - gm) ** 2 for g in groups)
        ss_w = sum(sum((x - sum(g) / len(g)) ** 2 for x in g) for g in groups)
        ms_b = ss_b / (k - 1)
        ms_w = ss_w / (n_tot - k) if n_tot > k else 0.0
        n0 = (n_tot - sum(n * n for n in ns) / n_tot) / (k - 1)
        return (ms_b - ms_w) / (ms_b + (n0 - 1) * ms_w) if ms_b + (n0 - 1) * ms_w > 0 else 0.0

    groups = list(rep.values())
    point = icc(groups)
    boots = []
    for _ in range(2000):
        sample = [groups[rng.randrange(len(groups))] for _ in groups]
        boots.append(icc(sample))
    boots.sort()
    lo, hi = boots[50], boots[1949]
    print(f"  cells with >= 2 runs: {len(rep)} (runs {sum(len(v) for v in rep.values())})")
    print(f"  ICC = {point:.3f} [{lo:.3f},{hi:.3f}]")
    print(f"  P29.2: CI lower > 0 -> {'SUPPORTED' if lo > 0 else 'FALSIFIED'}")
    disp = []
    by_arm_s = collections.defaultdict(list)
    for r in recs:
        s = len(rx.families(r.upstream_text)) if r.upstream else 0
        by_arm_s[(r.condition, s)].append(float(inv_count(r)))
    for (_arm, _s), v in by_arm_s.items():
        if len(v) >= 15:
            m = sum(v) / len(v)
            if m > 0:
                var = sum((x - m) ** 2 for x in v) / (len(v) - 1)
                disp.append(var / m)
    disp.sort()
    if disp:
        print(f"  dispersion indices (descriptive, no bar): n={len(disp)} cells, "
              f"median {disp[len(disp)//2]:.2f}, range [{disp[0]:.2f},{disp[-1]:.2f}]")

    # ------------------------------------------------------------- P29.3
    print()
    print("=" * 74)
    print("P29.3  SLOPE DECOMPOSITION (pooled qualifying-arm runs)")
    print("=" * 74)
    pool = [r for r in recs if r.condition in fits]
    # Precompute features ONCE; the bootstrap resamples tuples, never re-runs
    # the instrument (the first version re-scored the corpus per draw).
    feats = []
    for r in pool:
        up = rx.families(r.upstream_text)
        out = rx.families(r.output)
        feats.append((float(len(up)), {f: 1.0 if f in out else 0.0 for f in FAMS}))

    def decompose(rows):
        s = [a for a, _ in rows]
        ms = sum(s) / len(s)
        var_s = sum((x - ms) ** 2 for x in s) / (len(s) - 1)
        shares = {}
        for f in FAMS:
            yf = [b[f] for _, b in rows]
            myf = sum(yf) / len(yf)
            cov = sum((a - ms) * (b - myf) for a, b in
                      zip(s, yf, strict=True)) / (len(s) - 1)
            shares[f] = cov / var_s
        return shares

    sh = decompose(feats)
    total = sum(sh.values())
    print("  " + "  ".join(f"w_{f}={v:+.3f}" for f, v in sh.items())
          + f"   sum={total:.3f}")
    share_m = sh["modeled"] / total if total else float("nan")
    boots = []
    for _ in range(2000):
        sample = [feats[rng.randrange(len(feats))] for _ in feats]
        d = decompose(sample)
        t = sum(d.values())
        if t:
            boots.append(d["modeled"] / t)
    boots.sort()
    lo, hi = boots[50], boots[len(boots) - 51]
    print(f"  modeled share of composite w: {share_m:.3f} [{lo:.3f},{hi:.3f}] "
          f"(equal share = 0.25)")
    print(f"  P29.3: CI upper < 0.25 -> {'SUPPORTED' if hi < 0.25 else 'FALSIFIED'}")

    # ------------------------------------------------------------- P29.4
    print()
    print("=" * 74)
    print("P29.4  REGISTER-DEPENDENT INTERCEPT (RE-pooled c by output register)")
    print("=" * 74)
    prose = [(f["c"], f["se_c"]) for a, f in fits.items()
             if a not in LEDGER_REGISTER and a != "c20-decide"
             and not f["extrap"]]
    ledger = [(f["c"], f["se_c"]) for a, f in fits.items() if a in LEDGER_REGISTER]
    if len(prose) >= 2 and len(ledger) >= 2:
        pm, pse, ptau, _, _ = dl_meta([x for x, _ in prose], [x for _, x in prose])
        lm, lse, ltau, _, _ = dl_meta([x for x, _ in ledger], [x for _, x in ledger])
        p_ci = (pm - 1.96 * pse, pm + 1.96 * pse)
        l_ci = (lm - 1.96 * lse, lm + 1.96 * lse)
        print(f"  prose  (k={len(prose)}):  c = {pm:.3f} [{p_ci[0]:.3f},{p_ci[1]:.3f}]"
              f"  tau={ptau:.3f}")
        print(f"  ledger (k={len(ledger)}): c = {lm:.3f} [{l_ci[0]:.3f},{l_ci[1]:.3f}]"
              f"  tau={ltau:.3f}")
        if "c20-decide" in fits:
            f = fits["c20-decide"]
            print(f"  decide (descriptive, single arm): c = {f['c']:.3f}±{f['se_c']:.3f}")
        disjoint = l_ci[1] < p_ci[0]
        print(f"  P29.4: prose/ledger CIs disjoint, prose above -> "
              f"{'SUPPORTED' if disjoint else 'FALSIFIED'}")
    else:
        print(f"  P29.4: NOT EVALUABLE (prose k={len(prose)}, ledger k={len(ledger)})")


if __name__ == "__main__":
    main()
