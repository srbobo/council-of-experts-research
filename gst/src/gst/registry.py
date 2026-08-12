"""The dictation registry — every construct-bearing phrase the system's own
prompts put into the writer's mouth.

WHY THIS EXISTS. Finding #8 (instrument-scaffold entanglement) is not an
instrument defect and no better instrument fixes it. Any measured rate is

    M = C + B

where C is compliance (the scaffold NAMED the phrase and the writer echoed
it) and B is behaviour (the construct appeared unprompted). A phrase echoed
on command is still genuinely an instance of the construct, so a PERFECT
instrument counts it. The difference between C and B is not in the text --
it is in the causal path -- so it must be resolved by design and provenance,
never by detection alone.

This module supplies the provenance half: a frozen, hashed record of what
was dictated, so "did we put these words in its mouth?" is a lookup rather
than an archaeology project.

ON THE NO-REGEX DIRECTIVE (standing, 2026-08-09). Nothing here uses regex as
a natural-language instrument. Extraction is (a) Python `ast` parsing of
source files to recover string constants and (b) character-level scanning
for quote delimiters and literal markers. That is parsing source code and
lifting quoted material out of it -- the same basis as Cell 37's known-value
check, not semantic classification. The one regex touch is `family_hint`,
which runs the legacy lexicon over each entry purely to FLAG entries for
review. It is recorded as a hint, is never a measurement, and no verdict may
rest on it (see RegexInstrument's docstring: screening and instrument
decomposition are its listed appropriate uses).

WHAT THE REGISTRY CANNOT DO. Membership establishes that a phrase WAS
dictated somewhere in the system. It does not establish that any particular
occurrence in an output was CAUSED by that dictation -- a writer may produce
"modeled at" spontaneously.

BOUND DIRECTION -- CORRECTED 2026-08-11, and the correction matters.
An earlier draft of this docstring and of the pre-registration stated
"M_novel is a LOWER bound on B". That is backwards for any matcher whose
misses outnumber its false alarms, which is the empirical case here. The
direction follows from where each error type sends an event:

  - matcher MISSES a paraphrase of dictated material -> that compliance
    event lands in M_novel, inflating it
  - matcher FALSELY flags novel material -> M_novel deflates

Measured (V-A/V-B, `train/run_dictation_validation.py`): misses run ~33% on
literal items while false alarms run ~7%, and corpus-level over-attribution
is 0/2907 spans. Misses dominate. Therefore:

    M_dictated  is a LOWER bound on compliance C
    M_novel     is an UPPER bound on behaviour B

The partition is still decisive in one direction: a SMALL M_novel is strong
evidence that behaviour is small. A large M_novel proves nothing, because
undetected paraphrase inflates it. Claims may be made from a small M_novel;
never from a large one.
"""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

# --- Prompt sources ---------------------------------------------------------
# EXPLICIT, not globbed: a registry that silently changes coverage when a file
# is added is worse than no registry. Vendored third-party code
# (train/llama.cpp/**) is excluded -- it is not part of any pipeline prompt.
# Judge prompts ARE included: a judge is a prompted model, and a judge prompt
# that names the construct entangles the instrument with itself.

