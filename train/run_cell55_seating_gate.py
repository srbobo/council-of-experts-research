"""Cell 55 — seating-gate predictive validity.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 55 PRE-REGISTRATION"
(commit 33d9277, before any run).

Gate stage first (frozen C42 degeneracy rule on two screen items OUTSIDE
the pipeline case set, plus a descriptive format smoke); verdicts are
committed before any pipeline run. Pipeline stage seats every candidate
on the six Cell 44 cases. P55.1: strict rank separation of pipeline
defect rates by gate verdict.

Run:  .venv/bin/python train/run_cell55_seating_gate.py gate
      .venv/bin/python train/run_cell55_seating_gate.py pipeline
      .venv/bin/python train/run_cell55_seating_gate.py measure
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
from train.run_cell30_descaffold import SEATS                  # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell55"
RUNS = ROOT / "bench" / "runs" / "cell55_seating.jsonl"

# (label, ollama tag, seat role) — frozen at registration; no additions.
CANDIDATES = [
    ("qwen2.5",    "qwen2.5:7b-instruct",                                  "healthcare"),
    ("llama3",     "llama3:8b-instruct-q4_K_M",                            "healthcare"),
    ("mistral",    "mistral:7b-instruct-v0.3-q4_K_M",                      "healthcare"),
    ("deepseek",   "deepseek-r1:7b",                                       "healthcare"),
    ("phi4",       "phi4:14b",                                             "healthcare"),
    ("meditron3",  "huggingface.co/mradermacher/Meditron3-Qwen2.5-7B-GGUF:Q4_K_M", "healthcare"),
    ("med42",      "huggingface.co/mradermacher/Llama3-Med42-8B-GGUF:Q4_K_M",      "healthcare"),
    ("openbiollm", "hf.co/mradermacher/OpenBioLLM-Llama3-8B-GGUF:Q4_K_M",  "healthcare"),
    ("biomistral", "hf.co/MaziyarPanahi/BioMistral-7B-GGUF:Q4_K_M",        "healthcare"),
    ("saul",       "huggingface.co/MaziyarPanahi/Saul-Instruct-v1-GGUF:Q4_K_M",    "legal"),
]

# Screen items: DISJOINT from the pipeline case set (cross-item transfer).
SCREEN_ITEMS = ("case_8_trigger_light_hand_hygiene",
                "case_7_trigger_light_baseline")
SCREEN_REPS = 6
DEGEN_CHARS = 800
SCREEN_PROMPT = ("You are an analyst. Give a substantive written analysis "
                 "of the situation below for a decision-maker. Be specific "
                 "and concrete.")

FORMAT_REPS = 4
FORMAT_SYS = ("Answer the question in a short paragraph, then end your "
              "reply with a final line of exactly: VERDICT: YES or "
              "VERDICT: NO")
FORMAT_Q = ("A vendor contract auto-renews unless cancelled 60 days before "
            "term end. Today is 45 days before term end. Can the customer "
            "still avoid renewal under the clause alone?")

# Pipeline: the six Cell 44 cases, Cell 52 arm-A seat protocol.
PIPE_CASES = ("case_4_glp1_employer_coverage",
              "case_2_cross_border_digital_therapeutic",
              "case_5_nonprofit_hospital_pe_conversion",
              "case_l3_l3b", "case_1_clinical_decision_support",
              "case_l2_l2b")
PIPE_REPS = 3
ROSTER = ("Two other specialists — a {a} analyst and a {b} analyst — are "
          "being consulted separately on the same question.")

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def vis(t: str | None) -> str:
    """Visible contribution text: thinking blocks do not count as content."""
    return _THINK.sub("", t or "").strip()


def _append(row: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with RUNS.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _done() -> set[str]:
    if not RUNS.exists():
        return set()
    return {r["run_id"] for r in map(json.loads,
                                     RUNS.read_text().splitlines())}


def stage_gate() -> None:
    from examples.test_cases import get_case
    done = _done()
    for label, tag, _ in CANDIDATES:
        t = chat(tag, "Reply with the single word OK.", "ping",
                 temperature=0.0, max_tokens=2048)
        print(f"preflight {label}: {'ok' if t and t.strip() else 'EMPTY'}",
              flush=True)
    t0 = time.time()
    for label, tag, _ in CANDIDATES:
        for case in SCREEN_ITEMS:
            for rep in range(SCREEN_REPS):
                rid = f"{label}__screen__{case}__r{rep}"
                if rid in done:
                    continue
                t = chat(tag, SCREEN_PROMPT, get_case(case).prompt,
                         temperature=0.7, max_tokens=4096)
                _append({"run_id": rid, "label": label, "stage": "screen",
                         "case": case, "rep": rep, "chars": len(vis(t))})
        for rep in range(FORMAT_REPS):
            rid = f"{label}__format__r{rep}"
            if rid in done:
                continue
            t = chat(tag, FORMAT_SYS, FORMAT_Q,
                     temperature=0.7, max_tokens=2048)
            lines = [l.strip() for l in vis(t).splitlines() if l.strip()]
            ok = bool(lines) and lines[-1].upper().startswith("VERDICT:")
            _append({"run_id": rid, "label": label, "stage": "format",
                     "rep": rep, "ok": ok, "chars": len(vis(t))})
        print(f"  gated {label} ({time.time()-t0:.0f}s)", flush=True)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()]
    verdicts = {}
    for label, _, _ in CANDIDATES:
        sc = [r["chars"] for r in rows
              if r["label"] == label and r["stage"] == "screen"]
        fm = [r["ok"] for r in rows
              if r["label"] == label and r["stage"] == "format"]
        verdicts[label] = {
            "screen_runs": len(sc), "screen_min": min(sc), "screen_max": max(sc),
            "screen_mean": sum(sc) // len(sc),
            "gate_pass": all(c >= DEGEN_CHARS for c in sc),
            "format_ok": sum(fm), "format_n": len(fm)}
        v = verdicts[label]
        print(f"{label:<12} screen min/mean/max {v['screen_min']}/"
              f"{v['screen_mean']}/{v['screen_max']}  gate "
              f"{'PASS' if v['gate_pass'] else 'FAIL'}  format "
              f"{v['format_ok']}/{v['format_n']}")
    (OUT / "gate_verdicts.json").write_text(json.dumps(verdicts, indent=1))
    print("gate verdicts written — COMMIT before running the pipeline stage")


def stage_pipeline() -> None:
    from examples.test_cases import get_case
    if not (OUT / "gate_verdicts.json").exists():
        raise SystemExit("gate verdicts missing — gate stage first")
    done = _done()
    roles = ("healthcare", "legal", "finance")
    t0 = time.time()
    for label, tag, role in CANDIDATES:
        a, b = tuple(r for r in roles if r != role)
        for case in PIPE_CASES:
            for rep in range(PIPE_REPS):
                rid = f"{label}__pipe__{case}__r{rep}"
                if rid in done:
                    continue
                user = (get_case(case).prompt + "\n\n"
                        + ROSTER.format(a=a, b=b))
                txt = None
                for _ in range(3):
                    txt = chat(tag, SEATS[role], user,
                               temperature=0.7, max_tokens=4096)
                    if txt and txt.strip():
                        break
                v = vis(txt)
                _append({"run_id": rid, "label": label, "stage": "pipe",
                         "case": case, "rep": rep, "chars": len(v),
                         "empty": not v,
                         "defect": (not v) or len(v) < DEGEN_CHARS})
        print(f"  piped {label} ({time.time()-t0:.0f}s)", flush=True)
    print("cell55 pipeline complete")


def stage_measure() -> None:
    import random
    rng = random.Random(55)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines()]
    verd = json.loads((OUT / "gate_verdicts.json").read_text())
    pipe = [r for r in rows if r["stage"] == "pipe"]
    print("=" * 78)
    print("CELL 55 RAW TABLE (mandatory, before any verdict)")
    print(f"{'candidate':<12}{'gate':>6}{'screen mean':>12}{'format':>8}"
          f"{'pipe defects':>14}{'pipe mean chars':>16}")
    rates = {}
    for label, _, _ in CANDIDATES:
        v = verd[label]
        p = [r for r in pipe if r["label"] == label]
        d = sum(1 for r in p if r["defect"])
        rates[label] = d / max(len(p), 1)
        print(f"{label:<12}{'PASS' if v['gate_pass'] else 'FAIL':>6}"
              f"{v['screen_mean']:>12}{v['format_ok']}/{v['format_n']:>4}"
              f"{d}/{len(p):>10}"
              f"{sum(r['chars'] for r in p)//max(len(p),1):>16}")
    fails = [l for l, _, _ in CANDIDATES if not verd[l]["gate_pass"]]
    passes = [l for l, _, _ in CANDIDATES if verd[l]["gate_pass"]]
    print(f"\ngate-FAIL candidates: {fails or 'none'}")
    if not fails:
        print("P55.1: NOT EVALUABLE — no candidate failed the gate; the "
              "pool contains no test of the fail side")
        return
    worst_pass = max(rates[l] for l in passes)
    best_fail = min(rates[l] for l in fails)
    sep = best_fail > worst_pass
    print(f"P55.1 RANK SEPARATION: min fail-rate {best_fail:.3f} vs max "
          f"pass-rate {worst_pass:.3f} -> "
          + ("SUPPORTED — the gate's verdict predicts pipeline defects"
         if sep else "FALSIFIED — a gate-pass candidate defects at or "
                     "above a gate-fail candidate"))
    # P55.2 pooled contrast, bootstrap over cases
    by_case = {}
    for r in pipe:
        g = "fail" if r["label"] in fails else "pass"
        by_case.setdefault(r["case"], {"fail": [], "pass": []})[g].append(
            r["defect"])
    cases = sorted(by_case)
    ds = []
    for _ in range(5000):
        s = [cases[rng.randrange(len(cases))] for _ in cases]
        vf = [x for c in s for x in by_case[c]["fail"]]
        vp = [x for c in s for x in by_case[c]["pass"]]
        if vf and vp:
            ds.append(sum(vf)/len(vf) - sum(vp)/len(vp))
    ds.sort()
    vf = [x for c in cases for x in by_case[c]["fail"]]
    vp = [x for c in cases for x in by_case[c]["pass"]]
    est = sum(vf)/len(vf) - sum(vp)/len(vp)
    print(f"P55.2 pooled defect contrast (fail - pass): {est:+.3f} "
          f"[{ds[int(.025*len(ds))]:+.3f}, {ds[int(.975*len(ds))]:+.3f}]")


if __name__ == "__main__":
    {"gate": stage_gate, "pipeline": stage_pipeline,
     "measure": stage_measure}[sys.argv[1]]()
