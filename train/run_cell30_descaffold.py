"""Cell 30 — the de-scaffolded replication.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 30 PRE-REGISTRATION".
Prompts, instrument, and predictions FROZEN there.

The point: every prior w estimate came from a system whose INSTRUCTIONS and
whose INSTRUMENT shared vocabulary (audit #2, finding #8). Here neither the
seats nor the writer are told any family name or phrasing, and measurement
is by dual judges with verbatim-quote verification.

Stages (idempotent, cached under bench/analysis/cell30/):
  seats     3 de-scaffolded domain roles x 9 cases
  variants  ablation supply sweep (construction only)
  runs      gpt-oss x2 repeats + phi4 x1 repeat over every variant
  judge     dual-judge document-level labelling, quote-verified
  measure   P30.0-P30.4

Run:  .venv/bin/python train/run_cell30_descaffold.py seats
      ... variants / runs / judge / measure
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

from train.run_cell25_moa import CASES, chat  # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell30"
RUNS = ROOT / "bench" / "runs" / "cell30_descaffold.jsonl"
WRITERS = [("gpt-oss:20b", 2), ("phi4:14b", 1)]
JUDGES = ["gpt-oss:20b", "qwen2.5:7b-instruct"]
FAMS = ("cutoff", "modeled", "jurisd", "hedging")

# ---------------------------------------------------------------------------
# DE-SCAFFOLDED PROMPTS — frozen. No family names, no uncertainty instruction,
# no phrase dictation. Compare council/prompts.py, which names all four
# families and dictates the strings "modeled at" and "assumed".
# ---------------------------------------------------------------------------
SEATS = {
    "healthcare": "You are a healthcare analyst advising a decision-maker. "
                  "Provide a substantive analysis of the healthcare aspects of "
                  "the question below. Be specific and concrete.",
    "legal": "You are a legal analyst advising a decision-maker. Provide a "
             "substantive analysis of the legal aspects of the question below. "
             "Be specific and concrete.",
    "finance": "You are a financial analyst advising a decision-maker. Provide "
               "a substantive analysis of the financial aspects of the question "
               "below. Be specific and concrete.",
}

WRITER_PROMPT = ("You are the lead analyst. Several specialists have written "
                 "the contributions below. Write the final answer to the "
                 "decision-maker's question.")

# Frozen Cell 23 definitions, unchanged.
DEFS = {
    "cutoff": "The writer says their information may be outdated or should be verified.",
    "modeled": "The writer labels a number or estimate as an assumption.",
    "jurisd": "The writer treats different jurisdictions or regulatory regimes separately.",
    "hedging": "The writer states conditions under which the claim could change or vary.",
}

JUDGE_PROMPT = """Below is an analyst's written response. For each property, \
decide whether the response exhibits it. If it does, quote ONE sentence \
copied EXACTLY from the response that demonstrates it.

{defs}

RESPONSE:
{text}

