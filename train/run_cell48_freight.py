"""Cell 48 (L4) — out-of-band epistemic freight.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 48 (L4)".

Both arms share byte-identical writer prose (Cell 41 control corpus); the
single factor is whether the harness appends a mechanically-assembled
"Assumptions & Caveats" appendix drawn from EXISTING validated labels.
Zero generation; the whole cell is judging.

Run:  .venv/bin/python train/run_cell48_freight.py build
      .venv/bin/python train/run_cell48_freight.py judge
      .venv/bin/python train/run_cell48_freight.py measure
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
from train.run_cell43_preference import (JUDGE_PROMPT, judge_pair,  # noqa: E402
                                         parse_winner)

OUT = ROOT / "bench" / "analysis" / "cell48"
C41_RUNS = ROOT / "bench" / "runs" / "cell41_phraseswap.jsonl"
C30 = ROOT / "bench" / "analysis" / "c30c31"
C46L = ROOT / "bench" / "analysis" / "cell46" / "labels.json"
C46V = ROOT / "bench" / "analysis" / "cell46" / "variants.json"
JUDGES = ["gpt-oss:20b", "qwen2.5:7b-instruct"]     # label judges (historic)
PRIMARY_JUDGE = "gpt-oss:20b"
REPL_JUDGE = "qwen3-vl:30b-a3b-instruct"
REPL_SUBSAMPLE = 40
FAMS = ("cutoff", "modeled", "jurisd", "hedging")
REPEATS = 7


def old_case_caveats() -> dict[str, list[str]]:
    """Both-judge construct sentences from c30c31 upstream units, per case
    (full-supply variant preferred = the complete seat stack)."""
    units = json.loads((C30 / "units.json").read_text())
    lab = json.loads((C30 / "labels.json").read_text())
    flat, owner = [], []
    for u in units:
        for s in u["sentences"]:
            flat.append(s)
            owner.append(u)
    per_variant: dict[tuple[str, int], list[str]] = {}
    for off in sorted({int(k.split("|")[1]) for k in lab}):
        a, b = lab.get(f"{JUDGES[0]}|{off}"), lab.get(f"{JUDGES[1]}|{off}")
        if not a or not b:
            continue
        for pos in range(1, 11):
            i = off + pos - 1
            if i >= len(flat):
                break
            u = owner[i]
            if u["kind"] != "upstream":
                continue
            la, lb = a.get(str(pos)), b.get(str(pos))
            if la and lb and any(la.get(f) and lb.get(f) for f in FAMS):
                per_variant.setdefault((u["key"][0], u["key"][1]), []).append(flat[i])
    out: dict[str, list[str]] = {}
    for (case, _vid), sents in sorted(per_variant.items()):
        if len(sents) > len(out.get(case, [])):
            out[case] = sents          # richest variant per case
    return out


def new_case_caveats() -> dict[str, list[str]]:
    """Both-judge construct sentences from Cell 46 upstream labels."""
    from train.run_cell46_writer_replication import split_sentences
    lab = json.loads(C46L.read_text())
    variants = json.loads(C46V.read_text())
    vtext = {f"{v['case']}__v{v['variant_id']}":
             [s for t in v["upstream"] if t for s in split_sentences(t)]
             for v in variants}
    out: dict[str, list[str]] = {}
    for k, e in lab.items():
        if not k.startswith("UP::"):
            continue
        key = k[4:]
        case = key.rsplit("__v", 1)[0]
        sents = vtext.get(key, [])
        a, b = (e["judges"].get(j, {}) for j in JUDGES)
        got = [sents[i] for i in range(min(e["n"], len(sents)))
               if a.get(str(i)) and b.get(str(i))
               and any(a[str(i)].get(f) and b[str(i)].get(f) for f in FAMS)]
        if len(got) > len(out.get(case, [])):
            out[case] = got
    return out


def build_appendix(sents: list[str]) -> str:
    body = "\n".join(f"- {s.strip()}" for s in sents)
    return ("\n\n---\nASSUMPTIONS & CAVEATS (as stated by the specialist "
            "contributors)\n" + body)


def stage_build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cav = old_case_caveats()
    cav.update({k: v for k, v in new_case_caveats().items() if k not in cav})
    rows = [json.loads(l) for l in C41_RUNS.read_text().splitlines()
            if l.strip() and json.loads(l)["arm"] == "control"]
    missing = sorted({r["case"] for r in rows} - set(cav))
    if missing:
        # Deviation recorded in the runbook: the registration's 18/18 check
        # verified labeled-upstream presence per case, not agreed-caveat
        # presence. Cases whose upstream carries ZERO both-judge caveat
        # sentences cannot have an appendix and are excluded, not faked.
        print(f"EXCLUDING caveat-free cases (no agreed caveat sentences): "
              f"{missing}")
        rows = [r for r in rows if r["case"] in cav]
    arts = []
    for r in rows:
        app = build_appendix(cav[r["case"]])
        arts.append({"case": r["case"], "repeat": r["repeat"],
                     "bare": r["output"], "freight": r["output"] + app,
                     "n_caveats": len(cav[r["case"]]),
                     "app_chars": len(app)})
    (OUT / "artifacts.json").write_text(json.dumps(arts, ensure_ascii=False))
    import statistics as st
    print(f"built {len(arts)} artifact pairs over "
          f"{len({a['case'] for a in arts})} cases")
    print(f"  caveats/case: min {min(a['n_caveats'] for a in arts)}  "
          f"median {st.median(a['n_caveats'] for a in arts)}  "
          f"max {max(a['n_caveats'] for a in arts)}")
    print(f"  appendix chars: median {st.median(a['app_chars'] for a in arts):.0f} "
          f"vs prose median {st.median(len(a['bare']) for a in arts):.0f}")


def stage_judge() -> None:
    import random
    from examples.test_cases import get_case
    arts = json.loads((OUT / "artifacts.json").read_text())
    cpath = OUT / "judgments.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    rng = random.Random(48)
    keys = [(a["case"], a["repeat"]) for a in arts]
    repl = set(rng.sample(keys, min(REPL_SUBSAMPLE, len(keys))))
    (OUT / "repl_subsample.json").write_text(json.dumps(sorted(map(list, repl))))
    by = {(a["case"], a["repeat"]): a for a in arts}
    jobs = [(PRIMARY_JUDGE, k) for k in keys] + \
           [(REPL_JUDGE, k) for k in keys if k in repl]
    print(f"cell48 judge: {len(jobs)} pairs x 2 orderings", flush=True)
    t0 = time.time()
    for i, (j, (case, rep)) in enumerate(jobs):
        a = by[(case, rep)]
        q = get_case(case).prompt
        # side-1 = FREIGHT (the arm under test), matching C43's S1 convention
        judge_pair(j, q, a["freight"], a["bare"], cache,
                   f"{j}|L4|{case}|{rep}|fwd")
        judge_pair(j, q, a["bare"], a["freight"], cache,
                   f"{j}|L4|{case}|{rep}|rev")
        cpath.write_text(json.dumps(cache))
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            print(f"  {i+1}/{len(jobs)} {el:.0f}s "
                  f"~{el/(i+1)*(len(jobs)-i-1):.0f}s left", flush=True)
    print("cell48 judging complete")


def _decide(cache, judge, case, rep):
    f = cache.get(f"{judge}|L4|{case}|{rep}|fwd")
    v = cache.get(f"{judge}|L4|{case}|{rep}|rev")
    if f is None or v is None:
        return None
    w_f = "S1" if f == "A" else "S2"
    w_r = "S1" if v == "B" else "S2"
    return w_f if w_f == w_r else "TIE"


def stage_measure() -> None:
    import random
    import statistics as st
    rng = random.Random(0)
    arts = json.loads((OUT / "artifacts.json").read_text())
    cache = json.loads((OUT / "judgments.json").read_text())
    cases = sorted({a["case"] for a in arts})

    # P48.1 carriage (manipulation check) — literal containment
    def norm(t):
        return re.sub(r"\s+", " ", t.replace("*", "")).lower()
    carr_f, carr_b, tot = 0, 0, 0
    cav_map = {}
    for a in arts:
        key = a["case"]
        if key not in cav_map:
            app = a["freight"][len(a["bare"]):]
            cav_map[key] = [l[2:].strip() for l in app.splitlines()
                            if l.startswith("- ")]
        for c in cav_map[key]:
            tot += 1
            carr_f += norm(c) in norm(a["freight"])
            carr_b += norm(c) in norm(a["bare"])
    tot = max(tot, 1)

    def share(judge, pairs):
        by = {}
        for case, rep in pairs:
            d = _decide(cache, judge, case, rep)
            if d in ("S1", "S2"):
                by.setdefault(case, []).append(d == "S1")
        pool = sorted(by)
        dec = [x for c in pool for x in by[c]]
        # ties counted BEFORE any early return — the first version returned
        # ties=0 when decisives were empty, hiding a 40/40 all-tie replication
        # (verdict-printing bug family, instance four).
        ties = sum(1 for case, rep in pairs
                   if _decide(cache, judge, case, rep) == "TIE")
        if not dec:
            return float("nan"), (float("nan"),) * 2, 0, ties
        ds = []
        for _ in range(5000):
            s = [pool[rng.randrange(len(pool))] for _ in pool]
            w = [x for c in s for x in by[c]]
            if w:
                ds.append(sum(w) / len(w))
        ds.sort()
        return (sum(dec) / len(dec),
                (ds[int(.025 * len(ds))], ds[int(.975 * len(ds))]),
                len(dec), ties)

    keys = [(a["case"], a["repeat"]) for a in arts]
    print("=" * 76)
    print("CELL 48 (L4) — out-of-band epistemic freight")
    print("=" * 76)
    print("P48.3 RAW TABLE (mandatory, before any verdict)")
    from collections import Counter
    raw = Counter(v for k, v in cache.items() if v and k.startswith(PRIMARY_JUDGE))
    print(f"  primary raw position split: A {raw.get('A',0)} / B {raw.get('B',0)}")
    print(f"  appendix chars: median "
          f"{st.median(a['app_chars'] for a in arts):.0f}; prose median "
          f"{st.median(len(a['bare']) for a in arts):.0f}  "
          f"(C43 winner-is-longer ran 0.73-0.80 — reported per registration)")

    print()
    print("P48.1 CARRIAGE (manipulation check)")
    print(f"  freight {carr_f}/{tot} = {carr_f/tot:.3f} (gate >= 0.95)   "
          f"bare {carr_b}/{tot} = {carr_b/tot:.3f} (gate <= 0.35)")
    ok1 = carr_f / tot >= 0.95 and carr_b / tot <= 0.35
    print(f"  P48.1: {'PASS' if ok1 else 'FAIL — estimand premise not established'}")

    print()
    print("P48.2 THE ESTIMAND — freight-vs-bare preference (registered bands)")
    pt, ci, n, ties = share(PRIMARY_JUDGE, keys)
    print(f"  [{PRIMARY_JUDGE}] share {pt:.3f}  CI [{ci[0]:.3f},{ci[1]:.3f}]  "
          f"decisive n={n}  ties {ties}")
    if ci[0] > 0.32:
        print("  P48.2: SUPPORTED — the appendix clears the entire in-prose "
              "penalty band (0.20-0.32)")
    elif ci[1] < 0.40:
        print("  P48.2: FALSIFIED — the appendix is penalized like in-prose "
              "hedging; harness §6 fails for preference-surviving deployment")
    else:
        print("  P48.2: NOT EVALUABLE at this power (CI straddles the bands), "
              "as registered")
    repl = [tuple(x) for x in json.loads((OUT / "repl_subsample.json").read_text())]
    pt2, ci2, n2, ties2 = share(REPL_JUDGE, repl)
    print(f"  [{REPL_JUDGE}] share {pt2:.3f}  CI [{ci2[0]:.3f},{ci2[1]:.3f}]  "
          f"decisive n={n2}  ties {ties2}  (replication, reported beside, "
          f"never pooled)")
    (OUT / "measured.json").write_text(json.dumps(
        {"carriage": [carr_f / tot, carr_b / tot],
         "primary": [pt, ci, n], "repl": [pt2, ci2, n2]}))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"build": stage_build, "judge": stage_judge,
     "measure": stage_measure}[stage]()
