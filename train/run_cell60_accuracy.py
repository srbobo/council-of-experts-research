"""Cell 60 — the harder accuracy battery.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 60 PRE-REGISTRATION"
(commit 6d32991); items frozen after guards (ebfc001).

Run:  .venv/bin/python train/run_cell60_accuracy.py pilot
      .venv/bin/python train/run_cell60_accuracy.py runs
      .venv/bin/python train/run_cell60_accuracy.py measure
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
from train.run_cell30_descaffold import SEATS, WRITER_PROMPT   # noqa: E402
from train.run_cell44_reconsult import S1_PROMPT               # noqa: E402
from train.run_cell57_planner import PLANNER_PROMPT as IDENTIFY  # noqa: E402
from train.run_cell59_subquestions import parse_plan           # noqa: E402
from train.run_integration_demo import (FOLLOWUP, ROSTER,      # noqa: E402
                                        SUBQ_PROMPT, _THINK)
from gst.gates import FABRICATION_BLOCKLIST, blocklist_gate, fold  # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell60"
RUNS = ROOT / "bench" / "runs" / "cell60_accuracy.jsonl"
ITEMS = json.loads((ROOT / "docs" / "CELL60_ITEMS.json").read_text())["items"]
MODEL = "gpt-oss:20b"
ROLES = ("healthcare", "legal", "finance")
DIRECT_REPS, COUNCIL_REPS, PILOT_REPS = 6, 3, 6
SCREEN_LO, SCREEN_HI = 1, 5          # of 6 pilot reps, inclusive band

DIRECT_PROMPT = ("You are an analyst answering a quantitative question "
                 "for a decision-maker. Be careful and exact.")
S2_ANSWER = ("You are the lead analyst. Below are the specialist "
             "contributions, the tension list you already wrote, and any "
             "follow-up clarification you requested. Answer the "
             "decision-maker's question exactly. Work step by step, then "
             "end your reply with a final line of exactly:\n"
             "ANSWER: <number>")


def gen(system, user, temp=0.6, toks=8192, model=MODEL):
    for attempt in range(6):
        if attempt:
            time.sleep(10 * attempt)
        t = chat(model, system, user, temperature=temp, max_tokens=toks)
        if t and t.strip():
            return _THINK.sub("", t).strip()
    raise SystemExit("generation failed 6x")


def parse_answer(txt: str):
    for line in reversed((txt or "").splitlines()):
        s = line.strip().lstrip("*# ")
        if s.upper().startswith("ANSWER"):
            tail = fold(s.split(":", 1)[1] if ":" in s else s[6:])
            num = ""
            for ch in tail:
                if ch.isdigit() or ch in ".-":
                    num += ch
                elif num:
                    break
            try:
                return float(num)
            except ValueError:
                return None
    return None


def correct(val, answer) -> bool:
    if val is None:
        return False
    a = float(answer)
    return abs(val - a) <= max(0.005 * abs(a), 0.01)


def council_run(it):
    q = it["prompt"]
    ids = gen(IDENTIFY, f"Question:\n{q}", toks=2048, temp=0.7)
    quants = [l.strip() for l in ids.splitlines() if l.strip()][:6]
    plan = None
    for _ in range(3):
        plan = parse_plan(gen("Follow the output format exactly.",
                              SUBQ_PROMPT.format(quantities="\n".join(quants))
                              + f"\n\nQuestion:\n{q}", toks=2048, temp=0.7))
        if plan:
            break
    if not plan:
        return None, "plan-parse"
    contribs = {}
    for role in ROLES:
        a, b = tuple(r for r in ROLES if r != role)
        contribs[role] = gen(SEATS[role],
                             f"Case:\n{q}\n\nYour sub-question:\n"
                             f"{plan[role]}\n\n" + ROSTER.format(a=a, b=b),
                             toks=4096, temp=0.7)
    pile = "\n\n".join(
        f"--- {r.upper()} SPECIALIST CONTRIBUTION ---\n{contribs[r]}"
        for r in ROLES)
    s1 = gen(S1_PROMPT, f"{pile}\n\nQuestion:\n{q}", toks=2048)
    route, tension = None, None
    for line in (l.strip() for l in s1.splitlines() if l.strip()):
        for r in ROLES:
            if r in line.lower():
                route, tension = r, line
                break
        if route:
            break
    reply_block = ""
    if route:
        reply = gen(SEATS[route],
                    f"Case:\n{q}\n\nYour earlier contribution:\n"
                    f"{contribs[route]}\n\n"
                    + FOLLOWUP.format(tension=tension), toks=2048, temp=0.7)
        if not blocklist_gate(reply, FABRICATION_BLOCKLIST):
            reply_block = (f"--- FOLLOW-UP CLARIFICATION (from the {route} "
                           f"specialist) ---\n{reply}\n\n")
    s2 = gen(S2_ANSWER,
             f"{pile}\n\n--- YOUR TENSION LIST ---\n{s1}\n\n{reply_block}"
             f"Question:\n{q}")
    return s2, route


def _done():
    if not RUNS.exists():
        return set()
    return {r["run_id"] for r in map(json.loads,
                                     RUNS.read_text().splitlines())}


def _run_grid(jobs, label):
    done = _done()
    jobs = [j for j in jobs if j[0] not in done]
    print(f"cell60 {label}: {len(jobs)} runs to go", flush=True)
    t0 = time.time()
    with RUNS.open("a") as fh:
        for k, (rid, it, arm, rep) in enumerate(jobs):
            if arm == "direct":
                txt = gen(DIRECT_PROMPT, it["prompt"])
                route = None
            else:
                txt, route = council_run(it)
                if txt is None:
                    fh.write(json.dumps({"run_id": rid, "item": it["id"],
                                         "arm": arm, "rep": rep,
                                         "invalid": route}) + "\n")
                    fh.flush()
                    continue
            val = parse_answer(txt)
            fh.write(json.dumps(
                {"run_id": rid, "item": it["id"], "arm": arm, "rep": rep,
                 "val": val, "ok": correct(val, it["answer"]),
                 "route": route, "chars": len(txt),
                 "tail": txt[-400:]}, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 10 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(jobs)} {el:.0f}s "
                      f"~{el/(k+1)*(len(jobs)-k-1)/60:.0f}m left",
                      flush=True)
    print(f"cell60 {label} complete")


def stage_pilot():
    OUT.mkdir(parents=True, exist_ok=True)
    t = chat(MODEL, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED")
    jobs = [(f"{it['id']}__direct__r{r}", it, "direct", r)
            for it in ITEMS for r in range(PILOT_REPS)]
    _run_grid(jobs, "pilot(direct)")
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()]
    keep, table = [], []
    for it in ITEMS:
        v = [r for r in rows if r["item"] == it["id"]
             and r["arm"] == "direct" and r["rep"] < PILOT_REPS]
        k = sum(1 for r in v if r.get("ok"))
        table.append((it["id"], k, len(v)))
        if SCREEN_LO <= k <= SCREEN_HI:
            keep.append(it["id"])
    print(f"{'item':<8}{'direct':>8}")
    for iid, k, n in table:
        mark = " KEEP" if iid in keep else ""
        print(f"{iid:<8}{k}/{n:>4}{mark}")
    ok = len(keep) >= 20
    (OUT / "screen.json").write_text(json.dumps(
        {"keep": keep, "pass": ok}))
    print(f"DIFFICULTY SCREEN: {len(keep)}/36 in band -> "
          f"{'PASS' if ok else 'FAIL — re-author harder'}")


def stage_runs():
    scr = json.loads((OUT / "screen.json").read_text())
    if not scr["pass"]:
        raise SystemExit("screen FAIL recorded — runs not permitted")
    keep = [it for it in ITEMS if it["id"] in set(scr["keep"])]
    jobs = [(f"{it['id']}__council__r{r}", it, "council", r)
            for it in keep for r in range(COUNCIL_REPS)]
    _run_grid(jobs, "runs(council)")


def stage_measure():
    import random
    rng = random.Random(60)
    scr = json.loads((OUT / "screen.json").read_text())
    keep = set(scr["keep"])
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()
            if l.strip()]
    inv = [r for r in rows if "invalid" in r]
    rows = [r for r in rows if "invalid" not in r and r["item"] in keep]
    per = {}
    for iid in sorted(keep):
        d = [r for r in rows if r["item"] == iid and r["arm"] == "direct"]
        c = [r for r in rows if r["item"] == iid and r["arm"] == "council"]
        per[iid] = (sum(r["ok"] for r in d) / max(len(d), 1),
                    sum(r["ok"] for r in c) / max(len(c), 1))
    print("=" * 70)
    print("CELL 60 RAW TABLE (mandatory, before any verdict)")
    print(f"  screened items {len(keep)}  invalid council runs {len(inv)}")
    print(f"{'item':<8}{'direct':>8}{'council':>9}{'diff':>8}")
    for iid, (d, c) in sorted(per.items()):
        print(f"{iid:<8}{d:>8.2f}{c:>9.2f}{c-d:>+8.2f}")
    dm = sum(d for d, _ in per.values()) / len(per)
    cm = sum(c for _, c in per.values()) / len(per)
    diffs = [c - d for d, c in per.values()]
    bs = []
    for _ in range(5000):
        s = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        bs.append(sum(s) / len(s))
    bs.sort()
    lo, hi = bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]
    est = sum(diffs) / len(diffs)
    print(f"\narm means: direct {dm:.3f}  council {cm:.3f}")
    print(f"P60.1 council - direct: {est:+.3f} [{lo:+.3f}, {hi:+.3f}]  "
          f"({len(per)} item clusters)")
    # MDD simulation at the realized item count (registered)
    import statistics as st
    sd = st.stdev(diffs) if len(diffs) > 1 else 0.3
    def power(delta, draws=400):
        hit = 0
        for _ in range(draws):
            sim = [delta + rng.gauss(0, sd) for _ in diffs]
            b2 = []
            for _ in range(400):
                s = [sim[rng.randrange(len(sim))] for _ in sim]
                b2.append(sum(s) / len(s))
            b2.sort()
            if b2[int(.025 * 400)] > 0:
                hit += 1
        return hit / draws
    mdd = None
    for dlt in (0.06, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25):
        if power(dlt) >= 0.8:
            mdd = dlt
            break
    print(f"registered MDD at realized k: ~{mdd}")
    if lo > 0:
        print("P60.1: ADVANTAGE — the no-advantage row is rewritten")
    elif hi < 0:
        print("P60.1: HARM — the council costs accuracy on this class")
    elif mdd is not None and (hi - lo) / 2 <= mdd:
        print("P60.1: INFORMATIVE NULL at the registered MDD")
    else:
        print("P60.1: NOT EVALUABLE at power")
    disc = sum(1 for d, c in per.values() if abs(c - d) > 1e-9)
    print(f"descriptive: discordant items {disc}/{len(per)} "
          f"(the Cell 36 diagnostic)")
    for tpl in sorted({i["template"] for i in ITEMS}):
        ids = [i["id"] for i in ITEMS if i["template"] == tpl
               and i["id"] in keep]
        if ids:
            d = sum(per[i][0] for i in ids) / len(ids)
            c = sum(per[i][1] for i in ids) / len(ids)
            print(f"  template {tpl}: direct {d:.2f} council {c:.2f} "
                  f"(n={len(ids)})")


if __name__ == "__main__":
    {"pilot": stage_pilot, "runs": stage_runs,
     "measure": stage_measure}[sys.argv[1]]()
