"""Cell 67 — the wrong figure in the live chain, with a checkable answer.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 67 PRE-REGISTRATION".

Cells 47 and 59 found that a second specialist holding the right figure cuts
the editor's use of a wrong one. Both used eight items and matched figures in
free text. This cell runs the same idea through the assembled chain (plan,
three specialists, tension list, one follow-up, final answer) on the Cell 63
items, where the final answer is a number the generator script can check.

The figure is removed from the case. It reaches the chain only through a
specialist's private notes (the Cell 54/59 channel):

  bare         specialist A's notes quote the passage with a WRONG figure
  redundancy   the same, and specialist B's notes quote the RIGHT figure

Within an item the plan and the texts of specialists A and C are generated
once and used in both arms, so the arms differ in specialist B's notes and
in what follows from them. One model plays every part (gpt-oss:20b), as in
the system the paper describes.

Scoring is by script: the final ANSWER line against the engine's answers.

Run:  .venv/bin/python train/run_cell67_livechain.py smoke     (an item Cell 63 excluded)
      .venv/bin/python train/run_cell67_livechain.py runs
      .venv/bin/python train/run_cell67_livechain.py measure
"""
from __future__ import annotations

import collections
import json
import random
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))
sys.path.insert(0, str(ROOT / "train"))

import gen_cell60_items as G60                                       # noqa: E402
from gst import runlog                                               # noqa: E402
from gst.gates import FABRICATION_BLOCKLIST, blocklist_gate          # noqa: E402
from gst.smallcluster import sign_flip_p, t_interval                 # noqa: E402
from train.run_cell30_descaffold import SEATS                        # noqa: E402
from train.run_cell44_reconsult import S1_PROMPT                     # noqa: E402
from train.run_cell57_planner import PLANNER_PROMPT as IDENTIFY      # noqa: E402
from train.run_cell59_subquestions import NOTES, parse_plan          # noqa: E402
from train.run_cell60_accuracy import S2_ANSWER, correct, parse_answer  # noqa: E402
from train.run_cell63_checkable import ITEMS_PATH, _has_figure, load_items  # noqa: E402
from train.run_integration_demo import FOLLOWUP, ROSTER, SUBQ_PROMPT, _THINK  # noqa: E402

REGISTRATION = runlog.registration_for("67", ROOT)
OUT = ROOT / "bench" / "analysis" / "cell67"
RUNS = ROOT / "bench" / "runs" / "cell67_livechain.jsonl"
SHARED = OUT / "shared.json"
MODEL = "gpt-oss:20b"
ROLES = ("healthcare", "legal", "finance")
ARMS = ("bare", "redundancy")
NOTE = 'The source document I am working from reads: "{passage}"'
CONVEY_BAR = 0.75
SHORT = 4096       # short steps; 2,048 was exhausted by reasoning in Cell 61 and in this runner's shakedown


def roles_for(item_id: str) -> tuple[str, str, str]:
    """Which specialist holds the wrong figure (A), which the right one (B),
    and which holds none (C). Fixed per item."""
    order = list(ROLES)
    random.Random(f"cell67|{item_id}").shuffle(order)
    return order[0], order[1], order[2]


def gen(system: str, user: str, *, temp: float, toks: int, tag: str, audit: list) -> str | None:
    for attempt in range(4):
        if attempt:
            time.sleep(10 * attempt)
        text, meta = runlog.chat_logged(MODEL, system, user, temperature=temp, max_tokens=toks,
                                        seed=runlog.seed_for(tag) + attempt)
        audit.append({"step": tag.rsplit("|", 1)[-1], **meta})
        if text and text.strip():
            return _THINK.sub("", text).strip()
    return None


def seat(it: dict, role: str, subq: str, passage: str | None, tag: str, audit: list) -> str | None:
    a, b = tuple(r for r in ROLES if r != role)
    user = f"Case:\n{it['case_removed']}\n\nYour sub-question:\n{subq}\n\n" + ROSTER.format(a=a, b=b)
    if passage is not None:
        user += f"\n\n{NOTES}\n" + NOTE.format(passage=passage)
    return gen(SEATS[role], user, temp=0.7, toks=4096, tag=tag, audit=audit)


