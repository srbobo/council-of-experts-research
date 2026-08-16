"""ATTAINABILITY PROBE — does a domain fine-tune leave a detectable signature
in HOW it reasons, separable from surface form?

NOT a cell. This is checklist item 12 applied before registering anything:
it measures whether the proposed instrument has resolution, and what n a
real cell would need. It licenses no claim about approach.

THE DESIGN QUESTION IT SERVES. "Specialist vs generalist" moves
architecture, identity, training data and scale at once (audit #3, P36.2).
The way around it is CROSSED domain x base-family:

    medical fine-tune A  (Meditron3)  <- base Qwen2.5-7B
    medical fine-tune B  (BioMistral) <- base Mistral-7B

If domain training induces an approach, the A-minus-its-base delta and the
B-minus-its-base delta should point the SAME way despite sharing no lineage.
That is the only contrast here that identity cannot explain.

CONTROLS, all forced by the seat-approach pilot (commit df644bd):
  - identical prompt to every producer: no role text, no domain framing, so
    topic cannot drive the signature
  - same items for every producer
  - surface features reported beside every content number, because two
    GENERALISTS already separate at AUC 0.945 on length alone

INSTRUMENT. A frozen framework inventory -- containment checks against a
fixed list, the same basis as Cell 37's numeral check, not regex-as-NLP.
Counts are normalised per 1k characters so verbosity cannot buy signal.

Run:  .venv/bin/python train/run_probe_domain_signature.py runs
      .venv/bin/python train/run_probe_domain_signature.py measure
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                    # noqa: E402

OUT = ROOT / "bench" / "analysis" / "probe_domain"
RUNS = ROOT / "bench" / "runs" / "probe_domain_signature.jsonl"
REPEATS = 2

# (label, ollama tag, family, kind) -- kind: "tuned" | "base"
PRODUCERS = [
    ("meditron3", "huggingface.co/mradermacher/Meditron3-Qwen2.5-7B-GGUF:Q4_K_M",
     "qwen2.5", "tuned"),
    ("qwen2.5",   "qwen2.5:7b-instruct", "qwen2.5", "base"),
    ("biomistral", "hf.co/MaziyarPanahi/BioMistral-7B-GGUF:Q4_K_M",
     "mistral", "tuned"),
    ("mistral",   "mistral:7b-instruct-v0.3-q4_K_M", "mistral", "base"),
]

# IDENTICAL for every producer. No role, no domain cue, no format dictation
# beyond length -- the pilot showed format is where spurious signal lives.
PROMPT = ("You are an analyst. Give a substantive written analysis of the "
          "situation below for a decision-maker. Be specific and concrete.")

# Half in the fine-tunes' domain, half outside it. If the signature is real
# it should be DOMAIN-SPECIFIC, not a global style difference.
ITEMS = [
    ("hc", "case_1_clinical_decision_support"),
    ("hc", "case_4_glp1_employer_coverage"),
    ("hc", "case_8_trigger_light_hand_hygiene"),
    ("off", "case_9_trigger_light_nda_clauses"),
    ("off", "case_10_trigger_light_depreciation"),
    ("off", "case_l1_l1a"),
]

# FROZEN inventory -- fixed before any run of this probe.
FRAMEWORKS = {
    "healthcare": ["differential diagnosis", "standard of care",
                   "number needed to treat", "sensitivity", "specificity",
                   "ISO 14971", "IRB", "clinical evaluation", "510(k)",
                   "post-market surveillance", "contraindication",
                   "comorbidity", "guideline", "evidence base", "cohort",
                   "randomized", "adverse event", "clinical trial"],
    "legal": ["black-letter", "holding", "dicta", "statutory", "case law",
              "preemption", "lawful basis", "DPIA", "safe harbour",
              "indemnif", "force majeure", "jurisdiction"],
    "finance": ["DCF", "discounted cash flow", "unit economics", "actuarial",
                "capital adequacy", "break-even", "IRR", "EBITDA",
                "reserve", "payer mix", "WACC", "amortiz"],
}


def profile(text: str) -> dict:
    lo = text.lower()
    per_k = max(len(text) / 1000, 1e-9)
    out = {f"fw_{d}": sum(1 for k in ks if k.lower() in lo) / per_k
           for d, ks in FRAMEWORKS.items()}
    lines = [l for l in text.split("\n") if l.strip()]
    toks = [w.lower().strip(".,;:()[]\"'*#") for w in text.split()]
    toks = [w for w in toks if w]
    sents = [s for s in text.replace("!", ".").replace("?", ".").split(".")
             if 15 < len(s) < 600]
    out.update({
        "chars": len(text),
        "mean_sent_len": sum(len(s) for s in sents) / max(len(sents), 1),
        "list_frac": sum(1 for l in lines if l.lstrip()[:2] in ("- ", "* "))
                     / max(len(lines), 1),
        "ttr": len(set(toks)) / max(len(toks), 1),
    })
    return out


def stage_runs() -> None:
    from examples.test_cases import get_case
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RUNS.exists():
        for line in RUNS.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    todo = [(p, it, r) for p in PRODUCERS for it in ITEMS
            for r in range(REPEATS)
            if f"{p[0]}__{it[1]}__r{r}" not in done]
    print(f"probe: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0, fails = time.time(), 0
    with RUNS.open("a") as fh:
        for k, ((lbl, tag, fam, kind), (dom, case), rep) in enumerate(todo):
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
                                 "domain": dom, "case": case, "repeat": rep,
                                 "output": txt}, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 6 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print("probe runs complete")


def stage_measure() -> None:
    import math
    import random
    rng = random.Random(0)
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    for r in rows:
        r.update(profile(r["output"]))

    def sel(prod, dom=None):
        return [r for r in rows if r["producer"] == prod
                and (dom is None or r["domain"] == dom)]

    def mean(v, k):
        return sum(x[k] for x in v) / len(v) if v else float("nan")

    print("=" * 78)
    print("ATTAINABILITY PROBE — domain signature, crossed over base family")
    print("=" * 78)
    print(f"  {'producer':<12}{'kind':<7}{'n':>4}{'chars':>8}{'list':>7}{'ttr':>7}"
          f"{'fw_hc/k':>9}{'fw_lg/k':>9}{'fw_fi/k':>9}")
    for lbl, _tag, fam, kind in PRODUCERS:
        v = sel(lbl)
        if not v:
            continue
        print(f"  {lbl:<12}{kind:<7}{len(v):>4}{mean(v,'chars'):>8.0f}"
              f"{mean(v,'list_frac'):>7.3f}{mean(v,'ttr'):>7.3f}"
              f"{mean(v,'fw_healthcare'):>9.3f}{mean(v,'fw_legal'):>9.3f}"
              f"{mean(v,'fw_finance'):>9.3f}")

    print()
    print("THE CROSSED TEST — does the medical delta replicate across lineages?")
    print("  (tuned minus its OWN base, on IN-DOMAIN items; identity cannot")
    print("   explain a delta that repeats on two unrelated bases)")
    deltas = {}
    for tuned, base, fam in (("meditron3", "qwen2.5", "qwen2.5"),
                             ("biomistral", "mistral", "mistral")):
        for dom in ("hc", "off"):
            a, b = sel(tuned, dom), sel(base, dom)
            if not a or not b:
                continue
            d = mean(a, "fw_healthcare") - mean(b, "fw_healthcare")
            deltas[(fam, dom)] = d
            print(f"  {fam:<9} {dom:<4} fw_healthcare/k  "
                  f"{mean(b,'fw_healthcare'):.3f} -> {mean(a,'fw_healthcare'):.3f}"
                  f"   delta {d:+.3f}")
    # DEGENERACY GUARD (finding #6). An arm that barely writes scores 0.000
    # on every per-kchar content measure for want of text, not for want of
    # frameworks. Such an arm is uninterpretable and its lineage drops out.
    DEGEN = 800
    degen = {lbl: sum(1 for r in sel(lbl) if r["chars"] < DEGEN)
             for lbl, *_ in PRODUCERS}
    print()
    print(f"  DEGENERACY (<{DEGEN} chars): "
          + "  ".join(f"{k} {v}/{len(sel(k))}" for k, v in degen.items()))
    dead = {k for k, v in degen.items() if v > len(sel(k)) / 2}
    if dead:
        print(f"  UNINTERPRETABLE ARMS: {sorted(dead)} — their 0.000 content")
        print("  rates reflect absent text. Their lineage is dropped.")

    hc = {"qwen2.5": deltas.get(("qwen2.5", "hc")),
          "mistral": deltas.get(("mistral", "hc"))}
    live = {f: d for f, d in hc.items() if d is not None
            and not ({"meditron3", "qwen2.5"} & dead if f == "qwen2.5"
                     else {"biomistral", "mistral"} & dead)}
    print()
    if len(live) < 2:
        print(f"  CROSSED TEST NOT EVALUABLE — only {len(live)} usable lineage(s).")
        print("  Replication across base families is the ONLY contrast identity")
        print("  cannot explain, so a single lineage licenses nothing.")
        for f, d in live.items():
            print(f"    surviving lineage {f}: delta {d:+.3f} "
                  f"({'SUPPORTS' if d > 0 else 'CONTRADICTS'} the hypothesis, "
                  f"which predicts tuned > base)")
    else:
        vals = list(live.values())
        agree = (vals[0] > 0) == (vals[1] > 0)
        supports = agree and vals[0] > 0
        print(f"  in-domain deltas: " + ", ".join(f"{f} {d:+.3f}"
                                                  for f, d in live.items()))
        print(f"  -> {'SAME' if agree else 'OPPOSITE'} direction; "
              f"{'SUPPORTS' if supports else 'CONTRADICTS' if agree else 'NO replicable signature'}"
              f" the hypothesis (predicted: tuned > base)")

    print()
    print("SURFACE CONFOUND CHECK (the pilot: 2 generalists separate at AUC 0.945)")

    def auc(a, b):
        return (sum((1. if x > y else .5 if x == y else 0.) for x in a for y in b)
                / (len(a) * len(b))) if a and b else float("nan")
    for tuned, base in (("meditron3", "qwen2.5"), ("biomistral", "mistral")):
        for k in ("chars", "list_frac", "ttr"):
            a = [x[k] for x in sel(tuned)]
            b = [x[k] for x in sel(base)]
            print(f"  {tuned:>11} vs {base:<11} {k:<14} AUC {auc(a,b):.3f}")

    print()
    print("ATTAINABILITY — n per producer for the observed in-domain effect")
    for tuned, base in (("meditron3", "qwen2.5"), ("biomistral", "mistral")):
        a = [x["fw_healthcare"] for x in sel(tuned, "hc")]
        b = [x["fw_healthcare"] for x in sel(base, "hc")]
        if len(a) < 2 or len(b) < 2:
            continue
        ma, mb = sum(a)/len(a), sum(b)/len(b)
        va = sum((x-ma)**2 for x in a)/max(len(a)-1, 1)
        vb = sum((x-mb)**2 for x in b)/max(len(b)-1, 1)
        sd = math.sqrt((va+vb)/2)
        d = abs(ma-mb)/sd if sd > 0 else float("inf")
        n = math.ceil(2*(1.959964+0.8416212)**2/d**2) if d > 0 else float("inf")
        print(f"  {tuned:>11} vs {base:<11} Cohen d {d:5.2f}  "
              f"-> n/producer {n if n != float('inf') else '-'} for 80% power")
    print("\n  NOTE: probe n is tiny by design. These are ORDER-OF-MAGNITUDE")
    print("  sizings to decide whether a real cell is worth running, not results.")
    (OUT / "profiled.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k != "output"} for r in rows], indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "runs"
    {"runs": stage_runs, "measure": stage_measure}[stage]()
