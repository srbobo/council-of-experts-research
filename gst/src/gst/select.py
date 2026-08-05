"""C5 -- verifier-blind best-of-n selection. The universal intervention.

Works on black-box writers, needs no training, and is the only intervention
in the framework that a hosted-API pipeline can adopt unchanged.

The design constraint is structural rather than procedural, so read the
signature carefully: `generate` is a zero-argument sampler. There is no
parameter through which verifier output could reach the model, because the
distinction between selection and feedback is the whole point.

  selection  conditions the OUTPUT distribution. The generator never observes
             the verifier, so it cannot learn to evade a signal it never sees.
  feedback   conditions the POLICY INPUT. The generator observes the
             verifier's findings and -- measured in the originating program --
             moves probability mass into the verifier's blind spot, because
             paraphrasing is a cheaper distributional move than removal.

That measurement: a revision loop quoting matched phrases removed 0.88
families by the instrument that generated the feedback, while manual
inspection showed the content mostly surviving in rewording. (An
entailment detector initially credited with confirming this was later
audited and found insensitive -- it had detected nothing before the
revisions either. The lesson cuts both ways: feedback loops optimize the
visible instrument, and "independent confirmation" requires demonstrated
sensitivity, not just a second detector.)

Residual failures are ANNOTATED, never revised. Annotation is disclosure to
the reader; revision is a feedback channel wearing a different name.
"""
from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field

from .audit import ProvenanceReport, audit
from .instruments import DEFAULT, Instrument


@dataclass
class SelectionResult:
    chosen: str
    chosen_index: int
    reports: list[ProvenanceReport]
    n_sampled: int
    n_clean: int
    annotated: bool = False
    annotation: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return self.n_clean > 0


def _score(rep: ProvenanceReport) -> tuple:
    """Rank candidates: clean first, then fewer inventions, then more
    preserved. Never rewards production of the property for its own sake --
    that reward is what made a whole class of training runs chase markers."""
    return (0 if rep.floor_guard_tripped else 1,
            -len(rep.invented),
            len(rep.kept),
            rep.output_chars)


def select(generate, upstream: list[str], *, n: int = 3,
           instrument: Instrument = DEFAULT, annotate: bool = True,
           min_output_chars: int = 500) -> SelectionResult:
    """Sample n candidates and return the best by provenance. Synchronous.

    `generate` MUST take no arguments. Passing a rewrite-style callable that
    accepts feedback is rejected: that is the failure mode this function
    exists to make impossible.
    """
    _reject_feedback_signature(generate)
    cands = [generate() for _ in range(n)]
    return _finish(cands, upstream, instrument, annotate, min_output_chars)


async def aselect(generate, upstream: list[str], *, n: int = 3,
                  instrument: Instrument = DEFAULT, annotate: bool = True,
                  min_output_chars: int = 500,
                  concurrent: bool = True) -> SelectionResult:
    """Async form. Samples concurrently by default; latency is then one
    sample's, not n."""
    _reject_feedback_signature(generate)
    if concurrent:
        cands = list(await asyncio.gather(*(generate() for _ in range(n))))
    else:
        cands = [await generate() for _ in range(n)]
    return _finish(cands, upstream, instrument, annotate, min_output_chars)


def _finish(cands: list[str], upstream: list[str], instrument: Instrument,
            annotate: bool, floor: int) -> SelectionResult:
    reports = [audit(upstream, c or "", instrument, min_output_chars=floor)
               for c in cands]
    best = max(range(len(cands)), key=lambda i: _score(reports[i]))
    res = SelectionResult(chosen=cands[best], chosen_index=best, reports=reports,
                          n_sampled=len(cands),
                          n_clean=sum(1 for r in reports if r.ok))
    if not reports[best].ok and annotate:
        res.annotation = annotation_for(reports[best])
        res.chosen = cands[best] + res.annotation
        res.annotated = True
    if res.n_clean == 0:
        res.notes.append(f"no clean candidate in {len(cands)} samples; the residual "
                         "is disclosed, not repaired")
    return res


def annotation_for(rep: ProvenanceReport) -> str:
    """Reader-facing disclosure appended to an unclean output.

    Two rules encoded here. The annotation names families rather than quoting
    matched phrases -- quoting is what teaches paraphrase. And it is appended
    after a delimiter so downstream measurement can strip it: an annotation
    that names families would otherwise be counted as the families themselves,
    inflating the very number it discloses.
    """
    if rep.floor_guard_tripped:
        return ("\n\n---\nProvenance note: this response was too short to audit "
                "for source traceability.")
    fams = ", ".join(sorted(rep.invented))
    return ("\n\n---\nProvenance note: the following qualification types appear "
            f"in this response without a source in the specialist material: {fams}. "
            "They may still be correct, but they are not traceable to the "
            "consulted experts.")


ANNOTATION_DELIM = "\n\n---\nProvenance note:"


def strip_annotation(text: str) -> str:
    """Remove a provenance annotation before measuring. Always call this on
    stored outputs; measuring the annotation as content is a real defect that
    inflates preserved-family counts."""
    i = text.rfind(ANNOTATION_DELIM)
    return text[:i] if i >= 0 else text


def _reject_feedback_signature(fn) -> None:
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return
    required = [p for p in sig.parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)]
    if required:
        raise TypeError(
            f"generate must take no required arguments; got {[p.name for p in required]}. "
            "Verifier-blind selection means the sampler cannot receive verifier "
            "output. If you intended a revision loop, that is a feedback channel "
            "and this kit does not provide one -- see gst.select's docstring.")
