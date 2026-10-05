"""Cell 66 (amended check): figures quoted in the analyst's reading that the
registered scoring stages do not print. Not a registered test; no verdict word
depends on it. The registered outputs are `train/run_cell66_check.py measure`
and `train/run_cell66_conveyed.py measure`.

    .venv/bin/python bench/analysis/cell66/reading_checks.py

Reads bench/analysis/cell66/check_items.json and bench/runs/cell66_check.jsonl,
calls no model, writes reading_checks.json.

  A. Integrity of the check's 1,120 judge calls.
  B. K2 judge by judge, and each pair where both judges called the original
     and the altered statement FULLY, with whether the original figure is in
     the passages the judges saw.
  C. K3 judge by judge.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                            # noqa: E402

ITEMS = ROOT / "bench" / "analysis" / "cell66" / "check_items.json"
CALLS = ROOT / "bench" / "runs" / "cell66_check.jsonl"
OUT = ROOT / "bench" / "analysis" / "cell66" / "reading_checks.json"
J = ("gpt-oss:20b", "qwen3-vl:30b-a3b-instruct")


def main() -> None:
    doc = json.loads(ITEMS.read_text())
    rows = runlog.read_jsonl(CALLS)
    v: dict = collections.defaultdict(dict)
    for r in rows:
        j, iid = r["key"].split("|", 1)
        v[iid][j] = r["verdict"]
    aud = [r["audit"] for r in rows]
    out: dict = {"integrity": {
        "calls": len(rows), "registration": sorted({a["registration"] for a in aud}), "script_sha": sorted({a["script_sha"] for a in aud}),
        "head_commits": sorted({a["head"] for a in aud}), "digests": sorted({a["digest"] for a in aud}), "ctx_hit": sum(bool(a["ctx_hit"]) for a in aud),
        "done_reason": dict(collections.Counter(a["done_reason"] for a in aud)), "unparsed": sum(r["verdict"] is None for r in rows),
        "temperature": sorted({a["temperature"] for a in aud}), "first_utc": min(a["t_utc"] for a in aud), "last_utc": max(a["t_utc"] for a in aud),
        "items_by_part": dict(collections.Counter(it["part"] for it in doc["items"]))}}
    print("A. integrity")
    for k, val in out["integrity"].items():
        print(f"   {k}: {val}")

    pairs: dict = collections.defaultdict(dict)
    for it in doc["items"]:
        if it["part"] == "K2":
            pairs[it["pair"]][it["form"]] = it
    print("B. K2, altered figure")
    out["K2"] = {"per_judge": {}, "both_fully_both_forms": []}
    for j in J:
        of = [p for p in pairs.values() if v[p["original"]["id"]][j] == "fully"]
        c = collections.Counter(v[p["altered"]["id"]][j] for p in of)
        out["K2"]["per_judge"][j] = {"originals_fully": len(of), **dict(c)}
        print(f"   {j:<28} originals FULLY {len(of)}; altered form FULLY {c['fully']}, PARTLY {c['partly']}, NO {c['no']}")
    for n, p in sorted(pairs.items()):
        if all(v[p[f]["id"]][j] == "fully" for f in ("original", "altered") for j in J):
            fig = p["original"]["figure"].replace(",", "")
            in_pass = any(fig in s["text"].replace(",", "").replace(" ", "").replace(" ", "") for s in p["original"]["short"])
            rec = {"pair": n, "figure": p["original"]["figure"], "altered_figure": p["altered"]["figure"],
                   "original_figure_in_passages": in_pass, "statement": p["original"]["statement"]}
            out["K2"]["both_fully_both_forms"].append(rec)
            print(f"   pair {n}: {rec['figure']} -> {rec['altered_figure']}; original figure in the passages: {in_pass}; {rec['statement'][:110]}")
    k3 = [it for it in doc["items"] if it["part"] == "K3"]
    out["K3"] = {j: sum(v[it["id"]][j] in ("fully", "partly") for it in k3) for j in J}
    out["K3"]["both"] = sum(all(v[it["id"]][j] in ("fully", "partly") for j in J) for it in k3)
    print(f"C. K3, other scenario, conveyed (of {len(k3)}): {out['K3']}")
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
