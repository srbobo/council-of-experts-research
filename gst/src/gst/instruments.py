"""Instruments — pluggable detectors for the property class under study.

The framework is not about hedging. It is about any countable property that
upstream components can supply and a writer can preserve, discard, or
invent: epistemic qualification, source attribution, numeric provenance,
safety caveats. Swapping the property class means swapping the instrument.

Two rules are enforced by construction elsewhere in this kit and stated here
because they are the reason `Instrument` carries a `name`:

  1. A verdict needs two instruments. One instrument measuring itself is a
     tautology, not a result.
  2. The instrument that generates corrective feedback may never grade
     compliance with that feedback. In the originating program a regex-fed
     revision loop removed 0.88 families by its own count while an
     independent instrument saw no change -- and an audit then showed that
     instrument had never detected the behavior pre-revision either, so it
     corroborated nothing. Manual inspection settled it: the content mostly
     survived in rewording, and one flagged case was the detector's own
     false positive. Rule 1 exists precisely because a "second instrument"
     is only as good as its demonstrated sensitivity to the construct.
"""
from __future__ import annotations

import re
from typing import Protocol, runtime_checkable


@runtime_checkable
class Instrument(Protocol):
    """Detects which families of the property class a text exhibits."""

    name: str

    def families(self, text: str) -> set[str]: ...

    def spans(self, text: str) -> list[tuple[int, int, str]]:
        """(start, end, family) character offsets. Needed for span measurement
        and for masked-loss training; may return [] if unsupported."""
        ...


# --- The default property class: epistemic qualification -------------------
# Four families the originating program validated as detectable on both a
# regex and an NLI instrument. A fifth (vocabulary precision) sat below
# detection on both and is deliberately absent: shipping an undetectable
# family invites unfalsifiable claims about it.

EPISTEMIC_QUALIFICATION: dict[str, list[str]] = {
    "cutoff": [r'training[- ]?cut[- ]?off', r'knowledge cut[- ]?off',
               r'may (?:be |have )(?:stale|outdated|evolved)', r'post[- ]?cut[- ]?off',
               r'after my training', r'verify (?:current|latest|recent)',
               r'as of (?:my )?(?:training|knowledge|2024|2025)'],
    "modeled": [r'modell?ed at', r'\bassume[ds]? (?:that|the)',
                r'\bassuming (?:that|the|a |an |\d)', r'under the assumption',
                r'this assume[ds]', r'\bwe assume\b', r'\bhypothetical[ly]?\b'],
    "jurisd": [r'\bUK\s?GDPR\b', r'\bEU\s?GDPR\b', r'post[- ]Brexit',
               r'each\s+(?:jurisdiction|country|state|regime)', r'preempt(?:ion|s|ed)'],
    "hedging": [r'(?:false[- ]positive|false[- ]negative)', r'alert fatigue',
                r'real[- ]world\s+(?:evidence|data)', r'sensitivity (?:analysis|range|to|of)',
                r'low/?high (?:case|scenario|estimate)', r'\b±\s?\d',
                r'(?:may|might|could)\s+(?:vary|differ|change)'],
}

# A worked second property class, shipped so the kit demonstrates on arrival
# that it is not hedging-specific. Attribution: does the writer mark where a
# claim came from?
SOURCE_ATTRIBUTION: dict[str, list[str]] = {
    "named_source": [r'\baccording to\b', r'\bper the\b', r'\bcites?\b',
                     r'\bas reported by\b', r'\bsource:\s'],
    "seat_credit": [r'\b(?:the )?(?:healthcare|legal|finance|clinical|medical)'
                    r'\s+(?:seat|specialist|expert|analysis)\b'],
    "quantified": [r'\b\d+(?:\.\d+)?\s?%', r'\$\s?\d', r'\bn\s?=\s?\d+'],
    "uncertainty_owner": [r'\b(?:they|the specialist|the analysis)\s+(?:notes?|flags?|warns?)\b'],
}


class RegexInstrument:
    """Lexicon-backed detection. Fast, transparent, and -- documented from the
    originating program -- evadable by paraphrase under optimization pressure.
    Fine as a measurement instrument; never use it alone inside a loop the
    model can see."""

    def __init__(self, families: dict[str, list[str]] | None = None,
                 name: str = "regex"):
        self.name = name
        self.family_names = tuple((families or EPISTEMIC_QUALIFICATION).keys())
        self._rx = {k: [re.compile(p, re.I) for p in ps]
                    for k, ps in (families or EPISTEMIC_QUALIFICATION).items()}

    def families(self, text: str) -> set[str]:
        return {k for k, ps in self._rx.items() if any(r.search(text) for r in ps)}

    def count(self, text: str) -> dict[str, int]:
        return {k: sum(len(r.findall(text)) for r in ps) for k, ps in self._rx.items()}

    def spans(self, text: str) -> list[tuple[int, int, str]]:
        out = [(m.start(), m.end(), k)
               for k, ps in self._rx.items() for r in ps for m in r.finditer(text)]
        return sorted(out)

    def matches(self, text: str, limit: int = 5) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for k, ps in self._rx.items():
            hits = [m.group(0) for r in ps for m in r.finditer(text)]
            if hits:
                out[k] = hits[:limit]
        return out


class CallableInstrument:
    """Adapter for any detector you already have: an LLM judge, a classifier,
    an embedding-similarity rule. Supply a function text -> set[family]."""

    def __init__(self, fn, name: str, family_names: tuple[str, ...] = ()):
        self._fn = fn
        self.name = name
        self.family_names = family_names

    def families(self, text: str) -> set[str]:
        return set(self._fn(text))

    def spans(self, text: str) -> list[tuple[int, int, str]]:
        return []


class ConsensusInstrument:
    """k-of-n agreement across instruments with weakly dependent blind spots.

    This is the object the framework says to put in a reward or a selector:
    joint evasion is the product of the individual blind-spot rates rather
    than any one of them. Requires >= 2 instruments by construction."""

    def __init__(self, instruments: list, k: int = 2, name: str = "consensus"):
        if len(instruments) < 2:
            raise ValueError("consensus requires >= 2 instruments; one instrument "
                             "grading itself is not a verdict")
        if not 1 <= k <= len(instruments):
            raise ValueError(f"k must be in [1, {len(instruments)}]")
        self.instruments = instruments
        self.k = k
        self.name = name

    def families(self, text: str) -> set[str]:
        votes: dict[str, int] = {}
        for ins in self.instruments:
            for fam in ins.families(text):
                votes[fam] = votes.get(fam, 0) + 1
        return {f for f, v in votes.items() if v >= self.k}

    def spans(self, text: str) -> list[tuple[int, int, str]]:
        keep = self.families(text)
        out: list[tuple[int, int, str]] = []
        for ins in self.instruments:
            out += [s for s in ins.spans(text) if s[2] in keep]
        return sorted(set(out))


DEFAULT = RegexInstrument()
