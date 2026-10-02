"""Cell 63: figures quoted in the analyst's reading that the registered scoring
stage does not print. Nothing here is a registered test and no verdict word
depends on it. The registered output is `train/run_cell63_checkable.py measure`.

    .venv/bin/python bench/analysis/cell63/reading_checks.py [writer]

Reads bench/runs/cell63_checkable.jsonl and docs/CELL63_ITEMS.json, calls no
model, and writes bench/analysis/cell63/reading_checks.json.

What it reports, per editor model:
  A. Integrity: run ids, layouts, one runner version, one model build.
  B. Second tries: recorded runs whose seed is not the first seed of the run
     id (the first reply was empty and the registered retry rule drew again),
     by layout and template, with the time the discarded tries took.
  C. C4's split (registered under P63.5 as "reported", not printed by the
     scoring stage): which of the two wrong figures the answer follows, and
     whether the first-listed one wins.
  D. C3 by listing order, with "other" and "no answer" kept in the count.
  E. A check of the "both figures" detector on layouts where one of the two
     figures is nowhere in the prompt (how often its digits turn up anyway).
  F. Template-level shares behind the registered differences.
  G. Reply length and output tokens by layout.
  H. The registered detector does not match a figure typeset with LaTeX
     thousands separators (5{,}200 or 2\\,300). The same counts with those
     separators removed first, as a sensitivity check on P63.4, and the number
     of replies that hold nothing but the final answer line.
  I. C3 and C4 together: how often the answer follows the first-listed note,
     the second-listed note, or neither, and how often the larger of the two
     figures. Listing order and the label "Analyst A" cannot be told apart in
     this design: the first-listed note is always Analyst A's.
  J. Output tokens (hidden reasoning included) in C1 against C0, item by item:
     does a note that contradicts the case make the editor work longer?
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import re
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] if "bench" in Path(__file__).resolve().parts else Path.cwd()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                            # noqa: E402
from train import run_cell63_checkable as C63                    # noqa: E402

CONDS = C63.CONDS
OUT = ROOT / "bench" / "analysis" / "cell63" / "reading_checks.json"


def _t(s: str) -> dt.datetime:
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def _has_figure_tolerant(text: str, tok: str) -> bool:
    """The registered check after removing LaTeX separators between digits:
    5{,}200 and 2\\,300 become 5200 and 2300. Nothing else is changed."""
    flat = re.sub(r"(?<=\d)(?:\{,\}|\\[,;! ])(?=\d{3}(?!\d))", "", text)
    return C63._has_figure(flat, tok)


def _pair(cond: str):
    return {"C1": ("right", "wrong1"), "C3": ("right", "wrong1"), "C4": ("wrong1", "wrong2")}.get(cond)


def check_writer(rows: list[dict], all_rows: list[dict], items: dict[str, dict], writer: str) -> dict:
    out: dict = {}
    print(f"\n=== {writer}: {len(rows)} recorded runs")

    # ---- A. integrity
    ids = [r["run_id"] for r in rows]
    per_cond = collections.Counter(r["cond"] for r in rows)
    per_item = collections.Counter((r["item"], r["cond"]) for r in rows)
    aud = [r["audit"] for r in rows]
    integ = {
        "unique_run_ids": len(set(ids)), "runs": len(ids),
        "per_layout": dict(per_cond),
        "items": len({r["item"] for r in rows}), "templates": len({r["template"] for r in rows}),
        "two_runs_per_item_and_layout": all(v == 2 for v in per_item.values()) and len(per_item) == len(items) * len(CONDS),
        "registration": sorted({a["registration"] for a in aud}),
        "script_sha": sorted({a["script_sha"] for a in aud}),
        "model_digest": sorted({a["digest"] for a in aud}),
        "head_commits": sorted({a["head"] for a in aud}),
        "num_ctx": sorted({a["num_ctx"] for a in aud}),
        "max_tokens": sorted({a["max_tokens"] for a in aud}),
        "temperature": sorted({a["temperature"] for a in aud}),
        "ctx_hit": sum(bool(a.get("ctx_hit")) for a in aud),
        "budget_exhausted_recorded": sum(bool(a.get("budget_exhausted")) for a in aud),
        "done_reason": dict(collections.Counter(a.get("done_reason") for a in aud)),
        "first_run_utc": min(a["t_utc"] for a in aud), "last_run_utc": max(a["t_utc"] for a in aud),
        "max_prompt_plus_output_tokens": max((a.get("prompt_tokens") or 0) + (a.get("output_tokens") or 0) for a in aud),
    }
    out["integrity"] = integ
    print("A. integrity")
    for k, v in integ.items():
        print(f"   {k}: {v}")

    # ---- B. second tries
    order = {r["run_id"]: i for i, r in enumerate(all_rows)}
    retried = []
    for r in rows:
        k = r["audit"]["seed"] - runlog.seed_for(r["run_id"])
        if k:
            i = order[r["run_id"]]
            gap = None
            if i > 0 and all_rows[i - 1]["writer"] == writer:
                p = all_rows[i - 1]["audit"]
                gap = (_t(r["audit"]["t_utc"]) - _t(p["t_utc"])).total_seconds() - (p.get("wall_s") or 0)
            retried.append({"run_id": r["run_id"], "cond": r["cond"], "template": r["template"], "extra_tries": k,
                            "outcome": r["outcome"], "seconds_before_recorded_try": gap,
                            "recorded_output_tokens": r["audit"].get("output_tokens")})
    by_cond = collections.Counter(x["cond"] for x in retried)
    by_tmpl = collections.Counter(x["template"] for x in retried)
    out["second_tries"] = {"runs": len(retried), "discarded_replies": sum(x["extra_tries"] for x in retried),
                           "by_layout": {c: by_cond.get(c, 0) for c in CONDS}, "by_template": dict(by_tmpl),
                           "outcome_of_recorded_reply": dict(collections.Counter(x["outcome"] for x in retried)),
                           "detail": retried}
    print(f"B. second tries: {len(retried)} recorded runs needed one "
          f"({sum(x['extra_tries'] for x in retried)} discarded empty replies)")
    print(f"   by layout:   {out['second_tries']['by_layout']}")
    print(f"   by template: {dict(by_tmpl)}")
    print(f"   outcome of the recorded reply: {out['second_tries']['outcome_of_recorded_reply']}")
    for x in retried:
        g = x["seconds_before_recorded_try"]
        print(f"   {x['run_id']:<34} extra tries {x['extra_tries']}  time before the recorded try "
              f"{'n/a' if g is None else f'{g:.0f}s'}  recorded outcome {x['outcome']}")
    toks = [r["audit"].get("output_tokens") or 0 for r in rows]
    rate = [(r["audit"].get("output_tokens") or 0) / r["audit"]["wall_s"] for r in rows if r["audit"].get("wall_s")]
    out["speed"] = {"median_tokens_per_s": st.median(rate), "median_output_tokens": st.median(toks),
                    "max_output_tokens": max(toks), "seconds_for_16384_tokens_at_median_speed": 16384 / st.median(rate)}
    print(f"   speed: median {st.median(rate):.1f} tokens/s; 16,384 tokens take about "
          f"{16384 / st.median(rate):.0f}s; largest recorded reply {max(toks)} tokens")

    # ---- C. C4 split
    c4 = [r for r in rows if r["cond"] == "C4"]
    split = collections.Counter(r["outcome"] for r in c4)
    first = sum(1 for r in c4 if r["outcome"] == r["layout"]["A"])
    second = sum(1 for r in c4 if r["outcome"] == r["layout"]["B"])
    by_t = collections.defaultdict(list)
    for r in c4:
        if r["outcome"] in ("wrong1", "wrong2"):
            by_t[r["template"]].append(r["outcome"] == r["layout"]["A"])
    shares = [st.mean(v) for v in by_t.values()]
    iv = C63.t_interval(shares) if len(shares) >= 2 else (float("nan"),) * 3
    out["C4_split"] = {"n": len(c4), "outcomes": dict(split), "follows_first_listed": first, "follows_second_listed": second,
                       "first_listed_share_by_template": {"mean": iv[0], "lo": iv[1], "hi": iv[2], "k": len(shares)}}
    print(f"C. C4 (two wrong figures): outcomes {dict(split)} of {len(c4)}")
    print(f"   follows the first-listed figure {first}, the second-listed {second}; "
          f"first-listed share by template {iv[0]:.3f} [{iv[1]:.3f}, {iv[2]:.3f}] (k = {len(shares)})")
    print(f"   raised figure (wrong1) {split.get('wrong1', 0)}, lowered figure (wrong2) {split.get('wrong2', 0)}")
    out["C4_by_order"] = {}
    for a in ("wrong1", "wrong2"):
        rc = [r for r in c4 if r["layout"]["A"] == a]
        cnt = collections.Counter(r["outcome"] for r in rc)
        out["C4_by_order"][f"{a}_listed_first"] = {"n": len(rc), **dict(cnt)}
        print(f"   {a} listed first: n={len(rc)} {dict(cnt)}")

    # ---- D. C3 by order, all outcomes
    out["C3_by_order"] = {}
    print("D. C3 (one wrong, one right) by which note is listed first, all outcomes")
    for a in ("right", "wrong1"):
        rc = [r for r in rows if r["cond"] == "C3" and r["layout"]["A"] == a]
        cnt = collections.Counter(r["outcome"] for r in rc)
        out["C3_by_order"][f"{a}_listed_first"] = {"n": len(rc), **dict(cnt)}
        print(f"   {a} listed first: n={len(rc)} {dict(cnt)}")

    # ---- E. detector check
    print("E. 'both figures' detector: how often a figure's digits appear in the reply")
    det = {}
    for c in CONDS:
        rc = [r for r in rows if r["cond"] == c]
        row = {"n": len(rc)}
        for key in ("right", "wrong1", "wrong2"):
            row[key] = sum(C63._has_figure(r["output"], items[r["item"]]["tok"][key]) for r in rc)
        det[c] = row
        print(f"   {c}: n={row['n']}  right figure in reply {row['right']}  wrong1 {row['wrong1']}  wrong2 {row['wrong2']}")
    out["figure_in_reply"] = det
    print("   (in C0 neither wrong figure is in the prompt; in C2 the right figure is not; in C1 and C3 wrong2 is not;")
    print("    in C4 the right figure is not. Those counts are the detector's chance rate.)")
    # C1 and C3: both figures, split by outcome
    for c in ("C1", "C3", "C4"):
        rc = [r for r in rows if r["cond"] == c]
        tab = collections.Counter((r["outcome"], bool(r["both_figures"])) for r in rc)
        out[f"{c}_both_by_outcome"] = {f"{o}|{'both' if b else 'not both'}": n for (o, b), n in sorted(tab.items())}
        print(f"   {c} outcome by both-figures: {out[f'{c}_both_by_outcome']}")

    # ---- F. template-level shares
    planted = lambda r: r["outcome"] in ("wrong1", "wrong2")       # noqa: E731
    tmpl = sorted({r["template"] for r in rows}, key=lambda s: (s[0] != "t", int(s[1:])))
    print("F. by template: share of runs following a planted figure (C0..C4), then C0 right, then n per layout")
    out["by_template"] = {}
    for t in tmpl:
        row = {}
        for c in CONDS:
            rc = [r for r in rows if r["template"] == t and r["cond"] == c]
            row[c] = {"n": len(rc), "planted": sum(planted(r) for r in rc), "right": sum(r["outcome"] == "right" for r in rc),
                      "other": sum(r["outcome"] == "other" for r in rc), "none": sum(r["outcome"] == "none" for r in rc),
                      "both": sum(bool(r["both_figures"]) for r in rc)}
        out["by_template"][t] = row
        print(f"   {t:<4}" + "".join(f"{row[c]['planted'] / row[c]['n']:>7.2f}" for c in CONDS)
              + f"   C0 right {row['C0']['right'] / row['C0']['n']:.2f}   n {row['C0']['n']}"
              + f"   C3 right {row['C3']['right']}/{row['C3']['n']}  C1 right {row['C1']['right']}/{row['C1']['n']}")
    # item-level: how many items ever follow the planted figure in C1
    c1_items = collections.defaultdict(list)
    for r in rows:
        if r["cond"] == "C1":
            c1_items[r["item"]].append(r["outcome"])
    n_any = sum(1 for v in c1_items.values() if any(o in ("wrong1", "wrong2") for o in v))
    n_all = sum(1 for v in c1_items.values() if all(o in ("wrong1", "wrong2") for o in v))
    out["C1_items"] = {"items": len(c1_items), "planted_in_any_run": n_any, "planted_in_both_runs": n_all}
    print(f"   C1 items following the planted figure in at least one of two runs: {n_any} of {len(c1_items)}; in both: {n_all}")

    # ---- G. length by layout
    print("G. reply length and output tokens by layout (median)")
    out["length"] = {}
    for c in CONDS:
        rc = [r for r in rows if r["cond"] == c]
        ch, tk = st.median(r["chars"] for r in rc), st.median(r["audit"].get("output_tokens") or 0 for r in rc)
        out["length"][c] = {"median_chars": ch, "median_output_tokens": tk}
        print(f"   {c}: {ch:.0f} characters, {tk:.0f} output tokens (reasoning included)")

    # ---- H. format-tolerant detector, and replies that are the answer line alone
    print("H. the same figure check with LaTeX separators removed first (5{,}200 -> 5200); not the registered measure")
    tol = {}
    for c in CONDS:
        rc = [r for r in rows if r["cond"] == c]
        row = {"n": len(rc), "answer_line_only": sum(r["chars"] <= 40 for r in rc)}
        for key in ("right", "wrong1", "wrong2"):
            row[key] = sum(_has_figure_tolerant(r["output"], items[r["item"]]["tok"][key]) for r in rc)
        if _pair(c):
            a, b = _pair(c)
            row["both"] = sum(_has_figure_tolerant(r["output"], items[r["item"]]["tok"][a])
                              and _has_figure_tolerant(r["output"], items[r["item"]]["tok"][b]) for r in rc)
            row["both_registered"] = sum(bool(r["both_figures"]) for r in rc)
        tol[c] = row
        print(f"   {c}: n={row['n']}  right {row['right']}  wrong1 {row['wrong1']}  wrong2 {row['wrong2']}"
              + (f"  both {row['both']} (registered detector {row['both_registered']})" if "both" in row else "")
              + f"  replies of 40 characters or fewer {row['answer_line_only']}")
    by_t = collections.defaultdict(list)
    for r in rows:
        if r["cond"] in ("C3", "C4"):
            a, b = _pair(r["cond"])
            by_t[r["template"]].append(_has_figure_tolerant(r["output"], items[r["item"]]["tok"][a])
                                       and _has_figure_tolerant(r["output"], items[r["item"]]["tok"][b]))
    shares = [st.mean(v) for v in by_t.values()]
    iv = C63.t_interval(shares)
    tol["C3_C4_both_by_template"] = {"mean": iv[0], "lo": iv[1], "hi": iv[2], "k": len(shares)}
    print(f"   C3+C4 both figures, separators removed, by template: {iv[0]:.3f} [{iv[1]:.3f}, {iv[2]:.3f}] (k = {len(shares)})")
    out["figure_in_reply_separators_removed"] = tol

    # ---- I. first-listed note, C3 and C4 together
    conf = [r for r in rows if r["cond"] in ("C3", "C4")]
    f = sum(r["outcome"] == r["layout"]["A"] for r in conf)
    g = sum(r["outcome"] == r["layout"]["B"] for r in conf)
    by_t = collections.defaultdict(list)
    for r in conf:
        if r["outcome"] in (r["layout"]["A"], r["layout"]["B"]):
            by_t[r["template"]].append(r["outcome"] == r["layout"]["A"])
    shares = [st.mean(v) for v in by_t.values()]
    iv = C63.t_interval(shares)
    p_half = C63.sign_flip_p([x - 0.5 for x in shares])
    larger = sum(r["outcome"] == "wrong1" for r in conf)          # wrong1 is the raised figure in both layouts
    smaller = sum(r["outcome"] in ("right", "wrong2") for r in conf)
    out["first_listed_C3_C4"] = {"n": len(conf), "first": f, "second": g, "neither": len(conf) - f - g,
                                 "share_by_template": {"mean": iv[0], "lo": iv[1], "hi": iv[2], "k": len(shares)},
                                 "sign_flip_p_against_half_not_registered": p_half,
                                 "larger_figure": larger, "smaller_figure": smaller}
    print(f"I. C3+C4 ({len(conf)} runs): first-listed note followed {f}, second-listed {g}, neither {len(conf) - f - g}")
    print(f"   first-listed share among runs following either, by template: {iv[0]:.3f} [{iv[1]:.3f}, {iv[2]:.3f}] "
          f"(k = {len(shares)}); sign-flip p against one half = {p_half:.4f} (not a registered test)")
    print(f"   larger of the two figures followed {larger}, smaller {smaller}")

    # ---- J. C1 against C0, output tokens per item
    tok = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        if r["cond"] in ("C0", "C1", "C2", "C3", "C4"):
            tok[r["item"]][r["cond"]].append(r["audit"].get("output_tokens") or 0)
    d10 = [st.mean(v["C1"]) - st.mean(v["C0"]) for v in tok.values()]
    d32 = [st.mean(v["C3"]) - st.mean(v["C2"]) for v in tok.values()]
    out["output_tokens_item_differences"] = {
        "C1_minus_C0": {"mean": st.mean(d10), "median": st.median(d10), "items_higher": sum(x > 0 for x in d10), "items": len(d10)},
        "C3_minus_C2": {"mean": st.mean(d32), "median": st.median(d32), "items_higher": sum(x > 0 for x in d32), "items": len(d32)}}
    print(f"J. output tokens per item, C1 minus C0: mean {st.mean(d10):+.0f}, median {st.median(d10):+.0f}, "
          f"higher on {sum(x > 0 for x in d10)} of {len(d10)} items")
    print(f"   C3 minus C2: mean {st.mean(d32):+.0f}, median {st.median(d32):+.0f}, "
          f"higher on {sum(x > 0 for x in d32)} of {len(d32)} items")
    return out


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = args[0] if args else None
    items = {it["id"]: it for it in C63.load_items()}
    all_rows = runlog.read_jsonl(C63.RUNS)
    result = {}
    for writer in C63.WRITERS:
        if only and writer != only:
            continue
        rows = [r for r in all_rows if r["writer"] == writer]
        if rows:
            result[writer] = check_writer(rows, all_rows, items, writer)
    if "--no-write" not in sys.argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=1, default=float))
        print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
