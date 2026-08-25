"""Cell 54 — the private briefing: live seat conveys held-but-unwritten fact.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 54 PRE-REGISTRATION"
(commit 81831ba). Round-1 is byte-identical to Cell 44; the fact reaches
the live seat only as private working notes at reply time. Archived Cell
44 control/informed arms are the registered comparators; a fresh
mini-control (never pooled) guards the batch confound.

Run:  .venv/bin/python train/run_cell54_briefed_followup.py pilot
      .venv/bin/python train/run_cell54_briefed_followup.py runs
      .venv/bin/python train/run_cell54_briefed_followup.py judge
      .venv/bin/python train/run_cell54_briefed_followup.py measure
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
from train.run_cell44_reconsult import (JUDGE_PROMPT, S1_PROMPT,  # noqa: E402
                                        S2_PROMPT, build_contribs,
                                        parse_adopt, tension_named)
from train.run_cell53_live_followup import ITEMS, has_fact     # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell54"
RUNS = ROOT / "bench" / "runs" / "cell54_briefed.jsonl"
C44_RUNS = ROOT / "bench" / "runs" / "cell44_reconsult.jsonl"
C44_JUDG = ROOT / "bench" / "analysis" / "cell44" / "judgments.json"
WRITER = "gpt-oss:20b"
JUDGES = ["gpt-oss:20b", "qwen3-vl:30b-a3b-instruct"]
REPEATS = 6
MINI_REPS = 2
PROD_GATE, NAME_BAND_LO, PROXY_BAND_HI = 4, 0.15, 0.6

NOTES = "Your private working notes (not shared with the panel):"


def briefed_reply(it) -> str | None:
    from examples.test_cases import get_case
    seats = json.loads((ROOT / "bench" / "analysis" / "cell41" /
                        "seats.json").read_text())[it["case"]]
    user = (f"Question under analysis:\n{get_case(it['case']).prompt}\n\n"
            f"Your earlier contribution:\n{seats[it['seat_B']].rstrip()}"
            f"\n\n{it['pos_B']}\n\n{NOTES}\n{it['fact_R1']}\n\n"
            f"{it['followup_q']}")
    for _ in range(3):
        t = chat(WRITER, SEATS[it["seat_B"]], user,
                 temperature=0.7, max_tokens=2048)
        if t and t.strip():
            return t.strip()
    return None


def one_run(it, arm: str, rep: int) -> dict | None:
    from examples.test_cases import get_case
    contribs = build_contribs(it)          # Cell 44's builder — no fact
    q = get_case(it["case"]).prompt
    s1 = chat(WRITER, S1_PROMPT, f"{contribs}\n\nQuestion:\n{q}",
              temperature=0.6, max_tokens=2048)
    if not s1 or not s1.strip():
        return None
    named = tension_named(s1, it)
    dispatched = named and arm == "live"
    reply, fact_in_reply = None, None
    if dispatched:
        reply = briefed_reply(it)
        if reply is None:
            return None
        fact_in_reply = has_fact(reply, it)
    user2 = f"{contribs}\n\n--- YOUR TENSION LIST ---\n{s1.strip()}\n\n"
    if dispatched:
        user2 += (f"--- FOLLOW-UP CLARIFICATION (from the "
                  f"{it['route_domain']} specialist, at the lead's request) "
                  f"---\n{reply}\n\n")
    user2 += f"Question:\n{q}"
    s2 = chat(WRITER, S2_PROMPT, user2, temperature=0.6, max_tokens=8192)
    if not s2 or not s2.strip():
        return None
    return {"run_id": f"i{it['id']}__{arm}__r{rep}", "item": it["id"],
            "case": it["case"], "arm": arm, "repeat": rep,
            "tension_named": named, "dispatched": dispatched,
            "fact_in_reply": fact_in_reply, "reply": reply,
            "s1": s1, "output": s2}


def _generate(arms, repeats, label) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RUNS.exists():
        done = {json.loads(l)["run_id"]
                for l in RUNS.read_text().splitlines() if l.strip()}
    todo = [(it, a, r) for it in ITEMS for a in arms for r in range(repeats)
            if f"i{it['id']}__{a}__r{r}" not in done]
    print(f"cell54 {label}: {len(todo)} runs to go", flush=True)
    t0, fails = 0.0 + time.time(), 0
    with RUNS.open("a") as fh:
        for k, (it, a, r) in enumerate(todo):
            rec = one_run(it, a, r)
            if rec is None:
                fails += 1
                if fails >= 5:
                    raise SystemExit("ABORTING — resumable.")
                continue
            fails = 0
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 5 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1)/60:.0f}m left", flush=True)
    print(f"cell54 {label} complete")


def stage_pilot() -> None:
    t = chat(WRITER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED")
    print("preflight ok", flush=True)
    prod, saved = 0, {}
    for it in ITEMS:
        rep = briefed_reply(it)
        saved[str(it["id"])] = rep
        got = bool(rep) and has_fact(rep, it)
        prod += got
        print(f"  GP1 item {it['id']}: reply {len(rep or '')} chars, "
              f"fact surfaced: {got}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gp1_replies.json").write_text(json.dumps(saved,
                                                     ensure_ascii=False))
    print(f"GP1 production: {prod}/{len(ITEMS)} (require >= {PROD_GATE})")
    _generate(("mini-control",), MINI_REPS, "batch-check")
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()
            if l.strip()]
    mini = [r for r in rows if r["arm"] == "mini-control"]
    by = {it["id"]: it for it in ITEMS}
    named = sum(1 for r in mini if r["tension_named"])
    from train.run_cell53_live_followup import _deep
    lit = sum(1 for r in mini
              if any(_deep(k) in _deep(r["output"])
                     for k in by[r["item"]]["r_keys"]))
    nr, px = named / max(len(mini), 1), lit / max(len(mini), 1)
    print(f"GP2 batch check: named {named}/{len(mini)} = {nr:.2f} "
          f"(require >= {NAME_BAND_LO}); literal R-proxy {px:.2f} "
          f"(require <= {PROXY_BAND_HI})")
    ok = prod >= PROD_GATE and nr >= NAME_BAND_LO and px <= PROXY_BAND_HI
    (OUT / "pilot_gate.json").write_text(json.dumps(
        {"prod": prod, "mini_named": nr, "mini_proxy": px, "pass": ok}))
    print("PILOT GATES: " + ("PASS" if ok else "FAIL — cell halts"))


def stage_runs() -> None:
    gate = json.loads((OUT / "pilot_gate.json").read_text())
    if not gate["pass"]:
        raise SystemExit("pilot gate FAIL recorded — runs not permitted")
    _generate(("live",), REPEATS, "runs")


def stage_judge() -> None:
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()
            if l.strip()]
    by = {it["id"]: it for it in ITEMS}
    cpath = OUT / "judgments.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    t0 = time.time()
    for i, r in enumerate(rows):
        it = by[r["item"]]
        r_first = (r["repeat"] % 2 == 0)
        p1, p2 = ((it["R_desc"], it["antiR_desc"]) if r_first
                  else (it["antiR_desc"], it["R_desc"]))
        for j in JUDGES:
            key = f"{j}|{r['run_id']}"
            if cache.get(key) is not None:
                continue
            lab = parse_adopt(chat(j, JUDGE_PROMPT.format(p1=p1, p2=p2),
                                   f"REPORT:\n{r['output']}",
                                   temperature=0.0, max_tokens=2048))
            if lab in ("ONE", "TWO"):
                lab = ("R" if (lab == "ONE") == r_first else "ANTI")
            cache[key] = lab
        cpath.write_text(json.dumps(cache))
        if (i + 1) % 10 == 0:
            print(f"  judged {i+1}/{len(rows)} "
                  f"{time.time()-t0:.0f}s", flush=True)
    print("cell54 judging complete")


def _adopt(r, cache, judges):
    labs = [cache.get(f"{j}|{r['run_id']}") for j in judges]
    return labs[0] if (None not in labs and labs[0] == labs[1]) else \
        ("QUAR" if None in labs else "DISAGREE")


def stage_measure() -> None:
    import random
    rng = random.Random(54)
    fresh = [json.loads(l) for l in RUNS.read_text().splitlines()
             if l.strip()]
    fcache = json.loads((OUT / "judgments.json").read_text())
    arch = [json.loads(l) for l in C44_RUNS.read_text().splitlines()
            if l.strip()]
    acache = json.loads(C44_JUDG.read_text())
    for r in fresh:
        r["adopt"] = _adopt(r, fcache, JUDGES)
    for r in arch:
        r["adopt"] = _adopt(r, acache, JUDGES)
    live = [r for r in fresh if r["arm"] == "live" and r["tension_named"]]
    mini = [r for r in fresh if r["arm"] == "mini-control"
            and r["tension_named"]]
    ctrl = [r for r in arch if r["arm"] == "control" and r["tension_named"]]
    scri = [r for r in arch if r["arm"] == "informed" and r["tension_named"]]
    print("=" * 76)
    print("CELL 54 RAW TABLE (mandatory, before any verdict)")
    print(f"  {'arm':<22}{'n(named)':>9}{'R':>5}{'ANTI':>6}{'NEITHER':>9}"
          f"{'fact-in-reply':>15}")
    for lbl, v in (("live (fresh)", live), ("mini-control (fresh)", mini),
                   ("control (C44 arch)", ctrl),
                   ("informed (C44 arch)", scri)):
        fr = sum(1 for r in v if r.get("fact_in_reply"))
        print(f"  {lbl:<22}{len(v):>9}"
              f"{sum(1 for r in v if r['adopt']=='R'):>5}"
              f"{sum(1 for r in v if r['adopt']=='ANTI'):>6}"
              f"{sum(1 for r in v if r['adopt']=='NEITHER'):>9}"
              f"{fr:>15}")
    lf = [r for r in fresh if r["arm"] == "live"]
    print(f"  live-arm trigger: "
          f"{sum(1 for r in lf if r['tension_named'])}/{len(lf)}")

    is_r = lambda r: r["adopt"] == "R"

    def cluster_diff(va, vb):
        items_ = sorted({r["item"] for r in va + vb})
        d: dict[tuple, list] = {}
        for tag, rows_ in (("a", va), ("b", vb)):
            for r in rows_:
                d.setdefault((r["item"], tag), []).append(is_r(r))
        ds = []
        for _ in range(5000):
            s = [items_[rng.randrange(len(items_))] for _ in items_]
            xa = [x for i in s for x in d.get((i, "a"), [])]
            xb = [x for i in s for x in d.get((i, "b"), [])]
            if xa and xb:
                ds.append(sum(xa)/len(xa) - sum(xb)/len(xb))
        ds.sort()
        xa = [x for i in items_ for x in d.get((i, "a"), [])]
        xb = [x for i in items_ for x in d.get((i, "b"), [])]
        return (sum(xa)/max(len(xa), 1) - sum(xb)/max(len(xb), 1),
                ds[int(.025*len(ds))], ds[int(.975*len(ds))])

    e, lo, hi = cluster_diff(live, ctrl)
    print(f"\nP54.1 live-briefed - archived control (R-adoption): "
          f"{e:+.3f} [{lo:+.3f}, {hi:+.3f}]")
    print("P54.1: " + ("SUPPORTED — the live loop works end-to-end"
                       if lo > 0 else
                       ("FALSIFIED — live conveyance does not beat no-loop"
                        if hi < 0 else "NOT EVALUABLE at power")))
    e2, lo2, hi2 = cluster_diff(live, scri)
    print(f"P54.2 live-briefed - scripted ceiling: {e2:+.3f} "
          f"[{lo2:+.3f}, {hi2:+.3f}]")
    print("P54.2: " + ("live comparable to the scripted ceiling"
                       if lo2 > -0.3 else
                       "live deficit exceeds 0.3 — reported as measured"))
    disp = [r for r in live if r["dispatched"]]
    fr = [r for r in disp if r.get("fact_in_reply")]
    print(f"\nP54.3 production: fact in briefed reply {len(fr)}/{len(disp)}"
          f" = {len(fr)/max(len(disp),1):.3f}")
    for grp, lbl in ((fr, "fact-present"),
                     ([r for r in disp if not r.get("fact_in_reply")],
                      "fact-absent")):
        k = sum(1 for r in grp if is_r(r))
        print(f"  R-adoption | {lbl}: {k}/{len(grp)} = "
              f"{k/max(len(grp),1):.3f} (descriptive, unclustered)")
    (OUT / "measured.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k not in ("s1", "output", "reply")}
         for r in fresh], indent=1))


if __name__ == "__main__":
    {"pilot": stage_pilot, "runs": stage_runs,
     "judge": stage_judge, "measure": stage_measure}[sys.argv[1]]()
