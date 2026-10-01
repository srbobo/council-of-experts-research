"""Cell 63 — a wrong figure the editor could check.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 63 PRE-REGISTRATION".
Items frozen in docs/CELL63_ITEMS.json by the `items` stage (mechanical rule,
no item written by judgment).

Every item is a Cell 60 or Cell 60-R question whose answer is COMPUTED by the
generator script. One input figure is altered by a fixed rule; the answer
under the altered figure is computed by the same engine. The editor (the
Cell 30 one-sentence writer prompt) receives three short scripted analyst
contributions and the question, in five layouts:

  C0  the case states the figure; an analyst repeats it correctly
  C1  the case states the right figure; an analyst quotes a wrong one
  C2  the figure is removed from the case; one analyst supplies a wrong one
  C3  removed; one analyst supplies a wrong figure, another the right one
  C4  removed; two analysts supply two different wrong figures

Scoring is by script: the final ANSWER line against the engine's answers, and
whether the reply mentions both conflicting figures. No judge.

Run:  .venv/bin/python train/run_cell63_checkable.py items
      .venv/bin/python train/run_cell63_checkable.py smoke        (excluded items only)
      .venv/bin/python train/run_cell63_checkable.py runs [writer]
      .venv/bin/python train/run_cell63_checkable.py measure
"""
from __future__ import annotations

import collections
import json
import re
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))
sys.path.insert(0, str(ROOT / "train"))

import gen_cell60_items as G60                                   # noqa: E402
import gen_cell60R_items as G60R                                 # noqa: E402
from gst import runlog                                           # noqa: E402
from gst.smallcluster import paired_diffs, sign_flip_p, t_interval  # noqa: E402
from train.run_cell30_descaffold import WRITER_PROMPT            # noqa: E402
from train.run_cell60_accuracy import correct, parse_answer      # noqa: E402

REGISTRATION = runlog.registration_for("63", ROOT)
OUT = ROOT / "bench" / "analysis" / "cell63"
RUNS = ROOT / "bench" / "runs" / "cell63_checkable.jsonl"
ITEMS_PATH = ROOT / "docs" / "CELL63_ITEMS.json"
WRITERS = {"gpt-oss:20b": 16384,                 # primary; reasoning model, Cell 60 budget
           "phi4:14b": 4096,                     # replication
           "qwen3-vl:30b-a3b-instruct": 4096}    # replication
PRIMARY = "gpt-oss:20b"
CONDS = ("C0", "C1", "C2", "C3", "C4")
REPEATS = 2                      # repeat 0 / 1 swap which analyst is listed first
TEMPERATURE = 0.6
PLACEHOLDER = "[figure given in the analysts' passages]"
NOTE_FIG = 'Analyst {who}: for reference, the passage I am working from reads: "{passage}"'
NOTE_NONE = "Analyst {who}: I have no figures to add beyond those in the case."
NUMCH = set("0123456789")


# ------------------------------------------------------------------ items

def _perturb(v, up: bool):
    """Fixed alteration rule. Integers only; about 20-25% up or down, keeping
    the figure's round-number shape."""
    if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
        return None
    if v >= 1000:
        step = 10 ** (len(str(v)) - 2)
        w = int(round(v * (1.2 if up else 0.8) / step) * step)
    else:
        w = int(round(v * (1.25 if up else 0.75)))
        if w == v:
            w = v + 1 if up else v - 1
    return w if w > 0 and w != v else None


def _token_span(a: str, b: str):
    """The single differing figure in two prompts that differ in one input.
    Returns (start, end_in_a, end_in_b) widened to the whole figure, or None
    when the prompts differ in more than one place."""
    cp = 0
    while cp < min(len(a), len(b)) and a[cp] == b[cp]:
        cp += 1
    cs = 0
    while cs < min(len(a), len(b)) - cp and a[-1 - cs] == b[-1 - cs]:
        cs += 1
    start, ea, eb = cp, len(a) - cs, len(b) - cs
    # widen left over digits, and over , or . that sit between two digits
    while start > 0 and (a[start - 1] in NUMCH or
                         (a[start - 1] in ",." and start >= 2 and a[start - 2] in NUMCH
                          and start < len(a) and a[start] in NUMCH)):
        start -= 1
    if start > 0 and a[start - 1] == "$":
        start -= 1

    def widen_right(s: str, e: int) -> int:
        while e < len(s) and (s[e] in NUMCH or
                              (s[e] in ",." and e + 1 < len(s) and s[e + 1] in NUMCH)):
            e += 1
        if e < len(s) and s[e] == "%":
            e += 1
        return e
    ea, eb = widen_right(a, ea), widen_right(b, eb)
    ta, tb = a[start:ea], b[start:eb]
    # each side must be one plain figure; if the prompts differ in two places
    # the span between them contains words and is rejected here
    fig = re.compile(r"^\$?\d[\d,]*(?:\.\d+)?%?$")
    if not fig.match(ta) or not fig.match(tb):
        return None
    if a[:start] != b[:start] or a[ea:] != b[eb:]:
        return None
    return start, ea, eb


