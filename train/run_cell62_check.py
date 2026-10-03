"""Cell 62 amendment — what can be measured about the sentence judges
without a person's labels.

Registered: RUNBOOK_PAPER_HARDENING.md "CELL 62 AMENDMENT (2026-10-02)".
P62.0 to P62.2 are NOT EVALUABLE (no reference). Reported, no bar:

  1. the judge-only parts of P62.3 on the 404 sampled sentences: kappa
     between each pair of judges per kind, each stored judge's agreement
     with its own stored label, and the two-class latent-class estimate;
  2. a neighbouring-construct check: the SFU Review Corpus annotated for
     speculation (human cues; modality, not conditionals), 200 sentences
     with a cue and 200 without, labelled by the six judges with the frozen
     prompt. Reported: the share of cue sentences each judge or rule marks
     as "hedging" (and as any kind), and the share of cue-free sentences
     it marks, weighted to the corpus.

Stages
  build    parse the corpus and draw the 400 sentences (seed 62)
  smoke    one batch of ten sentences outside the sample, each judge; not recorded
  judge    six judges, batches of ten (resumable)
  measure  -> bench/analysis/cell62/check_measured.json

Run:  .venv/bin/python train/run_cell62_check.py build|smoke|judge|measure
"""
from __future__ import annotations

import collections
import json
import random
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                              # noqa: E402
from gst.smallcluster import kappa                                  # noqa: E402
from train import run_cell62_instrument as C62                      # noqa: E402
from train.cell23_presence_calib import DEFS                        # noqa: E402
from train.run_cellIV_batchjudge import ALL_FAMS, PROMPT, parse     # noqa: E402

REGISTRATION = runlog.registration_for("62-check", ROOT)
OUT = ROOT / "bench" / "analysis" / "cell62"
EXT = ROOT / "bench" / "external" / "sfu_review" / "SFU_Review_Corpus_Negation_Speculation"
ITEMS = OUT / "check_items.json"
LABELS = OUT / "check_judge_labels.json"
CALLS = ROOT / "bench" / "runs" / "cell62_check_calls.jsonl"
JUDGES, RULES, FAMS, BATCH = C62.JUDGES, C62.RULES, C62.FAMS, C62.BATCH
SEED = 62
N_PER_CLASS = 200
MIN_WORDS = 6


# ------------------------------------------------------------------ corpus

def _detok(words: list[str]) -> str:
    out = ""
    for w in words:
        if out and (w in {".", ",", "!", "?", ";", ":", ")", "'s", "n't", "'ll", "'re", "'ve", "'m", "'d", "%"}
                    or out.endswith("(") or out.endswith("$")):
            out += w
        else:
            out += (" " if out else "") + w
    return out


def _sentences() -> list[dict]:
    rows = []
    for path in sorted(EXT.glob("*/*.xml")):
        tree = ET.parse(path)
        for n, sent in enumerate(tree.iter("SENTENCE")):
            words = [w.text for w in sent.iter("W") if w.text]
            cues = {c.get("type") for c in sent.iter("cue")}
            text = _detok(words)
            if len(words) < MIN_WORDS or not re.search(r"[A-Za-z]{2,}", text):
                continue
            rows.append({"id": f"{path.parent.name}/{path.stem}#{n}", "text": text,
                         "speculation": "speculation" in cues, "negation": "negation" in cues})
    return rows


def stage_build() -> None:
    rows = _sentences()
    pos = sorted((r for r in rows if r["speculation"]), key=lambda r: r["id"])
    neg = sorted((r for r in rows if not r["speculation"]), key=lambda r: r["id"])
    rng = random.Random(SEED)
    sample = rng.sample(pos, N_PER_CLASS) + rng.sample(neg, N_PER_CLASS)
    for r in sample:
        r["w"] = (len(pos) if r["speculation"] else len(neg)) / N_PER_CLASS
    sample.sort(key=lambda r: r["id"])
    OUT.mkdir(parents=True, exist_ok=True)
    ITEMS.write_text(json.dumps({"seed": SEED, "pool": {"speculation": len(pos), "none": len(neg)}, "items": sample},
                                ensure_ascii=False, indent=0))
    print(f"corpus: {len(rows)} sentences of {MIN_WORDS}+ words, {len(pos)} with a speculation cue; sampled {len(sample)}")