Reply with STRICT JSON and nothing else:
{{"cutoff": {{"present": true, "quote": "..."}}, "modeled": {{...}}, \
"jurisd": {{...}}, "hedging": {{...}}}}
Use "quote": "" when present is false. Quotes must be copied verbatim."""

_WS = re.compile(r"\s+")


def norm(t: str) -> str:
    return _WS.sub(" ", t or "").strip().lower()


# ------------------------------------------------------------------ stages
def stage_seats() -> None:
    from examples.test_cases import get_case
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "seats.json"
    done = json.loads(path.read_text()) if path.exists() else {}
    t0 = time.time()
    for case in CASES:
        done.setdefault(case, {})
        for role, sysmsg in SEATS.items():
            if done[case].get(role):
                continue
            print(f"seat {case[:34]} / {role} ({time.time()-t0:.0f}s)", flush=True)
            txt = chat("gpt-oss:20b", sysmsg, get_case(case).prompt,
                       temperature=0.7, max_tokens=4096)
            if txt and txt.strip():
                done[case][role] = txt
                path.write_text(json.dumps(done, ensure_ascii=False))
    missing = [(c, r) for c in CASES for r in SEATS if not done.get(c, {}).get(r)]
    print(f"seats complete: {27-len(missing)}/27" + (f" MISSING {missing}" if missing else ""))


def stage_variants() -> None:
    from gst.corpus import supply_variants
    seats = json.loads((OUT / "seats.json").read_text())
    out = []
    for case in CASES:
        up = [seats[case][r] for r in SEATS if seats[case].get(r)]
        for vid, (supply_regex, variant, _f) in enumerate(supply_variants(up)):
            out.append({"case": case, "variant_id": vid,
                        "supply_regex_construction": supply_regex,
                        "upstream": variant})
    (OUT / "variants.json").write_text(json.dumps(out, ensure_ascii=False))
    print(f"variants: {len(out)}  (regex construction levels only; measured "
          f"supply comes from the judges)")


def stage_runs() -> None:
    from examples.test_cases import get_case
    variants = json.loads((OUT / "variants.json").read_text())
    done = set()
    if RUNS.exists():
        for line in RUNS.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    todo = [(v, writer, rep)
            for v in variants
            for writer, reps in WRITERS
            for rep in range(reps)
            if f"{v['case']}__v{v['variant_id']}__{writer}__r{rep}" not in done]
    print(f"runs: {len(todo)} to go ({len(done)} cached)", flush=True)
    t0 = time.time()
    with RUNS.open("a") as fh:
        for i, (v, writer, rep) in enumerate(todo):
            rid = f"{v['case']}__v{v['variant_id']}__{writer}__r{rep}"
            body = "\n\n".join(f"--- SPECIALIST CONTRIBUTION ---\n{t}"
                               for t in v["upstream"] if t)
            user = (f"{body}\n\nQuestion:\n{get_case(v['case']).prompt}")
            txt = chat(writer, WRITER_PROMPT, user, temperature=0.6, max_tokens=8192)
            if not txt or not txt.strip():
                print(f"  EMPTY {rid} — recorded failed, not scored", flush=True)
                continue
            fh.write(json.dumps({
                "run_id": rid, "prompt_id": v["case"], "variant_id": v["variant_id"],
                "writer": writer, "repeat": rep,
                "upstream": [t for t in v["upstream"] if t], "output": txt,
            }, ensure_ascii=False) + "\n")
            fh.flush()
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)} {rid[:58]} {el:.0f}s "
                  f"~{el/(i+1)*(len(todo)-i-1):.0f}s left", flush=True)
    print("runs complete")


def _judge_one(model: str, text: str) -> dict | None:
    prompt = JUDGE_PROMPT.format(
        defs="\n".join(f"- {f}: {DEFS[f]}" for f in FAMS), text=text[:14000])
    raw = chat(model, None, prompt, temperature=0, max_tokens=2048)
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
    out = {}
    for f in FAMS:
        v = obj.get(f)
        if not isinstance(v, dict) or not isinstance(v.get("present"), bool):
            return None
        out[f] = {"present": v["present"], "quote": str(v.get("quote") or "")}
    return out


def stage_judge() -> None:
    """Judge every distinct text once: each variant's upstream and each output."""
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    path = OUT / "judged.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    items: dict[str, str] = {}
    for r in rows:
        items[f"out::{r['run_id']}"] = r["output"]
        items[f"up::{r['prompt_id']}::{r['variant_id']}"] = "\n\n".join(r["upstream"])
    todo = [k for k in items if k not in cache]
    print(f"judge: {len(todo)} texts x {len(JUDGES)} judges "
          f"({len(cache)} cached)", flush=True)
    t0 = time.time()
    for i, key in enumerate(todo):
        text = items[key]
        verdicts = {}
        for j in JUDGES:
            v = _judge_one(j, text)
            if v:  # quote verification
                nt = norm(text)
                for f in FAMS:
                    q = norm(v[f]["quote"])
                    v[f]["verified"] = bool(
                        v[f]["present"] and len(q) >= 15 and q in nt)
            verdicts[j] = v
        cache[key] = verdicts
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)}  {el:.0f}s ~{el/(i+1)*(len(todo)-i-1):.0f}s left",
                  flush=True)
            path.write_text(json.dumps(cache, ensure_ascii=False))
    path.write_text(json.dumps(cache, ensure_ascii=False))
    print("judge complete")


# ----------------------------------------------------------------- measure
def _families(verdicts: dict) -> set[str] | None:
    """Both judges agree AND (for positives) the quote verified."""
    vs = [verdicts.get(j) for j in JUDGES]
    if any(v is None for v in vs):
        return None
    out = set()
    for f in FAMS:
        votes = [v[f]["present"] and v[f].get("verified", False) for v in vs]
        if all(votes):
            out.add(f)
    return out


