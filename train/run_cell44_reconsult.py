"""Cell 44 — orchestrator-routed re-consultation (design c), lead side.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 44 PRE-REGISTRATION".
Items frozen in docs/CELL44_ITEMS.json before any run.

Two-stage lead, identical stage-1 in all arms; the single factor is what
the orchestrator appends between stages: nothing (control), a responsive
clarification without the deciding fact (filler), or with it (informed).

Run:  .venv/bin/python train/run_cell44_reconsult.py pilot
      .venv/bin/python train/run_cell44_reconsult.py runs
      .venv/bin/python train/run_cell44_reconsult.py judge
      .venv/bin/python train/run_cell44_reconsult.py measure
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

from train.run_cell25_moa import chat                          # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell44"
RUNS = ROOT / "bench" / "runs" / "cell44_reconsult.jsonl"
SEATS_PATH = ROOT / "bench" / "analysis" / "cell41" / "seats.json"
ITEMS = json.loads((ROOT / "docs" / "CELL44_ITEMS.json").read_text())["items"]
WRITER = "gpt-oss:20b"
JUDGES = ["gpt-oss:20b", "qwen3-vl:30b-a3b-instruct"]
ROLES = ("healthcare", "legal", "finance")
ARMS = ("control", "filler", "informed")
REPEATS = 6
PILOT_REPEATS = 2
NAME_GATE, DECIDE_GATE = 0.5, 0.4

S1_PROMPT = ("You are the lead analyst. Several specialists have written the "
             "contributions below. Before writing your final answer, list the "
             "3-5 most important TENSIONS you see between the contributions — "
             "places where following one specialist makes another's "
             "recommendation harder, or where they disagree. Output ONLY the "
             "numbered tension list, one or two sentences each.")

S2_PROMPT = ("You are the lead analyst. Below are the specialist "
             "contributions, the tension list you already wrote, and any "
             "follow-up clarification you requested. Write the final answer "
             "to the decision-maker's question.")

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def preflight() -> None:
    from gst.registry import gate_GE, load_frozen
    reg = load_frozen(ROOT / "docs" / "DICTATION_REGISTRY.json")
    viol = gate_GE({"S1": S1_PROMPT, "S2": S2_PROMPT}, reg, construct_only=True)
    if viol:
        raise SystemExit("GATE G-E FAILED: " + "; ".join(viol))
    t = chat(WRITER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED — backend unreachable.")
    print("preflight: gate G-E PASS, backend responds")


def guard_items() -> None:
    """Registered construction guards: probe collisions and filler length."""
    problems = []
    for it in ITEMS:
        prem = (it["pos_A"] + " " + it["pos_B"]).lower()
        for k in it["r_keys"] + it["anti_keys"]:
            if k.lower() in prem:
                problems.append(f"item {it['id']}: probe {k!r} occurs in its "
                                f"own appended premises")
        ratio = len(it["filler"]) / max(len(it["fact_F"]), 1)
        if not 0.85 <= ratio <= 1.15:
            problems.append(f"item {it['id']}: filler/informed length ratio "
                            f"{ratio:.2f} outside 15%")
        if it["seat_B"] != it["route_domain"]:
            problems.append(f"item {it['id']}: route_domain != seat_B")
    if problems:
        for p in problems:
            print("  " + p)
        raise SystemExit("ITEM GUARDS FAILED")
    print(f"item guards: PASS ({len(ITEMS)} items)")


def build_contribs(it) -> str:
    seats = json.loads(SEATS_PATH.read_text())[it["case"]]
    parts = []
    for role in ROLES:
        base = seats.get(role, "")
        if not base:
            continue
        add = ""
        if role == it["seat_A"]:
            add = "\n\n" + it["pos_A"]
        elif role == it["seat_B"]:
            add = "\n\n" + it["pos_B"]
        parts.append(f"--- {role.upper()} SPECIALIST CONTRIBUTION ---\n"
                     + base.rstrip() + add)
    return "\n\n".join(parts)


def tension_named(s1_text: str, it) -> bool:
    """Frozen per-item keyword containment — a known-value check. The
    planted tension is 'named' if any line mentions the route domain AND an
    item topic key."""
    low = _THINK.sub("", s1_text).lower()
    for line in low.splitlines():
        if it["route_domain"] in line and any(k in line for k in it["trigger_keys"]):
            return True
    return False


def clarification(it, arm: str) -> str:
    body = it["fact_F"] if arm == "informed" else it["filler"]
    return (f"--- FOLLOW-UP CLARIFICATION (from the {it['route_domain']} "
            f"specialist, at the lead's request) ---\n{body}")


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
    user2 = f"{contribs}\n\n--- YOUR TENSION LIST ---\n{s1.strip()}\n\n"
    if dispatched:
        user2 += clarification(it, arm) + "\n\n"
    user2 += f"Question:\n{q}"
    s2 = chat(WRITER, S2_PROMPT, user2, temperature=0.6, max_tokens=8192)
    if not s2 or not s2.strip():
        return None
    return {"run_id": f"i{it['id']}__{arm}__r{rep}", "item": it["id"],
            "case": it["case"], "arm": arm, "repeat": rep,
            "tension_named": named, "dispatched": dispatched,
            "s1": s1, "output": s2}


def _stage_generate(arms, repeats, label) -> None:
    preflight()
    guard_items()
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RUNS.exists():
        for l in RUNS.read_text().splitlines():
            if l.strip():
                done.add(json.loads(l)["run_id"])
    todo = [(it, a, r) for it in ITEMS for a in arms for r in range(repeats)
            if f"i{it['id']}__{a}__r{r}" not in done]
    print(f"cell44 {label}: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0, fails = time.time(), 0
    with RUNS.open("a") as fh:
        for k, (it, a, r) in enumerate(todo):
            rec = one_run(it, a, r)
            if rec is None:
                fails += 1
                print(f"  EMPTY i{it['id']}/{a}/r{r} (consecutive {fails})", flush=True)
                if fails >= 5:
                    raise SystemExit("ABORTING — backend down; resumable.")
                continue
            fails = 0
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 5 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print(f"cell44 {label} complete")


def stage_pilot() -> None:
    """Control arm only, registered gates. Runs are reused by the full stage."""
    _stage_generate(("control",), PILOT_REPEATS, "pilot")
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    pilot = [r for r in rows if r["arm"] == "control" and r["repeat"] < PILOT_REPEATS]
    named = sum(1 for r in pilot if r["tension_named"])
    # decisive proxy for the gate: literal adoption of either side
    def lit(r):
        it = ITEMS[r["item"]]
        low = r["output"].lower()
        return (any(k in low for k in it["r_keys"])
                or any(k in low for k in it["anti_keys"]))
    dec = sum(1 for r in pilot if lit(r))
    print("=" * 70)
    print(f"PILOT GATES (registered): n={len(pilot)}")
    print(f"  planted tension named in S1: {named}/{len(pilot)} = "
          f"{named/len(pilot):.2f}  (gate >= {NAME_GATE})  -> "
          f"{'PASS' if named/len(pilot) >= NAME_GATE else 'FAIL'}")
    print(f"  literal side-adoption (proxy): {dec}/{len(pilot)} = "
          f"{dec/len(pilot):.2f}  (gate >= {DECIDE_GATE})  -> "
          f"{'PASS' if dec/len(pilot) >= DECIDE_GATE else 'FAIL'}")
    print("  (judged adoption in the full measure will exceed the literal "
          "proxy; the gate is conservative)")


def stage_runs() -> None:
    _stage_generate(ARMS, REPEATS, "runs")


JUDGE_PROMPT = """\
You are auditing an analyst's final report. Two possible positions on one
specific decision are given below. Decide which position the report
actually adopts.

