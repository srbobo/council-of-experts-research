# Architecture-wide sweep with the GST kit — 2026-08-05

Ran the shipped measurement kit across every arm in the ledger (1,260 usable
runs, 27 arms with n≥30) to ask a question the program had never asked in this
form: **across everything we built, what actually moved the writer's
behavior?**

Analysis is post-hoc and exploratory. It is not a pre-registered test, and
nothing here is a verdict on a registered proposition; it is a re-measurement
of existing runs under a common instrument with intervals attached.

---

## 1. Most of our own comparisons were never powered

Of 27 arms with n≥30 and an identifiable evidence weight:

| status | arms |
|---|---|
| comparable (zero-supply observed, w interval ≤ 0.35) | **5** |
| prior fill extrapolated (no runs at supply 0) | 1 |
| weakly identified (w interval > 0.35) | **21** |

The naive ranking's leaders — w=0.760 for `cell6b-lead-repro`, c=−0.588 for
`arch-debate` — are precisely the arms with no zero-supply data. A negative
prior fill is impossible for a count and is what exposed the extrapolation:
`c` is the fit at s=0, so when no run executed at s=0 it is a projection
beyond the data. Two guards now live in `gst.measure.shrinkage`
(`c_extrapolated`, `weakly_identified`) and refuse the estimate rather than
report it.

**Confound caught:** the label `arch-council` pools three cells (8, 14, 15)
and 17 cases, including 8 load-sweep cases no other arm ran. Comparing it
directly to `c17/c19/c20` (9 cases each) compares case batteries, not arms.
All figures below restrict every arm to the 9 shared cases, n=45 each, same
writer (gpt-oss:20b). `gst.compare.check_comparable` now detects this.

## 2. The five comparable arms (regex instrument)

| arm | w [95% CI] | c [95% CI] | λ | p₀ | f | clean @ s=0 |
|---|---|---|---|---|---|---|
| arch-council | 0.346 [0.22,0.47] | 0.713 [0.44,0.99] | 0.333 | 0.667 | 0.065 | 0.444 |
| arch-flat | 0.255 [0.13,0.39] | 0.079 [−0.17,0.33] | 0.044 | 0.956 | 0.000 | 0.750 |
| c17-suppress | 0.375 [0.23,0.49] | 0.732 [0.39,1.19] | 0.178 | 0.844 | 0.067 | 0.571 |
| c19-gated | 0.443 [0.28,0.60] | 0.527 [0.20,0.96] | 0.178 | 0.822 | 0.069 | 0.833 |
| c20-decide | 0.419 [0.27,0.57] | 0.805 [0.53,1.11] | 0.222 | 0.778 | 0.055 | 0.364 |

Every w interval overlaps every other. On the shrinkage parameters, **no arm
is distinguishable from any other.**

On invention rate against the council baseline (bootstrap CI on the
difference, 5,000 draws, n=45 per arm):

| arm | λ | runs with invention | diff CI vs baseline | |
|---|---|---|---|---|
| arch-flat | 0.044 | 2/45 | [−0.444, −0.133] | **disjoint** |
| c17-suppress | 0.178 | 7/45 | [−0.333, +0.044] | not distinguishable |
| c19-gated | 0.178 | 8/45 | [−0.333, +0.022] | not distinguishable |
| c20-decide | 0.222 | 10/45 | [−0.289, +0.067] | not distinguishable |

One disjoint result in the whole comparison, and it belongs to the arm whose
feature-span fraction is **0.000** — `arch-flat` emits essentially no
qualification content at all. It is not preserving upstream caution better;
it is silent, and silence scores well on a test for invention.

## 3. Two-instrument adjudication — the result that matters

225 runs re-scored with the calibrated NLI instrument (`gst.nli`, frozen
Youden thresholds, four detectable families).

| arm | λ regex | λ NLI | diff CI vs baseline (NLI) |
|---|---|---|---|
| arch-council | 0.333 | 0.156 | — |
| arch-flat | 0.044 | **0.156** | [−0.156, +0.156] |
| c17-suppress | 0.178 | 0.089 | [−0.200, +0.067] |
| c19-gated | 0.178 | 0.089 | [−0.200, +0.067] |
| c20-decide | 0.222 | 0.067 | [−0.222, +0.044] |

