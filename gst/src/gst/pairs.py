"""C2 -- minimal pairs and span-masked preference training.

Why whole-sequence preference training keeps failing on this behavior:
a DPO/ORPO margin is a sum over all tokens, so when the property occupies a
small fraction f of the completion, roughly (1-f) of the margin can be earned
on style, length, and phrasing. The optimizer takes the cheap route. The
result is the learning-acting dissociation measured twice in the originating
program -- preference accuracy climbing from 0.48 to 0.94 while the emitted
behavior did not move at all.

Two repairs, and they are redundant on purpose so that either one alone is
sufficient:

  minimal pairs   chosen and rejected are identical outside one edited span,
                  so there is no off-feature margin to earn.
  masked loss     the objective is summed only over the edited span, so no
                  gradient can flow to off-feature tokens even if one existed.

`diagnose_pair` measures how much off-feature margin a pair set actually
offers. Run it on your existing preference data before training: if the
off-feature fraction is high, this module predicts your run will move
ranking metrics and nothing else.
"""
from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .corpus import CounterfactualItem
from .instruments import DEFAULT, Instrument
from .measure import _sentences

_TOK = re.compile(r'\S+')


@dataclass
class MinimalPair:
    prompt: str
    chosen: str
    rejected: str
    kind: str                                   # "invention" | "drop"
    family: str = ""
    chosen_spans: list[tuple[int, int]] = field(default_factory=list)
    rejected_spans: list[tuple[int, int]] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"prompt": self.prompt, "chosen": self.chosen,
                "rejected": self.rejected, "kind": self.kind, "family": self.family,
                "chosen_spans": [list(s) for s in self.chosen_spans],
                "rejected_spans": [list(s) for s in self.rejected_spans],
                "meta": self.meta}


@dataclass
class PairDiagnosis:
    n_pairs: int
    differing_token_frac: float
    off_feature_frac: float
    length_ratio: float
    minimal: bool
    notes: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if self.minimal:
            return ("MINIMAL -- essentially all of the preference margin sits on "
                    "the property. Whole-sequence training is defensible here.")
        return (f"DILUTED -- {self.off_feature_frac:.0%} of the differing tokens "
                "carry no property content. A margin this shaped is satisfiable "
                "off-feature; expect ranking metrics to move and behavior not to. "
                "Use minimal pairs, or mask the loss to the property spans.")


def make_drop_pair(reference: str, item: CounterfactualItem,
                   instrument: Instrument = DEFAULT) -> list[MinimalPair]:
    """chosen = reference; rejected = reference minus one SOURCED qualification.

    Teaches preservation: dropping something the upstream raised is the error.
    """
    out: list[MinimalPair] = []
    sents = _sentences(reference)
    spans = instrument.spans(reference)
    for fam in sorted(item.target_families):
        hit = next(((a, b) for a, b in sents
                    if any(a <= st < b and k == fam for st, _e, k in spans)), None)
        if hit is None:
            continue
        a, b = hit
        rejected = (reference[:a] + reference[b:]).strip()
        if len(rejected) < 200:
            continue
        out.append(MinimalPair(prompt=_prompt_for(item), chosen=reference,
                               rejected=rejected, kind="drop", family=fam,
                               chosen_spans=[(a, b)], rejected_spans=[],
                               meta={"supply": item.supply}))
    return out


def make_invention_pair(reference: str, item: CounterfactualItem,
                        injections: dict[str, str],
                        instrument: Instrument = DEFAULT) -> list[MinimalPair]:
    """chosen = reference; rejected = reference plus one UNSOURCED qualification.

    Teaches conditionality: adding a qualification the upstream never raised is
    the error, even when the sentence is true. `injections` maps family name to
    a sentence exhibiting it -- supply your own so the phrasing matches your
    domain rather than this kit's.
    """
    out: list[MinimalPair] = []
    sents = _sentences(reference)
    if not sents:
        return out
    insert_at = sents[min(1, len(sents) - 1)][0]
    for fam, sentence in sorted(injections.items()):
        if fam in item.target_families:
            continue                                  # sourced: not invention
        if fam not in instrument.families(sentence):
            continue                                  # injection must be detectable
        rejected = reference[:insert_at] + sentence.strip() + " " + reference[insert_at:]
        out.append(MinimalPair(prompt=_prompt_for(item), chosen=reference,
                               rejected=rejected, kind="invention", family=fam,
                               chosen_spans=[],
                               rejected_spans=[(insert_at,
                                                insert_at + len(sentence.strip()))],
                               meta={"supply": item.supply}))
    return out


def _prompt_for(item: CounterfactualItem) -> str:
    body = "\n\n".join(f"--- SPECIALIST CONTRIBUTION ---\n{t}"
                       for t in item.upstream if t)
    return body


