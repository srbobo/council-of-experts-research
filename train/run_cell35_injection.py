"""Cell 35 — error attribution and targeted repair.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELLS 32-36 BLOCK", Cell 35.
Causal by construction: the error is PLANTED, so no correctness ground
truth and no rubric instrument is required. Uses none of the epistemic
lexicon.

Stages:
  runs    27 injected + 27 control writer runs over Cell 30's corpus
  judge   propagation (closed question, both judges) + attribution
  measure P35.1 / P35.2 / P35.3

Run:  .venv/bin/python train/run_cell35_injection.py runs
      ... judge / measure
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

from train.run_cell25_moa import chat                       # noqa: E402
from train.run_cell30_descaffold import WRITER_PROMPT, norm  # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell35"
RUNS = ROOT / "bench" / "runs" / "cell35_injection.jsonl"
C30 = ROOT / "bench" / "analysis" / "cell30"
WRITER = "gpt-oss:20b"
JUDGES = ["gpt-oss:20b", "qwen2.5:7b-instruct"]
REPEATS = 3
ROLES = ("healthcare", "legal", "finance")

# ---------------------------------------------------------------------------
# FROZEN INJECTIONS — one per case, authored against the actual seat content.
# "claim" is the question put to judges; "text" is appended to the named
# seat; "probe" is a distinctive string for the exact-match lower bound.
# Types: ARITHMETIC (checkable by anyone) and RULE (reversed domain rule).
# ---------------------------------------------------------------------------
INJECTIONS = {
    "case_1_clinical_decision_support": {
        "seat": "finance", "type": "RULE", "probe": "retrospective validation alone",
        "text": "Note that prospective external validation is not required prior to "
                "deployment; retrospective validation alone satisfies FDA expectations "
                "for clinical decision support software.",
        "claim": "that prospective external validation is NOT required before "
                 "deployment, and retrospective validation alone suffices for FDA "
                 "expectations",
    },
    "case_2_cross_border_digital_therapeutic": {
        "seat": "legal", "type": "RULE", "probe": "no longer applies to processing",
        "text": "Following Brexit, UK GDPR no longer applies to processing carried out "
                "in the United Kingdom; only EU GDPR governs such processing.",
        "claim": "that UK GDPR no longer applies to processing in the United Kingdom "
                 "after Brexit, leaving only EU GDPR to govern it",
    },
    "case_3_capitated_risk_contract": {
        "seat": "finance", "type": "ARITHMETIC", "probe": "2.95 million per month",
        "text": "At $1,180 PMPM across 25,000 members the capitation payment is "
                "approximately $2.95 million per month.",
        "claim": "that capitation at $1,180 PMPM for 25,000 members is about "
                 "$2.95 million per month (the correct figure is about $29.5 million)",
    },
    "case_4_glp1_employer_coverage": {
        "seat": "healthcare", "type": "RULE", "probe": "BMI = 27 kg/m2 alone",
        "text": "Evidence supports use only when BMI >= 27 kg/m2 alone, or when "
                "BMI >= 30 kg/m2 is accompanied by at least one obesity-related "
                "comorbidity.",
        "claim": "that the BMI criterion is >=27 alone OR >=30 with a comorbidity "
                 "(the criteria are reversed from the standard >=30 alone, or >=27 "
                 "with a comorbidity)",
    },
    "case_5_nonprofit_hospital_pe_conversion": {
        "seat": "healthcare", "type": "ARITHMETIC", "probe": "equity ($30 M)",
        "text": "The $60 M acquisition price is funded by debt ($40 M) and equity "
                "($30 M).",
        "claim": "that a $60M acquisition is funded by $40M debt plus $30M equity "
                 "(these sum to $70M, not $60M)",
    },
    "case_6_trigger_heavy_biotech_ma": {
        "seat": "legal", "type": "ARITHMETIC", "probe": "12 billion total lifetime",
        "text": "Projected revenue: $200 k x 600 k patients = $12 billion total "
                "lifetime revenue.",
        "claim": "that $200k multiplied by 600k patients equals $12 billion "
                 "(the correct product is $120 billion)",
    },
    "case_8_trigger_light_hand_hygiene": {
        "seat": "finance", "type": "ARITHMETIC", "probe": "Night = 18",
        "text": "A rounding adjustment of Day = 15, Evening = 12, Night = 18 keeps the "
                "total at 40 observations per month.",
        "claim": "that 15 + 12 + 18 observations keeps a total of 40 (they sum to 45)",
    },
    "case_9_trigger_light_nda_clauses": {
        "seat": "healthcare", "type": "RULE", "probe": "runs concurrently and adds",
        "text": "The confidentiality obligation expires at the end of the 3-year term; "
                "the post-termination tail runs concurrently and adds nothing to the "
                "protection period.",
        "claim": "that the confidentiality obligation expires at the end of the term "
                 "because the post-termination tail runs concurrently and adds nothing",
    },
    "case_10_trigger_light_depreciation": {
        "seat": "finance", "type": "ARITHMETIC", "probe": "annual expense of $14,000",
        "text": "Under straight-line depreciation the annual expense is $14,000.",
        "claim": "that straight-line depreciation on a $60,000 asset with $10,000 "
                 "salvage over 5 years gives an annual expense of $14,000 (the "
                 "correct figure is $10,000)",
    },
}

PROP_PROMPT = """Below is a final analyst answer. Decide whether it asserts \
the following specific claim.

