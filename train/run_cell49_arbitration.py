"""Cell 49 — the arbitration mechanism (prior-plausibility vs domain-congruence).

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 49 PRE-REGISTRATION".
Quantities reuse Cell 47's frozen items; values come from the writer's own
elicited prior under the registered frozen rule.

Run:  .venv/bin/python train/run_cell49_arbitration.py prior
      .venv/bin/python train/run_cell49_arbitration.py freeze
      .venv/bin/python train/run_cell49_arbitration.py runs
      .venv/bin/python train/run_cell49_arbitration.py measure
"""
from __future__ import annotations

import json
import re
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                          # noqa: E402
from train.run_cell30_descaffold import WRITER_PROMPT          # noqa: E402
from train.run_cell47_redundancy import ITEMS as C47, norm     # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell49"
RUNS = ROOT / "bench" / "runs" / "cell49_arbitration.jsonl"
SEATS_PATH = ROOT / "bench" / "analysis" / "cell41" / "seats.json"
WRITER = "gpt-oss:20b"
ROLES = ("healthcare", "legal", "finance")
ARMS = ("congruent", "incongruent")
REPEATS = 5
PRIOR_K = 5

# Frozen per-item domain-congruence, with rationale (registered).
CONGRUENT = {0: "finance",     # subscription pricing
             1: "healthcare",  # pilot cohort sizing
             2: "finance",     # PBM rebate rate
             3: "finance",     # lease payment
             4: "finance",     # budget allocation
             5: "legal",       # liquidated-damages negotiation
             6: "finance",     # agency markup
             7: "legal"}       # processor/DPA migration window

PRIOR_PROMPT = ("You are an analyst. For the situation below, state a "
                "single typical figure for {quantity}. Reply with the "
                "figure alone on one line — no range, no explanation.")

AUTH_LEX = ("typical", "industry", "standard")


def anchored_in(probe_n: str, hay_n: str) -> bool:
    """Containment where a leading-digit probe may not continue a longer
    number: '$6m' must not match inside '1.6m'. Both args pre-normed."""
    start = 0
    while True:
        i = hay_n.find(probe_n, start)
        if i < 0:
            return False
        if not probe_n[0].isdigit():
            return True
        prev = hay_n[i - 1] if i > 0 else " "
        if not (prev.isdigit() or prev == "."):
            return True
        start = i + 1


def first_number(txt: str):
    t = norm(txt)
    m = re.search(r"(\d+(?:\.\d+)?)", t)
    return float(m.group(1)) if m else None


def stage_prior() -> None:
    from examples.test_cases import get_case
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "priors.json"
    done = json.loads(path.read_text()) if path.exists() else {}
    for it in C47:
        key = str(it["id"])
        got = done.get(key, [])
        while len(got) < PRIOR_K:
            t = chat(WRITER, PRIOR_PROMPT.format(quantity=it["quantity"]),
                     f"Situation:\n{get_case(it['case']).prompt}",
                     temperature=0.8, max_tokens=1024)
            v = first_number(t or "")
            if v is not None:
                got.append(v)
                done[key] = got
                path.write_text(json.dumps(done))
        print(f"  item {it['id']}: elicited {got}", flush=True)
    print("priors complete")


def _fmt(v: float, template: str) -> str:
    """Format a numeric value in the item's own value style."""
    if "%" in template:
        return f"{v:g}%"
    if "million" in template:
        return f"${v:g} million"
    if "week" in template:
        n = int(round(v))
        words = {4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
                 10: "ten", 12: "twelve", 14: "fourteen", 16: "sixteen"}
        return f"{words.get(n, str(n))} weeks"
    if "patient" in template:
        return f"{int(round(v))} patients"
    return f"${int(round(v)):,}"


def _probes(v: float, template: str) -> list[str]:
    if "%" in template:
        return [f"{v:g}%", f"{v:g} percent"]
    if "million" in template:
        return [f"{v:g} million", f"${v:g}m"]
    if "week" in template:
        n = int(round(v))
        words = {4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
                 10: "ten", 12: "twelve", 14: "fourteen", 16: "sixteen"}
        w = words.get(n, str(n))
        return [f"{w} week", f"{n} week"]
    if "patient" in template:
        n = int(round(v))
        return [f"{n} patient", f"cohort of {n}"]
    return [f"{int(round(v)):,}", str(int(round(v)))]


