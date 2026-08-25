"""Cell 53 — live-seat follow-ups: the routed loop end-to-end.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 53 PRE-REGISTRATION"
(commit 39c1860, before item authoring). Items: CELL44_ITEMS.json fields
extended by CELL53_ITEMS.json (fact_R1, followup_q, fact_keys).

Arms: control (no loop) / live (real seat writes the reply) /
scripted (Cell 44's informed arm, the ceiling). fact_R1 is inserted at
the midpoint of seat_B's base text by a frozen rule, identically in all
arms — the loop is the only factor.

Run:  .venv/bin/python train/run_cell53_live_followup.py guards
      .venv/bin/python train/run_cell53_live_followup.py pilot
      .venv/bin/python train/run_cell53_live_followup.py runs
      .venv/bin/python train/run_cell53_live_followup.py judge
      .venv/bin/python train/run_cell53_live_followup.py measure
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
                                        S2_PROMPT, parse_adopt,
                                        tension_named)
from train.run_cell47_redundancy import norm                   # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell53"
RUNS = ROOT / "bench" / "runs" / "cell53_live_followup.jsonl"
SEATS_PATH = ROOT / "bench" / "analysis" / "cell41" / "seats.json"
C44 = {it["id"]: it for it in
       json.loads((ROOT / "docs" / "CELL44_ITEMS.json").read_text())["items"]}
EXT = {it["id"]: it for it in
       json.loads((ROOT / "docs" / "CELL53_ITEMS.json").read_text())["items"]}
ITEMS = [{**C44[i], **EXT[i]} for i in sorted(C44)]
WRITER = "gpt-oss:20b"
JUDGES = ["gpt-oss:20b", "qwen3-vl:30b-a3b-instruct"]
ROLES = ("healthcare", "legal", "finance")
ARMS = ("control", "live", "scripted")
REPEATS = 6
PILOT_REPEATS = 2
NAME_GATE, HEADROOM_GATE, PROD_GATE = 0.5, 0.6, 4


def seat_b_text(it) -> str:
    """seat_B base text with fact_R1 inserted at the midpoint line —
    the frozen burial rule, applied identically in every arm."""
    seats = json.loads(SEATS_PATH.read_text())[it["case"]]
    base = seats[it["seat_B"]].rstrip()
    lines = base.split("\n")
    mid = len(lines) // 2
    lines = lines[:mid] + ["", it["fact_R1"], ""] + lines[mid:]
    return "\n".join(lines)


def build_contribs(it) -> str:
    seats = json.loads(SEATS_PATH.read_text())[it["case"]]
    parts = []
    for role in ROLES:
        base = seats.get(role, "")
        if not base:
            continue
        if role == it["seat_B"]:
            body = seat_b_text(it) + "\n\n" + it["pos_B"]
        elif role == it["seat_A"]:
            body = base.rstrip() + "\n\n" + it["pos_A"]
        else:
            body = base.rstrip()
        parts.append(f"--- {role.upper()} SPECIALIST CONTRIBUTION ---\n"
                     + body)
    return "\n\n".join(parts)


def has_fact(reply: str, it) -> bool:
    lo = norm(reply or "")
    return any(norm(k) in lo for k in it["fact_keys"])


def live_reply(it) -> str | None:
    from examples.test_cases import get_case
    user = (f"Question under analysis:\n{get_case(it['case']).prompt}\n\n"
            f"Your earlier contribution:\n{seat_b_text(it)}\n\n{it['pos_B']}"
            f"\n\n{it['followup_q']}")
    for _ in range(3):
        t = chat(WRITER, SEATS[it["seat_B"]], user,
                 temperature=0.7, max_tokens=2048)
        if t and t.strip():
            return t.strip()
    return None


def clar_block(it, body: str) -> str:
    return (f"--- FOLLOW-UP CLARIFICATION (from the {it['route_domain']} "
            f"specialist, at the lead's request) ---\n{body}")


def stage_guards() -> None:
    from examples.test_cases import get_case
    from gst.registry import gate_GE, load_frozen
    seats_all = json.loads(SEATS_PATH.read_text())
    problems = []
    for it in ITEMS:
        seats = seats_all[it["case"]]
        ambient = norm(get_case(it["case"]).prompt) + " " + " ".join(
            norm(seats.get(r, "")) for r in ROLES) + " " + \
            norm(it["pos_A"]) + " " + norm(it["pos_B"])
        qn = norm(it["followup_q"])
        for k in it["fact_keys"]:
            if norm(k) in ambient:
                problems.append(f"item {it['id']}: fact_key {k!r} ambient")
            if norm(k) in qn:
                problems.append(f"item {it['id']}: fact_key {k!r} in "
                                f"followup_q")
        for k in it["r_keys"] + it["anti_keys"]:
            if norm(k) in qn:
                problems.append(f"item {it['id']}: resolution key {k!r} in "
                                f"followup_q")
        if norm(it["fact_R1"]).split()[:4] == norm(it["fact_F"]).split()[:4]:
            problems.append(f"item {it['id']}: fact_R1 opens like fact_F")
    reg = load_frozen(ROOT / "docs" / "DICTATION_REGISTRY.json")
    viol = gate_GE({"S1": S1_PROMPT, "S2": S2_PROMPT,
                    **{f"fq{it['id']}": it["followup_q"] for it in ITEMS}},
                   reg, construct_only=True)
    if viol:
        problems += ["G-E: " + v for v in viol]
    if problems:
        for p in problems:
            print("  " + p)
        raise SystemExit("ITEM GUARDS FAILED")
    print(f"item guards: PASS ({len(ITEMS)} items); gate G-E PASS")


def one_run(it, arm: str, rep: int) -> dict | None:
    from examples.test_cases import get_case
    contribs = build_contribs(it)
    q = get_case(it["case"]).prompt
    s1 = chat(WRITER, S1_PROMPT, f"{contribs}\n\nQuestion:\n{q}",
              temperature=0.6, max_tokens=2048)
    if not s1 or not s1.strip():
        return None
    named = tension_named(s1, it)
    dispatched = named and arm != "control"
    reply, fact_in_reply = None, None
    if dispatched:
        if arm == "scripted":
            reply = it["fact_F"]
        else:
            reply = live_reply(it)
            if reply is None:
                return None
        fact_in_reply = has_fact(reply, it)
    user2 = f"{contribs}\n\n--- YOUR TENSION LIST ---\n{s1.strip()}\n\n"
    if dispatched:
        user2 += clar_block(it, reply) + "\n\n"
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
    print(f"cell53 {label}: {len(todo)} runs to go", flush=True)
    t0, fails = time.time(), 0
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
    print(f"cell53 {label} complete")


def stage_pilot() -> None:
    stage_guards()
    t = chat(WRITER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED")
    print("preflight ok", flush=True)
    # GP1: one live dispatch per item
    prod = 0
    for it in ITEMS:
        rep = live_reply(it)
        got = bool(rep) and has_fact(rep, it)
        prod += got
        print(f"  GP1 item {it['id']}: reply {len(rep or '')} chars, "
              f"fact surfaced: {got}", flush=True)
    print(f"GP1 production: {prod}/{len(ITEMS)} (require >= {PROD_GATE})")
    # GP2/GP3: control pilot
    _generate(("control",), PILOT_REPEATS, "pilot")
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    pilot = [r for r in rows if r["arm"] == "control"
             and r["repeat"] < PILOT_REPEATS]
    by = {it["id"]: it for it in ITEMS}
    named = sum(1 for r in pilot if r["tension_named"])
    lit = sum(1 for r in pilot
              if any(norm(k) in norm(r["output"])
                     for k in by[r["item"]]["r_keys"]))
    name_rate = named / max(len(pilot), 1)
    floor = lit / max(len(pilot), 1)
    print(f"GP3 tension named: {named}/{len(pilot)} = {name_rate:.2f} "
          f"(require >= {NAME_GATE})")
    print(f"GP2 control literal R-proxy: {lit}/{len(pilot)} = {floor:.2f} "
          f"(require <= {HEADROOM_GATE})")
    ok = prod >= PROD_GATE and name_rate >= NAME_GATE and \
        floor <= HEADROOM_GATE
    (OUT / "pilot_gate.json").write_text(json.dumps(
        {"prod": prod, "name_rate": name_rate, "floor": floor, "pass": ok}))
    print("PILOT GATES: " + ("PASS" if ok else "FAIL — cell halts"))


def stage_runs() -> None:
    gate = json.loads((OUT / "pilot_gate.json").read_text())
    if not gate["pass"]:
        raise SystemExit("pilot gate FAIL recorded — runs not permitted")
    _generate(ARMS, REPEATS, "runs")


def stage_judge() -> None:
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    by = {it["id"]: it for it in ITEMS}
    cpath = OUT / "judgments.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    t0 = time.time()
    for i, r in enumerate(rows):
        it = by[r["item"]]
        r_first = (r["repeat"] % 2 == 0)
        p1, p2 = ((it["R_desc"], it["antiR_desc"]) if r_first
                  else (it["antiR_desc"], it["R_desc"]))
        body = f"REPORT:\n{r['output']}"
        for j in JUDGES:
            key = f"{j}|{r['run_id']}"
            if cache.get(key) is not None:
                continue
            lab = parse_adopt(chat(j, JUDGE_PROMPT.format(p1=p1, p2=p2), body,
                                   temperature=0.0, max_tokens=2048))
            if lab in ("ONE", "TWO"):
                lab = ("R" if (lab == "ONE") == r_first else "ANTI")
            cache[key] = lab
        cpath.write_text(json.dumps(cache))
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            print(f"  judged {i+1}/{len(rows)} {el:.0f}s "
                  f"~{el/(i+1)*(len(rows)-i-1):.0f}s left", flush=True)
    print("cell53 judging complete")


def stage_measure() -> None:
    import random
    rng = random.Random(53)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    cache = json.loads((OUT / "judgments.json").read_text())
    for r in rows:
        labs = [cache.get(f"{j}|{r['run_id']}") for j in JUDGES]
        r["adopt"] = labs[0] if (None not in labs and labs[0] == labs[1]) \
            else ("QUAR" if None in labs else "DISAGREE")
    named = [r for r in rows if r["tension_named"]]
    agree = sum(1 for r in rows if r["adopt"] in ("R", "ANTI", "NEITHER"))
    print("=" * 76)
    print("CELL 53 RAW TABLE (mandatory, before any verdict)")
    print(f"  runs {len(rows)}  named {len(named)} "
          f"({len(named)/max(len(rows),1):.2f})  judge agreement "
          f"{agree}/{len(rows)} = {agree/max(len(rows),1):.3f}")
    print(f"  {'arm':<10}{'n(named)':>9}{'R':>5}{'ANTI':>6}{'NEITHER':>9}"
          f"{'disp':>6}{'fact-in-reply':>15}")
    for a in ARMS:
        v = [r for r in named if r["arm"] == a]
        fr = [r for r in v if r.get("fact_in_reply")]
        print(f"  {a:<10}{len(v):>9}"
              f"{sum(1 for r in v if r['adopt']=='R'):>5}"
              f"{sum(1 for r in v if r['adopt']=='ANTI'):>6}"
              f"{sum(1 for r in v if r['adopt']=='NEITHER'):>9}"
              f"{sum(1 for r in v if r['dispatched']):>6}"
              f"{len(fr):>15}")

    is_r = lambda r: r["adopt"] == "R"

    def cluster_diff(a, b):
        items_ = sorted({r["item"] for r in named})
        d = {}
        for r in named:
            d.setdefault((r["item"], r["arm"]), []).append(is_r(r))
        pts, ds = None, []
        for _ in range(5000):
            s = [items_[rng.randrange(len(items_))] for _ in items_]
            va = [x for i in s for x in d.get((i, a), [])]
            vb = [x for i in s for x in d.get((i, b), [])]
            if va and vb:
                ds.append(sum(va)/len(va) - sum(vb)/len(vb))
        ds.sort()
        va = [x for i in items_ for x in d.get((i, a), [])]
        vb = [x for i in items_ for x in d.get((i, b), [])]
        est = sum(va)/max(len(va), 1) - sum(vb)/max(len(vb), 1)
        return est, ds[int(.025*len(ds))], ds[int(.975*len(ds))]

    e, lo, hi = cluster_diff("live", "control")
    print(f"\nP53.1 live - control (R-adoption): {e:+.3f} [{lo:+.3f}, "
          f"{hi:+.3f}]")
    print("P53.1: " + ("SUPPORTED — the live loop works end-to-end"
                       if lo > 0 else
                       ("FALSIFIED — the live loop does not beat no-loop"
                        if hi < 0 else
                        "NOT EVALUABLE at power" if e > 0 else
                        "FALSIFIED — the live loop does not beat no-loop")))
    e2, lo2, hi2 = cluster_diff("live", "scripted")
    print(f"P53.2 live - scripted: {e2:+.3f} [{lo2:+.3f}, {hi2:+.3f}]")
    print("P53.2: " + ("live loop comparable to the scripted ceiling"
                       if lo2 > -0.3 else "live deficit exceeds 0.3 — gap "
                       "reported as measured"))
    disp = [r for r in named if r["arm"] == "live" and r["dispatched"]]
    fr = [r for r in disp if r.get("fact_in_reply")]
    print(f"\nP53.3 production: fact in live reply {len(fr)}/{len(disp)} = "
          f"{len(fr)/max(len(disp),1):.3f}")
    for grp, lbl in ((fr, "fact-present"),
                     ([r for r in disp if not r.get("fact_in_reply")],
                      "fact-absent")):
        k = sum(1 for r in grp if is_r(r))
        print(f"  R-adoption | {lbl}: {k}/{len(grp)}"
              f" = {k/max(len(grp),1):.3f} (descriptive, unclustered)")
    (OUT / "measured.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k not in ("s1", "output", "reply")}
         for r in rows], indent=1))


if __name__ == "__main__":
    {"guards": stage_guards, "pilot": stage_pilot, "runs": stage_runs,
     "judge": stage_judge, "measure": stage_measure}[sys.argv[1]]()
