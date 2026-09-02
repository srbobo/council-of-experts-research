"""Cell 61 — the bundle A/B: old architecture vs the assembled harness.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 61 PRE-REGISTRATION"
(commit f4ed692, before any run).

Run:  .venv/bin/python train/run_cell61_bundle_ab.py gen
      .venv/bin/python train/run_cell61_bundle_ab.py judge
      .venv/bin/python train/run_cell61_bundle_ab.py judge_prose
      .venv/bin/python train/run_cell61_bundle_ab.py measure
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell43_preference import judge_pair              # noqa: E402
from train.run_cell44_reconsult import S1_PROMPT, S2_PROMPT     # noqa: E402
from train.run_cell30_descaffold import SEATS                   # noqa: E402
from train.run_cell57_planner import PLANNER_PROMPT as IDENTIFY  # noqa: E402
from train.run_cell59_subquestions import parse_plan            # noqa: E402
from train.run_integration_demo import (FOLLOWUP, ROSTER,       # noqa: E402
                                        SUBQ_PROMPT, extract_caveats,
                                        gen)
from gst.gates import FABRICATION_BLOCKLIST, blocklist_gate     # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell61"
ARTS = OUT / "harness_artifacts.jsonl"
C41_RUNS = ROOT / "bench" / "runs" / "cell41_phraseswap.jsonl"
ROLES = ("healthcare", "legal", "finance")
REPS = 3
JUDGE_PRIMARY = "gpt-oss:20b"
JUDGE_REPL = "qwen3-vl:30b-a3b-instruct"


def old_corpus():
    rows = [json.loads(l) for l in C41_RUNS.read_text().splitlines()
            if l.strip()]
    return {(r["case"], r["repeat"]): r["output"]
            for r in rows if r["arm"] == "control"}


def harness_artifact(case: str) -> dict:
    from examples.test_cases import get_case
    q = get_case(case).prompt
    ids = gen(IDENTIFY, f"Question:\n{q}", toks=4096)
    quants = [l.strip() for l in ids.splitlines() if l.strip()][:6]
    plan = None
    for _ in range(3):
        plan = parse_plan(gen("Follow the output format exactly.",
                              SUBQ_PROMPT.format(
                                  quantities="\n".join(quants))
                              + f"\n\nQuestion:\n{q}", toks=4096))
        if plan:
            break
    if not plan:
        raise SystemExit("plan parse failed 3x")
    contribs, caveats = {}, []
    for role in ROLES:
        a, b = tuple(r for r in ROLES if r != role)
        ans = gen(SEATS[role],
                  f"Case:\n{q}\n\nYour sub-question:\n{plan[role]}\n\n"
                  + ROSTER.format(a=a, b=b))
        contribs[role] = ans
        caveats += extract_caveats(ans)
    pile = "\n\n".join(
        f"--- {r.upper()} SPECIALIST CONTRIBUTION ---\n{contribs[r]}"
        for r in ROLES)
    s1 = gen(S1_PROMPT, f"{pile}\n\nQuestion:\n{q}", temp=0.6, toks=4096)
    route, tension = None, None
    for line in (l.strip() for l in s1.splitlines() if l.strip()):
        for r in ROLES:
            if r in line.lower():
                route, tension = r, line
                break
        if route:
            break
    reply_block = ""
    if route:
        reply = gen(SEATS[route],
                    f"Case:\n{q}\n\nYour earlier contribution:\n"
                    f"{contribs[route]}\n\n"
                    + FOLLOWUP.format(tension=tension), toks=4096)
        if not blocklist_gate(reply, FABRICATION_BLOCKLIST):
            reply_block = (f"--- FOLLOW-UP CLARIFICATION (from the "
                           f"{route} specialist) ---\n{reply}\n\n")
    prose = gen(S2_PROMPT,
                f"{pile}\n\n--- YOUR TENSION LIST ---\n{s1}\n\n"
                f"{reply_block}Question:\n{q}", temp=0.6, toks=12288)
    full = prose
    if caveats:
        full += ("\n\n---\nASSUMPTIONS & CAVEATS (as stated by the "
                 "specialist contributors)\n"
                 + "\n".join(f"- {c}" for c in caveats))
    return {"prose": prose, "full": full, "route": route,
            "n_caveats": len(caveats)}


def stage_gen():
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if ARTS.exists():
        done = {(r["case"], r["rep"]) for r in
                map(json.loads, ARTS.read_text().splitlines())}
    cases = sorted({c for c, _ in old_corpus()})
    todo = [(c, r) for c in cases for r in range(REPS)
            if (c, r) not in done]
    print(f"cell61 gen: {len(todo)} harness pipelines to go", flush=True)
    t0 = time.time()
    with ARTS.open("a") as fh:
        for k, (case, rep) in enumerate(todo):
            art = harness_artifact(case)
            fh.write(json.dumps({"case": case, "rep": rep, **art},
                                ensure_ascii=False) + "\n")
            fh.flush()
            el = time.time() - t0
            print(f"  {k+1}/{len(todo)} {case[:30]} r{rep} "
                  f"({art['n_caveats']} caveats, route={art['route']}) "
                  f"{el:.0f}s ~{el/(k+1)*(len(todo)-k-1)/60:.0f}m left",
                  flush=True)
    print("cell61 gen complete")


def pairs():
    old = old_corpus()
    harts = [json.loads(l) for l in ARTS.read_text().splitlines()
             if l.strip()]
    out = []
    for h in harts:
        for old_rep in (h["rep"], h["rep"] + 3):
            key = (h["case"], old_rep)
            if key in old:
                out.append((h, old_rep, old[key]))
    return out


def _judge(field: str, cpath: Path, judges):
    from examples.test_cases import get_case
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    ps = pairs()
    jobs = [(j, i) for j in judges for i in range(len(ps))]
    print(f"cell61 judge[{field}]: {len(jobs)} pairs x 2 orderings",
          flush=True)
    t0 = time.time()
    for n, (j, i) in enumerate(jobs):
        h, old_rep, old_txt = ps[i]
        q = get_case(h["case"]).prompt
        key = f"{j}|{h['case']}|{h['rep']}|{old_rep}"
        judge_pair(j, q, h[field], old_txt, cache, key + "|fwd")
        judge_pair(j, q, old_txt, h[field], cache, key + "|rev")
        cpath.write_text(json.dumps(cache))
        if (n + 1) % 20 == 0:
            el = time.time() - t0
            print(f"  {n+1}/{len(jobs)} {el:.0f}s "
                  f"~{el/(n+1)*(len(jobs)-n-1)/60:.0f}m left", flush=True)
    print("judging complete")


def stage_judge():
    _judge("full", OUT / "judgments_full.json",
           [JUDGE_PRIMARY, JUDGE_REPL])


def stage_judge_prose():
    _judge("prose", OUT / "judgments_prose.json", [JUDGE_PRIMARY])


def _decide(cache, j, key):
    f, v = cache.get(f"{j}|{key}|fwd"), cache.get(f"{j}|{key}|rev")
    if f is None or v is None:
        return None
    wf = "H" if f == "A" else "O"
    wr = "H" if v == "B" else "O"
    return wf if wf == wr else "TIE"


def stage_measure():
    import random
    rng = random.Random(61)
    ps = pairs()
    full = json.loads((OUT / "judgments_full.json").read_text())
    print("=" * 72)
    print("CELL 61 RAW TABLE (mandatory, before any verdict)")
    for j, label in ((JUDGE_PRIMARY, "primary"), (JUDGE_REPL, "replication")):
        dec = {}
        for h, old_rep, _ in ps:
            key = f"{h['case']}|{h['rep']}|{old_rep}"
            d = _decide(full, j, key)
            dec.setdefault(h["case"], []).append(d)
        flat = [d for v in dec.values() for d in v]
        nH = sum(1 for d in flat if d == "H")
        nO = sum(1 for d in flat if d == "O")
        nT = sum(1 for d in flat if d == "TIE")
        print(f"  {label:<12} H {nH}  O {nO}  TIE {nT}  "
              f"undecided {sum(1 for d in flat if d is None)}")
        if nH + nO == 0:
            continue
        per = {c: (sum(1 for d in v if d == "H"),
                   sum(1 for d in v if d in ("H", "O")))
               for c, v in dec.items()}
        cs = [c for c in per if per[c][1] > 0]
        bs = []
        for _ in range(5000):
            s = [cs[rng.randrange(len(cs))] for _ in cs]
            num = sum(per[c][0] for c in s)
            den = sum(per[c][1] for c in s)
            if den:
                bs.append(num / den)
        bs.sort()
        share = nH / (nH + nO)
        lo, hi = bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]
        print(f"  {label} harness share of decisive: {share:.3f} "
              f"[{lo:.3f}, {hi:.3f}]  (n={nH+nO} decisive, "
              f"{len(cs)} case clusters)")
        if j == JUDGE_PRIMARY:
            if lo > 0.5:
                print("  P61.1: HARNESS PREFERRED — the bundle preserves "
                      "the lift")
            elif hi < 0.5:
                print("  P61.1: THE HARNESS BUNDLE COSTS PREFERENCE — "
                      "recorded at full prominence")
            else:
                print("  P61.1: spans 0.5 — graded vs realized decisive "
                      "count (registered)")
    # prose-only sensitivity
    pp = OUT / "judgments_prose.json"
    if pp.exists():
        prose = json.loads(pp.read_text())
        flat = []
        for h, old_rep, _ in ps:
            key = f"{h['case']}|{h['rep']}|{old_rep}"
            flat.append(_decide(prose, JUDGE_PRIMARY, key))
        nH = sum(1 for d in flat if d == "H")
        nO = sum(1 for d in flat if d == "O")
        print(f"\n  sensitivity (prose-only, primary): H {nH}  O {nO}  "
              f"TIE {sum(1 for d in flat if d == 'TIE')}  share "
              f"{nH/max(nH+nO,1):.3f} — divergence from the full-artifact "
              f"verdict is attributed to the appendix (registered "
              f"reading)")
    harts = [json.loads(l) for l in ARTS.read_text().splitlines()]
    old = old_corpus()
    hl = sum(len(h["full"]) for h in harts) / len(harts)
    ol = sum(len(v) for v in old.values()) / len(old)
    print(f"\n  descriptive: harness artifact mean {hl:.0f} chars "
          f"(incl. appendix) vs old {ol:.0f}; caveats/artifact "
          f"{sum(h['n_caveats'] for h in harts)/len(harts):.1f}; "
          f"dispatch fired {sum(1 for h in harts if h['route'])}/"
          f"{len(harts)}")


if __name__ == "__main__":
    {"gen": stage_gen, "judge": stage_judge,
     "judge_prose": stage_judge_prose,
     "measure": stage_measure}[sys.argv[1]]()
