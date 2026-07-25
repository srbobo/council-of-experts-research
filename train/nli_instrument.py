"""Cell 7a — NLI disposition instrument (DeBERTa-v3-base-MNLI-fever-anli).

Zero-shot entailment scoring of the five behavior families, per sentence,
with per-claim (per-sentence) normalization. Two modes:

  calibrate  — score chosen vs rejected texts from the passing pairs of all
               three domains (labels by construction), report AUC + per-family
               separation, and emit frozen thresholds (Youden's J).
  score      — (Phase C) score imported bench runs with frozen thresholds.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 7a PRE-REGISTRATION".
Hypotheses are FROZEN there; do not edit without a documented amendment.

Run:  .venv-train/bin/python train/nli_instrument.py calibrate
      .venv-train/bin/python train/nli_instrument.py score
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).parent.parent
MODEL = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"

# Frozen hypotheses (v1) — must match the pre-registration verbatim.
HYPOTHESES = {
    "cutoff":  "The writer says their information may be outdated or should be verified.",
    "modeled": "The writer labels a number or estimate as an assumption.",
    "precise": "The writer explicitly distinguishes between two similar technical terms.",
    "jurisd":  "The writer treats different jurisdictions or regulatory regimes separately.",
    "hedging": "The writer states conditions under which the claim could change or vary.",
}

THRESHOLDS_PATH = ROOT / "train" / "data" / "nli_thresholds.json"

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_THINK = re.compile(r"<think>.*?</think>|^.*?</think>", re.DOTALL)


def sentences(text: str) -> list[str]:
    text = _THINK.sub("", text or "")  # strip Qwen3 reasoning blocks
    # drop markdown headers/table rules; keep prose sentences of useful length
    parts = [s.strip() for s in _SENT_SPLIT.split(text)]
    return [s for s in parts if 20 <= len(s) <= 600]


class NLI:
    def __init__(self) -> None:
        self.tok = AutoTokenizer.from_pretrained(MODEL)
        self.dev = "mps" if torch.backends.mps.is_available() else "cpu"
        self.mod = AutoModelForSequenceClassification.from_pretrained(MODEL).to(self.dev).eval()

    @torch.no_grad()
    def entail_probs(self, premises: list[str], hypothesis: str, bs: int = 32) -> list[float]:
        out: list[float] = []
        for i in range(0, len(premises), bs):
            batch = premises[i:i + bs]
            enc = self.tok(batch, [hypothesis] * len(batch), truncation=True,
                           max_length=256, padding=True, return_tensors="pt").to(self.dev)
            logits = self.mod(**enc).logits
            probs = torch.softmax(logits, dim=-1)[:, 0]  # index 0 = entailment
            out.extend(probs.cpu().tolist())
        return out


def text_scores(nli: NLI, text: str) -> dict[str, list[float]]:
    """Per-family entailment probability for every sentence of `text`."""
    sents = sentences(text)
    if not sents:
        return {f: [] for f in HYPOTHESES}
    return {f: nli.entail_probs(sents, h) for f, h in HYPOTHESES.items()}


def nli_density(scores: dict[str, list[float]], thresholds: dict[str, float]) -> float:
    """Entailing sentence-hits per 10 sentences (per-claim normalization)."""
    n = max(len(next(iter(scores.values()), [])), 1)
    hits = sum(sum(1 for p in ps if p >= thresholds[f]) for f, ps in scores.items())
    return hits / n * 10


def auc(pos: list[float], neg: list[float]) -> float:
    """Rank AUC (Mann-Whitney)."""
    pairs = 0
    wins = 0.0
    for p in pos:
        for q in neg:
            pairs += 1
            if p > q:
                wins += 1
            elif p == q:
                wins += 0.5
    return wins / pairs if pairs else 0.5


def load_pairs(cap_per_domain: int = 150) -> list[dict]:
    """Passing pairs from all domains; labels by construction."""
    sources = [
        ("legal", ROOT / "train" / "data" / "dpo_pairs_raw.jsonl"),
        ("health", ROOT / "train" / "data" / "dpo_pairs_health_raw.jsonl"),
        ("finance", ROOT / "train" / "data" / "dpo_pairs_finance_raw.jsonl"),
    ]
    out = []
    for domain, path in sources:
        if not path.exists():
            continue
        n = 0
        for line in path.open():
            rec = json.loads(line)
            if not rec.get("pass"):
                continue
            out.append({"domain": domain, "chosen": rec["chosen"],
                        "rejected": rec["rejected"],
                        "chosen_behaviors": rec.get("chosen_behaviors", {})})
            n += 1
            if n >= cap_per_domain:
                break
    return out


def calibrate() -> int:
    nli = NLI()
    pairs = load_pairs()
    print(f"calibration set: {len(pairs)} pairs "
          f"({', '.join(sorted(set(p['domain'] for p in pairs)))})", flush=True)

    # Text-level max-entailment per family, chosen vs rejected.
    per_family_pos: dict[str, list[float]] = {f: [] for f in HYPOTHESES}
    per_family_neg: dict[str, list[float]] = {f: [] for f in HYPOTHESES}
    total_pos: list[float] = []
    total_neg: list[float] = []
    for i, p in enumerate(pairs):
        cs = text_scores(nli, p["chosen"])
        rs = text_scores(nli, p["rejected"])
        for f in HYPOTHESES:
            if cs[f]:
                per_family_pos[f].append(max(cs[f]))
            if rs[f]:
                per_family_neg[f].append(max(rs[f]))
        # overall separation: mean of family-max scores
        if any(cs.values()) and any(rs.values()):
            total_pos.append(sum(max(v) if v else 0 for v in cs.values()) / 5)
            total_neg.append(sum(max(v) if v else 0 for v in rs.values()) / 5)
        if (i + 1) % 25 == 0:
            print(f"  scored {i+1}/{len(pairs)} pairs", flush=True)

    print("\n=== chosen-vs-rejected separation (text-level max entailment) ===")
    overall = auc(total_pos, total_neg)
    print(f"OVERALL AUC: {overall:.3f}   (P-7a.1 gate: >= 0.85)")
    thresholds: dict[str, float] = {}
    for f in HYPOTHESES:
        a = auc(per_family_pos[f], per_family_neg[f])
        # Youden threshold over candidate cuts
        best_t, best_j = 0.5, -1.0
        for t in [i / 100 for i in range(5, 100, 5)]:
            tpr = sum(1 for v in per_family_pos[f] if v >= t) / max(len(per_family_pos[f]), 1)
            fpr = sum(1 for v in per_family_neg[f] if v >= t) / max(len(per_family_neg[f]), 1)
            j = tpr - fpr
            if j > best_j:
                best_j, best_t = j, t
        thresholds[f] = best_t
        print(f"  {f:<8} AUC {a:.3f}  threshold {best_t:.2f}  (J={best_j:.2f})")

    THRESHOLDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    THRESHOLDS_PATH.write_text(json.dumps(
        {"model": MODEL, "overall_auc": round(overall, 4),
         "thresholds": thresholds}, indent=2))
    print(f"\nfrozen thresholds -> {THRESHOLDS_PATH}")
    return 0


# Phase C — verdict re-scoring over imported runs -----------------------------

CASES7 = "case_7_trigger_light_baseline"
VERDICT_MODES = {
    "legal":   ("local-council-repro", "local-council-dpo", "legal"),
    "health":  ("local-council-health-repro", "local-council-health-orpo", "healthcare"),
    "finance": ("local-council-finance-repro", "local-council-finance-orpo", "finance"),
}


def score() -> int:
    cfg = json.loads(THRESHOLDS_PATH.read_text())
    thresholds = cfg["thresholds"]
    nli = NLI()
    imported = ROOT / "bench" / "runs" / "imported"

    def runs(mode: str, case7: bool):
        for f in sorted(imported.glob(f"*__{mode}.json")):
            if ("case_7" in f.name) == case7:
                yield json.loads(f.read_text())

    print(f"thresholds: { {k: round(v,2) for k,v in thresholds.items()} }")
    print(f"\n{'seat':<9} {'arm':<28} {'gate NLI-density':>16} {'seat NLI-density':>17}")
    for seat, (repro, orpo, seat_role) in VERDICT_MODES.items():
        for mode in (repro, orpo):
            gate_vals, seat_vals = [], []
            for case7 in (True, False):
                for d in runs(mode, case7):
                    turns = [t for t in d.get("deliberation", {}).get("turns", [])
                             if t.get("seat") == seat_role]
                    if not turns:
                        if case7:
                            gate_vals.append(0.0)
                        continue
                    dens = nli_density(text_scores(nli, turns[0]["output_text"]), thresholds)
                    (gate_vals if case7 else seat_vals).append(dens)
            g = sum(gate_vals) / len(gate_vals) if gate_vals else float("nan")
            s = sum(seat_vals) / len(seat_vals) if seat_vals else float("nan")
            print(f"{seat:<9} {mode:<28} {g:>16.2f} {s:>17.2f}", flush=True)
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "calibrate"
    raise SystemExit(calibrate() if mode == "calibrate" else score())
