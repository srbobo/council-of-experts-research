"""Provenance auditing — the preserved / discarded / invented decomposition.

The measurement that produced this program's central findings: partial
compensation (invention monotone in scarcity) and the instruction
dissociation (preservation responds to instructions, invention does not).
"""
from dataclasses import dataclass, field

from .lexicon import Lexicon, DEFAULT

MIN_OUTPUT_CHARS = 500   # floor guard: rates on shorter outputs are refused
                         # (BioMistral incident: 208-char fragments, 18x distortion)


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
    def ok(self) -> bool:
        return not self.invented and not self.floor_guard_tripped


def audit(seat_texts: list[str], final_output: str,
          lexicon: Lexicon = DEFAULT) -> ProvenanceReport:
    seats = " ".join(t for t in seat_texts if t)
    raised = lexicon.families(seats) if seats.strip() else set()
    if len(final_output) < MIN_OUTPUT_CHARS:
        return ProvenanceReport(raised=raised, kept=set(), discarded=raised,
                                invented=set(), supply=len(raised),
                                traceability=0.0, output_chars=len(final_output),
                                floor_guard_tripped=True)
    present = lexicon.families(final_output)
    kept = raised & present
    invented = present - raised
    tr = len(kept) / (len(kept) + len(invented)) if (kept or invented) else 1.0
    ev = {k: v for k, v in lexicon.matches(final_output).items() if k in invented}
    return ProvenanceReport(raised=raised, kept=kept, discarded=raised - present,
                            invented=invented, supply=len(raised),
                            traceability=tr, output_chars=len(final_output),
                            invented_evidence=ev)
