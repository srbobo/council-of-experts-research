"""Cell 60-R item generator — rule-interaction round (frozen path
8c53e0e). Difficulty lives in selecting and sequencing interacting
rules; arithmetic is deliberately trivial. Each template is a rule
ENGINE: the code is the ground truth, and the prompt states the rules
exactly as coded. Every item records which rule path fired; a guard
requires >=3 distinct paths per template.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
FMT = ("\n\nEvery rule and fact needed is stated above. Reason through "
       "which rules apply and in what order, then end your reply with a "
       "final line of exactly:\nANSWER: <number>")


def r1(hire_year, vol, notice, vac, sick, rate, cause):
    """Termination payout."""
    path = []
    v = vac
    if cause:
        v = min(v, 40); path.append("cause-cap")
    total = v * rate
    if hire_year < 2015:
        total += min(sick, 60) * rate; path.append("grandfathered-sick")
    if vol and notice >= 14:
        total += 500; path.append("notice-bonus")
    p = (f"An employee is leaving a company. Payout rules: (1) unused "
         f"vacation hours are paid at the employee's base rate; (2) unused "
         f"sick hours are NOT paid, except that employees hired before "
         f"2015 are paid for unused sick hours up to a cap of 60 hours; "
         f"(3) if the termination is for cause, paid vacation hours are "
         f"capped at 40; (4) a $500 notice bonus is paid only if the "
         f"departure is voluntary AND the employee gave at least 14 days' "
         f"notice. Facts: hired in {hire_year}; departure is "
         f"{'voluntary' if vol else 'involuntary (for cause)' if cause else 'an involuntary layoff (not for cause)'}; "
         f"{notice} days' notice was given; {vac} unused vacation hours; "
         f"{sick} unused sick hours; base rate ${rate}/hour. What is the "
         f"total payout, in dollars?")
    return p, total, "+".join(path) or "base"


def r2(late, fm, fm_notice_ok, contract, per_day, notice_late):
    """Late-delivery penalty."""
    path = []
    eff = late
    if fm_notice_ok:
        eff -= fm; path.append("fm-excluded")
    grace = 0 if notice_late else 10
    if notice_late:
        path.append("grace-forfeit")
    billable = max(0, eff - grace)
    pen = billable * per_day
    cap = 0.10 * contract - 2000
    if pen > cap:
        pen = cap; path.append("cap")
    p = (f"A supplier delivered {late} days after the contract date. "
         f"Penalty rules: (1) a penalty of ${per_day:,} per day applies "
         f"after a 10-day grace period; (2) the grace period is forfeited "
         f"entirely if the supplier notified the buyer of the delay later "
         f"than 5 days before the contract date — "
         f"{'which happened here' if notice_late else 'the supplier notified in time, so grace applies'}; "
         f"(3) days lost to force majeure are excluded from the delay, "
         f"but only if the force-majeure event was reported within 3 days "
         f"— {fm} of the late days were force majeure, "
         f"{'reported within 3 days' if fm_notice_ok else 'reported after the 3-day window'}; "
         f"(4) the total penalty is capped at 10% of the contract value "
         f"of ${contract:,} minus the $2,000 deposit the buyer already "
         f"retains. What penalty is owed, in dollars?")
    return p, round(pen), "+".join(path) or "base"


def r3(claims, ded, coins, oopmax):
    """Member cost over ordered claims. claims: (amount, kind) with kind
    in-network 'in', preventive 'prev', out-of-network 'oon'."""
    path = []
    ded_left = {"in": ded, "oon": ded * 2}
    oop = 0.0
    member = 0.0
    for amt, kind in claims:
        if kind == "prev":
            path.append("prev-bypass"); continue
        dl = ded_left["oon" if kind == "oon" else "in"]
        d = min(amt, dl)
        ded_left["oon" if kind == "oon" else "in"] -= d
        if kind == "oon":
            member += d + (amt - d) * coins
            path.append("oon")
            continue
        pay_d = d
        rem = (amt - d) * coins
        room = max(0.0, oopmax - oop)
        pay = min(pay_d + rem, room)
        if pay < pay_d + rem:
            path.append("oop-cap")
        member += pay
        oop += pay
    p_claims = "; ".join(
        f"claim {i+1}: ${amt:,}, "
        + {"in": "in-network", "prev": "in-network preventive",
           "oon": "out-of-network"}[kind]
        for i, (amt, kind) in enumerate(claims))
    p = (f"A health plan member has three claims processed in the order "
         f"listed. Rules: (1) an in-network deductible of ${ded:,} applies "
         f"first — the member pays claim costs until it is met; (2) after "
         f"the deductible, the member pays {int(coins*100)}% coinsurance "
         f"on in-network claims; (3) the member's in-network payments "
         f"(deductible and coinsurance) stop at an out-of-pocket maximum "
         f"of ${oopmax:,}; (4) preventive in-network care is free — no "
         f"deductible, no coinsurance; (5) out-of-network claims face a "
         f"separate deductible of twice the in-network amount, then the "
         f"same coinsurance, and NONE of those payments count toward the "
         f"out-of-pocket maximum. Claims: {p_claims}. What is the "
         f"member's total payment, in dollars?")
    return p, round(member), "+".join(sorted(set(path))) or "base"


def r4(income, t1, service_ok, liability):
    """Credit stacking."""
    path = []
    A = 1200 if income < t1 else 0
    B = 1850 if service_ok else 0
    if A and B:
        big = max(A, B); path.append("choose-larger")
    else:
        big = A or B
    C = 750 if income < 90000 else 0
    if not C:
        path.append("c-phaseout")
    nonref = (big if big == B else 0) + C
    nonref_used = min(nonref, liability)
    if nonref_used < nonref:
        path.append("liability-limit")
    refund = big if big == A else 0
    total = refund + nonref_used + 350
    p = (f"Compute a taxpayer's total benefit from three credits. Rules: "
         f"(1) Credit A is $1,200 if income is below ${t1:,}; (2) Credit "
         f"B is $1,850 if the qualifying property was placed in service "
         f"in an eligible year — "
         f"{'it was' if service_ok else 'it was not'}; A and B cannot be "
         f"combined: if both qualify, take only the larger; (3) Credit C "
         f"is $750 and stacks with either, but is eliminated entirely "
         f"when income is $90,000 or more; (4) Credit A is refundable "
         f"(paid in full regardless of tax owed); Credits B and C are "
         f"nonrefundable — together they cannot exceed the tax liability "
         f"of ${liability:,}; (5) a $350 state rebate is refundable and "
         f"stacks with everything above. Facts: income ${income:,}. What "
         f"is the total benefit, in dollars?")
    return p, total, "+".join(path) or "base"


def r5(days, rate, diff):
    """Weekly pay under daily/weekly/7th-day overtime, no double count.
    days: list of 7 daily hours (Mon..Sun), 7th consecutive day = Sunday
    only if all 7 worked."""
    path = []
    reg = ot15 = ot2 = 0.0
    seventh = all(d > 0 for d in days)
    for i, h in enumerate(days):
        if i == 6 and seventh:
            a = min(h, 8); b = max(0.0, h - 8)
            ot15 += a; ot2 += b; path.append("seventh-day")
            continue
        d_ot = max(0.0, h - 8)
        ot15 += d_ot
        reg += h - d_ot
    if reg > 40:
        ot15 += reg - 40; reg = 40.0; path.append("weekly-ot")
    worked = sum(1 for d in days if d > 0)
    pay = reg * rate + ot15 * rate * 1.5 + ot2 * rate * 2 + worked * diff
    p = (f"Compute a worker's weekly pay. Hours Monday through Sunday: "
         f"{', '.join(str(d) for d in days)}. Rules: (1) daily overtime: "
         f"hours beyond 8 in a day are paid at 1.5x the base rate; "
         f"(2) weekly overtime: regular (non-overtime) hours beyond 40 in "
         f"the week are paid at 1.5x — hours already paid as daily "
         f"overtime do not count toward the 40; (3) if all seven days are "
         f"worked, the seventh day is special: its first 8 hours are paid "
         f"at 1.5x and hours beyond 8 at 2x (rules 1-2 do not also apply "
         f"to that day); (4) a shift differential of ${diff} is paid for "
         f"each day worked, and overtime multipliers apply to the base "
         f"rate of ${rate}/hour only, never to the differential. What is "
         f"the weekly pay, in dollars?")
    return p, round(pay), "+".join(sorted(set(path))) or "base"


def r6(closure_m, minor_at18_m, hold_m, erasure_m):
    """Deletion deadline in months after a reference date. closure_m:
    months-after-reference of case closure; minor_at18_m: months-after-
    reference when the person turns 18 (None if adult); hold_m: litigation
    hold duration in months (0 none); erasure_m: months-after-reference of
    a verified erasure request (None if none)."""
    path = []
    start = closure_m
    if minor_at18_m is not None and minor_at18_m > start:
        start = minor_at18_m; path.append("minor-clock")
    deadline = start + 24
    if erasure_m is not None:
        deadline = erasure_m + 1; path.append("erasure-override")
    if hold_m:
        deadline += hold_m; path.append("hold-extends")
    p = (f"Compute a record's deletion deadline, expressed as the number "
         f"of months after January 2025 (January 2025 = 0). Rules: "
         f"(1) records are deleted 24 months after case closure; (2) for "
         f"a person who was a minor at closure, the 24-month clock starts "
         f"when they turn 18 instead, if that is later; (3) a verified "
         f"erasure request overrides rules 1-2: the deadline becomes one "
         f"month after the request; (4) an active litigation hold "
         f"suspends deletion: add the hold's duration to whatever "
         f"deadline applies (the hold applies even against an erasure "
         f"request). Facts: the case closed {closure_m} months after "
         f"January 2025"
         + (f"; the person turns 18 {minor_at18_m} months after January "
            f"2025" if minor_at18_m is not None else
            "; the person was an adult at closure")
         + (f"; a verified erasure request arrived {erasure_m} months "
            f"after January 2025" if erasure_m is not None else
            "; no erasure request was made")
         + (f"; a litigation hold ran for {hold_m} months."
            if hold_m else "; there was no litigation hold.")
         + " What is the deletion deadline, in months after January "
           "2025?")
    return p, deadline, "+".join(path) or "base"


SPECS = [
    ("r1", r1, [(2012, True, 20, 85, 90, 31, False),
                (2018, True, 9, 62, 45, 27, False),
                (2013, False, 0, 70, 30, 29, True),
                (2016, False, 30, 55, 80, 33, False),
                (2011, True, 14, 38, 72, 26, True)]),
    ("r2", r2, [(34, 9, True, 180000, 850, False),
                (27, 6, False, 120000, 950, False),
                (41, 12, True, 90000, 1100, True),
                (19, 0, True, 300000, 700, True),
                (52, 15, False, 150000, 800, False)]),
    ("r3", r3, [([(900, "in"), (2400, "in"), (600, "prev")], 1500, .2, 3000),
                ([(900, "in"), (6800, "in"), (1500, "oon")], 1000, .25, 2200),
                ([(1800, "oon"), (1200, "in"), (2600, "in")], 1200, .3, 2800),
                ([(3100, "in"), (450, "prev"), (2900, "oon")], 2000, .2, 3500),
                ([(2000, "in"), (900, "in"), (1200, "oon")], 1400, .25, 1700)]),
    ("r4", r4, [(52000, 60000, True, 4000),
                (95000, 60000, True, 5000),
                (52000, 60000, False, 400),
                (85000, 60000, True, 2100),
                (40000, 60000, False, 900)]),
    ("r5", r5, [([9, 8, 10, 8, 8, 4, 0], 30, 15),
                ([8, 8, 8, 8, 8, 8, 6], 28, 12),
                ([10, 9, 9, 8, 8, 0, 0], 32, 20),
                ([9, 9, 9, 9, 9, 5, 4], 26, 10),
                ([12, 8, 8, 8, 8, 0, 3], 34, 18)]),
    ("r6", r6, [(6, None, 0, None), (4, 30, 0, None), (8, None, 5, 12),
                (3, 26, 7, 14), (10, None, 6, None)]),
]


def main() -> None:
    items, paths = [], {}
    for tname, fn, variants in SPECS:
        for vi, params in enumerate(variants):
            prompt, ans, path = fn(*params)
            items.append({"id": f"{tname}_v{vi}", "template": tname,
                          "params": repr(params), "path": path,
                          "prompt": prompt + FMT, "answer": ans})
            paths.setdefault(tname, set()).add(path)
    for tname, ps in paths.items():
        assert len(ps) >= 3, f"{tname}: only {len(ps)} rule paths {ps}"
    out = {"note": ("Cell 60-R items (frozen path 8c53e0e). Rule-engine "
                    "ground truth computed by train/gen_cell60R_items.py; "
                    "each template's variants traverse >=3 distinct rule "
                    "paths (asserted). Tolerance: relative 0.5%, min "
                    "absolute 0.01."),
           "items": items}
    Path(ROOT / "docs" / "CELL60R_ITEMS.json").write_text(
        json.dumps(out, indent=1))
    print(f"{len(items)} items; paths per template: "
          + "; ".join(f"{k}:{len(v)}" for k, v in paths.items()))
    for i in items:
        print(f"  {i['id']:<7} ans={i['answer']:>8}  path={i['path']}")


if __name__ == "__main__":
    main()
