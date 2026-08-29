"""Cell 57 — planner competence: can the orchestrator find the
load-bearing quantities?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 57 PRE-REGISTRATION"
(commit e690dd9, before label authoring). Labels: docs/CELL57_LABELS.json
(frozen after guards, before any elicitation).

Run:  .venv/bin/python train/run_cell57_planner.py guards
      .venv/bin/python train/run_cell57_planner.py runs
      .venv/bin/python train/run_cell57_planner.py score
      .venv/bin/python train/run_cell57_planner.py measure   (needs
        docs/CELL57_CONFIRM.json, the committed manual confirmations)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                          # noqa: E402
from train.run_cell47_redundancy import norm                   # noqa: E402
from train.run_cell49_arbitration import anchored_in           # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell57"
RUNS = ROOT / "bench" / "runs" / "cell57_planner.jsonl"
SEATS_PATH = ROOT / "bench" / "analysis" / "cell41" / "seats.json"
LABELS = json.loads((ROOT / "docs" / "CELL57_LABELS.json").read_text())["labels"]
PLANNER = "gpt-oss:20b"
ARMS = ("pre-seat", "post-seat")
REPEATS = 5
ROLES = ("healthcare", "legal", "finance")

PLANNER_PROMPT = (
    "You are the orchestrator of a specialist panel (a healthcare analyst, "
    "a legal analyst, and a financial analyst) answering the question "
    "below. Before dispatching sub-questions, list the 3-6 LOAD-BEARING "
    "QUANTITIES: the specific numbers, rates, prices, sizes, deadlines, or "
    "thresholds -- whether stated in the material or missing from it -- on "
    "which the final recommendation will turn. Output only the numbered "
    "list, one short line per quantity.")


def build_user(case: str, arm: str) -> str:
    from examples.test_cases import get_case
    u = f"Question:\n{get_case(case).prompt}"
    if arm == "post-seat":
        seats = json.loads(SEATS_PATH.read_text())[case]
        for r in ROLES:
            u += (f"\n\n--- {r.upper()} SPECIALIST CONTRIBUTION ---\n"
                  + seats.get(r, "").rstrip())
    return u


def stage_guards() -> None:
    from examples.test_cases import get_case
    from gst.registry import gate_GE, load_frozen
    problems = []
    pn = norm(PLANNER_PROMPT)
    for entry in LABELS:
        cp = norm(get_case(entry["case"]).prompt)
        for q in entry["quantities"]:
            hit = any(anchored_in(norm(p), cp) for p in q["probes"])
            if not hit:
                problems.append(f"{q['id']}: no probe vocabulary in its "
                                f"case prompt")
            for p in q["probes"]:
                if norm(p) in pn:
                    problems.append(f"{q['id']}: probe {p!r} appears in the "
                                    f"planner prompt")
    viol = gate_GE({"PLANNER": PLANNER_PROMPT},
                   load_frozen(ROOT / "docs" / "DICTATION_REGISTRY.json"),
                   construct_only=True)
    problems += ["G-E: " + v for v in viol]
    if problems:
        for p in problems:
            print("  " + p)
        raise SystemExit("LABEL GUARDS FAILED")
    n = sum(len(e["quantities"]) for e in LABELS)
    print(f"label guards: PASS ({len(LABELS)} cases, {n} labels); "
          f"gate G-E PASS")


def stage_runs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RUNS.exists():
        done = {json.loads(l)["run_id"]
                for l in RUNS.read_text().splitlines() if l.strip()}
    t = chat(PLANNER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED")
    todo = [(e["case"], a, r) for e in LABELS for a in ARMS
            for r in range(REPEATS)
            if f"{e['case']}__{a}__r{r}" not in done]
    print(f"cell57: {len(todo)} elicitations to go", flush=True)
    t0, fails = time.time(), 0
    with RUNS.open("a") as fh:
        for k, (case, a, r) in enumerate(todo):
            txt = chat(PLANNER, PLANNER_PROMPT, build_user(case, a),
                       temperature=0.7, max_tokens=2048)
            if not txt or not txt.strip():
                fails += 1
                if fails >= 5:
                    raise SystemExit("ABORTING — resumable.")
                continue
            fails = 0
            fh.write(json.dumps(
                {"run_id": f"{case}__{a}__r{r}", "case": case, "arm": a,
                 "rep": r, "list": txt.strip()}, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 10 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1)/60:.0f}m left", flush=True)
    print("cell57 runs complete")


def lines_of(txt: str) -> list[str]:
    return [l.strip() for l in txt.splitlines() if l.strip()]


def stage_score() -> None:
    """Mechanical prefilter -> match table for committed confirmation."""
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()
            if l.strip()]
    matches = []
    for r in rows:
        entry = next(e for e in LABELS if e["case"] == r["case"])
        for line in lines_of(r["list"]):
            ln = norm(line)
            for q in entry["quantities"]:
                if any(anchored_in(norm(p), ln) for p in q["probes"]):
                    matches.append({"run_id": r["run_id"], "label": q["id"],
                                    "line": line})
    (OUT / "matches.json").write_text(json.dumps(matches, indent=1,
                                                 ensure_ascii=False))
    uniq = sorted({(m["label"], m["line"]) for m in matches})
    print(f"match instances: {len(matches)}; unique (label,line) pairs: "
          f"{len(uniq)}")
    print("Write docs/CELL57_CONFIRM.json: {\"pairs\": {\"<label>||<line>\""
          ": true/false, ...}} for every unique pair, then run measure.")
    (OUT / "unique_pairs.json").write_text(json.dumps(
        [{"label": a, "line": b} for a, b in uniq], indent=1,
        ensure_ascii=False))


def stage_measure() -> None:
    import random
    rng = random.Random(57)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()
            if l.strip()]
    matches = json.loads((OUT / "matches.json").read_text())
    conf = json.loads((ROOT / "docs" /
                       "CELL57_CONFIRM.json").read_text())["pairs"]
    missing = {f"{m['label']}||{m['line']}" for m in matches} - set(conf)
    if missing:
        raise SystemExit(f"{len(missing)} unconfirmed pairs — finish "
                         f"docs/CELL57_CONFIRM.json")
    ok = {(m["run_id"], m["label"]) for m in matches
          if conf[f"{m['label']}||{m['line']}"]}

    def recall(rowset, entry_for):
        """per-label recall over reps -> dict label -> share"""
        out = {}
        for r in rowset:
            for q in entry_for(r)["quantities"]:
                out.setdefault(q["id"], []).append(
                    (r["run_id"], q["id"]) in ok)
        return {k: sum(v) / len(v) for k, v in out.items()}

    ent = {e["case"]: e for e in LABELS}
    print("=" * 76)
    print("CELL 57 RAW TABLE (mandatory, before any verdict)")
    per_arm = {}
    for a in ARMS:
        sub = [r for r in rows if r["arm"] == a]
        rec = recall(sub, lambda r: ent[r["case"]])
        per_arm[a] = rec
    print(f"{'label':<16}{'class':>8}{'pre-seat':>10}{'post-seat':>11}")
    for e in LABELS:
        for q in e["quantities"]:
            print(f"{q['id']:<16}{q['class']:>8}"
                  f"{per_arm['pre-seat'].get(q['id'], 0):>10.2f}"
                  f"{per_arm['post-seat'].get(q['id'], 0):>11.2f}")
    # cross (mismatched) recall: label probes vs OTHER cases' lists
    def cross(a):
        hits, n = 0, 0
        for e in LABELS:
            for q in e["quantities"]:
                for r in rows:
                    if r["arm"] != a or r["case"] == e["case"]:
                        continue
                    n += 1
                    if any(any(anchored_in(norm(p), norm(l))
                               for p in q["probes"])
                           for l in lines_of(r["list"])):
                        hits += 1
        return hits / n
    # NOTE: cross-recall is prefilter-only by design (no manual pass over
    # mismatched pairs); this is CONSERVATIVE for P57.1 since the matched
    # side is confirmation-filtered and the mismatched side is not.

    def by_case_mean(a):
        d = {}
        for e in LABELS:
            vals = [per_arm[a][q["id"]] for q in e["quantities"]]
            d[e["case"]] = sum(vals) / len(vals)
        return d

    for a in ARMS:
        bc = by_case_mean(a)
        pooled = sum(bc.values()) / len(bc)
        xr = cross(a)
        cases = list(bc)
        bs = []
        for _ in range(5000):
            s = [bc[cases[rng.randrange(len(cases))]] for _ in cases]
            bs.append(sum(s) / len(s))
        bs.sort()
        lo, hi = bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]
        print(f"\narm {a}: confirmed recall {pooled:.3f} [{lo:.3f}, "
              f"{hi:.3f}]  (12 case clusters)   mismatched cross-recall "
              f"{xr:.3f} (prefilter-only, conservative)")
        band = ("STRONG (>=0.7): the planner component is buildable as "
                "specified" if pooled >= 0.7 else
                "PARTIAL (0.4-0.7): redundancy protection is bounded by "
                "planner coverage" if pooled >= 0.4 else
                "WEAK (<0.4): the component underdelivers §3")
        print(f"  P57.2 band ({a}): {band}")
        print(f"  P57.1 ({a}): " + (
            "SUPPORTED — matched exceeds mismatched"
            if lo > xr else "NOT SUPPORTED — instrument cannot see "
            "planner competence; P57.2 NOT EVALUABLE"))
    d = {c: by_case_mean("post-seat")[c] - by_case_mean("pre-seat")[c]
         for c in by_case_mean("pre-seat")}
    vals = list(d.values())
    bs = []
    for _ in range(5000):
        s = [vals[rng.randrange(len(vals))] for _ in vals]
        bs.append(sum(s) / len(s))
    bs.sort()
    print(f"\nP57.3 post-seat - pre-seat: "
          f"{sum(vals)/len(vals):+.3f} [{bs[125]:+.3f}, {bs[4875]:+.3f}]")
    for cls in ("stated", "unknown"):
        for a in ARMS:
            v = [per_arm[a][q["id"]] for e in LABELS
                 for q in e["quantities"] if q["class"] == cls]
            print(f"descriptive {cls:>8} recall ({a}): "
                  f"{sum(v)/len(v):.3f} (n={len(v)} labels)")


if __name__ == "__main__":
    {"guards": stage_guards, "runs": stage_runs,
     "score": stage_score, "measure": stage_measure}[sys.argv[1]]()
