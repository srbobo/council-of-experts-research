"""Behavior lexicon — the pluggable family definitions.

The default is this program's four detectable epistemic families. The regex
sets are byte-identical to train/build_ledger.py (the canonical instrument);
a domain-specific lexicon replaces FAMILIES wholesale.
"""
import re

FAMILIES: dict[str, list[str]] = {
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


class Lexicon:
    def __init__(self, families: dict[str, list[str]] | None = None):
        self._rx = {k: [re.compile(p, re.I) for p in ps]
                    for k, ps in (families or FAMILIES).items()}

    def families(self, text: str) -> set[str]:
        return {k for k, ps in self._rx.items() if any(r.search(text) for r in ps)}

    def count(self, text: str) -> dict[str, int]:
        return {k: sum(len(r.findall(text)) for r in ps) for k, ps in self._rx.items()}

    def matches(self, text: str) -> dict[str, list[str]]:
        """Family -> matched phrases. Used by the gate to build evidence-
        specific feedback (a generic warning is Cell 17's failed clause)."""
        out: dict[str, list[str]] = {}
        for k, ps in self._rx.items():
            hits = [m.group(0) for r in ps for m in r.finditer(text)]
            if hits:
                out[k] = hits[:5]
        return out


DEFAULT = Lexicon()
