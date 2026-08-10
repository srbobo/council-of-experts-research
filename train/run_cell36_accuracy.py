"""Cell 36 — domain factual accuracy on the verifiable battery.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELLS 32-36 BLOCK" (Cell 36)
plus amendment #1 (routing dimension, >=50 items, attempt-rate reporting)
and amendment #2 (battery built; measures domain-FRAMED REASONING, not
recall).

Arms — one factor is the routing mechanism:
  A-council      matching domain specialist -> gpt-oss writer   (prompted routing)
  A-moe-single   gpt-oss:20b alone                              (learned routing, MoE)
  A-dense-single phi4:14b alone                                 (no expert routing)

The council arm is given the CORRECT specialist with no planner, which is
the most favourable construction available to it: a null therefore cannot
be blamed on routing error. Stated a fortiori, as elsewhere in this
program.

Scoring is exact match of a required "ANSWER:" line against per-item
accepted forms — a known-value check, not regex-as-NLP.

Run:  .venv/bin/python train/run_cell36_accuracy.py runs
      .venv/bin/python train/run_cell36_accuracy.py measure
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

from council.cabinet import CABINET                    # noqa: E402
from examples.verifiable_battery import BATTERY        # noqa: E402
from train.run_cell25_moa import chat                  # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell36"
RUNS = ROOT / "bench" / "runs" / "cell36_accuracy.jsonl"
MOE, DENSE = "gpt-oss:20b", "phi4:14b"
SEAT_TAG = {d: CABINET[d].ollama_tag for d in ("healthcare", "legal", "finance")}
REPEATS = 1

ASK = ("Answer the question. Show brief working if useful, then end your "
       "reply with a final line in exactly this form:\nANSWER: <value>")
SEAT_ASK = ("You are a {domain} specialist. Analyse the question below and "
            "state your answer with brief working.")
WRITER = ("You are the lead analyst. A specialist has provided the analysis "
          "below. Give the decision-maker the final answer.\n" + ASK)

_WS = re.compile(r"\s+")


def norm(t: str) -> str:
    t = (t or "").replace(",", "").replace("$", "").replace("–", "-")
    return _WS.sub(" ", t).strip().lower()


def answer_line(text: str) -> str | None:
    m = re.findall(r"ANSWER:\s*(.+)", text or "", re.I)
    return m[-1].strip() if m else None


def stage_runs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RUNS.exists():
        for line in RUNS.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    todo = [(it, arm, r) for it in BATTERY
            for arm in ("council", "moe-single", "dense-single")
            for r in range(REPEATS)
            if f"{it['id']}__{arm}__r{r}" not in done]
    print(f"cell36: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0 = time.time()
    with RUNS.open("a") as fh:
        for i, (it, arm, rep) in enumerate(todo):
            rid = f"{it['id']}__{arm}__r{rep}"
            seat_txt = None
            if arm == "council":
                seat_txt = chat(SEAT_TAG[it["domain"]],
                                SEAT_ASK.format(domain=it["domain"]), it["q"],
                                temperature=0.6, max_tokens=2048)
                if not seat_txt or not seat_txt.strip():
                    print(f"  EMPTY seat {rid}", flush=True)
                    continue
                txt = chat(MOE, WRITER,
                           f"--- SPECIALIST ANALYSIS ---\n{seat_txt}\n\n"
                           f"Question:\n{it['q']}",
                           temperature=0.6, max_tokens=2048)
            else:
                txt = chat(MOE if arm == "moe-single" else DENSE, ASK, it["q"],
                           temperature=0.6, max_tokens=2048)
            if not txt or not txt.strip():
                print(f"  EMPTY {rid} — failed, not scored", flush=True)
                continue
            fh.write(json.dumps({"run_id": rid, "item": it["id"],
                                 "domain": it["domain"], "arm": arm,
                                 "repeat": rep, "seat_text": seat_txt,
                                 "output": txt}, ensure_ascii=False) + "\n")
            fh.flush()
            if (i + 1) % 10 == 0:
                el = time.time() - t0
                print(f"  {i+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(i+1)*(len(todo)-i-1):.0f}s left", flush=True)
    print("cell36 runs complete")


def stage_measure() -> None:
    from gst.stats import wilson_ci
    import random
    rng = random.Random(0)
    by_id = {it["id"]: it for it in BATTERY}
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]

    scored = {}
    for r in rows:
        it = by_id[r["item"]]
        line = answer_line(r["output"])
        # attempt = the model produced the required ANSWER line at all
        attempted = line is not None
        hay = norm(line) if attempted else norm(r["output"])
        correct = any(norm(f) in hay for f in it["forms"])
        scored.setdefault(r["arm"], []).append(
            {"item": r["item"], "domain": r["domain"],
             "correct": correct, "attempted": attempted,
             "fallback": (not attempted) and correct})

    print("=" * 74)
    print("ACCURACY BY ARM  (attempt rate reported beside it, per amendment #1)")
    print("=" * 74)
    acc = {}
    for arm in ("council", "moe-single", "dense-single"):
        v = scored.get(arm, [])
        if not v:
            print(f"  {arm:<14} no runs")
            continue
        k = sum(1 for x in v if x["correct"])
        att = sum(1 for x in v if x["attempted"])
        fb = sum(1 for x in v if x["fallback"])
        ci = wilson_ci(k, len(v))
        acc[arm] = [1.0 if x["correct"] else 0.0 for x in v]
        print(f"  {arm:<14} {k}/{len(v)} = {k/len(v):.3f} "
              f"[{ci[0]:.3f},{ci[1]:.3f}]   attempt {att}/{len(v)} = "
              f"{att/len(v):.3f}   full-text fallbacks {fb}")

    print()
    for arm in ("council", "moe-single", "dense-single"):
        v = scored.get(arm, [])
        if not v:
            continue
        per = {}
        for x in v:
            per.setdefault(x["domain"], []).append(x["correct"])
        print(f"  {arm:<14} " + "  ".join(
            f"{d}={sum(b)}/{len(b)}" for d, b in sorted(per.items())))

    def paired(a, b):
        """Paired bootstrap over ITEMS on the correctness difference."""
        ia = {x["item"]: x["correct"] for x in scored.get(a, [])}
        ib = {x["item"]: x["correct"] for x in scored.get(b, [])}
        keys = sorted(set(ia) & set(ib))
        if len(keys) < 10:
            return None
        d = []
        for _ in range(5000):
            s = [keys[rng.randrange(len(keys))] for _ in keys]
            d.append(sum(ia[k] for k in s) / len(s) - sum(ib[k] for k in s) / len(s))
        d.sort()
        return d[125], d[4874], len(keys)

    print()
    print("=" * 74)
    r = paired("council", "moe-single")
    if r:
        lo, hi, n = r
        print(f"P36.1 council - MoE-single: diff CI [{lo:+.3f},{hi:+.3f}] "
              f"(n={n} paired items) -> "
              f"{'SUPPORTED' if lo > 0 else 'FALSIFIED (includes 0 or favours MoE)'}")
    r = paired("moe-single", "dense-single")
    if r:
        lo, hi, n = r
        print(f"P36.2 MoE-single - dense-single: diff CI [{lo:+.3f},{hi:+.3f}] "
              f"(n={n}) — CONFOUNDED (architecture AND identity AND training "
              f"data AND scale differ); suggestive of routing, never demonstrative")
    print()
    print("Reminder (amendment #2): this battery measures domain-FRAMED "
          "REASONING, not recall. A null licenses only 'no advantage applying "
          "domain conventions to stated premises'.")
    (OUT / "scored.json").write_text(json.dumps(scored, indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "runs"
    {"runs": stage_runs, "measure": stage_measure}[stage]()
