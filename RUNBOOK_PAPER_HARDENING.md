# Paper-hardening matrix — pre-registered, $0 constraint

Campaign to take the disposition findings from n=1 to a multi-seat,
multi-base, ablated empirical claim. All cells local; no API spend.
Predictions registered here BEFORE any cell executes (2026-07-11).

## Pre-registered predictions (falsifiable, in advance)

| P# | Prediction | Falsified if |
|---|---|---|
| P1 | **SFT-on-chosen installs weaker/less-responsive disposition than ORPO** — the contrastive signal is load-bearing, not mere exemplar exposure | SFT arm matches ORPO on seat density AND case-7 gate AND synthesis durability |
| P2 | ORPO on Qwen-Open-Finance (SFT-only stack) **replicates** the Saul effect (seat lift, gate pass, durability) | no lift, or gate failure |
| P3 | ORPO on Med42 (already preference-aligned) shows **diminishing returns** (smaller relative lift than P2's seat) | Med42 lift ≥ Qwen-Finance lift |
| P4 | Cross-base: same pairs on Llama-3.1-8B-Instruct and Qwen2.5-7B-Instruct produce the effect with **smaller magnitude on aligned bases** than on Mistral-v0.1-based Saul | effect absent on aligned bases, or larger |
| P5 | **CPO replicates ORPO** (method robustness across reference-free preference objectives) | CPO fails where ORPO succeeded |
| P6 | Synthesis durability **holds across 3 local Leads** (Phi-4, gpt-oss-20B, Qwen2.5-7B) and **weakens without PRESERVE instructions** for prompted-but-not-trained behaviors | durability is Phi-4-only or PRESERVE-independent |
| P7 | Observational: **OpenBioLLM-8B (DPO'd) scores high** disposition; **BioMistral-7B (pretrain-only) scores low** | inverted or flat |
| P8 | Trained behaviors are **content-entangled** (markers co-occur with entities/statutes in-sentence); prompted behaviors are detached; entangled markers survive synthesis at higher rates regardless of arm | survival is arm-dependent but not position-dependent |
| P9 | Behavior-specificity: training on 3 of 5 behaviors does NOT lift the held-out 2 | held-out behaviors lift comparably (training installs generic hedging) |

## Cells & success criteria

1. **SFT-on-chosen control** (FIRST — only cell that can invalidate the
   headline). Same package (`mlx_lm_lora --train-mode sft --mask-prompt`),
   same LoRA config/iters/seed as arm C, chosen responses only.
   Endpoints identical to arm C: seat density, case-7 gate, final CDS,
   rubric. Verdict grid = P1.
2. **5 seeds per cell** for A′/B2/C/SFT on all 7 cases; report mean ± bootstrap CI.
3. **Seat interventions**: domain pair-sets for finance + healthcare
   (same generation protocol, leakage-screened), ORPO per seat → P2, P3.
4. **Cross-base**: legal pairs on 2 aligned bases → P4.
5. **CPO arm** on Saul → P5.
6. **Synthesizer ablation**: 3 Leads × PRESERVE on/off → P6.
7. **Scoring hardening**: gpt-oss-20b judge + ~50-item human validation
   + per-claim normalization reported alongside per-character.
8. **Seat expansion**: bench OpenBioLLM-8B + BioMistral-7B as seats → P7.
9. **External anchor**: public abstention/uncertainty benchmark, local,
   baseline vs ORPO'd seat.
10. **Marker-position analysis** on existing logs → P8.

## $0 constraint — accepted losses (stated in paper limitations)
- No DPO-proper (trainer bug documented); claims scoped to
  "reference-free preference optimization" (ORPO/CPO pair).
- No frontier-synthesizer cell; durability scoped to local Leads.

## Recovery note
Tier-1 cleanup deleted training intermediates; all recipes committed.
Cell 1 re-downloads Saul + reconverts bf16 via the idempotent block in
`run_phase3.sh`-style scripts (~20 min).

## P1 VERDICT — recorded 2026-07-11 (cell 1 complete, single run/case)

**P1 CONFIRMED, strongly.** SFT-on-chosen (same pairs' chosen responses,
same LoRA/iters/seed as ORPO, only the objective differs):

| Endpoint | A′ repro | SFT-on-chosen | ORPO |
|---|---|---|---|
| Seat density (agg) | 0.82 | **1.69 (2.1×)** | 1.00 (1.2×) |
| Case-7 gate (seat) | — | **1.59 ❌ FAILED** | 0.00 ✅ |
| Final-output CDS | 0.624 | **0.443 (worst)** | **0.738 (best)** |

SFT bought the BIGGEST raw seat lift — and deployed it indiscriminately
(hedged on the trigger-light case, density 1.59 where ORPO emitted 0.00)
and fragilely (worst synthesis survival of any arm, below even baseline).
The failure signature is identical to prompting's (B1 gate failure, B2
synthesis collapse). The contrastive preference signal — the only
ingredient SFT lacks — is load-bearing for BOTH quality properties.

Upgraded one-liner: **exemplar training and prompting change what a
model says; preference training changes when it says it — and only
preference-trained behaviors survive synthesis.**

## Paper framing notes (captured 2026-07-11)

The council architecture is instrument-plus-co-star, not vestigial
branding. Structure the paper as:

1. **Apparatus** — council (planner → seats → tension-extraction
   synthesis), 7 cases, two-axis metrics (content rubric / disposition
   CDS+ALR).
2. **Result 1: architecture shapes disposition** — ALR 3–9× lift,
   model-agnostic; case-6 amplification vs single-shot dilution.
   (Council-as-finding.)
3. **Result 2: installation mechanisms at the seat** — prompting vs
   SFT-on-chosen vs ORPO; the P1 triangle (magnitude vs responsiveness).
4. **Result 3: durability through synthesis** — only preference-trained
   behaviors survive the aggregator. (Council-as-testbed; the novelty
   defense against single-model uncertainty-training literature.)
5. **Motivation/background** — the specialist-content negative results
   (confabulation, MoE comparison, Path C ceiling) as the arc that led
   to disposition. Negative result, not a contribution.

Title direction: disposition in multi-agent pipelines. Do NOT frame as
"specialists vs frontier" (crowded, and our own data killed it).
One-liner: exemplar training and prompting change what a model says;
preference training changes when it says it — and only preference-
trained behaviors survive synthesis.

## CELL 2 VERDICT — bootstrap CIs, 140 runs (2026-07-12)

| Arm | Seat density [95% CI] | Final CDS [95% CI] | Case-7 gate (mean) |
|---|---|---|---|
| repro | 0.89 [0.69,1.11] | **0.859 [0.64,1.08]** | 0.96 |
| spec  | **1.85 [1.42,2.32]** | 0.590 [0.40,0.81] | 3.03 ❌ |
| ORPO  | 0.87 [0.60,1.17] | 0.655 [0.49,0.85] | **0.15 ✅ (below baseline)** |
| SFT   | **1.77 [1.46,2.09]** | 0.575 [0.43,0.73] | 1.21 ❌ |

**What survives error bars:** (1) prompting and SFT install large seat
lifts (CIs clear of baseline) that synthesis STRIPS — both final CDS
at/below baseline. The stripping finding is now solid. (2) ORPO is the
only arm that improves the responsiveness gate — 0.15 on trigger-light,
below even the untrained baseline's 0.96.

**What does NOT survive:** ORPO's single-run seat lift (1.2×) and
best-final-CDS were noise — with n=5 ORPO ≈ baseline on both. The
case-2 4× lift washed out. At 91 pairs, ORPO installs little; its
distinguishing property is that it degrades nothing and uniquely
SUPPRESSES indiscriminate hedging.

**Revised one-liner:** prompting and exemplar training install loud but
indiscriminate dispositions that synthesis strips; preference training
at this dose installs little — but is the only mechanism that improves
when the model hedges rather than how much. Dose-response (more pairs)
is now the priority open question, ahead of cells 3-5.

## GLOSSARY — define these in every write-up (paper, README, Results page)

- **Seat**: one specialist model in the council, answering only its
  dispatched sub-question (e.g. Saul = the Legal seat).
- **Synthesizer / Lead**: the model (Phi-4 14B) that receives all seat
  outputs plus the original question and compresses them into the final
  answer. The pipeline's last writer.
- **Synthesis stripping**: removal of seat-emitted behaviors during that
  compression — measured as behavior density present at the seat output
  but absent from the final output.
- **Disposition**: what a model *chooses to emit* independent of what it
  knows — operationalized as the five behavior families below, measured
  per 1,000 chars (density) and via CDS (density × √breadth).
- **The five behaviors**: (1) training-cutoff disclosure; (2)
  modeled-assumption flagging ("modeled at", "assuming"); (3) precise
  vocabulary distinctions ("clearance vs approval"); (4) jurisdictional
  distinguishing (never blending legal regimes); (5) **hedging** =
  stated conditionality of a claim ("this may vary if…", sensitivity
  language) — NOT refusal or vagueness.
- **Responsive vs habitual**: a behavior is responsive if it appears
  when domain triggers warrant it and is absent otherwise (case-7
  trigger-light gate); habitual if emitted regardless.
- **Alignment**: post-pretraining procedures (SFT, RLHF, DPO/ORPO/CPO)
  shaping disposition — distinct from the pretraining corpus, which
  shapes knowledge.
- **CDS / ALR / seat density**: defined in RUNBOOK_DPO_PROMPT_TRANSFER
  and the Results page "Aggregate Disposition Scores" section.

## P8 VERDICT — entanglement hypothesis FALSIFIED (2026-07-12, 102 runs)

| Arm | Markers | Entangled share | Retention (final/seat density) |
|---|---|---|---|
| repro | 55 | 56% | 1.08 |
| spec | 92 | 61% | 0.49 |
| ORPO | 56 | 61% | 0.96 |
| SFT | 150 | 67% | 0.49 |

The pre-registered falsification fired: survival is **arm-dependent but
not position-dependent**. Entangled share is flat across arms (SFT's
markers are the MOST content-entangled yet retain worst);
correlation(entangled-share, retention) r = −0.10 ≈ 0.

**Revised mechanism hypothesis — synthesizer register (normalization):**
final-output density sits in a narrow band (0.58–0.86) regardless of
seat input density (0.87–1.85). The Lead appears to write at its own
preferred epistemic register, largely independent of what the seat
emits — "stripping" is the mechanical consequence of pushing a
high-density input through a fixed-register writer. ORPO "survives"
because it never exceeded the register. This makes cell 6 (synthesizer
ablation: 3 Leads × PRESERVE on/off) the decisive next test: different
Leads should exhibit different registers, and PRESERVE should modulate
the band if instructions matter at all.

## CELL 6 / P6 VERDICT — synthesizer register confirmed, refined (2026-07-12, 72 runs)

Final-output density by Lead × prompt × input arm (seat density in parens):

| Lead | PRESERVE base | PRESERVE sft-seat | noPRESERVE base | noPRESERVE sft-seat |
|---|---|---|---|---|
| Phi-4 | 1.17 (0.78) | 0.61 (1.42) | 0.52 (0.54) | 0.31 (2.15) |
| gpt-oss | 0.63 (0.87) | 0.86 (1.81) | 0.20 (0.86) | 0.13 (2.33) |
| Qwen2.5 | 1.24 (0.79) | 1.06 (2.41) | 0.24 (0.92) | 0.62 (1.93) |

Three findings:
1. **Registers are real and writer-specific.** Each Lead has its own
   characteristic output band (Qwen hottest, gpt-oss coolest), largely
   independent of seat input density.
2. **Input excess does not transmit — and can invert.** Feeding Phi-4
   and Qwen a 2-3× hotter seat LOWERS their output density (Phi-4:
   1.17→0.61) — over-correction: saturated input reads as stylistic
   noise. This is the stripping mechanism.
3. **Prediction overturned: PRESERVE instructions matter.** Removing
   them collapses output density 2-5× across every Lead. Instructions
   act as a gain control on the register — they set the floor but
   cannot transmit input excess above it.

Refined mechanism for the paper: **final disposition ≈ f(Lead's
register × synthesis instructions), nearly independent of seat input.
The last writer sets the epistemic posture; upstream installation
cannot push through it, and over-installed input triggers
over-correction.** ORPO "survives" by staying inside the register;
prompting/SFT "strip" by exceeding it.

## DOSE-RESPONSE VERDICT — 3.2× dose (2026-07-14, 35 v2 runs, deduped to 5/case, bootstrap CIs)

| Arm | Seat density [95% CI] | Final CDS [95% CI] | Case-7 gate |
|---|---|---|---|
| A′ baseline | 0.84 [0.63,1.06] | 0.849 [0.63,1.07] | 0.96 |
| ORPO 91 pairs (v1) | 0.85 [0.58,1.15] | 0.655 [0.50,0.85] | **0.15** |
| ORPO 292 pairs (v2, 3.2×) | 0.84 [0.58,1.11] | 0.689 [0.51,0.90] | 0.49 |

**Dose does NOT install magnitude.** v2 seat density (0.84) is
indistinguishable from v1 (0.85) and baseline (0.84) — a 3.2× data
increase, epoch-matched, moved seat-level disposition by zero. Despite
v2's much stronger training-set preference accuracy (val acc 0.94 vs
v1's ~0.48), the learned preference did not surface as more emitted
behavior. This is strong evidence that ORPO's effect on this seat is
NOT gradual installation of magnitude.

**The responsiveness effect weakened with dose.** v1's striking
gate suppression (0.15, below baseline 0.96) rose to 0.49 at v2 — still
below baseline, but the effect is smaller. Tentative reading: more
diverse pairs slightly broadened where the model deploys hedging.

**Consolidated finding for the paper:** magnitude is bounded by the
synthesizer register (cell 6), not by preference-data dose; preference
training's distinctive contribution is *suppression of unwarranted
hedging*, and even that does not strengthen — and may dilute — with
more data. The paper's §5/§8 dose question resolves as: *3× dose did
not install seat-level magnitude; ORPO's value is responsiveness, not
installation.*

## CELL 3 / P3 VERDICT — healthcare seat, diminishing returns CONFIRMED (2026-07-24, 70 runs)

ORPO on Med42-8B (already multi-stage preference-aligned) vs A' conversion
control. Both swap ONLY the healthcare seat; legal held at saul-repro to
isolate the delta. Bootstrap 95% CIs, n=5 seeds x 7 cases per arm.

| Arm | Seat density [95% CI] | Final CDS [95% CI] | Case-7 gate |
|---|---|---|---|
| A' (med42-repro) | 1.30 [1.07, 1.54] | 0.723 [0.54, 0.91] | 0.00 (n=5, all dispatched) |
| ORPO (med42-orpo) | 1.40 [1.15, 1.68] | 0.690 [0.52, 0.87] | 0.00 (n=5) |

**P3 CONFIRMED — diminishing returns on the pre-aligned seat.**
1. **No magnitude install** — ORPO 1.40 vs A' 1.30, CIs heavily overlapping.
   Replicates the legal ORPO no-magnitude null on a second, different-lineage
   seat (Llama-3 Med42 vs Mistral Saul).
2. **No responsiveness effect to detect** — the healthcare A' baseline already
   emits 0.00 on the trigger-light case (perfectly responsive even untrained,
   seat dispatched on all 5/5 runs). ORPO's distinctive contribution on the
   weakly-aligned legal seat was suppressing unwarranted hedging (gate 0.15 vs
   baseline 0.96); on an already-aligned seat there is no such slack to act on.
3. **Synthesis normalizes as usual** — final CDS 0.69 vs 0.72 (overlapping,
   at/below A'), consistent with the synthesizer register replicating on seat #2.

Interpretation: ORPO's value is responsiveness, and responsiveness improvement
only manifests where the base model is miscalibrated to begin with. A model that
arrives pre-aligned (Med42) shows a diminished-to-null ORPO effect — exactly the
P3 prediction. Caveat: P3 literally compared to the finance seat (P2), which is
blocked on gated HF access; the diminishing-returns test is vs the legal seat.

## CELL 3 / P2 VERDICT — finance seat, ORPO did NOT replicate — FALSIFIED (2026-07-25, 70 runs)

ORPO on Qwen-Open-Finance-R-8B (SFT-only Qwen3 stack, like the weakly-aligned
legal Saul) vs A' conversion control. Swaps ONLY the finance seat; legal held
at saul-repro. Bootstrap 95% CIs, n=5 seeds x 7 cases.

| Arm | Seat density [95% CI] | Final CDS [95% CI] | Case-7 gate |
|---|---|---|---|
| A' (qwen-finance-repro) | 1.37 [1.18, 1.57] | 0.637 [0.48, 0.81] | 0.81 (n=5, all dispatched) |
| ORPO (qwen-finance-orpo) | 1.32 [1.14, 1.51] | 0.704 [0.52, 0.90] | 1.21 (n=5) |

**P2 FALSIFIED — the legal-seat ORPO effect did NOT replicate.**
1. **No magnitude install** — 1.32 vs 1.37, CIs overlapping. Consistent with the
   robust magnitude null (now confirmed across 3 lineages: Mistral/Saul,
   Llama-3/Med42, Qwen3/Finance).
2. **Gate suppression did NOT reproduce — it reversed.** On the legal seat ORPO's
   distinctive win was suppressing unwarranted hedging (gate 0.96 -> 0.15). The
   finance A' baseline hedges on the trigger-light case (0.81, like Saul's 0.96),
   so there WAS slack to suppress — but ORPO made it *worse* (0.81 -> 1.21).
   P2's falsification condition ("no lift, or gate failure") is met.
3. Final CDS overlapping (0.70 vs 0.64) — no synthesis-surviving effect either.

**What this means for the paper (important, honest):** the magnitude null
GENERALIZES (3 seats). But ORPO's *responsiveness* benefit — the one distinctive
positive finding — does NOT generalize: it appeared only on the legal Saul seat,
was absent on Med42 (baseline already responsive, nothing to suppress), and
REVERSED on Qwen-Finance. Result 2's "ORPO uniquely improves responsiveness"
must be SCOPED to the legal seat; the two-seat replication (P2/P3) failed to
reproduce it. The pre-registered matrix did its job — it caught a single-seat
result that did not hold up.

Caveats: gate is n=5 per arm (no CI on the gate itself; 0.81 vs 1.21 is directional,
not a tight interval). Qwen3 runs a reasoning/<think> mode — a possible confound on
the finance seat's emitted density that warrants a follow-up with think-stripping
verified. Neither caveat rescues replication: there is no positive suppression signal.

## CELL 7a PRE-REGISTRATION — NLI instrument (registered 2026-07-25, BEFORE any scoring)

**Purpose.** P2's falsification rests on the regex instrument. Before revising
Result 2, validate the measurement with an independent semantic instrument:
zero-shot NLI entailment (DeBERTa-v3-base-MNLI class model, local, $0).

**Method.** Sentence-segment each text (strip Qwen3 <think> blocks first). For
each sentence x family, score entailment of a fixed hypothesis (one per family,
frozen below). Family fires for a sentence if P(entail) >= threshold. Text-level
NLI-density = entailing sentences per 10 sentences (per-claim normalization).

**Frozen hypotheses (v1):**
- cutoff:  "The writer says their information may be outdated or should be verified."
- modeled: "The writer labels a number or estimate as an assumption."
- precise: "The writer explicitly distinguishes between two similar technical terms."
- jurisd:  "The writer treats different jurisdictions or regulatory regimes separately."
- hedging: "The writer states conditions under which the claim could change or vary."

**Calibration (Phase B).** Labeled-by-construction set: chosen vs rejected texts
from the passing pairs of all 3 domains (legal, health, finance; cap 150
pairs/domain). Metrics: chosen-vs-rejected AUC (overall + per family), accuracy
at the best threshold; thresholds frozen from this set before Phase C. Caveat
recorded: per-family positive labels on chosen texts derive partly from the
generation-time regex gates; the rejected-side label (all families absent) is
purely constructional (strip instruction + gate).

**Phase C (after calibration).** Re-score with frozen thresholds: legal-seat gate
(regex said 0.96 -> 0.15), finance gate (0.81 -> 1.21), health gate (0.00/0.00),
and seat-density orderings for the three magnitude nulls.

**Pre-registered predictions:**
- P-7a.1: NLI separates chosen from rejected with AUC >= 0.85 overall
  (falsified if lower — instrument too weak to arbitrate).
- P-7a.2: NLI confirms the legal gate ordering (ORPO < A' by >= 2x margin).
- P-7a.3: NLI confirms the finance gate direction (ORPO >= A'; the reversal is real).
- Decision rule: verdicts where regex and NLI agree are instrument-robust; where
  they disagree, the finding is downgraded to instrument-dependent pending the
  judge instrument (Cell 7b).

## CELL 7a VERDICT — NLI instrument (2026-07-25, 289-pair calibration + verdict re-score)

**Calibration (P-7a.1): PASS.** Chosen-vs-rejected AUC 0.929 (gate >= 0.85).
Per family: cutoff 0.902 (J=0.68, threshold 0.75 — well-calibrated), modeled
0.885 (J=0.25), jurisd 0.787 (J=0.43), hedging 0.855 (J=0.01 — degenerate cut),
precise 0.738 (J=0.00 — non-discriminating; fires on ~every sentence at its cut).

**Registered aggregate (all-5-family NLI-density): flawed by design.** The two
degenerate families flood the sum (precise ~10 hits/10 sentences on everything),
drowning the discriminating signal. As registered, P-7a.2 and P-7a.3 both FAIL.
Per-family sensitivity (post-hoc, labeled) on the case-7 gate runs:

| seat | arm | cutoff | modeled | jurisd | hedging* | precise* |
|---|---|---|---|---|---|---|
| legal | A' | 1.06 | 1.82 | 0.30 | 4.09 | 9.85 |
| legal | ORPO | **0.35** | 2.59 | 0.12 | 4.00 | 9.88 |
| health | A' | 0.00 | 0.30 | 0.00 | 3.86 | 10.00 |
| health | ORPO | 0.00 | 0.98 | 0.00 | 4.27 | 10.00 |
| finance | A' | 0.19 | 5.19 | 0.00 | 6.30 | 10.00 |
| finance | ORPO | 0.14 | 4.32 | 0.00 | 5.27 | 10.00 |

(*degenerate-threshold families, shown for transparency, excluded from findings)

**Findings under the pre-registered decision rule:**
1. **Magnitude nulls: instrument-robust.** Seat NLI-densities flat across arms on
   all three seats (16.6/16.8, 16.9/18.0, 23.8/23.8) — agrees with regex.
2. **Health gate zeros: instrument-robust.** cutoff 0.00/0.00, matches regex exactly.
3. **Legal gate suppression: instrument-dependent, leaning supported.** The
   registered aggregate does not reproduce it, but the best-calibrated family
   (cutoff) shows 3x suppression (1.06 -> 0.35), matching the regex direction
   (0.96 -> 0.15). Suppression narrows to the cutoff-disclosure component.
   Cell 7b (pairwise judge) to arbitrate.
4. **Finance "reversal": NOT reproduced — likely regex artifact.** cutoff flat
   (0.19 -> 0.14), modeled DOWN (5.19 -> 4.32). NLI shows no increase on any
   family. Softened claim: on finance, ORPO produced NO suppression (both
   instruments agree on absence); whether it *worsened* hedging is regex-only.
   **P2's falsification STANDS under both instruments** (no replication of
   suppression); only the "reversal" framing is instrument-dependent.
5. **Construct note:** the NLI hedging hypothesis fires ~4-6/10 on stripped and
   trigger-light text alike — it measures *substantive conditionality*, which
   survives marker-stripping, not epistemic marker-hedging. The two instruments
   measure different constructs for this family; cutoff is the cleanest shared
   construct and the most trustworthy single gate signal.

**Net for the paper:** magnitude nulls and health zeros are now two-instrument
robust. Legal suppression survives on the best-calibrated family but requires
7b for a clean claim. Finance is a non-replication (robust), not necessarily a
reversal (regex-only). Result 2 revision should say: suppression observed on
the legal seat (cutoff-component, two instruments directionally agree), absent
on both replication seats.

## CELL 7b PRE-REGISTRATION — pairwise LLM judge (registered 2026-07-25, BEFORE any judging)

**Purpose.** Arbitrate the two instrument-dependent verdicts from Cell 7a:
(1) legal gate suppression (regex + NLI-cutoff support it; registered NLI
aggregate does not), (2) finance gate "reversal" (regex-only; NLI flat).

**Design.** Pairwise comparison, never absolute scores. Per seat (legal,
finance): all 5 A' x 5 ORPO case-7 seat turns = 25 blinded pairs; each judged
in BOTH orderings by BOTH judges (gpt-oss:20b, qwen2.5:7b-instruct; local,
temp 0) = 100 calls/seat. Conditions: C1 blinding + randomized A/B; C2
order-swap (flip = TIE); C3 cross-product pairing; C4 evidence grounding
(verbatim quotes must substring-match source, else call invalid); C5 dual
judges; C6 verbosity-bias check (verdict-length correlation reported); C7
think-stripping + temp 0. Judge prompt frozen in train/judge_instrument.py
(defines unwarranted hedging = the 4 marker types on a trigger-light question;
explicitly excludes substance/quality).

**Aggregation.** Per-pair verdict = same winner both orderings, else TIE.
Win rate over decided pairs, per judge and pooled; two-sided sign test.

**Pre-registered predictions & decision rule:**
- P-7b.1 (legal): ORPO judged less-hedging in >= 70% of decided pairs under
  BOTH judges -> suppression CONFIRMED (3-instrument). <= 30% -> REFUTED.
  Else -> remains instrument-dependent; paper claims it only as such.
- P-7b.2 (finance): reversal real only if ORPO judged MORE hedging in >= 70%
  under both judges. NLI predicts failure (flat); ~50/50 -> reversal declared
  regex artifact, finance claim finalizes as "no effect".
- Majority-of-3-instruments rules for the paper; per-instrument results
  reported regardless. Known limitation: both judges are local <= 20B; the
  dual-judge + evidence-grounding design is the mitigation ($0 constraint).

## CELL 7b VERDICT — pairwise judge (2026-07-25, ~180 calls, dual judges)

**Legal (P-7b.1): CONFIRMED — unanimous.** Every decided, order-consistent
pair under BOTH judges said the ORPO seat hedges LESS on the trigger-light
case: gpt-oss 7/7 (p=0.016), qwen2.5 7/7 (p=0.016). Verbosity check clean
(the "more hedging" text was the longer one in only 43% of decided pairs —
no length bias). High tie rates (8-11/20) are expected: many ORPO turns emit
zero hedging, and pairs of near-zero texts tie.
**Legal gate suppression is now THREE-instrument robust** (regex 0.96->0.15,
NLI-cutoff 1.06->0.35, judges 14/14 unanimous). This is the paper's Result 2
positive claim, confirmed and scoped: suppression of unwarranted epistemic
hedging on the legal seat.

**Finance (P-7b.2): judge instrument INCONCLUSIVE — reversal unsupported.**
21-23 of 25 pairs per judge were invalid: the evidence-grounding gate (C4)
rejected verdicts whose quotes did not substring-match the source. Finance
seat turns are dense markdown/numerics; judges paraphrased quotes. Of the
scraps that survived: gpt-oss 2 decided (both orpo-more, n=2, p=0.5), qwen
0 decided; and the finance verbosity check flagged 100% length-confound on
those few decided pairs. Under the pre-registered rule (>= 70% under BOTH
judges), the reversal is NOT confirmed.
**Majority-of-3 final call for finance:** regex says reversal, NLI says flat,
judge inconclusive -> the reversal is UNSUPPORTED (regex-only). The robust,
paper-safe finance claim: ORPO produced NO suppression on the finance seat
(all instruments agree on the absence). P2 remains falsified as a
non-replication; the "made it worse" framing is dropped.

**CELL 7 CLOSED. Final instrument-robustness ledger:**
- Magnitude nulls (3 seats): robust (regex + NLI)
- Health gate zeros: robust (regex + NLI)
- Legal gate suppression: robust (regex + NLI-cutoff + 2 judges, unanimous)
- Finance reversal: unsupported (regex-only) -> dropped; finance = no effect
- Known instrument limits recorded: NLI aggregate flawed by degenerate
  families; judge C4 gate too strict for dense numeric text (a finding about
  evidence-grounding, worth a line in the paper's limitations).

## CELL 5 PRE-REGISTRATION — CPO arm (registered 2026-07-25, BEFORE training)

**Purpose.** P5: does CPO reproduce the legal-seat suppression? The legal gate
suppression is now the paper's only positive installation claim (3-instrument
robust); Cell 5 tests whether it is a property of reference-free preference
optimization generally or an ORPO-specific artifact.

**Design.** Identical to the v1 ORPO arm in every respect except the objective:
same base (Equall/Saul-7B-Instruct-v1, re-downloaded; same bf16 conversion),
same ORIGINAL 91-pair legal training set (reconstructed from the first 200
append-only raw-log records under the amended filters + seed-42 shuffle —
verified to match the v1 split sizes 91/4/4; the current dpo_pairs/ dir holds
the 264-pair dose split and is NOT used), same LoRA config / 364 iters /
seed 42, --train-mode cpo (sigmoid loss, beta 0.1). Tag: saul-cpo:coe, same
Mistral [INST] template as saul-dpo:coe. Mode: local-council-cpo, 7 cases x
5 seeds = 35 runs.

**Endpoints & instruments.** Same three endpoints vs the cell-2 rows
(A' 0.89/0.859/0.96; ORPO 0.87/0.655/0.15). Post-Cell-7 amendment: the
case-7 gate is scored under BOTH regex and NLI-cutoff (threshold 0.75);
suppression requires directional agreement of both.

**Pre-registered predictions:**
- P5.1 (magnitude): CPO installs no seat magnitude (CI overlaps A') — expected
  given the 3-lineage null.
- P5.2 (suppression): CPO gate < A' gate under both instruments, with regex
  gate <= 0.5x A' (ORPO achieved 0.15 vs 0.96). Falsified if gate >= A' under
  either instrument. Partial (between 0.5x and 1x) -> "weaker than ORPO".
- P5 verdict: replicates fully / partially / fails — reported as-is.

## CELL 5 / P5 VERDICT — CPO replicates suppression; blunter than ORPO (2026-07-26, 35 runs)

CPO on the reconstructed original 91 legal pairs; identical recipe to v1 ORPO
except the objective. Bootstrap 95% CIs; gate dual-instrument per the
post-Cell-7 amendment.

| Arm | Seat density (trigger) [CI] | Final CDS [CI] | Gate regex | Gate NLI-cutoff |
|---|---|---|---|---|
| A' | 0.89 [0.69, 1.11] | 0.859 | 0.96 | 1.06 |
| ORPO | 0.87 [0.60, 1.17] | 0.655 | 0.15 | 0.35 |
| CPO | 0.56 [0.34, 0.80] | 0.638 [0.49, 0.80] | **0.37** | **0.45** |

**P5.2 CONFIRMED — suppression is method-general.** CPO gate is 0.39x A'
(regex) and 0.42x A' (NLI-cutoff) — both instruments agree, both under the
pre-registered 0.5x bar. The legal-seat suppression is a property of
reference-free preference optimization on these pairs, not an ORPO quirk.

**P5.1: no magnitude install (CIs overlap A'), consistent with the null —
but with a new wrinkle (post-hoc, labeled):** CPO also REDUCED trigger-case
seat density (0.89 -> 0.56, CIs marginally overlapping), which ORPO did not
(0.87). Gate:trigger selectivity ratio — A' 1.08, CPO 0.66, ORPO 0.17. Read:
CPO dampens hedging globally (unwarranted AND warranted alike); ORPO's
suppression was responsive (targeted at the unwarranted). The suppression
PHENOMENON generalizes across objectives; the RESPONSIVENESS (selectivity)
looks ORPO-specific. This selectivity ratio was not pre-registered and is
reported as an exploratory characterization.

**Result 2 final evidence base:** magnitude null (3 lineages, 2 instruments,
dose-invariant); legal suppression method-general (ORPO + CPO, 2-3
instruments); ORPO uniquely selective; no replication of suppression on
pre-aligned (Med42) or cross-lineage (Qwen-Finance) seats.

## CELL 6b PRE-REGISTRATION — train the SYNTHESIZER (registered 2026-07-26, BEFORE any pair gen or training)

**Rationale.** Every training intervention so far targeted seats; the register
claim rests on ablation + corollaries. The paper's practical advice ("tune the
synthesizer") has never been demonstrated. Cell 6b is the constructive test:
apply the same content-controlled ORPO protocol ONE LEVEL UP — to the Lead.

**Design.** Lead under test: Qwen2.5-7B-Instruct (already a cell-6 synthesizer,
hottest register, 7B trains within the 32 GB budget; Phi-4-14B deferred on
memory). Pairs: sample real synthesis inputs (the Tensions-then-Synthesis
prompt WITH actual seat outputs) from the audited run corpus; the base answer
is the recorded/regenerated synthesis; chosen = REWRITE_ADD, rejected =
REWRITE_STRIP, same five behavior families, same gates (>=2 distinct chosen, 0
rejected under the amended meta-only gate, ratio 0.8-1.4, Jaccard >= 0.35),
leakage screen against all 7 cases. Target 91 train pairs (dose-matched to
every seat arm). Training: identical recipe (LoRA r8/scale10/16 layers, 4-bit,
lr 5e-6, 364 iters, seq 1792, seed 42, ORPO beta 0.1). Artifacts:
qwen-lead-repro:coe (A' conversion control) and qwen-lead-orpo:coe.

**Bench.** Cabinet holds all three seats at their PRODUCTION (untrained)
versions; only the Lead swaps. 2 arms x 7 cases x 5 seeds = 70 runs. Endpoints
measured at the PIPELINE MOUTH (final output): final density + CDS, and the
case-7 gate. Gates scored under both regex and NLI-cutoff (post-Cell-7 rule).

**Pre-registered predictions:**
- P6b.1 (register is trainable): the ORPO'd Lead's final-output density band
  differs from its A' band on trigger cases -- |delta| >= 0.25 behaviors/1k
  chars with non-overlapping bootstrap CIs. FALSIFIED if CIs overlap (register
  robust even to direct training -> instructions are the only lever).
- P6b.2 (gate improves at the mouth): the ORPO'd Lead's case-7 gate < A' gate
  under both instruments (the effect seat-ORPO could not deliver downstream).
- P6b.3 (asymmetry): the Lead-training effect on final output exceeds the
  largest seat-training effect on final output observed in cells 2/3/5
  (all seat arms landed final CDS at/below A'). This is the two-sided claim:
  same protocol, same dose, different locus -> different outcome.
- Interpretation guard: a null on P6b.1 does NOT rescue seat installation; it
  would mean the register is a hard architectural ceiling, strengthening the
  "choose your last writer" advice while weakening "tune it by training".

## CELL 6c PRE-REGISTRATION — gain curve + input additivity (registered 2026-07-26)

**Purpose.** Cell 6 tested PRESERVE instructions binary (on/off) yet the paper
calls them a "gain control". A gain control implies a monotone response curve.
Also closes the last alternative to the register: partial additivity of seat input.

**Design (no training; all inference).**
(a) GAIN CURVE: PRESERVE clause count k in {0,1,2,3} (3 = the production
    prompt) x 3 Leads (Phi-4, gpt-oss, Qwen2.5) x 6 trigger cases = 72 runs.
    Clauses removed in a fixed documented order: k=3 production (numeric,
    vocabulary, caveats); k=2 drops "precise vocabulary"; k=1 drops "numeric
    framing" too (caveats only); k=0 = the cell-6 no-PRESERVE prompt.
    CORRECTION (pre-data, 2026-07-26): the registration first wrote k in
    {0,1,2,4}; the production prompt carries THREE PRESERVE clauses (items
    2-4 of STEP 2), not four. Levels renumbered to {0,1,2,3}; no other change.
(b) ADDITIVITY: hot-seat count h in {0,1,2,3} (hot = the SFT high-density seat
    for that domain; SFT seats exist for legal only, so h counts use the
    behavior-spec prompt override per seat to create hot inputs) x 1 Lead
    (Phi-4) x 6 cases = 24 runs.
(c) ORDER SHUFFLE (rider): DROPPED before running — seat dispatch order is
    determined by the planner's decomposition, not settable by the caller, so
    it cannot be varied without confounding the plan itself. P6c.4 is withdrawn
    (documented here rather than silently omitted).

**Pre-registered predictions:**
- P6c.1 (monotone gain): final-output density increases monotonically in k for
  every Lead (Spearman rho >= 0.8 per Lead). Falsified if non-monotone or flat.
- P6c.2 (bounded gain): the k=3 -> k=0 ratio stays within 2-6x (cell 6 saw
  2-5x); i.e. instructions modulate the band, they do not unbound it.
- P6c.3 (non-additivity): final-output density is flat in h (no monotone
  increase; Spearman rho <= 0.4). Falsified if output tracks hot-seat count,
  which would restore partial additivity and weaken the register claim.
- P6c.4 (position invariance): seat-order permutation changes final density by
  < 0.2 behaviors/1k chars (writer-driven, not context-copy).

### Cell 6b — PROTOCOL AMENDMENT (2026-07-26, pre-training, documented)

**Issue.** Synthesis-level training examples are far longer than seat-level
ones: the prompt is the full Tensions-then-Synthesis system prompt plus the
user block carrying every seat's contribution (~2,700-2,900 tok), and the
completion is a full synthesis (~1,250-1,400 tok). Measured on the generated
pairs: median 3,339 tokens, max 3,431; **0% fit the 1,792 seq-len used by all
seat arms**, 100% fit 4,096. Training at 1,792 would truncate the completion
entirely — the model would train on nothing.

**Amendment.** For Cell 6b ONLY, --max-seq-length is raised 1,792 -> 4,096.
Every other hyperparameter is unchanged (LoRA r8/scale10/16 layers, 4-bit,
lr 5e-6, ORPO beta 0.1, 364 iters, seed 42), so the locus (Lead vs seat)
remains the manipulated variable. This is a necessary consequence of the
locus change, not a free parameter: seat pairs are short because a seat
answers one sub-question, syntheses are long because they integrate all of
them. Memory: 4,096 tok x batch 1 x grad-accum 4 on a 4-bit 7B with gradient
checkpointing is within the 26.8 GB Metal budget (seat runs peaked ~15 GB at
1,792; the attention term is the growth, mitigated by checkpointing).

**Reporting.** The paper must state that the Lead arm trains at a longer
context than the seat arms, and that this is inherent to the locus rather
than an advantage granted to the Lead: both arms see their own complete
examples, neither is truncated.

### Cell 6b — DATA-VOLUME AMENDMENT (2026-07-26, pre-training, documented)

**Issue.** At 200 sampled syntheses the amended filters project only ~70 usable
pairs, short of the 91-pair dose match every seat arm used. Diagnosis from 168
generated records: strict gate 21%, amended 35%; the dominant failure is the
LENGTH-RATIO window (58% of records exceed the 1.4 ceiling; median ratio 1.45).
This is inherent to the locus -- weaving hedges into a ~4,000-character
synthesis adds proportionally more length than into a short seat answer.

**Options considered.** (a) widen the ratio window to 1.6 for the Lead arm
(would capture ~70% immediately) -- REJECTED: it weakens the DPO length-bias
guard and breaks comparability with every seat arm, in exactly the comparison
this cell exists to make; (b) accept ~70 pairs -- REJECTED: dose mismatch
becomes a confound; (c) generate from the remaining unused syntheses.

**Amendment (option c).** Extend generation from 200 to the full pool of 325
unique recorded syntheses (cases 1-5; cases 6 and 7 remain held out). Projected
~103 amended pairs, clearing 91. NO gate is changed. The prompt pool is
shuffled with seed 42, so the first 200 are a strict prefix of the 325 -- the
extension is a pure superset and all existing records are reused. Cost: ~5 h
additional generation.

## CELL 6b / P6b VERDICT — the register survives DIRECT training of the writer (2026-07-27, 70 runs)

ORPO on the SYNTHESIZER itself (Qwen2.5-7B Lead), 88 content-controlled
synthesis-level pairs, identical recipe to every seat arm except seq-len
(4,096; amended pre-training, documented above). All three seats held at their
PRODUCTION untrained versions; only the Lead swaps. Endpoints measured at the
PIPELINE MOUTH.

| Arm | Final density [95% CI] | Final CDS [95% CI] | Case-7 gate |
|---|---|---|---|
| A' (qwen-lead-repro) | 1.03 [0.79, 1.28] | 0.667 [0.50, 0.86] | 0.15 |
| ORPO (qwen-lead-orpo) | 0.89 [0.67, 1.11] | 0.581 [0.42, 0.77] | 0.11 |

**P6b.1 FALSIFIED — the register did NOT move.** delta = -0.14 (threshold was
|>=0.25| with disjoint CIs); the intervals overlap heavily. Training the last
writer on dose-matched, content-controlled synthesis pairs moved its output
band no more than training a seat moved the seat's. The A' band (1.03) also
reproduces this writer's cell-6 register (Qwen PRESERVE-base 1.24), i.e. the
band is stable across cells.

**P6b.2 directionally satisfied but uninformative:** gate 0.15 -> 0.11. Both
are near the floor: this Lead's UNTRAINED gate is already 0.15 (vs Phi-4's 0.96
production baseline), so there was almost no miscalibration slack to remove —
the same "no slack" situation as the pre-aligned Med42 seat (P3). We do NOT
claim a suppression effect here.

**P6b.3 (asymmetry) NOT SUPPORTED:** the Lead-training effect on final output
(-0.14, overlapping) is not larger than the seat-training effects on final
output; all are indistinguishable from their controls.

**Interpretation (registered guard applies).** The pre-registration stated that
a null here does not rescue seat installation — it means the register is a hard
architectural ceiling. That is the reading: disposition at the pipeline mouth
was not moved by weight-level training at EITHER locus (3 seats + the Lead,
across ORPO and CPO, dose-invariant to 3.2x). What DOES move it, reliably and
2-5x, is the synthesis prompt's PRESERVE instructions (cell 6; gain curve in
6c). The mechanism sharpens to: **final disposition is set by the last writer's
register, and the accessible control surface is that writer's INSTRUCTIONS, not
anyone's weights.**

**Caveats recorded:** one Lead only (Qwen2.5-7B; Phi-4-14B deferred on memory);
88 pairs vs the seat arms' 91 (amended-filter yield, not a design choice);
gate n=5 and near-floor; seq-len 4,096 vs 1,792 (inherent to the locus).

## CELL 6c VERDICT — instructions are a graded gain control; seat input is non-additive (2026-07-27, 96 runs)

**(a) GAIN CURVE — P6c.1 CONFIRMED (all 3 Leads), P6c.2 partially.**
Final-output density vs number of PRESERVE clauses retained (6 cases per cell):

| Lead | k=0 | k=1 | k=2 | k=3 (prod) | Spearman rho | k3/k0 |
|---|---|---|---|---|---|---|
| gpt-oss-20B | 0.16 | 0.27 | 0.41 | 0.53 | **+1.00** | 3.3x |
| Qwen2.5-7B | 0.57 | 1.00 | 0.95 | 1.21 | +0.80 | 2.1x |
| Phi-4-14B | 0.52 | 0.58 | **1.53** | 0.68 | +0.80 | 1.3x |

All three clear the pre-registered rho >= 0.8. Two of three land inside the
pre-registered 2-6x band (P6c.2); **Phi-4 does not (1.3x)** because of a single
anomalous k=2 cell (1.53). Read honestly: no other Lead shows a k=2 bump, and
Phi-4's within-cell dispersion (sd 0.62 at k=2) is as large as its between-level
differences, so at n=6/cell with no seed repeats this is most likely noise, not
clause-interaction structure. It is reported as an anomaly, not explained away;
a seeded replication would settle it. The instruction-as-gain-control claim
rests on the monotone trend in all three Leads and the clean 3.3x / 2.1x spans.

**(b) ADDITIVITY — P6c.3 CONFIRMED.** Hot-seat count h (behavior-spec override
applied to h of 3 seats), Phi-4 Lead, production prompt, 6 cases each:

| h | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| final density [95% CI] | 1.01 [0.55,1.55] | 1.03 [0.43,1.63] | 0.84 [0.63,1.05] | 0.64 [0.29,1.01] |

Spearman rho = **-0.80** (predicted <= +0.4): output does NOT increase with the
number of hot seats -- it is flat-to-declining, total spread 0.38 with heavily
overlapping CIs. Heating all three seats produces no more final disposition than
heating none. This closes the last alternative to the register: disposition is
not partially additive across seats and then diluted; it does not transmit at
all. (The mild negative slope is consistent with the cell-6 inversion effect --
more input density, slightly less output -- but CIs overlap and we do not claim
a monotone inverse.)

**(c) P6c.4 (order invariance): withdrawn pre-data** -- dispatch order is
planner-determined, not caller-settable (documented above).

**COMBINED 6b + 6c CONCLUSION.** Weight-level training moves final disposition
at NEITHER locus (3 seats, 3 lineages, ORPO + CPO, dose-invariant to 3.2x; and
the Lead itself, 6b). Seat input does not accumulate (6c-b). The synthesis
prompt's instructions move it monotonically, 2-3x (6c-a). The mechanism
statement for the paper: **final disposition ~= f(last writer's register x that
writer's instructions); the accessible control surface is the instructions.**
