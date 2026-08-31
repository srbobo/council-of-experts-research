"""Integration demonstration — the assembled harness, end-to-end.

Registered: RUNBOOK_PAPER_HARDENING.md "INTEGRATION RUN" (commit
df957e6). Descriptive telemetry only; no verdicts.

Run:  .venv/bin/python train/run_integration_demo.py
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                          # noqa: E402
from train.run_cell30_descaffold import (DEFS, JUDGE_PROMPT,   # noqa: E402
                                         SEATS, WRITER_PROMPT)
from train.run_cell44_reconsult import S1_PROMPT, S2_PROMPT    # noqa: E402
from train.run_cell57_planner import PLANNER_PROMPT as IDENTIFY  # noqa: E402
from train.run_cell59_subquestions import parse_plan           # noqa: E402
from gst.gates import FABRICATION_BLOCKLIST, blocklist_gate, fold  # noqa: E402

OUT = ROOT / "bench" / "analysis" / "integration"
MODEL = "gpt-oss:20b"
JUDGES = ("gpt-oss:20b", "qwen2.5:7b-instruct")
ROLES = ("healthcare", "legal", "finance")
CASES = ("case_3_capitated_risk_contract", "case_l1_l1a", "case_l4_l4b")
SCREEN = ("case_8_trigger_light_hand_hygiene",
          "case_7_trigger_light_baseline")
SCREEN_PROMPT = ("You are an analyst. Give a substantive written analysis "
                 "of the situation below for a decision-maker. Be specific "
                 "and concrete.")
ROSTER = ("Two other specialists — a {a} analyst and a {b} analyst — are "
          "answering their own sub-questions on the same case.")
SUBQ_PROMPT = (
    "You are the orchestrator of a specialist panel: a healthcare analyst, "
    "a legal analyst, and a financial analyst. Decompose the question "
    "below into three self-contained sub-questions, one per specialist. "
    "The orchestrator has identified these load-bearing quantities, and "
    "EVERY one must be addressed by at least TWO of the three "
    "sub-questions:\n{quantities}\n\nOutput exactly three lines:\n"
    "HEALTHCARE: <sub-question>\nLEGAL: <sub-question>\n"
    "FINANCE: <sub-question>")
FOLLOWUP = ("The lead's tension list includes this item: \"{tension}\". "
            "What specifically drives your position on this? If a "
            "concrete constraint or mechanism is behind it, state it and "
            "what it implies for the final recommendation.")
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def gen(system, user, temp=0.7, toks=4096, model=MODEL):
    for attempt in range(6):
        if attempt:
            time.sleep(10 * attempt)
        t = chat(model, system, user, temperature=temp, max_tokens=toks)
        if t and t.strip():
            return _THINK.sub("", t).strip()
    raise SystemExit("generation failed 6x")


def seat_gate(tel):
    from examples.test_cases import get_case
    chars = []
    for case in SCREEN:
        for _ in range(6):
            chars.append(len(gen(SCREEN_PROMPT, get_case(case).prompt)))
    tel["seat_gate"] = {"model": MODEL, "screen_chars": chars,
                        "pass": all(c >= 800 for c in chars)}
    print(f"  seating gate: min {min(chars)} -> "
          f"{'PASS' if tel['seat_gate']['pass'] else 'FAIL'}", flush=True)
    if not tel["seat_gate"]["pass"]:
        raise SystemExit("seat model failed S1 — not seated")


def extract_caveats(text):
    prompt = JUDGE_PROMPT.format(
        defs="\n".join(f"- {k}: {v}" for k, v in DEFS.items()),
        text=text[:12000])
    per_judge = []
    for j in JUDGES:
        t = gen("Reply with STRICT JSON only.", prompt, temp=0.0,
                toks=2048, model=j)
        try:
            s = t[t.index("{"):t.rindex("}") + 1]
            per_judge.append(json.loads(s))
        except (ValueError, json.JSONDecodeError):
            per_judge.append({})
    out = []
    for fam in DEFS:
        a, b = (pj.get(fam, {}) for pj in per_judge)
        if a.get("present") and b.get("present"):
            q = (a.get("quote") or "").strip()
            if q and fold(q) in fold(text):
                out.append(q)
    return out


def run_case(case, tel):
    from examples.test_cases import get_case
    t0 = time.time()
    q = get_case(case).prompt
    ct = {"case": case}
    # planner half 1: identify
    ids = gen(IDENTIFY, f"Question:\n{q}", toks=2048)
    quants = [l.strip() for l in ids.splitlines() if l.strip()][:6]
    ct["quantities"] = quants
    # planner half 2: sub-questions
    plan = None
    for _ in range(3):
        plan = parse_plan(gen(
            "Follow the output format exactly.",
            SUBQ_PROMPT.format(quantities="\n".join(quants))
            + f"\n\nQuestion:\n{q}", toks=2048))
        if plan:
            break
    ct["plan"] = plan
    # coverage self-check (rough, mechanical): digits of each quantity
    # line found in >=2 sub-questions
    cov = 0
    for qu in quants:
        toks_ = [w for w in fold(qu).split() if len(w) >= 6][:3]
        if toks_ and sum(1 for r in ROLES
                         if any(w in fold(plan[r]) for w in toks_)) >= 2:
            cov += 1
    ct["coverage_selfcheck"] = f"{cov}/{len(quants)}"
    # seats
    contribs, caveats = {}, {}
    for role in ROLES:
        a, b = tuple(r for r in ROLES if r != role)
        ans = gen(SEATS[role],
                  f"Case:\n{q}\n\nYour sub-question:\n{plan[role]}\n\n"
                  + ROSTER.format(a=a, b=b))
        contribs[role] = ans
        caveats[role] = extract_caveats(ans)
        print(f"    seat {role}: {len(ans)} chars, "
              f"{len(caveats[role])} caveats", flush=True)
    ct["seat_chars"] = {r: len(contribs[r]) for r in ROLES}
    ct["degenerate"] = [r for r in ROLES if len(contribs[r]) < 800]
    ct["caveat_counts"] = {r: len(caveats[r]) for r in ROLES}
    pile = "\n\n".join(
        f"--- {r.upper()} SPECIALIST CONTRIBUTION ---\n{contribs[r]}"
        for r in ROLES)
    # lead stage 1: tension list
    s1 = gen(S1_PROMPT, f"{pile}\n\nQuestion:\n{q}", temp=0.6, toks=2048)
    tensions = [l.strip() for l in s1.splitlines() if l.strip()]
    ct["n_tensions"] = len(tensions)
    # orchestrator routing: first tension naming a role
    route, tension = None, None
    for line in tensions:
        for r in ROLES:
            if r in line.lower():
                route, tension = r, line
                break
        if route:
            break
    ct["dispatch"] = {"route": route, "tension": tension}
    reply_block = ""
    if route:
        reply = gen(SEATS[route],
                    f"Case:\n{q}\n\nYour earlier contribution:\n"
                    f"{contribs[route]}\n\n"
                    + FOLLOWUP.format(tension=tension), toks=2048)
        hits = blocklist_gate(reply, FABRICATION_BLOCKLIST)
        ct["dispatch"]["reply_chars"] = len(reply)
        ct["dispatch"]["blocklist_hits"] = hits
        ct["dispatch"]["content_gate"] = "NOT-DEPLOYABLE/FLAGGED"
        if hits:
            ct["dispatch"]["delivered"] = False
            print(f"    reply DROPPED by blocklist: {hits}", flush=True)
        else:
            ct["dispatch"]["delivered"] = True
            reply_block = (f"--- FOLLOW-UP CLARIFICATION (from the {route} "
                           f"specialist, at the lead's request; delivered "
                           f"flagged: content gate not deployable) ---\n"
                           f"{reply}\n\n")
    # lead stage 2: synthesis
    s2 = gen(S2_PROMPT,
             f"{pile}\n\n--- YOUR TENSION LIST ---\n{s1}\n\n{reply_block}"
             f"Question:\n{q}", temp=0.6, toks=8192)
    # assembly: prose + appendix
    all_cavs = [c for r in ROLES for c in caveats[r]]
    artifact = s2
    if all_cavs:
        artifact += ("\n\n---\nASSUMPTIONS & CAVEATS (as stated by the "
                     "specialist contributors)\n"
                     + "\n".join(f"- {c}" for c in all_cavs))
    ct["appendix_caveats"] = len(all_cavs)
    ct["artifact_chars"] = len(artifact)
    ct["seconds"] = round(time.time() - t0)
    (OUT / f"{case}.artifact.md").write_text(artifact)
    (OUT / f"telemetry_{case}.json").write_text(json.dumps(ct, indent=1))
    tel["cases"].append(ct)
    print(f"  {case}: done in {ct['seconds']}s — artifact "
          f"{ct['artifact_chars']} chars, {len(all_cavs)} caveats, "
          f"dispatch={route}", flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tel = {"registered": "df957e6", "model": MODEL, "cases": []}
    print("integration demo: seating gate", flush=True)
    seat_gate(tel)
    for case in CASES:
        done = OUT / f"telemetry_{case}.json"
        if done.exists():
            tel["cases"].append(json.loads(done.read_text()))
            print(f"integration demo: {case} (cached)", flush=True)
            continue
        print(f"integration demo: {case}", flush=True)
        run_case(case, tel)
    (OUT / "telemetry.json").write_text(json.dumps(tel, indent=1))
    print("integration demo complete — telemetry written")


if __name__ == "__main__":
    main()