def _sentence(text: str, start: int, end: int) -> tuple[int, int]:
    """Bounds of the sentence containing text[start:end]."""
    cuts = [0] + [m.end() for m in re.finditer(r"(?<=[.?!])\s+(?=[A-Z(])", text)] + [len(text)]
    for i in range(len(cuts) - 1):
        if cuts[i] <= start < cuts[i + 1]:
            return cuts[i], cuts[i + 1]
    return 0, len(text)


def _digits(tok: str) -> str:
    return "".join(c for c in tok if c in NUMCH or c == ".").strip(".")


def _distinct(*answers) -> bool:
    vals = [float(x) for x in answers]
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            a, b = vals[i], vals[j]
            if abs(a - b) <= 2 * max(0.005 * max(abs(a), abs(b)), 0.01):
                return False
    return True


def build_items() -> tuple[list[dict], list[dict]]:
    items, excluded = [], []
    for src, mod in (("C60", G60), ("C60R", G60R)):
        for tname, fn, variants in mod.SPECS:
            for vi, params in enumerate(variants):
                iid = f"{tname}_v{vi}"
                out0 = fn(*params)
                p0, a0 = out0[0], out0[1]
                chosen, why = None, "no integer input that appears once and moves the answer both ways"
                for pi, v in enumerate(params):
                    w1, w2 = _perturb(v, True), _perturb(v, False)
                    if w1 is None or w2 is None:
                        continue
                    try:
                        q1, q2 = list(params), list(params)
                        q1[pi], q2[pi] = w1, w2
                        o1, o2 = fn(*q1), fn(*q2)
                    except Exception:                          # noqa: BLE001
                        continue
                    s1, s2 = _token_span(p0, o1[0]), _token_span(p0, o2[0])
                    if not s1 or not s2 or s1[0] != s2[0] or s1[1] != s2[1]:
                        continue
                    if not _distinct(a0, o1[1], o2[1]):
                        continue
                    start, end = s1[0], s1[1]
                    tok0, tok1, tok2 = p0[start:end], o1[0][start:s1[2]], o2[0][start:s2[2]]
                    d0, d1, d2 = _digits(tok0), _digits(tok1), _digits(tok2)
                    ambient = p0[:start] + " " + p0[end:]
                    # neither altered figure may already occur in the case text
                    if any(re.search(r"(?<![\d.,])" + re.escape(t.lstrip("$").rstrip("%")) + r"(?![\d])", ambient)
                           for t in (tok1, tok2)):
                        continue
                    if len({d0, d1, d2}) < 3:
                        continue
                    sa, sb = _sentence(p0, start, end)
                    chosen = {
                        "id": iid, "source": src, "template": tname, "param_index": pi,
                        "right": v, "wrong1": w1, "wrong2": w2,
                        "tok": {"right": tok0, "wrong1": tok1, "wrong2": tok2},
                        "case": p0,
                        "case_removed": p0[:start] + PLACEHOLDER + p0[end:],
                        "passage": {"right": p0[sa:sb].strip(),
                                    "wrong1": (p0[sa:start] + tok1 + p0[end:sb]).strip(),
                                    "wrong2": (p0[sa:start] + tok2 + p0[end:sb]).strip()},
                        "answer": {"right": a0, "wrong1": o1[1], "wrong2": o2[1]},
                    }
                    break
                if chosen:
                    items.append(chosen)
                else:
                    excluded.append({"id": iid, "source": src, "template": tname,
                                     "params": repr(params), "case": p0, "answer": a0, "reason": why})
    return items, excluded


def stage_items() -> None:
    items, excluded = build_items()
    by_t = collections.Counter(i["template"] for i in items)
    print(f"usable items: {len(items)}; excluded: {len(excluded)}; templates: {len(by_t)}")
    print("  per template:", dict(sorted(by_t.items())))
    if len(items) < 40 or len(by_t) < 10:
        raise SystemExit("ITEM GUARDS FAILED — registered minimums (40 items, 10 templates) not met")
    ITEMS_PATH.write_text(json.dumps({
        "note": ("Cell 63 items. Built by train/run_cell63_checkable.py `items` from the Cell 60 and "
                 "60-R engines; re-running must reproduce this file. One integer input per item is "
                 "altered by a fixed rule and the answers are computed by the engine."),
        "items": items, "excluded": excluded}, indent=1, ensure_ascii=False))
    print(f"wrote {ITEMS_PATH}")
    ex = items[0]
    print("example:", ex["id"], ex["tok"], ex["answer"])


