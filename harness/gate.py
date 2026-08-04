"""Runtime provenance gate — the intervention class left standing.

Instruction failed generically (Cell 17); training failed under three
objective classes (Cells 6b, 11, 18). The gate is reactive and evidence-
specific: it names the exact invented phrases in THIS draft and demands they
be removed or grounded. Only the writing call is re-run; upstream is frozen.
Residual invention is annotated, never silently passed.
"""
from dataclasses import dataclass, field

from .audit import ProvenanceReport, audit
from .lexicon import Lexicon, DEFAULT

FAMILY_DESC = {
    "cutoff": "training-cutoff / recency disclaimers",
    "modeled": "assumption or modeling language",
    "jurisd": "jurisdictional or regime distinctions",
    "hedging": "hedging or variability qualifiers",
}


@dataclass
class GateRecord:
    pre: ProvenanceReport
    post: ProvenanceReport
    retries: int
    feedback_sent: list[str] = field(default_factory=list)
    residual_invented: set[str] = field(default_factory=set)
    annotated: bool = False


def feedback_for(report: ProvenanceReport) -> str:
    lines = ["REVISION REQUIRED. Your draft introduced the following "
             "qualifications that NO specialist raised:"]
    for fam in sorted(report.invented):
        ev = ", ".join(f'"{p}"' for p in report.invented_evidence.get(fam, [])[:3])
        lines.append(f"- {FAMILY_DESC.get(fam, fam)}: {ev}")
    lines.append(
        "Remove each of these, or ground it by explicitly attributing it to a "
        "specific specialist's contribution. Do not add new qualifications. "
        "Keep everything else, including qualifications the specialists DID "
        "raise, exactly as supported.")
    return "\n".join(lines)


def annotation_for(residual: set[str]) -> str:
    fams = ", ".join(FAMILY_DESC.get(f, f) for f in sorted(residual))
    return (f"\n\n---\n*Provenance note: this answer contains {fams} that no "
            f"consulted specialist raised; treat those passages as the "
            f"synthesizer's own framing rather than specialist input.*")


async def gate(seat_texts, draft, rewrite_fn, *, lexicon: Lexicon = DEFAULT,
               max_retries: int = 2) -> tuple[str, GateRecord]:
    """rewrite_fn(draft, feedback) -> new draft (re-runs ONLY the writer)."""
    pre = audit(seat_texts, draft, lexicon)
    rec = GateRecord(pre=pre, post=pre, retries=0)
    out = draft
    while rec.post.invented and rec.retries < max_retries:
        fb = feedback_for(rec.post)
        rec.feedback_sent.append(fb)
        out = await rewrite_fn(out, fb)
        rec.retries += 1
        rec.post = audit(seat_texts, out, lexicon)
    rec.residual_invented = set(rec.post.invented)
    if rec.residual_invented:
        out = out + annotation_for(rec.residual_invented)
        rec.annotated = True
    return out, rec
