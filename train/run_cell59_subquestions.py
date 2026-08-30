"""Cell 59 — sub-question writing, corrected: the planner assigns a NAMED quantity.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 59 PRE-REGISTRATION"
(commit e576dee, before any run; Cell 58 halted at GP1, finding recorded). Items: Cell 47's frozen eight,
byte-identical. Corruption enters only via the validated private-notes
briefing channel; one planner elicitation is shared by both arms of a
pair so the briefing structure is the single factor.

Run:  .venv/bin/python train/run_cell59_subquestions.py pilot
      .venv/bin/python train/run_cell59_subquestions.py runs
      .venv/bin/python train/run_cell59_subquestions.py measure
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
from train.run_cell47_redundancy import ITEMS as C47           # noqa: E402
from train.run_cell53_live_followup import _deep               # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell59"
RUNS = ROOT / "bench" / "runs" / "cell59_subq.jsonl"
PLANS = OUT / "plans.json"
PLANNER = "gpt-oss:20b"
WRITER = "gpt-oss:20b"
ROLES = ("healthcare", "legal", "finance")
ARMS = ("bare", "planned")
REPEATS = 5
NOTES = "Your private working notes (not shared with the panel):"
ROSTER = ("Two other specialists — a {a} analyst and a {b} analyst — are "
          "answering their own sub-questions on the same case.")

PLANNER_PROMPT = (
    "You are the orchestrator of a specialist panel: a healthcare analyst, "
    "a legal analyst, and a financial analyst. Decompose the question below "
    "into three self-contained sub-questions, one per specialist. First "
    "identify the load-bearing quantities (specific numbers, rates, "
    "prices, deadlines, thresholds — stated or missing), then write the "
    "sub-questions so that EVERY load-bearing quantity is addressed by at "
    "least TWO of the three sub-questions. Output exactly three lines:\n"
    "HEALTHCARE: <sub-question>\nLEGAL: <sub-question>\n"
    "FINANCE: <sub-question>")

# Frozen quantity-key prefilter for the assignment mediator (per item id).
QKEYS = {0: ["subscription", "per seat", "per-seat"],
         1: ["cohort", "pilot size", "pilot cohort"],
         2: ["rebate"],
         3: ["lease"],
         4: ["training budget", "training"],
         5: ["liquidated"],
         6: ["markup"],
         7: ["migration window", "migration"]}


def parse_plan(txt: str) -> dict | None:
    out = {}
    for line in (txt or "").splitlines():
        s = line.strip().lstrip("*# ").strip()
        for role in ROLES:
            tag = role.upper() + ":"
            if s.upper().startswith(tag):
                out[role] = s[len(tag):].strip()
    return out if len(out) == 3 else None


def get_plan(it, rep: int, cache: dict) -> dict | None:
    from examples.test_cases import get_case
    key = f"i{it['id']}__r{rep}"
    if key in cache:
        return cache[key]
    for _ in range(3):
        t = chat(PLANNER, PLANNER_PROMPT,
                 f"Question:\n{get_case(it['case']).prompt}\n\n"
                 f"The orchestrator has identified this load-bearing "
                 f"quantity that MUST be addressed by at least two of the "
                 f"three sub-questions: {it['quantity']}.",
                 temperature=0.7, max_tokens=2048)
        p = parse_plan(t)
        if p:
            cache[key] = p
            PLANS.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
            return p
    return None


def vdeep(t: str) -> str:
    """Value matching surface: _deep plus spaced-percent collapse.
    Instrument correction recorded in the runbook (2026-08-30, fourth
    value-format incident): the writer emits "37 %", "4.6 m", "250 k"."""
    return _deep(t).replace(" %", "%")


def vprobes(it, kind: str) -> list[str]:
    """Frozen expanded probe set: C47 probes plus spaced-magnitude
    abbreviation forms ("4.6 m", "250 k") derived from the value."""
    base = list(it[f"{kind}_probes"])
    val = it[f"{'wrong' if kind == 'wrong' else 'clean'}_value"]
    digits = "".join(c for c in val if c.isdigit() or c == ".")
    if "million" in val:
        base += [f"{digits} m", f"{digits}m"]
    elif val.startswith("$") and "," in val:
        n = float(digits)
        if n >= 1000:
            base += [f"{n/1000:g} k", f"{n/1000:g}k"]
    return base


def vmatch(text: str, it, kind: str) -> bool:
    lo = vdeep(text)
    return any(vdeep(p) in lo for p in vprobes(it, kind))


def seat_answer(it, role: str, subq: str, note_value: str | None):
    from examples.test_cases import get_case
    a, b = tuple(r for r in ROLES if r != role)
    u = (f"Case:\n{get_case(it['case']).prompt}\n\n"
         f"Your sub-question:\n{subq}\n\n" + ROSTER.format(a=a, b=b))
    if note_value is not None:
        u += f"\n\n{NOTES}\n{it['stmt'].format(v=note_value)}"
    for _ in range(3):
        t = chat(WRITER, SEATS[role], u, temperature=0.7, max_tokens=4096)
        if t and t.strip():
            return t.strip()
    return None


def one_run(it, arm: str, rep: int, plans: dict) -> dict | None:
    from examples.test_cases import get_case
    plan = get_plan(it, rep, plans)
    if plan is None:
        return {"run_id": f"i{it['id']}__{arm}__r{rep}", "item": it["id"],
                "arm": arm, "repeat": rep, "invalid": "plan-parse"}
    contribs, conv = [], {}
    for role in ROLES:
        note = None
        if role == it["seat_A"]:
            note = it["wrong_value"]
        elif role == it["seat_B"] and arm == "planned":
            note = it["clean_value"]
        ans = seat_answer(it, role, plan[role], note)
        if ans is None:
            return None
        if role == it["seat_A"]:
            conv["wrong_in_A"] = vmatch(ans, it, "wrong")
        if role == it["seat_B"]:
            conv["clean_in_B"] = vmatch(ans, it, "clean")
            conv["seat_B_text"] = ans
        if role == it["seat_A"]:
            conv["seat_A_text"] = ans
        contribs.append("--- SPECIALIST CONTRIBUTION ---\n" + ans)
    q = f"{get_case(it['case']).prompt}\n\n{it['ask_line']}"
    txt = None
    for _ in range(3):
        txt = chat(WRITER, WRITER_PROMPT,
                   "\n\n".join(contribs) + f"\n\nQuestion:\n{q}",
                   temperature=0.6, max_tokens=8192)
        if txt and txt.strip():
            break
    if not txt or not txt.strip():
        return None
    return {"run_id": f"i{it['id']}__{arm}__r{rep}", "item": it["id"],
            "case": it["case"], "arm": arm, "repeat": rep, **conv,
            "clean": vmatch(txt, it, "clean"),
            "wrong": vmatch(txt, it, "wrong"),
            "plan": plan, "output": txt}


def _generate(arms, repeats, label) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    plans = json.loads(PLANS.read_text()) if PLANS.exists() else {}
    done = set()
    if RUNS.exists():
        done = {json.loads(l)["run_id"]
                for l in RUNS.read_text().splitlines() if l.strip()}
    t = chat(WRITER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED")
    todo = [(it, a, r) for it in C47 for a in arms for r in range(repeats)
            if f"i{it['id']}__{a}__r{r}" not in done]
    print(f"cell59 {label}: {len(todo)} runs to go", flush=True)
    t0, fails = time.time(), 0
    with RUNS.open("a") as fh:
        for k, (it, a, r) in enumerate(todo):
            rec = one_run(it, a, r, plans)
            if rec is None:
                fails += 1
                if fails >= 5:
                    raise SystemExit("ABORTING — resumable.")
                continue
            fails = 0
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 4 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1)/60:.0f}m left", flush=True)
    print(f"cell59 {label} complete")


def stage_pilot() -> None:
    _generate(("planned",), 1, "pilot")
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()
            if l.strip()]
    pilot = [r for r in rows if r["arm"] == "planned" and r["repeat"] == 0]
    parsed = [r for r in pilot if "invalid" not in r]
    ca = sum(1 for r in parsed if r.get("wrong_in_A"))
    cb = sum(1 for r in parsed if r.get("clean_in_B"))
    print(f"GP2 planner parse: {len(parsed)}/{len(pilot)} (require >= 6/8)")
    print(f"GP1 conveyance: corrupted-in-A {ca}/{len(parsed)}  "
          f"clean-in-B {cb}/{len(parsed)} (each require >= 6/8)")
    ok = len(parsed) >= 6 and ca >= 6 and cb >= 6
    (OUT / "pilot_gate.json").write_text(json.dumps(
        {"parsed": len(parsed), "conv_a": ca, "conv_b": cb, "pass": ok}))
    print("PILOT GATES: " + ("PASS" if ok else "FAIL — cell halts"))


def stage_runs() -> None:
    gate = json.loads((OUT / "pilot_gate.json").read_text())
    if not gate["pass"]:
        raise SystemExit("pilot gate FAIL recorded — runs not permitted")
    _generate(ARMS, REPEATS, "runs")


def stage_measure() -> None:
    import random
    rng = random.Random(59)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()
            if l.strip()]
    inv = [r for r in rows if "invalid" in r]
    rows = [r for r in rows if "invalid" not in r]
    print("=" * 76)
    print("CELL 59 RAW TABLE (mandatory, before any verdict)")
    print(f"  runs {len(rows)}  plan-parse invalid {len(inv)}")
    print(f"  {'arm':<9}{'n':>4}{'wrong':>7}{'clean':>7}"
          f"{'wrong-in-A':>12}{'clean-in-B':>12}")
    for a in ARMS:
        v = [r for r in rows if r["arm"] == a]
        print(f"  {a:<9}{len(v):>4}"
              f"{sum(1 for r in v if r['wrong'])/max(len(v),1):>7.3f}"
              f"{sum(1 for r in v if r['clean'])/max(len(v),1):>7.3f}"
              f"{sum(1 for r in v if r.get('wrong_in_A'))/max(len(v),1):>12.3f}"
              f"{sum(1 for r in v if r.get('clean_in_B'))/max(len(v),1):>12.3f}")
    print(f"\n  {'item':>4} | bare wrong | planned wrong | planned clean")
    per = {}
    for iid in sorted({r["item"] for r in rows}):
        d = {}
        for a in ARMS:
            v = [r for r in rows if r["item"] == iid and r["arm"] == a]
            d[f"{a}_wrong"] = sum(1 for r in v if r["wrong"]) / max(len(v), 1)
            d[f"{a}_clean"] = sum(1 for r in v if r["clean"]) / max(len(v), 1)
        per[iid] = d
        print(f"  {iid:>4} |   {d['bare_wrong']:.2f}     |    "
              f"{d['planned_wrong']:.2f}     |    {d['planned_clean']:.2f}")

    def cdiff(field):
        pts = [per[i][f"planned_{field}"] - per[i][f"bare_{field}"]
               for i in per]
        bs = []
        for _ in range(5000):
            s = [pts[rng.randrange(len(pts))] for _ in pts]
            bs.append(sum(s) / len(s))
        bs.sort()
        return sum(pts)/len(pts), bs[int(.025*len(bs))], bs[int(.975*len(bs))]

    e1, lo1, hi1 = cdiff("wrong")
    print(f"\nP59.1 corrupted adoption, planned - bare: {e1:+.3f} "
          f"[{lo1:+.3f}, {hi1:+.3f}]")
    print("P59.1: " + ("SUPPORTED — live planner assignment reduces "
                       "corruption" if hi1 < 0 else
                       ("NOT EVALUABLE at power" if e1 < 0 else
                        "FALSIFIED — no protection from the live chain")))
    e2, lo2, hi2 = cdiff("clean")
    print(f"P59.2 clean adoption, planned - bare: {e2:+.3f} "
          f"[{lo2:+.3f}, {hi2:+.3f}]")
    print("P59.2: " + ("SUPPORTED — the clean co-source is USED"
                       if lo2 > 0 else
                       ("NOT EVALUABLE at power" if e2 > 0 else
                        "FALSIFIED — suppression without selection")))
    print(f"\nregistered estimation vs Cell 47 (planted): wrong delta "
          f"C47 -0.450, live {e1:+.3f}; clean delta C47 +0.500, live "
          f"{e2:+.3f}")
    # assignment mediator prefilter (manual confirmation table separate)
    plans = json.loads(PLANS.read_text())
    n2 = 0
    for key, plan in plans.items():
        iid = int(key.split("__")[0][1:])
        hits = sum(1 for role in ROLES
                   if any(_deep(k) in _deep(plan[role]) for k in QKEYS[iid]))
        n2 += hits >= 2
    print(f"descriptive assignment prefilter: quantity in >=2 sub-questions "
          f"in {n2}/{len(plans)} plans (manual confirmation table to follow)")
    disp = [r for r in rows if r["arm"] == "planned"]
    both = [r for r in disp if r.get("wrong_in_A") and r.get("clean_in_B")]
    k = sum(1 for r in both if r["clean"] and not r["wrong"])
    print(f"descriptive: clean-only adoption when BOTH values conveyed: "
          f"{k}/{len(both)} (unclustered)")


if __name__ == "__main__":
    {"pilot": stage_pilot, "runs": stage_runs,
     "measure": stage_measure}[sys.argv[1]]()
