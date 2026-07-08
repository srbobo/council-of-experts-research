"""Re-score the raw pair log under the AMENDED filters and write the splits.

Protocol amendment (2026-07-08, documented in RUNBOOK_DPO_PROMPT_TRANSFER.md,
applied BEFORE any training):

  1. Rejected-gate `jurisd` patterns narrowed to disposition META-COMMENTARY
     only. The original gate included `federal…state` co-occurrence and
     `preempt*`, which in legal analyses are SUBSTANTIVE CONTENT the strip-
     rewrite correctly refuses to remove — those records could never pass,
     by construction. The CDS *measurement* used in evaluation is untouched;
     only the pair-selection gate changes.
  2. Length-ratio window widened 0.8–1.3 → 0.8–1.4. Weaving in hedge
     phrases genuinely lengthens text; the 1.3–1.5 band held most drops.
     1.4 rescues the bulk while still guarding DPO's length bias.

Run AFTER gen_pairs.py completes (this supersedes its split step, which
uses the original per-record flags):

    .venv/bin/python train/rescore_split.py

Idempotent — rebuilds train/valid/test from the raw log every run and
reports yield under BOTH filter sets for transparency.
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from council.prompts import LEGAL_SYSTEM  # noqa: E402

RAW_LOG = Path(__file__).parent / "data" / "dpo_pairs_raw.jsonl"
OUT_DIR = Path(__file__).parent / "data" / "dpo_pairs"

# Amended rejected gate. cutoff/modeled/precise/hedging unchanged from the
# generator; jurisd narrowed to meta-commentary.
GATE = {
    "cutoff":  [r"training[- ]?cut[- ]?off", r"knowledge cut[- ]?off",
                r"may (?:be |have )(?:stale|outdated|out[- ]of[- ]date|evolved)",
                r"post[- ]?cut[- ]?off", r"after my training",
                r"verify (?:current|latest|recent) (?:rates|guidance|regulations|status)",
                r"as of (?:my )?(?:training|knowledge|2024|2025)"],
    "modeled": [r"modell?ed at", r"\bassume[ds]? (?:that|the)",
                r"\bassuming (?:that|the|a |an |\d)", r"under the assumption",
                r"this assume[ds]", r"\bwe assume\b", r"\bhypothetical[ly]?\b"],
    "precise": [r"(?:approval).*?(?:vs\.?|versus|not).*?(?:clearance)",
                r"distinguish(?:es|ing|ed)? between", r"standard[- ]of[- ]care"],
    "jurisd":  [r"each\s+(?:jurisdiction|country|state|regime)",
                r"treat(?:ing|ed)?\s+each\s+\w+\s+separately",
                r"\bUK\s?GDPR\b.*?\bEU\s?GDPR\b"],
    "hedging": [r"sensitivity (?:analysis|range|to|of)", r"\b±\s?\d",
                r"(?:may|might|could)\s+(?:vary|differ|change)",
                r"low/?high (?:case|scenario|estimate)"],
}
RATIO_LO, RATIO_HI = 0.8, 1.4


def amended_pass(rec: dict) -> bool:
    chosen_distinct = sum(1 for v in rec["chosen_behaviors"].values() if v > 0)
    rej_hits = sum(
        len(re.findall(p, rec["rejected"], re.I))
        for pats in GATE.values() for p in pats
    )
    return (chosen_distinct >= 2 and rej_hits == 0
            and RATIO_LO <= rec["len_ratio"] <= RATIO_HI)


def main() -> int:
    random.seed(42)
    recs = [json.loads(l) for l in RAW_LOG.open()]
    orig = [r for r in recs if r.get("pass")]
    amended = [r for r in recs if amended_pass(r)]
    print(f"records: {len(recs)}")
    print(f"original filters: {len(orig)} pass")
    print(f"amended filters:  {len(amended)} pass")

    rows = [{
        "prompt": LEGAL_SYSTEM + "\n\n" + r["question"],
        "chosen": r["chosen"],
        "rejected": r["rejected"],
    } for r in amended]
    random.shuffle(rows)
    n = len(rows)
    n_val = n_test = max(4, n // 20)
    splits = {"valid": rows[:n_val],
              "test": rows[n_val:n_val + n_test],
              "train": rows[n_val + n_test:]}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, subset in splits.items():
        with (OUT_DIR / f"{name}.jsonl").open("w") as f:
            for row in subset:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{name}: {len(subset)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
