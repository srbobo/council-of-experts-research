# Attainability audit — 2026-08-11

**Trigger.** Cell 40 was the third consecutive null decided by a floor or
ceiling rather than by the manipulation (Cell 36 ceiling, Cell 37 P37.2
floor, Cell 40 non-firing outcome). The recorded risk: when the program's
falsifications keep tracing back to my own construction errors, some
fraction of its negative results may be artifacts of underpowered or
badly-built manipulations rather than facts about the architecture.

**Registration of scope, stated before computing.** This is an AUDIT, not
a test. It is post-hoc by construction and licenses no new claims. It
answers exactly two questions per verdict, from data already on disk:

1. **Did the outcome variable fire?** What fraction of runs produced a
   non-degenerate outcome the estimand is defined on?
2. **Could the null have detected the effect it is cited against?** Is the
   original / registered effect size inside or outside the null's CI?

**Standing caution, repeated.** Decisive-fraction must never become a
design target. A cell built to force the outcome to fire measures
compliance with the forcing (finding #8).

## Classification vocabulary

| class | meaning |
|---|---|
| **INFORMATIVE** | outcome fired at material rate AND the CI excludes the effect size the null is cited against |
| **WEAK** | outcome fired, but the CI cannot exclude effects of the size originally claimed or plausibly interesting |
| **UNINFORMATIVE** | the originally claimed effect sits INSIDE the null's CI — the cell cannot distinguish "no effect" from "the effect we used to claim" |
| **DEGENERATE** | the outcome variable rarely fired (floor) or nearly always fired (ceiling); the verdict is about the construction, not the manipulation |
| **UNAUDITED** | run-level data not in auditable form under current instruments |

---

## The table

| cell | verdict on record | outcome fired | CI vs effect of interest | class |
|---|---|---|---|---|
| 26 (corroboration) | FALSIFIED — no agreement weighting | modeled family measured on n=76 k≥2 runs, transport ~0.5 both sides — no floor | diff CI [−0.153, +0.080] **excludes any gain > +0.08** | **INFORMATIVE** |
| PD-13 (compliance) | positive, DiD +0.83 | 0/30 → 28/30 — massive event rates both cells | CI [+0.67, +1.00] far from 0 | **INFORMATIVE** |
| 35 (error propagation, MoE) | 0/17 propagation | arithmetic engagement 10/15; injections authored against seat content, **coherent with host cases** (checked: case_3 figures match the case; case_5 adds figures the case never states) | propagation CI [0, 0.184] excludes rates > 18% | **INFORMATIVE, narrowed** — already limited by Cell 37 to the redundancy-protected case |
| 39 (dense writer) | both architectures filter | dense engagement 6/15 = 0.40 | CI [0, 0.259] — excludes only rates > 26% | **WEAK** (engagement 0.40 and n=11 judged) |
| 30 (transport law) | P30.1 SUPPORTED, w = 0.150 | 11 distinct supply levels, n=60; y=0 in 22/60 runs — variance present on both axes | CI [0.058, 0.252] excludes 0 | **INFORMATIVE** (positive; survives its own audit) |
| 27 (ledger, regex-era) | all four falsified | supply spread 0–4 but 52/69 runs carry no detected property — instrument-floor | P27.2 diff CI [−0.444, +0.033], direction FAVOURED the ledger; width 0.48 | **WEAK** — registered bars honestly missed, but citing "the ledger does nothing" from this cell overreaches; regex-era besides |
| 31 (ledger, validated) | Δc = +0.182 [−0.868, +1.261] → withdrawal | y=0 in 37% (P) and 45% (L) of runs; mean emitted 1.25 / 1.61 — outcome fired | **original claimed gap +0.637 is INSIDE the CI** | **UNINFORMATIVE** |
| 36 (accuracy) | P36.1 falsified, noted weak | attempt rate 59/60, 58/59, 60/60 — but correctness at ceiling 0.92–0.97 | paired comparison contains **3 discordant items of 59** (1 favouring council, 2 favouring MoE) | **DEGENERATE (ceiling)** — the bootstrap resampled three coin-flips |
| 37 P37.1 (recomputation) | FALSIFIED | decisive 7/27, 4/27, 7/27, 12/27 — low but the falsifier is the within-arm 5-vs-2 contrast in A2 plus the monotone gradient 1→0→5→12 | within-arm; base-rate depression cannot manufacture it | **INFORMATIVE despite the floor** (stands as recorded) |
| 37 P37.2 (prior) | downgraded 2026-08-11 | A2 correct 2/27, A3 0/27 — both at floor | no attainability note was ever registered for it | **DEGENERATE (floor)** (as recorded) |
| 40 (seat directive) | NOT EVALUABLE | decisive 3/27, 6/27, 2/27 vs a floor of 6 | — | **DEGENERATE (floor)** (as recorded; finding #11) |
| 23 / 28 / 29 / IV | instrument & formula cells | verdicts are about fits and instruments, not run-level events | own pre-registered checks | out of scope; no change |
| 8 / 14 / 15 (early nulls) | feed the "no council advantage" row | pre-audit-era formats, regex-era instruments | — | **UNAUDITED** at run level |

---

## Consequences, applied

### 1. Cell 31: the ledger withdrawal stands; the ledger *null* does not

The withdrawal was a burden-of-proof decision — the original evidence
compounded a two-factor baseline with an entangled instrument, so the
claim had no support. That reasoning is untouched. But the replacement
cell's CI is 2.13 wide and **contains the original +0.637**. Cell 31
cannot be cited as evidence the ledger does nothing; it can only be cited
as failure to re-establish the claim. STATUS.md reworded accordingly.
"Is the ledger a distinct mechanism?" is OPEN, not answered-no.

### 2. Cell 36: the accuracy null was three coin-flips

With 56 of 59 paired items identical across arms, the paired bootstrap had
three informative events. The LIVE row's Cell 36 clause is downgraded from
"weak null — ceiling" to stating the discordant count outright. The
composite "no measured council advantage" row now rests on Cells 8/14/15
(unaudited, regex-era) plus this. The row survives — no *positive*
evidence of advantage exists anywhere — but its evidential weight is
thinner than the ledger has implied, and it is now marked as resting on
absence of evidence, not evidence of absence, pending the harder battery.

### 3. Cells that survive their own audit

Cell 26's corroboration null is genuinely informative (excludes gains
above +0.08 on the validated family). PD-13 is overwhelming. Cell 30's
positive survives. Cell 35's null is real within its (already narrowed)
redundancy-protected scope. Cell 37's P37.1 falsification stands because
its falsifier is within-arm. The audit is not a uniform indictment — it
sorts, which is what it was for.

### 4. The checklist gains item 12

**Outcome attainability**: before any cell runs, compute — from existing
runs, not intuition — the fraction of runs in which the outcome variable
can fire at all, and state the CI width the planned n buys against the
effect size the cell is meant to detect. An attainability note for the
PRIMARY only (Cell 37's mistake) does not cover the secondaries.

### 5. What this audit does NOT license

- No null is deleted; reclassification changes *citation strength*, not
  history. Verdicts on record stay on record.
- No re-run is triggered by this document. Re-runs remain gated on their
  own pre-run conditions (Cell 40's two; Cell 36's harder battery).
- "The nulls were underpowered" is NOT evidence the effects exist. An
  uninformative null moves a question back to OPEN — never to supported.