def load_items() -> list[dict]:
    return json.loads(ITEMS_PATH.read_text())["items"]


# ------------------------------------------------------------------ prompts

def layout(it: dict, cond: str, rep: int) -> dict:
    """What the case shows and what analysts A and B quote."""
    swap = rep % 2 == 1
    if cond == "C0":
        return {"case": it["case"], "A": "right", "B": None}
    if cond == "C1":
        return {"case": it["case"], "A": "wrong1", "B": None}
    if cond == "C2":
        return {"case": it["case_removed"], "A": "wrong1", "B": None}
    if cond == "C3":
        a, b = ("right", "wrong1") if swap else ("wrong1", "right")
        return {"case": it["case_removed"], "A": a, "B": b}
    if cond == "C4":
        a, b = ("wrong2", "wrong1") if swap else ("wrong1", "wrong2")
        return {"case": it["case_removed"], "A": a, "B": b}
    raise ValueError(cond)


def compose(it: dict, cond: str, rep: int) -> tuple[str, str]:
    lay = layout(it, cond, rep)
    notes = []
    for who in ("A", "B", "C"):
        key = lay.get(who)
        notes.append(NOTE_FIG.format(who=who, passage=it["passage"][key]) if key
                     else NOTE_NONE.format(who=who))
    body = "\n\n".join(f"--- SPECIALIST CONTRIBUTION ---\n{t}" for t in notes)
    return WRITER_PROMPT, f"{body}\n\nQuestion:\n{lay['case']}{G60.FMT}"


def _has_figure(text: str, tok: str) -> bool:
    """Known-value check: the figure's digits appear as a whole number in the
    reply (thousands separators and currency or percent signs ignored)."""
    flat = re.sub(r"(?<=\d)[,    ](?=\d{3}(?!\d))", "", text)
    d = _digits(tok)
    return re.search(r"(?<![\d.])" + re.escape(d) + r"(?![\d]|\.\d)", flat) is not None


def classify(text: str, it: dict, cond: str) -> dict:
    val = parse_answer(text)
    if val is None:
        outcome = "none"
    elif correct(val, it["answer"]["right"]):
        outcome = "right"
    elif correct(val, it["answer"]["wrong1"]):
        outcome = "wrong1"
    elif correct(val, it["answer"]["wrong2"]):
        outcome = "wrong2"
    else:
        outcome = "other"
    pair = {"C1": ("right", "wrong1"), "C3": ("right", "wrong1"), "C4": ("wrong1", "wrong2")}.get(cond)
    both = bool(pair and _has_figure(text, it["tok"][pair[0]]) and _has_figure(text, it["tok"][pair[1]]))
    return {"val": val, "outcome": outcome, "both_figures": both}


# ------------------------------------------------------------------ running

def _run_one(writer: str, it: dict, cond: str, rep: int, tag: str = "") -> dict | None:
    run_id = f"{tag}{it['id']}__{cond}__r{rep}__{writer}"
    system, user = compose(it, cond, rep)
    text, meta = None, None
    for attempt in range(3):
        text, meta = runlog.chat_logged(writer, system, user, temperature=TEMPERATURE,
                                        max_tokens=WRITERS[writer],
                                        seed=runlog.seed_for(run_id) + attempt)
        if text and text.strip():
            break
        time.sleep(5 * (attempt + 1))
    if not text or not text.strip():
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    row = {"run_id": run_id, "item": it["id"], "template": it["template"], "cond": cond,
           "rep": rep, "writer": writer, "layout": layout(it, cond, rep) | {"case": None},
           **classify(text, it, cond), "chars": len(text), "output": text}
    return runlog.stamp(row, meta, root=ROOT, script=Path(__file__), registration=REGISTRATION)


