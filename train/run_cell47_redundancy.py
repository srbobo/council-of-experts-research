"""Cell 47 (L2) — the redundancy-planner lift.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 47 (L2)".
Items frozen in docs/CELL47_ITEMS.json before any run.

One factor: whether the orchestrator assigned the load-bearing quantity to
a second seat carrying the clean value. Seat A carries the corrupted value
in BOTH arms; the ask-line (identical in both arms) makes the outcome
attainable and names the quantity, never a value.

Run:  .venv/bin/python train/run_cell47_redundancy.py pilot
      .venv/bin/python train/run_cell47_redundancy.py runs
      .venv/bin/python train/run_cell47_redundancy.py measure
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
from train.run_cell30_descaffold import WRITER_PROMPT          # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell47"
RUNS = ROOT / "bench" / "runs" / "cell47_redundancy.jsonl"
SEATS_PATH = ROOT / "bench" / "analysis" / "cell41" / "seats.json"
ITEMS = json.loads((ROOT / "docs" / "CELL47_ITEMS.json").read_text())["items"]
WRITER = "gpt-oss:20b"
ROLES = ("healthcare", "legal", "finance")
ARMS = ("bare", "planned")
REPEATS = 5
PILOT_REPEATS = 2
PILOT_GATE = 0.5

_WS = re.compile(r"\s+")


def norm(t: str) -> str:
    """Match normalization. The pilot gate first failed at 0.44 because the
    writer formats digits with Unicode narrow spaces ("$2\u202f450/seat")
    and hyphenated units ("six-week") that plain probes missed — raw digit
    strings were present in 15/16 pilot outputs. Group separators and
    hyphens are normalized away on BOTH sides before matching."""
    t = (t or "").replace("$", "").replace("*", "")
    for sep in ("\u202f", "\u00a0", "\u2009", ","):
        t = t.replace(sep, "")
    t = t.replace("-", " ")
    return _WS.sub(" ", t).lower()


def guard_items() -> None:
    """Frozen rules: probes absent from case text AND both seats' base text."""
    from examples.test_cases import get_case
    seats = json.loads(SEATS_PATH.read_text())
    problems = []
    for it in ITEMS:
        hay = norm(get_case(it["case"]).prompt)
        for role in (it["seat_A"], it["seat_B"]):
            hay += " " + norm(seats[it["case"]].get(role, ""))
        for p in it["clean_probes"] + it["wrong_probes"]:
            if norm(p) in hay:
                problems.append(f"item {it['id']}: probe {p!r} occurs in case "
                                f"or seat base text")
        if it["seat_A"] == it["seat_B"]:
            problems.append(f"item {it['id']}: seat_A == seat_B")
    if problems:
        for p in problems:
            print("  " + p)
        raise SystemExit("ITEM GUARDS FAILED")
    print(f"item guards: PASS ({len(ITEMS)} items; probes collide with "
          f"neither case nor seat text)")


