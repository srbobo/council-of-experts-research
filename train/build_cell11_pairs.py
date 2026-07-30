"""Cell 11 stage 3 — score samples with the calibration reward, build pairs.

Reward (registered):  heavy prompt  R = +CDS(sample)
                      light prompt  R = -density(sample)
chosen = argmax R, rejected = argmin R, per prompt. Gates:
  - reward margin |R_chosen - R_rejected| >= 0.10 (ties carry no signal)
  - length ratio within the 6b window [0.8, 1.4]
  - NLI directional cross-check (frozen DeBERTa-v3-MNLI instrument, frozen
    Youden thresholds): the NLI density ordering must agree with the regex
    ordering (heavy: chosen >= rejected; light: chosen <= rejected).
Output: train/data/dpo_pairs_cell11/{train,valid,test}.jsonl in the 6b flat
format (prompt = synthesis system + user), seed-42 shuffle, cap 88 train.
Run: .venv-train/bin/python train/build_cell11_pairs.py
"""
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from train.nli_instrument import NLI, nli_density, text_scores  # noqa: E402

SAMPLES = Path("train/data/cell11_samples")
OUT = Path("train/data/dpo_pairs_cell11")
THRESHOLDS = json.loads(Path("train/data/nli_thresholds.json").read_text())["thresholds"]
CAP_TRAIN, N_VALID, N_TEST = 88, 4, 4
MARGIN, RATIO_LO, RATIO_HI = 0.10, 0.8, 1.4

# Canonical behavior regexes (identical to every recorded verdict).
BEH = {
    "c": [r'training[- ]?cut[- ]?off', r'knowledge cut[- ]?off',
          r'may (?:be |have )(?:stale|outdated|evolved)', r'post[- ]?cut[- ]?off',
          r'after my training', r'verify (?:current|latest|recent)',
          r'as of (?:my )?(?:training|knowledge|2024|2025)'],
    "m": [r'modell?ed at', r'\bassume[ds]? (?:that|the)',
          r'\bassuming (?:that|the|a |an |\d)', r'under the assumption',
          r'this assume[ds]', r'\bwe assume\b', r'\bhypothetical[ly]?\b'],
    "p": [r'(?:approval).*?(?:vs\.?|versus|not).*?(?:clearance)',
          r'distinguish(?:es|ing|ed)? between', r'standard[- ]of[- ]care',
          r'(?:510\(k\)|de novo|PMA)\s+(?:clearance|approval|pathway)',
          r'\b(?:NDA|BLA)\s+approval\b'],
    "j": [r'\bUK\s?GDPR\b', r'\bEU\s?GDPR\b', r'post[- ]Brexit',
          r'each\s+(?:jurisdiction|country|state|regime)', r'preempt(?:ion|s|ed)'],
    "h": [r'(?:false[- ]positive|false[- ]negative)', r'alert fatigue',
          r'real[- ]world\s+(?:evidence|data)', r'sensitivity (?:analysis|range|to|of)',
          r'low/?high (?:case|scenario|estimate)', r'\b±\s?\d',
          r'(?:may|might|could)\s+(?:vary|differ|change)'],
}


def dens(t: str) -> float:
    if not t:
        return 0.0
    return sum(len(re.findall(p, t, re.I)) for ps in BEH.values() for p in ps) / len(t) * 1000


def cds(t: str) -> float:
    if not t:
        return 0.0
    k = sum(1 for ps in BEH.values() if any(re.search(p, t, re.I) for p in ps))
    return dens(t) * ((k / 5) ** 0.5)


def main() -> None:
    files = sorted(SAMPLES.glob("*.json"))
    nli = NLI()
    pairs, stats = [], {"no_routes": 0, "margin": 0, "ratio": 0, "nli": 0, "kept": 0}
    for f in files:
        rec = json.loads(f.read_text())
        if rec.get("skipped"):
            stats["no_routes"] += 1
            continue
        heavy = rec["label"] == "heavy"
        scored = [((cds(s) if heavy else -dens(s)), s) for s in rec["samples"]]
        scored.sort(key=lambda x: x[0])
        r_lo, rejected = scored[0]
        r_hi, chosen = scored[-1]
        if r_hi - r_lo < MARGIN:
            stats["margin"] += 1
            continue
        ratio = len(chosen) / max(len(rejected), 1)
        if not (RATIO_LO <= ratio <= RATIO_HI):
            stats["ratio"] += 1
            continue
        nc = nli_density(text_scores(nli, chosen), THRESHOLDS)
        nr = nli_density(text_scores(nli, rejected), THRESHOLDS)
        if (heavy and nc < nr) or (not heavy and nc > nr):
            stats["nli"] += 1
            continue
        stats["kept"] += 1
        sysm, userm = rec["synthesis_messages"][0], rec["synthesis_messages"][1]
        pairs.append({"label": rec["label"],
                      "prompt": f"{sysm['content']}\n\n{userm['content']}",
                      "chosen": chosen, "rejected": rejected})
    print("gates:", stats, flush=True)
    hl = {"heavy": sum(1 for p in pairs if p["label"] == "heavy"),
          "light": sum(1 for p in pairs if p["label"] == "light")}
    print(f"realized mix: {hl}", flush=True)

    random.seed(42)
    random.shuffle(pairs)
    for p in pairs:
        del p["label"]
    test, valid = pairs[:N_TEST], pairs[N_TEST:N_TEST + N_VALID]
    train = pairs[N_TEST + N_VALID:N_TEST + N_VALID + CAP_TRAIN]
    OUT.mkdir(parents=True, exist_ok=True)
    for name, split in (("train", train), ("valid", valid), ("test", test)):
        with (OUT / f"{name}.jsonl").open("w") as fh:
            for p in split:
                fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"=== CELL11 PAIRS: {len(train)} train / {len(valid)} valid / "
          f"{len(test)} test ===", flush=True)


main()
