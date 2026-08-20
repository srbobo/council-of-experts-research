"""Cell 46 — second-writer replication of the transport law.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 46 PRE-REGISTRATION".

Cell 30's nine cases cluster-ceiling at n_eff 47.4, exactly the requirement
phi4 needs, so the CORPUS is doubled rather than the repeat count: nine
further cases (de-scaffolded seat text built for Cell 41 with Cell 30's
exact clean prompts) yield 21 new supply variants over 18 cases.

Construction and instrument are Cell 30's: `supply_variants` builds
regex-construction levels while MEASURED SUPPLY COMES FROM THE JUDGES.

Run:  .venv/bin/python train/run_cell46_writer_replication.py variants
      ... runs / judge / measure
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                              # noqa: E402
from train.run_cell30_descaffold import WRITER_PROMPT              # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell46"
RUNS = ROOT / "bench" / "runs" / "cell46_writer.jsonl"
C30 = ROOT / "bench" / "analysis" / "c30c31"
C30_VARIANTS = ROOT / "bench" / "analysis" / "cell30" / "variants.json"
C41_SEATS = ROOT / "bench" / "analysis" / "cell41" / "seats.json"
C30_SEATS = ROOT / "bench" / "analysis" / "cell30" / "seats.json"
WRITERS = ("gpt-oss:20b", "phi4:14b")
JUDGES = ["gpt-oss:20b", "qwen2.5:7b-instruct"]
ROLES = ("healthcare", "legal", "finance")
REPEATS = 2
FAMS = ("cutoff", "modeled", "jurisd", "hedging")


def preflight() -> None:
    for w in WRITERS:
        t = chat(w, "Reply with the single word OK.", "ping",
                 temperature=0.0, max_tokens=256)
        if not t or not t.strip():
            raise SystemExit(f"PREFLIGHT FAILED — {w} unreachable.")
    print(f"preflight: both writers respond")


def stage_variants() -> None:
    """Build the 21 new variants with Cell 30's exact construction."""
    from gst.corpus import supply_variants
    OUT.mkdir(parents=True, exist_ok=True)
    s41 = json.loads(C41_SEATS.read_text())
    s30 = json.loads(C30_SEATS.read_text())
    new_cases = [c for c in s41 if c not in s30]
    out = []
    for case in new_cases:
        up = [s41[case][r] for r in ROLES if s41[case].get(r)]
        for vid, (level, variant, _f) in enumerate(supply_variants(up)):
            out.append({"case": case, "variant_id": vid,
                        "supply_regex_construction": level,
                        "upstream": variant})
    (OUT / "variants.json").write_text(json.dumps(out, ensure_ascii=False))
    print(f"cell46 variants: {len(out)} across {len(new_cases)} new cases "
          f"(measured supply comes from the judges, not these levels)")


