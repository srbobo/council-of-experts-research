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