def shared_part(it: dict, store: dict, prefix: str = "") -> dict | None:
    """The plan and the texts of specialists A and C: made once per item."""
    key = prefix + it["id"]
    if key in store:
        return store[key]
    audit: list = []
    q = it["case_removed"] + G60.FMT
    ids = gen(IDENTIFY, f"Question:\n{q}", temp=0.7, toks=SHORT, tag=f"{key}|identify", audit=audit)
    if ids is None:
        return None
    quants = [l.strip() for l in ids.splitlines() if l.strip()][:6]
    plan = None
    for n in range(3):
        t = gen("Follow the output format exactly.",
                SUBQ_PROMPT.format(quantities="\n".join(quants)) + f"\n\nQuestion:\n{q}",
                temp=0.7, toks=SHORT, tag=f"{key}|plan{n}", audit=audit)
        plan = parse_plan(t)
        if plan:
            break
    if not plan:
        store[key] = {"invalid": "plan-parse", "audit": audit}
        return store[key]
    ra, rb, rc = roles_for(it["id"])
    ta = seat(it, ra, plan[ra], it["passage"]["wrong1"], f"{key}|seatA", audit)
    tc = seat(it, rc, plan[rc], None, f"{key}|seatC", audit)
    if ta is None or tc is None:
        return None
    store[key] = {"quantities": quants, "plan": plan, "roles": {"A": ra, "B": rb, "C": rc},
                  "seat_A": ta, "seat_C": tc, "audit": audit}
    return store[key]


def arm_part(it: dict, sh: dict, arm: str, prefix: str = "") -> dict | None:
    key = f"{prefix}{it['id']}|{arm}"
    audit: list = []
    ra, rb, rc = sh["roles"]["A"], sh["roles"]["B"], sh["roles"]["C"]
    tb = seat(it, rb, sh["plan"][rb], it["passage"]["right"] if arm == "redundancy" else None,
              f"{key}|seatB", audit)
    if tb is None:
        return None
    contribs = {ra: sh["seat_A"], rb: tb, rc: sh["seat_C"]}
    pile = "\n\n".join(f"--- {r.upper()} SPECIALIST CONTRIBUTION ---\n{contribs[r]}" for r in ROLES)
    q = it["case_removed"] + G60.FMT
    s1 = gen(S1_PROMPT, f"{pile}\n\nQuestion:\n{q}", temp=0.6, toks=SHORT, tag=f"{key}|tensions", audit=audit)
    if s1 is None:
        return None
    route, tension = None, None
    for line in (l.strip() for l in s1.splitlines() if l.strip()):
        for r in ROLES:
            if r in line.lower():
                route, tension = r, line
                break
        if route:
            break
    reply, reply_block, blocked = None, "", False
    if route:
        reply = gen(SEATS[route],
                    f"Case:\n{it['case_removed']}\n\nYour earlier contribution:\n{contribs[route]}\n\n"
                    + FOLLOWUP.format(tension=tension), temp=0.7, toks=SHORT, tag=f"{key}|followup", audit=audit)
        if reply is not None:
            blocked = bool(blocklist_gate(reply, FABRICATION_BLOCKLIST))
            if not blocked:
                reply_block = f"--- FOLLOW-UP CLARIFICATION (from the {route} specialist) ---\n{reply}\n\n"
    s2 = gen(S2_ANSWER, f"{pile}\n\n--- YOUR TENSION LIST ---\n{s1}\n\n{reply_block}Question:\n{q}",
             temp=0.6, toks=16384, tag=f"{key}|answer", audit=audit)
    if s2 is None:
        return None
    val = parse_answer(s2)
    outcome = ("none" if val is None else "right" if correct(val, it["answer"]["right"])
               else "wrong" if correct(val, it["answer"]["wrong1"]) else "other")
    tok = it["tok"]
    row = {"run_id": key, "item": it["id"], "template": it["template"], "arm": arm, "roles": sh["roles"],
           "wrong_in_A": _has_figure(sh["seat_A"], tok["wrong1"]),
           "right_in_B": _has_figure(tb, tok["right"]), "wrong_in_B": _has_figure(tb, tok["wrong1"]),
           "tensions_both_figures": _has_figure(s1, tok["wrong1"]) and _has_figure(s1, tok["right"]),
           "route": route, "route_seat": {ra: "A", rb: "B", rc: "C"}.get(route),
           "followup_blocked": blocked, "val": val, "outcome": outcome,
           "answer_both_figures": _has_figure(s2, tok["wrong1"]) and _has_figure(s2, tok["right"]),
           "seat_B": tb, "tensions": s1, "followup": reply, "output": s2,
           "ctx_hit": any(a.get("ctx_hit") for a in audit + sh["audit"]),
           "steps": audit}
    return runlog.stamp(row, None, root=ROOT, script=Path(__file__), registration=REGISTRATION)


