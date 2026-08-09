"""Cell IV — does BATCHED sentence judging preserve the validated protocol?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL IV PRE-REGISTRATION".
Bars frozen there: consistency >= 0.80/family, anchors >= 0.80/judge,
parse failures < 20%/judge. All three must pass.

Sentences stay ISOLATED and numbered — only the call packaging changes, so
the judgment unit remains one sentence.

Run:  .venv/bin/python train/run_cellIV_batchjudge.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.cell23_presence_calib import ANCHORS, DEFS, JUDGES  # noqa: E402
from train.run_cell25_moa import chat                          # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cellIV"
C23 = ROOT / "bench" / "analysis" / "cell23" / "judged.json"
BATCH_SIZES = (5, 10)
SCORED = ("modeled", "jurisd", "hedging")   # cutoff excluded: 3 positives
ALL_FAMS = ("cutoff", "modeled", "jurisd", "hedging")

PROMPT = """You are labelling {n} independent sentences from analyst \
reports. Judge each sentence ON ITS OWN; they are unrelated to each other.

For each sentence, decide whether it exhibits each property. Judge only \
what the sentence itself does, and do not reward particular wording — a \
sentence can exhibit a property in any phrasing.

{defs}

SENTENCES:
{items}

Reply with STRICT JSON and nothing else: an object whose keys are the \
sentence numbers as strings, each mapping to an object of the four \
properties with true/false values. Example for two sentences:
{{"1": {{"cutoff": false, "modeled": true, "jurisd": false, "hedging": false}}, \
"2": {{"cutoff": true, "modeled": false, "jurisd": false, "hedging": false}}}}
Include every sentence number from 1 to {n}."""


def load_reference():
    """Frozen labels: agreement-filtered sample + known-truth anchors."""
    rows = json.loads(C23.read_text())
    sample, anchors = [], []
    for r in rows:
        if r["stratum"] == "ANCHOR":
            anchors.append({"sentence": r["sentence"],
                            "truth": {f: f in r["truth"] for f in ALL_FAMS}})
            continue
        va, vb = (r["judges"].get(j) for j in JUDGES)
        if va is None or vb is None:
            continue
        lab = {f: va[f] for f in ALL_FAMS if va[f] == vb[f]}
        if len(lab) == len(ALL_FAMS):     # only fully-agreed sentences
            sample.append({"sentence": r["sentence"], "truth": lab})
    return sample, anchors


def parse(raw, n):
    if not raw or not raw.strip():
        return None
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    out = {}
    for i in range(1, n + 1):
        v = obj.get(str(i)) or obj.get(i)
        if not isinstance(v, dict):
            return None
        row = {}
        for f in ALL_FAMS:
            if not isinstance(v.get(f), bool):
                return None
            row[f] = v[f]
        out[i] = row
    return out


def judge_batches(items, size, judge, cache, tag):
    """Returns {index_in_items: {family: bool}} plus failure count."""
    got, fails = {}, 0
    for start in range(0, len(items), size):
        chunk = items[start:start + size]
        key = f"{tag}|{judge}|{size}|{start}"
        if key in cache:
            res = cache[key]
        else:
            body = "\n".join(f"{i+1}. {c['sentence']}" for i, c in enumerate(chunk))
            res = parse(chat(judge, None, PROMPT.format(
                n=len(chunk), defs="\n".join(f"- {f}: {DEFS[f]}" for f in ALL_FAMS),
                items=body), temperature=0, max_tokens=4096), len(chunk))
            cache[key] = res
        if res is None:
            fails += 1
            continue
        for i, c in enumerate(chunk):
            got[start + i] = res[i + 1]
    return got, fails


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cpath = OUT / "cache.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    sample, anchors = load_reference()
    print(f"reference: {len(sample)} fully-agreed sentences, {len(anchors)} anchors\n")

    results = {}
    t0 = time.time()
    for size in BATCH_SIZES:
        results[size] = {}
        for judge in JUDGES:
            s_got, s_fail = judge_batches(sample, size, judge, cache, "sample")
            a_got, a_fail = judge_batches(anchors, size, judge, cache, "anchor")
            cpath.write_text(json.dumps(cache))
            nb = (len(sample) + size - 1) // size + (len(anchors) + size - 1) // size
            results[size][judge] = {"s": s_got, "a": a_got,
                                    "fails": s_fail + a_fail, "batches": nb}
            print(f"  B={size:<3} {judge:<22} parse failures {s_fail+a_fail}/{nb} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    print()
    for size in BATCH_SIZES:
        print("=" * 74)
        print(f"BATCH SIZE {size}")
        print("=" * 74)
        # P-IV.3 usability
        ok3 = True
        for judge in JUDGES:
            r = results[size][judge]
            rate = r["fails"] / max(r["batches"], 1)
            ok3 &= rate < 0.20
            print(f"  P-IV.3 {judge:<22} parse-failure {rate:.3f} "
                  f"({r['fails']}/{r['batches']}) {'ok' if rate < 0.20 else 'FAIL'}")
        # P-IV.1 consistency (both judges must agree with frozen label)
        print(f"  {'family':<9}{'n':>5}{'agree':>8}")
        ok1 = True
        for f in SCORED:
            agree = tot = 0
            for i, item in enumerate(sample):
                vs = [results[size][j]["s"].get(i) for j in JUDGES]
                if any(v is None for v in vs):
                    continue
                tot += 1
                batched = all(v[f] for v in vs)     # both-agree rule, as in Cell 23
                agree += int(batched == item["truth"][f])
            rate = agree / tot if tot else float("nan")
            ok1 &= rate >= 0.80
            print(f"  {f:<9}{tot:>5}{rate:>8.3f}{'' if rate >= 0.80 else '  FAIL'}")
        # P-IV.2 anchors, per judge
        ok2 = True
        for judge in JUDGES:
            corr = tot = 0
            for i, item in enumerate(anchors):
                v = results[size][judge]["a"].get(i)
                if v is None:
                    continue
                for f in ALL_FAMS:
                    tot += 1
                    corr += int(v[f] == item["truth"][f])
            rate = corr / tot if tot else float("nan")
            ok2 &= rate >= 0.80
            print(f"  P-IV.2 anchors {judge:<22} {rate:.3f} ({corr}/{tot})"
                  f"{'' if rate >= 0.80 else '  FAIL'}")
        verdict = "PASSES ALL BARS" if (ok1 and ok2 and ok3) else "FAILS"
        print(f"  --> B={size}: {verdict}")
    print()
    print("Registered consequence: ship the largest passing batch size; if none "
          "passes, batching is rejected and re-measurement is BLOCKED.")


if __name__ == "__main__":
    main()
