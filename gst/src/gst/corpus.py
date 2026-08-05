"""C1 -- counterfactual corpus construction.

The shrinkage law's root cause is that on ordinary text, topic and register
predict how much qualification an answer carries. A writer that leans on that
correlation is not malfunctioning; it is doing correct statistics. So the
intervention is not to instruct against the prior but to train on a
distribution where the prior earns nothing: the SAME task appearing at
several supply levels, with references that match supply exactly.

On that distribution the likelihood-optimal qualification policy is w=1, c=0.
That is a claim about the training signal, not a promise of transfer -- which
is what the held-out refit in `gst.measure.shrinkage` is for.

Construction is programmatic: it edits upstream text you already log, and
needs no model in the loop.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from .instruments import DEFAULT, Instrument
from .measure import _sentences
from .record import RunRecord


@dataclass
class CounterfactualItem:
    prompt_id: str
    supply: int
    upstream: list[str]
    target_families: set[str]
    provenance: str = ""          # how this variant was made

    def reference_constraint(self) -> str:
        """The specification a reference output must satisfy. Enforceable by
        `verify_reference`; deliberately not auto-generated, because a
        model-written reference inherits the very prior being corrected."""
        fams = ", ".join(sorted(self.target_families)) or "(none)"
        return (f"The reference answer must exhibit exactly these qualification "
                f"families: {fams}. No others. Each must be attributable to the "
                f"upstream text supplied with this item.")


@dataclass
class Corpus:
    items: list[CounterfactualItem] = field(default_factory=list)

    def by_supply(self) -> dict[int, int]:
        out: dict[int, int] = defaultdict(int)
        for it in self.items:
            out[it.supply] += 1
        return dict(sorted(out.items()))

    def decorrelation_report(self) -> DecorrelationReport:
        return decorrelation_report(self)


@dataclass
class DecorrelationReport:
    n_items: int
    n_prompts: int
    supply_levels: list[int]
    normalized_mi: float
    balanced: bool
    notes: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if not self.balanced:
            return ("NOT DECORRELATED -- topic still predicts supply, so training "
                    "on this corpus can be satisfied by the prior it is meant to "
                    "remove")
        return "DECORRELATED (topic carries no information about supply)"


def ablate(text: str, instrument: Instrument = DEFAULT,
           remove: set[str] | None = None) -> str:
    """Drop sentences carrying the named families (all, if unspecified).

    Sentence-level rather than phrase-level on purpose: excising a phrase
    leaves ungrammatical residue that a model reads as a distribution shift,
    which would confound supply with fluency.
    """
    spans = instrument.spans(text)
    if remove is not None:
        spans = [s for s in spans if s[2] in remove]
    if not spans:
        return text
    sents = _sentences(text)
    keep = [(a, b) for a, b in sents
            if not any(a <= st < b for st, _e, _k in spans)]
    return " ".join(text[a:b].strip() for a, b in keep).strip()


def supply_variants(upstream: list[str], instrument: Instrument = DEFAULT,
                    ) -> list[tuple[int, list[str], set[str]]]:
    """Matched variants of one item spanning supply levels.

    Returns [(supply, upstream_variant, families_present)] from the full text
    down to zero, removing one family at a time. Removal order is sorted so
    the construction is deterministic and reproducible across machines.
    """
    present = sorted(instrument.families("\n\n".join(t for t in upstream if t)))
    out: list[tuple[int, list[str], set[str]]] = []
    for i in range(len(present), -1, -1):
        keep = set(present[:i])
        drop = set(present) - keep
        variant = [ablate(t, instrument, remove=drop) if drop else t for t in upstream]
        got = instrument.families("\n\n".join(v for v in variant if v))
        out.append((len(got), variant, got))
    return out


def build_corpus(records: list[RunRecord], instrument: Instrument = DEFAULT, *,
                 min_variant_chars: int = 200) -> Corpus:
    """One record in, up to (k+1) matched supply variants out."""
    corpus = Corpus()
    seen: set[str] = set()
    for rec in records:
        if rec.prompt_id in seen:
            continue                      # one variant family per task
        seen.add(rec.prompt_id)
        for supply, variant, fams in supply_variants(rec.upstream, instrument):
            if sum(len(v) for v in variant) < min_variant_chars:
                continue
            corpus.items.append(CounterfactualItem(
                prompt_id=rec.prompt_id, supply=supply, upstream=variant,
                target_families=fams,
                provenance=f"ablation from {rec.run_id}"))
    return corpus


def decorrelation_report(corpus: Corpus) -> DecorrelationReport:
    """Does topic still predict supply? Normalized mutual information between
    prompt_id and supply level, which is the property that makes C1 work.

    Zero means a model cannot infer how much qualification to emit from what
    the question is about -- it must read the upstream text. Anything much
    above zero means the corpus preserves the shortcut.
    """
    import math
    n = len(corpus.items)
    if n == 0:
        return DecorrelationReport(0, 0, [], float("nan"), False, ["empty corpus"])
    joint: dict[tuple[str, int], int] = defaultdict(int)
    pm: dict[str, int] = defaultdict(int)
    sm: dict[int, int] = defaultdict(int)
    for it in corpus.items:
        joint[(it.prompt_id, it.supply)] += 1
        pm[it.prompt_id] += 1
        sm[it.supply] += 1
    mi = 0.0
    for (p, s), c in joint.items():
        pxy = c / n
        mi += pxy * math.log(pxy / ((pm[p] / n) * (sm[s] / n)))
    hs = -sum((v / n) * math.log(v / n) for v in sm.values() if v)
    nmi = mi / hs if hs > 0 else 0.0
    notes: list[str] = []
    balanced = nmi < 0.15
    if not balanced:
        notes.append(f"normalized MI {nmi:.3f}: prompts do not cover supply levels "
                     "evenly. Balance by dropping variants until each prompt "
                     "contributes to the same set of levels.")
    counts = sorted({v for v in sm.values()})
    if len(counts) > 1 and counts[-1] > 3 * max(1, counts[0]):
        notes.append(f"supply levels are unbalanced in size ({dict(sorted(sm.items()))}); "
                     "the regression will be dominated by the largest stratum")
    if n < 1000:
        notes.append(f"{n} items: below the >=1000 scale the framework specifies. "
                     "Every training attempt in the originating program that ran at "
                     "49-88 items produced no behavioral change.")
    return DecorrelationReport(n_items=n, n_prompts=len(pm),
                               supply_levels=sorted(sm), normalized_mi=nmi,
                               balanced=balanced, notes=notes)


def verify_reference(item: CounterfactualItem, reference: str,
                     instrument: Instrument = DEFAULT) -> tuple[bool, str]:
    """Check a candidate reference satisfies Q_out == Q_in for its item."""
    got = instrument.families(reference)
    if got == item.target_families:
        return True, "ok"
    missing = item.target_families - got
    extra = got - item.target_families
    parts = []
    if missing:
        parts.append(f"missing {sorted(missing)}")
    if extra:
        parts.append(f"unsourced {sorted(extra)}")
    return False, "; ".join(parts)


_WS = re.compile(r'\s+')


def normalize(text: str) -> str:
    return _WS.sub(" ", text).strip()
