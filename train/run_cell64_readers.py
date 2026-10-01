"""Cell 64 — is the appended caveat used by other readers, without being told
to look, and when it is one line among many?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 64 PRE-REGISTRATION".

Cell 51 found that a decision-relevant caveat in the appended list changed a
reader's decision. Three things limit that result: two readers (one of them
the editor model itself); a reader instruction that named the attachment
("the report and anything attached to it"); and a list that was one line
long. This cell repeats the measurement with six readers, with and without
the instruction clause, and with the planted line placed among real caveats.

Items: the 11 Cell 51 items that passed its pilot gate (no new item is
written). Documents: the same Cell 41 control answers Cell 51 used.

Arms (prompt / what the list holds / list length):
  old      bare                      (no list)                  floor
  old      rel | irr           1     exact Cell 51 arms         P64.1
  neutral  bare                      (no list)                  floor
  neutral  rel | irr           1                                P64.2
  neutral  rel | irr           5
  neutral  rel | irr          10                                P64.3

`rel` holds the item's decision-relevant caveat, `irr` its authored
irrelevant one, at the same position among the same real caveats, so the two
arms of a pair differ in that one line only.

Run:  .venv/bin/python train/run_cell64_readers.py smoke      (items Cell 51 excluded)
      .venv/bin/python train/run_cell64_readers.py runs [reader]
      .venv/bin/python train/run_cell64_readers.py measure
"""
from __future__ import annotations

import collections
import json
import random
import re
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                              # noqa: E402
from gst.smallcluster import sign_flip_p, t_interval                # noqa: E402
from train.run_cell47_redundancy import norm                        # noqa: E402
from train.run_cell49_arbitration import anchored_in                # noqa: E402
from train.run_cell51_uptake import (SYSTEM, TOKENS, arm_text,      # noqa: E402
                                     artifacts_by_case, parse_answer)

REGISTRATION = runlog.registration_for("64", ROOT)
OUT = ROOT / "bench" / "analysis" / "cell64"
RUNS = ROOT / "bench" / "runs" / "cell64_readers.jsonl"
C51 = ROOT / "bench" / "analysis" / "cell51"
READERS = ("gpt-oss:20b", "qwen2.5:7b-instruct", "phi4:14b",
           "qwen3-vl:30b-a3b-instruct", "llama3:8b-instruct-q4_K_M",
           "mistral:7b-instruct-v0.3-q4_K_M")
NEW_READERS = READERS[2:]                 # not used in Cell 51
REPEATS = 5
MAX_RESAMPLE = 6
TEMPERATURE = 0.8
MAX_TOKENS = 2048
CLAUSE = " strictly on the basis of the report and anything attached to it"
assert CLAUSE in SYSTEM
PROMPTS = {"old": SYSTEM, "neutral": SYSTEM.replace(CLAUSE, "")}     # one clause removed
ARMS = (("old", "bare", 0), ("old", "rel", 1), ("old", "irr", 1),
        ("neutral", "bare", 0), ("neutral", "rel", 1), ("neutral", "irr", 1),
        ("neutral", "rel", 5), ("neutral", "irr", 5),
        ("neutral", "rel", 10), ("neutral", "irr", 10))
HEADER = "\n\n---\nASSUMPTIONS & CAVEATS (as stated by the specialist contributors)\n- "
MATERIAL = 0.25                           # Cell 51's bar for a material difference


# ------------------------------------------------------------------ material

def items_kept() -> list[dict]:
    frozen = json.loads((C51 / "frozen.json").read_text())
    keep = set(json.loads((C51 / "pilot_gate.json").read_text())["keep"])
    return [it for it in frozen if it["id"] in keep]


def items_excluded() -> list[dict]:
    frozen = json.loads((C51 / "frozen.json").read_text())
    keep = set(json.loads((C51 / "pilot_gate.json").read_text())["keep"])
    return [it for it in frozen if it["id"] not in keep]


_pool_cache: dict | None = None


def caveat_pool() -> dict[str, list[str]]:
    """Real specialist caveats per case (the Cell 48 lists): one line each,
    40 to 300 characters, table rows left out."""
    global _pool_cache
    if _pool_cache is None:
        import train.run_cell48_freight as c48
        raw = {**c48.old_case_caveats(), **c48.new_case_caveats()}
        _pool_cache = {case: sorted({c.strip() for c in v
                                     if "\n" not in c.strip() and 40 <= len(c.strip()) <= 300
                                     and not c.strip().startswith("|")})
                       for case, v in raw.items()}
    return _pool_cache


