"""Cell 25 — the shrinkage law on a Mixture-of-Agents architecture.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 25 PRE-REGISTRATION".
Architecture, prompts, temperatures, populations and predictions are FROZEN
there. Same writer as the council arms by design; supply manipulated by
programmatic ablation so zero-supply is measured, not extrapolated.

Stages (idempotent, cached):
  propose   3 general proposers x 9 cases            -> bench/analysis/cell25/proposals.json
  variants  ablation supply sweep + FLUENCY GATE     -> bench/analysis/cell25/variants.json
  aggregate MoA aggregator over every variant x2     -> bench/runs/cell25_moa.jsonl
  measure   parameter card + P25.1-25.3 verdicts

Run:  .venv/bin/python train/run_cell25_moa.py propose
      .venv/bin/python train/run_cell25_moa.py variants
      (manual fluency inspection per registration)
      .venv/bin/python train/run_cell25_moa.py aggregate
      .venv/bin/python train/run_cell25_moa.py measure
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

OUT = ROOT / "bench" / "analysis" / "cell25"
RUNS = ROOT / "bench" / "runs" / "cell25_moa.jsonl"
OLLAMA = "http://127.0.0.1:11434/api/chat"

PROPOSERS = ["phi4:14b", "qwen2.5:7b-instruct", "mistral:7b-instruct-v0.3-q4_K_M"]
AGGREGATOR = "gpt-oss:20b"
CASES = ['case_1_clinical_decision_support', 'case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract', 'case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion', 'case_6_trigger_heavy_biotech_ma',
         'case_8_trigger_light_hand_hygiene', 'case_9_trigger_light_nda_clauses',
         'case_10_trigger_light_depreciation']
REPEATS = 2

# Wang et al. 2024, "Mixture-of-Agents Enhances Large Language Model
# Capabilities" — aggregation prompt, verbatim.
MOA_PROMPT = """You have been provided with a set of responses from various \
open-source models to the latest user query. Your task is to synthesize \
these responses into a single, high-quality response. It is crucial to \
critically evaluate the information provided in these responses, recognizing \
that some of it may be biased or incorrect. Your response should not simply \
replicate the given answers but should offer a refined, accurate, and \
comprehensive reply to the instruction. Ensure your response is \
well-structured, coherent, and adheres to the highest standards of accuracy \
and reliability.

