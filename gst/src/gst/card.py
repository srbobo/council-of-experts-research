"""The parameter card -- the artifact an external replication publishes.

One system, one card: the four parameters with intervals, the guards that
passed or failed, and the intervention the measurements indicate. Comparable
across architectures because the parameters are defined on the writing step,
not on any particular orchestrator.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from .instruments import DEFAULT, Instrument
from .measure import (
    BlindspotResult,
    CleanRateResult,
    ShrinkageResult,
    SpanResult,
    blindspot,
    clean_rate,
    shrinkage,
    span_fraction,
)
from .record import RunRecord, partition


@dataclass
class ParameterCard:
    system: str
    n_records_supplied: int
    n_records_used: int
    dropped: dict[str, int]
    instrument: str
    shrinkage: ShrinkageResult | None = None
    spans: SpanResult | None = None
    blindspot: BlindspotResult | None = None
    clean: CleanRateResult | None = None
    notes: list[str] = field(default_factory=list)

    # -- the decision rule from the framework, applied to measured values ---
    def recommendations(self, *, white_box: bool = False,
                        can_train: bool = False, has_rl_infra: bool = False
                        ) -> list[str]:
        out: list[str] = []
        sh, sp, cl = self.shrinkage, self.spans, self.clean
        if sh and sh.identifiable and sh.w >= 0.85 and sh.c <= 0.15:
            out.append("C0 only: the writer already transduces faithfully "
                       f"(w={sh.w:.2f}, c={sh.c:.2f}). No intervention indicated; "
                       "publishing this is a falsification datum for A1.")
            return out
        if cl and cl.n_runs:
            n, basis = cl.n_for(0.95)
            out.append(f"C5 verifier-blind best-of-n, deployable now: n={n} reaches "
                       f"0.95 clean at the worst supply stratum (basis: {basis}; "
                       f"p0={cl.p0_worst:.2f}). Needs no training and no weight access."
                       if n > 0 else
                       "C5 best-of-n cannot reach 0.95 within n=32 at the worst "
                       "stratum: selection alone is insufficient here.")
        if can_train:
            if sp and sp.f_median == sp.f_median and sp.f_median < 0.5:
                out.append(f"C2 minimal-pair, span-masked preference training: f="
                           f"{sp.f_median:.2f} implies a ~{sp.dilution_factor:.0f}:1 "
                           "margin dilution, so whole-sequence DPO/ORPO is predicted "
                           "to move ranking metrics without moving behavior.")
            out.append("C1 counterfactual corpus: build matched supply variants so "
                       "topic stops predicting the property (gst.corpus). Target "
                       ">= 1000 items; every failed attempt in the originating "
                       "program ran at 49-88.")
        if white_box:
            out.append("C4 conditional activation steering is available (residual "
                       "stream access): predicts w -> 1 and c -> 0 in a refit.")
        else:
            out.append("C4 steering unavailable: no residual-stream access on this "
                       "writer. Stated as a scope boundary, not a footnote.")
        if has_rl_infra:
            out.append("C3 ensemble-reward RL: run last, gated on C1/C2 results, "
                       "and only with a consensus instrument the policy never sees.")
        return out

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("shrinkage", "spans", "blindspot", "clean"):
            v = d.get(k)
            if isinstance(v, dict):
                d[k] = {kk: _jsonable(vv) for kk, vv in v.items()}
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=_jsonable)

    def render(self) -> str:
        L: list[str] = []
        add = L.append
        add(f"GST PARAMETER CARD -- {self.system}")
        add("=" * 68)
        add(f"records: {self.n_records_used} used of {self.n_records_supplied} supplied"
            + (f"   dropped: {self.dropped}" if self.dropped else ""))
        add(f"instrument: {self.instrument}")
        add("")
        sh = self.shrinkage
        if sh:
            add("A1  SHRINKAGE   y = w*s + c")
            if sh.identifiable:
                add(f"    w = {sh.w:.3f} {_ci(sh.w_ci)}      evidence weight")
                add(f"    c = {sh.c:.3f} {_ci(sh.c_ci)}      prior fill")
                add(f"    prior-trust ratio (1-w)/w = {sh.prior_trust_ratio:.2f}")
                add(f"    R^2 = {sh.r2_runs:.3f} (runs), {sh.r2_strata:.3f} (strata)"
                    f"   n = {sh.n_runs}")
                add("    supply -> emitted: " + "  ".join(
                    f"{s}:{m:.2f}(n={n})" for s, (m, n) in sh.strata.items()))
            add(f"    verdict: {sh.verdict}")
            for n in sh.notes:
                add(f"    ! {n}")
            add("")
        sp = self.spans
        if sp:
            add("A2  FEATURE SPAN")
            add(f"    f = {sp.f_median:.3f} chars (p25 {sp.f_p25:.3f}, p75 {sp.f_p75:.3f}),"
                f" {sp.f_median_tokens:.3f} tokens   n = {sp.n_runs}")
            add(f"    verdict: {sp.verdict}")
            for n in sp.notes:
                add(f"    ! {n}")
            add("")
        bs = self.blindspot
        if bs:
            add("A3  BLIND SPOTS")
            for name, v in bs.per_instrument.items():
                add(f"    eps[{name}] = {v:.3f} {_ci(bs.per_instrument_ci.get(name))}")
            add(f"    joint (independence assumed) = {bs.joint_independent:.4f}")
            for (a, b), d in bs.pairwise_disagreement.items():
                add(f"    disagreement {a} vs {b}: {d:.3f}")
            for n in bs.notes:
                add(f"    ! {n}")
            add("")
        cl = self.clean
        if cl and cl.n_runs:
            add("p0  CLEAN-SAMPLE RATE AND SELECTION")
            add(f"    p0 overall = {cl.p0_overall:.3f}   worst stratum s={cl.worst_supply}:"
                f" {cl.p0_worst:.3f} {_ci(cl.p0_worst_ci)}")
            add(f"    lambda = {cl.lam:.3f}   Poisson e^-lambda = {cl.poisson_p0:.3f}"
                f"  (vs empirical {cl.p0_overall:.3f})")
            add("    best-of-n (independence): " + "  ".join(
                f"n={n}:{v:.3f}" for n, v in cl.bon_independent.items()))
            if cl.bon_empirical:
                add("    best-of-n (empirical):    " + "  ".join(
                    f"n={n}:{v:.3f}" for n, v in cl.bon_empirical.items()))
                add("      cells contributing:    " + "  ".join(
                    f"n={n}:{c}" for n, c in sorted(cl.bon_empirical_cells.items())))
            for n in cl.notes:
                add(f"    ! {n}")
            add("")
        if self.notes:
            add("NOTES")
            for n in self.notes:
                add(f"    ! {n}")
        return "\n".join(L)


def _ci(t) -> str:
    if not t or t[0] != t[0]:
        return ""
    return f"[{t[0]:.3f}, {t[1]:.3f}]"


def _jsonable(v):
    if isinstance(v, set):
        return sorted(v)
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, tuple):
        return list(v)
    if isinstance(v, list):
        return [_jsonable(x) for x in v]
    return v


def measure_all(records: list[RunRecord], *, system: str,
                instrument: Instrument = DEFAULT,
                probes: list[tuple[str, set[str]]] | None = None,
                instruments: list[Instrument] | None = None,
                seed: int = 0) -> ParameterCard:
    """Estimate every parameter this run set supports and build the card."""
    usable, dropped = partition(records)
    card = ParameterCard(system=system, n_records_supplied=len(records),
                         n_records_used=len(usable), dropped=dropped,
                         instrument=getattr(instrument, "name", "unnamed"))
    if not usable:
        card.notes.append("no usable records after validation")
        return card
    card.shrinkage = shrinkage(usable, instrument, seed=seed)
    card.spans = span_fraction(usable, instrument)
    card.clean = clean_rate(usable, instrument, seed=seed)
    if probes and instruments:
        card.blindspot = blindspot(probes, instruments)
    else:
        card.notes.append("no blind-spot estimate: supply labelled probes and >= 2 "
                          "instruments. Until then no verdict from this kit is "
                          "two-instrument validated.")
    return card