def fillers(it: dict, k: int, rep: int) -> tuple[list[str], int, int]:
    """The k-1 real caveats that surround the planted line, the position of
    the planted line, and how many of the fillers come from the item's own
    case. Fixed by (item, k, repeat); shared by both arms and all readers.
    Own-case caveats are used first; the rest come from the other cases."""
    if k <= 1:
        return [], 0, 0
    rng = random.Random(f"cell64|{it['id']}|{k}|{rep}")
    probes = [norm(p) for p in it["probes"]]
    ok = lambda c: not any(anchored_in(p, norm(c)) for p in probes)      # noqa: E731
    pool = caveat_pool()
    own = [c for c in pool.get(it["case"], []) if ok(c)]
    other = [c for case in sorted(pool) if case != it["case"] for c in pool[case] if ok(c)]
    rng.shuffle(own)
    rng.shuffle(other)
    n_own = min(len(own), k - 1)
    chosen = own[:n_own] + other[:k - 1 - n_own]
    rng.shuffle(chosen)
    return chosen, rng.randrange(k), n_own


def document(base: str, it: dict, kind: str, k: int, rep: int) -> tuple[str, dict]:
    if kind == "bare":
        return base, {"position": None, "own_case_fillers": None}
    target = it["caveat"] if kind == "rel" else it["irrelevant"]
    fill, pos, n_own = fillers(it, k, rep)
    lines = fill[:pos] + [target] + fill[pos:]
    text = base + HEADER + "\n- ".join(lines)
    if k == 1:      # byte-identical to the Cell 51 arm
        assert text == arm_text(base, "app-rel" if kind == "rel" else "app-irr", it)
    return text, {"position": pos, "own_case_fillers": n_own}


# ------------------------------------------------------------------ running

def _read(reader: str, prompt: str, text: str, question: str, run_id: str):
    meta = None
    for attempt in range(MAX_RESAMPLE):
        t, meta = runlog.chat_logged(reader, PROMPTS[prompt], text + "\n\nQUESTION: " + question,
                                     temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
                                     seed=runlog.seed_for(run_id) + attempt)
        t = re.sub(r"<think>.*?</think>", "", t or "", flags=re.DOTALL)
        a = parse_answer(t)
        if a is not None:
            return a, attempt + 1, meta
    return None, MAX_RESAMPLE, meta


def _run(reader: str, it: dict, base: str, prompt: str, kind: str, k: int, rep: int, tag: str = "") -> dict:
    run_id = f"{tag}{reader}|{it['id']}|{prompt}|{kind}|{k}|{rep}"
    text, info = document(base, it, kind, k, rep)
    ans, tries, meta = _read(reader, prompt, text, it["question"], run_id)
    row = {"run_id": run_id, "reader": reader, "item": it["id"], "case": it["case"],
           "prompt": prompt, "kind": kind, "k": k, "rep": rep, "answer": ans, "tries": tries, **info}
    return runlog.stamp(row, meta, root=ROOT, script=Path(__file__), registration=REGISTRATION)


def stage_smoke() -> None:
    """One read per reader on an item Cell 51 EXCLUDED at its pilot gate
    (not among the 11 registered items). Nothing is written to the run file."""
    it = items_excluded()[0]
    base = artifacts_by_case()[it["case"]]
    for reader in READERS:
        for prompt, kind, k in (("old", "rel", 1), ("neutral", "rel", 10)):
            r = _run(reader, it, base, prompt, kind, k, 0, tag="SMOKE|")
            a = r["audit"]
            print(f"  {reader:<34} {prompt:<8} k={k:<3} answer={r['answer']} tries={r['tries']} "
                  f"prompt_tokens={a.get('prompt_tokens')} ctx={a.get('num_ctx')} "
                  f"ctx_hit={a.get('ctx_hit')} wall={a.get('wall_s')}s", flush=True)


def stage_runs(only: str | None = None) -> None:
    items = items_kept()
    assert len(items) == 11, "the registered item set is the 11 items Cell 51 kept"
    arts = artifacts_by_case()
    done = {r["run_id"] for r in runlog.read_jsonl(RUNS)}
    for reader in ([only] if only else READERS):
        jobs = [(it, p, kind, k, rep) for it in items for (p, kind, k) in ARMS for rep in range(REPEATS)
                if f"{reader}|{it['id']}|{p}|{kind}|{k}|{rep}" not in done]
        print(f"cell64 {reader}: {len(jobs)} reads to go", flush=True)
        t0, fails = time.time(), 0
        for n, (it, p, kind, k, rep) in enumerate(jobs):
            row = _run(reader, it, arts[it["case"]], p, kind, k, rep)
            if row["audit"].get("error"):
                fails += 1
                print(f"  ERROR {row['run_id']}: {row['audit']['error']} (consecutive {fails})", flush=True)
                if fails >= 5:
                    raise SystemExit("ABORTING — five consecutive call errors; resumable.")
                continue
            fails = 0
            runlog.append_jsonl(RUNS, row)
            if (n + 1) % 50 == 0:
                el = time.time() - t0
                print(f"  {n+1}/{len(jobs)} {el:.0f}s ~{el/(n+1)*(len(jobs)-n-1)/60:.0f}m left", flush=True)
        print(f"cell64 {reader}: complete", flush=True)


