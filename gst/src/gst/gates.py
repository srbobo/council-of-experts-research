"""Delivery gates for the expert-seat harness (§5 of the architecture).

Registered: RUNBOOK_PAPER_HARDENING.md "GATES-AS-CODE VALIDATION"
(commit 3490b97, acceptance criteria frozen before any computation).

Both gates filter DELIVERY only. Per instrument rule 2 (Cell 19),
nothing a gate produces is ever fed back to any model as feedback; the
blocklist grows only by committed manual classification.
"""
from __future__ import annotations

import unicodedata

CONTENT_GATE_JUDGES = ("gpt-oss:20b", "qwen3-vl:30b-a3b-instruct")

CONTENT_GATE_PROMPT = (
    "Below are a specialist's EARLIER CONTRIBUTION and their FOLLOW-UP "
    "REPLY to a clarification request. Does the follow-up state at least "
    "one specific fact, constraint, number, or mechanism that is NOT "
    "already present in the earlier contribution? Reply with exactly one "
    "word: YES or NO.")

# Cumulative value/format folding: narrow spaces (C47), Unicode hyphens
# (C53/C57), NFKC. Spaced-percent collapse is applied by callers that
# match numeric values (vdeep in cell 59); span matching here folds the
# same surface.
_HYPHENS = "‐‑‒–—―−"


def fold(t: str) -> str:
    t = unicodedata.normalize("NFKC", t or "")
    for ch in _HYPHENS:
        t = t.replace(ch, "-")
    for ch in (" ", " ", " "):
        t = t.replace(ch, " ")
    t = t.replace("-", " ").replace("*", "").replace(",", "")
    return " ".join(t.lower().split())


def _parse_yesno(txt: str | None) -> str | None:
    words = {w.strip(".,;:!?()'\"*").upper()
             for w in (txt or "").split()}
    hits = [w for w in ("YES", "NO") if w in words]
    return hits[0] if len(hits) == 1 else None


def content_gate(chat, earlier: str, reply: str,
                 judges=CONTENT_GATE_JUDGES) -> str:
    """Return 'PASS' (deliver), 'DROP' (withhold), or 'QUARANTINE'
    (deliver flagged — the gate fails open on judge disagreement or
    parse failure)."""
    body = (f"EARLIER CONTRIBUTION:\n{earlier}\n\n"
            f"FOLLOW-UP REPLY:\n{reply}")
    votes = []
    for j in judges:
        v = _parse_yesno(chat(j, CONTENT_GATE_PROMPT, body,
                              temperature=0.0, max_tokens=2048))
        votes.append(v)
    if votes[0] is None or votes[1] is None or votes[0] != votes[1]:
        return "QUARANTINE"
    return "PASS" if votes[0] == "YES" else "DROP"


def blocklist_gate(reply: str, blocklist: list[str]) -> list[str]:
    """Return the blocklisted spans present in the reply (empty list =
    deliver). Matching under the cumulative format folding."""
    lo = fold(reply)
    return [s for s in blocklist if fold(s) in lo]


# Seed list: the committed Cell 54/56 classifications
# (docs/CELL56_CLASSIFICATION.json). Grows ONLY by committed manual
# classification of new confirmed fabrications.
FABRICATION_BLOCKLIST = ["Rosenbaum v. Uber", "Klein v. Lyft",
                         "Wright v. ICO"]
