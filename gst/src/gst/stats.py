"""Statistics — pure stdlib, deterministic.

No numpy on purpose: the core of this kit installs with zero dependencies so
that running the measurements is never blocked by an environment problem.
The fits here are small (one or two regressors); the arithmetic is exact
enough and the bootstrap is seeded.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Fit:
    slope: float
    intercept: float
    r2: float
    n: int
    slope_ci: tuple[float, float] | None = None
    intercept_ci: tuple[float, float] | None = None

    def predict(self, x: float) -> float:
        return self.slope * x + self.intercept


def ols(xs: list[float], ys: list[float]) -> Fit:
    n = len(xs)
    if n < 2:
        raise ValueError("need >= 2 points")
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        raise ValueError("no variation in x: slope unidentifiable "
                         "(vary the upstream supply level)")
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    slope = sxy / sxx
    intercept = my - slope * mx
    sst = sum((y - my) ** 2 for y in ys)
    sse = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys, strict=True))
    r2 = 1.0 - sse / sst if sst > 0 else float("nan")
    return Fit(slope=slope, intercept=intercept, r2=r2, n=n)


def bootstrap_ols(xs: list[float], ys: list[float], *, draws: int = 2000,
                  seed: int = 0, alpha: float = 0.05) -> Fit:
    """Percentile bootstrap over observations. Seeded, so reruns agree."""
    base = ols(xs, ys)
    rng = random.Random(seed)
    n = len(xs)
    slopes: list[float] = []
    intercepts: list[float] = []
    for _ in range(draws):
        idx = [rng.randrange(n) for _ in range(n)]
        bx = [xs[i] for i in idx]
        by = [ys[i] for i in idx]
        try:
            f = ols(bx, by)
        except ValueError:
            continue                      # resample had no x-variation
        slopes.append(f.slope)
        intercepts.append(f.intercept)
    if len(slopes) < draws * 0.5:
        return base                       # too degenerate to bootstrap honestly
    base.slope_ci = _pct_ci(slopes, alpha)
    base.intercept_ci = _pct_ci(intercepts, alpha)
    return base


def _pct_ci(vals: list[float], alpha: float) -> tuple[float, float]:
    v = sorted(vals)
    lo = v[max(0, int(math.floor((alpha / 2) * len(v))))]
    hi = v[min(len(v) - 1, int(math.ceil((1 - alpha / 2) * len(v))) - 1)]
    return (lo, hi)


def solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("singular design matrix")
        m[col], m[piv] = m[piv], m[col]
        for r in range(n):
            if r == col:
                continue
            f = m[r][col] / m[col][col]
            for c in range(col, n + 1):
                m[r][c] -= f * m[col][c]
    return [m[i][n] / m[i][i] for i in range(n)]


def quadratic_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Fit y = c + b*x + a*x^2, return (a, b, c). Used as a linearity probe."""
    n = len(xs)
    s = [sum(x ** k for x in xs) for k in range(5)]
    s[0] = float(n)
    xtx = [[s[0], s[1], s[2]], [s[1], s[2], s[3]], [s[2], s[3], s[4]]]
    xty = [sum(ys),
           sum(x * y for x, y in zip(xs, ys, strict=True)),
           sum(x * x * y for x, y in zip(xs, ys, strict=True))]
    c, b, a = solve(xtx, xty)
    return a, b, c


def bootstrap_quadratic_ci(xs: list[float], ys: list[float], *, draws: int = 1000,
                           seed: int = 0, alpha: float = 0.05) -> tuple[float, float]:
    """CI on the quadratic coefficient. Excluding zero flags non-linearity."""
    rng = random.Random(seed)
    n = len(xs)
    vals: list[float] = []
    for _ in range(draws):
        idx = [rng.randrange(n) for _ in range(n)]
        try:
            a, _, _ = quadratic_fit([xs[i] for i in idx], [ys[i] for i in idx])
        except ValueError:
            continue
        vals.append(a)
    if len(vals) < draws * 0.5:
        return (float("nan"), float("nan"))
    return _pct_ci(vals, alpha)


def mean(v: list[float]) -> float:
    return sum(v) / len(v) if v else float("nan")


def median(v: list[float]) -> float:
    if not v:
        return float("nan")
    s = sorted(v)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def quantile(v: list[float], q: float) -> float:
    if not v:
        return float("nan")
    s = sorted(v)
    i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[i]


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval — behaves at 0 and 1, where normal approx does not."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))
