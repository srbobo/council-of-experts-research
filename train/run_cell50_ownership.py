"""Cell 50 — the ownership law.

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 50 PRE-REGISTRATION".
Items frozen in docs/CELL50_ITEMS.json before any elicitation.

The ownership map is elicited from the writer BEFORE any values exist,
frozen as a prediction, and tested on fresh quantities with counterbalanced
placement so any value effect cancels.

Run:  .venv/bin/python train/run_cell50_ownership.py own
      .venv/bin/python train/run_cell50_ownership.py prior
      .venv/bin/python train/run_cell50_ownership.py freeze
      .venv/bin/python train/run_cell50_ownership.py runs
      .venv/bin/python train/run_cell50_ownership.py measure
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
from train.run_cell47_redundancy import norm                   # noqa: E402
from train.run_cell49_arbitration import anchored_in, first_number  # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell50"
RUNS = ROOT / "bench" / "runs" / "cell50_ownership.jsonl"
SEATS_PATH = ROOT / "bench" / "analysis" / "cell41" / "seats.json"
ITEMS = json.loads((ROOT / "docs" / "CELL50_ITEMS.json").read_text())["items"]
WRITER = "gpt-oss:20b"
ROLES = ("healthcare", "legal", "finance")
PLACEMENTS = ("v1-owner", "v2-owner")
REPEATS = 5
K = 5
STABLE_MIN = 4

OWN_PROMPT = ("Three specialist analysts are consulted separately on the "
              "situation below: a healthcare analyst, a legal analyst, and "
              "a finance analyst. For the figure named, which ONE analyst "
              "would you rely on as the source? Reply with exactly one "
              "word: healthcare, legal, or finance.")

PRIOR_PROMPT = ("You are an analyst. For the situation below, state a "
                "single typical figure for {quantity}, expressed in "
                "{unit}. Reply with the figure alone on one line — no "
                "range, no explanation.")


def _fmt(v: float, vtype: str) -> str:
    if vtype == "millions":
        return f"${v:g} million"
    if vtype == "hours":
        return f"{int(round(v))} hours"
    if vtype == "days":
        return f"{int(round(v))} days"
    if vtype == "sites":
        return f"{int(round(v))} sites"
    return f"${int(round(v)):,}"


def _probes(v: float, vtype: str) -> list[str]:
    if vtype == "millions":
        return [f"{v:g} million", f"{v:g}m"]
    n = int(round(v))
    if vtype == "hours":
        return [f"{n} hour"]
    if vtype == "days":
        return [f"{n} day"]
    if vtype == "sites":
        return [f"{n} site", f"{n} pilot"]
    return [f"{n:,}", str(n)]


def stage_own() -> None:
    from examples.test_cases import get_case
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "ownership.json"
    done = json.loads(path.read_text()) if path.exists() else {}
    for it in ITEMS:
        key = str(it["id"])
        got = done.get(key, [])
        while len(got) < K:
            t = chat(WRITER, OWN_PROMPT,
                     f"Situation:\n{get_case(it['case']).prompt}\n\n"
                     f"Figure: {it['quantity']}",
                     temperature=0.8, max_tokens=1024)
            low = norm(t or "")
            hits = [r for r in ROLES if r in low]
            if len(hits) == 1:
                got.append(hits[0])
                done[key] = got
                path.write_text(json.dumps(done))
        from collections import Counter
        c = Counter(got)
        modal, k = c.most_common(1)[0]
        print(f"  item {it['id']}: {dict(c)}  -> owner={modal} "
              f"({'STABLE' if k >= STABLE_MIN else 'unstable'})", flush=True)
    print("ownership elicitation complete")


def stage_prior() -> None:
    from examples.test_cases import get_case
    path = OUT / "priors.json"
    done = json.loads(path.read_text()) if path.exists() else {}
    for it in ITEMS:
        key = str(it["id"])
        got = done.get(key, [])
        while len(got) < K:
            t = chat(WRITER, PRIOR_PROMPT.format(quantity=it["quantity"],
                                                 unit=it["unit"]),
                     f"Situation:\n{get_case(it['case']).prompt}",
                     temperature=0.8, max_tokens=1024)
            v = first_number(t or "")
            if v is not None:
                got.append(v)
                done[key] = got
                path.write_text(json.dumps(done))
        print(f"  item {it['id']}: elicited {got}", flush=True)
    print("value elicitation complete")


def stage_freeze() -> None:
    from collections import Counter
    from examples.test_cases import get_case
    own = json.loads((OUT / "ownership.json").read_text())
    priors = json.loads((OUT / "priors.json").read_text())
    seats = json.loads(SEATS_PATH.read_text())
    frozen, problems = [], []
    for it in ITEMS:
        c = Counter(own[str(it["id"])])
        owner, k = c.most_common(1)[0]
        stable = k >= STABLE_MIN
        foil = ROLES[(ROLES.index(owner) + 1) % 3]
        if not seats[it["case"]].get(owner) or not seats[it["case"]].get(foil):
            problems.append(f"item {it['id']}: missing seat text for "
                            f"{owner}/{foil}")
            continue
        vals = priors[str(it["id"])]
        if it["vtype"] == "millions":
            vals = [v / 1e6 if v > 10000 else v for v in vals]
        med = st.median(vals)
        hay = norm(get_case(it["case"]).prompt) + " " + " ".join(
            norm(seats[it["case"]].get(r, "")) for r in ROLES)

        def ambient(v):
            if any(anchored_in(norm(p), hay) for p in _probes(v, it["vtype"])):
                return True
            if it["vtype"] == "millions":
                return False
            digits = re.sub(r"\D", "", _probes(v, it["vtype"])[-1])
            return (len(digits) >= 3 and
                    digits in re.sub(r"\D", " ", hay).split())
        v1 = med
        if ambient(v1):
            for eps in (1.05, 0.95, 1.1, 0.9):
                if not ambient(med * eps):
                    v1 = med * eps
                    break
            else:
                problems.append(f"item {it['id']}: V1 ambient")
                continue
        for cand in (med * 2, med / 2):
            if not ambient(cand) and _fmt(cand, it["vtype"]) != _fmt(v1, it["vtype"]):
                v2 = cand
                break
        else:
            problems.append(f"item {it['id']}: both 2x and /2 ambient")
            continue
        frozen.append({**it, "owner": owner, "foil": foil, "stable": stable,
                       "own_votes": dict(c),
                       "v1": _fmt(v1, it["vtype"]), "v2": _fmt(v2, it["vtype"]),
                       "v1_probes": _probes(v1, it["vtype"]),
                       "v2_probes": _probes(v2, it["vtype"])})
    if problems:
        for p in problems:
            print("  " + p)
        raise SystemExit("FREEZE GUARDS FAILED")
    (OUT / "frozen.json").write_text(json.dumps(frozen, indent=1))
    for f in frozen:
        print(f"  item {f['id']}: owner={f['owner']}"
              f"{'' if f['stable'] else ' (UNSTABLE)'} foil={f['foil']}  "
              f"V1={f['v1']}  V2={f['v2']}")
    n_stable = sum(1 for f in frozen if f["stable"])
    print(f"frozen {len(frozen)}/8; stable items: {n_stable} "
          f"(P50.1 requires >= 4)")


def stage_runs() -> None:
    from examples.test_cases import get_case
    items = json.loads((OUT / "frozen.json").read_text())
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
    todo = [(it, p, r) for it in items for p in PLACEMENTS
            for r in range(REPEATS) if f"i{it['id']}__{p}__r{r}" not in done]
    print(f"cell50: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0, fails = time.time(), 0
    with RUNS.open("a") as fh:
        for k, (it, place, rep) in enumerate(todo):
            ov, fv = (it["v1"], it["v2"]) if place == "v1-owner" \
                else (it["v2"], it["v1"])
            parts = []
            for role in ROLES:
                base = seats[it["case"]].get(role, "")
                if not base:
                    continue
                add = ""
                if role == it["owner"]:
                    add = "\n\n" + it["stmt"].format(v=ov)
                elif role == it["foil"]:
                    add = "\n\n" + it["stmt"].format(v=fv)
                parts.append("--- SPECIALIST CONTRIBUTION ---\n"
                             + base.rstrip() + add)
            q = f"{get_case(it['case']).prompt}\n\n{it['ask_line']}"
            txt = None
            for attempt in range(3):
                txt = chat(WRITER, WRITER_PROMPT,
                           f"{chr(10).join(parts)}\n\nQuestion:\n{q}",
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
            op = it["v1_probes"] if place == "v1-owner" else it["v2_probes"]
            fp = it["v2_probes"] if place == "v1-owner" else it["v1_probes"]
            fh.write(json.dumps({
                "run_id": f"i{it['id']}__{place}__r{rep}", "item": it["id"],
                "place": place, "repeat": rep, "stable": it["stable"],
                "owner_val": any(anchored_in(norm(p), low) for p in op),
                "foil_val": any(anchored_in(norm(p), low) for p in fp),
                "chars": len(txt), "output": txt}, ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 8 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print("cell50 runs complete")


def stage_measure() -> None:
    import random
    rng = random.Random(0)
    rows = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    items = json.loads((OUT / "frozen.json").read_text())
    dec = [r for r in rows if r["owner_val"] != r["foil_val"]]

    def share(sel):
        byc = {}
        for r in dec:
            if sel(r):
                byc.setdefault(r["item"], []).append(r["owner_val"])
        pool = sorted(byc)
        d = [x for i in pool for x in byc[i]]
        if not d:
            return float("nan"), (float("nan"),) * 2, 0
        ds = []
        for _ in range(5000):
            s = [pool[rng.randrange(len(pool))] for _ in pool]
            w = [x for i in s for x in byc[i]]
            if w:
                ds.append(sum(w) / len(w))
        ds.sort()
        return (sum(d) / len(d),
                (ds[int(.025 * len(ds))], ds[int(.975 * len(ds))]), len(d))

    print("=" * 76)
    print("CELL 50 — the ownership law")
    print("=" * 76)
    print("P50.3 RAW TABLE (mandatory, before any verdict)")
    print(f"  {'place':<10}{'n':>4}{'owner-val':>11}{'foil-val':>10}"
          f"{'both':>6}{'NEITHER':>9}{'chars':>7}")
    for p in PLACEMENTS:
        v = [r for r in rows if r["place"] == p]
        o = sum(1 for r in v if r["owner_val"] and not r["foil_val"])
        f = sum(1 for r in v if r["foil_val"] and not r["owner_val"])
        b = sum(1 for r in v if r["owner_val"] and r["foil_val"])
        n = sum(1 for r in v if not r["owner_val"] and not r["foil_val"])
        print(f"  {p:<10}{len(v):>4}{o:>11}{f:>10}{b:>6}{n:>9}"
              f"{sum(r['chars'] for r in v)//max(len(v),1):>7}")
    print("  per-item owner-value adoption (decisive; v1-owner | v2-owner):")
    for it in items:
        parts = []
        for p in PLACEMENTS:
            v = [r for r in dec if r["item"] == it["id"] and r["place"] == p]
            parts.append(f"{sum(1 for r in v if r['owner_val'])}/{len(v)}")
        print(f"    item {it['id']} (owner={it['owner']}"
              f"{'' if it['stable'] else ', UNSTABLE'}): "
              f"{parts[0]} | {parts[1]}")

    print()
    print("P50.2 MAP STABILITY (mandatory)")
    n_stable = sum(1 for it in items if it["stable"])
    for it in items:
        print(f"  item {it['id']}: votes {it['own_votes']}")
    print(f"  stable items: {n_stable}/8 (P50.1 requires >= 4)")

    print()
    print("P50.1 THE OWNERSHIP LAW — predicted-owner-seat value adoption "
          "(chance 0.5)")
    if n_stable < 4:
        print("  NOT EVALUABLE BY CONSTRUCTION — fewer than 4 stable items")
        return
    pt, ci, n = share(lambda r: r["stable"])
    print(f"  stable items: share {pt:.3f}  CI [{ci[0]:.3f},{ci[1]:.3f}]  "
          f"decisive n={n}")
    if ci[0] > 0.5:
        print("  P50.1: SUPPORTED — the pre-elicited ownership map predicts "
              "arbitration; harness §3 upgrades to an operating rule")
    elif pt <= 0.5:
        print("  P50.1: FALSIFIED — the elicited map does not predict "
              "arbitration; Cell 49's 0.895 stays a descriptive artifact")
    else:
        print("  P50.1: NOT EVALUABLE at this power, as registered")
    pa, ca, na = share(lambda r: True)
    print(f"  all-items sensitivity: share {pa:.3f} "
          f"[{ca[0]:.3f},{ca[1]:.3f}]  n={na}")
    (OUT / "measured.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k != "output"} for r in rows], indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "own"
    {"own": stage_own, "prior": stage_prior, "freeze": stage_freeze,
     "runs": stage_runs, "measure": stage_measure}[stage]()
