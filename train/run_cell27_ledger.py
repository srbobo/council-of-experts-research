"""Cell 27 — the evidence ledger: externalizing the writer's estimator.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 27 PRE-REGISTRATION".
Protocol, arms, hygiene and predictions FROZEN there.

Stages:
  gate       3-run delimiter-compliance check (registered stop condition)
  l2         ledger writer over the Cell 25 variants (80 runs, primary)
  l1         council pipeline with ledger synthesis (45 runs, secondary)
  measure    cards + P27.1-P27.4

Measurement hygiene: ONLY the text after "### ANSWER" is ever scored; the
ledger section necessarily contains family phrases and is stripped first.
Runs missing the delimiter are quarantined and counted, never pooled.

Run:  .venv/bin/python train/run_cell27_ledger.py gate
      .venv/bin/python train/run_cell27_ledger.py l2
      .venv/bin/python train/run_cell27_ledger.py l1
      .venv/bin/python train/run_cell27_ledger.py measure
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import AGGREGATOR, CASES, OUT as C25_OUT, chat  # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell27"
RUNS_L2 = ROOT / "bench" / "runs" / "cell27_ledger_moa.jsonl"
RUNS_L1 = ROOT / "bench" / "runs" / "imported"
REPEATS = 2
SEEDS_L1 = 5
MODE_L1 = "c27-ledger"
DELIM = "### ANSWER"

LEDGER_PROTOCOL = """You are the lead writer synthesizing contributions \
from several sources into a final answer. Follow this two-phase protocol \
EXACTLY.

PHASE 1 — Output a section headed exactly "### EVIDENCE LEDGER".
Build a table with one row per substantive claim or qualification found in \
the source contributions, with columns:
| claim or qualification | raised by (source number/name) | # sources \
raising it | contested by another source? | verdict |
The verdict must be one of: ADOPT (state it as established), QUALIFY \
(carry it into the answer WITH its qualification), DROP (exclude it, with \
brief reason). Every qualification any source raised must appear as a row. \
If no source raised any qualification, write "NO QUALIFICATION ROWS".