def stage_smoke() -> None:
    """The whole chain once, on an item Cell 63 EXCLUDED (not a registered
    item). The case is left whole and the notes quote its first sentence, so
    this checks plumbing, parsing and timing only. Nothing is written."""
    ex = json.loads(ITEMS_PATH.read_text())["excluded"][0]
    first = ex["case"].split(". ")[0] + "."
    fake = {"id": "smoke_" + ex["id"], "template": ex["template"], "case_removed": ex["case"],
            "passage": {"right": first, "wrong1": first}, "tok": {"right": "0", "wrong1": "0"},
            "answer": {"right": ex["answer"], "wrong1": -1}}
    t0 = time.time()
    sh = shared_part(fake, {}, prefix="SMOKE|")
    if not sh or sh.get("invalid"):
        raise SystemExit(f"smoke: shared part failed ({sh})")
    print(f"  plan parsed; roles {sh['roles']}; seat A {len(sh['seat_A'])} chars, seat C {len(sh['seat_C'])} chars; "
          f"{time.time()-t0:.0f}s", flush=True)
    row = arm_part(fake, sh, "redundancy", prefix="SMOKE|")
    if row is None:
        raise SystemExit("smoke: arm part failed")
    print(f"  seat B {len(row['seat_B'])} chars; route {row['route']} ({row['route_seat']}); follow-up blocked "
          f"{row['followup_blocked']}; answer val {row['val']} -> {row['outcome']} (engine answer {ex['answer']}); "
          f"ctx_hit {row['ctx_hit']}; total {time.time()-t0:.0f}s")
    for a in sh["audit"] + row["steps"]:
        print(f"    {a['step']:<10} prompt_tokens={a.get('prompt_tokens')} output_tokens={a.get('output_tokens')} "
              f"wall={a.get('wall_s')}s done={a.get('done_reason')}")


def stage_runs() -> None:
    gate = ROOT / "bench" / "analysis" / "cell63" / "measured.json"
    if not gate.exists() or not json.loads(gate.read_text()).get(MODEL, {}).get("P63.0", {}).get("pass"):
        raise SystemExit("Cell 63's clean-layout gate (P63.0) has not passed for this model: Cell 67 does not run.")
    items = load_items()
    OUT.mkdir(parents=True, exist_ok=True)
    store = json.loads(SHARED.read_text()) if SHARED.exists() else {}
    done = {r["run_id"] for r in runlog.read_jsonl(RUNS)}
    todo = [it for it in items if any(f"{it['id']}|{arm}" not in done for arm in ARMS)]
    print(f"cell67: {len(todo)} items to go", flush=True)
    t0, fails = time.time(), 0
    for n, it in enumerate(todo):
        sh = shared_part(it, store)
        if sh is not None:
            SHARED.write_text(json.dumps(store, ensure_ascii=False))
        if sh is None:
            fails += 1
            print(f"  EMPTY generation on {it['id']} (consecutive {fails})", flush=True)
            if fails >= 3:
                raise SystemExit("ABORTING — three consecutive failures; resumable.")
            continue
        if sh.get("invalid"):
            for arm in ARMS:
                if f"{it['id']}|{arm}" not in done:
                    runlog.append_jsonl(RUNS, runlog.stamp(
                        {"run_id": f"{it['id']}|{arm}", "item": it["id"], "template": it["template"],
                         "arm": arm, "invalid": sh["invalid"]}, None, root=ROOT, script=Path(__file__),
                        registration=REGISTRATION))
            continue
        for arm in ARMS:
            if f"{it['id']}|{arm}" in done:
                continue
            row = arm_part(it, sh, arm)
            if row is None:
                fails += 1
                print(f"  EMPTY generation on {it['id']}/{arm} (consecutive {fails})", flush=True)
                if fails >= 3:
                    raise SystemExit("ABORTING — three consecutive failures; resumable.")
                continue
            fails = 0
            runlog.append_jsonl(RUNS, row)
        el = time.time() - t0
        print(f"  {n+1}/{len(todo)} items, {el/60:.0f}m, ~{el/(n+1)*(len(todo)-n-1)/3600:.1f}h left", flush=True)
    print("cell67 runs complete")


