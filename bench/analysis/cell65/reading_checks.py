"""Cell 65: figures quoted in the analyst's reading that the registered scoring
stage does not print. Not a registered test; no verdict word depends on it.
The registered output is `train/run_cell65_judges.py measure`.

    .venv/bin/python bench/analysis/cell65/reading_checks.py

Reads bench/runs/cell65_judgments.jsonl and the Cell 41 answers, calls no
model, writes reading_checks.json.

  A. Integrity: judgments per judge, one runner hash, model builds, context
     windows against the longest prompt, parse and time span.
  B. Position: each judge's choice in the forward and the reversed order,
     and how many of its 378 pairs it decided at all.
  C. Length: for the pairs a judge decided (same side wins in both orders),
     how often the winner is the longer answer; the length ratio of the
     sides in each comparison.
  D. phi4 (the one added judge that counts) against the two stored judges,
     pair by pair, on the pairs both decided.
"""
from __future__ import annotations

import collections
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                            # noqa: E402
from train import run_cell65_judges as C65                       # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell65" / "reading_checks.json"


def main() -> None:
    rows = runlog.read_jsonl(C65.CALLS)
    outs = C65.load_outputs()
    cs = C65.cases41()
    data = C65._load()
    out: dict = {}
    print(f"=== Cell 65: {len(rows)} judgments by the added judges")

    # A
    by = collections.defaultdict(list)
    for r in rows:
        by[r["judge"]].append(r)
    out["integrity"] = {}
    print("A. integrity")
    for j, L in by.items():
        a = [r["audit"] for r in L]
        pt = [x["prompt_tokens"] or 0 for x in a]
        d = {"judgments": len(L), "unique_keys": len({r["key"] for r in L}), "digest": sorted({x["digest"] for x in a}),
             "registration": sorted({x["registration"] for x in a}), "script_sha": sorted({x["script_sha"] for x in a}),
             "head_commits": sorted({x["head"] for x in a}), "num_ctx": sorted({x["num_ctx"] for x in a}),
             "prompt_tokens_max": max(pt), "prompt_tokens_median": st.median(pt), "ctx_hit": sum(bool(x["ctx_hit"]) for x in a),
             "done_reason": dict(collections.Counter(x["done_reason"] for x in a)), "unparsed": sum(r["winner"] is None for r in L),
             "output_tokens_median": st.median(x["output_tokens"] or 0 for x in a), "temperature": sorted({x["temperature"] for x in a}),
             "max_tokens": sorted({x["max_tokens"] for x in a}), "first_utc": min(x["t_utc"] for x in a), "last_utc": max(x["t_utc"] for x in a),
             "wall_hours": round(sum(x["wall_s"] for x in a) / 3600, 2)}
        out["integrity"][j] = d
        print(f"   {j}: " + ", ".join(f"{k} {v}" for k, v in d.items()))

    # B
    print("B. position: choice by order (A = the first-listed answer), and pairs decided")
    out["position"] = {}
    for j, got in data.items():
        fwd = collections.Counter(got.get(f"{comp}|{c}|{r}|fwd") for comp in C65.COMPARISONS for c in cs for r in range(C65.REPEATS))
        rev = collections.Counter(got.get(f"{comp}|{c}|{r}|rev") for comp in C65.COMPARISONS for c in cs for r in range(C65.REPEATS))
        decided = split = 0
        for comp in C65.COMPARISONS:
            for c in cs:
                for r in range(C65.REPEATS):
                    f, v = got.get(f"{comp}|{c}|{r}|fwd"), got.get(f"{comp}|{c}|{r}|rev")
                    if f is None or v is None:
                        continue
                    if (f == "A") != (v == "A"):
                        decided += 1
                    else:
                        split += 1
        out["position"][j] = {"fwd": dict(fwd), "rev": dict(rev), "decided_pairs": decided, "split_pairs": split}
        print(f"   {j:<34} forward {dict(fwd)}  reversed {dict(rev)}  decided {decided}  split {split}")

    # C
    print("C. length: of the pairs a judge decided, the share won by the longer answer; side-1 over side-2 length ratio")
    out["length"] = {}
    for comp in C65.COMPARISONS:
        a1, a2 = C65.PAIR_ARMS[comp]
        ratios = [len(outs[(a1, c, r)]) / len(outs[(a2, c, r)]) for c in cs for r in range(C65.REPEATS)]
        out["length"][comp] = {"side1_over_side2_median": st.median(ratios), "side1_longer_share": sum(x > 1 for x in ratios) / len(ratios)}
        print(f"   {comp} {C65.LABEL[comp]}: side 1 longer in {sum(x > 1 for x in ratios)} of {len(ratios)} pairs, median ratio {st.median(ratios):.2f}")
    for j, got in data.items():
        rec = {}
        for comp in C65.COMPARISONS:
            a1, a2 = C65.PAIR_ARMS[comp]
            longer_wins = n = 0
            for c in cs:
                for r in range(C65.REPEATS):
                    f, v = got.get(f"{comp}|{c}|{r}|fwd"), got.get(f"{comp}|{c}|{r}|rev")
                    if f is None or v is None or (f == "A") == (v == "A"):
                        continue
                    side1_wins = f == "A"
                    l1, l2 = len(outs[(a1, c, r)]), len(outs[(a2, c, r)])
                    if l1 == l2:
                        continue
                    n += 1
                    longer_wins += (side1_wins == (l1 > l2))
            rec[comp] = {"decided": n, "longer_wins": longer_wins}
        out["length"][j] = rec
        print(f"   {j:<34} " + "  ".join(f"{comp}: longer wins {v['longer_wins']}/{v['decided']}" for comp, v in rec.items()))

    # D
    print("D. phi4 against the stored judges on pairs both decided (per comparison)")
    out["phi4_agreement"] = {}
    p = data["phi4:14b"]
    for sj in C65.STORED:
        s = data[sj]
        for comp in C65.COMPARISONS:
            agree = n = 0
            for c in cs:
                for r in range(C65.REPEATS):
                    k1, k2 = f"{comp}|{c}|{r}|fwd", f"{comp}|{c}|{r}|rev"
                    if any(x.get(k) is None for x in (p, s) for k in (k1, k2)):
                        continue
                    dp = (p[k1] == "A") != (p[k2] == "A")
                    ds = (s[k1] == "A") != (s[k2] == "A")
                    if dp and ds:
                        n += 1
                        agree += (p[k1] == s[k1])
            out["phi4_agreement"][f"{sj}|{comp}"] = {"both_decided": n, "same_winner": agree}
            print(f"   phi4 and {sj.split(':')[0]:<9} {comp}: both decided {n:>3}, same winner {agree}")
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
