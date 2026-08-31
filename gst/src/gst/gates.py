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


CONTENT_GATE_V2_PROMPT = (
    "Below are a specialist's EARLIER CONTRIBUTION and their FOLLOW-UP "
    "REPLY to a clarification request. Quote, verbatim from the "
    "FOLLOW-UP REPLY, the single most specific NEW fact, constraint, "
    "number, or mechanism it states that is not already present in the "
    "earlier contribution. Output only that verbatim quote on one line. "
    "If the follow-up states nothing specific and new, output exactly: "
    "NONE")


def _anchored_quote(quote: str, reply: str, earlier: str) -> bool:
    """Mechanical verification: quote in reply, absent from earlier,
    carrying a concrete anchor (digit, or capitalized token that is not
    sentence-initial in the quote's own casing)."""
    q = (quote or "").strip().strip('"').strip()
    if not q or q.upper() == "NONE" or len(q) < 8:
        return False
    if fold(q) not in fold(reply) or fold(q) in fold(earlier):
        return False
    if any(c.isdigit() for c in q):
        return True
    words = q.split()
    for i, w in enumerate(words):
        core = w.strip('.,;:!?()"\'')
        if not core or not core[0].isupper() or not core[0].isalpha():
            continue
        if i == 0:
            continue
        prev = words[i - 1].rstrip()
        if prev and prev[-1] in ".:!?":
            continue
        return True
    return False


def content_gate_v2(chat, earlier: str, reply: str,
                    judges=CONTENT_GATE_JUDGES) -> str:
    """Extract-then-verify (registration 91a3e3f). PASS iff both judges
    produce a mechanically verified anchored quote; both fail -> DROP;
    split -> QUARANTINE (fails open)."""
    body = (f"EARLIER CONTRIBUTION:\n{earlier}\n\n"
            f"FOLLOW-UP REPLY:\n{reply}")
    oks = []
    for j in judges:
        t = chat(j, CONTENT_GATE_V2_PROMPT, body,
                 temperature=0.0, max_tokens=2048)
        line = next((l.strip() for l in (t or "").splitlines()[::-1]
                     if l.strip()), "")
        oks.append(_anchored_quote(line, reply, earlier))
    if all(oks):
        return "PASS"
    if not any(oks):
        return "DROP"
    return "QUARANTINE"


# Seed list: the committed Cell 54/56 classifications
# (docs/CELL56_CLASSIFICATION.json). Grows ONLY by committed manual
# classification of new confirmed fabrications.
FABRICATION_BLOCKLIST = ["Rosenbaum v. Uber", "Klein v. Lyft",
                         "Wright v. ICO"]
