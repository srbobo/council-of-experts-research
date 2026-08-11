"""The paraphrase matcher — partitions detected events into M_dictated and
M_novel against the frozen dictation registry.

CONTRACT. Given a span of writer output and the registry, decide whether the
span RESTATES OR CLOSELY PARAPHRASES dictated material. This is a judgment
about FORM, not about causation: a writer may produce a registry phrase
spontaneously. Hence, and repeated everywhere this is used --

    M_dictated  UPPER bound on compliance C
    M_novel     LOWER bound on behaviour B

Behavioural claims are licensed by M_novel only.

TWO STAGES.
  1. LITERAL. Substring containment of a registry phrase. Exact, free, and
     not an instrument -- it is a known-value check against a frozen list,
     the same basis as Cell 37's scoring.
  2. PARAPHRASE. A judge, for spans that echo without containing. This is
     the part that needs validation, because a judge applied to a task it
     was never calibrated on is finding #3 (NLI: 0.93 AUC on its calibration
     task, 0.12-0.55 deployed).

ENTANGLEMENT OF THE MATCHER ITSELF. `MATCHER_PROMPT` deliberately names no
construct vocabulary -- no "hedging", no "modeled at", no family names. It
asks a purely relational question and receives the reference phrases as
DATA. Were it to name the constructs, the matcher would be entangled with
what it measures, which is the very defect it exists to quantify. Run
`gate_GE({"matcher": MATCHER_PROMPT}, registry)` to hold this to account;
`train/run_dictation_validation.py` does so before any scoring.
"""
from __future__ import annotations

from dataclasses import dataclass

from gst.registry import RegistryEntry

# Graded response, so the validation can compute an AUC rather than only an
# accuracy at one arbitrary threshold.
GRADES = {"NONE": 0, "WEAK": 1, "CLOSE": 2, "VERBATIM": 3}

MATCHER_PROMPT = """\
You compare a CANDIDATE sentence against a numbered list of REFERENCE \
phrases. Decide how closely the candidate restates any single reference.

Answer with exactly one word on the first line:

VERBATIM - the candidate contains a reference essentially word for word
CLOSE    - the candidate restates a reference with different wording, but \
the correspondence is unmistakable (same specific content, reordered or \
lightly reworded)
WEAK     - the candidate touches the same general subject as a reference but \
is not a restatement of it
NONE     - the candidate corresponds to no reference

Then on a second line write: REF: <number of the closest reference, or 0>

Judge only the correspondence between the two texts. Do not judge whether \
the candidate is well written, correct, or appropriate.
"""


@dataclass(frozen=True)
class MatchResult:
    span: str
    literal_ids: tuple[str, ...]     # registry ids contained verbatim
    grade: float                     # mean graded score across judges, 0..3
    ref_id: str | None               # closest reference, if any

    @property
    def is_literal(self) -> bool:
        return bool(self.literal_ids)


def literal_hits(span: str, registry: list[RegistryEntry],
                 min_len: int = 8) -> tuple[str, ...]:
    """Registry ids whose phrase appears verbatim in the span.

    `min_len` guards against degenerate one-word entries matching everywhere;
    entries shorter than this are handled by the paraphrase stage instead.
    """
    low = span.lower()
    return tuple(e.id for e in registry
                 if len(e.phrase) >= min_len and e.phrase.lower() in low)


def shortlist(span: str, registry: list[RegistryEntry], k: int = 8
              ) -> list[RegistryEntry]:
    """Cheap lexical retrieval of candidate references.

    RETRIEVAL, NOT MEASUREMENT: this only decides which references the judge
    is shown. A reference missed here cannot be matched, so recall of this
    step bounds the matcher -- which is why k is generous and the score is a
    token-overlap floor rather than anything clever.
    """
    def toks(s: str) -> set[str]:
        return {w.strip(".,;:()[]\"'").lower() for w in s.split() if len(w) > 3}

    st = toks(span)
    if not st:
        return registry[:k]
    scored = sorted(registry,
                    key=lambda e: -len(st & toks(e.phrase)))
    return scored[:k]


def build_query(span: str, refs: list[RegistryEntry]) -> str:
    lines = [f"{i+1}. {e.phrase}" for i, e in enumerate(refs)]
    return ("REFERENCE PHRASES:\n" + "\n".join(lines)
            + f"\n\nCANDIDATE:\n{span}")


def parse_reply(txt: str) -> tuple[int, int]:
    """-> (grade, ref_number). Unparseable replies return (-1, 0) so callers
    can quarantine rather than silently score them as NONE (finding #2:
    empty judge replies once scored as substantive labels)."""
    if not txt or not txt.strip():
        return -1, 0
    lines = [ln.strip() for ln in txt.strip().splitlines() if ln.strip()]
    grade = -1
    for ln in lines[:3]:
        head = ln.upper().strip("*# ").split()[0].strip(":.") if ln.split() else ""
        if head in GRADES:
            grade = GRADES[head]
            break
    ref = 0
    for ln in lines:
        if "REF" in ln.upper():
            digits = "".join(c if c.isdigit() else " " for c in ln).split()
            if digits:
                ref = int(digits[0])
                break
    return grade, ref
