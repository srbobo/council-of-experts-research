"""NLI-backed family detection — the validated second instrument.

Wraps the program's calibrated DeBERTa-v3-MNLI instrument (frozen per-family
Youden thresholds, chosen-vs-rejected AUC 0.929) for the task it was
validated on: detecting whether a behavior FAMILY is present in a response.

Exists because a regex-only gate creates selection pressure toward the
lexicon's documented paraphrase blind spot: the gate quotes regex-matched
phrases, so a reviser can pass by rephrasing. NLI judges the behavior, not
the phrase.

Known non-use: compound contrastive claims (tension grounding), where this
instrument measures paraphrase distance rather than groundedness. Family
presence only.

Heavy imports are lazy; requires the training venv (torch/transformers).
"""
import json
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_nli = None
_thresholds = None


def _load():
    global _nli, _thresholds
    if _nli is None:
        import sys
        sys.path.insert(0, str(_ROOT))
        from train.nli_instrument import NLI
        _nli = NLI()
        _thresholds = json.loads(
            (_ROOT / "train/data/nli_thresholds.json").read_text())["thresholds"]
    return _nli, _thresholds


# Map harness family names -> instrument threshold keys (identical here).
FAMILY_KEYS = ("cutoff", "modeled", "jurisd", "hedging")


def families(text: str) -> set[str]:
    """Families present per the calibrated NLI instrument."""
    nli, thr = _load()
    from train.nli_instrument import sentences, text_scores
    scores = text_scores(nli, text)
    out = set()
    for fam in FAMILY_KEYS:
        ps = scores.get(fam, [])
        if ps and max(ps) >= thr[fam]:
            out.add(fam)
    return out


def confirm_invention(seat_texts: list[str], output: str) -> set[str]:
    """Families present in output but raised by no seat, per NLI."""
    seats = " ".join(t for t in seat_texts if t)
    raised = families(seats) if seats.strip() else set()
    return families(output) - raised