def stage_smoke() -> None:
    """Plumbing check on EXCLUDED items only. Nothing here is a registered run
    and nothing is written to the run file."""
    excluded = json.loads(ITEMS_PATH.read_text())["excluded"]
    if not excluded:
        raise SystemExit("no excluded items to smoke-test on")
    ex = excluded[0]
    fake = {"id": "smoke_" + ex["id"], "template": ex["template"], "case": ex["case"],
            "case_removed": ex["case"], "tok": {"right": "0", "wrong1": "0", "wrong2": "0"},
            "passage": {"right": ex["case"][:200], "wrong1": ex["case"][:200], "wrong2": ex["case"][:200]},
            "answer": {"right": ex["answer"], "wrong1": -1, "wrong2": -2}}
    for writer in WRITERS:
        r = _run_one(writer, fake, "C0", 0, tag="SMOKE_")
        if r is None:
            print(f"  {writer}: NO REPLY")
            continue
        a = r["audit"]
        print(f"  {writer}: outcome={r['outcome']} val={r['val']} chars={r['chars']} "
              f"prompt_tokens={a.get('prompt_tokens')} output_tokens={a.get('output_tokens')} "
              f"wall={a.get('wall_s')}s ctx_hit={a.get('ctx_hit')} budget_exhausted={a.get('budget_exhausted')}")


def stage_runs(only: str | None = None) -> None:
    items = load_items()
    done = {r["run_id"] for r in runlog.read_jsonl(RUNS)}
    writers = [only] if only else list(WRITERS)
    for writer in writers:
        todo = [(it, c, r) for it in items for c in CONDS for r in range(REPEATS)
                if f"{it['id']}__{c}__r{r}__{writer}" not in done]
        print(f"cell63 {writer}: {len(todo)} runs to go", flush=True)
        t0, fails = time.time(), 0
        for k, (it, cond, rep) in enumerate(todo):
            row = _run_one(writer, it, cond, rep)
            if row is None:
                fails += 1
                print(f"  EMPTY {it['id']}/{cond}/r{rep} (consecutive {fails})", flush=True)
                if fails >= 5:
                    raise SystemExit("ABORTING — five consecutive empty replies; resumable.")
                continue
            fails = 0
            runlog.append_jsonl(RUNS, row)
            if (k + 1) % 20 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s ~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
        print(f"cell63 {writer}: complete", flush=True)


# ------------------------------------------------------------------ measure

def _rate(rows, pred) -> float:
    return sum(1 for r in rows if pred(r)) / len(rows) if rows else float("nan")


def _cluster(rows, key, a, b, value):
    ids, d = paired_diffs(rows, key, "cond", a, b, value)
    if len(d) < 2:
        return None
    m, lo, hi = t_interval(d)
    return {"mean": m, "lo": lo, "hi": hi, "p": sign_flip_p(d), "k": len(d)}


