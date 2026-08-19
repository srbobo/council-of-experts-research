"""Tension-fate audit — what happens to the tensions the lead itself names?

Registered scope: RUNBOOK_PAPER_HARDENING.md "TENSION-FATE AUDIT".
DESCRIPTIVE AND POST-HOC. Licenses no claim; produces the headroom number
for a prospective lead-to-seat re-consultation cell.

Fates:
  RESOLVED      the synthesis takes a position on the tension — decides the
                trade-off, adjusts a number, or sequences the plan because
                of it
  ACKNOWLEDGED  mentioned or restated in the synthesis, but not resolved
  DROPPED       never addressed after the Tensions list

Extraction of tensions is FORMAT parsing (the prompt mandates a
"## Tensions" section of bullets), not semantic classification. The fate
label is semantic and comes from two judges; unparseable replies are
quarantined (finding #2); headline numbers use both-judges-agree labels.

Run:  .venv/bin/python train/run_audit_tension_fate.py sample
      .venv/bin/python train/run_audit_tension_fate.py judge
      .venv/bin/python train/run_audit_tension_fate.py measure
"""
from __future__ import annotations

import glob
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                          # noqa: E402

OUT = ROOT / "bench" / "analysis" / "tension_fate"
JUDGES = ["gpt-oss:20b", "qwen3-vl:30b-a3b-instruct"]
N_RUNS = 50
FATES = ("RESOLVED", "ACKNOWLEDGED", "DROPPED")

JUDGE_PROMPT = """\
You are auditing an analyst's report. The report begins by listing
TENSIONS the analyst noticed between specialist inputs, then gives the
final SYNTHESIS.

You will be shown ONE tension and the full synthesis. Classify what the
synthesis does with that tension:

RESOLVED     - the synthesis takes a position on it: chooses a side of the
trade-off, changes or conditions a number or recommendation because of it,
or sequences the plan specifically to deal with it
ACKNOWLEDGED - the synthesis mentions or restates it but does not resolve
it (saying it matters, or that both sides must be balanced, is not
resolving)
DROPPED      - the synthesis never addresses it

Reply with exactly one word on a single line: RESOLVED, ACKNOWLEDGED, or
DROPPED."""


def split_tensions(text: str) -> tuple[list[str], str]:
    """(tension bullets, synthesis text). Format parsing of the mandated
    '## Tensions' / '## Synthesis' structure; returns ([], '') if absent."""
    low = text
    if "## Tensions" not in low:
        return [], ""
    after = low.split("## Tensions", 1)[1]
    if "## Synthesis" in after:
        tens_block, synth = after.split("## Synthesis", 1)
    else:
        parts = after.split("\n## ", 1)
        if len(parts) < 2:
            return [], ""
        tens_block, synth = parts[0], parts[1]
    bullets = []
    for line in tens_block.splitlines():
        s = line.strip()
        if s.startswith(("-", "*")) and len(s) > 25:
            bullets.append(s.lstrip("-* ").strip())
    return bullets, synth.strip()


def stage_sample() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(0)
    files = sorted(glob.glob(str(ROOT / "bench/runs/2026*/case_*.json")))
    pool = []
    for f in files:
        try:
            d = json.loads(Path(f).read_text())["deliberation"]
        except Exception:
            continue
        out = (d.get("synthesis") or {}).get("output_text") or ""
        tens, synth = split_tensions(out)
        if tens and len(synth) > 500:
            pool.append({"file": str(Path(f).relative_to(ROOT)),
                         "tensions": tens, "synthesis": synth})
    rng.shuffle(pool)
    sample = pool[:N_RUNS]
    n_t = sum(len(x["tensions"]) for x in sample)
    (OUT / "sample.json").write_text(json.dumps(sample, ensure_ascii=False))
    print(f"eligible runs {len(pool)}; sampled {len(sample)}; "
          f"tensions to judge {n_t} (x{len(JUDGES)} judges = {n_t*len(JUDGES)} calls)")


def parse_fate(txt: str | None) -> str | None:
    if not txt or not txt.strip():
        return None
    import re
    t = re.sub(r"<think>.*?</think>", "", txt, flags=re.DOTALL).upper()
    hits = [f for f in FATES if f in t]
    return hits[0] if len(hits) == 1 else None


