"""Cell 68 — checks on the screen for the analyst's reading (screen data only;
nothing from the arms is read). Run: .venv/bin/python bench/analysis/cell68/screen_checks.py"""
import collections
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "train"), str(ROOT), str(ROOT / "gst" / "src")]
import run_cell68_equalcost as C  # noqa: E402

items = {it["id"]: it for it in C.load_items(C.TEST, C.TEST_SHA)}
rows = [json.loads(l) for l in C.SCREEN_RUNS.read_text().splitlines() if l.strip()]
rows = sorted(rows, key=lambda r: (r["item"], r["k"]))
by = collections.defaultdict(list)
for r in rows:
    by[r["item"]].append(r)
keep = json.loads((C.OUT / "screen.json").read_text())["keep"]

print("A. draws, time")
walls = [sum(s.get("wall_s") or 0 for s in r["steps"]) for r in rows]
t0 = min(r["steps"][0]["t_utc"] for r in rows); t1 = max(r["steps"][0]["t_utc"] for r in rows)
print(f"  draws {len(rows)}; candidates {len(by)}; first {t0}; last {t1}; draw time {sum(walls)/3600:.1f} h")
print(f"  draws over 3,000 s (machine asleep): {sum(w > 3000 for w in walls)}; retries (more than one call): "
      f"{sum(len(r['steps']) > 1 for r in rows)}; context-limit hits {sum(r['ctx_hit'] for r in rows)}")
for c in C.CATS:
    w = [x for r, x in zip(rows, walls) if r["category"] == c and x < 3000]
    o = [r["steps"][-1].get("output_tokens") or 0 for r in rows if r["category"] == c]
    print(f"  {c:<9} mean {st.mean(w):.0f} s, median {st.median(w):.0f} s; median output tokens {st.median(o):.0f}, max {max(o)}")

print("\nB. kept questions: right draws out of six")
for c in C.CATS:
    k = [i for i in keep if items[i]["category"] == c]
    cnt = collections.Counter(sum(r["ok"] for r in by[i]) for i in k)
    n = collections.Counter(len(by[i]) for i in k)
    print(f"  {c:<9} kept {len(k)}: right 2 -> {cnt[2]}, 3 -> {cnt[3]}, 4 -> {cnt[4]}; draws used {dict(sorted(n.items()))}")

print("\nC. kept questions by original source")
for c in C.CATS:
    k = [i for i in keep if items[i]["category"] == c]
    seen = [i for i in by if items[i]["category"] == c and C._decide([r["ok"] for r in by[i]])]
    sk = collections.Counter(items[i]["src"] for i in k); ss = collections.Counter(items[i]["src"] for i in seen)
    print(f"  {c}: " + "; ".join(f"{s} {sk[s]}/{ss[s]}" for s, _ in ss.most_common()))

print("\nD. replies with no readable letter")
un = [r for r in rows if r["letter"] is None]
kinds = collections.Counter()
for r in un:
    t = (r.get("tail") or "").strip()
    last = [x for x in t.splitlines() if x.strip()][-1:] or [""]
    L = last[0].strip()
    if L.upper().lstrip("*# ").startswith("ANSWER") and sum(ch in C.LETTERS for ch in L.split(":", 1)[-1].replace("*", "").strip()[:4]) >= 2:
        kinds["two or more letters on the ANSWER line"] += 1
    elif "ANSWER" in t.upper():
        kinds["an ANSWER line in another form"] += 1
    elif len(t) <= 3:
        kinds["a bare letter"] += 1
    else:
        kinds["no ANSWER line"] += 1
print(f"  {len(un)} of {len(rows)} draws: " + "; ".join(f"{k} {v}" for k, v in kinds.most_common()))
affected = sorted({r["item"] for r in un if r["item"] in keep})
print(f"  kept questions with at least one such draw: {len(affected)}")
for i in affected:
    print(f"    {i} {items[i]['category']} key {items[i]['key']}: letters {[r['letter'] for r in by[i]]}; "
          f"unread tails {[(r.get('tail') or '')[-60:] for r in by[i] if r['letter'] is None]}")

print("\nE. kept questions: what the wrong draws chose")
for c in C.CATS:
    k = [i for i in keep if items[i]["category"] == c]
    one = 0
    for i in k:
        wrong = [r["letter"] for r in by[i] if not r["ok"] and r["letter"]]
        if len(wrong) >= 2 and len(set(wrong)) == 1:
            one += 1
    print(f"  {c:<9} kept {len(k)}; questions whose wrong draws (two or more) all chose the same letter: {one}")
