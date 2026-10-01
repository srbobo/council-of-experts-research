"""Cell 65 — does the judge preference repeat with four more judges?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 65 PRE-REGISTRATION".

Cell 43 asked an AI judge which of two answers is better, on 378 stored
pairs (18 scenarios x 7 repeats x 3 comparisons), each pair in both orders.
Two judges have covered all pairs: gpt-oss:20b (the model that wrote every
answer) and qwen3-vl:30b (Cell 43-R). This cell adds four judges from other
model families on the same pairs with the same prompt and settings, and
scores every pair, counting a pair the judge splits by position as half.

No new answer is generated. The pairs, the judge prompt, the temperature
and the token limit are those of Cell 43.

Run:  .venv/bin/python train/run_cell65_judges.py smoke      (a made-up pair)
      .venv/bin/python train/run_cell65_judges.py judge [judge]
      .venv/bin/python train/run_cell65_judges.py measure
"""
from __future__ import annotations

import collections
import json
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                              # noqa: E402
from gst.smallcluster import kappa, sign_flip_p, t_interval         # noqa: E402
from train.run_cell43_preference import (COMPARISONS, JUDGE_PROMPT,  # noqa: E402
                                         PAIR_ARMS, REPEATS, cases41,
                                         load_outputs, parse_winner)

REGISTRATION = runlog.registration_for("65", ROOT)
AN = ROOT / "bench" / "analysis"
OUT = AN / "cell65"
CALLS = ROOT / "bench" / "runs" / "cell65_judgments.jsonl"
NEW_JUDGES = ("qwen2.5:7b-instruct", "phi4:14b", "llama3:8b-instruct-q4_K_M",
              "mistral:7b-instruct-v0.3-q4_K_M")
STORED = {"gpt-oss:20b": AN / "cell43" / "judgments.json",
          "qwen3-vl:30b-a3b-instruct": AN / "cell43R" / "judgments.json"}
LABEL = {"C1": "pipeline answer vs single answer", "C2": "'modeled at' answer vs plain",
         "C3": "'taken to be' answer vs plain"}
MAX_TOKENS = 4096
UNUSABLE_LIMIT = 0.20
FIRST_LIMIT = 0.95           # a judge that picks the first-listed answer this often does not count


def _body(q: str, ra: str, rb: str) -> str:
    return f"Question:\n{q}\n\n--- Response A ---\n{ra}\n\n--- Response B ---\n{rb}"


def _call(judge: str, key: str, q: str, ra: str, rb: str) -> dict:
    text, meta = runlog.chat_logged(judge, JUDGE_PROMPT, _body(q, ra, rb), temperature=0.0,
                                    max_tokens=MAX_TOKENS, seed=runlog.seed_for(key))
    return runlog.stamp({"key": key, "judge": judge, "winner": parse_winner(text)}, meta,
                        root=ROOT, script=Path(__file__), registration=REGISTRATION)


def stage_smoke() -> None:
    """A made-up pair, both orders, every added judge. Not a stored pair;
    nothing is written."""
    q = "A shop sells pens at $2 each. How much do 3 pens cost?"
    good, bad = "Three pens cost $6 (3 x $2).", "Three pens cost $9."
    for judge in NEW_JUDGES:
        f = _call(judge, f"SMOKE|{judge}|fwd", q, good, bad)
        r = _call(judge, f"SMOKE|{judge}|rev", q, bad, good)
        print(f"  {judge:<34} good listed first -> {f['winner']}; listed second -> {r['winner']}; "
              f"prompt_tokens={f['audit'].get('prompt_tokens')} wall={f['audit'].get('wall_s')}s", flush=True)


