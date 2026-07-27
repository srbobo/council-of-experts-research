"""Cell 7c — per-family, seat-matched decomposition of every core verdict.

Motivation. The composite disposition metric sums five behavior families, but
they are not uniformly distributed across seats: modeled-assumption flagging
lives almost entirely on the finance seat, hedging on healthcare/finance, and
jurisdictional distinguishing is thin everywhere. Scoring all five on one seat
(as the headline tables do) understates families that belong elsewhere and lets
the composite be dominated by training-cutoff disclosure.

This script re-decomposes the EXISTING 628 imported runs -- no new inference --
answering: which of the paper's claims are cutoff-only, and which hold for the
families that actually carry signal on the seat that owns them?

Ownership (empirical, from untrained-baseline densities per seat):
    cutoff   -> universal (all three seats)
    modeled  -> finance
    hedging  -> healthcare, finance
    jurisd   -> legal (weak, reported with the caveat)
    precise  -> none; below detection on every seat (documented, not analysed)

Run: .venv/bin/python train/family_decompose.py
"""

from __future__ import annotations

import json
import os
import random
import re
import statistics as st
from pathlib import Path

random.seed(42)
IMPORTED = Path("bench/runs/imported")

FAM = {
    "cutoff": [r'training[- ]?cut[- ]?off', r'knowledge cut[- ]?off',
               r'may (?:be |have )(?:stale|outdated|evolved)', r'post[- ]?cut[- ]?off',
               r'after my training', r'verify (?:current|latest|recent)',
               r'as of (?:my )?(?:training|knowledge|2024|2025)'],
    "modeled": [r'modell?ed at', r'\bassume[ds]? (?:that|the)',
                r'\bassuming (?:that|the|a |an |\d)', r'under the assumption',
                r'this assume[ds]', r'\bwe assume\b', r'\bhypothetical[ly]?\b'],
    "precise": [r'(?:approval).*?(?:vs\.?|versus|not).*?(?:clearance)',
                r'distinguish(?:es|ing|ed)? between', r'standard[- ]of[- ]care',
                r'(?:510\(k\)|de novo|PMA)\s+(?:clearance|approval|pathway)',
                r'\b(?:NDA|BLA)\s+approval\b'],
    "jurisd": [r'\bUK\s?GDPR\b', r'\bEU\s?GDPR\b', r'post[- ]Brexit',
               r'each\s+(?:jurisdiction|country|state|regime)', r'preempt(?:ion|s|ed)'],
    "hedging": [r'(?:false[- ]positive|false[- ]negative)', r'alert fatigue',
                r'real[- ]world\s+(?:evidence|data)', r'sensitivity (?:analysis|range|to|of)',
                r'low/?high (?:case|scenario|estimate)', r'\b±\s?\d',
                r'(?:may|might|could)\s+(?:vary|differ|change)'],
}
# Seat that owns each family (empirically determined; see docstring).
OWNER = {"cutoff": None, "modeled": "finance", "hedging": "healthcare",
         "jurisd": "legal", "precise": None}
DETECTABLE = ["cutoff", "modeled", "hedging", "jurisd"]  # precise excluded


def fam_density(text: str, fam: str) -> float:
    if not text:
        return 0.0
    hits = sum(len(re.findall(p, text, re.I)) for p in FAM[fam])
    return hits / len(text) * 1000


def boot_ci(vals: list[float], n: int = 10000) -> tuple[float, float, float]:
    if not vals:
        return (0.0, 0.0, 0.0)
    means = sorted(sum(random.choices(vals, k=len(vals))) / len(vals) for _ in range(n))
    return (st.mean(vals), means[int(n * 0.025)], means[int(n * 0.975)])


def load(mode: str, *, case7: bool | None = False):
    """Yield (filename, run dict) for a mode; case7=None means all cases."""
    for fn in sorted(os.listdir(IMPORTED)):
        if not fn.endswith(f"__{mode}.json"):
            continue
        if case7 is not None and (("case_7" in fn) != case7):
            continue
        yield fn, json.loads((IMPORTED / fn).read_text())


def seat_texts(mode: str, seat: str, *, case7: bool | None = False) -> list[str]:
    out = []
    for _, d in load(mode, case7=case7):
        for t in d.get("deliberation", {}).get("turns", []):
            if t.get("seat") == seat:
                out.append(t.get("output_text", ""))
                break
    return out


def final_texts(mode: str, *, case7: bool | None = False) -> list[str]:
    return [d.get("final_output", "") for _, d in load(mode, case7=case7)]