PROMPT_SOURCES: tuple[tuple[str, str], ...] = (
    ("council/prompts.py", "LEAD_PLANNER_SYSTEM"),
    ("council/prompts.py", "HEALTHCARE_SYSTEM"),
    ("council/prompts.py", "LEGAL_SYSTEM"),
    ("council/prompts.py", "FINANCE_SYSTEM"),
    ("council/prompts.py", "LEAD_SYNTHESIS_SYSTEM"),
    ("council/prompts.py", "BEHAVIOR_SPEC_ADDENDUM"),
    ("council/prompts.py", "LEAD_DIRECT_ANSWER_SYSTEM"),
    ("council/orchestrator.py", "suffix"),
    ("train/domains.py", "HEALTH_ADD"),
    ("train/domains.py", "HEALTH_STRIP"),
    ("train/domains.py", "FINANCE_ADD"),
    ("train/domains.py", "FINANCE_STRIP"),
    ("train/gen_pairs.py", "REWRITE_ADD"),
    ("train/gen_pairs.py", "REWRITE_STRIP"),
    ("train/gen_lead_pairs.py", "REWRITE_ADD"),
    ("train/gen_lead_pairs.py", "REWRITE_STRIP"),
    ("train/gen_cell11_prompts.py", "GEN_SYSTEM"),
    ("train/run_cell6c.py", "HOT_ADDENDUM"),
    ("train/run_cell8_arch.py", "FLAT_MERGE"),
    ("train/run_cell14_gate.py", "FLAT_MERGE"),
    ("train/run_cell15_load.py", "FLAT_MERGE"),
    ("train/run_cell17_suppress.py", "SUPPRESSION"),
    ("train/run_cell20_decide.py", "DECIDE"),
    ("train/run_cell25_moa.py", "MOA_PROMPT"),
    ("train/run_cell27_ledger.py", "LEDGER_PROTOCOL"),
    ("train/run_cell30_descaffold.py", "WRITER_PROMPT"),
    ("train/run_cell35_injection.py", "PROP_PROMPT"),
    ("train/run_cell35_injection.py", "ATTR_PROMPT"),
    ("train/run_cell36_accuracy.py", "ASK"),
    ("train/run_cell40_seat_directive.py", "DIRECTIVE"),
    # --- judge / instrument prompts: a judge is a prompted model too --------
    ("train/judge_instrument.py", "PROMPT"),
    ("train/cell23_presence_calib.py", "JUDGE_PROMPT"),
    ("train/run_cell30_descaffold.py", "JUDGE_PROMPT"),
    ("train/run_cellIV_batchjudge.py", "PROMPT"),
)

# Also registered: dict-valued prompt collections, whose VALUES are prompts.
PROMPT_SOURCES_DICT: tuple[tuple[str, str], ...] = (
    ("train/run_cell30_descaffold.py", "SEATS"),
)

_OPEN_QUOTES = {'"': '"', "“": "”", "'": "'", "‘": "’"}
_EXAMPLE_MARKERS = ("Example:", "example:", "e.g.", "E.g.", "for example",
                    "For example")


@dataclass(frozen=True)
class RegistryEntry:
    """One phrase the system dictated, with where it came from."""
    id: str
    phrase: str
    kind: str          # "quoted" | "example" | "whole_prompt"
    source_file: str
    source_symbol: str
    family_hint: tuple[str, ...]   # regex SCREEN only -- never a measurement