def stage_runs() -> None:
    from examples.test_cases import get_case
    preflight()
    variants = json.loads((OUT / "variants.json").read_text())
    done = set()
    if RUNS.exists():
        for l in RUNS.read_text().splitlines():
            if l.strip():
                done.add(json.loads(l)["run_id"])
    todo = [(v, w, r) for v in variants for w in WRITERS for r in range(REPEATS)
            if f"{v['case']}__v{v['variant_id']}__{w}__r{r}" not in done]
    print(f"cell46: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0, fails = time.time(), 0
    with RUNS.open("a") as fh:
        for k, (v, w, rep) in enumerate(todo):
            body = "\n\n".join(f"--- SPECIALIST CONTRIBUTION ---\n{t}"
                               for t in v["upstream"] if t)
            txt = None
            for attempt in range(3):
                txt = chat(w, WRITER_PROMPT,
                           f"{body}\n\nQuestion:\n{get_case(v['case']).prompt}",
                           temperature=0.6, max_tokens=8192)
                if txt and txt.strip():
                    break
                time.sleep(5 * (attempt + 1))
            if not txt or not txt.strip():
                fails += 1
                print(f"  EMPTY {v['case']}/v{v['variant_id']}/{w}/r{rep} "
                      f"(consecutive {fails})", flush=True)
                if fails >= 5:
                    raise SystemExit("ABORTING — backend down; resumable.")
                continue
            fails = 0
            fh.write(json.dumps({
                "run_id": f"{v['case']}__v{v['variant_id']}__{w}__r{rep}",
                "case": v["case"], "variant_id": v["variant_id"],
                "writer": w, "repeat": rep,
                "upstream": [t for t in v["upstream"] if t],
                "output": txt}, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 10 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print("cell46 runs complete")


def split_sentences(text: str) -> list[str]:
    out, buf = [], []
    for i, ch in enumerate(text):
        buf.append(ch)
        if ch in ".!?" and i + 1 < len(text) and text[i + 1].isspace():
            s = "".join(buf).strip()
            if s:
                out.append(s)
            buf = []
    s = "".join(buf).strip()
    if s:
        out.append(s)
    return [x for x in out if 25 <= len(x) <= 400]


def stage_judge() -> None:
    """Validated B=10 two-judge protocol on upstream (supply) and output
    (emission) units, exactly as Cell 30 measured them."""
    from train.run_cellIV_batchjudge import judge_batches
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    cpath = OUT / "judge_cache.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    labels = {}
    lpath = OUT / "labels.json"
    if lpath.exists():
        labels = json.loads(lpath.read_text())

    # upstream units are shared across writers/repeats — judge each once
    seen_up = {}
    for r in rows:
        key = f"{r['case']}__v{r['variant_id']}"
        seen_up.setdefault(key, r["upstream"])

    t0 = time.time()
    print(f"cell46 judge: {len(seen_up)} upstream units + {len(rows)} outputs",
          flush=True)
    for i, (key, up) in enumerate(sorted(seen_up.items())):
        if f"UP::{key}" in labels:
            continue
        sents = [s for t in up for s in split_sentences(t)]
        items = [{"sentence": s} for s in sents]
        per = {}
        for j in JUDGES:
            got, _ = judge_batches(items, 10, j, cache, f"UP::{key}")
            per[j] = {str(k): v for k, v in got.items()}
        labels[f"UP::{key}"] = {"n": len(sents), "judges": per}
        cpath.write_text(json.dumps(cache))
        lpath.write_text(json.dumps(labels))
        print(f"  upstream {i+1}/{len(seen_up)} ({time.time()-t0:.0f}s)", flush=True)

    for i, r in enumerate(rows):
        rid = r["run_id"]
        if f"OUT::{rid}" in labels:
            continue
        items = [{"sentence": s} for s in split_sentences(r["output"])]
        per = {}
        for j in JUDGES:
            got, _ = judge_batches(items, 10, j, cache, f"OUT::{rid}")
            per[j] = {str(k): v for k, v in got.items()}
        labels[f"OUT::{rid}"] = {"n": len(items), "judges": per}
        cpath.write_text(json.dumps(cache))
        lpath.write_text(json.dumps(labels))
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            print(f"  outputs {i+1}/{len(rows)} {el:.0f}s", flush=True)
    print("cell46 judging complete")


def _count(entry) -> int:
    """Both-judges-agree count of construct-bearing sentences."""
    a, b = (entry["judges"].get(j, {}) for j in JUDGES)
    n = 0
    for i in range(entry["n"]):
        la, lb = a.get(str(i)), b.get(str(i))
        if not la or not lb:
            continue
        if any(la.get(f) and lb.get(f) for f in FAMS):
            n += 1
    return n


def _agreement(labels) -> tuple[int, int]:
    ok = tot = 0
    for e in labels.values():
        a, b = (e["judges"].get(j, {}) for j in JUDGES)
        for i in range(e["n"]):
            la, lb = a.get(str(i)), b.get(str(i))
            if not la or not lb:
                continue
            for f in FAMS:
                tot += 1
                ok += (la.get(f) == lb.get(f))
    return ok, tot


def stage_measure() -> None:
    import math
    import random
    from gst.stats import bootstrap_ols
    rng = random.Random(0)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    labels = json.loads((OUT / "labels.json").read_text())

    # new points
    pts = []
    for r in rows:
        up = labels.get(f"UP::{r['case']}__v{r['variant_id']}")
        out = labels.get(f"OUT::{r['run_id']}")
        if not up or not out:
            continue
        pts.append({"case": r["case"], "writer": r["writer"],
                    "s": _count(up), "y": _count(out),
                    "chars": len(r["output"])})
    # existing Cell 30 points
    old = json.loads((C30 / "measured.json").read_text())["P"]
    for r in old:
        pts.append({"case": r["key"][0], "writer": r["writer"],
                    "s": r["s"], "y": r["y"], "chars": None})

    ok, tot = _agreement(labels)
    print("=" * 78)
    print("CELL 46 — second-writer replication of the transport law")
    print("=" * 78)
    print("P46.3 MANDATORY TABLE (before any verdict)")
    print(f"  new judge agreement (per family-decision): {ok}/{tot} = "
          f"{ok/tot:.3f}  -> {'PASS' if ok/tot >= 0.70 else 'FAIL (bar 0.70)'}")

    def fit_for(w):
        v = [p for p in pts if p["writer"] == w]
        xs = [p["s"] for p in v]
        ys = [p["y"] for p in v]
        cases = sorted({p["case"] for p in v})
        n = len(v)
        de = 1 + (n / max(len(cases), 1) - 1) * 0.190
        f = bootstrap_ols(xs, ys, draws=5000)
        # cluster bootstrap over cases
        by = {}
        for p in v:
            by.setdefault(p["case"], []).append(p)
        sl = []
        for _ in range(5000):
            s = [cases[rng.randrange(len(cases))] for _ in cases]
            X = [q["s"] for c in s for q in by[c]]
            Y = [q["y"] for c in s for q in by[c]]
            if len(set(X)) < 2:
                continue
            mx = sum(X) / len(X)
            my = sum(Y) / len(Y)
            den = sum((x - mx) ** 2 for x in X)
            if den:
                sl.append(sum((x - mx) * (y - my) for x, y in zip(X, Y)) / den)
        sl.sort()
        cl = (sl[int(.025 * len(sl))], sl[int(.975 * len(sl))]) if sl else (float("nan"),) * 2
        return f, n, len(cases), n / de, cl, ys

    print(f"  {'writer':<14}{'n':>5}{'cases':>7}{'n_eff':>8}{'w':>8}"
          f"{'cluster CI':>22}{'mean y':>9}")
    res = {}
    for w in WRITERS:
        f, n, k, neff, cl, ys = fit_for(w)
        res[w] = (f, neff, cl)
        print(f"  {w:<14}{n:>5}{k:>7}{neff:>8.1f}{f.slope:>8.3f}"
              f"   [{cl[0]:+.3f},{cl[1]:+.3f}]{sum(ys)/len(ys):>9.3f}")
        print(f"                 intercept c = {f.intercept:.3f} "
              f"{f.intercept_ci}  (bootstrap-seed sensitive; report as "
              f"consistent-with-zero unless robust)")

    print()
    print("P46.1 THE ESTIMAND — does phi4's slope exclude zero?")
    f2, neff2, cl2 = res["phi4:14b"]
    ok2 = cl2[0] > 0
    print(f"  phi4 w = {f2.slope:.3f}  cluster CI [{cl2[0]:+.3f},{cl2[1]:+.3f}]  "
          f"n_eff = {neff2:.1f}  (requirement was ~47)")
    if ok2:
        print("  P46.1: SUPPORTED — the transport law holds for a SECOND writer")
    elif neff2 >= 47:
        print("  P46.1: FALSIFIED at adequate power — the law is writer-specific")
    else:
        print(f"  P46.1: NOT EVALUABLE — n_eff {neff2:.1f} below the registered ~47")

    print()
    print("P46.2 AGREEMENT (not equality) — do the two writers' CIs overlap?")
    f1, _, cl1 = res["gpt-oss:20b"]
    overlap = not (cl1[1] < cl2[0] or cl2[1] < cl1[0])
    print(f"  gpt-oss [{cl1[0]:+.3f},{cl1[1]:+.3f}]   phi4 [{cl2[0]:+.3f},{cl2[1]:+.3f}]")
    print(f"  P46.2: {'SUPPORTED — intervals overlap' if overlap else 'FALSIFIED — disjoint; both writers transport at materially different rates (a finding, not a failure)'}")
    (OUT / "measured.json").write_text(json.dumps(pts, indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "variants"
    {"variants": stage_variants, "runs": stage_runs,
     "judge": stage_judge, "measure": stage_measure}[stage]()
