"""PD-13 — is the clause effect compliance or behavior change?

Registered in RUNBOOK_PAPER_HARDENING.md ("REGISTERED RE-ANALYSIS PD-13")
before computation. Zero model calls.

A lexicon pattern is DICTATED iff it matches the text of
council/prompts.py — an objective mechanical split. If a clause's effect
is concentrated in the dictated patterns, it is compliance with a phrase
instruction; if it is spread across a family's other phrasings, it is
behavior change.

Run:  .venv/bin/python train/run_pd13_patterns.py
"""
from __future__ import annotations

import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst.adapters.coe import from_ledger        # noqa: E402
from gst.instruments import EPISTEMIC_QUALIFICATION  # noqa: E402

SEED = 0
DRAWS = 5000
FLOOR_EVENTS = 5
rng = random.Random(SEED)

# Which clause names which family (Cell 13's design).
CLAUSE_FAMILY = {"c13-c1": None,          # tension acknowledgement: no family
                 "c13-c2": "modeled",     # numeric framing
                 "c13-c3": None,          # vocabulary precision (family below detection)
                 "c13-c4": "cutoff"}      # caveats / recency


def split_patterns() -> dict[str, dict[str, list[str]]]:
    """DICTATED iff the pattern matches the prompt source text."""
    prompts = (ROOT / "council" / "prompts.py").read_text()
    out: dict[str, dict[str, list[str]]] = {}
    for fam, pats in EPISTEMIC_QUALIFICATION.items():
        d, n = [], []
        for p in pats:
            (d if re.search(p, prompts, re.I) else n).append(p)
        out[fam] = {"dictated": d, "non_dictated": n}
    return out


def present(text: str, pats: list[str]) -> int:
    return int(any(re.search(p, text, re.I) for p in pats))


def boot_did(a_d, a_n, b_d, b_n) -> tuple[float, float]:
    """CI on (arm_dictated - base_dictated) - (arm_nondict - base_nondict)."""
    vals = []
    for _ in range(DRAWS):
        ad = sum(rng.choice(a_d) for _ in a_d) / len(a_d)
        an = sum(rng.choice(a_n) for _ in a_n) / len(a_n)
        bd = sum(rng.choice(b_d) for _ in b_d) / len(b_d)
        bn = sum(rng.choice(b_n) for _ in b_n) / len(b_n)
        vals.append((ad - bd) - (an - bn))
    vals.sort()
    return vals[int(0.025 * DRAWS)], vals[int(0.975 * DRAWS)]


def main() -> None:
    split = split_patterns()
    print("=" * 76)
    print("PATTERN SPLIT — dictated iff the pattern matches council/prompts.py")
    print("=" * 76)
    for fam, s in split.items():
        print(f"  {fam}:")
        print(f"    DICTATED     ({len(s['dictated'])}): {s['dictated']}")
        print(f"    non-dictated ({len(s['non_dictated'])}): {s['non_dictated']}")
    print()

    recs = [r for r in from_ledger(ROOT / "bench/runs/imported")
            if r.condition.startswith("c13-") and len(r.output) >= 500]
    arms: dict[str, list] = {}
    for r in recs:
        arms.setdefault(r.condition, []).append(r)
    print(f"Cell 13 arms: {{k: len(v) for k, v in ...}} -> "
          f"{ {k: len(v) for k, v in sorted(arms.items())} }")
    base = arms.get("c13-none", [])
    if not base:
        print("no baseline arm — stop")
        return

    print()
    print("=" * 76)
    print("PD13.1 — clause lift on DICTATED vs NON-DICTATED phrasings")
    print("=" * 76)
    any_scored = False
    for arm, fam in CLAUSE_FAMILY.items():
        if arm not in arms:
            continue
        if fam is None:
            print(f"{arm}: names no detectable family — skipped by design")
            continue
        s = split[fam]
        if not s["non_dictated"] or not s["dictated"]:
            print(f"{arm} ({fam}): NOT EVALUABLE — family has no "
                  f"{'non-dictated' if not s['non_dictated'] else 'dictated'} patterns")
            continue
        a_d = [present(r.output, s["dictated"]) for r in arms[arm]]
        a_n = [present(r.output, s["non_dictated"]) for r in arms[arm]]
        b_d = [present(r.output, s["dictated"]) for r in base]
        b_n = [present(r.output, s["non_dictated"]) for r in base]
        events_nd = sum(a_n) + sum(b_n)
        lift_d = sum(a_d) / len(a_d) - sum(b_d) / len(b_d)
        lift_n = sum(a_n) / len(a_n) - sum(b_n) / len(b_n)
        print(f"\n{arm}  (clause names '{fam}')   n_arm={len(a_d)} n_base={len(b_d)}")
        print(f"  DICTATED     : {sum(b_d)}/{len(b_d)} -> {sum(a_d)}/{len(a_d)}"
              f"   lift {lift_d:+.3f}")
        print(f"  non-dictated : {sum(b_n)}/{len(b_n)} -> {sum(a_n)}/{len(a_n)}"
              f"   lift {lift_n:+.3f}")
        if events_nd < FLOOR_EVENTS:
            print(f"  NOT EVALUABLE — non-dictated channel has {events_nd} positive "
                  f"runs (< {FLOOR_EVENTS}); a design limit of the lexicon, not a result")
            continue
        lo, hi = boot_did(a_d, a_n, b_d, b_n)
        any_scored = True
        print(f"  DiD (dictated lift - non-dictated lift) = {lift_d - lift_n:+.3f} "
              f"[{lo:+.3f},{hi:+.3f}]")
        print(f"  -> {'COMPLIANCE SIGNATURE (CI excludes 0)' if lo > 0 else 'not distinguishable'}")

    # Whole-block contrast, all families pooled
    print()
    print("=" * 76)
    print("Whole block (c13-all vs c13-none), per family")
    print("=" * 76)
    if "c13-all" in arms:
        for fam, s in split.items():
            if not s["dictated"] or not s["non_dictated"]:
                print(f"  {fam:<9} — one channel empty; skipped")
                continue
            a_d = [present(r.output, s["dictated"]) for r in arms["c13-all"]]
            a_n = [present(r.output, s["non_dictated"]) for r in arms["c13-all"]]
            b_d = [present(r.output, s["dictated"]) for r in base]
            b_n = [present(r.output, s["non_dictated"]) for r in base]
            print(f"  {fam:<9} dictated {sum(b_d)}/{len(b_d)}->{sum(a_d)}/{len(a_d)}"
                  f"   non-dictated {sum(b_n)}/{len(b_n)}->{sum(a_n)}/{len(a_n)}")
    if not any_scored:
        print("\nPD13.1: NOT EVALUABLE on any channel — reported as a lexicon "
              "design limit per the registration.")


if __name__ == "__main__":
    main()
