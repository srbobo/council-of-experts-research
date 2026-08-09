"""Measure Cells 30 and 31 with the Cell IV-validated instrument.

Deviation recorded in RUNBOOK_PAPER_HARDENING.md ("CELL 31 — REGISTERED
DEVIATION"). Batched sentence judging at B=10, both judges, both-agree
rule. Measured variable: count of qualification-bearing sentences.

Sentences are batched GLOBALLY across documents — the condition Cell IV
validated (200 unrelated sentences judged independently).

Stages:
  judge    2,339 sentences -> 234 batches x 2 judges (resumable)
  measure  paired cluster bootstrap, P31.1 / P31.2 as sign tests

Run:  .venv/bin/python train/run_measure_c30_c31.py judge
      .venv/bin/python train/run_measure_c30_c31.py measure
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst.nli import sentence_spans                                  # noqa: E402
from train.cell23_presence_calib import DEFS, JUDGES                # noqa: E402
from train.run_cellIV_batchjudge import ALL_FAMS, PROMPT, parse     # noqa: E402
from train.run_cell25_moa import chat                               # noqa: E402

OUT = ROOT / "bench" / "analysis" / "c30c31"
B = 10
SEED = 0
DRAWS = 5000
SCORED = ("modeled", "jurisd", "hedging")   # cutoff excluded: 3 positives


def collect():
    """-> units: list of {id, kind, key, sentences[]}"""
    c30 = [json.loads(x) for x in
           (ROOT / "bench/runs/cell30_descaffold.jsonl").read_text().splitlines()
           if x.strip()]
    c31 = [json.loads(x) for x in
           (ROOT / "bench/runs/cell31_matched_ledger.jsonl").read_text().splitlines()
           if x.strip()]
    c30 = [r for r in c30 if len(r.get("output", "")) >= 500]
    c31 = [r for r in c31 if not r.get("protocol_violation")
           and len(r.get("output", "")) >= 500]
    units, variants = [], {}
    for r in c30:
        variants.setdefault((r["prompt_id"], r["variant_id"]),
                            "\n\n".join(r["upstream"]))
    for (pid, vid), text in variants.items():
        units.append({"id": f"up::{pid}::{vid}", "kind": "upstream",
                      "key": [pid, vid],
                      "sentences": [s for _a, _b, s in sentence_spans(text)]})
    for arm, rows in (("P", c30), ("L", c31)):
        for r in rows:
            units.append({"id": f"{arm}::{r['run_id']}", "kind": "output",
                          "arm": arm, "key": [r["prompt_id"], r["variant_id"]],
                          "writer": r.get("writer", "?"),
                          "sentences": [s for _a, _b, s in
                                        sentence_spans(r["output"])]})
    return units


def stage_judge() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    units = collect()
    (OUT / "units.json").write_text(json.dumps(units))
    flat = [(u["id"], i, s) for u in units for i, s in enumerate(u["sentences"])]
    print(f"{len(units)} units, {len(flat)} sentences, "
          f"{(len(flat)+B-1)//B} batches x {len(JUDGES)} judges", flush=True)
    cpath = OUT / "labels.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    t0, done = time.time(), 0
    for start in range(0, len(flat), B):
        chunk = flat[start:start + B]
        for judge in JUDGES:
            key = f"{judge}|{start}"
            if key in cache:
                continue
            body = "\n".join(f"{i+1}. {s}" for i, (_u, _i, s) in enumerate(chunk))
            res = parse(chat(judge, None, PROMPT.format(
                n=len(chunk),
                defs="\n".join(f"- {f}: {DEFS[f]}" for f in ALL_FAMS),
                items=body), temperature=0, max_tokens=4096), len(chunk))
            cache[key] = ({str(i + 1): res[i + 1] for i in range(len(chunk))}
                          if res else None)
            done += 1
            if done % 20 == 0:
                cpath.write_text(json.dumps(cache))
                el = time.time() - t0
                rem = (len(flat) // B + 1) * len(JUDGES) - len(cache)
                print(f"  {len(cache)} calls done, {el:.0f}s, ~{el/done*rem/3600:.1f}h "
                      f"left", flush=True)
    cpath.write_text(json.dumps(cache))
    fails = sum(1 for v in cache.values() if v is None)
    print(f"judge complete: {len(cache)} calls, {fails} unparseable "
          f"({fails/max(len(cache),1):.1%})")


def stage_measure() -> None:
    rng = random.Random(SEED)
    units = json.loads((OUT / "units.json").read_text())
    cache = json.loads((OUT / "labels.json").read_text())
    flat = [(u["id"], i) for u in units for i in range(len(u["sentences"]))]

    # both-agree rule per sentence
    labels: dict[str, list[dict]] = {u["id"]: [None] * len(u["sentences"])
                                     for u in units}
    unusable = 0
    for start in range(0, len(flat), B):
        chunk = flat[start:start + B]
        vs = [cache.get(f"{j}|{start}") for j in JUDGES]
        if any(v is None for v in vs):
            unusable += len(chunk)
            continue
        for k, (uid, idx) in enumerate(chunk):
            a, b = (v.get(str(k + 1)) for v in vs)
            if not a or not b:
                unusable += 1
                continue
            labels[uid][idx] = {f: bool(a[f] and b[f]) for f in ALL_FAMS}

    def count(uid):
        """sentences bearing >=1 SCORED family; None-labelled sentences skipped"""
        lab = [x for x in labels[uid] if x is not None]
        n_any = sum(1 for x in lab if any(x[f] for f in SCORED))
        per = {f: sum(1 for x in lab if x[f]) for f in SCORED}
        return n_any, per, len(lab)

    supply = {}
    for u in units:
        if u["kind"] == "upstream":
            n, per, _ = count(u["id"])
            supply[tuple(u["key"])] = (n, per)

    arms = {"P": [], "L": []}
    for u in units:
        if u["kind"] != "output":
            continue
        n, per, nlab = count(u["id"])
        s = supply.get(tuple(u["key"]))
        if s is None:
            continue
        arms[u["arm"]].append({"key": tuple(u["key"]), "s": float(s[0]),
                               "y": float(n), "per": per, "nlab": nlab,
                               "writer": u["writer"]})
    print(f"unusable sentence-labels: {unusable}")
    for a in ("P", "L"):
        v = arms[a]
        print(f"  arm {a}: {len(v)} runs, mean supply {sum(x['s'] for x in v)/len(v):.2f}, "
              f"mean emitted {sum(x['y'] for x in v)/len(v):.2f}")

    def ols(rows):
        n = len(rows)
        mx = sum(r["s"] for r in rows) / n
        my = sum(r["y"] for r in rows) / n
        sxx = sum((r["s"] - mx) ** 2 for r in rows)
        if sxx == 0:
            return None
        w = sum((r["s"] - mx) * (r["y"] - my) for r in rows) / sxx
        return w, my - w * mx

    fp, fl = ols(arms["P"]), ols(arms["L"])
    if not fp or not fl:
        print("unidentifiable — stop")
        return
    print(f"\n  arm P (plain):  w={fp[0]:.3f}  c={fp[1]:+.3f}")
    print(f"  arm L (ledger): w={fl[0]:.3f}  c={fl[1]:+.3f}")

    keys = sorted({r["key"] for r in arms["P"]} & {r["key"] for r in arms["L"]})
    byP, byL = {}, {}
    for r in arms["P"]:
        byP.setdefault(r["key"], []).append(r)
    for r in arms["L"]:
        byL.setdefault(r["key"], []).append(r)
    dw, dc = [], []
    for _ in range(DRAWS):
        samp = [keys[rng.randrange(len(keys))] for _ in keys]
        rp = [x for k in samp for x in byP.get(k, [])]
        rl = [x for k in samp for x in byL.get(k, [])]
        a, b = ols(rl), ols(rp)
        if a and b:
            dw.append(a[0] - b[0])
            dc.append(a[1] - b[1])
    dw.sort()
    dc.sort()
    lo_c, hi_c = dc[int(.025 * len(dc))], dc[int(.975 * len(dc))]
    lo_w, hi_w = dw[int(.025 * len(dw))], dw[int(.975 * len(dw))]
    print(f"  shared variants: {len(keys)}")
    print("=" * 70)
    print(f"P31.1 delta-c = {fl[1]-fp[1]:+.3f} [{lo_c:+.3f},{hi_c:+.3f}] -> "
          f"{'SUPPORTED (entirely below 0)' if hi_c < 0 else 'FALSIFIED (includes 0)'}")
    print(f"P31.2 delta-w = {fl[0]-fp[0]:+.3f} [{lo_w:+.3f},{hi_w:+.3f}] -> "
          f"{'FALSIFIED (below 0 — bought by silence)' if hi_w < 0 else 'SUPPORTED'}")
    print("=" * 70)
    for a in ("P", "L"):
        z = [r["y"] for r in arms[a] if r["s"] == 0]
        print(f"  arm {a}: zero-supply runs {len(z)}, mean emitted "
              f"{sum(z)/len(z) if z else float('nan'):.2f}")
    print("  per-family mean emitted:")
    for a in ("P", "L"):
        per = {f: sum(r["per"][f] for r in arms[a]) / len(arms[a]) for f in SCORED}
        print(f"    arm {a}: " + "  ".join(f"{f}={v:.2f}" for f, v in per.items()))
    (OUT / "measured.json").write_text(json.dumps(
        {"P": arms["P"], "L": arms["L"]}, default=list, indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "judge"
    {"judge": stage_judge, "measure": stage_measure}[stage]()
