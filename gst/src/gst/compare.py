"""Comparing arms -- with intervals, and under two instruments.

Added after a sweep across 27 arms of the originating architecture, where
hand-rolled comparisons twice produced conclusions that a proper interval
erased. Two failure modes this module exists to prevent:

  ranking point estimates   "0.089 beats 0.156" is 4 events against 7 at
                            n=45. A difference is a difference only when its
                            interval excludes zero.
  one-instrument verdicts   an arm that improves under the instrument its
                            intervention was tuned against, and not under an
                            independent one, has changed vocabulary rather
                            than behavior. `compare_two_instrument` reports
                            both and labels that case explicitly.

Comparability is the caller's responsibility and it is easy to get wrong:
arms must share the task battery and the writer. Pooling an arm that ran a
different case set makes the difference a case effect wearing an arm's name.
`check_comparable` will tell you when that has happened.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from .audit import audit_record
from .instruments import DEFAULT, Instrument
from .record import RunRecord


@dataclass
class ArmDiff:
    arm: str
    baseline: str
    lam: float
    lam_baseline: float
    diff_ci: tuple[float, float]
    n: int
    n_baseline: int
    runs_with_invention: int

    @property
    def distinguishable(self) -> bool:
        return self.diff_ci[0] > 0 or self.diff_ci[1] < 0

    @property
    def verdict(self) -> str:
        if not self.distinguishable:
            return "not distinguishable from baseline"
        return ("lower invention than baseline" if self.diff_ci[1] < 0
                else "HIGHER invention than baseline")


@dataclass
class TwoInstrumentDiff:
    arm: str
    primary: ArmDiff
    secondary: ArmDiff
    primary_name: str
    secondary_name: str

    @property
    def verdict(self) -> str:
        p, s = self.primary, self.secondary
        if p.distinguishable and s.distinguishable:
            same = (p.diff_ci[1] < 0) == (s.diff_ci[1] < 0)
            return ("CONFIRMED by both instruments" if same else
                    "CONTRADICTORY: the instruments disagree on the direction")
        if p.distinguishable and not s.distinguishable:
            return (f"INSTRUMENT-RELATIVE: {self.primary_name} sees a difference "
                    f"{self.secondary_name} does not. Treat as a change in wording, "
                    "not behavior, until an independent instrument confirms it.")
        if s.distinguishable and not p.distinguishable:
            return (f"only {self.secondary_name} sees a difference; "
                    f"{self.primary_name} does not")
        return "no difference under either instrument"


def _invention_counts(records: list[RunRecord], instrument: Instrument) -> list[int]:
    out = []
    for r in records:
        rep = audit_record(r, instrument)
        if not rep.floor_guard_tripped:
            out.append(len(rep.invented))
    return out


def _boot_diff(a: list[int], b: list[int], *, seed: int, draws: int,
               alpha: float) -> tuple[float, float]:
    rng = random.Random(seed)
    d = []
    for _ in range(draws):
        ma = sum(rng.choice(a) for _ in a) / len(a)
        mb = sum(rng.choice(b) for _ in b) / len(b)
        d.append(ma - mb)
    d.sort()
    return d[int((alpha / 2) * draws)], d[min(draws - 1, int((1 - alpha / 2) * draws))]


def compare_arm(arm_records: list[RunRecord], baseline_records: list[RunRecord], *,
                arm: str = "arm", baseline: str = "baseline",
                instrument: Instrument = DEFAULT, seed: int = 0,
                draws: int = 5000, alpha: float = 0.05) -> ArmDiff:
    """Bootstrap CI on the difference in invention rate. Never a bare ranking."""
    a = _invention_counts(arm_records, instrument)
    b = _invention_counts(baseline_records, instrument)
    if not a or not b:
        raise ValueError("both arms need usable runs")
    return ArmDiff(arm=arm, baseline=baseline,
                   lam=sum(a) / len(a), lam_baseline=sum(b) / len(b),
                   diff_ci=_boot_diff(a, b, seed=seed, draws=draws, alpha=alpha),
                   n=len(a), n_baseline=len(b),
                   runs_with_invention=sum(1 for x in a if x))


def compare_two_instrument(arm_records: list[RunRecord],
                           baseline_records: list[RunRecord],
                           primary: Instrument, secondary: Instrument, *,
                           arm: str = "arm", baseline: str = "baseline",
                           **kw) -> TwoInstrumentDiff:
    """The comparison the framework's own rules require. Use it for any claim
    that an intervention worked."""
    return TwoInstrumentDiff(
        arm=arm,
        primary=compare_arm(arm_records, baseline_records, arm=arm,
                            baseline=baseline, instrument=primary, **kw),
        secondary=compare_arm(arm_records, baseline_records, arm=arm,
                              baseline=baseline, instrument=secondary, **kw),
        primary_name=getattr(primary, "name", "primary"),
        secondary_name=getattr(secondary, "name", "secondary"))


@dataclass
class ComparabilityReport:
    shared_prompts: set[str]
    per_arm_only: dict[str, set[str]]
    writers: dict[str, set[str]]
    comparable: bool
    notes: list[str] = field(default_factory=list)


def check_comparable(arms: dict[str, list[RunRecord]]) -> ComparabilityReport:
    """Do these arms actually share a task battery and a writer?

    Reuse of one arm label across experiments with different case sets is a
    real and easy mistake -- it happened three times in the originating
    program -- and it turns a case effect into an apparent arm effect.
    """
    sets = {a: {r.prompt_id for r in rs} for a, rs in arms.items()}
    shared = set.intersection(*sets.values()) if sets else set()
    only = {a: s - shared for a, s in sets.items()}
    writers = {a: {r.writer_id for r in rs} for a, rs in arms.items()}
    notes: list[str] = []
    for a, extra in only.items():
        if extra:
            notes.append(f"{a} has {len(extra)} case(s) no other arm ran: "
                         f"{sorted(extra)[:4]}{'...' if len(extra) > 4 else ''}. "
                         "Restrict every arm to the shared battery before comparing.")
    multi = {a: w for a, w in writers.items() if len(w) > 1}
    if multi:
        notes.append(f"arms spanning multiple writer ids: {sorted(multi)}. "
                     "A writer change inside an arm is a confound, not a redraw.")
    return ComparabilityReport(shared_prompts=shared, per_arm_only=only,
                               writers=writers, comparable=not notes, notes=notes)


def restrict_to_shared(arms: dict[str, list[RunRecord]]) -> dict[str, list[RunRecord]]:
    """Drop every run whose task is not present in all arms."""
    shared = check_comparable(arms).shared_prompts
    return {a: [r for r in rs if r.prompt_id in shared] for a, rs in arms.items()}
