"""Cell 68 — checks for the analyst's reading of arms (a), (b), (b2) and (c).
Rows of arm (d) are ignored. Run: .venv/bin/python bench/analysis/cell68/reading_checks.py"""
import collections
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "train"), str(ROOT), str(ROOT / "gst" / "src")]
import run_cell68_equalcost as C  # noqa: E402
from gst.smallcluster import t_interval, sign_flip_p  # noqa: E402

items = {it["id"]: it for it in C.load_items(C.TEST, C.TEST_SHA)}
keys = {i: it["key"] for i, it in items.items()}
rows = [r for r in (json.loads(l) for l in C.RUNS.read_text().splitlines() if l.strip()) if r["unit"] != "chain"]
FIVE = {"q449", "q557", "q6382", "q6690", "q6741"}
scores, cnt = C.arm_scores(rows, keys)


def fmt(d):
    return "n/a" if not d else f"{d['mean']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}]  p = {d['p']:.4f}  (n = {d['n']})"


print("A. the check fixed in the screen reading: without q449, q557, q6382, q6690, q6741")
ids = [i for i in scores["a"] if i not in FIVE]
for name, h, l in (("P68.1 pipeline minus one answer", "c", "a"), ("P68.2 pipeline minus plain drafts + editor", "c", "b2"),
                   ("pipeline minus vote of four", "c", "b"), ("vote of four minus one answer", "b", "a"),
                   ("plain drafts + editor minus one answer", "b2", "a")):
    print(f"  {name:<46}{fmt(C.paired(scores, h, l, ids))}")
print("  accuracy without the five: " + ", ".join(f"{a} {st.mean(scores[a][i] for i in ids):.3f}" for a in ("a", "b", "b2", "c")))

print("\nB. where the editor's answer comes from (per replicate)")
by = collections.defaultdict(dict)
for r in rows:
    by[(r["item"], r["rep"])][r["unit"]] = r
stats = {"b2": collections.Counter(), "c": collections.Counter()}
draft_acc = {"b2": [], "c": []}
for (item, rep), u in by.items():
    k = keys[item]
    if "selfmoa" in u and all(f"direct{j}" in u for j in range(3)):
        drafts = [u[f"direct{j}"]["letter"] for j in range(3)]
        stats["b2"]["n"] += 1
        fin = u["selfmoa"]["letter"]
        draft_acc["b2"] += [float(x == k) for x in drafts]
    else:
        drafts = None
    for arm, unit in (("b2", "selfmoa"), ("c", "pipeline")):
        if unit not in u:
            continue
        ds = drafts if arm == "b2" else u["pipeline"]["proposer_letters"]
        if ds is None:
            continue
        if arm == "c":
            stats["c"]["n"] += 1
            draft_acc["c"] += [float(x == k) for x in ds]
        fin = u[unit]["letter"]
        s = stats[arm]
        maj = C.vote(ds)
        c3 = collections.Counter(x for x in ds if x)
        top = max(c3.values()) if c3 else 0
        s["final right"] += fin == k
        s["majority of drafts right"] += maj == k
        s["any draft right"] += k in ds
        s["drafts unanimous"] += top == 3
        s["unanimous and final differs"] += top == 3 and fin != maj
        s["split 2-1"] += top == 2
        s["split 2-1, final is the minority"] += top == 2 and fin != maj and fin in ds
        s["split 2-1, minority was right"] += top == 2 and maj != k and k in ds
        s["split 2-1, final takes the right minority"] += top == 2 and maj != k and fin == k
        s["split 2-1, final leaves the right majority"] += top == 2 and maj == k and fin != k
        s["final not among drafts"] += fin not in ds
for arm, s in stats.items():
    n = s["n"]
    print(f"  ({arm}) {n} replicates; draft accuracy {st.mean(draft_acc[arm]):.3f}")
    for key in [k for k in s if k != "n"]:
        print(f"     {key:<44}{s[key]:>5}  ({s[key]/n:.3f})")

print("\nC. role drafts by role (pipeline)")
role = collections.defaultdict(list)
for r in rows:
    if r["unit"] == "pipeline":
        for ro, x in zip(r["order"], r["proposer_letters"]):
            role[(ro, r["category"])].append(float(x == keys[r["item"]]))
for cat in C.CATS:
    print(f"  {cat:<9}" + "  ".join(f"{ro} {st.mean(role[(ro, cat)]):.3f}" for ro in C.ROLES)
          + f"  | direct draws {st.mean(float(r['ok']) for r in rows if r['unit'].startswith('direct') and r['category'] == cat):.3f}")
print("  position of the right role in the pile is shuffled; first-listed draft's letter = final: "
      f"{st.mean(float(r['proposer_letters'][0] == r['letter']) for r in rows if r['unit'] == 'pipeline'):.3f}")

print("\nD. role drafts against plain drafts, question level (the proposers alone)")
pa = collections.defaultdict(list); da = collections.defaultdict(list)
for r in rows:
    if r["unit"] == "pipeline":
        pa[r["item"]] += [float(x == keys[r["item"]]) for x in r["proposer_letters"]]
    elif r["unit"].startswith("direct"):
        da[r["item"]].append(float(r["ok"]))
d = [st.mean(pa[i]) - st.mean(da[i]) for i in pa if i in da]
m, lo, hi = t_interval(d)
print(f"  role draft minus direct draw: {m:+.3f} [{lo:+.3f}, {hi:+.3f}]  p = {sign_flip_p(d):.4f}  (n = {len(d)})")

print("\nE. unreadable answers per arm, and what a lenient reading would give")
def lenient(t):
    t = (t or "").strip()
    if len(t) <= 3 and t[:1].upper() in C.LETTERS:
        return t[:1].upper()
    import re
    m = re.findall(r"\\boxed\{\s*(?:\\text\{)?\s*(?:Answer\s*)?([A-J])\b", t)
    return m[-1] if m else None
for unit in ("direct", "selfmoa", "pipeline"):
    rs = [r for r in rows if r["unit"].startswith(unit)]
    un = [r for r in rs if r["letter"] is None]
    len_right = sum(lenient(r["output"]) == keys[r["item"]] for r in un)
    multi = sum(1 for r in un if any(ln.strip().lstrip("*# ").upper().startswith("ANSWER") for ln in (r["output"] or "").splitlines()))
    print(f"  {unit:<9} runs {len(rs)}; no readable letter {len(un)}; of these, an ANSWER line in some form {multi}; "
          f"lenient reading gives the key {len_right}")

print("\nF. cost")
for unit in ("direct", "selfmoa", "pipeline"):
    rs = [r for r in rows if r["unit"].startswith(unit)]
    print(f"  {unit:<9} median tokens {st.median(r['tokens'] for r in rs):.0f}; mean wall s "
          f"{st.mean(sum(s.get('wall_s') or 0 for s in r['steps']) for r in rs):.0f}")

print("\nG. accuracy of single draws by replicate and by draw position (stability)")
for rep in range(C.REPS):
    print(f"  rep {rep}: " + ", ".join(f"draw {k} {st.mean(float(r['ok']) for r in rows if r['unit']==f'direct{k}' and r['rep']==rep):.3f}" for k in range(4)))