def diagnose_pair(chosen: str, rejected: str, instrument: Instrument = DEFAULT,
                  *, sentence_level: bool = True) -> tuple[float, float, float]:
    """(differing_token_frac, off_feature_frac, length_ratio) for one pair.

    "Feature" here means exactly what `char_mask` means by it -- by default the
    whole sentence carrying the property, not the matched phrase inside it. The
    two must agree: measuring dilution against bare marker spans while masking
    the loss over sentences would report a clean single-sentence edit as ~90%
    off-feature and send you chasing a problem you had already solved.
    """
    ct = [(m.start(), m.end(), m.group(0)) for m in _TOK.finditer(chosen)]
    rt = [(m.start(), m.end(), m.group(0)) for m in _TOK.finditer(rejected)]
    sm = difflib.SequenceMatcher(a=[t[2] for t in ct], b=[t[2] for t in rt])
    diff_c: list[tuple[int, int]] = []
    diff_r: list[tuple[int, int]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        diff_c += [(ct[i][0], ct[i][1]) for i in range(i1, i2)]
        diff_r += [(rt[j][0], rt[j][1]) for j in range(j1, j2)]
    total = len(ct) + len(rt)
    ndiff = len(diff_c) + len(diff_r)
    if ndiff == 0:
        return 0.0, 0.0, 1.0
    cs = char_mask(chosen, instrument, sentence_level=sentence_level)
    rs = char_mask(rejected, instrument, sentence_level=sentence_level)
    on = sum(1 for a, b in diff_c if any(not (b <= s or a >= e) for s, e in cs))
    on += sum(1 for a, b in diff_r if any(not (b <= s or a >= e) for s, e in rs))
    lr = len(chosen) / len(rejected) if rejected else float("inf")
    return ndiff / total, 1.0 - on / ndiff, lr


def diagnose(pairs: list[tuple[str, str]],
             instrument: Instrument = DEFAULT) -> PairDiagnosis:
    """Run this on preference data BEFORE training it."""
    if not pairs:
        return PairDiagnosis(0, float("nan"), float("nan"), float("nan"), False,
                             ["no pairs supplied"])
    d, o, lr = [], [], []
    for c, r in pairs:
        a, b, c2 = diagnose_pair(c, r, instrument)
        d.append(a)
        o.append(b)
        lr.append(c2)
    from . import stats
    off = stats.median(o)
    notes: list[str] = []
    ratio = stats.median(lr)
    if abs(ratio - 1.0) > 0.15:
        notes.append(f"median length ratio {ratio:.2f}: chosen and rejected differ "
                     "systematically in length, which is itself an off-feature "
                     "signal the optimizer can exploit")
    minimal = off < 0.15
    return PairDiagnosis(n_pairs=len(pairs), differing_token_frac=stats.median(d),
                         off_feature_frac=off, length_ratio=ratio, minimal=minimal,
                         notes=notes)


# --- masked loss ----------------------------------------------------------

def char_mask(text: str, instrument: Instrument = DEFAULT, *,
              sentence_level: bool = True) -> list[tuple[int, int]]:
    """Character spans the loss should cover.

    Sentence-level by default: a marker phrase alone is too narrow a target
    and trains phrase production rather than the behavior -- the same mistake
    as rewarding markers.
    """
    spans = instrument.spans(text)
    if not spans:
        return []
    if not sentence_level:
        return [(a, b) for a, b, _ in spans]
    return [(a, b) for a, b in _sentences(text)
            if any(a <= st < b for st, _e, _k in spans)]


def token_mask(text: str, offsets: list[tuple[int, int]],
               spans: list[tuple[int, int]]) -> list[int]:
    """Convert char spans to a 0/1 token mask given a tokenizer's offset
    mapping (HuggingFace fast tokenizers: `return_offsets_mapping=True`).

    Kept dependency-free on purpose -- you pass the offsets, this returns the
    mask, and no tokenizer is imported here.
    """
    out = []
    for a, b in offsets:
        out.append(1 if any(not (b <= s or a >= e) for s, e in spans) else 0)
    return out


def masked_loss_recipe() -> str:
    """The trainer-side change, stated so it can be applied to any DPO/ORPO
    implementation without shipping a fork."""
    return (
        "Span-masked preference loss:\n"
        "  1. Tokenize chosen and rejected with return_offsets_mapping=True.\n"
        "  2. mask = gst.pairs.token_mask(text, offsets, gst.pairs.char_mask(text)).\n"
        "  3. Where the implementation computes per-token logprobs and sums them\n"
        "     into a sequence logprob, multiply by the mask before summing:\n"
        "         seq_lp = (per_token_lp * mask).sum(-1)\n"
        "     rather than per_token_lp.sum(-1).\n"
        "  4. Skip any pair whose mask is all zeros on BOTH sides -- it carries no\n"
        "     property signal and contributes only noise.\n"
        "  5. Normalize by mask.sum() only if the reference implementation\n"
        "     length-normalizes; mixing the two changes the effective beta.\n"
        "Sanity check before the run: gst.pairs.diagnose(pairs).minimal must be\n"
        "True, or the masking is compensating for pair construction that should\n"
        "have been fixed instead."
    )


def export_jsonl(pairs: list[MinimalPair], path: str | Path) -> int:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as fh:
        for pr in pairs:
            fh.write(json.dumps(pr.to_dict(), ensure_ascii=False) + "\n")
    return len(pairs)
