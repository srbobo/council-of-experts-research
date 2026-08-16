"""Cell 42 — do domain fine-tunes reason differently from their own bases?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 42 PRE-REGISTRATION".
Producers frozen in docs/CELL42_PRODUCERS.json BEFORE this cell ran.

THE CONFOUND THIS DEFEATS. "Specialist vs generalist" moves architecture,
identity, training data and scale at once (audit #3, P36.2). The only
contrast identity cannot explain is REPLICATION ACROSS BASE FAMILIES: if
domain training induces an approach, the tuned-minus-its-OWN-base delta
should point the same way on lineages sharing no ancestry.

  lineage qwen2.5 : qwen2.5:7b-instruct   <- Meditron3
  lineage llama3  : llama3:8b-instruct     <- Med42, OpenBioLLM

Med42 and OpenBioLLM share a base, giving a WITHIN-lineage replicate that
separates "this fine-tune is quirky" from "medical fine-tuning does this".

INSTRUMENT. Frozen framework inventory, counts per 1k characters so
verbosity cannot buy signal — a containment check against a fixed list, the
same basis as Cell 37's numeral check, not regex-as-NLP. Surface features
are reported beside every content number because two GENERALISTS already
separate at AUC 0.945 on length alone (seat-approach pilot, df644bd).

Run:  .venv/bin/python train/run_cell42_domain_signature.py runs
      .venv/bin/python train/run_cell42_domain_signature.py measure
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
from train.run_probe_domain_signature import FRAMEWORKS, profile   # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell42"
RUNS = ROOT / "bench" / "runs" / "cell42_domain_signature.jsonl"
SPEC = json.loads((ROOT / "docs" / "CELL42_PRODUCERS.json").read_text())
REPEATS = 6
DEGEN_CHARS = 800

# (label, tag, family, kind, domain) — read from the frozen file, never inline
PRODUCERS: list[tuple[str, str, str, str, str]] = []
for lin in SPEC["lineages"]:
    b = lin["base"]
    PRODUCERS.append((b["label"], b["tag"], lin["family"], "base", "-"))
    for t in lin["tuned"]:
        PRODUCERS.append((t["label"], t["tag"], lin["family"], "tuned", t["domain"]))

# IDENTICAL for every producer: no role, no domain cue, no format dictation.
PROMPT = ("You are an analyst. Give a substantive written analysis of the "
          "situation below for a decision-maker. Be specific and concrete.")

# 6 clinical, 6 non-clinical. A real domain signature must be DOMAIN-SPECIFIC;
# a difference that appears on both is global style and is reported as style.
ITEMS = [
    ("hc", "case_1_clinical_decision_support"),
    ("hc", "case_2_cross_border_digital_therapeutic"),
    ("hc", "case_4_glp1_employer_coverage"),
    ("hc", "case_8_trigger_light_hand_hygiene"),
    ("hc", "case_l2_l2a"),
    ("hc", "case_l3_l3a"),
    ("off", "case_7_trigger_light_baseline"),
    ("off", "case_9_trigger_light_nda_clauses"),
    ("off", "case_10_trigger_light_depreciation"),
    ("off", "case_l1_l1a"),
    ("off", "case_l1_l1b"),
    ("off", "case_l3_l3b"),
]


def preflight() -> None:
    """Every producer must answer before any of them runs. A cell that
    discovers a dead model at run 200 wastes the run; Cell 41's first launch
    churned 378 cells against a dead backend and reported success."""
    for lbl, tag, *_ in PRODUCERS:
        t = chat(tag, "Reply with the single word OK.", "ping",
                 temperature=0.0, max_tokens=256)
        if not t or not t.strip():
            raise SystemExit(f"PREFLIGHT FAILED — {lbl} ({tag}) returned nothing.")
    print(f"preflight: all {len(PRODUCERS)} producers respond")


def stage_runs() -> None:
    from examples.test_cases import get_case
    preflight()
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RUNS.exists():
        for line in RUNS.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    todo = [(p, it, r) for p in PRODUCERS for it in ITEMS for r in range(REPEATS)
            if f"{p[0]}__{it[1]}__r{r}" not in done]
    print(f"cell42: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0, fails = time.time(), 0
    with RUNS.open("a") as fh:
        for k, ((lbl, tag, fam, kind, dom), (idom, case), rep) in enumerate(todo):
            txt = None
            for attempt in range(3):
                txt = chat(tag, PROMPT, get_case(case).prompt,
                           temperature=0.6, max_tokens=4096)
                if txt and txt.strip():
                    break
                time.sleep(5 * (attempt + 1))
            if not txt or not txt.strip():
                fails += 1
                print(f"  EMPTY {lbl}/{case}/r{rep} (consecutive {fails})", flush=True)
                if fails >= 5:
                    raise SystemExit("ABORTING — backend down; stage is resumable.")
                continue
            fails = 0
            fh.write(json.dumps({"run_id": f"{lbl}__{case}__r{rep}",
                                 "producer": lbl, "family": fam, "kind": kind,
                                 "tuned_domain": dom, "item_domain": idom,
                                 "case": case, "repeat": rep, "output": txt},
                                ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 20 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print("cell42 runs complete")


def stage_measure() -> None:
    import random
    rng = random.Random(0)
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    for r in rows:
        r.update(profile(r["output"]))

    def sel(prod, idom=None):
        return [r for r in rows if r["producer"] == prod
                and (idom is None or r["item_domain"] == idom)]

    def mean(v, k):
        return sum(x[k] for x in v) / len(v) if v else float("nan")

    KEY = "fw_healthcare"

    print("=" * 80)
    print("CELL 42 — domain signature, replicated across base families")
    print("=" * 80)

    # --- P42.5 degeneracy, before anything is interpreted -----------------
    print("P42.5 DEGENERACY (mandatory; producer dropped if >50% of runs short)")
    dead = set()
    for lbl, *_ in PRODUCERS:
        v = sel(lbl)
        d = sum(1 for x in v if x["chars"] < DEGEN_CHARS)
        if d > len(v) / 2:
            dead.add(lbl)
        print(f"  {lbl:<12} {d:>3}/{len(v):<4} runs under {DEGEN_CHARS} chars"
              + ("   *** DROPPED ***" if lbl in dead else ""))

    print()
    print("P42.4 SURFACE CONTROL (mandatory; content rates are all per-kchar)")
    print(f"  {'producer':<12}{'kind':<7}{'n':>4}{'chars':>8}{'list':>7}{'ttr':>7}"
          f"{'hc/k':>8}{'hc/k(in)':>10}{'hc/k(off)':>11}")
    for lbl, _t, fam, kind, _d in PRODUCERS:
        v = sel(lbl)
        if not v:
            continue
        print(f"  {lbl:<12}{kind:<7}{len(v):>4}{mean(v,'chars'):>8.0f}"
              f"{mean(v,'list_frac'):>7.3f}{mean(v,'ttr'):>7.3f}"
              f"{mean(v,KEY):>8.3f}{mean(sel(lbl,'hc'),KEY):>10.3f}"
              f"{mean(sel(lbl,'off'),KEY):>11.3f}")

    # --- cluster bootstrap over ITEMS -------------------------------------
    cases = sorted({r["case"] for r in rows})
    by = {}
    for r in rows:
        by.setdefault((r["case"], r["producer"]), []).append(r)

    def delta_ci(tuned, base, idom):
        """CI on (tuned - base) mean framework density, resampling ITEMS."""
        pool = [c for c in cases
                if any(x["item_domain"] == idom for x in by.get((c, base), []))]
        ds = []
        for _ in range(5000):
            s = [pool[rng.randrange(len(pool))] for _ in pool]
            a = [y[KEY] for c in s for y in by.get((c, tuned), [])
                 if y["item_domain"] == idom]
            b = [y[KEY] for c in s for y in by.get((c, base), [])
                 if y["item_domain"] == idom]
            if a and b:
                ds.append(sum(a)/len(a) - sum(b)/len(b))
        ds.sort()
        return (ds[int(.025*len(ds))], ds[int(.975*len(ds))]) if ds else None

    pairs = []
    for lin in SPEC["lineages"]:
        for t in lin["tuned"]:
            pairs.append((t["label"], lin["base"]["label"], lin["family"]))

    print()
    print("P42.1 DOMAIN SIGNATURE — tuned minus its OWN base, in-domain items")
    print("  (registered prediction: POSITIVE, CI excluding 0, in BOTH lineages)")
    signs = {}
    for tuned, base, fam in pairs:
        if tuned in dead or base in dead:
            print(f"  {tuned:<12} lineage {fam}: NOT EVALUABLE (degenerate arm)")
            continue
        ci = delta_ci(tuned, base, "hc")
        d = mean(sel(tuned, "hc"), KEY) - mean(sel(base, "hc"), KEY)
        sig = "POSITIVE" if ci and ci[0] > 0 else "NEGATIVE" if ci and ci[1] < 0 else "spans 0"
        signs.setdefault(fam, []).append((tuned, d, sig))
        print(f"  {tuned:<12} vs {base:<10} delta {d:+.3f}  "
              f"CI [{ci[0]:+.3f},{ci[1]:+.3f}]  {sig}")

    # A lineage has a DIRECTION only if all its tuned models agree on a
    # non-null one. "spans 0" is not a direction -- it is the absence of one.
    # (The first version of this block treated a single-element {'spans 0'}
    # set as agreement and printed a replication claim for a null result.
    # Same failure family as the probe's sign-only test: a verdict line that
    # can fire without the evidence it names.)
    lin_dirs = {}
    for f, v in signs.items():
        ds = {s for _, _, s in v}
        lin_dirs[f] = next(iter(ds)) if ds <= {"POSITIVE"} or ds <= {"NEGATIVE"} else None
    usable = {f: d for f, d in lin_dirs.items() if d is not None}
    both = len(lin_dirs) >= 2
    all_pos = both and len(usable) == len(lin_dirs) and set(usable.values()) == {"POSITIVE"}
    print(f"\n  P42.1: {'SUPPORTED' if all_pos else 'FALSIFIED'}"
          + ("" if both else " — fewer than 2 usable lineages, NOT EVALUABLE"))
    if not all_pos:
        for f, v in signs.items():
            print(f"    lineage {f:<9} " + ", ".join(f"{t} {d:+.3f} [{s}]"
                                                     for t, d, s in v))
        if len(usable) < len(lin_dirs):
            print("    At least one lineage has NO consistent non-null direction,")
            print("    so replication across ancestries is not demonstrated.")
        elif set(usable.values()) == {"NEGATIVE"}:
            print("    Both lineages replicate NEGATIVE — the fine-tune would be")
            print("    LESS domain-framed than its base, which is a real result but")
            print("    the opposite of the registered prediction.")

    print()
    print("P42.2 DOMAIN-SPECIFICITY — in-domain delta vs off-domain delta")
    for tuned, base, fam in pairs:
        if tuned in dead or base in dead:
            continue
        din = mean(sel(tuned,'hc'),KEY) - mean(sel(base,'hc'),KEY)
        doff = mean(sel(tuned,'off'),KEY) - mean(sel(base,'off'),KEY)
        print(f"  {tuned:<12} in {din:+.3f}   off {doff:+.3f}   "
              f"{'domain-specific' if abs(din) > abs(doff)*2 else 'GLOBAL STYLE — report as style, not signature'}")

    print()
    print("P42.3 WITHIN-LINEAGE REPLICATION (Med42 vs OpenBioLLM, shared base)")
    ll = [(t, d, s) for t, d, s in signs.get("llama3", [])]
    if len(ll) >= 2:
        same = len({s for _, _, s in ll}) == 1
        print("  " + ",  ".join(f"{t} {d:+.3f} ({s})" for t, d, s in ll))
        print(f"  P42.3: {'SUPPORTED — same direction, so it is not per-model quirk' if same else 'FALSIFIED — the two fine-tunes disagree; effect is per-model'}")
    else:
        print("  NOT EVALUABLE — fewer than 2 usable tuned models on the llama3 base")

    (OUT / "profiled.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k != "output"} for r in rows], indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "runs"
    {"runs": stage_runs, "measure": stage_measure}[stage]()
