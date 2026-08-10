"""Cell 38 — judge-driven ablation: invention at TRUE zero supply.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 38 PRE-REGISTRATION".
Supply is CONFIRMED by re-judging the ablated upstream, never assumed —
the step whose absence produced finding #10.

Stages: ablate -> runs -> judge -> measure
Run:  .venv/bin/python train/run_cell38_judge_ablation.py ablate
      ... runs / judge / measure
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst.nli import sentence_spans                              # noqa: E402
from train.cell23_presence_calib import DEFS, JUDGES            # noqa: E402
from train.run_cellIV_batchjudge import ALL_FAMS, PROMPT, parse  # noqa: E402
from train.run_cell25_moa import CASES, chat                    # noqa: E402
from train.run_cell30_descaffold import SEATS, WRITER_PROMPT    # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell38"
C30 = ROOT / "bench" / "analysis" / "cell30"
RUNS = ROOT / "bench" / "runs" / "cell38.jsonl"
WRITER = "gpt-oss:20b"
B, REPEATS, SEED = 10, 3, 0
SCORED = ("modeled", "jurisd", "hedging")


def judge_sentences(sents, cache, tag):
    """Batched B=10, both judges, both-agree. Returns list of dict|None."""
    out = [None] * len(sents)
    for start in range(0, len(sents), B):
        chunk = sents[start:start + B]
        vs = []
        for j in JUDGES:
            key = f"{tag}|{j}|{start}"
            if key not in cache:
                body = "\n".join(f"{i+1}. {s}" for i, s in enumerate(chunk))
                res = parse(chat(j, None, PROMPT.format(
                    n=len(chunk),
                    defs="\n".join(f"- {f}: {DEFS[f]}" for f in ALL_FAMS),
                    items=body), temperature=0, max_tokens=4096), len(chunk))
                cache[key] = ({str(i + 1): res[i + 1] for i in range(len(chunk))}
                              if res else None)
            vs.append(cache[key])
        if any(v is None for v in vs):
            continue
        for k in range(len(chunk)):
            a, b = (v.get(str(k + 1)) for v in vs)
            if a and b:
                out[start + k] = {f: bool(a[f] and b[f]) for f in ALL_FAMS}
    return out


def flagged(lab):
    return lab is not None and any(lab[f] for f in SCORED)


def stage_ablate() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    seats = json.loads((C30 / "seats.json").read_text())
    cpath = OUT / "cache.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    result = {}
    t0 = time.time()
    for case in CASES:
        full, ablated, stats = {}, {}, {}
        for role in SEATS:
            text = seats[case].get(role, "")
            spans = sentence_spans(text)
            labs = judge_sentences([s for _a, _b, s in spans], cache,
                                   f"full|{case}|{role}")
            keep = [(a, b) for (a, b, _s), lab in zip(spans, labs, strict=True)
                    if not flagged(lab)]
            full[role] = text
            ablated[role] = " ".join(text[a:b].strip() for a, b in keep).strip()
            stats[role] = {"sentences": len(spans),
                           "removed": sum(1 for x in labs if flagged(x)),
                           "unlabelled": sum(1 for x in labs if x is None)}
        result[case] = {"full": full, "ablated": ablated, "stats": stats}
        cpath.write_text(json.dumps(cache))
        rem = sum(v["removed"] for v in stats.values())
        tot = sum(v["sentences"] for v in stats.values())
        print(f"  {case[:38]:<40} removed {rem}/{tot} sentences "
              f"({time.time()-t0:.0f}s)", flush=True)
    (OUT / "ablated.json").write_text(json.dumps(result, ensure_ascii=False))

    # ---- P38.1: CONFIRM supply on the ablated text (never assumed)
    print("\nCONFIRMING supply on ablated upstream (P38.1)")
    confirm = {}
    for case in CASES:
        text = "\n\n".join(result[case]["ablated"][r] for r in SEATS)
        spans = sentence_spans(text)
        labs = judge_sentences([s for _a, _b, s in spans], cache,
                               f"abl|{case}")
        cpath.write_text(json.dumps(cache))
        n = sum(1 for x in labs if flagged(x))
        confirm[case] = {"remaining": n, "sentences": len(spans)}
        print(f"  {case[:38]:<40} remaining qualification sentences: {n}",
              flush=True)
    (OUT / "confirm.json").write_text(json.dumps(confirm))
    ok = sum(1 for v in confirm.values() if v["remaining"] <= 1)
    print(f"\nP38.1: {ok}/9 cases at <=1 remaining -> "
          f"{'SUPPORTED' if ok >= 7 else 'FALSIFIED'}")


def stage_runs() -> None:
    from examples.test_cases import get_case
    abl = json.loads((OUT / "ablated.json").read_text())
    done = set()
    if RUNS.exists():
        for line in RUNS.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    todo = [(c, arm, r) for c in CASES for arm in ("full", "zero")
            for r in range(REPEATS) if f"{c}__{arm}__r{r}" not in done]
    print(f"cell38: {len(todo)} runs to go", flush=True)
    t0 = time.time()
    with RUNS.open("a") as fh:
        for i, (case, arm, rep) in enumerate(todo):
            key = "full" if arm == "full" else "ablated"
            upstream = [abl[case][key][r] for r in SEATS if abl[case][key].get(r)]
            body = "\n\n".join(f"--- SPECIALIST CONTRIBUTION ---\n{t}"
                               for t in upstream)
            txt = chat(WRITER, WRITER_PROMPT,
                       f"{body}\n\nQuestion:\n{get_case(case).prompt}",
                       temperature=0.6, max_tokens=8192)
            if not txt or not txt.strip():
                print(f"  EMPTY {case}/{arm}/r{rep}", flush=True)
                continue
            fh.write(json.dumps({"run_id": f"{case}__{arm}__r{rep}", "case": case,
                                 "arm": arm, "repeat": rep, "upstream": upstream,
                                 "output": txt}, ensure_ascii=False) + "\n")
            fh.flush()
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)} {case[:32]}/{arm}/r{rep} {el:.0f}s "
                  f"~{el/(i+1)*(len(todo)-i-1):.0f}s left", flush=True)
    print("runs complete")


def stage_judge() -> None:
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    cpath = OUT / "cache.json"
    cache = json.loads(cpath.read_text())
    t0 = time.time()
    for i, r in enumerate(rows):
        sents = [s for _a, _b, s in sentence_spans(r["output"])]
        labs = judge_sentences(sents, cache, f"out|{r['run_id']}")
        r["n_qual"] = sum(1 for x in labs if flagged(x))
        r["n_sent"] = len(sents)
        r["n_unlab"] = sum(1 for x in labs if x is None)
        if (i + 1) % 6 == 0:
            cpath.write_text(json.dumps(cache))
            el = time.time() - t0
            print(f"  {i+1}/{len(rows)} {el:.0f}s "
                  f"~{el/(i+1)*(len(rows)-i-1):.0f}s left", flush=True)
    cpath.write_text(json.dumps(cache))
    (OUT / "scored.json").write_text(json.dumps(rows, ensure_ascii=False))
    print("judge complete")


def stage_measure() -> None:
    from gst.stats import wilson_ci
    rows = json.loads((OUT / "scored.json").read_text())
    confirm = json.loads((OUT / "confirm.json").read_text())
    ok = sum(1 for v in confirm.values() if v["remaining"] <= 1)
    print("=" * 72)
    print(f"P38.1 ablation: {ok}/9 cases at <=1 remaining qualification "
          f"sentence -> {'SUPPORTED' if ok >= 7 else 'FALSIFIED'}")
    for c, v in sorted(confirm.items()):
        print(f"    {c[:40]:<42} remaining={v['remaining']}  "
              f"sentences={v['sentences']}")
    confirmed = {c for c, v in confirm.items() if v["remaining"] == 0}
    print(f"  cases at EXACTLY zero: {len(confirmed)}")

    zero = [r for r in rows if r["arm"] == "zero" and r["case"] in confirmed]
    full = [r for r in rows if r["arm"] == "full"]
    print()
    print("=" * 72)
    if len(zero) >= 8:
        k = sum(1 for r in zero if r["n_qual"] > 0)
        ci = wilson_ci(k, len(zero))
        print(f"P38.2 invention at TRUE zero supply: {k}/{len(zero)} = "
              f"{k/len(zero):.3f} [{ci[0]:.3f},{ci[1]:.3f}] -> "
              f"{'SUPPORTED' if ci[0] > 0 else 'FALSIFIED'}")
        print(f"      mean qualification sentences emitted: "
              f"{sum(r['n_qual'] for r in zero)/len(zero):.2f}")
    else:
        print(f"P38.2 NOT EVALUABLE — {len(zero)} confirmed-zero runs")
    print()
    print("=" * 72)
    print("P38.3 silence check (mandatory reporting, no bar)")
    for name, arm in (("A-full", full), ("A-zero", zero or
                      [r for r in rows if r["arm"] == "zero"])):
        if not arm:
            continue
        print(f"  {name:<8} n={len(arm):<3} mean chars="
              f"{sum(len(r['output']) for r in arm)/len(arm):.0f}  "
              f"mean sentences={sum(r['n_sent'] for r in arm)/len(arm):.1f}  "
              f"mean qualification={sum(r['n_qual'] for r in arm)/len(arm):.2f}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "ablate"
    {"ablate": stage_ablate, "runs": stage_runs, "judge": stage_judge,
     "measure": stage_measure}[stage]()
