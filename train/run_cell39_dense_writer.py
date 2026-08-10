"""Cell 39 — is the error filtering a COUNCIL property or a WRITER property?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 39 PRE-REGISTRATION".
One factor changes from Cell 35: the writing model. Everything else —
the nine planted errors, the upstream, the prompt, temperature, repeats,
and the scoring protocol — is imported from the Cell 35 harness so it
cannot drift.

Run:  .venv/bin/python train/run_cell39_dense_writer.py runs
      ... judge / measure
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                                # noqa: E402
from train.run_cell30_descaffold import WRITER_PROMPT, norm          # noqa: E402
from train.run_cell35_injection import (INJECTIONS, JUDGES, PROP_PROMPT,  # noqa: E402
                                        REPEATS, ROLES, _parse)

OUT = ROOT / "bench" / "analysis" / "cell39"
RUNS = ROOT / "bench" / "runs" / "cell39_dense.jsonl"
C30 = ROOT / "bench" / "analysis" / "cell30"
C35_RUNS = ROOT / "bench" / "runs" / "cell35_injection.jsonl"
C35_JUDGED = ROOT / "bench" / "analysis" / "cell35" / "judged.json"
WRITER = "phi4:14b"          # dense — the only change from Cell 35


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
    print(f"cell39 ({WRITER}): {len(todo)} runs to go", flush=True)
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
            txt = chat(WRITER, WRITER_PROMPT,
                       f"{body}\n\nQuestion:\n{get_case(case).prompt}",
                       temperature=0.6, max_tokens=8192)
            if not txt or not txt.strip():
                print(f"  EMPTY {case}/{arm}/r{rep} — failed, not scored", flush=True)
                continue
            fh.write(json.dumps({
                "run_id": f"{case}__{arm}__r{rep}", "case": case, "arm": arm,
                "repeat": rep, "writer": WRITER, "seat_order": order,
                "injected_index": order.index(inj["seat"]) + 1,
                "upstream": upstream, "output": txt}, ensure_ascii=False) + "\n")
            fh.flush()
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)} {case[:32]}/{arm}/r{rep} {el:.0f}s "
                  f"~{el/(i+1)*(len(todo)-i-1):.0f}s left", flush=True)
    print("cell39 runs complete")


def stage_judge() -> None:
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    path = OUT / "judged.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    todo = [r for r in rows if r["run_id"] not in cache]
    print(f"judge: {len(todo)} runs", flush=True)
    t0 = time.time()
    for i, r in enumerate(todo):
        inj = INJECTIONS[r["case"]]
        entry = {"prop": {}}
        for j in JUDGES:
            entry["prop"][j] = _parse(chat(j, None, PROP_PROMPT.format(
                claim=inj["claim"], answer=r["output"][:12000]),
                temperature=0, max_tokens=1024), ["asserts"])
        cache[r["run_id"]] = entry
        if (i + 1) % 6 == 0:
            path.write_text(json.dumps(cache, ensure_ascii=False))
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)} {el:.0f}s "
                  f"~{el/(i+1)*(len(todo)-i-1):.0f}s left", flush=True)
    path.write_text(json.dumps(cache, ensure_ascii=False))
    print("judge complete")


def _rate(rows, cache):
    """(propagated, usable) under the both-judges-agree rule."""
    k = n = 0
    for r in rows:
        e = cache.get(r["run_id"], {}).get("prop", {})
        vs = [e.get(j) for j in JUDGES]
        if any(v is None for v in vs):
            continue
        n += 1
        k += int(all(v["asserts"] for v in vs))
    return k, n


def stage_measure() -> None:
    from gst.stats import wilson_ci
    dense = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    dcache = json.loads((OUT / "judged.json").read_text())
    moe = [json.loads(x) for x in C35_RUNS.read_text().splitlines() if x.strip()]
    mcache = json.loads(C35_JUDGED.read_text())

    print("=" * 74)
    print("P39.1 PROPAGATION — dense writer vs the MoE writer of Cell 35")
    print("=" * 74)
    out = {}
    for name, rows, cache in (("MoE  (gpt-oss:20b)", moe, mcache),
                              ("dense (phi4:14b)", dense, dcache)):
        inj = [r for r in rows if r["arm"] == "inject"]
        ctl = [r for r in rows if r["arm"] == "control"]
        ki, ni = _rate(inj, cache)
        kc, nc = _rate(ctl, cache)
        ci_i = wilson_ci(ki, ni) if ni else (float("nan"),) * 2
        ci_c = wilson_ci(kc, nc) if nc else (float("nan"),) * 2
        em = sum(1 for r in inj
                 if norm(INJECTIONS[r["case"]]["probe"]) in norm(r["output"]))
        out[name] = (ci_i, ci_c)
        print(f"  {name:<20} inject {ki}/{ni} = {ki/max(ni,1):.3f} "
              f"[{ci_i[0]:.3f},{ci_i[1]:.3f}]   control {kc}/{nc} "
              f"[{ci_c[0]:.3f},{ci_c[1]:.3f}]   exact-match {em}/{len(inj)}")
    m_ci, _ = out["MoE  (gpt-oss:20b)"]
    d_ci, d_ctl = out["dense (phi4:14b)"]
    print()
    print(f"P39.1: {'SUPPORTED — dense propagates where the MoE did not' if d_ci[0] > m_ci[1] else 'FALSIFIED — both architectures filter'}"
          f"   (dense lower {d_ci[0]:.3f} vs MoE upper {m_ci[1]:.3f})")
    print(f"P39.2 control: dense false-positive CI [{d_ctl[0]:.3f},{d_ctl[1]:.3f}] "
          f"-> {'ok' if d_ctl[0] <= 0.001 else 'ELEVATED — propagation numbers suspect'}")

    print()
    print("=" * 74)
    print("P39.3 silence check (mandatory reporting, no bar)")
    import re
    CORRECT = {"case_3_capitated_risk_contract": r"29\.5|\$29",
               "case_5_nonprofit_hospital_pe_conversion": r"\$20\s?M|equity.{0,20}20",
               "case_6_trigger_heavy_biotech_ma": r"120\s?[Bb]illion|\$120",
               "case_8_trigger_light_hand_hygiene": r"\b13\b",
               "case_10_trigger_light_depreciation": r"10,000|10000|\$10\s?k"}
    for name, rows in (("MoE  ", moe), ("dense", dense)):
        inj = [r for r in rows if r["arm"] == "inject"]
        print(f"  {name} mean output {sum(len(r['output']) for r in inj)/max(len(inj),1):.0f} chars")
        c = w = neither = 0
        for r in inj:
            if r["case"] not in CORRECT:
                continue
            has_c = bool(re.search(CORRECT[r["case"]], r["output"], re.I))
            has_w = norm(INJECTIONS[r["case"]]["probe"][:18]) in norm(r["output"])
            c += has_c and not has_w
            w += has_w
            neither += not has_c and not has_w
        print(f"        arithmetic items: correct={c}  corrupted={w}  neither={neither}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "runs"
    {"runs": stage_runs, "judge": stage_judge, "measure": stage_measure}[stage]()
