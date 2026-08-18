"""Cell 43 — the preference-lift decomposition.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 43 PRE-REGISTRATION",
committed before any run or judgment.

Does an LLM preference judge show a MoA-style lift on this pipeline, and
what is the lift made of? The judge is the OBJECT of study, not an
instrument: it validates nothing and nothing validates it.

  C1  cell41 control (2-layer MoA)  vs  A-direct (same writer, no seats)
  C2  cell41 form-X                 vs  cell41 control
  C3  cell41 form-Y                 vs  cell41 control

C2/C3 lean on Cell 41's verdict: those arms differ ONLY in a dictated
phrase with no behavioural residue, so any preference gap IS phrase/register
preference, causally. Every output in every pair is gpt-oss text, so
self-preference bias is symmetric by construction.

Run:  .venv/bin/python train/run_cell43_preference.py direct
      .venv/bin/python train/run_cell43_preference.py judge
      .venv/bin/python train/run_cell43_preference.py measure
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
from train.run_cell30_descaffold import WRITER_PROMPT          # noqa: E402
from train.run_probe_domain_signature import profile           # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell43"
DIRECT_RUNS = ROOT / "bench" / "runs" / "cell43_direct.jsonl"
C41_RUNS = ROOT / "bench" / "runs" / "cell41_phraseswap.jsonl"
C41_LABELS = ROOT / "bench" / "analysis" / "cell41" / "labels.json"
WRITER = "gpt-oss:20b"
PRIMARY_JUDGE = "gpt-oss:20b"
REPL_JUDGE = "qwen2.5:7b-instruct"
REPL_SUBSAMPLE = 40                      # frozen per-comparison, seeded
REPEATS = 7
COMPARISONS = ("C1", "C2", "C3")

# One factor vs the Cell 41 control arm: the contributions sentence is
# removed and nothing else changes.
DIRECT_PROMPT = ("You are the lead analyst. Write the final answer to the "
                 "decision-maker's question.")
assert WRITER_PROMPT.replace(
    "Several specialists have written the contributions below. ", "") \
    == DIRECT_PROMPT, "A-direct prompt must be WRITER_PROMPT minus one sentence"

# Generic better-answer wording; gate G-E-checked in preflight. Names no
# construct vocabulary and no evaluative phrases from the registry.
JUDGE_PROMPT = ("You are comparing two responses to the same question. "
                "Decide which response is the better answer for the "
                "decision-maker overall. Reply with exactly one line:\n"
                "WINNER: A\nor\nWINNER: B")

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def cases41() -> list[str]:
    return sorted({json.loads(l)["case"]
                   for l in C41_RUNS.read_text().splitlines() if l.strip()})


def load_outputs() -> dict[tuple[str, str, int], str]:
    """{(arm, case, repeat): output} across cell41 arms + direct."""
    out = {}
    for l in C41_RUNS.read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            out[(r["arm"], r["case"], r["repeat"])] = r["output"]
    if DIRECT_RUNS.exists():
        for l in DIRECT_RUNS.read_text().splitlines():
            if l.strip():
                r = json.loads(l)
                out[("direct", r["case"], r["repeat"])] = r["output"]
    return out


PAIR_ARMS = {"C1": ("control", "direct"),     # side-1 = the MoA side
             "C2": ("form-X", "control"),
             "C3": ("form-Y", "control")}


def preflight() -> None:
    from gst.registry import gate_GE, load_frozen
    reg = load_frozen(ROOT / "docs" / "DICTATION_REGISTRY.json")
    viol = gate_GE({"JUDGE_PROMPT": JUDGE_PROMPT,
                    "DIRECT_PROMPT": DIRECT_PROMPT}, reg, construct_only=True)
    if viol:
        print("GATE G-E FAILED:")
        for v in viol:
            print("  " + v)
        raise SystemExit(1)
    t = chat(WRITER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED — writer/judge model unreachable.")
    print("preflight: gate G-E PASS, backend responds")


def stage_direct() -> None:
    from examples.test_cases import get_case
    preflight()
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if DIRECT_RUNS.exists():
        for l in DIRECT_RUNS.read_text().splitlines():
            if l.strip():
                done.add(json.loads(l)["run_id"])
    todo = [(c, r) for c in cases41() for r in range(REPEATS)
            if f"{c}__direct__r{r}" not in done]
    print(f"cell43 direct: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0, fails = time.time(), 0
    with DIRECT_RUNS.open("a") as fh:
        for k, (case, rep) in enumerate(todo):
            txt = None
            for attempt in range(3):
                txt = chat(WRITER, DIRECT_PROMPT, get_case(case).prompt,
                           temperature=0.6, max_tokens=8192)
                if txt and txt.strip():
                    break
                time.sleep(5 * (attempt + 1))
            if not txt or not txt.strip():
                fails += 1
                print(f"  EMPTY {case}/r{rep} (consecutive {fails})", flush=True)
                if fails >= 5:
                    raise SystemExit("ABORTING — backend down; resumable.")
                continue
            fails = 0
            fh.write(json.dumps({"run_id": f"{case}__direct__r{rep}",
                                 "case": case, "repeat": rep, "output": txt},
                                ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 10 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print("cell43 direct complete")


def parse_winner(txt: str | None) -> str | None:
    """'A' | 'B' | None (quarantined; finding #2 — never default a blank)."""
    if not txt or not txt.strip():
        return None
    t = _THINK.sub("", txt).upper()
    m = re.findall(r"WINNER:\s*([AB])\b", t)
    if m:
        return m[-1]
    hits = [x for x in ("A", "B")
            if re.search(rf"\b{x}\b", t.strip().splitlines()[-1])]
    return hits[0] if len(hits) == 1 else None


def judge_pair(judge: str, q: str, ra: str, rb: str, cache: dict,
               key: str) -> str | None:
    # A cached None is a transient failure, not a verdict — retry it.
    # (First judging launch cached quarantines permanently; 11 of the first
    # 44 calls were Nones that would never have been re-attempted.)
    if cache.get(key) is not None:
        return cache[key]
    body = (f"Question:\n{q}\n\n--- Response A ---\n{ra}\n\n"
            f"--- Response B ---\n{rb}")
    # 4096: the longest pairs are ~18k chars and the reasoning judge can
    # exhaust a 1024 budget before emitting its one-line verdict.
    w = parse_winner(chat(judge, JUDGE_PROMPT, body,
                          temperature=0.0, max_tokens=4096))
    cache[key] = w
    return w


def stage_judge() -> None:
    import random
    from examples.test_cases import get_case
    preflight()
    outs = load_outputs()
    missing = [(c, r) for c in cases41() for r in range(REPEATS)
               if ("direct", c, r) not in outs]
    if missing:
        raise SystemExit(f"A-direct incomplete ({len(missing)} missing) — "
                         f"run the direct stage first.")
    cpath = OUT / "judgments.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    rng = random.Random(43)
    repl = {comp: set(rng.sample([(c, r) for c in cases41()
                                  for r in range(REPEATS)], REPL_SUBSAMPLE))
            for comp in COMPARISONS}
    (OUT / "repl_subsample.json").write_text(json.dumps(
        {k: sorted(map(list, v)) for k, v in repl.items()}))

    jobs = []
    for comp in COMPARISONS:
        a1, a2 = PAIR_ARMS[comp]
        for c in cases41():
            for r in range(REPEATS):
                jobs.append((PRIMARY_JUDGE, comp, c, r, a1, a2))
                if (c, r) in repl[comp]:
                    jobs.append((REPL_JUDGE, comp, c, r, a1, a2))
    print(f"cell43 judge: {len(jobs)} pairs x 2 orderings", flush=True)
    t0 = time.time()
    for i, (j, comp, c, r, a1, a2) in enumerate(jobs):
        q = get_case(c).prompt
        x, y = outs[(a1, c, r)], outs[(a2, c, r)]
        judge_pair(j, q, x, y, cache, f"{j}|{comp}|{c}|{r}|fwd")
        judge_pair(j, q, y, x, cache, f"{j}|{comp}|{c}|{r}|rev")
        cpath.write_text(json.dumps(cache))
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            print(f"  {i+1}/{len(jobs)} {el:.0f}s "
                  f"~{el/(i+1)*(len(jobs)-i-1):.0f}s left", flush=True)
    print("cell43 judging complete")


def _decide(cache: dict, judge: str, comp: str, c: str, r: int) -> str | None:
    """'S1' | 'S2' | 'TIE' | None. S1 = first arm of PAIR_ARMS[comp]."""
    f = cache.get(f"{judge}|{comp}|{c}|{r}|fwd")
    v = cache.get(f"{judge}|{comp}|{c}|{r}|rev")
    if f is None or v is None:
        return None
    w_f = "S1" if f == "A" else "S2"
    w_r = "S1" if v == "B" else "S2"
    return w_f if w_f == w_r else "TIE"


def _qual_counts() -> dict[tuple[str, str, int], int]:
    """Both-judges `modeled` sentence counts per Cell 41 run (validated)."""
    lab = json.loads(C41_LABELS.read_text())
    out = {}
    for rid, d in lab.items():
        case, arm, rep = rid.split("__")
        a, b = (d["judges"].get(j, {}) for j in
                ("gpt-oss:20b", "qwen2.5:7b-instruct"))
        n = sum(1 for i in range(len(d["sentences"]))
                if a.get(str(i), {}).get("modeled") and
                   b.get(str(i), {}).get("modeled"))
        out[(arm, case, int(rep[1:]))] = n
    return out


def stage_measure() -> None:
    import random
    rng = random.Random(0)
    outs = load_outputs()
    cache = json.loads((OUT / "judgments.json").read_text())
    feats = {k: profile(v) for k, v in outs.items()}
    quals = _qual_counts()
    cs = cases41()

    def rows(judge, comp):
        a1, a2 = PAIR_ARMS[comp]
        out = []
        for c in cs:
            for r in range(REPEATS):
                d = _decide(cache, judge, comp, c, r)
                out.append({"case": c, "rep": r, "verdict": d,
                            "d_chars": feats[(a1, c, r)]["chars"]
                                       - feats[(a2, c, r)]["chars"],
                            "k1": (a1, c, r), "k2": (a2, c, r)})
        return out

    def share_ci(v):
        """Cluster bootstrap over cases on P(S1 wins | decisive)."""
        by = {}
        for x in v:
            if x["verdict"] in ("S1", "S2"):
                by.setdefault(x["case"], []).append(x["verdict"] == "S1")
        pool = sorted(by)
        if not pool:
            return float("nan"), (float("nan"),) * 2, 0
        ds = []
        for _ in range(5000):
            s = [pool[rng.randrange(len(pool))] for _ in pool]
            w = [b for c in s for b in by[c]]
            if w:
                ds.append(sum(w) / len(w))
        ds.sort()
        dec = [x for x in v if x["verdict"] in ("S1", "S2")]
        pt = sum(1 for x in dec if x["verdict"] == "S1") / len(dec)
        return pt, (ds[int(.025 * len(ds))], ds[int(.975 * len(ds))]), len(dec)

    print("=" * 78)
    print("CELL 43 — preference-lift decomposition (primary judge:",
          PRIMARY_JUDGE + ")")
    print("=" * 78)
    print("P43.4 RAW TABLE (mandatory, printed before any verdict)")
    labels = {"C1": "MoA vs direct", "C2": "form-X vs control",
              "C3": "form-Y vs control"}
    for judge in (PRIMARY_JUDGE, REPL_JUDGE):
        print(f"  [{judge}]")
        for comp in COMPARISONS:
            v = rows(judge, comp)
            n_j = sum(1 for x in v if x["verdict"] is not None)
            dec = sum(1 for x in v if x["verdict"] in ("S1", "S2"))
            tie = sum(1 for x in v if x["verdict"] == "TIE")
            quar = sum(1 for x in v if x["verdict"] is None)
            if judge == REPL_JUDGE and n_j == 0:
                continue
            print(f"    {comp} {labels[comp]:<20} judged {n_j:>4}  "
                  f"decisive {dec:>4}  tie {tie:>4}  quarantined {quar:>4}")
    print("  mean chars: " + "  ".join(
        f"{a}={sum(feats[(a,c,r)]['chars'] for c in cs for r in range(REPEATS))//(len(cs)*REPEATS)}"
        for a in ("control", "direct", "form-X", "form-Y")))

    print()
    print("P43.1 THE LIFT — C1, MoA side share of decisive pairs")
    pt, ci, n = share_ci(rows(PRIMARY_JUDGE, "C1"))
    hit = ci[0] > 0.5 or ci[1] < 0.5
    print(f"  share {pt:.3f}  CI [{ci[0]:.3f},{ci[1]:.3f}]  n={n}  -> "
          + ("LIFT toward MoA" if ci[0] > 0.5 else
             "preference for DIRECT" if ci[1] < 0.5 else
             "no detectable shift (MDD ~0.64 registered; null licenses only "
             "'no MoA-sized shift')"))

    print()
    print("P43.2 COMPLIANCE-PREFERENCE — C2/C3 (any gap IS phrase preference,"
          " per Cell 41)")
    dirs = {}
    for comp in ("C2", "C3"):
        pt, ci, n = share_ci(rows(PRIMARY_JUDGE, comp))
        d = "S1" if ci[0] > 0.5 else "S2" if ci[1] < 0.5 else "null"
        dirs[comp] = d
        print(f"  {comp} {labels[comp]:<20} share {pt:.3f}  "
              f"CI [{ci[0]:.3f},{ci[1]:.3f}]  n={n}  [{d}]")
    if dirs["C2"] == dirs["C3"] != "null":
        side = "the PHRASE arm" if dirs["C2"] == "S1" else "the CONTROL arm"
        print(f"  -> replicated across both forms: the judge prefers {side}")
    elif "null" in dirs.values() and set(dirs.values()) != {"null"}:
        print("  -> one form only: form-specific, NOT register preference")
    elif set(dirs.values()) == {"null"}:
        print("  -> no compliance-preference detected in either form")
    else:
        print("  -> forms disagree in direction: no coherent preference")

    print()
    print("P43.3 DECOMPOSITION — what the winner has more of (decisive pairs)")
    for comp in COMPARISONS:
        v = [x for x in rows(PRIMARY_JUDGE, comp)
             if x["verdict"] in ("S1", "S2")]
        if not v:
            continue
        n_len = sum(1 for x in v if (x["verdict"] == "S1") == (x["d_chars"] > 0))
        matched = [x for x in v if abs(x["d_chars"]) <
                   0.15 * max(feats[x["k1"]]["chars"], feats[x["k2"]]["chars"])]
        m_s1 = (sum(1 for x in matched if x["verdict"] == "S1") / len(matched)
                if matched else float("nan"))
        line = (f"  {comp}: winner-is-longer {n_len}/{len(v)} = "
                f"{n_len/len(v):.3f}   length-matched pairs {len(matched)}, "
                f"S1 share {m_s1:.3f}")
        if comp in ("C2", "C3"):
            a_q = sum(1 for x in v
                      if (x["verdict"] == "S1")
                      == (quals.get(x["k1"], 0) > quals.get(x["k2"], 0))
                      and quals.get(x["k1"], 0) != quals.get(x["k2"], 0))
            n_q = sum(1 for x in v
                      if quals.get(x["k1"], 0) != quals.get(x["k2"], 0))
            line += (f"   winner-has-more-qualification {a_q}/{n_q}"
                     f" = {a_q/max(n_q,1):.3f}")
        else:
            a_f = sum(1 for x in v
                      if (x["verdict"] == "S1")
                      == (feats[x["k1"]]["fw_healthcare"]
                          > feats[x["k2"]]["fw_healthcare"]))
            line += f"   winner-has-more-framework/k {a_f}/{len(v)} = {a_f/len(v):.3f}"
        print(line)

    (OUT / "measured.json").write_text(json.dumps(
        {comp: [{k: v for k, v in x.items() if k not in ("k1", "k2")}
                for x in rows(PRIMARY_JUDGE, comp)] for comp in COMPARISONS},
        indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "direct"
    {"direct": stage_direct, "judge": stage_judge,
     "measure": stage_measure}[stage]()