def load_constant(root: Path, rel: str, symbol: str):
    """Recover a module-level constant by parsing source -- no import, so no
    side effects and no dependency on the module's own imports resolving."""
    tree = ast.parse((root / rel).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == symbol:
                    try:
                        return ast.literal_eval(node.value)
                    except ValueError:
                        return None
    return None


def extract_quoted(text: str) -> list[str]:
    """Lift quoted material by scanning for quote delimiters.

    Character-level scanning, not regex and not classification. Apostrophes
    inside words (don't, ICO's) are excluded by requiring the closing
    delimiter and rejecting single-quote runs that begin mid-word.
    """
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in _OPEN_QUOTES:
            # a straight apostrophe preceded by a word char is possessive
            if ch == "'" and i > 0 and (text[i - 1].isalnum()):
                i += 1
                continue
            close = _OPEN_QUOTES[ch]
            j = text.find(close, i + 1)
            if j == -1:
                i += 1
                continue
            inner = text[i + 1:j].strip()
            if inner:
                out.append(inner)
            i = j + 1
            continue
        i += 1
    return out


def extract_examples(text: str) -> list[str]:
    """Lift the example SENTENCES a prompt supplies after an example marker.

    These are the most dangerous registry entries: the addendum ships whole
    model sentences ("modeled at $8,000/member/year under the assumption of
    60% persistence") that a writer can echo nearly verbatim.
    """
    out: list[str] = []
    for marker in _EXAMPLE_MARKERS:
        start = 0
        while True:
            k = text.find(marker, start)
            if k == -1:
                break
            seg = text[k + len(marker):]
            # to end of paragraph (blank line) or a hard stop at 320 chars
            end = seg.find("\n\n")
            seg = seg[:end if end != -1 else 320]
            seg = seg.strip().strip("-").strip()
            if seg:
                out.append(seg)
            start = k + len(marker)
    return out


def build_registry(root: Path) -> list[RegistryEntry]:
    """Assemble the full registry from the declared sources."""
    from gst.instruments import RegexInstrument
    screen = RegexInstrument()

    entries: list[RegistryEntry] = []
    seen: set[tuple[str, str]] = set()

    def add(phrase: str, kind: str, f: str, sym: str) -> None:
        phrase = " ".join(phrase.split())
        if len(phrase) < 3 or len(phrase) > 400:
            return
        key = (phrase.lower(), sym)
        if key in seen:
            return
        seen.add(key)
        entries.append(RegistryEntry(
            id=f"R{len(entries):03d}", phrase=phrase, kind=kind,
            source_file=f, source_symbol=sym,
            family_hint=tuple(sorted(screen.families(phrase))),
        ))

    sources: list[tuple[str, str, str]] = []
    for f, sym in PROMPT_SOURCES:
        val = load_constant(root, f, sym)
        if isinstance(val, str):
            sources.append((f, sym, val))
    for f, sym in PROMPT_SOURCES_DICT:
        val = load_constant(root, f, sym)
        if isinstance(val, dict):
            for k, v in val.items():
                if isinstance(v, str):
                    sources.append((f, f"{sym}[{k}]", v))

    for f, sym, text in sources:
        for q in extract_quoted(text):
            add(q, "quoted", f, sym)
        for e in extract_examples(text):
            add(e, "example", f, sym)

    return entries


def registry_digest(entries: list[RegistryEntry]) -> str:
    """Stable hash over the registry contents -- the freeze token."""
    payload = json.dumps([[e.phrase, e.source_symbol] for e in entries],
                         sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def freeze(root: Path, out_path: Path) -> dict:
    entries = build_registry(root)
    doc = {
        "schema": "dictation-registry/1",
        "digest": registry_digest(entries),
        "n_entries": len(entries),
        "sources": [f"{f}::{s}" for f, s in PROMPT_SOURCES]
                   + [f"{f}::{s}" for f, s in PROMPT_SOURCES_DICT],
        "entries": [asdict(e) for e in entries],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    return doc


def load_frozen(path: Path) -> list[RegistryEntry]:
    doc = json.loads(Path(path).read_text())
    return [RegistryEntry(**{**e, "family_hint": tuple(e["family_hint"])})
            for e in doc["entries"]]


# --- Gate G-E ---------------------------------------------------------------

def gate_GE(prompt_texts: dict[str, str], registry: list[RegistryEntry],
            construct_only: bool = True) -> list[str]:
    """Refuse a cell whose prompts re-introduce registry phrases.

    Returns a list of violation strings; empty means the gate passes. Pass
    the cell's own prompts (INCLUDING its judge prompts) as {label: text}.

    `construct_only` restricts the check to entries the screen flagged as
    construct-bearing; set False to check against every dictated phrase.
    """
    viol: list[str] = []
    pool = [e for e in registry if e.family_hint] if construct_only else registry
    for label, text in prompt_texts.items():
        low = text.lower()
        for e in pool:
            if e.phrase.lower() in low:
                viol.append(f"{label}: re-dictates {e.id} "
                            f"{e.phrase[:60]!r} (from {e.source_symbol})")
    return viol
