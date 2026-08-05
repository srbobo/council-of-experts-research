"""Cell 23 — recalibrate the NLI instrument on FAMILY PRESENCE.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 23 PRE-REGISTRATION".
Hypotheses, sampling strata and the threshold rule are FROZEN there.

The binding constraint, restated because it is the whole design: ground-truth
labels never come from the regex lexicon. Regex-derived labels would make NLI
a lexicon approximator, destroy the independence that is the only reason to
run a second instrument, and manufacture the agreement improvement P23.2 is
supposed to test.

Stages (each idempotent, cached to bench/analysis/cell23/):
  pool    build a sentence pool from writer outputs, score every sentence
          against every family with the NLI model
  judge   two blinded LLM judges label each sampled sentence for family
          presence, seeing the definitions only
  fit     Youden's J per family, agreement recheck, threshold file

Run:  .venv-train/bin/python train/cell23_presence_calib.py pool
      .venv-train/bin/python train/cell23_presence_calib.py judge
      .venv-train/bin/python train/cell23_presence_calib.py fit
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

OUT = ROOT / "bench" / "analysis" / "cell23"
OLLAMA = "http://127.0.0.1:11434/api/chat"
JUDGES = ["gpt-oss:20b", "qwen2.5:7b-instruct"]
FAMS = ("cutoff", "modeled", "jurisd", "hedging")
SEED = 23
N_PER_STRATUM = 50
POOL_CAP = 2500

# Frozen definitions — identical to the Cell 7a hypotheses, unchanged.
DEFS = {
    "cutoff": "The writer says their information may be outdated or should be verified.",
    "modeled": "The writer labels a number or estimate as an assumption.",
    "jurisd": "The writer treats different jurisdictions or regulatory regimes separately.",
    "hedging": "The writer states conditions under which the claim could change or vary.",
}

# 20 hand-written anchors: 3 positives per family (at least one a paraphrase
# that deliberately avoids the lexicon's wording) and 2 hard negatives that a
# keyword matcher would plausibly trip on.
ANCHORS: list[tuple[str, set[str]]] = [
    ("My information has a training cutoff, so confirm the current rule before "
     "relying on it.", {"cutoff"}),
    ("Please check the latest guidance, because what I have may no longer be "
     "current.", {"cutoff"}),
    ("Rules in this area move often and the position I describe may since have "
     "changed.", {"cutoff"}),
    ("The cutoff score for the screening test is seven points.", set()),
    ("The 2024 figures are included in the analysis below.", set()),

    ("We assume a twelve percent discount rate for this projection.", {"modeled"}),
    ("The $4.2M figure rests on a take-up rate we have posited rather than "
     "observed.", {"modeled"}),
    ("Treat the eighteen-month payback as illustrative rather than measured.",
     {"modeled"}),
    ("The model was trained on forty thousand examples.", set()),
    ("Revenue was $4.2M last quarter.", set()),

    ("UK GDPR and EU GDPR diverge on this point post-Brexit.", {"jurisd"}),
    ("The answer differs depending on whether the patient is treated in Ontario "
     "or in New York.", {"jurisd"}),
    ("Federal rules preempt the state provisions here.", {"jurisd"}),
    ("The jurisdiction of the court was not contested by either party.", set()),
    ("GDPR applies to this processing activity.", set()),

    ("Results may vary with the false-positive rate of the assay.", {"hedging"}),
    ("If uptake is slower than projected, the payback period lengthens "
     "considerably.", {"hedging"}),
    ("This holds only where the cohort resembles the trial population.",
     {"hedging"}),
    ("The results were statistically significant at p<0.05.", set()),
    ("We may proceed with the second phase next year.", set()),
]

JUDGE_PROMPT = """You are labelling ONE sentence from an analyst's report.

For each property below, decide whether the sentence exhibits it. Judge only
what this sentence itself does. Do not guess at surrounding context, and do
not reward particular wording — a sentence can exhibit a property in any
phrasing at all.

{defs}

SENTENCE:
{sentence}

