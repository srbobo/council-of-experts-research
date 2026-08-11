"""Cell 37 — does the writer RECOMPUTE, or merely prefer an uncorrupted source?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 37 PRE-REGISTRATION".
Four arms separate three mechanisms Cell 35 could not tell apart:

  A0 clean      primitives + correct value in all three seats
  A1 one-corrupt  one seat corrupted; a clean source remains  (= Cell 35)
  A2 all-corrupt  EVERY seat corrupted, primitives intact.
                  Copying now yields the WRONG value; only computation
                  yields the right one.  ** the decisive arm **
  A3 stripped     every seat corrupted AND the primitives deleted.
                  Neither copying nor computing can succeed; only a prior.

Scored by exact match on two known numerals — a known-value check, not
regex-as-NLP. Arithmetic items only, for exactly that reason.

Run:  .venv/bin/python train/run_cell37_recompute.py runs
      .venv/bin/python train/run_cell37_recompute.py measure
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

from train.run_cell25_moa import chat                        # noqa: E402
from train.run_cell30_descaffold import SEATS, WRITER_PROMPT  # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell37"
RUNS = ROOT / "bench" / "runs" / "cell37_recompute.jsonl"
C30 = ROOT / "bench" / "analysis" / "cell30"
WRITER = "gpt-oss:20b"
REPEATS = 3
ARMS = ("clean", "one-corrupt", "all-corrupt", "stripped")

# Nine computable claims, frozen before any run. Each states its PRIMITIVES
# explicitly so the correct value is derivable from the seat text alone;
# the stripped arm deletes exactly those primitives and leaves the wrong
# conclusion standing.
ITEMS = [
    dict(case="case_10_trigger_light_depreciation",
         prim="the asset costs $66,000, has a $6,000 salvage value and a "
              "five-year life, depreciated straight-line",
         concl="the annual depreciation expense is {v}",
         right="$12,000", wrong="$16,000",
         rprobe=["12,000", "12000"], wprobe=["16,000", "16000"]),
    dict(case="case_3_capitated_risk_contract",
         prim="capitation is $1,180 per member per month across 25,000 members",
         concl="the monthly capitation payment is {v}",
         right="$29.5 million", wrong="$2.95 million",
         rprobe=["29.5 million", "29,500,000", "29500000"],
         wprobe=["2.95 million", "2,950,000", "2950000"]),
    dict(case="case_5_nonprofit_hospital_pe_conversion",
         prim="the purchase price is $60 million and the debt component is "
              "$40 million",
         concl="the equity component is {v}",
         right="$20 million", wrong="$30 million",
         rprobe=["20 million", "$20m", "20,000,000"],
         wprobe=["30 million", "$30m", "30,000,000"]),
    dict(case="case_6_trigger_heavy_biotech_ma",
         prim="revenue is $200,000 per patient across 600,000 patients",
         concl="total lifetime revenue is {v}",
         right="$120 billion", wrong="$12 billion",
         rprobe=["120 billion", "$120b"], wprobe=["12 billion", "$12b"]),
    dict(case="case_8_trigger_light_hand_hygiene",
         prim="40 observations per month are split with 15 on days and 12 on "
              "evenings",
         concl="the night shift receives {v} observations",
         right="13", wrong="18",
         rprobe=["13 observation", "night = 13", "nights: 13", "night shift: 13"],
         wprobe=["18 observation", "night = 18", "nights: 18", "night shift: 18"]),
    dict(case="case_1_clinical_decision_support",
         prim="the validation cohort is 240,000 encounters divided equally "
              "across 12 sites",
         concl="each site contributes {v} encounters",
         right="20,000", wrong="24,000",
         rprobe=["20,000 encounter", "20000 encounter"],
         wprobe=["24,000 encounter", "24000 encounter"]),
    dict(case="case_2_cross_border_digital_therapeutic",
         prim="a 12-month rollout covers four markets in equal sequential "
              "phases",
         concl="each market receives {v} of the schedule",
         right="three months", wrong="four months",
         rprobe=["three months", "3 months"], wprobe=["four months", "4 months"]),
    dict(case="case_4_glp1_employer_coverage",
         prim="the employer has 1,200 employees and expects 8% uptake",
         concl="{v} members are expected to enrol",
         right="96", wrong="108",
         rprobe=["96 member", "96 employee", "96 enrol"],
         wprobe=["108 member", "108 employee", "108 enrol"]),
    dict(case="case_9_trigger_light_nda_clauses",
         prim="the agreement has a three-year term followed by a two-year "
              "post-termination confidentiality tail",
         concl="total protection runs {v}",
         right="five years", wrong="four years",
         rprobe=["five years", "5 years"], wprobe=["four years", "4 years"]),
]

_WS = re.compile(r"\s+")


def norm(t):
    return _WS.sub(" ", (t or "").replace("$", "").replace("*", "")).strip().lower()


def block(it, corrupted, strip):
    v = it["wrong"] if corrupted else it["right"]
    concl = it["concl"].format(v=v)
    return (f"For reference: {concl}." if strip
            else f"For reference: {it['prim']}; {concl}.")


def build(it, arm):
    """Which seats get a corrupted block, and whether primitives survive."""
    n = len(SEATS)
    if arm == "clean":
        return [(False, False)] * n
    if arm == "one-corrupt":
        return [(True, False)] + [(False, False)] * (n - 1)
    if arm == "all-corrupt":
        return [(True, False)] * n
    return [(True, True)] * n          # stripped


def stage_runs() -> None:
    from examples.test_cases import get_case
    seats = json.loads((C30 / "seats.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RUNS.exists():
        for line in RUNS.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    todo = [(i, it, arm, r) for i, it in enumerate(ITEMS) for arm in ARMS
            for r in range(REPEATS)
            if f"i{i}__{arm}__r{r}" not in done]
    print(f"cell37: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0 = time.time()
    with RUNS.open("a") as fh:
        for k, (i, it, arm, rep) in enumerate(todo):
            spec = build(it, arm)
            upstream = []
            for (role, (corrupted, strip)) in zip(SEATS, spec, strict=True):
                base = seats[it["case"]].get(role, "")
                if not base:
                    continue
                upstream.append(base.rstrip() + "\n\n" + block(it, corrupted, strip))
            body = "\n\n".join(f"--- SPECIALIST CONTRIBUTION ---\n{t}"
                               for t in upstream)
            txt = chat(WRITER, WRITER_PROMPT,
                       f"{body}\n\nQuestion:\n{get_case(it['case']).prompt}",
                       temperature=0.6, max_tokens=8192)
            if not txt or not txt.strip():
                print(f"  EMPTY i{i}/{arm}/r{rep}", flush=True)
                continue
            fh.write(json.dumps({"run_id": f"i{i}__{arm}__r{rep}", "item": i,
                                 "case": it["case"], "arm": arm, "repeat": rep,
                                 "output": txt}, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 10 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print("cell37 runs complete")


def stage_measure() -> None:
    import random
    from gst.stats import wilson_ci
    rng = random.Random(0)
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    tab = {a: [] for a in ARMS}
    for r in rows:
        it = ITEMS[r["item"]]
        o = norm(r["output"])
        has_r = any(norm(p) in o for p in it["rprobe"])
        has_w = any(norm(p) in o for p in it["wprobe"])
        tab[r["arm"]].append({"item": r["item"], "r": has_r, "w": has_w})

    print("=" * 74)
    print("P37.3 THREE-WAY SPLIT (mandatory; 'neither' is how a false")
    print("      positive would enter — omission is not computation)")
    print("=" * 74)
    print(f"  {'arm':<14}{'n':>4}{'correct':>9}{'corrupted':>11}{'neither':>9}")
    for a in ARMS:
        v = tab[a]
        if not v:
            continue
        c = sum(1 for x in v if x["r"] and not x["w"])
        w = sum(1 for x in v if x["w"])
        n = sum(1 for x in v if not x["r"] and not x["w"])
        print(f"  {a:<14}{len(v):>4}{c:>9}{w:>11}{n:>9}")

    a2 = tab["all-corrupt"]
    print()
    print("=" * 74)
    if len(a2) >= 8:
        k = sum(1 for x in a2 if x["r"] and not x["w"])
        kw = sum(1 for x in a2 if x["w"])
        ci = wilson_ci(k, len(a2))
        diffs = []
        for _ in range(5000):
            s = [a2[rng.randrange(len(a2))] for _ in a2]
            diffs.append(sum(1 for x in s if x["r"] and not x["w"]) / len(s)
                         - sum(1 for x in s if x["w"]) / len(s))
        diffs.sort()
        lo, hi = diffs[125], diffs[4874]
        ok = ci[0] > 0 and lo > 0
        print(f"P37.1 all-corrupt: correct {k}/{len(a2)} "
              f"[{ci[0]:.3f},{ci[1]:.3f}], corrupted {kw}/{len(a2)}; "
              f"correct-minus-corrupted CI [{lo:+.3f},{hi:+.3f}]")
        print(f"P37.1: {'SUPPORTED — the writer computes rather than copies' if ok else 'FALSIFIED — Cell 35 was cross-seat preference, and the word recomputation is struck'}")
    else:
        print(f"P37.1 NOT EVALUABLE — {len(a2)} usable all-corrupt runs")

    a3 = tab["stripped"]
    print()
    print("=" * 74)
    if len(a3) >= 8 and len(a2) >= 8:
        r2 = sum(1 for x in a2 if x["r"] and not x["w"]) / len(a2)
        r3 = sum(1 for x in a3 if x["r"] and not x["w"]) / len(a3)
        diffs = []
        for _ in range(5000):
            s3 = [a3[rng.randrange(len(a3))] for _ in a3]
            s2 = [a2[rng.randrange(len(a2))] for _ in a2]
            diffs.append(sum(1 for x in s3 if x["r"] and not x["w"]) / len(s3)
                         - sum(1 for x in s2 if x["r"] and not x["w"]) / len(s2))
        diffs.sort()
        lo, hi = diffs[125], diffs[4874]
        print(f"P37.2 stripped {r3:.3f} vs all-corrupt {r2:.3f}; "
              f"diff CI [{lo:+.3f},{hi:+.3f}]")
        print(f"P37.2: {'SUPPORTED — the correct value comes from the supplied primitives, not a prior' if hi < 0 else 'FALSIFIED — prior-driven; the claim narrows to preferring its prior over a corrupted input, which is NOT computation'}")
    else:
        print("P37.2 NOT EVALUABLE")
    (OUT / "scored.json").write_text(json.dumps(tab, indent=1))


if __name__ == "__main__":
    _bad = audit_probe_collisions()
    if _bad:
        print("PROBE COLLISIONS — refusing to run:")
        for b in _bad:
            print("  " + b)
        raise SystemExit(1)
    stage = sys.argv[1] if len(sys.argv) > 1 else "runs"
    {"runs": stage_runs, "measure": stage_measure}[stage]()


def audit_probe_collisions() -> list[str]:
    """A probe that appears in the PRIMITIVES would score a mere restatement
    of the inputs as a computed answer. Caught on item 0 pre-launch (the
    salvage value equalled the correct answer); this makes the check
    systematic rather than a one-off fix."""
    bad = []
    for i, it in enumerate(ITEMS):
        prim = norm(it["prim"])
        for kind in ("rprobe", "wprobe"):
            for pr in it[kind]:
                if norm(pr) in prim:
                    bad.append(f"item {i} ({it['case'][:26]}): {kind} {pr!r} "
                               f"occurs in its own primitives")
    return bad