def stage_judge(only: str | None = None) -> None:
    from examples.test_cases import get_case
    outs = load_outputs()
    cs = cases41()
    done = {r["key"] for r in runlog.read_jsonl(CALLS)}
    for judge in ([only] if only else NEW_JUDGES):
        jobs = []
        for comp in COMPARISONS:
            a1, a2 = PAIR_ARMS[comp]
            for c in cs:
                for r in range(REPEATS):
                    for order in ("fwd", "rev"):
                        key = f"{judge}|{comp}|{c}|{r}|{order}"
                        if key not in done:
                            jobs.append((key, c, (a1, c, r), (a2, c, r), order))
        print(f"cell65 {judge}: {len(jobs)} judgments to go", flush=True)
        t0, errs = time.time(), 0
        for n, (key, c, k1, k2, order) in enumerate(jobs):
            x, y = outs[k1], outs[k2]
            row = _call(judge, key, get_case(c).prompt, *((x, y) if order == "fwd" else (y, x)))
            if row["audit"].get("error"):
                errs += 1
                print(f"  ERROR {key}: {row['audit']['error']} (consecutive {errs})", flush=True)
                if errs >= 5:
                    raise SystemExit("ABORTING — five consecutive call errors; resumable.")
                continue
            errs = 0
            runlog.append_jsonl(CALLS, row)
            if (n + 1) % 50 == 0:
                el = time.time() - t0
                print(f"  {n+1}/{len(jobs)} {el:.0f}s ~{el/(n+1)*(len(jobs)-n-1)/60:.0f}m left", flush=True)
        print(f"cell65 {judge}: complete", flush=True)


def _load() -> dict[str, dict[str, str | None]]:
    """judge -> {key without the judge prefix: 'A' | 'B' | None}. A judgment
    that hit the context limit is treated as unusable."""
    data: dict[str, dict] = {j: {} for j in list(STORED) + list(NEW_JUDGES)}
    for judge, path in STORED.items():
        for k, v in json.loads(path.read_text()).items():
            if k.startswith(judge + "|"):
                data[judge][k.split("|", 1)[1]] = v
    for r in runlog.read_jsonl(CALLS):
        data[r["judge"]][r["key"].split("|", 1)[1]] = None if r["audit"].get("ctx_hit") else r["winner"]
    return data