def stage_measure() -> None:
    import random

    from gst.instruments import RegexInstrument
    from gst.stats import bootstrap_ols, wilson_ci
    rx = RegexInstrument()
    rng = random.Random(0)

    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    cache = json.loads((OUT / "judged.json").read_text())

    # ---- P30.0 judge validity
    agree = tot = unusable = unverified = 0
    for key, verdicts in cache.items():
        vs = [verdicts.get(j) for j in JUDGES]
        if any(v is None for v in vs):
            unusable += 1
            continue
        for f in FAMS:
            tot += 1
            agree += int(vs[0][f]["present"] == vs[1][f]["present"])
            for v in vs:
                unverified += int(v[f]["present"] and not v[f].get("verified"))
    jj = agree / tot if tot else float("nan")
    print("=" * 74)
    print(f"P30.0 judge agreement = {jj:.3f} ({agree}/{tot} decisions); "
          f"unusable texts {unusable}; unverified positive quotes {unverified}")
    if jj < 0.70:
        print("P30.0 FAILED — instrument invalid; all other predictions NOT "
              "EVALUABLE per registration")
        return
    print("P30.0 PASS")

    # ---- assemble measured records
    recs = []
    for r in rows:
        up = _families(cache.get(f"up::{r['prompt_id']}::{r['variant_id']}", {}))
        out = _families(cache.get(f"out::{r['run_id']}", {}))
        if up is None or out is None or len(r["output"]) < 500:
            continue
        recs.append({**r, "s": len(up), "y": len(out),
                     "inv": len(out - up), "up": up, "out": out,
                     "s_rx": len(rx.families("\n\n".join(r["upstream"]))),
                     "inv_rx": len(rx.families(r["output"])
                                   - rx.families("\n\n".join(r["upstream"])))})
    print(f"\nmeasured runs: {len(recs)}")
    levels = sorted({r["s"] for r in recs})
    print(f"judge-measured supply levels: {levels}")
    strata = {s: [r["y"] for r in recs if r["s"] == s] for s in levels}
    print("  " + "  ".join(f"s={s}:{sum(v)/len(v):.2f}(n={len(v)})"
                           for s, v in strata.items()))

    def fit(sub, label):
        if len({r["s"] for r in sub}) < 3:
            print(f"{label}: NOT EVALUABLE — supply spans "
                  f"{len({r['s'] for r in sub})} levels (< 3)")
            return None
        f = bootstrap_ols([float(r["s"]) for r in sub],
                          [float(r["y"]) for r in sub], seed=0)
        print(f"{label}: w={f.slope:.3f} [{f.slope_ci[0]:.3f},{f.slope_ci[1]:.3f}]  "
              f"c={f.intercept:.3f} [{f.intercept_ci[0]:.3f},{f.intercept_ci[1]:.3f}]"
              f"  n={f.n}")
        return f

    print()
    print("=" * 74)
    prim = [r for r in recs if r["writer"] == "gpt-oss:20b"]
    f1 = fit(prim, "P30.1 primary writer (gpt-oss)")
    if f1:
        print(f"P30.1: {'SUPPORTED' if f1.slope_ci[0] > 0 else 'FALSIFIED'}")

    print("=" * 74)
    z = [r["inv"] for r in recs if r["s"] == 0]
    if z:
        k = sum(1 for v in z if v > 0)
        ci = wilson_ci(k, len(z))
        print(f"P30.2 zero-supply invention (pooled writers): {k}/{len(z)} = "
              f"{k/len(z):.3f} [{ci[0]:.3f},{ci[1]:.3f}] -> "
              f"{'SUPPORTED' if ci[0] > 0 else 'FALSIFIED'}")
    else:
        print("P30.2: no judge-measured zero-supply runs — NOT EVALUABLE")

    print("=" * 74)
    sec = [r for r in recs if r["writer"] == "phi4:14b"]
    f2 = fit(sec, "P30.3 second writer (phi4)")
    z2 = [r["inv"] for r in sec if r["s"] == 0]
    if z2:
        k2 = sum(1 for v in z2 if v > 0)
        ci2 = wilson_ci(k2, len(z2))
        ok = bool(f2 and f2.slope_ci[0] > 0) and ci2[0] > 0
        print(f"  phi4 zero-supply invention: {k2}/{len(z2)} "
              f"[{ci2[0]:.3f},{ci2[1]:.3f}]")
        print(f"P30.3: {'SUPPORTED' if ok else 'FALSIFIED'}")

    print("=" * 74)
    inv_j = sum(1 for r in recs if r["inv"] > 0) / len(recs)
    inv_r = sum(1 for r in recs if r["inv_rx"] > 0) / len(recs)
    print(f"P30.4 invention rate: regex {inv_r:.3f} vs judge {inv_j:.3f} -> "
          f"{'SUPPORTED (regex under-counts)' if inv_r < inv_j else 'FALSIFIED'}")
    sj = sum(r["s"] for r in recs) / len(recs)
    sr = sum(r["s_rx"] for r in recs) / len(recs)
    print(f"  mean supply: regex {sr:.2f} vs judge {sj:.2f}")
    (OUT / "measured.json").write_text(json.dumps(
        [{k: (sorted(v) if isinstance(v, set) else v) for k, v in r.items()
          if k not in ("upstream", "output")} for r in recs], indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "seats"
    {"seats": stage_seats, "variants": stage_variants, "runs": stage_runs,
     "judge": stage_judge, "measure": stage_measure}[stage]()