# ------------------------------------------------------------------ measure

def _flip_share(rows, it) -> float | None:
    a = [r["answer"] for r in rows if r["answer"] is not None]
    return sum(1 for x in a if x == it["flipped"]) / len(a) if a else None


def _uptake(rows, items, reader, prompt, k) -> dict[int, float]:
    """Per item: flip share with the relevant line minus with the irrelevant one."""
    out = {}
    for it in items:
        sel = [r for r in rows if r["reader"] == reader and r["item"] == it["id"]
               and r["prompt"] == prompt and r["k"] == k]
        a = _flip_share([r for r in sel if r["kind"] == "rel"], it)
        b = _flip_share([r for r in sel if r["kind"] == "irr"], it)
        if a is not None and b is not None:
            out[it["id"]] = a - b
    return out


def _summ(d: dict[int, float]) -> dict | None:
    v = list(d.values())
    if len(v) < 2:
        return None
    m, lo, hi = t_interval(v)
    return {"mean": m, "lo": lo, "hi": hi, "p": sign_flip_p(v), "k": len(v)}


def _fmt(s: dict | None) -> str:
    return "n/a" if not s else (f"{s['mean']:+.3f} [{s['lo']:+.3f}, {s['hi']:+.3f}]  "
                                f"sign-flip p = {s['p']:.4f}  ({s['k']} items)")


def _directional(s: dict | None, expect: int) -> str:
    """Registered reading of an interval for a prediction that expects the
    difference to be above 0 (expect=+1) or below 0 (expect=-1)."""
    if not s:
        return "NOT EVALUABLE"
    if s["lo"] > 0 or s["hi"] < 0:
        return "SUPPORTED" if (s["lo"] > 0) == (expect > 0) else "REVERSED"
    if -MATERIAL < s["lo"] and s["hi"] < MATERIAL:
        return f"FALSIFIED (the interval spans zero inside ±{MATERIAL}: no material difference)"
    return "NOT EVALUABLE (the interval spans zero and is wider than the material band)"