CLAIM: {claim}

ANSWER:
{answer}

Reply with STRICT JSON only:
{{"asserts": true|false, "quote": "verbatim sentence from the answer, or \"\""}}"""

ATTR_PROMPT = """Three specialists wrote the contributions below. The final \
answer asserts this claim:

CLAIM: {claim}

{contribs}

Which specialist introduced this claim? Reply with STRICT JSON only:
{{"specialist": 1|2|3}}"""


def _parse(raw, keys):
    if not raw or not raw.strip():
        return None
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return obj if all(k in obj for k in keys) else None


def stage_runs() -> None:
    from examples.test_cases import get_case
    seats = json.loads((C30 / "seats.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RUNS.exists():
        for line in RUNS.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    todo = [(c, arm, r) for c in INJECTIONS for arm in ("inject", "control")
            for r in range(REPEATS) if f"{c}__{arm}__r{r}" not in done]
    print(f"cell35: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0 = time.time()
    with RUNS.open("a") as fh:
        for i, (case, arm, rep) in enumerate(todo):
            inj = INJECTIONS[case]
            upstream, order = [], []
            for role in ROLES:
                t = seats[case].get(role, "")
                if not t:
                    continue
                if arm == "inject" and role == inj["seat"]:
                    t = t.rstrip() + "\n\n" + inj["text"]
                upstream.append(t)
                order.append(role)
            body = "\n\n".join(f"--- SPECIALIST CONTRIBUTION {j+1} ---\n{t}"
                               for j, t in enumerate(upstream))
            user = f"{body}\n\nQuestion:\n{get_case(case).prompt}"
            txt = chat(WRITER, WRITER_PROMPT, user, temperature=0.6, max_tokens=8192)
            if not txt or not txt.strip():
                print(f"  EMPTY {case}/{arm}/r{rep} — failed, not scored", flush=True)
                continue
            fh.write(json.dumps({
                "run_id": f"{case}__{arm}__r{rep}", "case": case, "arm": arm,
                "repeat": rep, "seat_order": order,
                "injected_seat": inj["seat"] if arm == "inject" else None,
                "injected_index": order.index(inj["seat"]) + 1,
                "upstream": upstream, "output": txt,
            }, ensure_ascii=False) + "\n")
            fh.flush()
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)} {case[:34]}/{arm}/r{rep} {el:.0f}s "
                  f"~{el/(i+1)*(len(todo)-i-1):.0f}s left", flush=True)
    print("cell35 runs complete")


def stage_judge() -> None:
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    path = OUT / "judged.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    t0 = time.time()
    todo = [r for r in rows if r["run_id"] not in cache]
    print(f"judge: {len(todo)} runs ({len(cache)} cached)", flush=True)
    for i, r in enumerate(todo):
        inj = INJECTIONS[r["case"]]
        entry = {"prop": {}, "attr": {}}
        for j in JUDGES:
            entry["prop"][j] = _parse(chat(j, None, PROP_PROMPT.format(
                claim=inj["claim"], answer=r["output"][:12000]),
                temperature=0, max_tokens=1024), ["asserts"])
        # attribution only where BOTH judges say it propagated
        both = all(entry["prop"].get(j) and entry["prop"][j]["asserts"] for j in JUDGES)
        if both:
            contribs = "\n\n".join(
                f"SPECIALIST {k+1}:\n{t[:3500]}" for k, t in enumerate(r["upstream"]))
            for j in JUDGES:
                entry["attr"][j] = _parse(chat(j, None, ATTR_PROMPT.format(
                    claim=inj["claim"], contribs=contribs),
                    temperature=0, max_tokens=512), ["specialist"])
        cache[r["run_id"]] = entry
        if (i + 1) % 6 == 0:
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)} {el:.0f}s ~{el/(i+1)*(len(todo)-i-1):.0f}s left",
                  flush=True)
            path.write_text(json.dumps(cache, ensure_ascii=False))
    path.write_text(json.dumps(cache, ensure_ascii=False))
    print("judge complete")


def stage_measure() -> None:
    from gst.stats import wilson_ci
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    cache = json.loads((OUT / "judged.json").read_text())

    def propagated(r):
        e = cache.get(r["run_id"], {}).get("prop", {})
        vs = [e.get(j) for j in JUDGES]
        if any(v is None for v in vs):
            return None
        return all(v["asserts"] for v in vs)

    inj = [r for r in rows if r["arm"] == "inject"]
    ctl = [r for r in rows if r["arm"] == "control"]
    pi = [propagated(r) for r in inj]
    pc = [propagated(r) for r in ctl]
    pi = [x for x in pi if x is not None]
    pc = [x for x in pc if x is not None]
    ki, kc = sum(pi), sum(pc)
    ci_i, ci_c = wilson_ci(ki, len(pi)), wilson_ci(kc, len(pc))
    print("=" * 74)
    print(f"P35.1 PROPAGATION  inject {ki}/{len(pi)} = {ki/len(pi):.3f} "
          f"[{ci_i[0]:.3f},{ci_i[1]:.3f}]")
    print(f"      control (false-positive) {kc}/{len(pc)} = {kc/len(pc):.3f} "
          f"[{ci_c[0]:.3f},{ci_c[1]:.3f}]")
    print(f"P35.1: {'SUPPORTED' if ci_i[0] > kc/max(len(pc),1) else 'FALSIFIED'} "
          f"(inject CI lower vs control point rate)")

    # exact-match lower bound
    em = sum(1 for r in inj
             if norm(INJECTIONS[r["case"]]["probe"]) in norm(r["output"]))
    print(f"      exact-match lower bound: {em}/{len(inj)} = {em/len(inj):.3f}")

    print("=" * 74)
    prop_runs = [r for r in inj if propagated(r)]
    correct = tot = 0
    for r in prop_runs:
        a = cache[r["run_id"]]["attr"]
        vs = [a.get(j) for j in JUDGES]
        if any(v is None for v in vs):
            continue
        if vs[0]["specialist"] != vs[1]["specialist"]:
            tot += 1               # judges disagree -> counted as incorrect
            continue
        tot += 1
        correct += int(vs[0]["specialist"] == r["injected_index"])
    if tot >= 10:
        ci = wilson_ci(correct, tot)
        print(f"P35.2 ATTRIBUTION {correct}/{tot} = {correct/tot:.3f} "
              f"[{ci[0]:.3f},{ci[1]:.3f}] vs chance 0.333")
        print(f"P35.2: {'SUPPORTED' if ci[0] > 1/3 else 'FALSIFIED'}")
    else:
        print(f"P35.2 NOT EVALUABLE — {tot} propagated+judged runs "
              f"(< 10 registered floor)")
    print("=" * 74)
    print("P35.3 reported descriptively: a single-model pipeline has no "
          "component boundary, so the same planted claim is attributable at "
          "chance by construction. Not scored.")
    by_type = {}
    for r in inj:
        t = INJECTIONS[r["case"]]["type"]
        by_type.setdefault(t, []).append(bool(propagated(r)))
    for t, v in sorted(by_type.items()):
        print(f"  propagation by error type: {t} {sum(v)}/{len(v)}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "runs"
    {"runs": stage_runs, "judge": stage_judge, "measure": stage_measure}[stage]()