def stage_judge() -> None:
    sample = json.loads((OUT / "sample.json").read_text())
    cpath = OUT / "judgments.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    jobs = [(ri, ti) for ri, r in enumerate(sample)
            for ti in range(len(r["tensions"]))]
    print(f"tension-fate: {len(jobs)} tensions x {len(JUDGES)} judges", flush=True)
    t0 = time.time()
    for i, (ri, ti) in enumerate(jobs):
        r = sample[ri]
        body = (f"TENSION:\n{r['tensions'][ti]}\n\n"
                f"SYNTHESIS:\n{r['synthesis']}")
        for j in JUDGES:
            key = f"{j}|{ri}|{ti}"
            if cache.get(key) is not None:
                continue
            cache[key] = parse_fate(chat(j, JUDGE_PROMPT, body,
                                         temperature=0.0, max_tokens=2048))
        cpath.write_text(json.dumps(cache))
        if (i + 1) % 20 == 0:
            el = time.time() - t0
            print(f"  {i+1}/{len(jobs)} {el:.0f}s "
                  f"~{el/(i+1)*(len(jobs)-i-1):.0f}s left", flush=True)
    print("tension-fate judging complete")


def stage_measure() -> None:
    from collections import Counter
    from gst.stats import wilson_ci
    sample = json.loads((OUT / "sample.json").read_text())
    cache = json.loads((OUT / "judgments.json").read_text())
    per_judge = {j: Counter() for j in JUDGES}
    agreed = Counter()
    quar = disagree = n_all = 0
    pos_agreed: dict[int, Counter] = {}
    for ri, r in enumerate(sample):
        for ti in range(len(r["tensions"])):
            n_all += 1
            labs = [cache.get(f"{j}|{ri}|{ti}") for j in JUDGES]
            for j, l in zip(JUDGES, labs):
                if l:
                    per_judge[j][l] += 1
            if any(l is None for l in labs):
                quar += 1
                continue
            if labs[0] == labs[1]:
                agreed[labs[0]] += 1
                pos_agreed.setdefault(min(ti, 4), Counter())[labs[0]] += 1
            else:
                disagree += 1

    print("=" * 74)
    print("TENSION-FATE AUDIT — descriptive; headline = both-judges-agree only")
    print("=" * 74)
    print(f"  tensions judged {n_all}   quarantined {quar}   "
          f"judge disagreement {disagree}   agreed {sum(agreed.values())}")
    n_agree_total = sum(agreed.values()) + disagree
    if n_agree_total:
        print(f"  judge-judge agreement: "
              f"{sum(agreed.values())}/{n_agree_total} = "
              f"{sum(agreed.values())/n_agree_total:.3f}")
    print()
    print("  per-judge marginals (context for the agreement number):")
    for j in JUDGES:
        tot = sum(per_judge[j].values())
        if tot:
            print(f"    {j:<28} " + "  ".join(
                f"{f} {per_judge[j][f]}/{tot} ({per_judge[j][f]/tot:.2f})"
                for f in FATES))
    n_ag = sum(agreed.values())
    if not n_ag:
        print("\n  NO agreed labels — audit NOT EVALUABLE at this sample.")
        return
    print()
    print("  AGREED fates:")
    for f in FATES:
        lo, hi = wilson_ci(agreed[f], n_ag)
        print(f"    {f:<13} {agreed[f]:>4}/{n_ag}  = {agreed[f]/n_ag:.3f} "
              f"[{lo:.3f},{hi:.3f}]")
    head = n_ag - agreed["RESOLVED"]
    lo, hi = wilson_ci(head, n_ag)
    print()
    print(f"  HEADROOM (not resolved) = {head}/{n_ag} = {head/n_ag:.3f} "
          f"[{lo:.3f},{hi:.3f}]")
    print("  Scaffold caveat (registered): ACKNOWLEDGED is partially "
          "compliance with the\n  synthesis prompt's own 'Acknowledge the "
          "tensions' order; RESOLVED is the one\n  fate the scaffold does "
          "not dictate.")
    print()
    print("  by tension position in the list (agreed labels):")
    for p in sorted(pos_agreed):
        c = pos_agreed[p]
        tot = sum(c.values())
        print(f"    #{p+1:<3} n={tot:<4} " + "  ".join(
            f"{f[0]}={c[f]/tot:.2f}" for f in FATES))
    (OUT / "measured.json").write_text(json.dumps(
        {"agreed": dict(agreed), "quarantined": quar,
         "disagree": disagree, "n": n_all}))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "sample"
    {"sample": stage_sample, "judge": stage_judge,
     "measure": stage_measure}[stage]()