PHASE 2 — Output a section headed exactly "### ANSWER".
Write the final answer. Constraints:
- Every qualification appearing in the answer must correspond to a ledger \
row with verdict QUALIFY.
- If the ledger has no qualification rows, the answer must contain no \
qualifications.
- Do not mention the ledger or this protocol inside the answer."""


def answer_of(text: str) -> str | None:
    """The scored portion. None = protocol violation (quarantine, count)."""
    i = text.find(DELIM)
    if i < 0:
        return None
    return text[i + len(DELIM):].strip()


def ledger_of(text: str) -> str:
    i = text.find(DELIM)
    return text[:max(i, 0)]


def _moa_user(variant: dict, case_prompt: str) -> str:
    body = "\n\n".join(f"{j+1}. {t}" for j, t in enumerate(variant["upstream"]) if t)
    return (f"{LEDGER_PROTOCOL}\n\nSource contributions:\n\n{body}\n\n"
            f"User query:\n{case_prompt}")


def stage_gate() -> None:
    """Registered compliance gate: 3 runs, delimiter check ONLY."""
    from examples.test_cases import get_case
    variants = json.loads((C25_OUT / "variants.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    picks = [variants[0], variants[len(variants) // 2], variants[-1]]
    ok = 0
    for v in picks:
        txt = chat(AGGREGATOR, None, _moa_user(v, get_case(v["case"]).prompt),
                   temperature=0.6, max_tokens=8192)
        comply = bool(txt) and DELIM in txt and "EVIDENCE LEDGER" in txt
        ok += int(comply)
        print(f"  {v['case'][:40]} v{v['variant_id']}: "
              f"{'COMPLIES' if comply else 'VIOLATION'}", flush=True)
    print(f"compliance gate: {ok}/3 " +
          ("PASS — proceed to l2/l1" if ok >= 2 else
           "FAIL — STOP and repair the prompt (registered stop condition)"))


def stage_l2() -> None:
    from examples.test_cases import get_case
    variants = json.loads((C25_OUT / "variants.json").read_text())
    done: set[str] = set()
    if RUNS_L2.exists():
        for line in RUNS_L2.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    todo = [(v, r) for v in variants for r in range(REPEATS)
            if f"{v['case']}__v{v['variant_id']}__r{r}" not in done]
    print(f"l2: {len(todo)} calls ({len(done)} cached)", flush=True)
    t0 = time.time()
    with RUNS_L2.open("a") as fh:
        for i, (v, rep) in enumerate(todo):
            run_id = f"{v['case']}__v{v['variant_id']}__r{rep}"
            txt = chat(AGGREGATOR, None, _moa_user(v, get_case(v["case"]).prompt),
                       temperature=0.6, max_tokens=8192)
            if not txt or not txt.strip():
                print(f"  EMPTY on {run_id} — recorded failed, not scored", flush=True)
                continue
            ans = answer_of(txt)
            fh.write(json.dumps({
                "run_id": run_id, "prompt_id": v["case"],
                "upstream": [t for t in v["upstream"] if t],
                "full_output": txt,
                "output": ans if ans is not None else "",
                "protocol_violation": ans is None,
                "condition": "moa-ledger", "writer_id": AGGREGATOR,
                "variant_id": v["variant_id"], "repeat": rep,
            }, ensure_ascii=False) + "\n")
            fh.flush()
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)}  {run_id[:56]}"
                  f"{'  [VIOLATION]' if ans is None else ''}  {el:.0f}s "
                  f"~{el/(i+1)*(len(todo)-i-1):.0f}s left", flush=True)
    print("l2 complete")


async def _l1_async() -> None:
    import asyncio  # noqa: F401
    from datetime import datetime, timezone

    from council.cabinet import CABINET, GPT_OSS_20B
    from council.models import chat as local_chat
    from council.orchestrator import PHASE_IDS, CabinetBackends, deliberate
    from council.thermal import ThermalGuard
    from examples.test_cases import get_case
    from gst.path import assert_path

    def uniform() -> CabinetBackends:
        async def fn(_m, messages, **kw):
            kw.pop("max_tokens", None)
            return await local_chat(GPT_OSS_20B, messages, max_tokens=8192, **kw)
        return CabinetBackends(**{p: fn for p in PHASE_IDS},
                               name="c27-gptoss-uniform",
                               backend_tags={p: f"ollama:{GPT_OSS_20B.ollama_tag}"
                                             for p in PHASE_IDS})

    thermal = ThermalGuard.from_env()
    for case in CASES:
        have = len(list(RUNS_L1.glob(f"*__{case}__{MODE_L1}.json")))
        for i in range(max(0, SEEDS_L1 - have)):
            print(f"=== {MODE_L1} / {case} [{have+i+1}/{SEEDS_L1}] ===", flush=True)
            try:
                d = await deliberate(get_case(case).prompt, thermal=thermal,
                                     cabinet=uniform(), cabinet_members=CABINET,
                                     synthesis_system_override=LEDGER_PROTOCOL)
            except Exception as e:  # noqa: BLE001
                print("  FAILED:", e, flush=True)
                continue
            syn = d.synthesis.input_messages if d.synthesis else []
            path = assert_path(d.plan.get("routes", []),
                               syn[0]["content"] if syn else "",
                               require_prompt_contains="EVIDENCE LEDGER")
            ans = answer_of(d.final_output or "")
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            (RUNS_L1 / f"{stamp}__{case}__{MODE_L1}.json").write_text(json.dumps({
                "schema_version": 2, "imported": True, "source": "cell27",
                "captured_at": stamp, "case_id": case, "case_title": case,
                "mode": MODE_L1, "model": GPT_OSS_20B.ollama_tag,
                "final_output": ans if ans is not None else (d.final_output or ""),
                "full_output": d.final_output,
                "protocol_violation": ans is None,
                "execution_path": {"routes": path.routes,
                                   "quarantined": path.quarantined,
                                   "reason": path.reason},
                "notes": "evidence-ledger synthesis; ANSWER section only in "
                         "final_output; ledger stripped per registration",
                "deliberation": d.to_dict()}, ensure_ascii=False))
            if path.quarantined or ans is None:
                print(f"  QUARANTINE/VIOLATION: {path.reason or 'no ANSWER delim'}",
                      flush=True)
    print("l1 complete")


def stage_l1() -> None:
    import asyncio
    asyncio.run(_l1_async())


def stage_measure() -> None:
    import random

    from gst.adapters import FieldMap, from_jsonl
    from gst.adapters.coe import from_ledger
    from gst.card import measure_all
    from gst.instruments import RegexInstrument
    from gst.stats import wilson_ci

    rng = random.Random(0)
    rx = RegexInstrument()

    def boot_diff(a, b, draws=5000):
        ds = []
        for _ in range(draws):
            ds.append(sum(rng.choice(a) for _ in a) / len(a)
                      - sum(rng.choice(b) for _ in b) / len(b))
        ds.sort()
        return ds[int(.025 * draws)], ds[int(.975 * draws)]

    fmap = FieldMap(upstream="upstream", output="output", prompt_id="prompt_id",
                    run_id="run_id", condition="condition", writer_id="writer_id")
    l2 = [r for r in from_jsonl(RUNS_L2, fmap) if r.output.strip()]
    raw = [json.loads(x) for x in RUNS_L2.read_text().splitlines() if x.strip()]
    viol = sum(1 for d in raw if d.get("protocol_violation"))
    print(f"L2: {len(raw)} runs, {viol} protocol violations (quarantined)")
    card = measure_all(l2, system="moa-ledger (cell 27 L2)")
    print(card.render())
    (OUT / "card_l2.json").write_text(card.to_json())

    naive = [r for r in from_jsonl(ROOT / "bench/runs/cell25_moa.jsonl", fmap)]

    print("=" * 74)
    sh = card.shrinkage
    if sh and sh.identifiable and sh.w_ci:
        p271 = sh.w_ci[0] > 0.234
        print(f"P27.1 (transport): ledger w={sh.w:.3f} [{sh.w_ci[0]:.3f},"
              f"{sh.w_ci[1]:.3f}] vs naive 0.158 [0.076,0.234] -> "
              f"{'SUPPORTED (disjoint above)' if p271 else 'FALSIFIED (overlap or below)'}"
              + ("  [flags: weak]" if sh.weakly_identified else ""))
    else:
        print("P27.1: unidentifiable — report and stop")

    def zero_inv(recs):
        out = []
        for r in recs:
            if len(r.output) < 500:
                continue
            if not rx.families(r.upstream_text):
                out.append(1.0 if rx.families(r.output) else 0.0)
        return out
    zl, zn = zero_inv(l2), zero_inv(naive)
    if zl and zn:
        lo, hi = boot_diff(zl, zn)
        rl, rn_ = sum(zl) / len(zl), sum(zn) / len(zn)
        cl_ci = wilson_ci(int(sum(zl)), len(zl))
        print(f"P27.2 (invention discipline): ledger s=0 invention {rl:.3f} "
              f"[{cl_ci[0]:.2f},{cl_ci[1]:.2f}] (n={len(zl)}) vs naive {rn_:.3f} "
              f"(n={len(zn)}), diff CI [{lo:+.3f},{hi:+.3f}] -> "
              f"{'SUPPORTED' if hi < 0 else 'FALSIFIED'}")

    def k_contrast(recs):
        one, multi = [], []
        for r in recs:
            if len(r.output) < 500:
                continue
            for f in ("cutoff", "modeled", "jurisd", "hedging"):
                k = sum(1 for t in r.upstream if f in rx.families(t))
                if k == 0:
                    continue
                (one if k == 1 else multi).append(
                    1.0 if f in rx.families(r.output) else 0.0)
        return one, multi
    lo1, lm = k_contrast(l2)
    no1, nm = k_contrast(naive)
    if len(lm) >= 10 and len(nm) >= 10:
        dl = sum(lm) / len(lm) - sum(lo1) / len(lo1)
        dn = sum(nm) / len(nm) - sum(no1) / len(no1)
        did = []
        for _ in range(5000):
            a = sum(rng.choice(lm) for _ in lm) / len(lm) - \
                sum(rng.choice(lo1) for _ in lo1) / len(lo1)
            b = sum(rng.choice(nm) for _ in nm) / len(nm) - \
                sum(rng.choice(no1) for _ in no1) / len(no1)
            did.append(a - b)
        did.sort()
        lo, hi = did[125], did[4874]
        print(f"P27.3 (agreement weighting, DiD): ledger Δ={dl:+.3f} "
              f"(n={len(lo1)}/{len(lm)}) vs naive Δ={dn:+.3f} "
              f"(n={len(no1)}/{len(nm)}), DiD CI [{lo:+.3f},{hi:+.3f}] -> "
              f"{'SUPPORTED' if lo > 0 else 'FALSIFIED'}")
    else:
        print(f"P27.3: k>=2 strata too thin (ledger n={len(lm)}, naive n={len(nm)}) "
              "— report as not evaluable at this n (anticipated in registration)")

    # P27.4 coupling: answer families ⊆ ledger families; empty ledger -> bare answer
    ok = tot = 0
    empty_ok = empty_tot = 0
    for d in raw:
        if d.get("protocol_violation") or len(d.get("output", "")) < 500:
            continue
        led = ledger_of(d["full_output"])
        af = rx.families(d["output"])
        lf = rx.families(led)
        if "NO QUALIFICATION ROWS" in led or not lf:
            empty_tot += 1
            empty_ok += int(not af)
        for f in af:
            tot += 1
            ok += int(f in lf)
        # note: family-level proxy for row correspondence, per registration
    if tot:
        rate = ok / tot
        print(f"P27.4 (coupling): {ok}/{tot} answer-qualification families have a "
              f"same-family ledger entry ({rate:.2f}; bar 0.80); empty-ledger runs "
              f"bare: {empty_ok}/{empty_tot} -> "
              f"{'SUPPORTED' if rate >= 0.80 and empty_ok == empty_tot else 'FALSIFIED'}")
    else:
        print(f"P27.4: no answer qualifications to check; empty-ledger runs bare: "
              f"{empty_ok}/{empty_tot}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "gate"
    {"gate": stage_gate, "l2": stage_l2, "l1": stage_l1,
     "measure": stage_measure}[stage]()
