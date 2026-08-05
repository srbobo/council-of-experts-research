"""Provenance decomposition -- preserved / discarded / invented.

For one run: which families the upstream components raised, which of those
survived into the writer's output, which were dropped, and which appeared in
the output with no upstream source. Invention is the quantity the framework's
shrinkage law explains and its interventions target.

Note what `invented` does and does not mean. It means "present in the output,
absent from every upstream text, per this instrument." A writer may state a
true and useful qualification that no specialist happened to raise; that is
still invention in the provenance sense, because the pipeline cannot trace
it. Traceability, not truth, is what this measures -- and conflating the two
is the most common misreading of the decomposition.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .instruments import DEFAULT, Instrument
from .record import RunRecord

MIN_OUTPUT_CHARS = 500


@dataclass
class ProvenanceReport:
    raised: set[str]
    kept: set[str]
    discarded: set[str]
    invented: set[str]
    supply: int
    traceability: float
    output_chars: int
    floor_guard_tripped: bool = False
    invented_evidence: dict[str, list[str]] = field(default_factory=dict)

    @property
    def emitted(self) -> int:
        return len(self.kept) + len(self.invented)

    @property
    def ok(self) -> bool:
        return not self.invented and not self.floor_guard_tripped


def audit(upstream: list[str], output: str, instrument: Instrument = DEFAULT,
          *, min_output_chars: int = MIN_OUTPUT_CHARS) -> ProvenanceReport:
    up = "\n\n".join(t for t in upstream if t)
    raised = instrument.families(up) if up.strip() else set()
    if len(output) < min_output_chars:
        return ProvenanceReport(raised=raised, kept=set(), discarded=raised,
                                invented=set(), supply=len(raised),
                                traceability=0.0, output_chars=len(output),
                                floor_guard_tripped=True)
    present = instrument.families(output)
    kept = raised & present
    invented = present - raised
    tr = len(kept) / (len(kept) + len(invented)) if (kept or invented) else 1.0
    ev: dict[str, list[str]] = {}
    if hasattr(instrument, "matches"):
        ev = {k: v for k, v in instrument.matches(output).items() if k in invented}
    return ProvenanceReport(raised=raised, kept=kept, discarded=raised - present,
                            invented=invented, supply=len(raised),
                            traceability=tr, output_chars=len(output),
                            invented_evidence=ev)


def audit_record(rec: RunRecord, instrument: Instrument = DEFAULT,
                 **kw) -> ProvenanceReport:
    return audit(rec.upstream, rec.output, instrument, **kw)
