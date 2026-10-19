"""Cell 68 — checks on arm (d), the assembled chain, for the analyst's reading.
Run: .venv/bin/python bench/analysis/cell68/chain_checks.py"""
import collections
import json
import re
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "train"), str(ROOT), str(ROOT / "gst" / "src")]
import run_cell68_equalcost as C  # noqa: E402

items = {it["id"]: it for it in C.load_items(C.TEST, C.TEST_SHA)}
keys = {i: it["key"] for i, it in items.items()}
rows = [json.loads(l) for l in C.RUNS.read_text().splitlines() if l.strip()]
scores, cnt = C.arm_scores(rows, keys)
FIVE = {"q449", "q557", "q6382", "q6690", "q6741"}
chain = [r for r in rows if r["unit"] == "chain"]


def fmt(d):
    return "n/a" if not d else f"{d['mean']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}]  p = {d['p']:.4f}  (n = {d['n']})"


print("A. chain against the other setups")
for h, l in (("d", "a"), ("d", "b"), ("d", "b2"), ("d", "c")):
    print(f"  {h} minus {l:<3}{fmt(C.paired(scores, h, l))}")
ids = [i for i in scores["d"] if i not in FIVE]
print(f"  without the five questions: d minus c {fmt(C.paired(scores, 'd', 'c', ids))}")

print("\nB. chain replies with no readable letter")
un = [r for r in chain if r["letter"] is None]
kinds = collections.Counter()
for r in un:
    o = r.get("output") or ""
    if r.get("invalid"):
        kinds["plan could not be parsed"] += 1
    elif not o.strip():
        kinds["empty"] += 1
    elif re.search(r"(?im)^\W*answer\W*:", o):
        last = [ln for ln in o.splitlines() if re.match(r"(?i)^\W*answer\W*:", ln.strip())][-1]
        kinds["ANSWER line: " + re.sub(r"[A-J]", "X", last.strip()[:40])] += 1
    else:
        kinds["no ANSWER line"] += 1
print(f"  {len(un)} of {len(chain)}")
for k, v in kinds.most_common():
    print(f"    {v:>3}  {k}")


def lenient(o):
    o = o or ""
    m = re.findall(r"(?i)answer\W{0,6}(?:is\W{0,3})?(?:option\s*)?\(?\b([A-J])\b", o)
    if m:
        return m[-1].upper()
    m = re.findall(r"\\boxed\{\s*(?:\\text\{)?\s*(?:Answer\s*)?([A-J])\b", o)
    return m[-1] if m else None


lk = sum(lenient(r.get("output")) == keys[r["item"]] for r in un)
print(f"  a lenient reading gives the key in {lk} of them")
# lenient-scored chain accuracy and P68.3 (post hoc)
alt = []
for r in rows:
    r2 = dict(r)
    if r["unit"] == "chain" and r["letter"] is None:
        r2["ok"] = lenient(r.get("output")) == keys[r["item"]]
        r2["letter"] = lenient(r.get("output"))
    alt.append(r2)
s2, _ = C.arm_scores(alt, keys)
print(f"  chain accuracy with lenient reading of unreadable replies {st.mean(s2['d'].values()):.3f}; "
      f"d minus c {fmt(C.paired(s2, 'd', 'c'))}")

print("\nC. accuracy among runs that gave a letter")
for arm, unit in (("a", "direct"), ("c", "pipeline"), ("d", "chain")):
    rs = [r for r in rows if r["unit"].startswith(unit) and r["letter"]]
    print(f"  {arm}: {st.mean(float(r['ok']) for r in rs):.3f} of {len(rs)}")

print("\nD. the chain's final reply")
L = [len(r.get("output") or "") for r in chain]
print(f"  median characters {st.median(L):.0f}; replies naming three or more option letters in a bold or listed form "
      f"{sum(len(set(re.findall(r'\\*\\*([A-J])[\\.\\)\\*]', r.get('output') or ''))) >= 3 for r in chain)}")
print(f"  route of the follow-up: {dict(collections.Counter(r.get('route') for r in chain))}")
steps = collections.Counter(len(r["steps"]) for r in chain)
print(f"  calls per run: {dict(sorted(steps.items()))}; tokens per run median {st.median(r['tokens'] for r in chain):.0f}")
by_cat = collections.defaultdict(list)
for r in chain:
    by_cat[r["category"]].append(r)
for c, rs in by_cat.items():
    print(f"  {c:<9} accuracy {st.mean(float(r['ok']) for r in rs):.3f}, gave a letter {st.mean(float(r['letter'] is not None) for r in rs):.3f}")

print("\nE. chain wrong where the pipeline's majority over replicates is right: letters chosen")
same_as_direct_majority = 0; n = 0
dmaj = {}
for i in items:
    ls = [r["letter"] for r in rows if r["item"] == i and r["unit"].startswith("direct")]
    if ls:
        dmaj[i] = collections.Counter(x for x in ls if x).most_common(1)[0][0] if any(ls) else None
for r in chain:
    if r["letter"] and not r["ok"]:
        n += 1
        same_as_direct_majority += r["letter"] == dmaj.get(r["item"])
print(f"  wrong chain letters {n}; of these, the direct draws' most common letter {same_as_direct_majority}")