# ------------------------------------------------------------------ judging

def _judge_chunk(judge: str, sentences: list[str], tag: str, record: bool) -> dict | None:
    body = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    prompt = PROMPT.format(n=len(sentences), items=body, defs="\n".join(f"- {f}: {DEFS[f]}" for f in ALL_FAMS))
    for attempt in range(2):
        text, meta = runlog.chat_logged(judge, None, prompt, temperature=0.0, max_tokens=4096,
                                        seed=runlog.seed_for(tag) + attempt)
        res = parse(text, len(sentences))
        if record:
            runlog.append_jsonl(CALLS, runlog.stamp(
                {"tag": tag, "judge": judge, "n": len(sentences), "attempt": attempt, "parsed": res is not None},
                meta, root=ROOT, script=Path(__file__), registration=REGISTRATION))
        if res is not None:
            return res
    return None


def _judge_items(judge: str, items: list[dict], store: dict, prefix: str, record: bool = True) -> int:
    fails = 0
    for start in range(0, len(items), BATCH):
        chunk = [it for it in items[start:start + BATCH] if it["id"] not in store]
        if not chunk:
            continue
        res = _judge_chunk(judge, [c["text"] for c in chunk], f"{prefix}|{judge}|{start}", record)
        if res is not None:
            for i, c in enumerate(chunk):
                store[c["id"]] = res[i + 1]
            continue
        half = (len(chunk) + 1) // 2
        for part, sub in enumerate((chunk[:half], chunk[half:])):
            if not sub:
                continue
            res = _judge_chunk(judge, [c["text"] for c in sub], f"{prefix}|{judge}|{start}|half{part}", record)
            if res is None:
                fails += len(sub)
                continue
            for i, c in enumerate(sub):
                store[c["id"]] = res[i + 1]
    return fails


def stage_smoke() -> None:
    have = {it["id"] for it in json.loads(ITEMS.read_text())["items"]}
    extra = [r for r in _sentences() if r["id"] not in have][:BATCH]
    for judge in JUDGES:
        store: dict = {}
        fails = _judge_items(judge, extra, store, "SMOKE", record=False)
        flagged = sum(any(v.values()) for v in store.values())
        print(f"  SMOKE {judge}: {len(store)} of {len(extra)} parsed, {fails} unparsed, {flagged} with any kind")


def stage_judge() -> None:
    items = json.loads(ITEMS.read_text())["items"]
    labels = json.loads(LABELS.read_text()) if LABELS.exists() else {}
    for judge in JUDGES:
        store = labels.setdefault(judge, {})
        t0 = time.time()
        fails = _judge_items(judge, items, store, "cell62check")
        LABELS.write_text(json.dumps(labels))
        print(f"cell62-check judge {judge}: {len(store)}/{len(items)} labelled, {fails} unparsed, {time.time()-t0:.0f}s", flush=True)
    print("cell62-check judging complete")


# ------------------------------------------------------------------ measure

def _rate(rows, pred) -> float:
    w = sum(r["w"] for r in rows)
    return sum(r["w"] for r in rows if pred(r)) / w if w else float("nan")


