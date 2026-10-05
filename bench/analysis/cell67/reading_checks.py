"""Cell 67: figures quoted in the analyst's reading that the registered scoring
stage does not print. Not a registered test; no verdict word depends on it.
The registered output is `train/run_cell67_livechain.py measure`.

    .venv/bin/python bench/analysis/cell67/reading_checks.py

Reads bench/runs/cell67_livechain.jsonl and bench/analysis/cell67/shared.json,
calls no model, writes reading_checks.json.

  A. Integrity: runs, model calls per step, extra tries, empty or cut-off
     replies by step, one runner hash, time span.
  B. Delivery (P67.0) by the registered figure detector and by the same
     detector after LaTeX separators are removed (the format miss recorded in
     the CELL 63 READING of 2026-10-02, before this cell ran).
  C. Final answers by arm and by whether the figures reached the
     specialists' texts (separators removed).
  D. Where the disagreement is visible: the editor's list of disagreements
     and the final answer, both detectors.
  E. The follow-up: which specialist it went to, and the answer by that.
  F. Figures from nowhere: how often a specialist with no notes writes the
     planted or the right figure, and final replies with two answer lines.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import re
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                            # noqa: E402
from train import run_cell63_checkable as C63                    # noqa: E402

_spec = importlib.util.spec_from_file_location("c63checks", ROOT / "bench" / "analysis" / "cell63" / "reading_checks.py")
_c63 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_c63)
tolerant = _c63._has_figure_tolerant

RUNS = ROOT / "bench" / "runs" / "cell67_livechain.jsonl"
SHARED = ROOT / "bench" / "analysis" / "cell67" / "shared.json"
OUT = ROOT / "bench" / "analysis" / "cell67" / "reading_checks.json"
BAR = 0.75


def main() -> None:
    rows = runlog.read_jsonl(RUNS)
    shared = {k: v for k, v in json.loads(SHARED.read_text()).items() if not k.startswith("SMOKE")}
    items = {it["id"]: it for it in C63.load_items()}
    out: dict = {}
    print(f"=== Cell 67: {len(rows)} runs on {len({r['item'] for r in rows})} items")

    # A
    steps = collections.Counter()
    tries = collections.Counter()
    cut = collections.Counter()
    empty = collections.Counter()
    times = []
    for src in list(shared.values()) + rows:
        seen = collections.Counter()
        for a in src.get("audit", []) if "seat_A" in src else src.get("steps", []):
            seen[a["step"]] += 1
            steps[a["step"]] += 1
            cut[a["step"]] += a.get("done_reason") == "length"
            empty[a["step"]] += bool(a.get("budget_exhausted"))
            times.append(a["t_utc"])
        for s, n in seen.items():
            if n > 1 and not s.startswith("plan"):
                tries[s] += n - 1
    out["integrity"] = {
        "runs": len(rows), "items": len({r["item"] for r in rows}), "per_arm": dict(collections.Counter(r["arm"] for r in rows)),
        "calls_by_step": dict(steps), "calls": sum(steps.values()), "extra_tries_by_step": dict(tries),
        "cut_at_allowance_by_step": {k: v for k, v in cut.items() if v}, "empty_replies_by_step": {k: v for k, v in empty.items() if v},
        "registration": sorted({r["audit"]["registration"] for r in rows}), "script_sha": sorted({r["audit"]["script_sha"] for r in rows}),
        "head_commits": sorted({r["audit"]["head"] for r in rows}), "ctx_hit": sum(bool(r["ctx_hit"]) for r in rows),
        "plan_attempts": dict(collections.Counter(sum(1 for a in sh["audit"] if a["step"].startswith("plan")) for sh in shared.values())),
        "first_utc": min(times), "last_utc": max(times), "followup_blocked": sum(bool(r["followup_blocked"]) for r in rows),
    }
    print("A. integrity")
    for k, v in out["integrity"].items():
        print(f"   {k}: {v}")

    # B
    a_reg = sum(C63._has_figure(sh["seat_A"], items[i]["tok"]["wrong1"]) for i, sh in shared.items())
    a_tol = sum(tolerant(sh["seat_A"], items[i]["tok"]["wrong1"]) for i, sh in shared.items())
    red = [r for r in rows if r["arm"] == "redundancy"]
    bare = [r for r in rows if r["arm"] == "bare"]
    b_reg = sum(bool(r["right_in_B"]) for r in red)
    b_tol = sum(tolerant(r["seat_B"], items[r["item"]]["tok"]["right"]) for r in red)
    n = len(shared)
    out["delivery"] = {"A_wrong_registered": a_reg, "A_wrong_separators_removed": a_tol, "B_right_registered": b_reg,
                       "B_right_separators_removed": b_tol, "n": n, "bar": BAR,
                       "missed_by_registered_detector": sorted(i for i, sh in shared.items()
                                                               if tolerant(sh["seat_A"], items[i]["tok"]["wrong1"])
                                                               and not C63._has_figure(sh["seat_A"], items[i]["tok"]["wrong1"]))}
    print("B. delivery of the figures to the specialists' texts")
    print(f"   wrong figure in A's text: registered detector {a_reg}/{n} = {a_reg/n:.3f}; separators removed {a_tol}/{n} = {a_tol/n:.3f} (bar {BAR})")
    print(f"   right figure in B's text (redundancy): registered {b_reg}/{len(red)} = {b_reg/len(red):.3f}; separators removed {b_tol}/{len(red)} = {b_tol/len(red):.3f}")
    print(f"   A texts the registered detector misses: {out['delivery']['missed_by_registered_detector']}")

    # C
    a_ok = {i: tolerant(sh["seat_A"], items[i]["tok"]["wrong1"]) for i, sh in shared.items()}
    print("C. final answers by arm and delivery (separators removed)")
    out["outcomes"] = {}
    for name, sel in (("bare, wrong figure reached A", [r for r in bare if a_ok[r["item"]]]),
                      ("bare, it did not", [r for r in bare if not a_ok[r["item"]]]),
                      ("redundancy, both reached", [r for r in red if a_ok[r["item"]] and tolerant(r["seat_B"], items[r["item"]]["tok"]["right"])]),
                      ("redundancy, only the wrong one reached A", [r for r in red if a_ok[r["item"]] and not tolerant(r["seat_B"], items[r["item"]]["tok"]["right"])]),
                      ("redundancy, only the right one reached B", [r for r in red if not a_ok[r["item"]] and tolerant(r["seat_B"], items[r["item"]]["tok"]["right"])]),
                      ("redundancy, neither reached", [r for r in red if not a_ok[r["item"]] and not tolerant(r["seat_B"], items[r["item"]]["tok"]["right"])])):
        c = collections.Counter(r["outcome"] for r in sel)
        out["outcomes"][name] = {"n": len(sel), **dict(c)}
        print(f"   {name:<44} n={len(sel):>2}  right {c['right']:>2}  wrong {c['wrong']:>2}  other {c['other']:>2}  none {c['none']:>2}")

    # D
    print("D. where the disagreement shows (redundancy arm)")
    t_reg = sum(bool(r["tensions_both_figures"]) for r in red)
    t_tol = sum(tolerant(r["tensions"], items[r["item"]]["tok"]["wrong1"]) and tolerant(r["tensions"], items[r["item"]]["tok"]["right"]) for r in red)
    f_reg = sum(bool(r["answer_both_figures"]) for r in red)
    f_tol = sum(tolerant(r["output"], items[r["item"]]["tok"]["wrong1"]) and tolerant(r["output"], items[r["item"]]["tok"]["right"]) for r in red)
    listed = [r for r in red if tolerant(r["tensions"], items[r["item"]]["tok"]["wrong1"]) and tolerant(r["tensions"], items[r["item"]]["tok"]["right"])]
    c = collections.Counter(r["outcome"] for r in listed)
    shown = sum(tolerant(r["output"], items[r["item"]]["tok"]["wrong1"]) and tolerant(r["output"], items[r["item"]]["tok"]["right"]) for r in listed)
    out["disagreement"] = {"list_both_registered": t_reg, "list_both_separators_removed": t_tol, "final_both_registered": f_reg,
                           "final_both_separators_removed": f_tol, "n": len(red),
                           "when_listed": {"n": len(listed), **dict(c), "final_shows_both": shown},
                           "final_chars_median": st.median(len(r["output"]) for r in red)}
    print(f"   the editor's list of disagreements names both figures: registered {t_reg}/{len(red)}, separators removed {t_tol}/{len(red)}")
    print(f"   the final answer shows both figures: registered {f_reg}/{len(red)}, separators removed {f_tol}/{len(red)}")
    print(f"   when the list names both (n = {len(listed)}): final right {c['right']}, wrong {c['wrong']}, other {c['other']}; final shows both {shown}")

    # E
    print("E. the follow-up question, by the specialist it went to")
    out["followup"] = {}
    for arm, sel in (("bare", bare), ("redundancy", red)):
        for seat in ("A", "B", "C", None):
            ss = [r for r in sel if r["route_seat"] == seat]
            c = collections.Counter(r["outcome"] for r in ss)
            out["followup"][f"{arm}|{seat}"] = {"n": len(ss), **dict(c)}
            print(f"   {arm:<10} to {str(seat):<4} n={len(ss):>2}  right {c['right']:>2}  wrong {c['wrong']:>2}  other {c['other']:>2}")

    # F
    print("F. figures from nowhere, and two-answer replies")
    c_wrong = sum(tolerant(sh["seat_C"], items[i]["tok"]["wrong1"]) for i, sh in shared.items())
    c_right = sum(tolerant(sh["seat_C"], items[i]["tok"]["right"]) for i, sh in shared.items())
    bb_wrong = sum(tolerant(r["seat_B"], items[r["item"]]["tok"]["wrong1"]) for r in bare)
    bb_right = sum(tolerant(r["seat_B"], items[r["item"]]["tok"]["right"]) for r in bare)
    a_right = sum(tolerant(sh["seat_A"], items[i]["tok"]["right"]) for i, sh in shared.items())
    two = collections.Counter((r["arm"], min(len(re.findall(r"ANSWER\s*:", r["output"])), 2)) for r in rows)
    out["nowhere"] = {"C_text_wrong": c_wrong, "C_text_right": c_right, "bare_B_text_wrong": bb_wrong, "bare_B_text_right": bb_right,
                      "A_text_right": a_right, "answer_lines": {f"{k[0]}|{k[1]}": v for k, v in two.items()}}
    print(f"   C's text (no notes) shows the planted figure in {c_wrong}/{n} items and the right figure in {c_right}/{n}")
    print(f"   B's text in the bare arm (no notes) shows the planted figure in {bb_wrong}/{len(bare)} and the right figure in {bb_right}/{len(bare)}")
    print(f"   A's text (wrong figure in its notes) shows the right figure in {a_right}/{n}")
    print(f"   final replies by number of answer lines (arm, 0/1/2+): {dict(two)}")
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
