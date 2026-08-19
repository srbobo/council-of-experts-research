"""Cell 45 — design (b) stage one: seat-side deferral discrimination.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 45 PRE-REGISTRATION".
Tasks frozen in docs/CELL45_TASKS.json before any run.

Same sub-question, two recipients: the seat whose domain holds the
deciding consideration (IN) and a seat whose domain does not (OUT).
The estimand is the flag-rate GAP, not the flag rate — a seat that flags
everywhere is performing compliance (the C41 outcome), and a seat that
never flags has no deferral behavior; both falsify.

Run:  .venv/bin/python train/run_cell45_deferral.py runs
      .venv/bin/python train/run_cell45_deferral.py measure
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

OUT_DIR = ROOT / "bench" / "analysis" / "cell45"
RUNS = ROOT / "bench" / "runs" / "cell45_deferral.jsonl"
ITEMS = {it["id"]: it for it in
         json.loads((ROOT / "docs" / "CELL44_ITEMS.json").read_text())["items"]}
TASKS = json.loads((ROOT / "docs" / "CELL45_TASKS.json").read_text())["tasks"]
WRITER = "gpt-oss:20b"
ROLES = ("healthcare", "legal", "finance")
DOMAIN_WORDS = ("healthcare", "legal", "finance", "clinical", "medical")
CONDITIONS = ("out", "in")
REPEATS = 6

# Roster-only awareness (never sibling outputs — the v2 lane-bleed lesson).
# The CONSULT token is a dictated FORM; the measured outcome is WHERE and
# WHETHER it fires, which the instruction does not and cannot dictate.
SEAT_PROMPT = (
    "You are the {role} analyst advising a decision-maker. Two other "
    "specialist analysts are consulted separately on this engagement: "
    "{others}. Answer the question below from your own domain.\n\n"
    "If, while answering, you judge that the DECIDING consideration for "
    "this question lies in one of the other analysts' domains rather than "
    "yours, still give your best answer, and then add a final line in "
    "exactly this form naming that domain:\nCONSULT: <domain>\n"
    "If the deciding considerations are within your own domain, do not "
    "add that line.")

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def guard_tasks() -> None:
    problems = []
    for t in TASKS:
        low = t["subq"].lower()
        for w in DOMAIN_WORDS:
            if w in low:
                problems.append(f"item {t['item']}: domain word {w!r} in subq")
    if problems:
        for p in problems:
            print("  " + p)
        raise SystemExit("TASK GUARDS FAILED")
    print(f"task guards: PASS ({len(TASKS)} tasks, no domain words)")


def preflight() -> None:
    from gst.registry import gate_GE, load_frozen
    reg = load_frozen(ROOT / "docs" / "DICTATION_REGISTRY.json")
    viol = gate_GE({"SEAT_PROMPT": SEAT_PROMPT.format(role="X", others="Y")},
                   reg, construct_only=True)
    if viol:
        raise SystemExit("GATE G-E FAILED: " + "; ".join(viol))
    t = chat(WRITER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED — backend unreachable.")
    print("preflight: gate G-E PASS, backend responds")


def parse_flag(txt: str) -> str | None:
    """Named domain from a CONSULT line, else None. Literal token parse."""
    t = _THINK.sub("", txt)
    m = re.findall(r"CONSULT:\s*([A-Za-z]+)", t)
    if not m:
        return None
    d = m[-1].lower()
    return d if d in ROLES else "OTHER"


def stage_runs() -> None:
    from examples.test_cases import get_case
    preflight()
    guard_tasks()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done = set()
    if RUNS.exists():
        for l in RUNS.read_text().splitlines():
            if l.strip():
                done.add(json.loads(l)["run_id"])
    todo = [(t, c, r) for t in TASKS for c in CONDITIONS for r in range(REPEATS)
            if f"i{t['item']}__{c}__r{r}" not in done]
    print(f"cell45: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0, fails = time.time(), 0
    with RUNS.open("a") as fh:
        for k, (t, cond, rep) in enumerate(todo):
            it = ITEMS[t["item"]]
            role = it["seat_B"] if cond == "in" else it["seat_A"]
            others = " and ".join(f"a {r} analyst" for r in ROLES if r != role)
            body = (f"Situation:\n{get_case(it['case']).prompt}\n\n"
                    f"Question:\n{t['subq']}")
            txt = None
            for attempt in range(3):
                txt = chat(WRITER, SEAT_PROMPT.format(role=role, others=others),
                           body, temperature=0.6, max_tokens=4096)
                if txt and txt.strip():
                    break
                time.sleep(5 * (attempt + 1))
            if not txt or not txt.strip():
                fails += 1
                print(f"  EMPTY i{t['item']}/{cond}/r{rep} "
                      f"(consecutive {fails})", flush=True)
                if fails >= 5:
                    raise SystemExit("ABORTING — backend down; resumable.")
                continue
            fails = 0
            fh.write(json.dumps({
                "run_id": f"i{t['item']}__{cond}__r{rep}", "item": t["item"],
                "cond": cond, "role": role, "home": it["route_domain"],
                "repeat": rep, "flag": parse_flag(txt),
                "chars": len(txt), "output": txt}, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 6 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print("cell45 runs complete")


def stage_measure() -> None:
    import random
    from gst.stats import wilson_ci
    rng = random.Random(0)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]

    def flagged(r):
        return r["flag"] is not None

    items_ = sorted({r["item"] for r in rows})
    by = {}
    for r in rows:
        by.setdefault((r["item"], r["cond"]), []).append(r)

    def rate(cond, pred):
        v = [r for r in rows if r["cond"] == cond]
        return sum(1 for r in v if pred(r)), len(v)

    def cluster_diff(pred):
        ds = []
        for _ in range(5000):
            s = [items_[rng.randrange(len(items_))] for _ in items_]
            vo = [pred(r) for i in s for r in by.get((i, "out"), [])]
            vi = [pred(r) for i in s for r in by.get((i, "in"), [])]
            if vo and vi:
                ds.append(sum(vo) / len(vo) - sum(vi) / len(vi))
        ds.sort()
        return ds[int(.025 * len(ds))], ds[int(.975 * len(ds))]

    print("=" * 74)
    print("CELL 45 — seat-side deferral discrimination")
    print("=" * 74)
    print("P45.3 RAW TABLE (mandatory, before any verdict)")
    for cond in CONDITIONS:
        v = [r for r in rows if r["cond"] == cond]
        k = sum(1 for r in v if flagged(r))
        print(f"  {cond.upper():<4} n={len(v):<4} flagged {k} "
              f"({k/len(v):.2f})   mean chars "
              f"{sum(r['chars'] for r in v)//len(v)}")
    print("  per-item OUT/IN flag counts:")
    for i in items_:
        vo, vi = by.get((i, "out"), []), by.get((i, "in"), [])
        print(f"    item {i}: OUT {sum(1 for r in vo if flagged(r))}/{len(vo)}"
              f"   IN {sum(1 for r in vi if flagged(r))}/{len(vi)}")

    ko, no = rate("out", flagged)
    ki, ni = rate("in", flagged)
    lo, hi = cluster_diff(flagged)
    print()
    print("P45.1 DISCRIMINATION — flag rate OUT vs IN")
    print(f"  OUT {ko}/{no} = {ko/no:.3f}   IN {ki}/{ni} = {ki/ni:.3f}   "
          f"gap CI [{lo:+.3f},{hi:+.3f}]")
    if lo > 0:
        print("  P45.1: SUPPORTED — the flag discriminates")
    elif ko/no >= 0.8 and ki/ni >= 0.8:
        print("  P45.1: FALSIFIED — ceiling-ceiling: performative compliance "
              "(the C41 outcome)")
    elif ko/no <= 0.2 and ki/ni <= 0.2:
        print("  P45.1: FALSIFIED — floor-floor: no deferral behavior")
    else:
        print("  P45.1: FALSIFIED — no discriminating gap")

    out_flags = [r for r in rows if r["cond"] == "out" and flagged(r)]
    correct = sum(1 for r in out_flags if r["flag"] == r["home"])
    print()
    print("P45.2 ROUTING ACCURACY — among OUT flags, named domain == home")
    if out_flags:
        wlo, whi = wilson_ci(correct, len(out_flags))
        print(f"  {correct}/{len(out_flags)} = {correct/len(out_flags):.3f} "
              f"[{wlo:.3f},{whi:.3f}]  (chance = 0.5, two alternatives)")
        print(f"  P45.2: {'SUPPORTED' if wlo > 0.5 else 'FALSIFIED or below power'}")
    else:
        print("  NOT EVALUABLE — no OUT-condition flags")
    (OUT_DIR / "measured.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k != "output"} for r in rows], indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "runs"
    {"runs": stage_runs, "measure": stage_measure}[stage]()