def stage_measure() -> None:
    print("=" * 78)
    print("CELL 62 AMENDED — the sentence judges without a person's labels (reported, no bar)")
    print("=" * 78)
    out: dict = {"P62.0": "NOT EVALUABLE", "P62.1": "NOT EVALUABLE", "P62.2": "NOT EVALUABLE"}
    print("  P62.0: NOT EVALUABLE — no person's labels\n  P62.1: NOT EVALUABLE — no reference\n  P62.2: NOT EVALUABLE — no reference")

    # 1. judge-only parts of P62.3 on the Cell 62 sample
    task = json.loads((C62.TASK / "task.json").read_text())
    key = json.loads((C62.TASK / "key.json").read_text())["items"]
    jl = json.loads((C62.OUT / "judge_labels.json").read_text())
    ids = [it["id"] for it in task["items"] if all(it["id"] in jl.get(j, {}) for j in JUDGES)]
    print(f"\n1. The 404-sentence sample: {len(ids)} sentences labelled by all six judges")
    out["sample"] = {"n": len(ids), "pairwise_kappa": {}, "stored_self_agreement": {}, "latent_class": {}, "flag_rate": {}}
    for f in FAMS:
        print(f"   kind {f}: share flagged " + ", ".join(f"{j.split(':')[0]} {sum(jl[j][i][f] for i in ids)/len(ids):.2f}" for j in JUDGES))
        out["sample"]["flag_rate"][f] = {j: sum(jl[j][i][f] for i in ids) / len(ids) for j in JUDGES}
        ks = {}
        for a in range(len(JUDGES)):
            for b in range(a + 1, len(JUDGES)):
                ja, jb = JUDGES[a], JUDGES[b]
                k = kappa([(jl[ja][i][f], jl[jb][i][f]) for i in ids])["kappa"]
                ks[f"{ja}|{jb}"] = k
        out["sample"]["pairwise_kappa"][f] = ks
        vals = sorted(ks.values())
        print(f"     kappa between judges: lowest {vals[0]:.2f}, median {vals[len(vals)//2]:.2f}, highest {vals[-1]:.2f}; "
              f"stored pair {ks[f'{C62.STORED[0]}|{C62.STORED[1]}']:.2f}")
        for j in C62.STORED:
            pairs = [(key[i]["stored"][j][f], jl[j][i][f]) for i in ids]
            k = kappa(pairs)
            out["sample"]["stored_self_agreement"][f"{f}|{j}"] = k
            print(f"     {j.split(':')[0]} against its own stored label: raw {k['raw']:.2f}, kappa {k['kappa']:.2f}")
        ds = C62.dawid_skene([[jl[j][i][f] for j in JUDGES] for i in ids])
        out["sample"]["latent_class"][f] = ds
        print(f"     latent-class estimate: prevalence {ds['prevalence']:.2f}; hit rates "
              + ", ".join(f"{j.split(':')[0]} {h:.2f}" for j, h in zip(JUDGES, ds["hit"]))
              + "; false alarms " + ", ".join(f"{j.split(':')[0]} {h:.2f}" for j, h in zip(JUDGES, ds["false_alarm"])))

    # 2. SFU neighbouring-construct check
    doc = json.loads(ITEMS.read_text())
    cl = json.loads(LABELS.read_text()) if LABELS.exists() else {}
    rows = [r for r in doc["items"] if all(r["id"] in cl.get(j, {}) for j in JUDGES)]
    print(f"\n2. SFU Review Corpus: {len(rows)} of {len(doc['items'])} sentences labelled by all six judges "
          f"(pool {doc['pool']}); weighted to the corpus")
    out["sfu"] = {"n": len(rows), "pool": doc["pool"], "hedging": {}, "any_kind": {}}
    print(f"   {'judge or rule':<36}{'cue sentences marked hedging':>30}{'cue-free marked hedging':>26}{'cue marked any kind':>22}{'cue-free any kind':>20}")
    for name, (needed, fn) in RULES.items():
        hed = lambda r, needed=needed, fn=fn: fn([cl[j][r["id"]]["hedging"] for j in needed])          # noqa: E731
        anyk = lambda r, needed=needed, fn=fn: fn([any(cl[j][r["id"]].values()) for j in needed])    # noqa: E731
        pos = [r for r in rows if r["speculation"]]
        neg = [r for r in rows if not r["speculation"]]
        d = {"cue_hedging": _rate(pos, hed), "free_hedging": _rate(neg, hed), "cue_any": _rate(pos, anyk), "free_any": _rate(neg, anyk)}
        out["sfu"]["hedging"][name] = d
        print(f"   {name:<36}{d['cue_hedging']:>30.3f}{d['free_hedging']:>26.3f}{d['cue_any']:>22.3f}{d['free_any']:>20.3f}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "check_measured.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "measure"
    {"build": stage_build, "smoke": stage_smoke, "judge": stage_judge, "measure": stage_measure}[stage]()
