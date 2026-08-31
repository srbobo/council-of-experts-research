"""Cell 60 item generator (registration 6d32991).

Every ground-truth answer is COMPUTED here, never judged. Run once to
produce docs/CELL60_ITEMS.json; re-running must reproduce it byte-for-
byte (fixed parameters, no randomness).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).parent.parent
FMT = ("\n\nEvery figure needed is stated above. Work step by step, then "
       "end your reply with a final line of exactly:\nANSWER: <number>")


def t1(cost, salv, life, months):
    """Declining balance, first year prorated, clamped at salvage."""
    rate = 2 / life
    y1 = rate * cost * months / 12
    y1 = min(y1, cost - salv)
    y2 = min(rate * (cost - y1), cost - y1 - salv)
    p = (f"A company buys equipment for ${cost:,} with an estimated salvage "
         f"value of ${salv:,} and a {life}-year useful life, and places it "
         f"in service with {months} months remaining in the fiscal year. "
         f"Policy: declining-balance depreciation at a rate of 2/{life} of "
         f"beginning book value; the first year's expense is prorated by "
         f"the {months} months in service; there is no switch to "
         f"straight-line; book value never falls below salvage. What is "
         f"the SECOND year's depreciation expense, in dollars rounded to "
         f"the nearest dollar?")
    return p, round(y2)


def t2(units, hours, rate, pick, brk):
    """Staffing cost per unit with a paid unproductive break."""
    prod = hours - brk / 60
    pickers = math.ceil(units / (pick * prod))
    cpu = pickers * hours * rate / units
    p = (f"A distribution centre must pick {units:,} units in one "
         f"{hours}-hour evening shift. Each picker sustains {pick} units "
         f"per hour while working, but the shift includes a paid "
         f"{brk}-minute meal break during which no picking occurs. The "
         f"loaded labour rate is ${rate} per hour, paid for the full "
         f"{hours} hours. Schedule the minimum whole number of pickers "
         f"that can clear the volume, then compute the labour cost per "
         f"unit. What is the labour cost per unit, in dollars rounded to "
         f"the nearest cent?")
    return p, round(cpu, 2)


def t3(fee, setup, weekly, rate, avert, value):
    """Months to recoup a setup cost from averted no-shows."""
    monthly_sav = weekly * (52 / 12) * rate * avert * value
    months = math.ceil(setup / (monthly_sav - fee))
    p = (f"A clinic schedules {weekly} appointments per week and has a "
         f"measured no-show rate of {int(rate*100)}%. A reminder service "
         f"costs ${fee:,} per month plus a one-time setup fee of "
         f"${setup:,}, and prevents {int(avert*100)}% of would-be "
         f"no-shows. Each prevented no-show is worth ${value} in retained "
         f"revenue. Using months of exactly 52/12 weeks, compute the "
         f"monthly net saving (prevented-no-show value minus the monthly "
         f"fee), then the number of whole months needed for cumulative "
         f"net savings to cover the setup fee (round up). How many "
         f"months?")
    return p, months


def t4(wk, per, cap, weeks, used):
    """Sick-leave balance under an accrual divisor and a cap."""
    accrued = min(cap, math.floor(wk * weeks / per))
    bal = accrued - used
    p = (f"An employee works {wk} hours per week and accrues 1 hour of "
         f"paid sick leave for every {per} hours worked (fractions do not "
         f"accrue; round accrued hours down), subject to an annual "
         f"accrual cap of {cap} hours. After exactly {weeks} weeks of "
         f"work the employee has used {used} hours of sick leave. What is "
         f"the remaining sick-leave balance, in hours?")
    return p, bal


def t5(pm, members, cost, slprem, thresh, hi_n, hi_cost):
    """Annual capitation margin with stop-loss recoveries."""
    rev = pm * members * 12
    base = cost * members * 12
    excess = max(0, hi_cost - thresh) * hi_n
    prem = slprem * members
    margin = rev - base - prem + excess
    p = (f"A medical group holds a capitated contract at ${pm:,} per "
         f"member per month for {members:,} members. Expected medical "
         f"cost averages ${cost:,} per member per month across the panel. "
         f"The group buys stop-loss insurance for ${slprem} per member "
         f"per year; the policy reimburses annual spend above "
         f"${thresh:,} per member. Exactly {hi_n} members are projected "
         f"to cost ${hi_cost:,} each for the year (their cost is already "
         f"included in the ${cost:,} average). Annual margin = capitation "
         f"revenue minus expected medical cost minus stop-loss premium "
         f"plus stop-loss reimbursements. What is the annual margin, in "
         f"dollars?")
    return p, margin


def t6(drivers, wage, uplift, share):
    """Reclassification reserve with a trebled wage-claim share."""
    res = round(drivers * wage * (1 + uplift) * ((1 - share) + 3 * share))
    p = (f"A company must reserve for reclassifying {drivers} contractor "
         f"drivers earning ${wage:,} each per year. Employer-cost uplift "
         f"(taxes and benefits) adds {int(uplift*100)}% on top of wages. "
         f"{int(share*100)}% of the base exposure is wage-claim exposure "
         f"subject to mandatory treble damages (multiply that share by "
         f"3); the remainder is counted once. Reserve = drivers x wage x "
         f"(1 + uplift) x [(1 - wage-claim share) + 3 x wage-claim "
         f"share]. What is the reserve, in dollars rounded to the "
         f"nearest dollar?")
    return p, res


def t7(lives, elig, up, m, q, offset):
    """Annual net drug budget with split persistence and an offset."""
    treated = round(lives * elig * up)
    persist = round(treated * q)
    spend = persist * 12 * m + (treated - persist) * 6 * m
    net = spend - persist * offset
    p = (f"A plan with {lives:,} covered lives estimates {int(elig*100)}% "
         f"are eligible for a drug programme and {int(up*100)}% of "
         f"eligible members enrol (round the enrolled count to the "
         f"nearest whole member). Net drug cost is ${m:,} per member per "
         f"month. {int(q*100)}% of enrolled members persist for 12 "
         f"months (round to the nearest whole member); the rest persist "
         f"for exactly 6 months. Each 12-month persister generates a "
         f"${offset:,} annual medical-cost offset. Annual net budget "
         f"impact = drug spend minus total offsets. What is it, in "
         f"dollars?")
    return p, spend - persist * offset


def t8(pay, esc, years):
    """Total lease cost under a compounding escalator."""
    total = round(sum(pay * (1 + esc) ** i for i in range(years)))
    p = (f"A sale-leaseback sets the first year's rent at ${pay:,}, "
         f"escalating {esc*100:g}% per year (compounding) starting in "
         f"year 2, for a {years}-year term. What is the total rent paid "
         f"over the full term, in dollars rounded to the nearest "
         f"dollar?")
    return p, total


SPECS = [
    ("t1", t1, [(67000, 9000, 5, 7), (84000, 12000, 7, 4), (53000, 6500, 5, 10),
                (128000, 15000, 8, 5), (46000, 5000, 4, 8)]),
    ("t2", t2, [(1700, 6, 29, 130, 30), (2300, 8, 31, 115, 45),
                (1150, 5, 27, 95, 20), (3400, 7, 33, 145, 40)]),
    ("t3", t3, [(1900, 52000, 220, .17, .32, 210), (2400, 98000, 310, .21, .28, 185),
                (1500, 41000, 180, .14, .41, 240), (3100, 125000, 420, .19, .35, 165)]),
    ("t4", t4, [(38, 30, 56, 24, 13), (42, 35, 64, 26, 24), (36, 28, 48, 15, 9),
                (40, 32, 72, 33, 29), (44, 30, 80, 19, 12)]),
    ("t5", t5, [(1180, 2400, 1085, 96, 30000, 14, 52000),
                (990, 5100, 940, 84, 25000, 22, 41000),
                (1320, 1800, 1210, 110, 35000, 9, 68000),
                (1075, 3600, 1010, 92, 28000, 19, 47500)]),
    ("t6", t6, [(180, 52000, .24, .35), (240, 47500, .21, .45),
                (95, 61000, .27, .30), (320, 43800, .22, .40)]),
    ("t7", t7, [(4100, .22, .18, 1050, .60, 2200),
                (6800, .17, .23, 985, .55, 1800),
                (2900, .26, .15, 1140, .65, 2600),
                (5200, .20, .21, 1015, .58, 2050)]),
    ("t8", t8, [(3100000, .025, 12), (2400000, .03, 15), (4150000, .02, 10),
                (1850000, .035, 20), (2750000, .028, 14), (3600000, .022, 18)]),
]


def main() -> None:
    items = []
    for tname, fn, variants in SPECS:
        for vi, params in enumerate(variants):
            prompt, ans = fn(*params)
            items.append({"id": f"{tname}_v{vi}", "template": tname,
                          "params": list(params),
                          "prompt": prompt + FMT, "answer": ans})
    out = {"note": ("Cell 60 items (registration 6d32991). Answers computed "
                    "by train/gen_cell60_items.py; regenerate to verify. "
                    "Tolerance: relative 0.5% (min absolute 0.01)."),
           "items": items}
    Path(ROOT / "docs" / "CELL60_ITEMS.json").write_text(
        json.dumps(out, indent=1))
    print(f"{len(items)} items written; answers: "
          + ", ".join(f"{i['id']}={i['answer']}" for i in items[:6]) + " ...")


if __name__ == "__main__":
    main()
