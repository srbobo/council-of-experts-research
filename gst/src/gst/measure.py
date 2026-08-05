"""The measurement kit -- estimators for the framework's four parameters.

    (w, c)   shrinkage: evidence weight and prior fill        -> shrinkage()
    f        feature-span fraction                            -> span_fraction()
    eps      instrument blind-spot vector                     -> blindspot()
    p0       clean-sample rate and the best-of-n curve        -> clean_rate()

Each estimator carries its own identifiability guard and returns the guard's
verdict alongside the number. A parameter that cannot be identified from the
supplied runs is reported as unidentifiable, never as a point estimate --
the failure mode this kit exists to prevent is a confident number computed
from a design that could not have produced it.
"""
from __future__ import annotations

import math
import random
import re
from collections import defaultdict
from dataclasses import dataclass, field

from . import stats
from .audit import audit_record
from .instruments import DEFAULT, Instrument
from .record import RunRecord

_SENT = re.compile(r'(?<=[.!?])\s+|\n+')


# --------------------------------------------------------------------------
# A1: the shrinkage law   y = w*s + c
# --------------------------------------------------------------------------

@dataclass
class ShrinkageResult:
    w: float
    c: float
    w_ci: tuple[float, float] | None
    c_ci: tuple[float, float] | None
    r2_runs: float
    r2_strata: float
    n_runs: int
    strata: dict[int, tuple[float, int]]      # supply -> (mean emitted, n)
    quadratic_coef: float
    quadratic_ci: tuple[float, float]
    identifiable: bool
    notes: list[str] = field(default_factory=list)

    @property
    def prior_trust_ratio(self) -> float:
        """(1-w)/w -- how much more the writer weights its prior than the
        evidence. 1.0 means even; above 1.0 means the prior dominates."""
        return (1 - self.w) / self.w if self.w > 0 else float("inf")

    @property
    def verdict(self) -> str:
        if not self.identifiable:
            return "UNIDENTIFIABLE"
        if self.w >= 0.85 and self.c <= 0.15:
            return "FAITHFUL TRANSDUCTION (no intervention indicated)"
        if self.w <= 0.15:
            return "PURE REGISTER (output nearly independent of upstream)"
        return "SHRINKAGE (compensating invention at low supply)"

    def compression_at(self, s_lo: float, s_hi: float) -> float:
        """Ratio by which upstream discrimination is compressed at the step."""
        up = s_hi / s_lo if s_lo > 0 else float("inf")
        dn = self.predict(s_hi) / self.predict(s_lo) if self.predict(s_lo) > 0 else float("inf")
        return dn / up if up else float("nan")

    def predict(self, s: float) -> float:
        return self.w * s + self.c