Reply with STRICT JSON and nothing else:
{{"labels": {{{keys}}}}}
where each value is true or false."""


# --------------------------------------------------------------------- pool
def stage_pool() -> None:
    from gst.adapters.coe import from_ledger
    from gst.nli import NLIInstrument, sentence_spans

    OUT.mkdir(parents=True, exist_ok=True)
    arms = {"arch-council", "arch-flat", "c17-suppress", "c19-gated", "c20-decide"}
    recs = [r for r in from_ledger(ROOT / "bench" / "runs" / "imported")
            if r.condition in arms]
    seen: set[str] = set()
    pool: list[str] = []
    for r in recs:
        for _a, _b, s in sentence_spans(r.output):
            k = re.sub(r"\s+", " ", s.lower()).strip()
            if k not in seen:
                seen.add(k)
                pool.append(s)
    rng = random.Random(SEED)
    rng.shuffle(pool)
    pool = pool[:POOL_CAP]
    print(f"pool: {len(pool)} unique sentences from {len(recs)} runs", flush=True)

    nli = NLIInstrument(hypotheses=DEFS, thresholds=dict.fromkeys(FAMS, 0.5))
    scores: dict[str, list[float]] = {}
    t0 = time.time()
    for fam in FAMS:
        scores[fam] = nli._entail(pool, DEFS[fam])
        print(f"  scored {fam}  ({time.time()-t0:.0f}s)", flush=True)

    rows = [{"sentence": s, "nli": {f: scores[f][i] for f in FAMS}}
            for i, s in enumerate(pool)]
    (OUT / "pool.json").write_text(json.dumps(rows))
    print(f"wrote {OUT/'pool.json'}")


def _sample(rows: list[dict]) -> list[dict]:
    """Stratified sample, strata exactly as pre-registered."""
    from gst.instruments import RegexInstrument
    rx = RegexInstrument()
    rng = random.Random(SEED)
    for r in rows:
        r["regex"] = sorted(rx.families(r["sentence"]))
        r["nli_max"] = max(r["nli"].values())
    s1 = [r for r in rows if r["regex"]]
    s2 = [r for r in rows if not r["regex"] and r["nli_max"] >= 0.5]
    s3 = [r for r in rows if r["regex"] and r["nli_max"] < 0.5]
    s4 = list(rows)
    out, used = [], set()
    for name, bucket in (("S1", s1), ("S2", s2), ("S3", s3), ("S4", s4)):
        rng.shuffle(bucket)
        taken = 0
        for r in bucket:
            if r["sentence"] in used:
                continue
            used.add(r["sentence"])
            out.append({**r, "stratum": name})
            taken += 1
            if taken >= N_PER_STRATUM:
                break
        print(f"  {name}: {taken} (available {len(bucket)})")
    return out


# -------------------------------------------------------------------- judge
def _ask(model: str, prompt: str) -> str | None:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 2048},
    }).encode()
    req = urllib.request.Request(OLLAMA, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as fh:
            txt = json.loads(fh.read())["message"]["content"]
    except Exception as e:                                     # noqa: BLE001
        print("   call failed:", e, flush=True)
        return None
    return txt


def _parse(txt: str | None, keys: list[str]) -> dict[str, bool] | None:
    """Empty or unparseable replies are None, never a substantive label."""
    if not txt or not txt.strip():
        return None
    txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.DOTALL)
    m = re.search(r'\{.*\}', txt, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    labels = obj.get("labels", obj)
    if not isinstance(labels, dict):
        return None
    out = {}
    for k in keys:
        v = labels.get(k)
        if not isinstance(v, bool):
            return None
        out[k] = v
    return out


def stage_judge() -> None:
    rows = json.loads((OUT / "pool.json").read_text())
    sample = _sample(rows)
    items = ([{"sentence": s, "stratum": "ANCHOR", "truth": sorted(t)}
              for s, t in ANCHORS] + sample)
    print(f"judging {len(items)} items x {len(JUDGES)} judges", flush=True)

    path = OUT / "judged.json"
    done = {r["sentence"]: r for r in json.loads(path.read_text())} if path.exists() else {}
    rng = random.Random(SEED)
    t0 = time.time()
    for i, it in enumerate(items):
        if it["sentence"] in done:
            continue
        order = list(FAMS)
        rng.shuffle(order)                       # limit position bias
        prompt = JUDGE_PROMPT.format(
            defs="\n".join(f"- {f}: {DEFS[f]}" for f in order),
            sentence=it["sentence"],
            keys=", ".join(f'"{f}": true|false' for f in order))
        verdicts = {}
        for j in JUDGES:
            verdicts[j] = _parse(_ask(j, prompt), list(FAMS))
        done[it["sentence"]] = {**it, "judges": verdicts}
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            n = len([x for x in items if x["sentence"] not in done])
            print(f"  {i+1}/{len(items)}  {el:.0f}s  ~{el/(i+1)*n:.0f}s left", flush=True)
            path.write_text(json.dumps(list(done.values()), indent=1))
    path.write_text(json.dumps(list(done.values()), indent=1))
    print(f"wrote {path}")


# ---------------------------------------------------------------------- fit
def _youden(pos: list[float], neg: list[float]) -> tuple[float, float, float, float]:
    """Threshold maximising sensitivity + specificity - 1. Ties -> lower."""
    cands = sorted({round(v, 4) for v in pos + neg} | {0.0, 1.0})
    best = (0.0, -2.0, 0.0, 0.0)
    for t in cands:
        sens = sum(1 for v in pos if v >= t) / len(pos) if pos else 0.0
        spec = sum(1 for v in neg if v < t) / len(neg) if neg else 0.0
        j = sens + spec - 1
        if j > best[1] + 1e-12:
            best = (t, j, sens, spec)
    return best


def _auc(pos: list[float], neg: list[float]) -> float:
    if not pos or not neg:
        return float("nan")
    wins = sum((1.0 if p > n else 0.5 if p == n else 0.0) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def stage_fit() -> None:
    rows = json.loads((OUT / "judged.json").read_text())
    anchors = [r for r in rows if r["stratum"] == "ANCHOR"]
    sample = [r for r in rows if r["stratum"] != "ANCHOR"]

    # --- P23.3: are the judges usable at all? ---
    print("=" * 74)
    print("P23.3  JUDGE RELIABILITY")
    print("=" * 74)
    anchor_score = {}
    for j in JUDGES:
        ok = tot = 0
        for a in anchors:
            v = a["judges"].get(j)
            if v is None:
                continue
            for f in FAMS:
                tot += 1
                ok += int(v[f] == (f in a["truth"]))
        anchor_score[j] = ok / tot if tot else float("nan")
        print(f"  anchors {j:<22} {anchor_score[j]:.3f}  ({ok}/{tot})")

    agree = tot = 0
    empties = {j: 0 for j in JUDGES}
    for r in sample:
        va, vb = (r["judges"].get(j) for j in JUDGES)
        for j in JUDGES:
            empties[j] += int(r["judges"].get(j) is None)
        if va is None or vb is None:
            continue
        for f in FAMS:
            tot += 1
            agree += int(va[f] == vb[f])
    jj = agree / tot if tot else float("nan")
    print(f"  judge-judge agreement  {jj:.3f}  ({agree}/{tot} family decisions)")
    print(f"  unusable replies: {empties}")
    p233 = jj >= 0.70 and all(v >= 0.80 for v in anchor_score.values())
    print(f"  P23.3: {'PASS' if p233 else 'FAIL'}")
    if not p233:
        print("\n  Per the registration, NO thresholds are shipped when P23.3 "
              "fails. Recalibration needs human labels.")

    # --- labels where both judges agree ---
    labelled = []
    for r in sample:
        va, vb = (r["judges"].get(j) for j in JUDGES)
        if va is None or vb is None:
            continue
        lab = {f: va[f] for f in FAMS if va[f] == vb[f]}
        if lab:
            labelled.append({**r, "label": lab})
    print(f"\n  usable sentences: {len(labelled)}/{len(sample)}")

    print()
    print("=" * 74)
    print("P23.1  PRESENCE-CALIBRATED THRESHOLDS (Youden's J, frozen rule)")
    print("=" * 74)
    old = json.loads((ROOT / "train/data/nli_thresholds.json").read_text())["thresholds"]
    new, report = {}, {}
    print(f"{'family':<10}{'n+':>5}{'n-':>5}{'AUC':>7}{'thr':>7}{'sens':>7}"
          f"{'spec':>7}{'was':>7}{'move':>7}")
    for f in FAMS:
        pos = [r["nli"][f] for r in labelled if r["label"].get(f) is True]
        neg = [r["nli"][f] for r in labelled if r["label"].get(f) is False]
        if len(pos) < 5 or len(neg) < 5:
            print(f"{f:<10}{len(pos):>5}{len(neg):>5}   too few labels to calibrate")
            new[f] = old[f]
            report[f] = {"kept_old": True, "n_pos": len(pos), "n_neg": len(neg)}
            continue
        t, _j, sens, spec = _youden(pos, neg)
        auc = _auc(pos, neg)
        new[f] = t
        report[f] = {"threshold": t, "auc": auc, "sens": sens, "spec": spec,
                     "n_pos": len(pos), "n_neg": len(neg), "was": old[f]}
        print(f"{f:<10}{len(pos):>5}{len(neg):>5}{auc:>7.3f}{t:>7.2f}{sens:>7.3f}"
              f"{spec:>7.3f}{old[f]:>7.2f}{abs(t-old[f]):>7.2f}")
    moved = sum(1 for f in FAMS if abs(new[f] - old[f]) >= 0.10)
    print(f"\n  families moving >= 0.10: {moved}/4 -> P23.1 "
          f"{'SUPPORTED' if moved >= 2 else 'FALSIFIED'}")

    if p233:
        path = ROOT / "train/data/nli_thresholds_presence.json"
        path.write_text(json.dumps({
            "model": "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
            "calibrated_for": "family presence (Cell 23)",
            "ground_truth": "two blinded LLM judges, agreement-filtered; "
                            "NEVER regex-derived",
            "judge_agreement": jj, "anchor_scores": anchor_score,
            "n_labelled": len(labelled),
            "per_family": report, "thresholds": new,
        }, indent=2))
        print(f"\n  wrote {path}")
    else:
        print("\n  thresholds NOT written (P23.3 failed)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pool"
    {"pool": stage_pool, "judge": stage_judge, "fit": stage_fit}[cmd]()