def preflight() -> None:
    t = chat(WRITER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED — backend unreachable.")
    print("preflight: backend responds")


def build(it, arm: str) -> str:
    seats = json.loads(SEATS_PATH.read_text())[it["case"]]
    parts = []
    for role in ROLES:
        base = seats.get(role, "")
        if not base:
            continue
        add = ""
        if role == it["seat_A"]:
            add = "\n\n" + it["stmt"].format(v=it["wrong_value"])
        elif role == it["seat_B"] and arm == "planned":
            add = "\n\n" + it["stmt"].format(v=it["clean_value"])
        parts.append("--- SPECIALIST CONTRIBUTION ---\n" + base.rstrip() + add)
    return "\n\n".join(parts)


def one_run(it, arm: str, rep: int):
    from examples.test_cases import get_case
    q = f"{get_case(it['case']).prompt}\n\n{it['ask_line']}"
    txt = None
    for attempt in range(3):
        txt = chat(WRITER, WRITER_PROMPT,
                   f"{build(it, arm)}\n\nQuestion:\n{q}",
                   temperature=0.6, max_tokens=8192)
        if txt and txt.strip():
            break
        time.sleep(5 * (attempt + 1))
    if not txt or not txt.strip():
        return None
    low = norm(txt)
    return {"run_id": f"i{it['id']}__{arm}__r{rep}", "item": it["id"],
            "case": it["case"], "arm": arm, "repeat": rep,
            "clean": any(norm(p) in low for p in it["clean_probes"]),
            "wrong": any(norm(p) in low for p in it["wrong_probes"]),
            "chars": len(txt), "output": txt}


def _generate(arms, repeats, label) -> None:
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
    print(f"cell47 {label}: {len(todo)} runs to go ({len(done)} cached)", flush=True)
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
            if (k + 1) % 8 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print(f"cell47 {label} complete")


def rescore(rows):
    """Recompute clean/wrong from stored outputs under the CURRENT norm —
    stored booleans reflect whatever norm was live at generation time."""
    by_id = {it["id"]: it for it in ITEMS}
    for r in rows:
        it = by_id[r["item"]]
        low = norm(r["output"])
        r["clean"] = any(norm(p) in low for p in it["clean_probes"])
        r["wrong"] = any(norm(p) in low for p in it["wrong_probes"])
    return rows


def stage_pilot() -> None:
    _generate(("bare",), PILOT_REPEATS, "pilot")
    rows = rescore([json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()])
    pilot = [r for r in rows if r["arm"] == "bare" and r["repeat"] < PILOT_REPEATS]
    dec = sum(1 for r in pilot if r["clean"] or r["wrong"])
    rate = dec / len(pilot)
    print("=" * 70)
    print(f"PILOT GATE (registered): decisive {dec}/{len(pilot)} = {rate:.2f} "
          f"(gate >= {PILOT_GATE})  -> {'PASS' if rate >= PILOT_GATE else 'FAIL'}")
    if rate < PILOT_GATE:
        raise SystemExit(1)


def stage_runs() -> None:
    _generate(ARMS, REPEATS, "runs")


def stage_measure() -> None:
    import random
    rng = random.Random(0)
    rows = rescore([json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()])
    items_ = sorted({r["item"] for r in rows})
    by = {}
    for r in rows:
        by.setdefault((r["item"], r["arm"]), []).append(r)

    def rate(arm, field):
        v = [r for r in rows if r["arm"] == arm]
        return sum(1 for r in v if r[field]), len(v)

    def cluster_diff(field, a, b):
        ds = []
        for _ in range(5000):
            s = [items_[rng.randrange(len(items_))] for _ in items_]
            va = [r[field] for i in s for r in by.get((i, a), [])]
            vb = [r[field] for i in s for r in by.get((i, b), [])]
            if va and vb:
                ds.append(sum(va) / len(va) - sum(vb) / len(vb))
        ds.sort()
        return ds[int(.025 * len(ds))], ds[int(.975 * len(ds))]

    print("=" * 74)
    print("CELL 47 (L2) — the redundancy-planner lift")
    print("=" * 74)
    print("L2.3 RAW TABLE (mandatory, before any verdict)")
    print(f"  {'arm':<9}{'n':>4}{'clean':>7}{'wrong':>7}{'both':>6}{'NEITHER':>9}{'chars':>8}")
    for a in ARMS:
        v = [r for r in rows if r["arm"] == a]
        if not v:
            continue
        c = sum(1 for r in v if r["clean"] and not r["wrong"])
        w = sum(1 for r in v if r["wrong"] and not r["clean"])
        b = sum(1 for r in v if r["clean"] and r["wrong"])
        n = sum(1 for r in v if not r["clean"] and not r["wrong"])
        print(f"  {a:<9}{len(v):>4}{c:>7}{w:>7}{b:>6}{n:>9}"
              f"{sum(r['chars'] for r in v)//len(v):>8}")
    print("  per-item wrong-adoption (bare -> planned):")
    for i in items_:
        vb = by.get((i, "bare"), [])
        vp = by.get((i, "planned"), [])
        print(f"    item {i}: {sum(1 for r in vb if r['wrong'])}/{len(vb)}"
              f" -> {sum(1 for r in vp if r['wrong'])}/{len(vp)}")

    kwb, nb = rate("bare", "wrong")
    kwp, np_ = rate("planned", "wrong")
    lo, hi = cluster_diff("wrong", "bare", "planned")
    print()
    print("L2.1 THE LIFT — corrupted-value adoption, bare vs planned")
    print(f"  bare {kwb}/{nb} = {kwb/nb:.3f}   planned {kwp}/{np_} = "
          f"{kwp/np_:.3f}   diff CI [{lo:+.3f},{hi:+.3f}]")
    print(f"  L2.1: {'SUPPORTED — planner-assigned overlap protects' if lo > 0 else 'FALSIFIED — the planner buys nothing; harness §3 is struck'}")

    kcb, _ = rate("bare", "clean")
    kcp, _ = rate("planned", "clean")
    lo2, hi2 = cluster_diff("clean", "planned", "bare")
    print()
    print("L2.2 THE MECHANISM — clean-value adoption, planned vs bare")
    print(f"  bare {kcb}/{nb} = {kcb/nb:.3f}   planned {kcp}/{np_} = "
          f"{kcp/np_:.3f}   diff CI [{lo2:+.3f},{hi2:+.3f}]")
    if lo2 > 0:
        print("  L2.2: SUPPORTED — the co-source is USED (selection, not suppression)")
    elif lo > 0:
        print("  L2.2: FALSIFIED — corrupted adoption fell without clean adoption "
              "rising: suppression, not selection; reported as such")
    else:
        print("  L2.2: FALSIFIED")
    (OUT / "measured.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k != "output"} for r in rows], indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    {"pilot": stage_pilot, "runs": stage_runs, "measure": stage_measure}[stage]()