def shrinkage(records: list[RunRecord], instrument: Instrument = DEFAULT, *,
              seed: int = 0, draws: int = 2000,
              min_supply_levels: int = 3) -> ShrinkageResult:
    """Regress emitted property level on upstream supply level.

    The estimate is only meaningful if the runs actually vary the supply. If
    your pipeline always feeds the writer the same amount, w is not weakly
    identified -- it is unidentified, and the guard says so. Vary supply by
    ablating upstream content (see gst.corpus) rather than hoping natural
    variation covers the range.
    """
    xs: list[float] = []
    ys: list[float] = []
    by_stratum: dict[int, list[float]] = defaultdict(list)
    notes: list[str] = []
    for rec in records:
        rep = audit_record(rec, instrument)
        if rep.floor_guard_tripped:
            continue
        xs.append(float(rep.supply))
        ys.append(float(rep.emitted))
        by_stratum[rep.supply].append(float(rep.emitted))

    strata = {s: (stats.mean(v), len(v)) for s, v in sorted(by_stratum.items())}
    levels = len(strata)
    if levels < min_supply_levels or len(xs) < 10:
        return ShrinkageResult(
            w=float("nan"), c=float("nan"), w_ci=None, c_ci=None,
            r2_runs=float("nan"), r2_strata=float("nan"), n_runs=len(xs),
            strata=strata, quadratic_coef=float("nan"),
            quadratic_ci=(float("nan"), float("nan")), identifiable=False,
            notes=[f"only {levels} distinct supply levels over {len(xs)} runs; "
                   f"need >= {min_supply_levels} levels and >= 10 runs"])

    fit = stats.bootstrap_ols(xs, ys, draws=draws, seed=seed)
    sx = sorted(strata)
    sfit = stats.ols([float(s) for s in sx], [strata[s][0] for s in sx])
    qa, _, _ = stats.quadratic_fit(xs, ys)
    qci = stats.bootstrap_quadratic_ci(xs, ys, draws=max(500, draws // 2), seed=seed)

    if not (math.isnan(qci[0]) or math.isnan(qci[1])) and (qci[0] > 0 or qci[1] < 0):
        msg = (f"quadratic term CI {qci[0]:.3f}..{qci[1]:.3f} excludes zero: "
               "the linear shrinkage form is a poor description here "
               "(framework hypothesis A1 is under strain -- report this)")
        # A count bounded by the number of families cannot keep rising
        # linearly once supply approaches that bound, so concave curvature at
        # the top of the range is a ceiling artifact rather than evidence
        # against A1. Distinguishing the two is the reader's job, not the
        # estimator's -- so say which case this is.
        nfam = len(getattr(instrument, "family_names", ()) or ())
        if qa < 0 and nfam and max(strata) >= nfam - 1:
            msg += (f". NOTE: supply reaches {max(strata)} of {nfam} available "
                    "families, so the curvature is concave against a ceiling. "
                    "Widen the property class before reading this as a "
                    "falsification; a bounded count must bend near its bound.")
        notes.append(msg)
    thin = [s for s, (_, n) in strata.items() if n < 10]
    if thin:
        notes.append(f"supply levels with n<10: {thin} (estimate leans on thin strata)")

    return ShrinkageResult(
        w=fit.slope, c=fit.intercept, w_ci=fit.slope_ci, c_ci=fit.intercept_ci,
        r2_runs=fit.r2, r2_strata=sfit.r2, n_runs=len(xs), strata=strata,
        quadratic_coef=qa, quadratic_ci=qci, identifiable=True, notes=notes)


# --------------------------------------------------------------------------
# A2: the feature-span fraction f
# --------------------------------------------------------------------------

@dataclass
class SpanResult:
    f_median: float
    f_p25: float
    f_p75: float
    f_median_tokens: float
    n_runs: int
    dilution_factor: float
    notes: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if math.isnan(self.f_median):
            return "UNIDENTIFIABLE"
        if self.f_median >= 0.5:
            return "LOW DILUTION (sequence-level preference training may transfer)"
        return (f"HIGH DILUTION (~{self.dilution_factor:.0f}:1) -- sequence-level "
                "preference margins are satisfiable off-feature; use minimal "
                "pairs with a masked loss")


def span_fraction(records: list[RunRecord], instrument: Instrument = DEFAULT) -> SpanResult:
    """Fraction of the output that actually carries the property.

    The prediction this parameter drives: a preference margin summed over all
    tokens can be satisfied ~(1-f) of the way off-feature, so the model learns
    the ranking without moving the behavior. Small f is the quantitative case
    for span-masked training over whole-sequence DPO/ORPO.
    """
    fr: list[float] = []
    ft: list[float] = []
    notes: list[str] = []
    for rec in records:
        text = rec.output
        if len(text) < 200:
            continue
        spans = instrument.spans(text)
        if not spans:
            fr.append(0.0)
            ft.append(0.0)
            continue
        sents = _sentences(text)
        hit_chars = sum(e - s for s, e in sents
                        if any(s <= a < e for a, _b, _k in spans))
        hit_toks = sum(len(text[s:e].split()) for s, e in sents
                       if any(s <= a < e for a, _b, _k in spans))
        fr.append(hit_chars / len(text))
        ft.append(hit_toks / max(1, len(text.split())))
    if not fr:
        return SpanResult(float("nan"), float("nan"), float("nan"), float("nan"),
                          0, float("nan"), ["no runs long enough to measure spans"])
    nz = [v for v in fr if v > 0]
    if len(nz) < len(fr) * 0.5:
        notes.append(f"{len(fr) - len(nz)}/{len(fr)} runs carry no detected property "
                     "at all; f is dominated by zeros -- check the instrument fits "
                     "this property class before acting on it")
    med = stats.median(fr)
    return SpanResult(f_median=med, f_p25=stats.quantile(fr, 0.25),
                      f_p75=stats.quantile(fr, 0.75),
                      f_median_tokens=stats.median(ft), n_runs=len(fr),
                      dilution_factor=(1.0 / med) if med > 0 else float("inf"),
                      notes=notes)


def _sentences(text: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    pos = 0
    for m in _SENT.finditer(text):
        if m.start() > pos:
            out.append((pos, m.start()))
        pos = m.end()
    if pos < len(text):
        out.append((pos, len(text)))
    return out


# --------------------------------------------------------------------------
# A3: the blind-spot vector eps
# --------------------------------------------------------------------------

@dataclass
class BlindspotResult:
    per_instrument: dict[str, float]              # name -> miss rate
    per_instrument_ci: dict[str, tuple[float, float]]
    joint_independent: float
    pairwise_disagreement: dict[tuple[str, str], float]
    n_probes: int
    notes: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if self.n_probes == 0:
            return "UNIDENTIFIABLE"
        best = min(self.per_instrument.values()) if self.per_instrument else 1.0
        return (f"single-instrument miss rate {best:.2f} -> ensemble "
                f"{self.joint_independent:.3f} under an independence assumption "
                f"that the disagreement matrix should be used to check")


def blindspot(probes: list[tuple[str, set[str]]], instruments: list[Instrument]
              ) -> BlindspotResult:
    """Estimate each instrument's miss rate against labelled probes.

    A probe is (text, families-truly-present). Construct probes by taking
    texts whose property content you control -- paraphrases of known
    qualifications are the ones that matter, because paraphrase is exactly
    the move an optimized policy makes.

    The joint figure multiplies the individual rates. That is an upper bound
    on ensemble strength and assumes independent blind spots; real detectors
    share failure modes. Report the pairwise disagreement matrix beside it --
    low disagreement means the instruments are near-duplicates and the
    product overstates your protection.
    """
    notes: list[str] = []
    if len(instruments) < 2:
        notes.append("only one instrument supplied: no ensemble estimate possible, "
                     "and no valid verdict can rest on it")
    miss: dict[str, float] = {}
    cis: dict[str, tuple[float, float]] = {}
    for ins in instruments:
        missed = total = 0
        for text, truth in probes:
            got = ins.families(text)
            for fam in truth:
                total += 1
                if fam not in got:
                    missed += 1
        miss[ins.name] = missed / total if total else float("nan")
        cis[ins.name] = stats.wilson_ci(missed, total) if total else (float("nan"),) * 2

    joint = 1.0
    for v in miss.values():
        if not math.isnan(v):
            joint *= v

    dis: dict[tuple[str, str], float] = {}
    for i, a in enumerate(instruments):
        for b in instruments[i + 1:]:
            d = n = 0
            for text, _ in probes:
                fa, fb = a.families(text), b.families(text)
                d += len(fa ^ fb)
                n += len(fa | fb)
            dis[(a.name, b.name)] = d / n if n else float("nan")
    for pair, d in dis.items():
        if not math.isnan(d) and d < 0.1:
            notes.append(f"{pair[0]} and {pair[1]} disagree on only {d:.1%} of "
                         "detections: near-duplicate instruments, so the joint "
                         "figure overstates ensemble strength")
    return BlindspotResult(per_instrument=miss, per_instrument_ci=cis,
                           joint_independent=joint, pairwise_disagreement=dis,
                           n_probes=len(probes), notes=notes)


# --------------------------------------------------------------------------
# p0 and the best-of-n curve
# --------------------------------------------------------------------------

@dataclass
class CleanRateResult:
    p0_overall: float
    p0_by_supply: dict[int, tuple[float, int]]
    worst_supply: int
    p0_worst: float
    p0_worst_ci: tuple[float, float]
    lam: float
    poisson_p0: float
    bon_independent: dict[int, float]
    bon_empirical: dict[int, float]
    n_runs: int
    bon_empirical_cells: dict[int, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def n_for(self, target: float, *, min_cell_frac: float = 0.5) -> tuple[int, str]:
        """Samples needed to reach `target` clean probability at worst supply.

        Returns (n, basis). Prefers the empirical curve, but only at points
        where enough cells still contribute to be representative; beyond that
        it falls back to the independence curve and says so, because an
        empirical point measured on a handful of surviving cells is not a
        stronger estimate than the formula -- it is a different question.
        """
        base = self.bon_empirical_cells.get(1, 0)
        for n in range(1, 33):
            emp = self.bon_empirical.get(n)
            cells = self.bon_empirical_cells.get(n, 0)
            representative = bool(base) and cells >= base * min_cell_frac
            if emp is not None and representative:
                if emp >= target:
                    return n, "empirical"
            else:
                val = self.bon_independent.get(n)
                if val is None:
                    val = 1 - (1 - self.p0_worst) ** n
                if val >= target:
                    return n, ("independence (optimistic; empirical data at this n "
                               "covers too few cells to be representative)")
        return -1, "unreachable"


def clean_rate(records: list[RunRecord], instrument: Instrument = DEFAULT, *,
               max_n: int = 6, seed: int = 0, trials: int = 400) -> CleanRateResult:
    """Probability a single sample is invention-free, and what selection buys.

    Two curves are returned and they are not the same claim:

      bon_independent  1 - (1 - p0)^n. Assumes redraws are independent.
      bon_empirical    measured by resampling actual repeated runs of the same
                       prompt_id. Requires >= 2 runs per prompt.

    Where the empirical curve sits below the independent one, samples are
    positively correlated -- the writer is reliably unclean on certain prompts
    rather than unclean at random -- and the independence formula overstates
    what best-of-n delivers. Report the empirical figure.
    """
    notes: list[str] = []
    clean_by_supply: dict[int, list[int]] = defaultdict(list)
    # Redraws must share the task AND the configuration. Pooling runs of one
    # task across different writers or arms treats a condition change as a
    # random redraw and inflates what selection appears to buy.
    by_cell: dict[tuple, list[int]] = defaultdict(list)
    cell_supply: dict[tuple, int] = {}
    inv_counts: list[int] = []
    n_used = 0
    for rec in records:
        rep = audit_record(rec, instrument)
        if rep.floor_guard_tripped:
            continue
        n_used += 1
        ok = 1 if not rep.invented else 0
        clean_by_supply[rep.supply].append(ok)
        inv_counts.append(len(rep.invented))
        if rec.prompt_id:
            key = (rec.prompt_id, rec.condition, rec.writer_id, rep.supply)
            by_cell[key].append(ok)
            cell_supply[key] = rep.supply

    if not n_used:
        return CleanRateResult(float("nan"), {}, -1, float("nan"),
                               (float("nan"),) * 2, float("nan"), float("nan"),
                               {}, {}, 0, ["no usable runs"])

    p0_by = {s: (stats.mean([float(x) for x in v]), len(v))
             for s, v in sorted(clean_by_supply.items())}
    scored = [(p, s, n) for s, (p, n) in p0_by.items() if n >= 5]
    if scored:
        p_worst, s_worst, _ = min(scored)
    else:
        s_worst = min(p0_by, key=lambda s: p0_by[s][0])
        p_worst = p0_by[s_worst][0]
        notes.append("every supply stratum has n<5; worst-case p0 is unreliable")
    k = sum(clean_by_supply[s_worst])
    tot = len(clean_by_supply[s_worst])

    lam = stats.mean([float(x) for x in inv_counts])
    bon_i = {n: 1 - (1 - p_worst) ** n for n in range(1, max_n + 1)}

    # Restrict the empirical curve to the SAME stratum the independence curve
    # is built from. Comparing a worst-stratum prediction against an
    # all-strata measurement is not a comparison, and it makes correlated
    # redraws look better than independent ones -- which is impossible.
    worst_cells = {k: v for k, v in by_cell.items() if cell_supply[k] == s_worst}
    bon_e, bon_cells = _empirical_bon(worst_cells, max_n, seed, trials)
    if not bon_e:
        bon_e, bon_cells = _empirical_bon(by_cell, max_n, seed, trials)
        if bon_e:
            notes.append(f"empirical best-of-n is pooled across all supply levels: "
                         f"too few repeated runs at the worst stratum (s={s_worst}) "
                         "to measure it there. It is therefore optimistic relative "
                         "to the worst case the independence curve describes.")
    if bon_e:
        for n in sorted(bon_e):
            if bon_e[n] < bon_i.get(n, 0) - 0.05:
                notes.append(f"at n={n} the empirical best-of-n ({bon_e[n]:.2f}) is "
                             f"below the independence prediction ({bon_i[n]:.2f}): "
                             "redraws are positively correlated; use the empirical "
                             "curve for sizing")
                break
        # Only cells with at least n runs can contribute to the n-th point, so
        # the curve is measured on a shrinking and possibly easier
        # subpopulation as n grows. A rise driven by that is composition, not
        # selection working.
        base = bon_cells.get(1, 0)
        shrunk = [n for n, c in sorted(bon_cells.items()) if base and c < base * 0.5]
        if shrunk:
            notes.append(f"cells contributing per n: {dict(sorted(bon_cells.items()))}. "
                         f"From n={shrunk[0]} onward fewer than half the cells "
                         "contribute, so those points describe a different "
                         "subpopulation -- size from the largest n whose cell count "
                         "is still representative, not from the end of the curve.")
    else:
        notes.append("no (task, condition, writer) cell had >= 2 runs: only the "
                     "independence curve is available, and it is optimistic by "
                     "construction")

    return CleanRateResult(
        p0_overall=stats.mean([float(x) for v in clean_by_supply.values() for x in v]),
        p0_by_supply=p0_by, worst_supply=s_worst, p0_worst=p_worst,
        p0_worst_ci=stats.wilson_ci(k, tot), lam=lam,
        poisson_p0=math.exp(-lam), bon_independent=bon_i, bon_empirical=bon_e,
        n_runs=n_used, bon_empirical_cells=bon_cells, notes=notes)


def _empirical_bon(by_cell: dict, max_n: int, seed: int,
                   trials: int) -> tuple[dict[int, float], dict[int, int]]:
    """Resample real redraws within each (task, condition, writer) cell:
    P(at least one clean in n). Returns (curve, cells-contributing-per-n).

    Sampling is without replacement within a cell, so a cell with fewer than n
    runs cannot contribute to the n-th point. That is deliberate -- drawing
    with replacement would manufacture independent redraws, which is exactly
    the assumption this estimator exists to avoid making.
    """
    usable = {p: v for p, v in by_cell.items() if len(v) >= 2}
    if not usable:
        return {}, {}
    rng = random.Random(seed)
    out: dict[int, float] = {}
    cells: dict[int, int] = {}
    for n in range(1, max_n + 1):
        hits = tot = 0
        contributing = 0
        for _p, v in usable.items():
            if len(v) < n:
                continue
            contributing += 1
            for _ in range(trials):
                draw = rng.sample(v, n)
                hits += 1 if any(draw) else 0
                tot += 1
        if tot:
            out[n] = hits / tot
            cells[n] = contributing
    return out, cells
