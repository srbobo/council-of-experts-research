"""Inference with few clusters, and chance-corrected agreement.

Added 2026-10-01 after the board review (docs/BOARD_REVIEW_2026-10-01.md),
which found two measurement habits in this program that overstated what the
data showed:

  * intervals from a percentile bootstrap over 6-11 case clusters, quoted as
    if they were exact, and in one figure run-level intervals reported under
    a "clustered" label;
  * raw percent agreement used as the acceptance gate for a two-judge
    instrument, at base rates where two judges answering independently
    already agree 0.75-0.88 of the time.

Everything here works on CLUSTER-LEVEL numbers (one value, or one paired
difference, per case or item). No dependencies.
"""
from __future__ import annotations

import itertools
import math
import random
import statistics as st

# two-sided 95% critical values of Student's t, by degrees of freedom
_T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
         7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179,
         13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101,
         19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064,
         25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}


def t_crit(df: int) -> float:
    """Two-sided 95% critical value; normal approximation above df=30 is
    slightly liberal, so use the df=30 value up to 60 and 1.96 beyond."""
    if df < 1:
        raise ValueError("need at least two clusters")
    if df in _T975:
        return _T975[df]
    return 2.0 if df <= 60 else 1.96


def t_interval(values: list[float]) -> tuple[float, float, float]:
    """(mean, lo, hi) for the mean of cluster-level values or differences."""
    k = len(values)
    if k < 2:
        raise ValueError("need at least two clusters")
    m = st.mean(values)
    se = st.stdev(values) / math.sqrt(k)
    c = t_crit(k - 1)
    return m, m - c * se, m + c * se


def sign_flip_p(diffs: list[float], *, draws: int = 20000, seed: int = 0) -> float:
    """Two-sided randomization test of 'no effect in any cluster' on paired
    cluster-level differences. Exact (all 2^k sign patterns) up to k=20,
    seeded Monte Carlo above that. With k clusters the smallest attainable
    p is 2 / 2^k, so 6 clusters cannot go below 0.031 — report k with it."""
    k = len(diffs)
    obs = abs(sum(diffs))
    if k <= 20:
        hits = sum(abs(sum(s * d for s, d in zip(signs, diffs))) >= obs - 1e-12
                   for signs in itertools.product((1, -1), repeat=k))
        return hits / 2 ** k
    rng = random.Random(seed)
    hits = sum(abs(sum(d if rng.random() < 0.5 else -d for d in diffs)) >= obs - 1e-12
               for _ in range(draws))
    return (hits + 1) / (draws + 1)


def cluster_boot(clusters: dict, stat, *, draws: int = 5000, seed: int = 0,
                 alpha: float = 0.05) -> tuple[float, float]:
    """Percentile bootstrap resampling whole clusters. `stat` receives a list
    of the resampled clusters' values and returns a number or None. Reported
    beside, never instead of, t_interval/sign_flip_p when clusters are few."""
    rng = random.Random(seed)
    keys = sorted(clusters)
    vals = []
    for _ in range(draws):
        v = stat([clusters[keys[rng.randrange(len(keys))]] for _ in keys])
        if v is not None:
            vals.append(v)
    vals.sort()
    lo = vals[max(0, int(math.floor(alpha / 2 * len(vals))))]
    hi = vals[min(len(vals) - 1, int(math.ceil((1 - alpha / 2) * len(vals))) - 1)]
    return lo, hi


def kappa(pairs: list[tuple[bool, bool]]) -> dict:
    """Agreement between two raters on a yes/no label.

    raw      share of items on which they give the same label
    chance   the raw agreement two independent raters with these base rates
             would reach
    kappa    (raw - chance) / (1 - chance)
    overlap  items both flag / items either flags (agreement on positives)
    """
    n = len(pairs)
    if n == 0:
        raise ValueError("no rated items")
    raw = sum(a == b for a, b in pairs) / n
    pa = sum(1 for a, _ in pairs if a) / n
    pb = sum(1 for _, b in pairs if b) / n
    chance = pa * pb + (1 - pa) * (1 - pb)
    both = sum(1 for a, b in pairs if a and b)
    either = sum(1 for a, b in pairs if a or b)
    return {"n": n, "raw": raw, "chance": chance,
            "kappa": (raw - chance) / (1 - chance) if chance < 1 else float("nan"),
            "pos_a": pa, "pos_b": pb,
            "overlap": both / either if either else float("nan")}


def prf(truth: list[bool], pred: list[bool]) -> dict:
    """Precision, recall and F1 of `pred` against `truth` (positives = True)."""
    tp = sum(1 for t, p in zip(truth, pred) if t and p)
    fp = sum(1 for t, p in zip(truth, pred) if not t and p)
    fn = sum(1 for t, p in zip(truth, pred) if t and not p)
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if tp else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec, "f1": f1}


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjusted p-values for a family of tests."""
    order = sorted(pvals, key=pvals.get)
    m = len(order)
    out, running = {}, 0.0
    for i, name in enumerate(order):
        running = max(running, min(1.0, (m - i) * pvals[name]))
        out[name] = running
    return out


def paired_diffs(rows: list[dict], cluster: str, arm_key: str, a: str, b: str,
                 value) -> tuple[list, list[float]]:
    """Per-cluster mean of `value(row)` in arm `a` minus arm `b`, for
    clusters that have rows in both arms. Returns (cluster ids, differences)."""
    by: dict = {}
    for r in rows:
        by.setdefault(r[cluster], {}).setdefault(r[arm_key], []).append(float(value(r)))
    ids = sorted(k for k, v in by.items() if a in v and b in v)
    return ids, [st.mean(by[k][a]) - st.mean(by[k][b]) for k in ids]
