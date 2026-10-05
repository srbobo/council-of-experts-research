"""Cell 67 — re-scoring with the figure detector's format miss repaired.

Recorded in RUNBOOK_PAPER_HARDENING.md, "CELL 67 CORRECTION (2026-10-05)",
at the author's decision. The registered verdict (P67.0 FAILS at 44 of 61)
stays on record as first scored. This script changes one thing: wherever
the registered scoring looks for a figure in a text, LaTeX thousands
separators between digit groups (5{,}200, 2\\,300) are removed first. The
repaired check is `_has_figure_tolerant` in
bench/analysis/cell63/reading_checks.py, committed on 2026-10-02 (1df7265)
before this cell ran and unchanged since. Nothing else is widened: a figure
written as "$150 k" is still not matched.

    .venv/bin/python bench/analysis/cell67/rescore.py

The five fields that depend on the detector are recomputed from the stored
texts (specialist A's text from shared.json; specialist B's text, the list
of disagreements and the final answer from each run record). The registered
scoring stage, `train/run_cell67_livechain.py::stage_measure`, is then run
unchanged on those rows. Its output goes to rescored.json; measured.json is
left as first scored. No model is called.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                            # noqa: E402
from train import run_cell63_checkable as C63                    # noqa: E402
from train import run_cell67_livechain as C67                    # noqa: E402

_spec = importlib.util.spec_from_file_location("c63checks", ROOT / "bench" / "analysis" / "cell63" / "reading_checks.py")
_c63 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_c63)
repaired = _c63._has_figure_tolerant

OUT = ROOT / "bench" / "analysis" / "cell67" / "rescored.json"


def main() -> None:
    rows = runlog.read_jsonl(C67.RUNS)
    shared = json.loads(C67.SHARED.read_text())
    items = {it["id"]: it for it in C63.load_items()}
    changed = {"wrong_in_A": [], "right_in_B": [], "wrong_in_B": [], "tensions_both_figures": [], "answer_both_figures": []}
    new_rows = []
    for r in rows:
        tok = items[r["item"]]["tok"]
        n = dict(r)
        n["wrong_in_A"] = repaired(shared[r["item"]]["seat_A"], tok["wrong1"])
        n["right_in_B"] = repaired(r["seat_B"], tok["right"])
        n["wrong_in_B"] = repaired(r["seat_B"], tok["wrong1"])
        n["tensions_both_figures"] = repaired(r["tensions"], tok["wrong1"]) and repaired(r["tensions"], tok["right"])
        n["answer_both_figures"] = repaired(r["output"], tok["wrong1"]) and repaired(r["output"], tok["right"])
        for k in changed:
            if bool(n[k]) != bool(r[k]):
                changed[k].append(r["run_id"])
            if bool(r[k]) and not bool(n[k]):
                raise SystemExit(f"the repaired check lost a match the registered one had: {r['run_id']} {k}")
        new_rows.append(n)

    print("CELL 67 RE-SCORED (correction of 2026-10-05) — figure fields recomputed with LaTeX separators removed;")
    print("everything between the rules below is printed by the registered scoring stage run on those fields.")
    print("Fields that changed (the repaired check only adds matches):")
    for k, ids in changed.items():
        print(f"  {k}: {len(ids)} run records" + (f"  {sorted(ids)}" if ids else ""))
    print()

    real_read, real_out = C67.runlog.read_jsonl, C67.OUT
    with tempfile.TemporaryDirectory() as tmp:
        C67.runlog.read_jsonl = lambda path: new_rows if Path(path) == C67.RUNS else real_read(path)
        C67.OUT = Path(tmp)
        try:
            C67.stage_measure()
            result = json.loads((Path(tmp) / "measured.json").read_text())
        finally:
            C67.runlog.read_jsonl, C67.OUT = real_read, real_out
    result["rescored"] = {"detector": "bench/analysis/cell63/reading_checks.py::_has_figure_tolerant (commit 1df7265, 2026-10-02)",
                          "changed_fields": changed}
    OUT.write_text(json.dumps(result, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(ROOT)}; bench/analysis/cell67/measured.json is unchanged (first scoring)")


if __name__ == "__main__":
    main()