def stage_measure() -> None:
    cs = cases41()
    data = _load()
    print("=" * 78)
    print("CELL 65 — judge preference with four added judges (all pairs; a split pair counts half)")
    print("=" * 78)
    result, decisions, case_means = {}, {}, {}
    for judge, got in data.items():
        if not got:
            continue
        total = len(COMPARISONS) * len(cs) * REPEATS
        usable_pairs, first, n_single = 0, 0, 0
        per = {}
        for comp in COMPARISONS:
            by, cnt = collections.defaultdict(list), collections.Counter()
            for c in cs:
                for r in range(REPEATS):
                    f, v = got.get(f"{comp}|{c}|{r}|fwd"), got.get(f"{comp}|{c}|{r}|rev")
                    if f is None or v is None:
                        continue
                    usable_pairs += 1
                    first += (f == "A") + (v == "A")
                    n_single += 2
                    s = ((f == "A") + (v == "B")) / 2
                    by[c].append(s)
                    cnt["win" if s == 1 else "loss" if s == 0 else "tie"] += 1
                    decisions.setdefault((comp, c, r), {})[judge] = s
            case_means[(judge, comp)] = {c: st.mean(v) for c, v in by.items()}
            d = [m - 0.5 for m in case_means[(judge, comp)].values()]
            if len(d) >= 2:
                m, lo, hi = t_interval(d)
                per[comp] = {"win": cnt["win"], "loss": cnt["loss"], "tie": cnt["tie"],
                             "all_pairs": st.mean(x for v in by.values() for x in v),
                             "mean": m, "lo": lo, "hi": hi, "p": sign_flip_p(d), "k": len(d)}
        unusable = 1 - usable_pairs / total
        first_share = first / n_single if n_single else None
        result[judge] = {"unusable": unusable, "first_listed_chosen": first_share,
                         "comparisons": per, "new": judge in NEW_JUDGES,
                         "counts": unusable <= UNUSABLE_LIMIT and first_share is not None and first_share < FIRST_LIMIT}
    print(f"\n  {'judge':<12}{'comparison':<36}{'win/loss/tie':>14}{'all pairs':>11}   scenario-level, minus 0.5")
    for judge, res in result.items():
        tag = "" if res["counts"] or not res["new"] else "   [does not count: shown only]"
        for comp in COMPARISONS:
            p = res["comparisons"].get(comp)
            if p:
                print(f"  {judge.split(':')[0]:<12}{LABEL[comp]:<36}{p['win']:>5}/{p['loss']}/{p['tie']:<4}"
                      f"{p['all_pairs']:>10.3f}   {p['mean']:+.3f} [{p['lo']:+.3f}, {p['hi']:+.3f}]  "
                      f"p = {p['p']:.4f}  (k = {p['k']}){tag}")
    print("\n  share of single judgments that chose the first-listed answer, and unusable pairs:")
    for judge, res in result.items():
        print(f"    {judge:<34} first-listed {res['first_listed_chosen']:.3f}   unusable {res['unusable']:.3f}"
              + ("" if not res["new"] else "   counts" if res["counts"] else "   does not count"))

    counted = [j for j in NEW_JUDGES if result.get(j, {}).get("counts")]
    print(f"\nVERDICT LINES (as registered; pooled over the {len(counted)} added judges that count)")
    verdicts = {}
    for pid, comp, sign, bar in (("P65.1", "C1", +1, 0.075), ("P65.2", "C2", -1, 0.052), ("P65.3", "C3", -1, 0.052)):
        d = []
        for c in cs:
            v = [case_means[(j, comp)][c] for j in counted if c in case_means.get((j, comp), {})]
            if v:
                d.append(st.mean(v) - 0.5)
        if len(counted) < 2 or len(d) < 2:
            verdicts[pid] = {"verdict": "NOT EVALUABLE (fewer than two added judges count)"}
            print(f"  {pid} NOT EVALUABLE — fewer than two added judges count")
            continue
        m, lo, hi = t_interval(d)
        pv = sign_flip_p(d)
        if sign > 0:
            word = "SUPPORTED" if lo > 0 else "FALSIFIED" if hi < bar else "NOT EVALUABLE"
        else:
            word = "SUPPORTED" if hi < 0 else "FALSIFIED" if lo > -bar else "NOT EVALUABLE"
        lean = [j for j in counted if (q := result[j]["comparisons"].get(comp)) and q["mean"] * sign > 0]
        verdicts[pid] = {"verdict": word, "mean": m, "lo": lo, "hi": hi, "p": pv, "k": len(d), "lean": lean}
        print(f"  {pid} {word} — {LABEL[comp]}: pooled all-pairs score minus 0.5 = {m:+.3f} [{lo:+.3f}, {hi:+.3f}], "
              f"sign-flip p = {pv:.4f}, {len(d)} scenarios; {len(lean)} of {len(counted)} judges lean the expected way")

    print("\nreported without a pass/fail: agreement between judges on which side wins a pair (split pairs left out)")
    judges = [j for j in result if result[j]["counts"] or j in STORED]
    for i, a_ in enumerate(judges):
        for b_ in judges[i + 1:]:
            pairs = [(d[a_] == 1, d[b_] == 1) for d in decisions.values()
                     if a_ in d and b_ in d and d[a_] != 0.5 and d[b_] != 0.5]
            if len(pairs) >= 20:
                k = kappa(pairs)
                print(f"    {a_.split(':')[0]:<10} and {b_.split(':')[0]:<10} n = {k['n']:>3}  raw {k['raw']:.3f}  kappa {k['kappa']:.3f}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "measured.json").write_text(json.dumps({"judges": result, "verdicts": verdicts}, indent=1, default=float))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "measure"
    if stage == "judge":
        stage_judge(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        {"smoke": stage_smoke, "measure": stage_measure}[stage]()
