"""GST -- measurement kit and interventions for epistemic distortion at the
writing step of lead-council architectures.

The framework in one paragraph. When a model writes a final answer over other
components' prose, it does not transport their epistemic content; it emits a
shrinkage estimate of how much such an answer should carry, weighting its own
prior against the supplied evidence. Measure that with three parameters and
you know which of five interventions your system needs.

    y = w*s + c        w  evidence weight        s  upstream supply level
                       c  prior fill             y  emitted level

Quickstart:

    from gst import measure_all
    from gst.adapters import FieldMap, from_jsonl

    fmap = FieldMap(upstream="specialists", output="final", prompt_id="task")
    records = from_jsonl("runs.jsonl", fmap)
    card = measure_all(records, system="my-pipeline")
    print(card.render())
    for line in card.recommendations(can_train=True):
        print("-", line)

Nothing in the core requires a dependency. The optional NLI second instrument
does; install with `pip install gst[nli]`, and read the two-instrument rule in
`gst.instruments` before reporting any verdict.
"""
from .audit import MIN_OUTPUT_CHARS, ProvenanceReport, audit, audit_record
from .card import ParameterCard, measure_all
from .instruments import (
                          EPISTEMIC_QUALIFICATION,
                          SOURCE_ATTRIBUTION,
                          CallableInstrument,
                          ConsensusInstrument,
                          Instrument,
                          RegexInstrument,
)
from .measure import blindspot, clean_rate, shrinkage, span_fraction
from .path import PathAudit, PathRecord, assert_path, audit_paths
from .record import RunRecord, partition, validate
from .select import annotation_for, aselect, select, strip_annotation

__version__ = "0.1.0"

__all__ = [
    "RunRecord", "validate", "partition",
    "Instrument", "RegexInstrument", "CallableInstrument", "ConsensusInstrument",
    "EPISTEMIC_QUALIFICATION", "SOURCE_ATTRIBUTION",
    "audit", "audit_record", "ProvenanceReport", "MIN_OUTPUT_CHARS",
    "shrinkage", "span_fraction", "blindspot", "clean_rate",
    "measure_all", "ParameterCard",
    "assert_path", "audit_paths", "PathRecord", "PathAudit",
    "select", "aselect", "annotation_for", "strip_annotation",
    "__version__",
]
