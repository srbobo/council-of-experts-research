"""Cell 66 amendment — the conveyed judge checked without a person.

Registered: RUNBOOK_PAPER_HARDENING.md "CELL 66 AMENDMENT (2026-10-02)".
Replaces the person's 120 labels (P66.0) with

  Part A  public human labels: FRANK summary sentences (no error vs a
          content error, unanimous), judged against the three closest
          article sentences, as the experiment judges a statement against
          the three closest answer sentences. Rule under test: both judges
          FULLY. Bars: kappa >= 0.60 and F1 >= 0.80, weighted to the pool.
  Part B  known values on repeat 6 of Cell 41's control answers, which the
          experiment does not use: K1 verbatim answer sentences (FULLY by
          both >= 0.90), K2 a specialist figure altered by the Cell 63
          rule (altered form FULLY by both <= 0.10 among originals that
          were FULLY), K3 a statement from another scenario (conveyed by
          the rule <= 0.05).

Stages
  frank    draw the 300 FRANK sentences and shortlist their passages
  known    build the K1/K2/K3 items and shortlist their passages
  smoke    two FRANK validation-split sentences and one repeat-6 item that
           are not in the samples; nothing recorded
  judge    both judges, every statement (resumable)
  measure  verdict for the amended P66.0 -> bench/analysis/cell66/check_measured.json

Run:  .venv/bin/python train/run_cell66_check.py frank|known|smoke|judge|measure
"""
from __future__ import annotations

import collections
import json
import math
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                              # noqa: E402
from train import run_cell66_conveyed as C66                        # noqa: E402
from train.run_cell46_writer_replication import split_sentences    # noqa: E402
from train.run_cell63_checkable import _perturb                     # noqa: E402

REGISTRATION = runlog.registration_for("66-check", ROOT)
AN = ROOT / "bench" / "analysis"
OUT = AN / "cell66"
EXT = ROOT / "bench" / "external" / "frank"
ITEMS = OUT / "check_items.json"
CALLS = ROOT / "bench" / "runs" / "cell66_check.jsonl"
JUDGES = C66.JUDGES
SEED = 66
N_FRANK = 150                      # per class
N_K1, N_K2, N_K3 = 50, 80, 50
MIN_WORDS = 6
MIN_K2_FULLY = 15
CONTENT_ERRORS = {"EntE", "OutE", "CircE", "RelE", "CorefE", "LinkE"}
BARS = {"kappa": 0.60, "f1": 0.80, "k1": 0.90, "k2": 0.10, "k3": 0.05}
REP6 = 6


# ------------------------------------------------------------------ items

def _load_items() -> dict:
    return json.loads(ITEMS.read_text()) if ITEMS.exists() else {"items": []}


