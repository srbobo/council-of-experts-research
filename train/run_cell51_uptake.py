"""Cell 51 — freight uptake: is appendix-carried content ever USED?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 51 PRE-REGISTRATION"
(commit 350578e, before item authoring). Items: docs/CELL51_ITEMS.json.

Four byte-controlled arms over the Cell 41 control artifacts (repeat 0):
bare / appendix-irrelevant / appendix-relevant / prose-relevant. A reader
answers a registered two-token decision question (PROCEED / HOLD).

Run:  .venv/bin/python train/run_cell51_uptake.py items
      .venv/bin/python train/run_cell51_uptake.py pilot
      .venv/bin/python train/run_cell51_uptake.py runs
      .venv/bin/python train/run_cell51_uptake.py measure
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

from train.run_cell25_moa import chat                          # noqa: E402
from train.run_cell47_redundancy import norm                   # noqa: E402
from train.run_cell49_arbitration import anchored_in           # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell51"
RUNS = ROOT / "bench" / "runs" / "cell51_uptake.jsonl"
C41_RUNS = ROOT / "bench" / "runs" / "cell41_phraseswap.jsonl"
ITEMS = json.loads((ROOT / "docs" / "CELL51_ITEMS.json").read_text())["items"]
READERS = ("gpt-oss:20b", "qwen2.5:7b-instruct")   # primary first (verdict)
ARMS = ("bare", "app-irr", "app-rel", "prose-rel")
REPEATS = 5
PILOT_REPS = 2
MAX_RESAMPLE = 6
TOKENS = ("PROCEED", "HOLD")

SYSTEM = ("You are a decision reviewer. Read the report the user provides "
          "and answer the decision question strictly on the basis of the "
          "report and anything attached to it. Reply with exactly one "
          "word: PROCEED or HOLD.")


def artifacts_by_case() -> dict[str, str]:
    rows = [json.loads(l) for l in C41_RUNS.read_text().splitlines()
            if l.strip()]
    return {r["case"]: r["output"] for r in rows
            if r["arm"] == "control" and r["repeat"] == 0}


def arm_text(base: str, arm: str, it: dict) -> str:
    if arm == "bare":
        return base
    if arm == "prose-rel":
        return base + "\n\n" + it["caveat"]
    cav = it["caveat"] if arm == "app-rel" else it["irrelevant"]
    return (base + "\n\n---\nASSUMPTIONS & CAVEATS (as stated by the "
            "specialist contributors)\n- " + cav)


def parse_answer(txt: str) -> str | None:
    words = {w.strip(".,;:!?()'\"*") for w in norm(txt or "").split()}
    hits = [t for t in TOKENS if t.lower() in words]
    return hits[0] if len(hits) == 1 else None


def stage_items() -> None:
    """Authoring guards -> frozen item list. Exclusion, never re-authoring."""
    from examples.test_cases import get_case
    OUT.mkdir(parents=True, exist_ok=True)
    arts = artifacts_by_case()
    frozen = []
    for it in ITEMS:
        base = norm(arts[it["case"]]) + " " + norm(get_case(it["case"]).prompt)
        qn = norm(it["question"])
        bad = []
        for p in it["probes"]:
            pn = norm(p)
            if anchored_in(pn, base):
                bad.append(f"probe '{p}' ambient in artifact/prompt")
            if anchored_in(pn, qn):
                bad.append(f"probe '{p}' present in question")
        if it["default"] not in TOKENS or it["flipped"] not in TOKENS \
                or it["default"] == it["flipped"]:
            bad.append("token fields invalid")
        if bad:
            print(f"  EXCLUDED item {it['id']} ({it['case']}): "
                  + "; ".join(bad))
            continue
        frozen.append(it)
    nb = sum(1 for i in frozen if i["direction"] == "blocking")
    ne = sum(1 for i in frozen if i["direction"] == "enabling")
    print(f"frozen: {len(frozen)} items ({nb} blocking / {ne} enabling)")
    if len(frozen) < 12 or nb < 5 or ne < 5:
        raise SystemExit("ITEM GUARDS FAILED — registered minimums not met")
    (OUT / "frozen.json").write_text(json.dumps(frozen, indent=1))
    print("frozen.json written")


def _read(reader: str, text: str, question: str) -> tuple[str | None, int]:
    for attempt in range(MAX_RESAMPLE):
        t = chat(reader, SYSTEM, text + "\n\nQUESTION: " + question,
                 temperature=0.8, max_tokens=2048)
        a = parse_answer(t or "")
        if a is not None:
            return a, attempt + 1
    return None, MAX_RESAMPLE


def _append(row: dict) -> None:
    with RUNS.open("a") as f:
        f.write(json.dumps(row) + "\n")


def _done() -> set[tuple]:
    if not RUNS.exists():
        return set()
    return {(r["reader"], r["item"], r["arm"], r["rep"])
            for r in map(json.loads, RUNS.read_text().splitlines())}


def _grid(frozen, reader_list, arms, reps) -> list[tuple]:
    return [(rd, it["id"], arm, rep) for rd in reader_list
            for it in frozen for arm in arms for rep in range(reps)]


def _run_jobs(jobs, frozen, arts) -> None:
    by = {it["id"]: it for it in frozen}
    done = _done()
    jobs = [j for j in jobs if j not in done]
    print(f"{len(jobs)} runs to do", flush=True)
    fails, t0 = 0, time.time()
    for i, (rd, iid, arm, rep) in enumerate(jobs):
        it = by[iid]
        text = arm_text(arts[it["case"]], arm, it)
        ans, tries = _read(rd, text, it["question"])
        if ans is None:
            fails += 1
            if fails >= 5:
                raise SystemExit("ABORT — 5 consecutive invalid reads")
        else:
            fails = 0
        _append({"reader": rd, "item": iid, "case": it["case"], "arm": arm,
                 "rep": rep, "answer": ans, "tries": tries})
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            print(f"  {i+1}/{len(jobs)} {el:.0f}s "
                  f"~{el/(i+1)*(len(jobs)-i-1)/60:.0f}m left", flush=True)


def stage_pilot() -> None:
    frozen = json.loads((OUT / "frozen.json").read_text())
    arts = artifacts_by_case()
    # preflight
    a, _ = _read(READERS[0], "REPORT: The sky is blue.",
                 "Is this report present? Reply with exactly one word: "
                 "PROCEED or HOLD.")
    if a is None:
        raise SystemExit("PREFLIGHT FAILED — primary reader not answering")
    print(f"preflight ok ({a})")
    _run_jobs(_grid(frozen, [READERS[0]], ("bare", "prose-rel"), PILOT_REPS),
              frozen, arts)
    # gates
    rows = [r for r in map(json.loads, RUNS.read_text().splitlines())
            if r["reader"] == READERS[0] and r["rep"] < PILOT_REPS]
    by = {it["id"]: it for it in frozen}
    keep, bare_flips, bare_n = [], 0, 0
    for it in frozen:
        b = [r["answer"] for r in rows
             if r["item"] == it["id"] and r["arm"] == "bare"]
        n_def = sum(1 for a in b if a == it["default"])
        bare_flips += sum(1 for a in b if a == it["flipped"])
        bare_n += len(b)
        if n_def * 2 > len(b):          # strict majority of pilot bare reps
            keep.append(it["id"])
        else:
            print(f"  G1 EXCLUDED item {it['id']}: bare pilot "
                  f"{n_def}/{len(b)} default")
    p_flips = sum(1 for r in rows
                  if r["arm"] == "prose-rel"
                  and r["answer"] == by[r["item"]]["flipped"])
    p_n = sum(1 for r in rows if r["arm"] == "prose-rel")
    pooled_bare_flip = bare_flips / bare_n if bare_n else 1.0
    potency = p_flips / p_n if p_n else 0.0
    print(f"G1 pooled bare flip: {pooled_bare_flip:.3f} (require <= 0.2)")
    print(f"G2 prose potency:    {potency:.3f} (require >= 0.6)")
    print(f"G1 per-item survivors: {len(keep)}/{len(frozen)} (require >= 10)")
    verdict = (pooled_bare_flip <= 0.2 and potency >= 0.6 and len(keep) >= 10)
    (OUT / "pilot_gate.json").write_text(json.dumps(
        {"keep": keep, "pooled_bare_flip": pooled_bare_flip,
         "potency": potency, "pass": verdict}))
    print("PILOT GATES: " + ("PASS" if verdict else
                             "FAIL — cell halts for redesign"))


def stage_runs() -> None:
    frozen = json.loads((OUT / "frozen.json").read_text())
    gate = json.loads((OUT / "pilot_gate.json").read_text())
    if not gate["pass"]:
        raise SystemExit("pilot gate FAIL recorded — runs not permitted")
    frozen = [it for it in frozen if it["id"] in set(gate["keep"])]
    arts = artifacts_by_case()
    _run_jobs(_grid(frozen, list(READERS), ARMS, REPEATS), frozen, arts)
    print("cell51 runs complete")


def stage_measure() -> None:
    frozen = json.loads((OUT / "frozen.json").read_text())
    gate = json.loads((OUT / "pilot_gate.json").read_text())
    items = [it for it in frozen if it["id"] in set(gate["keep"])]
    by = {it["id"]: it for it in items}
    rows = [r for r in map(json.loads, RUNS.read_text().splitlines())
            if r["item"] in by]
    inv = sum(1 for r in rows if r["answer"] is None)
    print(f"runs: {len(rows)}  invalid: {inv}")

    def shares(reader):
        out = {}
        for it in items:
            per = {}
            for arm in ARMS:
                a = [r["answer"] for r in rows
                     if r["reader"] == reader and r["item"] == it["id"]
                     and r["arm"] == arm and r["answer"] is not None]
                per[arm] = (sum(1 for x in a if x == it["flipped"]) / len(a)
                            if a else None)
            out[it["id"]] = per
        return out

    for reader in READERS:
        sh = shares(reader)
        print(f"\n=== RAW TABLE — reader {reader} (flip share per arm) ===")
        print(f"{'item':>4} {'dir':>9} | " + " ".join(f"{a:>9}" for a in ARMS))
        for iid, per in sorted(sh.items()):
            cells = " ".join(
                f"{per[a]:.2f}".rjust(9) if per[a] is not None
                else "-".rjust(9) for a in ARMS)
            print(f"{iid:>4} {by[iid]['direction']:>9} | {cells}")
        pooled = {a: [per[a] for per in sh.values() if per[a] is not None]
                  for a in ARMS}
        print("mean      | " + " ".join(
            f"{sum(v)/len(v):.3f}".rjust(9) if v else "-".rjust(9)
            for v in (pooled[a] for a in ARMS)))

    # P51.1 + P51.2 on primary reader, cluster bootstrap over items
    sh = shares(READERS[0])
    ids = [i for i in sh if all(sh[i][a] is not None for a in ARMS)]
    rng = random.Random(51)

    def boot(diff_fn, draws=5000):
        pts = [diff_fn(sh[i]) for i in ids]
        est = sum(pts) / len(pts)
        bs = []
        for _ in range(draws):
            s = [pts[rng.randrange(len(pts))] for _ in pts]
            bs.append(sum(s) / len(s))
        bs.sort()
        return est, bs[int(0.025 * draws)], bs[int(0.975 * draws)]

    e1, lo1, hi1 = boot(lambda p: p["app-rel"] - p["app-irr"])
    e2, lo2, hi2 = boot(lambda p: p["prose-rel"] - p["app-rel"])
    print(f"\nP51.1 uptake (app-rel - app-irr): {e1:+.3f} "
          f"[{lo1:+.3f}, {hi1:+.3f}]  k={len(ids)} items")
    print("P51.1: " + ("SUPPORTED — appendix content moves decisions"
                       if lo1 > 0 else
                       "FALSIFIED — no uptake beyond appendix presence"))
    print(f"P51.2 channel (prose-rel - app-rel): {e2:+.3f} "
          f"[{lo2:+.3f}, {hi2:+.3f}]")
    if lo2 > 0.25:
        print("P51.2: appendix channel MATERIALLY WEAKER than in-prose")
    elif hi2 < 0.25 and abs(e2) < 0.125:
        print("P51.2: parity at power")
    else:
        print("P51.2: not evaluable at power")
    bare = [sh[i]["bare"] for i in ids]
    irr = [sh[i]["app-irr"] for i in ids]
    print(f"\ndescriptive: bare floor {sum(bare)/len(bare):.3f}; "
          f"caution-priming delta (app-irr - bare) "
          f"{sum(irr)/len(irr) - sum(bare)/len(bare):+.3f}")


if __name__ == "__main__":
    {"items": stage_items, "pilot": stage_pilot,
     "runs": stage_runs, "measure": stage_measure}[sys.argv[1]]()
