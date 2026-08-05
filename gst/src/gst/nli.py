"""Zero-shot entailment instrument -- the general second detector.

A regex lexicon detects PHRASES. Under any optimization pressure that can see
the lexicon, phrases are the cheapest thing in the world to change, so a
regex-only verdict measures vocabulary rather than behavior. This module
scores each sentence against a natural-language hypothesis per family, which
moves the question from "did the writer use this wording" to "did the writer
do this thing".

It is not a better instrument -- it is a DIFFERENT one, with a different blind
spot. That is the entire point: `gst.measure.blindspot` multiplies blind-spot
rates only to the extent the instruments fail independently, and
`gst.instruments.ConsensusInstrument` is only worth building out of detectors
that disagree.

Requires the `nli` extra (`pip install gst-kit[nli]`). Heavy imports are lazy,
so importing this module costs nothing until you score something.

    from gst.nli import NLIInstrument
    nli = NLIInstrument(hypotheses={...}, thresholds={...})

Thresholds must be CALIBRATED on labelled data and then FROZEN before use --
choosing them after seeing results is how an instrument becomes an opinion.
And calibration must include an AUC gate on the task the instrument will
actually perform: a threshold fit on labels is meaningless if the underlying
score carries no signal for the construct. Measured cautionary case from the
originating program (Cell 23): thresholds calibrated for chosen-vs-rejected
discrimination (AUC 0.93) were reused for family PRESENCE, where the same
scores turned out to carry no signal at all (per-family presence AUC
0.12-0.55 against reliable judge labels). No threshold can rescue an AUC
below 0.5. Gate on AUC >= 0.75 for the deployed task before shipping any
threshold, and report the AUC beside it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

DEFAULT_MODEL = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
# Reasoning models emit visible scratchpads that were never part of the answer.
# Scoring them credits the writer with content no reader ever saw.
_THINK = re.compile(r"<think>.*?</think>|^.*?</think>", re.DOTALL)

MIN_SENT, MAX_SENT = 20, 600


def sentence_spans(text: str) -> list[tuple[int, int, str]]:
    """(start, end, sentence) over the answer text, scratchpads removed."""
    cleaned = _THINK.sub("", text or "")
    offset = len(text) - len(cleaned) if text else 0
    out: list[tuple[int, int, str]] = []
    pos = 0
    for part in _SENT_SPLIT.split(cleaned):
        i = cleaned.find(part, pos)
        if i < 0:
            continue
        pos = i + len(part)
        s = part.strip()
        if MIN_SENT <= len(s) <= MAX_SENT:
            out.append((offset + i, offset + i + len(part), s))
    return out


@dataclass
class NLIInstrument:
    """Per-sentence entailment scoring with frozen per-family thresholds."""

    hypotheses: dict[str, str]
    thresholds: dict[str, float]
    model: str = DEFAULT_MODEL
    name: str = "nli"
    batch_size: int = 32
    _cache: dict = field(default_factory=dict, repr=False)
    _mod: object = field(default=None, repr=False)
    _tok: object = field(default=None, repr=False)
    _dev: str = field(default="", repr=False)

    @property
    def family_names(self) -> tuple[str, ...]:
        return tuple(self.hypotheses)

    def _load(self):
        if self._mod is None:
            try:
                import torch
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
            except ImportError as e:                       # pragma: no cover
                raise ImportError(
                    "NLIInstrument needs the 'nli' extra: pip install gst-kit[nli]"
                ) from e
            self._tok = AutoTokenizer.from_pretrained(self.model)
            self._dev = ("mps" if torch.backends.mps.is_available()
                         else ("cuda" if torch.cuda.is_available() else "cpu"))
            self._mod = AutoModelForSequenceClassification.from_pretrained(
                self.model).to(self._dev).eval()
        return self._mod, self._tok, self._dev

    def _entail(self, premises: list[str], hypothesis: str) -> list[float]:
        import torch
        mod, tok, dev = self._load()
        out: list[float] = []
        with torch.no_grad():
            for i in range(0, len(premises), self.batch_size):
                chunk = premises[i:i + self.batch_size]
                enc = tok(chunk, [hypothesis] * len(chunk), return_tensors="pt",
                          truncation=True, max_length=512, padding=True).to(dev)
                logits = mod(**enc).logits
                # MNLI label order is (contradiction, neutral, entailment).
                probs = torch.softmax(logits, dim=-1)[:, 2]
                out += [float(p) for p in probs.cpu()]
        return out

    def _scored(self, text: str) -> dict[str, list[float]]:
        key = hash(text)
        if key in self._cache:
            return self._cache[key]
        spans = sentence_spans(text)
        sents = [s for _a, _b, s in spans]
        scores = ({fam: self._entail(sents, hyp) for fam, hyp in self.hypotheses.items()}
                  if sents else {fam: [] for fam in self.hypotheses})
        self._cache[key] = scores
        return scores

    def families(self, text: str) -> set[str]:
        scores = self._scored(text)
        return {fam for fam, ps in scores.items()
                if ps and max(ps) >= self.thresholds[fam]}

    def spans(self, text: str) -> list[tuple[int, int, str]]:
        """Sentence spans whose entailment clears the family threshold."""
        scores = self._scored(text)
        sent_spans = sentence_spans(text)
        out: list[tuple[int, int, str]] = []
        for fam, ps in scores.items():
            thr = self.thresholds[fam]
            for (a, b, _s), p in zip(sent_spans, ps, strict=True):
                if p >= thr:
                    out.append((a, b, fam))
        return sorted(out)