def hdr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def main() -> int:
    # ---------------------------------------------------------------- ownership
    hdr("[0] FAMILY OWNERSHIP — untrained baseline density per seat")
    print(f"{'family':<9}" + "".join(f"{s:>12}" for s in ("healthcare", "legal", "finance"))
          + f"{'owner':>13}")
    for fam in FAM:
        row = [st.mean([fam_density(t, fam) for t in seat_texts("local-council-repro", s)])
               for s in ("healthcare", "legal", "finance")]
        own = OWNER[fam] or ("universal" if max(row) > 0.3 else "BELOW DETECTION")
        print(f"{fam:<9}" + "".join(f"{v:12.2f}" for v in row) + f"{own:>13}")

    # ------------------------------------------------- 1. seat-level install
    hdr("[1] SEAT-LEVEL INSTALL, per family — legal seat arms (the Result-2 table)")
    print("Does the ~2x SFT/prompt install hold for families beyond cutoff?")
    arms = [("A'", "local-council-repro"), ("prompt", "local-council-spec"),
            ("SFT", "local-council-sft"), ("ORPO", "local-council-dpo"),
            ("CPO", "local-council-cpo")]
    print(f"{'family':<9}" + "".join(f"{a:>10}" for a, _ in arms))
    for fam in DETECTABLE:
        vals = [st.mean([fam_density(t, fam) for t in seat_texts(m, "legal")]) for _, m in arms]
        print(f"{fam:<9}" + "".join(f"{v:10.2f}" for v in vals))
    print("\n  NOTE: measured on the LEGAL seat, which owns only jurisd. cutoff is")
    print("  universal so it is comparable; modeled/hedging live elsewhere (see [2]).")

    # --------------------------------------------- 2. owner-seat install check
    hdr("[2] OWNER-SEAT CHECK — do the seat-3 replication arms move their OWN family?")
    checks = [
        ("finance", "modeled", "local-council-finance-repro", "local-council-finance-orpo"),
        ("healthcare", "hedging", "local-council-health-repro", "local-council-health-orpo"),
        ("legal", "jurisd", "local-council-repro", "local-council-dpo"),
    ]
    print(f"{'seat':<11}{'family':<9}{'A-prime [95% CI]':>26}{'ORPO [95% CI]':>26}  verdict")
    for seat, fam, a_mode, o_mode in checks:
        a = boot_ci([fam_density(t, fam) for t in seat_texts(a_mode, seat)])
        o = boot_ci([fam_density(t, fam) for t in seat_texts(o_mode, seat)])
        overlap = not (o[2] < a[1] or a[2] < o[1])
        print(f"{seat:<11}{fam:<9}{a[0]:8.2f} [{a[1]:.2f}, {a[2]:.2f}]{o[0]:12.2f} "
              f"[{o[1]:.2f}, {o[2]:.2f}]  {'null (CIs overlap)' if overlap else 'MOVED'}")

    # --------------------------------------------------- 3. synthesis survival
    hdr("[3] SYNTHESIS SURVIVAL, per family — seat density vs final density")
    print("Does every family get stripped, or only cutoff?")
    print(f"{'family':<9}{'owner seat':>12}{'seat dens':>11}{'final dens':>12}{'retention':>11}")
    for fam in DETECTABLE:
        seat = OWNER[fam] or "legal"
        sv = st.mean([fam_density(t, fam) for t in seat_texts("local-council-repro", seat)])
        fv = st.mean([fam_density(t, fam) for t in final_texts("local-council-repro")])
        ret = fv / sv if sv > 0.01 else float("nan")
        print(f"{fam:<9}{seat:>12}{sv:11.2f}{fv:12.2f}{ret:11.2f}")

    # ------------------------------------------------------ 4. gain curve
    hdr("[4] GAIN CURVE, per family — pooled over 3 Leads (6c)")
    print("Is the aggregate monotonicity carried by one family or several?")

    def spearman(x, y):
        n = len(x)
        rx = [sorted(x).index(v) + 1 for v in x]
        ry = [sorted(y).index(v) + 1 for v in y]
        return 1 - 6 * sum((a - b) ** 2 for a, b in zip(rx, ry)) / (n * (n * n - 1))

    print(f"{'family':<9}" + "".join(f"{'k=' + str(k):>8}" for k in (0, 1, 2, 3)) + f"{'rho':>8}")
    for fam in DETECTABLE:
        ms = []
        for k in (0, 1, 2, 3):
            texts = []
            for lead in ("phi4", "gptoss", "qwen"):
                texts += final_texts(f"cell6c-gain-k{k}-{lead}", case7=None)
            ms.append(st.mean([fam_density(t, fam) for t in texts]))
        print(f"{fam:<9}" + "".join(f"{m:8.2f}" for m in ms) + f"{spearman([0,1,2,3], ms):+8.2f}")

    # ------------------------------------------------------ 5. additivity
    hdr("[5] ADDITIVITY, per family — final density vs hot-seat count (6c)")
    print(f"{'family':<9}" + "".join(f"{'h=' + str(h):>8}" for h in (0, 1, 2, 3)) + f"{'rho':>8}")
    for fam in DETECTABLE:
        ms = [st.mean([fam_density(t, fam) for t in final_texts(f"cell6c-hot{h}", case7=None)])
              for h in (0, 1, 2, 3)]
        print(f"{fam:<9}" + "".join(f"{m:8.2f}" for m in ms) + f"{spearman([0,1,2,3], ms):+8.2f}")

    # ------------------------------------------------------ 6. lead training
    hdr("[6] LEAD-TRAINING NULL, per family (6b) — final output")
    print(f"{'family':<9}{'A-prime [95% CI]':>26}{'ORPO [95% CI]':>26}  verdict")
    for fam in DETECTABLE:
        a = boot_ci([fam_density(t, fam) for t in final_texts("cell6b-lead-repro")])
        o = boot_ci([fam_density(t, fam) for t in final_texts("cell6b-lead-orpo")])
        overlap = not (o[2] < a[1] or a[2] < o[1])
        print(f"{fam:<9}{a[0]:8.2f} [{a[1]:.2f}, {a[2]:.2f}]{o[0]:12.2f} [{o[1]:.2f}, {o[2]:.2f}]"
              f"  {'null (CIs overlap)' if overlap else 'MOVED'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