Position ONE: {p1}
Position TWO: {p2}

Reply with exactly one word on a single line:
ONE   - the report adopts Position ONE
TWO   - the report adopts Position TWO
NEITHER - the report does not commit to either"""


def parse_adopt(txt: str | None) -> str | None:
    if not txt or not txt.strip():
        return None
    t = _THINK.sub("", txt).upper()
    hits = [w for w in ("NEITHER", "ONE", "TWO") if re.search(rf"\b{w}\b", t)]
    if "NEITHER" in hits:
        return "NEITHER"
    return hits[0] if len(hits) == 1 else None


def stage_judge() -> None:
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    cpath = OUT / "judgments.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    t0 = time.time()
    for i, r in enumerate(rows):
        it = ITEMS[r["item"]]
        # counterbalance which position is ONE by repeat parity
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
    print("cell44 judging complete")


def stage_measure() -> None:
    import random
    from gst.stats import wilson_ci
    rng = random.Random(0)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    cache = json.loads((OUT / "judgments.json").read_text())

    for r in rows:
        labs = [cache.get(f"{j}|{r['run_id']}") for j in JUDGES]
        r["adopt"] = labs[0] if (None not in labs and labs[0] == labs[1]) else \
                     ("QUAR" if None in labs else "DISAGREE")

    # registered conditioning: trigger-named runs, all arms (S1 identical)
    named = [r for r in rows if r["tension_named"]]

    def by_arm(arm, pred):
        v = [r for r in named if r["arm"] == arm]
        return sum(1 for r in v if pred(r)), len(v)

    def cluster_diff(a, b, pred):
        items_ = sorted({r["item"] for r in named})
        d = {}
        for r in named:
            d.setdefault((r["item"], r["arm"]), []).append(pred(r))
        ds = []
        for _ in range(5000):
            s = [items_[rng.randrange(len(items_))] for _ in items_]
            va = [x for i in s for x in d.get((i, a), [])]
            vb = [x for i in s for x in d.get((i, b), [])]
            if va and vb:
                ds.append(sum(va) / len(va) - sum(vb) / len(vb))
        ds.sort()
        return (ds[int(.025 * len(ds))], ds[int(.975 * len(ds))]) if ds else None

    print("=" * 76)
    print("CELL 44 — orchestrator-routed re-consultation (lead side)")
    print("=" * 76)
    print("P44.4 RAW TABLE (mandatory, before any verdict)")
    n_named = len(named)
    print(f"  runs {len(rows)}; trigger-named {n_named} "
          f"({n_named/len(rows):.2f}); dispatched among named loop-arm runs: "
          f"{sum(1 for r in named if r['dispatched'])}")
    agree = sum(1 for r in rows if r["adopt"] in ("R", "ANTI", "NEITHER"))
    print(f"  judge agreement on adoption: {agree}/{len(rows)} = "
          f"{agree/len(rows):.3f}  "
          f"(disagree {sum(1 for r in rows if r['adopt']=='DISAGREE')}, "
          f"quarantined {sum(1 for r in rows if r['adopt']=='QUAR')})")
    print(f"  {'arm':<10}{'n(named)':>9}{'R':>6}{'ANTI':>7}{'NEITHER':>9}"
          f"{'chars':>8}")
    for a in ARMS:
        v = [r for r in named if r["arm"] == a]
        if not v:
            continue
        print(f"  {a:<10}{len(v):>9}"
              f"{sum(1 for r in v if r['adopt']=='R'):>6}"
              f"{sum(1 for r in v if r['adopt']=='ANTI'):>7}"
              f"{sum(1 for r in v if r['adopt']=='NEITHER'):>9}"
              f"{sum(len(r['output']) for r in v)//len(v):>8}")

    is_r = lambda r: r["adopt"] == "R"
    decided = lambda r: r["adopt"] in ("R", "ANTI")

    print()
    print("P44.1 INFORMATION USE — informed vs control, R-adoption")
    ci = cluster_diff("informed", "control", is_r)
    ka, na = by_arm("informed", is_r)
    kc, nc = by_arm("control", is_r)
    print(f"  control {kc}/{nc} = {kc/max(nc,1):.3f}   informed {ka}/{na} = "
          f"{ka/max(na,1):.3f}   diff CI [{ci[0]:+.3f},{ci[1]:+.3f}]")
    print(f"  P44.1: {'SUPPORTED' if ci[0] > 0 else 'FALSIFIED — the lead does not use a clarification it asked for'}")

    print()
    print("P44.2 RITUAL vs INFORMATION — informed vs filler, R-adoption")
    ci2 = cluster_diff("informed", "filler", is_r)
    kf, nf = by_arm("filler", is_r)
    print(f"  filler {kf}/{nf} = {kf/max(nf,1):.3f}   informed {ka}/{na} = "
          f"{ka/max(na,1):.3f}   diff CI [{ci2[0]:+.3f},{ci2[1]:+.3f}]")
    print(f"  P44.2: {'SUPPORTED' if ci2[0] > 0 else 'FALSIFIED — consultation works as ritual, not information'}")

    print()
    print("P44.3 CONSULTATION-AS-LICENSE — filler vs control, ANY decisive adoption")
    ci3 = cluster_diff("filler", "control", decided)
    kd, nd = by_arm("filler", decided)
    kc2, nc2 = by_arm("control", decided)
    print(f"  control {kc2}/{nc2} = {kc2/max(nc2,1):.3f}   filler {kd}/{nd} = "
          f"{kd/max(nd,1):.3f}   diff CI [{ci3[0]:+.3f},{ci3[1]:+.3f}]  "
          f"(mandatory reporting, no bar)")

    (OUT / "measured.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k not in ("s1", "output")}
         for r in rows], indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    {"pilot": stage_pilot, "runs": stage_runs,
     "judge": stage_judge, "measure": stage_measure}[stage]()