def stage_freeze() -> None:
    """Apply the REGISTERED value rule; guard against ambient collisions."""
    from examples.test_cases import get_case
    priors = json.loads((OUT / "priors.json").read_text())
    seats = json.loads(SEATS_PATH.read_text())
    frozen, problems = [], []
    for it in C47:
        vals = priors[str(it["id"])]
        tmpl = it["clean_value"]
        # Unit normalization: million-template items elicit mixed units
        # ("$3.5 million" parses as 3.5; "$3,500,000" as 3500000). Bring
        # raw-dollar answers into millions before taking the median.
        if "million" in tmpl:
            vals = [v / 1e6 if v > 10000 else v for v in vals]
        med = st.median(vals)
        hay = norm(get_case(it["case"]).prompt) + " " + " ".join(
            norm(seats[it["case"]].get(r, "")) for r in ROLES)

        def ambient(v):
            # Formatted-probe containment always applies. The bare digit-token
            # clause applies only to >=3-digit strings: for short values ("6",
            # "25") a lone matching digit exists somewhere in any long case
            # text, and flagging those made every candidate ambient. Residual
            # salience risk for short values is accepted and recorded (the
            # C47 item-6 salience caveat), since the SCORING probes remain
            # the formatted forms.
            if any(anchored_in(norm(p), hay) for p in _probes(v, tmpl)):
                return True
            if "%" in tmpl or "million" in tmpl:
                return False   # unit-bearing probes are self-disambiguating
            digits = re.sub(r"\D", "", _probes(v, tmpl)[-1])
            return (len(digits) >= 3 and
                    digits in re.sub(r"\D", " ", hay).split())
        plaus = med
        for cand in (med * 2, med / 2):
            if not ambient(cand):
                implaus = cand
                break
        else:
            problems.append(f"item {it['id']}: both 2x and /2 ambient")
            continue
        if ambient(plaus):
            # nudge the plausible value minimally off any ambient numeral
            for eps in (1.05, 0.95, 1.1, 0.9):
                if not ambient(med * eps):
                    plaus = med * eps
                    break
            else:
                problems.append(f"item {it['id']}: plausible value ambient")
                continue
        frozen.append({**{k: it[k] for k in ("id", "case", "seat_A", "seat_B",
                                             "quantity", "stmt", "ask_line")},
                       "congruent_seat": CONGRUENT[it["id"]],
                       "plaus_value": _fmt(plaus, tmpl),
                       "implaus_value": _fmt(implaus, tmpl),
                       "plaus_probes": _probes(plaus, tmpl),
                       "implaus_probes": _probes(implaus, tmpl),
                       "elicited": vals})
    if problems:
        for p in problems:
            print("  " + p)
        raise SystemExit("FREEZE GUARDS FAILED")
    for f in frozen:
        assert f["congruent_seat"] in (f["seat_A"], f["seat_B"]), f["id"]
    (OUT / "frozen_values.json").write_text(json.dumps(frozen, indent=1))
    for f in frozen:
        print(f"  item {f['id']}: plausible {f['plaus_value']}  "
              f"implausible {f['implaus_value']}  congruent={f['congruent_seat']}")
    print(f"frozen {len(frozen)}/8 under the registered rule")


def build(it, arm: str, seats) -> str:
    cong = it["congruent_seat"]
    other = it["seat_A"] if it["seat_B"] == cong else it["seat_B"]
    if arm == "congruent":
        place = {cong: it["plaus_value"], other: it["implaus_value"]}
    else:
        place = {cong: it["implaus_value"], other: it["plaus_value"]}
    parts = []
    for role in ROLES:
        base = seats[it["case"]].get(role, "")
        if not base:
            continue
        add = ""
        if role in place:
            add = "\n\n" + it["stmt"].format(v=place[role])
        parts.append("--- SPECIALIST CONTRIBUTION ---\n" + base.rstrip() + add)
    return "\n\n".join(parts)