**Under an independent instrument, nothing differs from the baseline —
including the one result that was disjoint under regex.** `arch-flat`'s
advantage does not shrink; it disappears exactly (0.156 against 0.156). Its
apparent superiority was an artifact of a lexicon that does not match its
phrasing, which is the same mechanism as paraphrase evasion arriving by
accident rather than by optimization.

Net: **no configuration we built — routing, suppression clause, runtime
gate, or DECIDE clause — is distinguishable from the plain council baseline
under two instruments.**

Directional observations, none significant, recorded because they are
consistent with earlier registered findings: the full council is the worst
arm on regex-measured invention (56% of zero-supply runs); the DECIDE clause
has the highest prior fill and worst zero-supply clean rate under regex
(0.364, best-of-7 needed), consistent with Cell 20's finding that asking for
commitment moves form rather than substance.

## 4. Instrument-validity finding #7 — the instruments are not interchangeable

The precondition for every two-instrument verdict in this program is that
both detect the same construct with independent errors. That precondition
fails here.

- Run-level: the two disagree on **whether invention occurred at all** in
  **59/225 runs (26.2%)** — regex-only 38, NLI-only 21, both 4, neither 162.
- Family-level: **agreement is zero.** Across 225 runs there is not a single
  case where both instruments flag the *same* family as invented.
- Supply: regex sees {0:41, 1:31, 2:36, 3:76, 4:41}; NLI sees
  {0:34, 1:86, 2:104, 3:1}. NLI essentially never registers 3+ families
  upstream where regex often does.

These are not two noisy measurements of one quantity. They are two different
quantities, and "confirmed by both instruments" cannot mean corroboration
until that is fixed.

Consequences, stated plainly:

1. The ensemble arithmetic in the intervention design (C3, joint evasion
   ≈ Πεᵢ) assumes weakly dependent blind spots on a shared construct. It does
   not hold for this instrument pair and must not be quoted for it.
2. Prior two-instrument verdicts in this program are weaker than recorded:
   agreement between them was never established, only used.
3. Likely cause to test first: the NLI thresholds were calibrated on a
   chosen-vs-rejected discrimination task (AUC 0.929 on *that* task), not on
   family-presence ground truth. A presence-calibrated threshold set is the
   obvious next step, and it is cheap.

Until then, `gst.instruments.ConsensusInstrument` should not be built from
this pair, and `gst.compare.compare_two_instrument` should be read as "two
independent measurements agree/disagree," not as one corroborating the other.

## 5. What this changes

- **Stop tuning prompts.** Four prompt-level interventions, none
  distinguishable. The framework predicted this (instructions do not change
  what is loss-optimal); the sweep confirms it on our own data.
- **The two untested interventions are the ones left.** Counterfactual-corpus
  retraining with span-masked minimal pairs (C1+C2), and verifier-blind
  best-of-n selection (C5). Neither has been run.
- **Fix the instrument pair before any further verdict.** Recalibrate NLI on
  family presence and re-check agreement. This blocks C3 and weakens every
  claim that leans on two instruments.
- **Design future cells for identifiability.** Include zero-supply cases in
  every arm, keep arm labels unique per case battery, and size for the
  interval rather than the point estimate.

Reproduce: `gst selftest bench/runs/imported`; raw adjudication in
`bench/analysis/nli_adjudication.json`.

---

## Postscript, same day — Cells 23 and 24 change two things above

**Section 3 is VOID.** Cell 23's presence calibration established that the
NLI instrument carries no family-presence signal at any threshold (AUC
0.12–0.55 against validated judge labels). The adjudication table above and
its conclusion — "under an independent instrument, nothing differs from
baseline" — rested on an instrument that measures no construct, and carry
no evidential weight. Finding #7 stands, now explained: the pair never
shared a construct.

**The corrected comparison (Cell 24, registered):** on the validated
modeled channel (lexicon sens/prec 0.92/0.92 per judge labels),
arch-flat's lower invention is REAL — council 0.722 vs flat 0.167 on
eligible runs, diff CI [−0.833,−0.250] — exactly what the composite regex
said and the void NLI table appeared to deny. The mechanism finding is
unchanged: flat's feature-span fraction is 0.000; it invents nothing
because it says nothing. c17-suppress, c19-gated, and c20-decide remain
indistinguishable from baseline on the validated channel (P24.3 and the
P24.2 rows), so §5's "stop tuning prompts" conclusion survives on better
evidence than it was first written on.