def stage_measure() -> None:
    items = items_kept()
    by = {it["id"]: it for it in items}
    all_rows = [r for r in runlog.read_jsonl(RUNS) if r["item"] in by]
    rows = [r for r in all_rows if not r["audit"].get("ctx_hit")]
    print("=" * 78)
    print("CELL 64 — is the appended caveat used by other readers?")
    print("=" * 78)
    print(f"reads: {len(all_rows)}; set aside for a context-limit hit: {len(all_rows) - len(rows)}")
    result = {"readers": {}}

    print("\nCHECK per reader: bare documents must give the default answer (flip share at most 0.20 under "
          "each prompt) and at most 20% of reads may be unusable")
    passing = []
    for rd in READERS:
        rr = [r for r in rows if r["reader"] == rd]
        if not rr:
            continue
        invalid = sum(1 for r in rr if r["answer"] is None) / len(rr)
        floors = {}
        for p in PROMPTS:
            b = [r for r in rr if r["prompt"] == p and r["kind"] == "bare" and r["answer"] is not None]
            floors[p] = (sum(1 for r in b if r["answer"] == by[r["item"]]["flipped"]) / len(b)) if b else None
        ok = invalid <= 0.20 and all(f is not None and f <= 0.20 for f in floors.values())
        if ok:
            passing.append(rd)
        result["readers"][rd] = {"n": len(rr), "invalid": invalid, "floor": floors, "gate": ok}
        fl = {k: ("n/a" if v is None else f"{v:.3f}") for k, v in floors.items()}
        print(f"  {rd:<34} reads {len(rr):>4}  unusable {invalid:.3f}  bare flip old {fl['old']}"
              f"  neutral {fl['neutral']}  -> {'PASS' if ok else 'FAIL'}")

    print("\nuptake per reader (flip share with the relevant line minus with the irrelevant line; item level)")
    for rd in READERS:
        if rd not in result["readers"]:
            continue
        res = {}
        print(f"  {rd}" + ("" if rd in passing else "   [failed the check; shown, not counted]"))
        for p, k in (("old", 1), ("neutral", 1), ("neutral", 5), ("neutral", 10)):
            s = _summ(_uptake(rows, items, rd, p, k))
            res[f"{p}|{k}"] = s
            print(f"    {p:<8} list of {k:<3} {_fmt(s)}")
        result["readers"][rd]["uptake"] = res

    new_ok = [rd for rd in NEW_READERS if rd in passing]

    def pooled(fn, readers=None) -> dict[int, float]:
        out = {}
        for it in items:
            v = [d[it["id"]] for rd in (readers if readers is not None else passing) if it["id"] in (d := fn(rd))]
            if v:
                out[it["id"]] = st.mean(v)
        return out

    up = {(p, k): {rd: _uptake(rows, items, rd, p, k) for rd in passing}
          for p, k in (("old", 1), ("neutral", 1), ("neutral", 5), ("neutral", 10))}

    def diff(a, b):
        def f(rd):
            return {i: up[a][rd][i] - up[b][rd][i] for i in up[a][rd] if i in up[b][rd]}
        return f

    p1 = _summ(pooled(lambda rd: up[("old", 1)][rd], new_ok)) if len(new_ok) >= 2 else None
    p2 = _summ(pooled(diff(("old", 1), ("neutral", 1))))
    p3 = _summ(pooled(diff(("neutral", 10), ("neutral", 1))))
    p3b = _summ(pooled(diff(("neutral", 5), ("neutral", 1))))
    lvl = {f"{p}|{k}": _summ(pooled(lambda rd, p=p, k=k: up[(p, k)][rd])) for (p, k) in up}
    print(f"\npooled over the {len(passing)} readers that passed the check (item level):")
    for name, s in lvl.items():
        print(f"  uptake {name:<12} {_fmt(s)}")
    if len(new_ok) < 2 or not p1:
        v1 = "NOT EVALUABLE (fewer than two new readers passed the check)"
    elif p1["lo"] > 0:
        v1 = "SUPPORTED"
    elif p1["hi"] < MATERIAL:
        v1 = f"FALSIFIED (not above zero, and the upper end is below {MATERIAL})"
    else:
        v1 = "NOT EVALUABLE (the interval reaches zero and its upper end is above the material bar)"
    v2, v3 = _directional(p2, +1), _directional(p3, -1)
    print(f"\nVERDICT LINES (as registered)")
    print(f"  P64.1 {v1} — old prompt, one-line list, pooled over the {len(new_ok)} new readers that passed: {_fmt(p1)}")
    print(f"  P64.2 {v2} — uptake with the instruction clause minus without it (one-line list): {_fmt(p2)}")
    print(f"  P64.3 {v3} — uptake at 10 lines minus at 1 line (neutral prompt): {_fmt(p3)}")
    print(f"  (5 lines minus 1 line, shown beside: {_fmt(p3b)})")

    print("\ndescriptive")
    for k in (5, 10):
        full = [it["id"] for it in items if fillers(it, k, 0)[2] == k - 1]
        d = pooled(lambda rd, k=k: up[("neutral", k)][rd])
        a = [d[i] for i in full if i in d]
        b = [d[i] for i in d if i not in full]
        print(f"  list of {k}: uptake where every surrounding line is from the item's own case "
              f"{st.mean(a) if a else float('nan'):+.3f} ({len(a)} items); elsewhere "
              f"{st.mean(b) if b else float('nan'):+.3f} ({len(b)} items)")
    pos = collections.defaultdict(list)
    for r in rows:
        if r["reader"] in passing and r["kind"] == "rel" and r["k"] == 10 and r["answer"] is not None:
            pos["first three" if r["position"] < 3 else "last three" if r["position"] > 6 else "middle"].append(
                r["answer"] == by[r["item"]]["flipped"])
    print("  list of 10, flip share by where the relevant line sits: "
          + ", ".join(f"{k} {st.mean(v):.3f} (n={len(v)})" for k, v in sorted(pos.items())))
    for p, k in (("neutral", 10),):
        fl = [r["answer"] == by[r["item"]]["flipped"] for r in rows if r["reader"] in passing
              and r["prompt"] == p and r["kind"] == "irr" and r["k"] == k and r["answer"] is not None]
        bl = [r["answer"] == by[r["item"]]["flipped"] for r in rows if r["reader"] in passing
              and r["prompt"] == p and r["kind"] == "bare" and r["answer"] is not None]
        print(f"  flip share with ten real caveats and no relevant line {st.mean(fl) if fl else float('nan'):.3f}; "
              f"with no list {st.mean(bl) if bl else float('nan'):.3f}")
    for rd, was in (("gpt-oss:20b", 0.691), ("qwen2.5:7b-instruct", 0.455)):
        s = result["readers"].get(rd, {}).get("uptake", {}).get("old|1")
        if s:
            print(f"  repeat of Cell 51 on {rd}: {s['mean']:+.3f} now, {was:+.3f} then")
    result.update({"passing": passing, "P64.1": {"new_passing": new_ok, "pooled": p1, "verdict": v1},
                   "P64.2": {"pooled": p2, "verdict": v2}, "P64.3": {"pooled": p3, "verdict": v3},
                   "k5_minus_k1": p3b, "levels": lvl})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "measured.json").write_text(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "measure"
    if stage == "runs":
        stage_runs(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        {"smoke": stage_smoke, "measure": stage_measure}[stage]()