def stage_runs() -> None:
    from examples.test_cases import get_case
    items = json.loads((OUT / "frozen_values.json").read_text())
    seats = json.loads(SEATS_PATH.read_text())
    t = chat(WRITER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED")
    done = set()
    if RUNS.exists():
        for l in RUNS.read_text().splitlines():
            if l.strip():
                done.add(json.loads(l)["run_id"])
    todo = [(it, a, r) for it in items for a in ARMS for r in range(REPEATS)
            if f"i{it['id']}__{a}__r{r}" not in done]
    print(f"cell49: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0, fails = time.time(), 0
    with RUNS.open("a") as fh:
        for k, (it, a, rep) in enumerate(todo):
            q = f"{get_case(it['case']).prompt}\n\n{it['ask_line']}"
            txt = None
            for attempt in range(3):
                txt = chat(WRITER, WRITER_PROMPT,
                           f"{build(it, a, seats)}\n\nQuestion:\n{q}",
                           temperature=0.6, max_tokens=8192)
                if txt and txt.strip():
                    break
                time.sleep(5 * (attempt + 1))
            if not txt or not txt.strip():
                fails += 1
                if fails >= 5:
                    raise SystemExit("ABORTING — backend down; resumable.")
                continue
            fails = 0
            low = norm(txt)
            adopted_sent = ""
            for s in txt.split("."):
                if any(anchored_in(norm(p), norm(s)) for p in
                       it["plaus_probes"] + it["implaus_probes"]):
                    adopted_sent = s
                    break
            fh.write(json.dumps({
                "run_id": f"i{it['id']}__{a}__r{rep}", "item": it["id"],
                "arm": a, "repeat": rep,
                "plaus": any(anchored_in(norm(p), low) for p in it["plaus_probes"]),
                "implaus": any(anchored_in(norm(p), low) for p in it["implaus_probes"]),
                "auth": any(w in norm(adopted_sent) for w in AUTH_LEX),
                "chars": len(txt), "output": txt}, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 8 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print("cell49 runs complete")


def stage_measure() -> None:
    import random
    rng = random.Random(0)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    items_ = sorted({r["item"] for r in rows})
    by = {}
    for r in rows:
        by.setdefault((r["item"], r["arm"]), []).append(r)

    def decisive(r):
        return r["plaus"] != r["implaus"]

    def plaus_share(pairsel):
        byc = {}
        for r in rows:
            if pairsel(r) and decisive(r):
                byc.setdefault(r["item"], []).append(r["plaus"])
        pool = sorted(byc)
        dec = [x for i in pool for x in byc[i]]
        if not dec:
            return float("nan"), (float("nan"),) * 2, 0
        ds = []
        for _ in range(5000):
            s = [pool[rng.randrange(len(pool))] for _ in pool]
            w = [x for i in s for x in byc[i]]
            if w:
                ds.append(sum(w) / len(w))
        ds.sort()
        return (sum(dec) / len(dec),
                (ds[int(.025 * len(ds))], ds[int(.975 * len(ds))]), len(dec))

    print("=" * 76)
    print("CELL 49 — arbitration: prior-plausibility vs domain-congruence")
    print("=" * 76)
    print("P49.3 RAW TABLE (mandatory, before any verdict)")
    print(f"  {'arm':<13}{'n':>4}{'plaus':>7}{'implaus':>9}{'both':>6}"
          f"{'NEITHER':>9}{'auth-lex':>10}{'chars':>7}")
    for a in ARMS:
        v = [r for r in rows if r["arm"] == a]
        if not v:
            continue
        p_ = sum(1 for r in v if r["plaus"] and not r["implaus"])
        i_ = sum(1 for r in v if r["implaus"] and not r["plaus"])
        b_ = sum(1 for r in v if r["plaus"] and r["implaus"])
        n_ = sum(1 for r in v if not r["plaus"] and not r["implaus"])
        au = sum(1 for r in v if r["auth"])
        print(f"  {a:<13}{len(v):>4}{p_:>7}{i_:>9}{b_:>6}{n_:>9}{au:>10}"
              f"{sum(r['chars'] for r in v)//len(v):>7}")
    print("  per-item plausible-adoption (congruent | incongruent, decisive only):")
    for i in items_:
        parts = []
        for a in ARMS:
            v = [r for r in by.get((i, a), []) if decisive(r)]
            parts.append(f"{sum(1 for r in v if r['plaus'])}/{len(v)}")
        print(f"    item {i}: {parts[0]} | {parts[1]}")

    print()
    print("P49.1 PRIOR ARBITRATION — pooled plausible share (chance 0.5)")
    pt, ci, n = plaus_share(lambda r: True)
    print(f"  share {pt:.3f}  CI [{ci[0]:.3f},{ci[1]:.3f}]  decisive n={n}  "
          f"(registered MDD ~0.68)")
    if ci[0] > 0.5:
        print("  P49.1: SUPPORTED — the writer arbitrates toward its own prior")
    elif pt <= 0.5:
        print("  P49.1: FALSIFIED — no prior arbitration (point at/below chance)")
    else:
        print("  P49.1: NOT EVALUABLE at this power, as registered")

    print()
    print("P49.2 DOMAIN AUTHORITY — plausible share, congruent vs incongruent")
    pc, cc, nc = plaus_share(lambda r: r["arm"] == "congruent")
    pi, cin, ni = plaus_share(lambda r: r["arm"] == "incongruent")
    byc = {}
    for r in rows:
        if decisive(r):
            byc.setdefault(r["item"], {}).setdefault(r["arm"], []).append(r["plaus"])
    pool = sorted(byc)
    ds = []
    for _ in range(5000):
        s = [pool[rng.randrange(len(pool))] for _ in pool]
        a1 = [x for i in s for x in byc[i].get("congruent", [])]
        a2 = [x for i in s for x in byc[i].get("incongruent", [])]
        if a1 and a2:
            ds.append(sum(a1) / len(a1) - sum(a2) / len(a2))
    ds.sort()
    dlo, dhi = (ds[int(.025 * len(ds))], ds[int(.975 * len(ds))]) if ds else (float("nan"),) * 2
    print(f"  congruent {pc:.3f} (n={nc})   incongruent {pi:.3f} (n={ni})   "
          f"diff CI [{dlo:+.3f},{dhi:+.3f}]  (registered MDD ~0.35)")
    if dlo > 0:
        print("  P49.2: SUPPORTED — placement in the domain-congruent seat adds adoption")
    elif dhi < 0:
        print("  P49.2: FALSIFIED-REVERSED — congruent placement REDUCES adoption")
    elif abs(pc - pi) < 0.05:
        print("  P49.2: point estimates near-equal; NOT EVALUABLE vs null "
              "indistinguishable at this power — reported as no detected "
              "placement effect")
    else:
        print("  P49.2: NOT EVALUABLE at this power, as registered")
    (OUT / "measured.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k != "output"} for r in rows], indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "prior"
    {"prior": stage_prior, "freeze": stage_freeze,
     "runs": stage_runs, "measure": stage_measure}[stage]()