def _tdiff(rows, a_arm, b_arm, pred) -> dict | None:
    """Template-level mean of item-level differences (arm a minus arm b)."""
    by_item = collections.defaultdict(dict)
    for r in rows:
        by_item[r["item"]][r["arm"]] = (r["template"], float(pred(r)))
    by_t = collections.defaultdict(list)
    for d in by_item.values():
        if a_arm in d and b_arm in d:
            by_t[d[a_arm][0]].append(d[a_arm][1] - d[b_arm][1])
    v = [st.mean(x) for x in by_t.values()]
    if len(v) < 2:
        return None
    m, lo, hi = t_interval(v)
    return {"mean": m, "lo": lo, "hi": hi, "p": sign_flip_p(v), "k": len(v), "items": sum(len(x) for x in by_t.values())}


def stage_measure() -> None:
    all_rows = runlog.read_jsonl(RUNS)
    invalid = [r for r in all_rows if r.get("invalid")]
    rows = [r for r in all_rows if not r.get("invalid") and not r.get("ctx_hit")]
    print("=" * 78)
    print("CELL 67 — the wrong figure in the live chain")
    print("=" * 78)
    print(f"runs {len(all_rows)}; plan could not be parsed {len(invalid)}; set aside for a context-limit hit "
          f"{len(all_rows) - len(invalid) - len(rows)}")
    result = {"n": len(rows)}
    print(f"\n  {'arm':<12}{'n':>4}{'right':>8}{'wrong':>8}{'other':>8}{'no answer':>11}{'both figures in answer':>24}")
    for arm in ARMS:
        ra = [r for r in rows if r["arm"] == arm]
        c = collections.Counter(r["outcome"] for r in ra)
        if ra:
            print(f"  {arm:<12}{len(ra):>4}{c['right']/len(ra):>8.3f}{c['wrong']/len(ra):>8.3f}{c['other']/len(ra):>8.3f}"
                  f"{c['none']/len(ra):>11.3f}{sum(r['answer_both_figures'] for r in ra)/len(ra):>24.3f}")
            result[arm] = {"n": len(ra), **{k: c[k] for k in ("right", "wrong", "other", "none")},
                           "both_figures": sum(r["answer_both_figures"] for r in ra)}
    bare = [r for r in rows if r["arm"] == "bare"]
    red = [r for r in rows if r["arm"] == "redundancy"]
    conv_a = sum(r["wrong_in_A"] for r in bare) / len(bare) if bare else float("nan")
    conv_b = sum(r["right_in_B"] for r in red) / len(red) if red else float("nan")
    gate = conv_a >= CONVEY_BAR and conv_b >= CONVEY_BAR
    print(f"\nP67.0  did the figures reach the specialists' texts? wrong figure in A's text {conv_a:.3f}; "
          f"right figure in B's text (redundancy arm) {conv_b:.3f}  (bar {CONVEY_BAR} each) -> {'PASSES' if gate else 'FAILS'}")
    p1 = _tdiff(rows, "bare", "redundancy", lambda r: r["outcome"] == "wrong")
    p2 = _tdiff(rows, "redundancy", "bare", lambda r: r["outcome"] == "right")

    def fmt(d):
        return "n/a" if not d else (f"{d['mean']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}]  sign-flip p = {d['p']:.4f}  "
                                    f"(k = {d['k']} templates, {d['items']} items)")
    print(f"\nP67.1  final answer follows the wrong figure, bare minus redundancy: {fmt(p1)}")
    print(f"P67.2  final answer is right, redundancy minus bare:               {fmt(p2)}")
    by_t = collections.defaultdict(list)
    for r in red:
        by_t[r["template"]].append(float(r["answer_both_figures"]))
    v = [st.mean(x) for x in by_t.values()]
    p3 = None
    if len(v) >= 2:
        m, lo, hi = t_interval(v)
        p3 = {"mean": m, "lo": lo, "hi": hi, "k": len(v)}
        print(f"P67.3  redundancy arm, final answer mentions both figures: {m:.3f} [{lo:.3f}, {hi:.3f}]  (k = {len(v)} templates)")
    print("\nVERDICT LINES (as registered)")
    if not gate:
        print("  P67.0: FAILS — the figures did not reach the specialists' texts often enough")
        for pid in ("P67.1", "P67.2", "P67.3"):
            print(f"  {pid}: NOT EVALUABLE — the figures did not reach the editor often enough")
    else:
        print("  P67.0: PASSES")
        for pid, d in (("P67.1", p1), ("P67.2", p2)):
            ok = d and d["mean"] > 0 and d["p"] < 0.05
            print(f"  {pid}: {'SUPPORTED' if ok else 'FALSIFIED'} — {fmt(d)}")
        if p3:
            word = "SUPPORTED" if p3["hi"] < 0.5 else "FALSIFIED" if p3["lo"] > 0.5 else "NOT EVALUABLE"
            print(f"  P67.3: {word} — expectation: below 0.5")
    print("\ndescriptive")
    both = [r for r in red if r["wrong_in_A"] and r["right_in_B"]]
    c = collections.Counter(r["outcome"] for r in both)
    if both:
        print(f"  redundancy arm, runs where both figures reached the specialists' texts (n = {len(both)}): "
              f"right {c['right']/len(both):.3f}, wrong {c['wrong']/len(both):.3f}, other {c['other']/len(both):.3f}, none {c['none']/len(both):.3f}")
    for arm, ra in (("bare", bare), ("redundancy", red)):
        if ra:
            print(f"  {arm}: tension list names both figures {sum(r['tensions_both_figures'] for r in ra)/len(ra):.3f}; "
                  f"follow-up went to A {sum(r['route_seat']=='A' for r in ra)/len(ra):.3f}, "
                  f"B {sum(r['route_seat']=='B' for r in ra)/len(ra):.3f}, C {sum(r['route_seat']=='C' for r in ra)/len(ra):.3f}, "
                  f"nobody {sum(r['route_seat'] is None for r in ra)/len(ra):.3f}; "
                  f"B's text shows the wrong figure {sum(r['wrong_in_B'] for r in ra)/len(ra):.3f}")
    for seat_ in ("A", "B"):
        v = [r for r in red if r["route_seat"] == seat_]
        if v:
            c = collections.Counter(r["outcome"] for r in v)
            print(f"  redundancy, follow-up to {seat_} (n = {len(v)}): right {c['right']/len(v):.3f}, wrong {c['wrong']/len(v):.3f}")
    result.update({"P67.0": {"wrong_in_A": conv_a, "right_in_B": conv_b, "pass": gate},
                   "P67.1": p1, "P67.2": p2, "P67.3": p3})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "measured.json").write_text(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    {"smoke": stage_smoke, "runs": stage_runs, "measure": stage_measure}[sys.argv[1] if len(sys.argv) > 1 else "measure"]()
