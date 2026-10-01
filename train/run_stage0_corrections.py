"""Stage 0 corrections — re-analysis of stored results, no model calls.

Record: RUNBOOK_PAPER_HARDENING.md "BOARD REVIEW AND STAGE-0 CORRECTIONS
(2026-10-01)". Trigger: docs/BOARD_REVIEW_2026-10-01.md.

Nothing here is a new experiment and nothing here is registered as a test:
every number is a re-computation of saved judgments, flags and labels under
the rules adopted after the review —

  * one value (or one paired difference) per case or item, then a t-interval
    and an exact sign-flip test over those clusters;
  * every preference comparison on ALL pairs, with ties shown;
  * agreement between judges corrected for chance;
  * counts compared as shares when input and output differ in length;
  * conditional results shown beside the all-run result.

Run:  .venv/bin/python train/run_stage0_corrections.py
Writes bench/analysis/stage0/report.txt and corrected.json.
"""
from __future__ import annotations

import collections
import contextlib
import io
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst.smallcluster import (cluster_boot, holm, kappa, paired_diffs,  # noqa: E402
                              sign_flip_p, t_interval)
from gst.stats import bootstrap_ols                                    # noqa: E402

AN = ROOT / "bench" / "analysis"
RUNS = ROOT / "bench" / "runs"
OUT = AN / "stage0"
FAMS = ("modeled", "jurisd", "hedging")
J = ("gpt-oss:20b", "qwen2.5:7b-instruct")
RESULT: dict = {"note": "re-analysis of stored data; descriptive, not a registered test"}


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def head(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def fmt(iv) -> str:
    return f"{iv[0]:+.3f} [{iv[1]:+.3f}, {iv[2]:+.3f}]"


# ------------------------------------------------------------------ 1
def carriage() -> None:
    head("1. Caveat carriage (Cell 48), after the parse fix")
    m = json.loads((AN / "cell48" / "measured.json").read_text())
    c = m["carriage_counts"]
    print(f"  full caveat sentences found word-for-word in the editor's prose: "
          f"{c['bare']}/{c['n']} = {m['carriage'][1]:.3f}")
    print(f"  superseded figure (caveats cut to their first line): "
          f"{m['carriage_superseded_line_parse'][1]:.3f}")
    print("  appendix: 1.000 by construction")
    RESULT["cell48_carriage"] = {"prose_verbatim": m["carriage"][1], "n": c["n"], "k": c["bare"],
                                 "superseded": m["carriage_superseded_line_parse"][1]}


# ------------------------------------------------------------------ 2
def redundancy() -> None:
    head("2. Second source for a figure (Cells 47 and 59): item-level, 8 items")
    for name, rows in (("cell47", json.loads((AN / "cell47" / "measured.json").read_text())),
                       ("cell59", jl(RUNS / "cell59_subq.jsonl"))):
        out = {}
        for label, field, a, b in (("drop in the planted wrong value", "wrong", "bare", "planned"),
                                   ("rise in the second source's value", "clean", "planned", "bare")):
            ids, d = paired_diffs(rows, "item", "arm", a, b, lambda r, f=field: bool(r[f]))
            iv = t_interval(d)
            p = sign_flip_p(d)
            print(f"  {name}  {label:<34} {fmt(iv)}  sign-flip p = {p:.4f}  (k = {len(d)} items)")
            out[field] = {"mean": iv[0], "lo": iv[1], "hi": iv[2], "p": p, "k": len(d), "per_item": d}
        for arm in ("bare", "planned"):
            a_ = [r for r in rows if r["arm"] == arm]
            out[arm] = {"n": len(a_), "wrong": sum(bool(r["wrong"]) for r in a_),
                        "clean": sum(bool(r["clean"]) for r in a_)}
        print(f"          counts: one source {out['bare']['wrong']}/{out['bare']['n']} wrong; two sources "
              f"{out['planned']['wrong']}/{out['planned']['n']} wrong, {out['planned']['clean']}/"
              f"{out['planned']['n']} the other value")
        RESULT[name] = out


# ------------------------------------------------------------------ 3
def uptake() -> None:
    head("3. Reader model and an appended caveat (Cell 51): item-level, 11 items")
    items = {x["id"]: x for x in json.loads((AN / "cell51" / "frozen.json").read_text())}
    rows = jl(RUNS / "cell51_uptake.jsonl")
    RESULT["cell51"] = {}
    for reader in sorted({r["reader"] for r in rows}):
        rr = [dict(r, flip=r["answer"] == items[r["item"]]["flipped"]) for r in rows if r["reader"] == reader]
        kept = {r["item"] for r in rr if r["arm"] == "app-rel"}
        rr = [r for r in rr if r["item"] in kept]
        ids, d = paired_diffs(rr, "item", "arm", "app-rel", "app-irr", lambda r: r["flip"])
        iv, p = t_interval(d), sign_flip_p(d)
        print(f"  {reader:<22} relevant minus irrelevant appendix {fmt(iv)}  sign-flip p = {p:.4f}  (k = {len(d)})")
        RESULT["cell51"][reader] = {"mean": iv[0], "lo": iv[1], "hi": iv[2], "p": p, "k": len(d)}
    print("  scope: a model reader, an appendix of ONE sentence placed just before the question")


# ------------------------------------------------------------------ 4
def reconsult() -> None:
    head("4. Follow-up to a specialist (Cells 44 and 54): conditional and all-run")
    m44 = json.loads((AN / "cell44" / "measured.json").read_text())
    m54 = json.loads((AN / "cell54" / "measured.json").read_text())
    out = {}
    for name, m in (("cell44", m44), ("cell54", m54)):
        for arm in sorted({x["arm"] for x in m}):
            a = [x for x in m if x["arm"] == arm]
            named = [x for x in a if x["tension_named"]]
            c = collections.Counter(x["adopt"] for x in named)
            agreed = len(named) - c["DISAGREE"]
            allr = sum(x["adopt"] == "R" for x in a)
            out[f"{name}/{arm}"] = {"n": len(a), "named": len(named), "R": c["R"], "anti": c["ANTI"],
                                    "disagree": c["DISAGREE"], "R_all_runs": allr}
            print(f"  {name} {arm:<13} named {len(named):>2}/{len(a)}  R {c['R']:>2}  anti {c['ANTI']}  "
                  f"judges split {c['DISAGREE']}  | R/named {c['R']/len(named):.3f}  "
                  f"R/agreed {c['R']/agreed if agreed else float('nan'):.3f}  | R over all runs {allr}/{len(a)}")
    # item-level difference, informed (or live) minus control, on named runs with judges agreed-or-not
    for label, treat, ctrl in (("C44 informed - control", [x for x in m44 if x["arm"] == "informed"],
                                [x for x in m44 if x["arm"] == "control"]),
                               ("C54 live - C44 archived control", [x for x in m54 if x["arm"] == "live"],
                                [x for x in m44 if x["arm"] == "control"])):
        for scope, keep in (("named runs", lambda x: x["tension_named"]), ("all runs", lambda x: True)):
            rows = [dict(x, arm="T") for x in treat if keep(x)] + [dict(x, arm="C") for x in ctrl if keep(x)]
            ids, d = paired_diffs(rows, "item", "arm", "T", "C", lambda r: r["adopt"] == "R")
            if len(d) >= 2:
                iv, p = t_interval(d), sign_flip_p(d)
                print(f"  {label:<34} {scope:<10} {fmt(iv)}  sign-flip p = {p:.4f}  (k = {len(d)} items with both)")
                out[f"{label} / {scope}"] = {"mean": iv[0], "lo": iv[1], "hi": iv[2], "p": p, "k": len(d)}
    print("  note: the C54 comparison uses a control arm run six days earlier")
    RESULT["reconsult"] = out


# ------------------------------------------------------------------ 5
def seating() -> None:
    head("5. Screening test for specialists (Cell 55): the unit is the model, n = 10")
    rows = jl(RUNS / "cell55_seating.jsonl")
    verdicts = json.loads((AN / "cell55" / "gate_verdicts.json").read_text())
    table = []
    for label, v in verdicts.items():
        pipe = [r for r in rows if r["label"] == label and r["stage"] == "pipe"]
        table.append((label, v["gate_pass"], sum((r["chars"] or 0) < 800 for r in pipe), len(pipe)))
        print(f"  {label:<11} {'pass' if v['gate_pass'] else 'FAIL'}  short outputs in the pipeline {table[-1][2]}/{table[-1][3]}")
    n_fail = sum(1 for t in table if not t[1])
    n = len(table)
    import math
    p = 1 / math.comb(n, n_fail)
    print(f"  the {n_fail} screen-fail models are exactly the {n_fail} with the most short outputs; "
          f"under random labels that has probability 1/{math.comb(n, n_fail)} = {p:.3f}")
    print("  note: the screen and the outcome are the same thing (output under 800 characters) on different prompts")
    RESULT["cell55"] = {"models": n, "fail": n_fail, "p_exact": p}


# ------------------------------------------------------------------ 6
def _count(entry) -> tuple[int, int]:
    a, b = entry["judges"].get(J[0], {}), entry["judges"].get(J[1], {})
    pos = n = 0
    for i in range(entry["n"]):
        la, lb = a.get(str(i)), b.get(str(i))
        if la is None or lb is None:
            continue
        n += 1
        pos += any(la.get(f) and lb.get(f) for f in FAMS)
    return pos, n


def transport() -> None:
    head("6. Caveats in and out (Cells 30 and 46)")
    pts = json.loads((AN / "cell46" / "measured.json").read_text())
    old_cases = {p["case"] for p in pts if p.get("chars") is None}

    def slope(v):
        xs, ys = [p["s"] for p in v], [p["y"] for p in v]
        mx, my = st.mean(xs), st.mean(ys)
        den = sum((x - mx) ** 2 for x in xs)
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else None

    out = {"fits": {}}
    print(f"  {'writer':<13}{'scenarios':<10}{'n':>4}{'w':>8}   {'run-level interval':<22}{'case-level interval (9 cases)'}")
    for w in ("gpt-oss:20b", "phi4:14b"):
        for corp in ("old", "new"):
            v = [p for p in pts if p["writer"] == w and ((p["case"] in old_cases) == (corp == "old"))]
            f = bootstrap_ols([p["s"] for p in v], [p["y"] for p in v], draws=5000)
            by = collections.defaultdict(list)
            for p in v:
                by[p["case"]].append(p)
            lo, hi = cluster_boot(by, lambda s: slope([q for c in s for q in c]))
            print(f"  {w:<13}{corp:<10}{len(v):>4}{f.slope:>8.3f}   [{f.slope_ci[0]:+.3f}, {f.slope_ci[1]:+.3f}]"
                  f"      [{lo:+.3f}, {hi:+.3f}]")
            out["fits"][f"{w}/{corp}"] = {"n": len(v), "w": f.slope, "run_level": list(f.slope_ci),
                                          "case_level": [lo, hi], "excludes_zero": lo > 0}
    print("  the run-level column is what the paper's transport figure printed")

    lab = json.loads((AN / "cell46" / "labels.json").read_text())
    up = {k[4:]: _count(e) for k, e in lab.items() if k.startswith("UP::")}
    agg = collections.defaultdict(lambda: [0, 0, 0, 0])
    for k, e in lab.items():
        if k.startswith("OUT::"):
            var, writer, _ = k[5:].rsplit("__", 2)
            y, n_out = _count(e)
            s, n_up = up[var]
            a = agg[("new scenarios", writer)]
            a[0] += s; a[1] += n_up; a[2] += y; a[3] += n_out
    units = json.loads((AN / "c30c31" / "units.json").read_text())
    lab2 = json.loads((AN / "c30c31" / "labels.json").read_text())
    owner = [ui for ui, u in enumerate(units) for _ in u["sentences"]]
    cnt = collections.defaultdict(lambda: [0, 0])
    for off in sorted({int(k.split("|")[1]) for k in lab2}):
        a, b = lab2.get(f"{J[0]}|{off}"), lab2.get(f"{J[1]}|{off}")
        if not a or not b:
            continue
        for pos in range(1, 11):
            i = off + pos - 1
            if i >= len(owner):
                break
            la, lb = a.get(str(pos)), b.get(str(pos))
            if la and lb:
                c = cnt[owner[i]]
                c[1] += 1
                c[0] += any(la.get(f) and lb.get(f) for f in FAMS)
    upk = {tuple(u["key"][:2]): cnt[i] for i, u in enumerate(units) if u["kind"] == "upstream"}
    for i, u in enumerate(units):
        if u["kind"] == "output" and str(u["id"]).startswith("P::"):
            s, n_up = upk[tuple(u["key"][:2])]
            y, n_out = cnt[i]
            a = agg[("original scenarios", "both writers")]
            a[0] += s; a[1] += n_up; a[2] += y; a[3] += n_out
    print("\n  share of sentences that carry a caveat, specialists' text vs the editor's answer:")
    out["shares"] = {}
    for (corp, w), (s, n_up, y, n_out) in sorted(agg.items()):
        print(f"    {corp:<20}{w:<14} in {s}/{n_up} = {s/n_up:.3f}   out {y}/{n_out} = {y/n_out:.3f}   "
              f"answer length / input length {n_out/n_up:.3f}   caveat sentences out / in {y/s:.3f}")
        out["shares"][f"{corp}/{w}"] = {"in": s / n_up, "out": y / n_out, "length_ratio": n_out / n_up,
                                        "count_ratio": y / s}
    RESULT["transport"] = out


# ------------------------------------------------------------------ 7
def _pair_scores(cache: dict, prefix_keys, first_is):
    """Per pair: share of the two single-order judgments won by the first arm."""
    out = []
    for case, key in prefix_keys:
        f, r = cache.get(key + "|fwd"), cache.get(key + "|rev")
        if f is None or r is None:
            continue
        s = ((f == "A") + (r == "B")) / 2
        out.append((case, s, "win" if s == 1 else "loss" if s == 0 else "tie", f, r))
    return out


def preference() -> None:
    head("7. AI-judge preference on ALL pairs (Cells 43, 43-R, 48, 61)")
    sets = []
    c43 = json.loads((AN / "cell43" / "judgments.json").read_text())
    c43r = json.loads((AN / "cell43R" / "judgments.json").read_text())
    for judge, cache in (("gpt-oss:20b", c43), ("qwen3-vl:30b-a3b-instruct", c43r)):
        for comp, label in (("C1", "pipeline vs single answer"), ("C2", "phrase 'modeled at' vs none"),
                            ("C3", "phrase 'taken to be' vs none")):
            keys = sorted({k.rsplit("|", 1)[0] for k in cache if k.startswith(f"{judge}|{comp}|")})
            sets.append((f"C43 {label}", judge, cache, [(k.split("|")[2], k) for k in keys]))
    c48 = json.loads((AN / "cell48" / "judgments.json").read_text())
    keys = sorted({k.rsplit("|", 1)[0] for k in c48 if k.startswith("gpt-oss:20b|L4|")})
    sets.append(("C48 report with caveat section vs without", "gpt-oss:20b", c48, [(k.split("|")[2], k) for k in keys]))
    c61 = json.loads((AN / "cell61" / "judgments_full.json").read_text())
    for judge in ("gpt-oss:20b", "qwen3-vl:30b-a3b-instruct"):
        keys = sorted({k.rsplit("|", 1)[0] for k in c61 if k.startswith(judge + "|")})
        sets.append(("C61 rebuilt system vs old pipeline", judge, c61, [(k.split("|")[1], k) for k in keys]))
    out = {}
    print(f"  {'comparison':<44}{'judge':<12}{'win/loss/tie':>14}{'decided-only':>14}{'all pairs':>11}"
          f"   case-level all-pairs minus 0.5")
    for label, judge, cache, pk in sets:
        ps = _pair_scores(cache, pk, None)
        c = collections.Counter(x[2] for x in ps)
        dec = c["win"] + c["loss"]
        by = collections.defaultdict(list)
        for case, s, *_ in ps:
            by[case].append(s)
        d = [st.mean(v) - 0.5 for v in by.values()]
        iv, p = t_interval(d), sign_flip_p(d)
        first = collections.Counter(x for _, _, _, f, r in ps for x in (f, r))
        allp = st.mean(x[1] for x in ps)
        print(f"  {label:<44}{judge.split(':')[0]:<12}{c['win']:>5}/{c['loss']}/{c['tie']:<4}"
              f"{(c['win']/dec if dec else float('nan')):>12.3f}{allp:>11.3f}   {fmt(iv)}  p = {p:.4f}  (k = {len(d)})")
        out[f"{label} | {judge}"] = {"win": c["win"], "loss": c["loss"], "tie": c["tie"],
                                     "decided_only": c["win"] / dec if dec else None, "all_pairs": allp,
                                     "case_mean_minus_half": iv[0], "lo": iv[1], "hi": iv[2], "p": p,
                                     "k": len(d), "first_listed_chosen": first["A"] / sum(first.values())}
    print("  'all pairs' is the share of single judgments won by the first-named side; a tie counts half")
    RESULT["preference"] = out


# ------------------------------------------------------------------ 8
def instrument() -> None:
    head("8. Agreement between the two sentence judges, corrected for chance")
    def pairs_a(lab, fam):
        o = []
        for e in lab.values():
            ja, jb = e["judges"].get(J[0], {}), e["judges"].get(J[1], {})
            for i in ja:
                la, lb = ja.get(i), jb.get(i)
                if la is not None and lb is not None:
                    o.append((bool(la.get(fam)), bool(lb.get(fam))))
        return o

    def pairs_b(lab, fam):
        o = []
        for off in sorted({int(k.split("|")[1]) for k in lab}):
            a, b = lab.get(f"{J[0]}|{off}"), lab.get(f"{J[1]}|{off}")
            if a and b:
                for pos in a:
                    la, lb = a.get(pos), b.get(pos)
                    if la and lb:
                        o.append((bool(la.get(fam)), bool(lb.get(fam))))
        return o

    out = {}
    print(f"  {'saved answers':<24}{'kind of caveat':<16}{'n':>7}{'raw':>7}{'chance':>8}{'kappa':>7}{'overlap':>9}")
    for name, path, fn in (("Cell 41", AN / "cell41" / "labels.json", pairs_a),
                           ("Cell 46", AN / "cell46" / "labels.json", pairs_a),
                           ("Cell 30/31", AN / "c30c31" / "labels.json", pairs_b)):
        lab = json.loads(path.read_text())
        pooled = []
        for fam in FAMS:
            pr = fn(lab, fam)
            pooled += pr
            k = kappa(pr)
            print(f"  {name:<24}{fam:<16}{k['n']:>7}{k['raw']:>7.3f}{k['chance']:>8.3f}{k['kappa']:>7.3f}{k['overlap']:>9.3f}")
            out[f"{name}/{fam}"] = k
        k = kappa(pooled)
        print(f"  {name:<24}{'all three':<16}{k['n']:>7}{k['raw']:>7.3f}{k['chance']:>8.3f}{k['kappa']:>7.3f}{k['overlap']:>9.3f}")
        out[f"{name}/pooled"] = k
    lab = json.loads((AN / "cell41" / "labels.json").read_text())
    for arm, form in (("form-X", "modeled at"), ("form-Y", "taken to be")):
        n = both = 0
        for key, e in lab.items():
            if key.rsplit("__", 2)[1] != arm:
                continue
            for i, s in enumerate(e["sentences"]):
                if form in s.lower():
                    la, lb = e["judges"][J[0]].get(str(i)), e["judges"][J[1]].get(str(i))
                    if la is not None and lb is not None:
                        n += 1
                        both += bool(la.get("modeled")) and bool(lb.get("modeled"))
        print(f"  sentences containing the instructed phrase '{form}': both judges label them {both}/{n} = {both/n:.3f}")
        out[f"recall/{form}"] = {"n": n, "both": both}
    RESULT["instrument"] = out


# ------------------------------------------------------------------ 9
def phrase_swap() -> None:
    head("9. Phrase instruction (Cell 41): case-level, 18 scenarios")
    rows = json.loads((AN / "cell41" / "scored.json").read_text())
    out = {}
    for arm, own, resid in (("form-X", "has_X", "modeled_not_X"), ("form-Y", "has_Y", "modeled_not_Y")):
        for label, field in (("own phrase appears", own), ("caveats in other wording", resid)):
            ids, d = paired_diffs(rows, "case", "arm", arm, "control", lambda r, f=field: r[f])
            iv, p = t_interval(d), sign_flip_p(d)
            print(f"  {arm}  {label:<26} {fmt(iv)}  sign-flip p = {p:.4f}  (k = {len(d)})")
            out[f"{arm}/{field}"] = {"mean": iv[0], "lo": iv[1], "hi": iv[2], "p": p, "k": len(d)}
    RESULT["cell41"] = out


# ------------------------------------------------------------------ 10
def family() -> None:
    head("10. Five statements the corrected paper keeps, adjusted for being five (Holm)")
    r = RESULT
    pv = {
        "instructed phrase appears (C41, 'modeled at')": r["cell41"]["form-X/has_X"]["p"],
        "judge prefers the answer without the phrase (C43, 'modeled at', all pairs)":
            r["preference"]["C43 phrase 'modeled at' vs none | gpt-oss:20b"]["p"],
        "judge prefers the pipeline to a single answer (C43, all pairs)":
            r["preference"]["C43 pipeline vs single answer | gpt-oss:20b"]["p"],
        "a second source lowers use of the first source's figure (C47)": r["cell47"]["wrong"]["p"],
        "reader model acts on an appended sentence (C51)": r["cell51"]["gpt-oss:20b"]["p"],
    }
    adj = holm(pv)
    for k in pv:
        print(f"  {k:<78} p = {pv[k]:.4f}   Holm-adjusted {adj[k]:.4f}")
    print("  retrospective: these five were chosen after the results were known")
    RESULT["holm"] = {k: {"p": pv[k], "adjusted": adj[k]} for k in pv}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()

    class Tee:
        def write(self, s):
            sys.__stdout__.write(s)
            buf.write(s)

        def flush(self):
            sys.__stdout__.flush()

    with contextlib.redirect_stdout(Tee()):
        print("STAGE 0 CORRECTIONS — re-analysis of stored results (no model calls)")
        carriage()
        redundancy()
        uptake()
        reconsult()
        seating()
        transport()
        preference()
        instrument()
        phrase_swap()
        family()
    (OUT / "report.txt").write_text(buf.getvalue())
    (OUT / "corrected.json").write_text(json.dumps(RESULT, indent=1, default=float))
    print(f"\nwrote {OUT / 'report.txt'} and corrected.json")


if __name__ == "__main__":
    main()
