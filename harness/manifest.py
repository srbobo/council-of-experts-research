"""Epistemic manifest — deterministic, quotation-only disclosure layer.

The harness's deliverable after the intervention picture closed: prompt
failed (17), weights failed under three objective classes (6b/11/18),
runtime revision teaches evasion (19), and the decision instruction moves
form but not commitment (20). What remains is detection and disclosure.

The manifest is assembled mechanically from the trace — no generation, so it
cannot invent and makes no demand a model could game:
  - RESTORED: qualifications specialists raised that the answer omitted,
    quoted verbatim with attribution
  - FLAGGED: qualification present in the answer that no specialist raised
  - CITATION MARKS: figure-bearing citations checked against the NAMED
    specialist's text (verified / unsupported / unchecked-qualitative)
"""
import re
from dataclasses import dataclass, field

from .audit import audit
from .lexicon import Lexicon, DEFAULT

CITE = re.compile(r'\b(healthcare|clinical|medical|legal|financial|finance)\s+'
                  r'(?:specialist|contribution|analysis|seat)\b[^.]*?\.', re.I)
SEAT_ALIAS = {'healthcare': 'healthcare', 'clinical': 'healthcare',
              'medical': 'healthcare', 'legal': 'legal', 'law': 'legal',
              'finance': 'finance', 'financial': 'finance'}
NUM = re.compile(r'\$?\d[\d,\.]+\s?(?:k|K|%|m|M|bn|million|billion)?')


@dataclass
class RestoredItem:
    family: str
    seat: str
    quote: str          # verbatim specialist sentence


@dataclass
class FlaggedItem:
    family: str
    phrases: list[str]
    answer_excerpt: str


@dataclass
class CitationMark:
    sentence: str
    seat: str
    status: str         # "verified" | "unsupported" | "unchecked-qualitative"


@dataclass
class Manifest:
    restored: list[RestoredItem] = field(default_factory=list)
    flagged: list[FlaggedItem] = field(default_factory=list)
    citations: list[CitationMark] = field(default_factory=list)
    supply: int = 0
    traceability: float = 1.0


def _sentences(text: str):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 30]


def build_manifest(seat_map: dict[str, str], final_output: str,
                   lexicon: Lexicon = DEFAULT) -> Manifest:
    rep = audit(list(seat_map.values()), final_output, lexicon)
    m = Manifest(supply=rep.supply, traceability=rep.traceability)

    for fam in sorted(rep.discarded):
        for seat, txt in seat_map.items():
            for sent in _sentences(txt):
                if fam in lexicon.families(sent):
                    m.restored.append(RestoredItem(fam, seat, sent[:400]))
                    break            # one quote per (family, seat)

    ans_sents = _sentences(final_output)
    for fam in sorted(rep.invented):
        phrases = rep.invented_evidence.get(fam, [])
        excerpt = next((s for s in ans_sents
                        if any(p.lower() in s.lower() for p in phrases)), "")
        m.flagged.append(FlaggedItem(fam, phrases[:4], excerpt[:400]))

    for cm in CITE.finditer(final_output):
        sent = cm.group(0)
        seat = SEAT_ALIAS.get(re.match(r'\w+', sent).group(0).lower())
        if seat not in seat_map:
            continue
        figs = set(NUM.findall(sent))
        if not figs:
            m.citations.append(CitationMark(sent[:300], seat, "unchecked-qualitative"))
        elif figs & set(NUM.findall(seat_map[seat])):
            m.citations.append(CitationMark(sent[:300], seat, "verified"))
        else:
            m.citations.append(CitationMark(sent[:300], seat, "unsupported"))
    return m
