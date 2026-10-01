"""Board review 2026-10-01 — recomputation of the numbers the review relies on.

Every figure quoted in docs/BOARD_REVIEW_2026-10-01.md that is not copied from
the paper or the runbook is produced here from files already in the repo. No
model is called and nothing is written.

Run from the repo root:
    .venv/bin/python bench/analysis/board_review/checks.py
"""
from __future__ import annotations

import collections
import itertools
import json
import math
import random
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

AN = ROOT / "bench" / "analysis"
RUNS = ROOT / "bench" / "runs"
FAMS = ("modeled", "jurisd", "hedging")
T975 = {5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 11: 2.228}


def jl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def head(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def t_interval(diffs: list[float]) -> tuple[float, float]:
    k = len(diffs)
    se = st.stdev(diffs) / math.sqrt(k)
    return st.mean(diffs) - T975[k] * se, st.mean(diffs) + T975[k] * se


def sign_flip_p(diffs: list[float]) -> float:
    """Exact two-sided randomization test on cluster-level paired differences."""
    obs = abs(sum(diffs))
    hits = total = 0
    for signs in itertools.product((1, -1), repeat=len(diffs)):
        total += 1
        hits += abs(sum(s * d for s, d in zip(signs, diffs))) >= obs - 1e-12
    return hits / total


def cluster_boot(clusters: dict, stat, draws: int = 5000, seed: int = 0):
    rng = random.Random(seed)
    keys = sorted(clusters)
    vals = []
    for _ in range(draws):
        v = stat([clusters[keys[rng.randrange(len(keys))]] for _ in keys])
        if v is not None:
            vals.append(v)
    vals.sort()
    return vals[int(.025 * len(vals))], vals[int(.975 * len(vals)) - 1]


# --------------------------------------------------------------------------
def redundancy() -> None:
    head("1. Redundancy (Cells 47 and 59): item-level effects, 8 item clusters")
    for name, rows in (
            ("Cell 47 planted (analysis/cell47/measured.json)",
             json.loads((AN / "cell47" / "measured.json").read_text())),
            ("Cell 59 live chain (runs/cell59_subq.jsonl)",
             jl(RUNS / "cell59_subq.jsonl"))):
        print(name)
        for arm in ("bare", "planned"):
            a = [r for r in rows if r["arm"] == arm]
            print(f"  {arm:<8} n={len(a)}  corrupted adopted "
                  f"{sum(bool(r['wrong']) for r in a)/len(a):.3f}  clean adopted "
                  f"{sum(bool(r['clean']) for r in a)/len(a):.3f}")
        dw, dc = [], []
        for i in sorted({r["item"] for r in rows}):
            b = [r for r in rows if r["item"] == i and r["arm"] == "bare"]
            p = [r for r in rows if r["item"] == i and r["arm"] == "planned"]
            bw = sum(bool(r["wrong"]) for r in b) / len(b)
            pw = sum(bool(r["wrong"]) for r in p) / len(p)
            bc = sum(bool(r["clean"]) for r in b) / len(b)
            pc = sum(bool(r["clean"]) for r in p) / len(p)
            dw.append(bw - pw)
            dc.append(pc - bc)
            print(f"    item {i}: corrupted {bw:.1f} -> {pw:.1f}   clean {bc:.1f} -> {pc:.1f}")
        for label, d in (("corrupted-adoption drop", dw), ("clean-adoption rise", dc)):
            lo, hi = t_interval(d)
            print(f"  {label}: mean {st.mean(d):+.3f}  t-interval over items "
                  f"[{lo:+.3f}, {hi:+.3f}]  exact sign-flip p = {sign_flip_p(d):.4f}")
    flags = jl(RUNS / "cell47_redundancy.jsonl")
    print("  note: flags stored in runs/cell47_redundancy.jsonl give bare corrupted "
          f"{sum(r['wrong'] for r in flags if r['arm']=='bare')}/40 (scored before the "
          "matcher was repaired); the analysis file gives 36/40")


# --------------------------------------------------------------------------
def carriage() -> None:
    head("2. Caveat carriage (Cell 48): the 0.174 figure")
    import train.run_cell48_freight as c48
    cav = c48.old_case_caveats()
    cav.update({k: v for k, v in c48.new_case_caveats().items() if k not in cav})
    arts = json.loads((AN / "cell48" / "artifacts.json").read_text())

    def norm(t: str) -> str:
        return re.sub(r"\s+", " ", t.replace("*", "")).lower()

    n_all = sum(len(v) for v in cav.values())
    n_multi = sum(1 for v in cav.values() for s in v if "\n" in s.strip())
    print(f"caveat 'sentences' across {len(cav)} cases: {n_all}; "
          f"{n_multi} ({n_multi/n_all:.1%}) contain a line break")
    s_tot = s_hit = f_tot = f_hit = a_hit = 0
    first_lines = collections.Counter()
    for a in arts:
        prose, full_art = norm(a["bare"]), norm(a["freight"])
        for line in a["freight"][len(a["bare"]):].splitlines():
            if line.startswith("- "):           # the measure stage's own parse
                c = line[2:].strip()
                s_tot += 1
                if norm(c) in prose:
                    s_hit += 1
                    first_lines[c[:40]] += 1
        for c in cav[a["case"]]:                # the sentences the appendix was built from
            f_tot += 1
            f_hit += norm(c) in prose
            a_hit += norm(c) in full_art
    print(f"paper's method (caveats re-parsed line by line from the appendix): "
          f"{s_hit}/{s_tot} = {s_hit/s_tot:.3f}")
    print(f"  most common 'carried' items: {first_lines.most_common(5)}")
    print(f"full caveat sentences, same literal-containment rule: prose "
          f"{f_hit}/{f_tot} = {f_hit/f_tot:.3f}; appendix {a_hit}/{f_tot} = {a_hit/f_tot:.3f}")
    n = [a["n_caveats"] for a in arts]
    print(f"appendix size: median {st.median(n)} items, mean {st.mean(n):.1f}, max {max(n)}; "
          f"median appendix {st.median(a['app_chars'] for a in arts):.0f} chars vs prose "
          f"{st.median(len(a['bare']) for a in arts):.0f}")


# --------------------------------------------------------------------------
def _pairs_c46_style(lab: dict, judges, fam: str):
    out = []
    for e in lab.values():
        ja, jb = e["judges"].get(judges[0], {}), e["judges"].get(judges[1], {})
        for i in ja:
            la, lb = ja.get(i), jb.get(i)
            if la is None or lb is None:
                continue
            out.append((bool(la.get(fam)), bool(lb.get(fam))))
    return out


def _pairs_c30(lab: dict, judges, fam: str):
    out = []
    for off in sorted({int(k.split("|")[1]) for k in lab}):
        a, b = lab.get(f"{judges[0]}|{off}"), lab.get(f"{judges[1]}|{off}")
        if not a or not b:
            continue
        for pos in a:
            la, lb = a.get(pos), b.get(pos)
            if la and lb:
                out.append((bool(la.get(fam)), bool(lb.get(fam))))
    return out


def _kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pa, pb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    both, either = sum(a and b for a, b in pairs), sum(a or b for a, b in pairs)
    return n, po, pa, pb, pe, (po - pe) / (1 - pe), both / either


def judge_agreement() -> None:
    head("3. The two-judge sentence instrument: raw agreement vs chance-corrected")
    j = ("gpt-oss:20b", "qwen2.5:7b-instruct")
    sets = (
        ("Cell 41 phrase-swap outputs", json.loads((AN / "cell41" / "labels.json").read_text()), _pairs_c46_style),
        ("Cell 46 transport corpus", json.loads((AN / "cell46" / "labels.json").read_text()), _pairs_c46_style),
        ("Cell 30/31 corpus", json.loads((AN / "c30c31" / "labels.json").read_text()), _pairs_c30),
    )
    print(f"{'corpus':<30}{'construct':<9}{'n':>7}{'raw':>7}{'chance':>8}{'kappa':>7}"
          f"{'pos A':>7}{'pos B':>7}{'overlap':>9}")
    for name, lab, fn in sets:
        pooled = []
        for fam in FAMS:
            p = fn(lab, j, fam)
            pooled += p
            n, po, pa, pb, pe, k, ov = _kappa(p)
            print(f"{name:<30}{fam:<9}{n:>7}{po:>7.3f}{pe:>8.3f}{k:>7.3f}{pa:>7.3f}{pb:>7.3f}{ov:>9.3f}")
        n, po, pa, pb, pe, k, ov = _kappa(pooled)
        print(f"{name:<30}{'pooled':<9}{n:>7}{po:>7.3f}{pe:>8.3f}{k:>7.3f}{'':>14}{ov:>9.3f}")
    print("overlap = sentences both judges flag / sentences either judge flags")

    lab = sets[0][1]
    print("\nRecall on sentences that contain the instructed phrase (Cell 41):")
    for arm, form in (("form-X", "modeled at"), ("form-Y", "taken to be")):
        n = a = b = both = 0
        for key, e in lab.items():
            if key.rsplit("__", 2)[1] != arm:
                continue
            for i, s in enumerate(e["sentences"]):
                if form not in s.lower():
                    continue
                la, lb = e["judges"][j[0]].get(str(i)), e["judges"][j[1]].get(str(i))
                if la is None or lb is None:
                    continue
                n += 1
                x, y = bool(la.get("modeled")), bool(lb.get("modeled"))
                a, b, both = a + x, b + y, both + (x and y)
        print(f"  '{form}': {n} judged sentences; labelled 'modeled' by gpt-oss {a/n:.3f}, "
              f"by qwen2.5 {b/n:.3f}, by both (the instrument) {both/n:.3f}")


# --------------------------------------------------------------------------
def _count(entry, judges) -> tuple[int, int]:
    a, b = entry["judges"].get(judges[0], {}), entry["judges"].get(judges[1], {})
    pos = n = 0
    for i in range(entry["n"]):
        la, lb = a.get(str(i)), b.get(str(i))
        if la is None or lb is None:
            continue
        n += 1
        pos += any(la.get(f) and lb.get(f) for f in FAMS)
    return pos, n


def transport() -> None:
    head("4. Transport (Cells 30/46): intervals and what the slope measures")
    from gst.stats import bootstrap_ols
    pts = json.loads((AN / "cell46" / "measured.json").read_text())
    old_cases = {p["case"] for p in pts if p.get("chars") is None}

    def slope(v):
        xs, ys = [p["s"] for p in v], [p["y"] for p in v]
        mx, my = st.mean(xs), st.mean(ys)
        den = sum((x - mx) ** 2 for x in xs)
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else None

    print(f"{'writer':<13}{'corpus':<8}{'n':>4}{'slope':>8}   {'run-level bootstrap':<22}{'case-clustered bootstrap'}")
    for w in ("gpt-oss:20b", "phi4:14b"):
        for corp in ("old", "new"):
            v = [p for p in pts if p["writer"] == w and ((p["case"] in old_cases) == (corp == "old"))]
            f = bootstrap_ols([p["s"] for p in v], [p["y"] for p in v], draws=5000)
            by = collections.defaultdict(list)
            for p in v:
                by[p["case"]].append(p)
            lo, hi = cluster_boot(by, lambda s: slope([q for c in s for q in c]))
            print(f"{w:<13}{corp:<8}{len(v):>4}{f.slope:>8.3f}   "
                  f"[{f.slope_ci[0]:+.3f}, {f.slope_ci[1]:+.3f}]      [{lo:+.3f}, {hi:+.3f}]")
    print("(the run-level column reproduces the intervals printed in the paper's Figure 5)")

    j = ("gpt-oss:20b", "qwen2.5:7b-instruct")
    lab = json.loads((AN / "cell46" / "labels.json").read_text())
    up = {k[4:]: _count(e, j) for k, e in lab.items() if k.startswith("UP::")}
    agg = collections.defaultdict(lambda: [0, 0, 0, 0])
    for k, e in lab.items():
        if not k.startswith("OUT::"):
            continue
        var, writer, _ = k[5:].rsplit("__", 2)
        y, n_out = _count(e, j)
        s, n_up = up[var]
        a = agg[("extension", writer)]
        a[0] += s; a[1] += n_up; a[2] += y; a[3] += n_out
    # original corpus, Cell 30 plain-writer arm
    units = json.loads((AN / "c30c31" / "units.json").read_text())
    lab2 = json.loads((AN / "c30c31" / "labels.json").read_text())
    flat_owner = [ui for ui, u in enumerate(units) for _ in u["sentences"]]
    cnt = collections.defaultdict(lambda: [0, 0])
    for off in sorted({int(k.split("|")[1]) for k in lab2}):
        a, b = lab2.get(f"{j[0]}|{off}"), lab2.get(f"{j[1]}|{off}")
        if not a or not b:
            continue
        for pos in range(1, 11):
            i = off + pos - 1
            if i >= len(flat_owner):
                break
            la, lb = a.get(str(pos)), b.get(str(pos))
            if la and lb:
                c = cnt[flat_owner[i]]
                c[1] += 1
                c[0] += any(la.get(f) and lb.get(f) for f in FAMS)
    upk = {tuple(u["key"][:2]): cnt[i] for i, u in enumerate(units) if u["kind"] == "upstream"}
    for i, u in enumerate(units):
        if u["kind"] == "output" and str(u["id"]).startswith("P::"):
            s, n_up = upk[tuple(u["key"][:2])]
            y, n_out = cnt[i]
            a = agg[("original", "both writers")]
            a[0] += s; a[1] += n_up; a[2] += y; a[3] += n_out
    print("\nShare of judged sentences that carry a qualification, inputs vs outputs:")
    for (corp, w), (s, n_up, y, n_out) in sorted(agg.items()):
        print(f"  {corp:<10}{w:<14} inputs {s}/{n_up} = {s/n_up:.3f}   outputs {y}/{n_out} = {y/n_out:.3f}"
              f"   output length / input length = {n_out/n_up:.3f}   qualified out / in = {y/s:.3f}")


# --------------------------------------------------------------------------
def preference() -> None:
    head("5. Preference (Cells 43 and 61): decisive-only share vs all pairs")
    m = json.loads((AN / "cell43" / "measured.json").read_text())
    names = {"C1": "aggregated vs direct", "C2": "form X vs control", "C3": "form Y vs control"}
    for comp, rows in m.items():
        c = collections.Counter(r["verdict"] for r in rows)
        dec = c["S1"] + c["S2"]
        print(f"  Cell 43 {names[comp]:<22} wins {c['S1']:>2}, losses {c['S2']:>2}, ties {len(rows)-dec:>2}"
              f" of {len(rows)}: decisive-only share {c['S1']/dec:.3f}; counting ties as half {(c['S1']+0.5*(len(rows)-dec))/len(rows):.3f}")
    jd = json.loads((AN / "cell61" / "judgments_full.json").read_text())
    pairs = collections.defaultdict(dict)
    for k, v in jd.items():
        judge, case, hr, orr, order = k.split("|")
        pairs[(judge, case, hr, orr)][order] = v
    for judge in sorted({k[0] for k in pairs}):
        res = collections.Counter()
        by = collections.defaultdict(list)
        first = collections.Counter()
        for (jg, case, _, _), d in pairs.items():
            if jg != judge:
                continue
            f, r = d.get("fwd"), d.get("rev")
            first.update(x for x in (f, r) if x in ("A", "B"))
            if f == "A" and r == "B":
                res["harness"] += 1; by[case].append(1)
            elif f == "B" and r == "A":
                res["old"] += 1; by[case].append(0)
            else:
                res["tie"] += 1
        dec = res["harness"] + res["old"]
        lo, hi = cluster_boot(by, lambda s: (lambda a: sum(a) / len(a) if a else None)([v for c in s for v in c]))
        tot = sum(res.values())
        print(f"  Cell 61 judge {judge:<26} harness {res['harness']}, old {res['old']}, ties {res['tie']}: "
              f"share {res['harness']/dec:.3f} [{lo:.3f}, {hi:.3f}] over {len(by)} cases with a decisive pair; "
              f"ties as half {(res['harness']+0.5*res['tie'])/tot:.3f}; first-position rate {first['A']/sum(first.values()):.3f}")


# --------------------------------------------------------------------------
def reconsult() -> None:
    head("6. Re-consultation (Cells 44 and 54): conditional vs all-run adoption")
    for name, path in (("Cell 44", AN / "cell44" / "measured.json"), ("Cell 54", AN / "cell54" / "measured.json")):
        m = json.loads(path.read_text())
        for arm in sorted({x["arm"] for x in m}):
            a = [x for x in m if x["arm"] == arm]
            named = [x for x in a if x["tension_named"]]
            c = collections.Counter(x["adopt"] for x in named)
            agreed = len(named) - c["DISAGREE"]
            allr = sum(x["adopt"] == "R" for x in a)
            print(f"  {name} {arm:<13} tension named {len(named):>2}/{len(a)}; among named: R {c['R']}, "
                  f"anti-R {c['ANTI']}, judges disagree {c['DISAGREE']} -> R/named {c['R']/len(named):.3f}, "
                  f"R/agreed {c['R']/agreed:.3f}; R over all runs {allr}/{len(a)} = {allr/len(a):.3f}")


# --------------------------------------------------------------------------
def registration_order() -> None:
    head("7. Version history: registration, verdict, and first commit of the run records")

    def first(args: list[str]) -> str:
        out = subprocess.run(["git", "-C", str(ROOT), "log", "--reverse", "--format=%h %ad",
                              "--date=format:%m-%d %H:%M", *args], capture_output=True, text=True).stdout
        return out.splitlines()[0] if out.strip() else "-"

    rows = (("41", "## CELL 41 PRE-REGISTRATION", "## CELL 41 VERDICT", "bench/runs/cell41_phraseswap.jsonl"),
            ("43", "## CELL 43 PRE-REGISTRATION", "## CELL 43 VERDICT", "bench/runs/cell43_direct.jsonl"),
            ("44", "## CELL 44 PRE-REGISTRATION", "## CELL 44 VERDICT", "bench/runs/cell44_reconsult.jsonl"),
            ("47", "## CELL 47 (L2) PRE-REGISTRATION", "## CELL 47 (L2) VERDICT", "bench/runs/cell47_redundancy.jsonl"),
            ("51", "## CELL 51 PRE-REGISTRATION", "## CELL 51 VERDICT", "bench/runs/cell51_uptake.jsonl"),
            ("54", "## CELL 54 PRE-REGISTRATION", "## CELL 54 VERDICT", "bench/runs/cell54_briefed.jsonl"),
            ("55", "## CELL 55 PRE-REGISTRATION", "## CELL 55 VERDICT", "bench/runs/cell55_seating.jsonl"),
            ("59", "## CELL 59 PRE-REGISTRATION", "## CELL 59 VERDICT", "bench/runs/cell59_subq.jsonl"))
    print(f"{'cell':<6}{'registration committed':<24}{'verdict committed':<22}{'run records first committed'}")
    for cell, reg, ver, path in rows:
        print(f"{cell:<6}{first(['-S' + reg, '--', 'RUNBOOK_PAPER_HARDENING.md']):<24}"
              f"{first(['-S' + ver, '--', 'RUNBOOK_PAPER_HARDENING.md']):<22}"
              f"{first(['--diff-filter=A', '--', path])}")


# --------------------------------------------------------------------------
def validation_sample() -> None:
    head("8. Where the sentence instrument was validated (Cell 23)")
    d = json.loads((AN / "cell23" / "judged.json").read_text())
    fam4 = ("cutoff",) + FAMS
    j = ("gpt-oss:20b", "qwen2.5:7b-instruct")
    anchors = [x for x in d if x["stratum"] == "ANCHOR"]
    sample = [x for x in d if x["stratum"] != "ANCHOR"]
    n_pos = sum(len(x["truth"]) for x in anchors)
    n_all = len(anchors) * len(fam4)
    print(f"anchors: {len(anchors)} sentences, {n_all} decisions, {n_pos} positives; "
          f"a judge answering 'no' throughout scores {(n_all-n_pos)/n_all:.3f}")
    for judge in j:
        tp = sum(bool(x["judges"][judge].get(f)) for x in anchors for f in x["truth"])
        tn = sum(not x["judges"][judge].get(f) for x in anchors for f in fam4 if f not in x["truth"])
        print(f"  {judge:<22} accuracy {(tp+tn)/n_all:.3f}; positives recognised {tp}/{n_pos}; "
              f"negatives correct {tn}/{n_all-n_pos}")
    for fam in FAMS:
        pairs = [(bool(x["judges"][j[0]].get(fam)), bool(x["judges"][j[1]].get(fam))) for x in sample]
        n, po, pa, pb, pe, k, _ = _kappa(pairs)
        print(f"  validation sample {fam:<8} n={n} positive rates {pa:.2f}/{pb:.2f} raw {po:.3f} kappa {k:.3f}")


# --------------------------------------------------------------------------
def uptake() -> None:
    head("9. Reader uptake (Cell 51)")
    items = {x["id"]: x for x in json.loads((AN / "cell51" / "frozen.json").read_text())}
    rows = jl(RUNS / "cell51_uptake.jsonl")
    print(f"authored caveat mean {st.mean(len(x['caveat']) for x in items.values()):.0f} chars; "
          f"irrelevant control mean {st.mean(len(x['irrelevant']) for x in items.values()):.0f} chars")
    for reader in sorted({r["reader"] for r in rows}):
        rr = [r for r in rows if r["reader"] == reader]
        kept = sorted({r["item"] for r in rr if r["arm"] == "app-rel"})

        def rate(arm, ids):
            a = [r for r in rr if r["arm"] == arm and r["item"] in ids]
            return sum(r["answer"] == items[r["item"]]["flipped"] for r in a) / len(a)

        d = [rate("app-rel", [i]) - rate("app-irr", [i]) for i in kept]
        lo, hi = t_interval(d)
        print(f"  {reader:<22} items {len(kept)}: bare {rate('bare', kept):.3f}, irrelevant appendix "
              f"{rate('app-irr', kept):.3f}, relevant appendix {rate('app-rel', kept):.3f}, relevant prose "
              f"{rate('prose-rel', kept):.3f}; uptake {st.mean(d):+.3f} t-interval [{lo:+.3f}, {hi:+.3f}] "
              f"sign-flip p = {sign_flip_p(d):.4f}")
    dropped = sorted(set(items) - set(kept))
    print(f"  items removed at the pilot gate: {dropped} "
          f"({collections.Counter(items[i]['direction'] for i in dropped)})")


# --------------------------------------------------------------------------
def seating_gate() -> None:
    head("10. Seating gate (Cell 55): the predictor and the outcome are both output length")
    rows = jl(RUNS / "cell55_seating.jsonl")
    verdicts = json.loads((AN / "cell55" / "gate_verdicts.json").read_text())
    for label, v in verdicts.items():
        screen = [r for r in rows if r["label"] == label and r["stage"] == "screen"]
        pipe = [r for r in rows if r["label"] == label and r["stage"] == "pipe"]
        print(f"  {label:<11} gate {'pass' if v['gate_pass'] else 'FAIL'}: screen runs under 800 chars "
              f"{sum((r['chars'] or 0) < 800 for r in screen)}/{len(screen)}; pipeline runs under 800 chars "
              f"{sum((r['chars'] or 0) < 800 for r in pipe)}/{len(pipe)}")


# --------------------------------------------------------------------------
def sizing() -> None:
    head("11. Sizing sketch for a future corruption cell (resampling Cell 47's item effects)")
    rng = random.Random(1)
    rows = json.loads((AN / "cell47" / "measured.json").read_text())
    pop = []
    for i in sorted({r["item"] for r in rows}):
        b = [r["wrong"] for r in rows if r["item"] == i and r["arm"] == "bare"]
        p = [r["wrong"] for r in rows if r["item"] == i and r["arm"] == "planned"]
        # shrink observed rates slightly away from 0 and 1
        pop.append(((sum(b) + 0.5) / (len(b) + 1), (sum(p) + 0.5) / (len(p) + 1)))
    tcrit = {8: 2.365, 20: 2.093, 40: 2.023}
    print(f"{'items':>6}{'repeats':>9}  {'true effect':<24}{'power':>7}{'95% half-width':>16}")
    for shrink, label in ((1.0, "as observed"), (0.5, "half the observed")):
        for k, reps in ((8, 5), (20, 3), (40, 3)):
            hits, widths = 0, []
            for _ in range(4000):
                d = []
                for _ in range(k):
                    pb, pp = pop[rng.randrange(len(pop))]
                    pp = pb - (pb - pp) * shrink
                    d.append(sum(rng.random() < pb for _ in range(reps)) / reps
                             - sum(rng.random() < pp for _ in range(reps)) / reps)
                sd = st.stdev(d) or 1e-9
                se = sd / math.sqrt(k)
                hits += abs(st.mean(d) / se) > tcrit[k]
                widths.append(tcrit[k] * se)
            print(f"{k:>6}{reps:>9}  {label:<24}{hits/4000:>7.2f}{st.mean(widths):>16.3f}")


# --------------------------------------------------------------------------
def overlap_illustration() -> None:
    head("12. Illustration only: content-word overlap between caveats and prose (Cell 48)")
    import train.run_cell48_freight as c48
    cav = c48.old_case_caveats()
    cav.update({k: v for k, v in c48.new_case_caveats().items() if k not in cav})
    arts = json.loads((AN / "cell48" / "artifacts.json").read_text())
    stop = set("a an the of to in on for and or but with by as at from is are was were be been being this "
               "that these those it its their there which who whom what when where how if then than so such "
               "not no nor can could may might must shall should will would do does did has have had into "
               "over under about above below between per via any all each more most less least very also "
               "only both either neither one two three".split())

    def toks(s: str) -> set[str]:
        return {w.strip(".,") for w in re.findall(r"[a-z0-9$%.,]+", s.lower())
                if len(w.strip(".,")) > 1 and w.strip(".,") not in stop}

    tot = 0
    hit = {0.5: 0, 0.6: 0, 0.8: 0}
    for a in arts:
        prose = [toks(s) for s in re.split(r"(?<=[.!?])\s+|\n+", a["bare"]) if len(s.strip()) > 20]
        for c in cav[a["case"]]:
            ct = toks(c)
            if len(ct) < 4:
                continue
            tot += 1
            best = max((len(ct & p) / len(ct) for p in prose), default=0)
            for th in hit:
                hit[th] += best >= th
    for th, n in hit.items():
        print(f"  some prose sentence shares >= {th:.0%} of the caveat's content words: {n/tot:.3f} (of {tot})")
    print("  (not a validated measure of whether a caveat was conveyed)")


# --------------------------------------------------------------------------
def verdict_tally() -> None:
    head("13. Rough tally of first-recorded verdicts per registered prediction (runbook)")
    text = (ROOT / "RUNBOOK_PAPER_HARDENING.md").read_text()
    pat = re.compile(r"\*\*\s*((?:P|PA|PD|L)[0-9A-Za-z]*[.\-][0-9a-zA-Z.]+)[^*\n]{0,60}?"
                     r"(NOT EVALUABLE|NOT REPLICATED|SUPPORTED|CONFIRMED|FALSIFIED|PARTIAL|MOOT|"
                     r"WITHDRAWN|INDETERMINATE|PASS|FAIL)", re.S)
    seen, tally = set(), collections.Counter()
    for sec in re.split(r"\n(?=#{2,3} )", text):
        if "VERDICT" not in sec.split("\n", 1)[0].upper():
            continue
        for m in pat.finditer(sec):
            pid = m.group(1).rstrip(".")
            if pid not in seen:
                seen.add(pid)
                tally[m.group(2)] += 1
    print(f"  {len(seen)} prediction ids matched (approximate; the pattern misses some formats)")
    print("  " + ", ".join(f"{k} {v}" for k, v in tally.most_common()))
    n_reg = len(re.findall(r"^#+ .*(?:PRE-REGISTRATION|EXECUTION REGISTRATION)", text, re.M))
    print(f"  registration headings in the runbook: {n_reg}")


if __name__ == "__main__":
    redundancy()
    carriage()
    judge_agreement()
    transport()
    preference()
    reconsult()
    registration_order()
    validation_sample()
    uptake()
    seating_gate()
    sizing()
    overlap_illustration()
    verdict_tally()