def _save_items(doc: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ITEMS.write_text(json.dumps(doc, ensure_ascii=False, indent=0))


def _frank_pool(split: str) -> list[dict]:
    rows = json.loads((EXT / "human_annotations_sentence.json").read_text())
    pool = []
    for r in rows:
        if r["split"] != split:
            continue
        for k, (s, ann) in enumerate(zip(r["summary_sentences"], r["summary_sentences_annotations"])):
            if len(s.split()) < MIN_WORDS:
                continue
            votes = [set(ann[a]) for a in sorted(ann)]
            if len(votes) != 3:
                continue
            noe = ["NoE" in v for v in votes]
            if all(noe):
                truth = True
            elif not any(noe) and sum(bool(v & CONTENT_ERRORS) for v in votes) >= 2:
                truth = False
            else:
                continue
            pool.append({"id": f"frank_{r['hash']}_{r['model_name']}_{k}", "part": "A", "statement": s,
                         "truth_fully": truth, "source": r["article"], "model": r["model_name"]})
    return pool


def stage_frank() -> None:
    pool = _frank_pool("test")
    pos = sorted((p for p in pool if p["truth_fully"]), key=lambda p: p["id"])
    neg = sorted((p for p in pool if not p["truth_fully"]), key=lambda p: p["id"])
    rng = random.Random(SEED)
    sample = rng.sample(pos, N_FRANK) + rng.sample(neg, N_FRANK)
    for p in sample:
        p["w"] = (len(pos) if p["truth_fully"] else len(neg)) / N_FRANK
    doc = _load_items()
    doc["frank_pool"] = {"no_error": len(pos), "error": len(neg)}
    doc["items"] = [it for it in doc["items"] if it["part"] != "A"] + sample
    _save_items(doc)
    print(f"frank: pool {len(pos)} no-error and {len(neg)} error sentences (test split, unanimous); sampled {len(sample)}")
    _shortlist("A")


def _prose(s: str) -> bool:
    """A plain sentence: no table row, line break or list marker, at least
    six words of letters. The experiment's own filter (_wordy) plus these."""
    s = s.strip()
    return (C66._wordy(s) and "|" not in s and "<br" not in s and "\n" not in s
            and not re.match(r"^[#*\-•\d]+[.)]?\s", s) and len(s.split()) >= MIN_WORDS)


def _rep6() -> dict[str, list[str]]:
    lab = json.loads((AN / "cell41" / "labels.json").read_text())
    return {k.split("__")[0]: [s for s in lab[k]["sentences"] if s.strip()]
            for k in lab if k.endswith(f"__control__r{REP6}")}


def _figure_sentences(seats: dict) -> list[dict]:
    """Specialist sentences with exactly one alterable integer (two or more
    digits, not part of a decimal, year-like figures excluded)."""
    out = []
    for case in sorted(seats):
        for seat in sorted(seats[case]):
            for s in split_sentences(seats[case][seat]):
                s = s.strip()
                if not _prose(s):
                    continue
                figs = [m for m in re.finditer(r"(?<![\d.,])\d{1,3}(?:,\d{3})+|(?<![\d.,])\d{2,}(?![\d.,%]*\d)", s)]
                if len(figs) != 1:
                    continue
                m = figs[0]
                v = int(m.group(0).replace(",", ""))
                if 1900 <= v <= 2100 or v < 10:
                    continue
                w = _perturb(v, up=(v % 2 == 0))
                if w is None:
                    continue
                alt = f"{w:,}" if "," in m.group(0) else str(w)
                if alt in s:
                    continue
                out.append({"case": case, "seat": seat, "statement": s,
                            "altered": s[:m.start()] + alt + s[m.end():], "figure": m.group(0), "altered_figure": alt})
    return out


def stage_known() -> None:
    answers = _rep6()
    seats = json.loads((AN / "cell41" / "seats.json").read_text())
    cases = sorted(c for c in answers if c in seats)
    rng = random.Random(SEED + 1)
    items = []
    # K1: verbatim answer sentences
    k1_pool = [{"case": c, "statement": s.strip()} for c in cases for s in answers[c] if _prose(s)]
    for n, p in enumerate(rng.sample(k1_pool, N_K1)):
        items.append({"id": f"k1_{n:03d}", "part": "K1", "case": p["case"], "answer_case": p["case"], "statement": p["statement"]})
    # K2: a specialist figure, original and altered
    k2_pool = [p for p in _figure_sentences(seats) if p["case"] in cases]
    for n, p in enumerate(rng.sample(k2_pool, N_K2)):
        items.append({"id": f"k2_{n:03d}_orig", "part": "K2", "form": "original", "pair": n, "case": p["case"],
                      "answer_case": p["case"], "statement": p["statement"], "figure": p["figure"]})
        items.append({"id": f"k2_{n:03d}_alt", "part": "K2", "form": "altered", "pair": n, "case": p["case"],
                      "answer_case": p["case"], "statement": p["altered"], "figure": p["altered_figure"]})
    # K3: a specialist sentence against another scenario's answer
    k3_pool = [{"case": c, "statement": s.strip()} for c in cases for seat in seats[c]
               for s in split_sentences(seats[c][seat]) if _prose(s)]
    for n, p in enumerate(rng.sample(k3_pool, N_K3)):
        other = rng.choice([c for c in cases if c != p["case"]])
        items.append({"id": f"k3_{n:03d}", "part": "K3", "case": p["case"], "answer_case": other, "statement": p["statement"]})
    doc = _load_items()
    doc["known_pools"] = {"K1": len(k1_pool), "K2": len(k2_pool), "K3": len(k3_pool)}
    doc["items"] = [it for it in doc["items"] if it["part"] == "A"] + items
    _save_items(doc)
    print(f"known: pools K1 {len(k1_pool)}, K2 {len(k2_pool)}, K3 {len(k3_pool)}; built {len(items)} items")
    _shortlist("K")


def _shortlist(which: str) -> None:
    """Top three source sentences by embedding, as the experiment does."""
    doc = _load_items()
    if "--no-embed" in sys.argv:                     # dry run of the item construction only
        return
    answers = _rep6() if which == "K" else {}
    todo = [it for it in doc["items"] if it["part"].startswith(which) and "short" not in it]
    by = collections.defaultdict(list)
    for it in todo:
        by[it["answer_case"] if which == "K" else it["id"]].append(it)
    t0 = time.time()
    for n, (k, its) in enumerate(sorted(by.items())):
        sents = answers[k] if which == "K" else [s.strip() for s in split_sentences(its[0]["source"]) if s.strip()]
        ev = C66._embed(["search_document: " + s for s in sents])
        qv = C66._embed(["search_query: " + it["statement"] for it in its])
        for it, q in zip(its, qv):
            top = sorted(((C66._cos(q, e), i) for i, e in enumerate(ev)), reverse=True)[:C66.TOP]
            it["short"] = [{"i": i, "sim": round(s, 4), "text": sents[i]} for s, i in top]
        if (n + 1) % 25 == 0:
            print(f"  {n+1}/{len(by)} shortlisted, {time.time()-t0:.0f}s", flush=True)
    for it in doc["items"]:
        it.pop("source", None)
    _save_items(doc)
    print(f"shortlist complete for part {which}; embedding model digest {runlog.model_digest(C66.EMBED)}")


# ------------------------------------------------------------------ judging

def _judge(judge: str, key: str, statement: str, short: list[dict], record: bool) -> str | None:
    text, meta = runlog.chat_logged(judge, None, C66.PROMPT.format(statement=statement, label=C66.SHORT_LABEL,
                                                                    passages=C66._passages(short)),
                                    temperature=0.0, max_tokens=C66.MAX_TOKENS, seed=runlog.seed_for(key))
    v = C66.parse_verdict(text)
    if record:
        runlog.append_jsonl(CALLS, runlog.stamp({"key": key, "judge": judge, "verdict": v}, meta,
                                                root=ROOT, script=Path(__file__), registration=REGISTRATION))
    return v


def stage_smoke() -> None:
    doc = _load_items()
    have = {it["id"] for it in doc["items"]}
    pool = [p for p in _frank_pool("valid") if p["id"] not in have][:2]
    answers = _rep6()
    c = sorted(answers)[0]
    extra = [{"id": "smoke_k1", "statement": answers[c][-1], "answer_case": c}]
    for p in pool:
        sents = [s.strip() for s in split_sentences(p["source"]) if s.strip()]
        ev = C66._embed(["search_document: " + s for s in sents])
        q = C66._embed(["search_query: " + p["statement"]])[0]
        top = sorted(((C66._cos(q, e), i) for i, e in enumerate(ev)), reverse=True)[:C66.TOP]
        p["short"] = [{"i": i, "sim": round(s, 4), "text": sents[i]} for s, i in top]
    for it in extra:
        sents = answers[it["answer_case"]]
        ev = C66._embed(["search_document: " + s for s in sents])
        q = C66._embed(["search_query: " + it["statement"]])[0]
        top = sorted(((C66._cos(q, e), i) for i, e in enumerate(ev)), reverse=True)[:C66.TOP]
        it["short"] = [{"i": i, "sim": round(s, 4), "text": sents[i]} for s, i in top]
    for it in pool + extra:
        for j in JUDGES:
            print(f"  SMOKE {it['id']} {j}: {_judge(j, 'SMOKE|' + it['id'], it['statement'], it['short'], record=False)}")


def stage_judge(only: str | None = None) -> None:
    doc = _load_items()
    done = {r["key"] for r in runlog.read_jsonl(CALLS)}
    for judge in ([only] if only else JUDGES):
        jobs = [it for it in doc["items"] if f"{judge}|{it['id']}" not in done]
        print(f"cell66-check {judge}: {len(jobs)} statements to go", flush=True)
        t0 = time.time()
        for n, it in enumerate(jobs):
            _judge(judge, f"{judge}|{it['id']}", it["statement"], it["short"], record=True)
            if (n + 1) % 50 == 0:
                el = time.time() - t0
                print(f"  {n+1}/{len(jobs)} {el:.0f}s ~{el/(n+1)*(len(jobs)-n-1)/60:.0f}m left", flush=True)
        print(f"cell66-check {judge}: complete", flush=True)


# ------------------------------------------------------------------ measure

def _verdicts() -> dict[str, dict[str, str | None]]:
    v: dict[str, dict] = collections.defaultdict(dict)
    for r in runlog.read_jsonl(CALLS):
        j, iid = r["key"].split("|", 1)
        v[iid][j] = r["verdict"]
    return v


def _weighted(rows: list[dict], truth, pred) -> dict:
    """Weighted confusion counts, kappa and precision/recall/F1."""
    tp = sum(r["w"] for r in rows if truth(r) and pred(r))
    fp = sum(r["w"] for r in rows if not truth(r) and pred(r))
    fn = sum(r["w"] for r in rows if truth(r) and not pred(r))
    tn = sum(r["w"] for r in rows if not truth(r) and not pred(r))
    n = tp + fp + fn + tn
    raw = (tp + tn) / n
    pa, pb = (tp + fn) / n, (tp + fp) / n
    chance = pa * pb + (1 - pa) * (1 - pb)
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    return {"n": len(rows), "raw": raw, "kappa": (raw - chance) / (1 - chance) if chance < 1 else float("nan"),
            "precision": prec, "recall": rec, "f1": 2 * prec * rec / (prec + rec) if tp else 0.0,
            "unweighted": {"tp": sum(1 for r in rows if truth(r) and pred(r)), "fp": sum(1 for r in rows if not truth(r) and pred(r)),
                           "fn": sum(1 for r in rows if truth(r) and not pred(r)), "tn": sum(1 for r in rows if not truth(r) and not pred(r))}}


def stage_measure() -> None:
    doc = _load_items()
    v = _verdicts()
    items = doc["items"]
    missing = [it["id"] for it in items if any(v.get(it["id"], {}).get(j) is None for j in JUDGES)]
    print("=" * 78)
    print("CELL 66 AMENDED P66.0 — the conveyed judge against public human labels and known values")
    print("=" * 78)
    print(f"statements {len(items)}; without a parsed verdict from both judges {len(missing)} (set aside)")
    ok = [it for it in items if it["id"] not in missing]
    both_fully = lambda it: all(v[it["id"]][j] == "fully" for j in JUDGES)                      # noqa: E731
    conveyed = lambda it: all(v[it["id"]][j] in ("fully", "partly") for j in JUDGES)             # noqa: E731
    out = {"missing": len(missing)}

    # Part A
    a = [it for it in ok if it["part"] == "A"]
    out["A"] = {"both_fully": _weighted(a, lambda r: r["truth_fully"], both_fully),
                "conveyed_rule_reported": _weighted(a, lambda r: r["truth_fully"], conveyed)}
    for j in JUDGES:
        out["A"][f"{j} alone"] = _weighted(a, lambda r: r["truth_fully"], lambda r, j=j: v[r["id"]][j] == "fully")
    print(f"\nPart A — FRANK, {len(a)} sentences ({sum(r['truth_fully'] for r in a)} no-error, "
          f"{sum(not r['truth_fully'] for r in a)} error), weighted to a pool of {doc.get('frank_pool')}")
    for name, d in out["A"].items():
        print(f"  {name:<32} kappa {d['kappa']:.3f}  precision {d['precision']:.3f}  recall {d['recall']:.3f}  "
              f"F1 {d['f1']:.3f}  counts tp/fp/fn/tn {d['unweighted']['tp']}/{d['unweighted']['fp']}/{d['unweighted']['fn']}/{d['unweighted']['tn']}")
    a_pass = out["A"]["both_fully"]["kappa"] >= BARS["kappa"] and out["A"]["both_fully"]["f1"] >= BARS["f1"]

    # Part B
    k1 = [it for it in ok if it["part"] == "K1"]
    k1_rate = sum(both_fully(it) for it in k1) / len(k1) if k1 else float("nan")
    k3 = [it for it in ok if it["part"] == "K3"]
    k3_rate = sum(conveyed(it) for it in k3) / len(k3) if k3 else float("nan")
    pairs = collections.defaultdict(dict)
    for it in ok:
        if it["part"] == "K2":
            pairs[it["pair"]][it["form"]] = it
    full_orig = [p for p in pairs.values() if "original" in p and "altered" in p and both_fully(p["original"])]
    k2_n = len(full_orig)
    k2_rate = sum(both_fully(p["altered"]) for p in full_orig) / k2_n if k2_n else float("nan")
    k2_partly = sum(conveyed(p["altered"]) and not both_fully(p["altered"]) for p in full_orig) / k2_n if k2_n else float("nan")
    out["B"] = {"K1": {"n": len(k1), "both_fully": k1_rate}, "K2": {"pairs": len(pairs), "originals_fully": k2_n,
                "altered_fully": k2_rate, "altered_partly": k2_partly, "evaluable": k2_n >= MIN_K2_FULLY},
                "K3": {"n": len(k3), "conveyed": k3_rate}}
    print(f"\nPart B — known values on repeat 6 (unused by the experiment)")
    print(f"  K1 verbatim answer sentences FULLY by both: {k1_rate:.3f} (n = {len(k1)}; bar at least {BARS['k1']})")
    print(f"  K2 altered figure: originals FULLY by both {k2_n} of {len(pairs)}; altered form FULLY by both {k2_rate:.3f}, "
          f"PARTLY {k2_partly:.3f} (bar at most {BARS['k2']}; needs {MIN_K2_FULLY} originals)")
    print(f"  K3 other scenario conveyed by the rule: {k3_rate:.3f} (n = {len(k3)}; bar at most {BARS['k3']})")
    k1_pass = k1_rate >= BARS["k1"]
    k3_pass = k3_rate <= BARS["k3"]
    k2_pass = (k2_rate <= BARS["k2"]) if k2_n >= MIN_K2_FULLY else None

    parts = {"A": a_pass, "K1": k1_pass, "K2": k2_pass, "K3": k3_pass}
    failed = [k for k, p in parts.items() if p is False]
    out["pass"] = not failed
    out["parts"] = parts
    print("\n  VERDICT LINE (amended P66.0, as registered)")
    if failed:
        print(f"  P66.0: FAILS — part(s) {', '.join(failed)} below the bar; P66.1 is NOT EVALUABLE with this tool (blocked)")
    else:
        print("  P66.0: PASSES — " + ", ".join(f"{k} {'passes' if p else 'not evaluable'}" for k, p in parts.items()))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "check_measured.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "measure"
    if stage == "judge":
        stage_judge(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        {"frank": stage_frank, "known": stage_known, "smoke": stage_smoke, "measure": stage_measure}[stage]()
