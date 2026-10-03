"""Cell 64: figures quoted in the analyst's reading that the registered scoring
stage does not print. Not a registered test; no verdict word depends on it.
The registered output is `train/run_cell64_readers.py measure`.

    .venv/bin/python bench/analysis/cell64/reading_checks.py

Reads bench/runs/cell64_readers.jsonl (and bench/runs/cell51_uptake.jsonl for
the repeat comparison), calls no model, writes reading_checks.json.

  A. Integrity: reads per reader and arm, one runner hash, model builds,
     context hits, time span, head commits.
  B. Tries: reads that needed more than one try for a one-word answer, and
     unusable reads, by reader and arm.
  C. Flip share by reader, prompt, list length and line kind (the table
     behind the uptake figures), with the bare floor.
  D. The repeat of Cell 51: read-by-read agreement with Cell 51's answers.
  E. Item-level uptake, pooled over the four new readers, old prompt, one
     line: how many of the 11 items are above 0, and the smallest.
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
from train import run_cell64_readers as C64                      # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell64" / "reading_checks.json"


def main() -> None:
    rows = runlog.read_jsonl(C64.RUNS)
    items = {str(it["id"]): it for it in C64.items_kept()}
    readers = list(C64.READERS)
    out: dict = {}
    print(f"=== Cell 64: {len(rows)} reads")

    # A
    aud = [r["audit"] for r in rows]
    per_reader = collections.Counter(r["reader"] for r in rows)
    per_arm = collections.Counter((r["prompt"], r["kind"], str(r["k"])) for r in rows)
    out["integrity"] = {
        "reads": len(rows), "unique_run_ids": len({r["run_id"] for r in rows}),
        "per_reader": dict(per_reader), "arms": len(per_arm), "reads_per_arm": sorted(set(per_arm.values())),
        "items": sorted(items), "registration": sorted({a["registration"] for a in aud}),
        "script_sha": sorted({a["script_sha"] for a in aud}), "head_commits": sorted({a["head"] for a in aud}),
        "digests": {rd: sorted({a["digest"] for r, a in zip(rows, aud) if r["reader"] == rd}) for rd in readers},
        "ctx_hit": sum(bool(a.get("ctx_hit")) for a in aud), "done_reason": dict(collections.Counter(a["done_reason"] for a in aud)),
        "temperature": sorted({a["temperature"] for a in aud}), "max_tokens": sorted({a["max_tokens"] for a in aud}),
        "num_ctx": sorted({a["num_ctx"] for a in aud}), "max_prompt_tokens": max(a["prompt_tokens"] or 0 for a in aud),
        "first_utc": min(a["t_utc"] for a in aud), "last_utc": max(a["t_utc"] for a in aud),
        "span_by_reader": {rd: (min(a["t_utc"] for r, a in zip(rows, aud) if r["reader"] == rd),
                                max(a["t_utc"] for r, a in zip(rows, aud) if r["reader"] == rd)) for rd in readers},
    }
    print("A. integrity")
    for k, v in out["integrity"].items():
        print(f"   {k}: {v}")

    # B
    print("B. tries and unusable reads")
    out["tries"] = {}
    for rd in readers:
        rr = [r for r in rows if r["reader"] == rd]
        c = collections.Counter(int(r["tries"]) for r in rr)
        unus = [r for r in rr if r["answer"] is None]
        by_arm = collections.Counter((r["prompt"], r["kind"], str(r["k"])) for r in unus)
        retried_arm = collections.Counter((r["prompt"], r["kind"], str(r["k"])) for r in rr if int(r["tries"]) > 1)
        out["tries"][rd] = {"tries": dict(c), "unusable": len(unus), "unusable_by_arm": {"|".join(k): v for k, v in by_arm.items()},
                            "retried_by_arm": {"|".join(k): v for k, v in retried_arm.items()}}
        print(f"   {rd:<34} tries {dict(sorted(c.items()))}  unusable {len(unus)}"
              + (f"  unusable by arm {dict(by_arm)}" if unus else ""))
        if retried_arm:
            print(f"      retried by arm: {dict(retried_arm)}")

    # C
    print("C. flip share by reader, prompt, list length and line (bare = no list)")
    out["flip"] = {}
    arms = [("old", "bare", "0"), ("old", "irr", "1"), ("old", "rel", "1"), ("neutral", "bare", "0"),
            ("neutral", "irr", "1"), ("neutral", "rel", "1"), ("neutral", "irr", "5"), ("neutral", "rel", "5"),
            ("neutral", "irr", "10"), ("neutral", "rel", "10")]
    print("   " + " " * 34 + "".join(f"{p[:3]}|{k}|{n:>2}  " for p, k, n in arms))
    for rd in readers:
        vals = []
        for p, k, n in arms:
            sel = [r for r in rows if r["reader"] == rd and r["prompt"] == p and r["kind"] == k and str(r["k"]) == n]
            a = [r for r in sel if r["answer"] is not None]
            v = sum(r["answer"] == items[str(r["item"])]["flipped"] for r in a) / len(a) if a else float("nan")
            vals.append(v)
        out["flip"][rd] = {"|".join(a_): v for a_, v in zip(arms, vals)}
        print(f"   {rd:<34}" + "".join(f"{v:>10.3f}  " for v in vals))

    # D
    c51 = runlog.read_jsonl(ROOT / "bench" / "runs" / "cell51_uptake.jsonl")
    arm = {"rel": "app-rel", "irr": "app-irr", "bare": "bare"}
    m = {(r["reader"], str(r["item"]), r["arm"], str(r["rep"])): r for r in c51}
    agree = collections.Counter()
    for r in rows:
        if r["prompt"] != "old" or r["kind"] not in arm:
            continue
        s = m.get((r["reader"], str(r["item"]), arm[r["kind"]], str(r["rep"])))
        if s is None:
            continue
        agree[(r["reader"], r["kind"], s["answer"] == r["answer"])] += 1
    out["cell51_repeat"] = {f"{rd}|{k}": {"same": agree[(rd, k, True)], "different": agree[(rd, k, False)]}
                            for rd in readers[:2] for k in ("bare", "rel", "irr")}
    print("D. the old-prompt arms against Cell 51's reads (same reader, item, line, repeat); Cell 51 drew without a fixed seed")
    for key, d in out["cell51_repeat"].items():
        print(f"   {key:<40} same answer {d['same']:>4}  different {d['different']:>3}")

    # E
    new = list(C64.NEW_READERS)
    per_item = {}
    for iid, it in items.items():
        vals = []
        for rd in new:
            u = C64._uptake(rows, [it], rd, "old", 1)
            if it["id"] in u:
                vals.append(u[it["id"]])
        if vals:
            per_item[iid] = st.mean(vals)
    out["item_uptake_new_readers_old_1"] = per_item
    print("E. item-level uptake pooled over the four new readers (old prompt, one line):")
    print("   " + ", ".join(f"item {i} {v:+.2f}" for i, v in sorted(per_item.items(), key=lambda x: x[1])))
    print(f"   items above 0: {sum(v > 0 for v in per_item.values())} of {len(per_item)}; "
          f"above 0.25: {sum(v > 0.25 for v in per_item.values())}")
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
