"""Cell 56 — bounding live-reply fabrication; testing the backfill mechanism.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 56 PRE-REGISTRATION"
(commit 64c6206, before any run). Items/machinery: Cells 53/54, frozen.

Arms: briefed (private notes with the deciding fact, Cell 54 verbatim)
vs unbriefed (identical minus the notes). Replies only; no S2.

Run:  .venv/bin/python train/run_cell56_fabrication.py runs
      .venv/bin/python train/run_cell56_fabrication.py extract
      .venv/bin/python train/run_cell56_fabrication.py measure
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
from train.run_cell30_descaffold import SEATS                  # noqa: E402
from train.run_cell53_live_followup import ITEMS               # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell56"
RUNS = ROOT / "bench" / "runs" / "cell56_fabrication.jsonl"
SEATS_PATH = ROOT / "bench" / "analysis" / "cell41" / "seats.json"
WRITER = "gpt-oss:20b"
ARMS = ("briefed", "unbriefed")
REPEATS = 10
NOTES = "Your private working notes (not shared with the panel):"


def reply_user(it, arm: str) -> str:
    from examples.test_cases import get_case
    seats = json.loads(SEATS_PATH.read_text())[it["case"]]
    u = (f"Question under analysis:\n{get_case(it['case']).prompt}\n\n"
         f"Your earlier contribution:\n{seats[it['seat_B']].rstrip()}"
         f"\n\n{it['pos_B']}\n\n")
    if arm == "briefed":
        u += f"{NOTES}\n{it['fact_R1']}\n\n"
    return u + it["followup_q"]


def stage_runs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RUNS.exists():
        done = {json.loads(l)["run_id"]
                for l in RUNS.read_text().splitlines() if l.strip()}
    t = chat(WRITER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED")
    todo = [(it, a, r) for it in ITEMS for a in ARMS for r in range(REPEATS)
            if f"i{it['id']}__{a}__r{r}" not in done]
    print(f"cell56: {len(todo)} replies to go", flush=True)
    t0, fails = time.time(), 0
    with RUNS.open("a") as fh:
        for k, (it, a, r) in enumerate(todo):
            txt = chat(WRITER, SEATS[it["seat_B"]], reply_user(it, a),
                       temperature=0.7, max_tokens=2048)
            if not txt or not txt.strip():
                fails += 1
                if fails >= 5:
                    raise SystemExit("ABORTING — resumable.")
                continue
            fails = 0
            fh.write(json.dumps(
                {"run_id": f"i{it['id']}__{a}__r{r}", "item": it["id"],
                 "domain": it["route_domain"], "arm": a, "rep": r,
                 "reply": txt.strip()}, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 10 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1)/60:.0f}m left", flush=True)
    print("cell56 runs complete")


def spans(text: str) -> list[str]:
    """Frozen prefilter, validated on the C54 archive (recall 4/4)."""
    out = []
    for pat in (" v. ", " vs. ", " v "):
        start = 0
        while True:
            i = text.find(pat, start)
            if i < 0:
                break
            pre = text[max(0, i - 40):i].split()
            post = text[i + len(pat):i + 40].split()
            if pre and post:
                a = pre[-1].strip("*_(),.;:'\"").lstrip("*_(")
                b = post[0].strip("*_(),.;:'\"").rstrip("*_)")
                if a[:1].isupper() and b[:1].isupper() \
                        and a.isalpha() and b.isalpha():
                    out.append(f"{a} {pat.strip()} {b}")
            start = i + 1
    return out


def stage_extract() -> None:
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()
            if l.strip()]
    table = {}
    for r in rows:
        s = spans(r["reply"])
        if s:
            table[r["run_id"]] = sorted(set(s))
    (OUT / "extracted.json").write_text(json.dumps(table, indent=1))
    uniq = sorted({s for v in table.values() for s in v})
    print(f"replies with spans: {len(table)}/{len(rows)}")
    print(f"unique spans ({len(uniq)}):")
    for s in uniq:
        n = sum(s in v for v in table.values())
        print(f"  {s}   (in {n} replies)")
    print("\nWrite docs/CELL56_CLASSIFICATION.json mapping each unique "
          "span to REAL / FABRICATED / UNVERIFIABLE / NOT-A-CITATION "
          "with a one-line justification, then run measure.")


def stage_measure() -> None:
    import random
    rng = random.Random(56)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()
            if l.strip()]
    table = json.loads((OUT / "extracted.json").read_text())
    cls = json.loads((ROOT / "docs" /
                      "CELL56_CLASSIFICATION.json").read_text())["spans"]
    missing = sorted({s for v in table.values() for s in v} - set(cls))
    if missing:
        raise SystemExit(f"unclassified spans: {missing}")

    def fab(rid, include_unver=False):
        okc = {"FABRICATED"} | ({"UNVERIFIABLE"} if include_unver else set())
        return any(cls[s]["class"] in okc for s in table.get(rid, []))

    print("=" * 74)
    print("CELL 56 RAW TABLE (mandatory, before any verdict)")
    from gst.stats import wilson_ci
    for inc, lbl in ((False, "primary (FABRICATED only)"),
                     (True, "sensitivity (+UNVERIFIABLE)")):
        print(f"\n--- {lbl} ---")
        print(f"{'arm':<11}{'fabricating':>12}{'rate':>7}{'wilson 95%':>18}")
        for a in ARMS:
            v = [r for r in rows if r["arm"] == a]
            k = sum(1 for r in v if fab(r["run_id"], inc))
            lo, hi = wilson_ci(k, len(v))
            print(f"{a:<11}{k}/{len(v):>7}{k/len(v):>7.3f}"
                  f"   [{lo:.3f}, {hi:.3f}]")
    print(f"\n{'item':>4} {'domain':>10} | briefed  unbriefed")
    per = {}
    for it_id in sorted({r['item'] for r in rows}):
        d = {}
        for a in ARMS:
            v = [r for r in rows if r["item"] == it_id and r["arm"] == a]
            d[a] = sum(1 for r in v if fab(r["run_id"])) / max(len(v), 1)
        per[it_id] = d
        dom = next(r["domain"] for r in rows if r["item"] == it_id)
        print(f"{it_id:>4} {dom:>10} |   {d['briefed']:.2f}      "
              f"{d['unbriefed']:.2f}")
    for dom in ("healthcare", "legal", "finance"):
        v = [r for r in rows if r["domain"] == dom]
        if v:
            k = sum(1 for r in v if fab(r["run_id"]))
            print(f"domain {dom}: {k}/{len(v)} = {k/len(v):.3f}")

    diffs = [per[i]["unbriefed"] - per[i]["briefed"] for i in per]
    bs = []
    for _ in range(5000):
        s = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        bs.append(sum(s) / len(s))
    bs.sort()
    est = sum(diffs) / len(diffs)
    lo, hi = bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]
    print(f"\nP56.2 backfill (unbriefed - briefed): {est:+.3f} "
          f"[{lo:+.3f}, {hi:+.3f}]  clusters={len(diffs)}")
    if lo > 0:
        print("P56.2: SUPPORTED — fabrication is backfill; the content "
              "channel is itself a fabrication control")
    elif hi < 0:
        print("P56.2: FALSIFIED (reversed) — fabrication is a style of "
              "answering, not gap-filling")
    else:
        print("P56.2: NOT EVALUABLE at power" if est > 0 else
              "P56.2: FALSIFIED — no excess under pressure")


if __name__ == "__main__":
    {"runs": stage_runs, "extract": stage_extract,
     "measure": stage_measure}[sys.argv[1]]()