def measure_writer(rows: list[dict], label: str, verdicts: bool) -> dict:
    planted = lambda r: r["outcome"] in ("wrong1", "wrong2")      # noqa: E731
    usable = [r for r in rows if not r["audit"].get("ctx_hit")]
    set_aside = len(rows) - len(usable)
    print(f"\n--- {label}: {len(rows)} runs, {set_aside} set aside (context limit hit)")
    print(f"  {'layout':<6}{'n':>5}{'right':>8}{'planted':>9}{'other':>7}{'no answer':>11}{'both figures':>14}")
    out = {"n": len(rows), "set_aside": set_aside, "table": {}}
    for c in CONDS:
        rc = [r for r in usable if r["cond"] == c]
        cnt = collections.Counter(r["outcome"] for r in rc)
        row = {"n": len(rc), "right": cnt["right"], "planted": cnt["wrong1"] + cnt["wrong2"],
               "other": cnt["other"], "none": cnt["none"], "both_figures": sum(r["both_figures"] for r in rc)}
        out["table"][c] = row
        if rc:
            print(f"  {c:<6}{len(rc):>5}{row['right']/len(rc):>8.3f}{row['planted']/len(rc):>9.3f}"
                  f"{row['other']/len(rc):>7.3f}{row['none']/len(rc):>11.3f}"
                  f"{(row['both_figures']/len(rc) if c in ('C1','C3','C4') else float('nan')):>14.3f}")
    c0 = [r for r in usable if r["cond"] == "C0"]
    gate = _rate(c0, lambda r: r["outcome"] == "right")
    out["P63.0"] = {"c0_right": gate, "pass": gate >= 0.90}
    out["P63.1"] = {"c2_planted": _rate([r for r in usable if r["cond"] == "C2"], planted)}
    out["P63.2"] = _cluster(usable, "template", "C2", "C1", planted)
    out["P63.2_c1_rate"] = _rate([r for r in usable if r["cond"] == "C1"], planted)
    out["P63.3"] = _cluster(usable, "template", "C2", "C3", planted)
    c3 = [r for r in usable if r["cond"] == "C3" and r["outcome"] in ("right", "wrong1")]
    by_t = collections.defaultdict(list)
    for r in c3:
        by_t[r["template"]].append(r["outcome"] == "right")
    shares = [st.mean(v) for v in by_t.values()]
    out["P63.3_c3_right_share"] = ({"mean": t_interval(shares)[0], "lo": t_interval(shares)[1],
                                    "hi": t_interval(shares)[2], "k": len(shares), "n": len(c3)}
                                   if len(shares) >= 2 else None)
    c34 = [r for r in usable if r["cond"] in ("C3", "C4")]
    by_t = collections.defaultdict(list)
    for r in c34:
        by_t[r["template"]].append(bool(r["both_figures"]))
    shares = [st.mean(v) for v in by_t.values()]
    out["P63.4"] = ({"mean": t_interval(shares)[0], "lo": t_interval(shares)[1], "hi": t_interval(shares)[2],
                     "k": len(shares), "n": len(c34)} if len(shares) >= 2 else None)
    first = [r for r in usable if r["cond"] == "C3" and r["layout"]["A"] == "right" and r["outcome"] in ("right", "wrong1")]
    second = [r for r in usable if r["cond"] == "C3" and r["layout"]["A"] == "wrong1" and r["outcome"] in ("right", "wrong1")]
    out["P63.5_order"] = {"right_when_listed_first": _rate(first, lambda r: r["outcome"] == "right"),
                          "right_when_listed_second": _rate(second, lambda r: r["outcome"] == "right"),
                          "n_first": len(first), "n_second": len(second)}

    def iv(d):
        return "n/a" if not d else f"{d['mean']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}]" + \
            (f"  sign-flip p = {d['p']:.4f}" if "p" in d else "") + f"  (k = {d['k']} templates)"
    print(f"  C0 right: {gate:.3f}   C2 follows the planted figure: {out['P63.1']['c2_planted']:.3f}   "
          f"C1 follows it: {out['P63.2_c1_rate']:.3f}")
    print(f"  C2 minus C1 (planted figure followed): {iv(out['P63.2'])}")
    print(f"  C2 minus C3 (planted figure followed): {iv(out['P63.3'])}")
    print(f"  C3 share right among runs giving either answer: {iv(out['P63.3_c3_right_share'])}")
    print(f"  C3+C4 reply mentions both figures: {iv(out['P63.4'])}")
    print(f"  C3 order: right when listed first {out['P63.5_order']['right_when_listed_first']:.3f} "
          f"(n={len(first)}), when listed second {out['P63.5_order']['right_when_listed_second']:.3f} (n={len(second)})")
    if verdicts:
        print("\n  VERDICT LINES (as registered; primary writer only)")
        if not out["P63.0"]["pass"]:
            print("  P63.0: FAILS — the clean layout is answered right in fewer than 0.90 of runs")
            for pid in ("P63.1", "P63.2", "P63.3", "P63.4"):
                print(f"  {pid}: NOT EVALUABLE — the clean-layout check failed")
        else:
            print("  P63.0: PASSES")
            p1 = out["P63.1"]["c2_planted"]
            print(f"  P63.1: {'SUPPORTED' if p1 >= 0.80 else 'FALSIFIED'} — sole-source figure followed at {p1:.3f} (bar 0.80)")
            for pid, d in (("P63.2", out["P63.2"]), ("P63.3", out["P63.3"])):
                ok = d and d["mean"] > 0 and d["p"] < 0.05
                print(f"  {pid}: {'SUPPORTED' if ok else 'FALSIFIED'} — difference {iv(d)}")
            d = out["P63.4"]
            if d:
                word = "SUPPORTED" if d["hi"] < 0.5 else "FALSIFIED" if d["lo"] > 0.5 else "NOT EVALUABLE"
                print(f"  P63.4: {word} — both figures mentioned {iv(d)} (expectation: below 0.5)")
    return out


def stage_measure() -> None:
    rows = runlog.read_jsonl(RUNS)
    print("=" * 78)
    print("CELL 63 — a wrong figure the editor could check")
    print("=" * 78)
    result = {}
    for writer in WRITERS:
        rw = [r for r in rows if r["writer"] == writer]
        if rw:
            result[writer] = measure_writer(rw, writer + (" (primary)" if writer == PRIMARY else " (repeat, reported beside)"),
                                            writer == PRIMARY)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "measured.json").write_text(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "items"
    if stage == "runs":
        stage_runs(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        {"items": stage_items, "smoke": stage_smoke, "measure": stage_measure}[stage]()