Responses from models:"""


def chat(model: str, system: str | None, user: str, *, temperature: float,
         max_tokens: int) -> str | None:
    msgs = ([{"role": "system", "content": system}] if system else []) + \
        [{"role": "user", "content": user}]
    body = json.dumps({"model": model, "messages": msgs, "stream": False,
                       "options": {"temperature": temperature,
                                   "num_predict": max_tokens}}).encode()
    req = urllib.request.Request(OLLAMA, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=900) as fh:
            return json.loads(fh.read())["message"]["content"]
    except Exception as e:                                     # noqa: BLE001
        print("  call failed:", model, e, flush=True)
        return None


def stage_propose() -> None:
    from examples.test_cases import get_case
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "proposals.json"
    done = json.loads(path.read_text()) if path.exists() else {}
    t0 = time.time()
    for case in CASES:
        done.setdefault(case, {})
        for model in PROPOSERS:
            if done[case].get(model):
                continue
            print(f"propose {case} / {model} ({time.time()-t0:.0f}s)", flush=True)
            txt = chat(model, None, get_case(case).prompt,
                       temperature=0.7, max_tokens=4096)
            if txt and txt.strip():
                done[case][model] = txt
                path.write_text(json.dumps(done, ensure_ascii=False))
    missing = [(c, m) for c in CASES for m in PROPOSERS if not done.get(c, {}).get(m)]
    print(f"proposals complete: {27 - len(missing)}/27" +
          (f"  MISSING: {missing}" if missing else ""))


def _injection_bank() -> dict[str, dict[str, str]]:
    """case -> family -> one verbatim single-family specialist sentence.

    Drawn from stored council runs for the same case (registered deviation):
    deterministic, seed-free (first qualifying sentence in sorted-file
    order), each sentence firing exactly ONE family, 40-400 chars.
    """
    import re

    from gst.instruments import RegexInstrument
    rx = RegexInstrument()
    bank: dict[str, dict[str, str]] = {c: {} for c in CASES}
    sent_split = re.compile(r'(?<=[.!?])\s+')
    for p in sorted((ROOT / "bench/runs/imported").glob("*.json")):
        d = None
        for case in CASES:
            if f"__{case}__" in p.name:
                try:
                    d = json.loads(p.read_text())
                except (OSError, json.JSONDecodeError):
                    d = None
                break
        if not d:
            continue
        case = d.get("case_id")
        if case not in bank or len(bank[case]) == 4:
            continue
        turns = (d.get("deliberation") or {}).get("turns") or []
        for t in turns:
            for s in sent_split.split(t.get("output_text") or ""):
                s = s.strip()
                if not 40 <= len(s) <= 400:
                    continue
                fams = rx.families(s)
                if len(fams) == 1:
                    f = next(iter(fams))
                    bank[case].setdefault(f, s)
    return bank


def stage_variants() -> None:
    from gst.corpus import supply_variants
    from gst.instruments import RegexInstrument
    rx = RegexInstrument()
    props = json.loads((OUT / "proposals.json").read_text())
    bank = _injection_bank()
    out = []
    for case in CASES:
        upstream = [props[case][m] for m in PROPOSERS if props[case].get(m)]
        # downward: ablation sweep (original registration)
        natural: set[str] = set()
        for vid, (supply, variant, fams) in enumerate(supply_variants(upstream)):
            out.append({"case": case, "variant_id": vid, "supply": supply,
                        "families": sorted(fams), "upstream": variant,
                        "construction": "ablation"})
            natural |= fams
        # upward: injection sweep (registered deviation) — append verbatim
        # single-family specialist sentences for families not naturally present
        missing = [f for f in ("cutoff", "modeled", "jurisd", "hedging")
                   if f not in natural and f in bank[case]]
        vid = 100
        aug = list(upstream)
        injected: list[str] = []
        for f in missing:
            aug = list(aug)
            aug[-1] = aug[-1] + "\n\n" + bank[case][f]
            injected.append(f)
            got = rx.families("\n\n".join(aug))
            out.append({"case": case, "variant_id": vid,
                        "supply": len(got), "families": sorted(got),
                        "upstream": aug, "construction": f"injection:{'+'.join(injected)}"})
            vid += 1
    (OUT / "variants.json").write_text(json.dumps(out, ensure_ascii=False))
    by_s: dict[int, int] = {}
    for v in out:
        by_s[v["supply"]] = by_s.get(v["supply"], 0) + 1
    print(f"variants: {len(out)} across supply levels {dict(sorted(by_s.items()))}")
    n_missing_bank = sum(1 for c in CASES for f in ("cutoff", "modeled", "jurisd", "hedging")
                         if f not in bank[c])
    print(f"injection bank gaps (family unavailable in stored seats): {n_missing_bank}")
    print("REGISTERED STOP CONDITION: manually inspect 10 random variants "
          "(ablated AND injected) for ungrammatical residue before `aggregate`.")


def stage_aggregate() -> None:
    from examples.test_cases import get_case
    variants = json.loads((OUT / "variants.json").read_text())
    done: set[str] = set()
    if RUNS.exists():
        for line in RUNS.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    t0 = time.time()
    todo = [(v, rep) for v in variants for rep in range(REPEATS)
            if f"{v['case']}__v{v['variant_id']}__r{rep}" not in done]
    print(f"aggregate: {len(todo)} calls to run ({len(done)} cached)", flush=True)
    with RUNS.open("a") as fh:
        for i, (v, rep) in enumerate(todo):
            run_id = f"{v['case']}__v{v['variant_id']}__r{rep}"
            body = MOA_PROMPT + "\n\n" + "\n\n".join(
                f"{j+1}. {t}" for j, t in enumerate(v["upstream"]) if t)
            user = f"{body}\n\nUser query:\n{get_case(v['case']).prompt}"
            txt = chat(AGGREGATOR, None, user, temperature=0.6, max_tokens=8192)
            if not txt or not txt.strip():
                print(f"  EMPTY reply on {run_id} — recorded as failed, not scored",
                      flush=True)
                continue
            fh.write(json.dumps({
                "run_id": run_id, "prompt_id": v["case"],
                "upstream": [t for t in v["upstream"] if t],
                "output": txt, "condition": "moa-l1",
                "writer_id": AGGREGATOR,
                "supply_registered": v["supply"],
                "variant_id": v["variant_id"], "repeat": rep,
            }, ensure_ascii=False) + "\n")
            fh.flush()
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)}  {run_id[:60]}  {el:.0f}s "
                  f"~{el/(i+1)*(len(todo)-i-1):.0f}s left", flush=True)
    print("aggregate complete")


def stage_measure() -> None:
    import random

    from gst.adapters import FieldMap, from_jsonl
    from gst.card import measure_all
    from gst.instruments import RegexInstrument
    from gst.stats import wilson_ci

    rng = random.Random(0)
    fmap = FieldMap(upstream="upstream", output="output", prompt_id="prompt_id",
                    run_id="run_id", condition="condition", writer_id="writer_id")
    recs = from_jsonl(RUNS, fmap)
    card = measure_all(recs, system="moa-l1 (cell 25)")
    print(card.render())

    sh = card.shrinkage
    print("=" * 74)
    if not (sh and sh.identifiable):
        print("P25.1: UNIDENTIFIABLE — design failed its own guard; STOP")
        return
    means = [m for _s, (m, _n) in sorted(sh.strata.items())]
    monotone = all(b >= a - 0.05 for a, b in zip(means, means[1:], strict=False))
    wlo, whi = sh.w_ci if sh.w_ci else (sh.w, sh.w)
    clo, chi = sh.c_ci if sh.c_ci else (sh.c, sh.c)
    # The registered support criterion is CI-based: BOTH corners excluded by
    # the intervals, not merely avoided by the point estimate. (A first
    # version of this check used the point estimate — the exact
    # instrument-says-what-I-wanted class the program audit documented.)
    excludes_register = wlo > 0.15
    excludes_faithful = not (wlo >= 0.85 and chi <= 0.15) and (whi < 0.85 or clo > 0.15)
    corner_register_holds = whi <= 0.15
    corner_faithful_holds = wlo >= 0.85 and chi <= 0.15
    print(f"P25.1 (shrinkage form): w={sh.w:.3f} [{wlo:.3f},{whi:.3f}], "
          f"c={sh.c:.3f} [{clo:.3f},{chi:.3f}], monotone={monotone}, "
          f"flags: weak={sh.weakly_identified} extrap={sh.c_extrapolated}")
    if sh.weakly_identified or sh.c_extrapolated or not monotone \
            or corner_register_holds or corner_faithful_holds:
        print("P25.1: FALSIFIED (a corner holds, monotonicity fails, or a "
              "guard fired)")
    elif excludes_register and excludes_faithful and clo > 0:
        print("P25.1: SUPPORTED (both corners excluded by the CIs)")
    else:
        print("P25.1: PARTIAL — shrinkage direction present (monotone, w CI "
              f"excluding 0: {wlo > 0}) but the registered CI exclusion "
              f"fails: register corner excluded={excludes_register}, "
              f"faithful excluded={excludes_faithful}, c>0 by CI={clo > 0}. "
              "Report as a boundary result, not support.")

    rx = RegexInstrument()
    zero_inv = []
    for r in recs:
        up = rx.families(r.upstream_text)
        if not up and len(r.output) >= 500:
            zero_inv.append(1 if rx.families(r.output) else 0)
    if zero_inv:
        rate = sum(zero_inv) / len(zero_inv)
        ci = wilson_ci(sum(zero_inv), len(zero_inv))
        p252 = rate >= 0.10 and ci[0] > 0
        print(f"P25.2 (invention at s=0): {rate:.3f} [{ci[0]:.2f},{ci[1]:.2f}] "
              f"n={len(zero_inv)} -> {'SUPPORTED' if p252 else 'FALSIFIED'}")
    else:
        print("P25.2: no zero-supply runs survived the floor — design gap, report")

    t_flags, i_flags = [], []
    for r in recs:
        if len(r.output) < 500:
            continue
        up, out = rx.families(r.upstream_text), rx.families(r.output)
        (t_flags if "modeled" in up else i_flags).append(
            1.0 if "modeled" in out else 0.0)
    if t_flags and i_flags:
        ds = []
        for _ in range(5000):
            tb = sum(rng.choice(t_flags) for _ in t_flags) / len(t_flags)
            ib = sum(rng.choice(i_flags) for _ in i_flags) / len(i_flags)
            ds.append(tb - ib)
        ds.sort()
        lo, hi = ds[125], ds[4874]
        d = sum(t_flags) / len(t_flags) - sum(i_flags) / len(i_flags)
        p253 = lo > 0 and hi < 0.85
        print(f"P25.3 (D_modeled): {d:.3f} [{lo:.3f},{hi:.3f}] "
              f"(T n={len(t_flags)}, I n={len(i_flags)}) -> "
              f"{'SUPPORTED' if p253 else 'FALSIFIED'}")
    (OUT / "card.json").write_text(card.to_json())
    print(f"\ncard written to {OUT/'card.json'}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "propose"
    {"propose": stage_propose, "variants": stage_variants,
     "aggregate": stage_aggregate, "measure": stage_measure}[stage]()
