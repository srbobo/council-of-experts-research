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

## CELL 7c — PER-FAMILY, SEAT-MATCHED DECOMPOSITION (2026-07-27, no new runs)

**Motivation.** The composite metric sums five behavior families, but they are
not uniformly distributed across seats. Scoring all five on one seat (as the
headline tables do) lets the composite be dominated by training-cutoff
disclosure and understates families that live elsewhere. Re-decomposition of
the existing 628 runs; no new inference.

**Family ownership (untrained baseline density per seat):**

| family | healthcare | legal | finance | owner |
|---|---|---|---|---|
| cutoff | 0.85 | 0.68 | 0.51 | universal |
| modeled | 0.00 | 0.00 | 0.25 | **finance** |
| hedging | 0.38 | 0.02 | 0.33 | **healthcare/finance** |
| jurisd | 0.05 | 0.14 | 0.13 | legal (weak) |
| precise | 0.02 | 0.00 | 0.01 | **BELOW DETECTION** |

**Findings.**

1. **Magnitude null is FAMILY-GENERAL (strengthens the paper).** Testing each
   family on the seat that owns it, ORPO moves none of them: finance/modeled
   0.40 [0.31,0.49] -> 0.34 [0.24,0.45]; healthcare/hedging 0.33 -> 0.26;
   legal/jurisd 0.14 -> 0.18. All CIs overlap. The 6b Lead-training null is
   likewise null in all four detectable families. The null is NOT a
   cutoff artifact.

2. **Prompt/SFT installation is MULTI-FAMILY (strengthens the paper).** On the
   legal seat: cutoff 0.68 -> 1.46 (prompt) / 1.21 (SFT); modeled 0.00 -> 0.27
   (SFT); hedging 0.02 -> 0.23 (SFT). Exemplar training installs behaviors the
   seat did not previously emit at all. Side effect worth reporting: SFT
   SUPPRESSED jurisdictional distinguishing (0.14 -> 0.02) while installing the
   others -- installation is not uniformly additive across families.

3. **NEW: synthesis stripping is NOT uniform across families.** Retention
   (final density / owner-seat density) at baseline:

   | family | seat | final | retention |
   |---|---|---|---|
   | cutoff | 0.68 | 0.47 | **0.69 (stripped)** |
   | hedging | 0.38 | 0.29 | 0.76 (partly stripped) |
   | modeled | 0.25 | 0.27 | **1.05 (survives)** |
   | jurisd | 0.14 | 0.17 | **1.25 (survives)** |

   The families that survive are the CONTENT-BEARING ones -- a modeled number
   ("modeled at $8,000") and a jurisdictional distinction carry substance the
   synthesizer needs, whereas cutoff disclosure is meta-commentary it can drop
   without losing content. This is a family-level version of the entanglement
   idea that P8 falsified at the ARM level: retention does not split by arm or
   marker position, but it DOES split by whether the family carries content.
   Reported as an observation from existing data, not a pre-registered test.

4. **QUALIFIED: gain-curve monotonicity is an AGGREGATE property.** Pooled over
   3 Leads, no single family is monotone in k: cutoff +0.40, modeled +0.60,
   hedging +0.40, jurisd -0.80. The composite rises because three families
   trend up jointly. "Instructions are a graded gain control" is fair for the
   composite; it is NOT true that each behavior is monotonically controllable.

5. **Non-additivity holds where there is signal:** cutoff rho -0.80, hedging
   rho -1.00; modeled/jurisd flat (rho 0.00) at densities too low to rank.

6. **`precise` is below detection on every seat (0.00-0.02)** and was the worst
   family for the NLI instrument too (AUC 0.738, Youden J = 0.00). Two
   independent instruments fail it. Recommendation: report the four detectable
   families and state that vocabulary-precision was operationalized but not
   measurable in these cases -- either the cases do not provoke it or the
   construct is not detectable as a surface feature.

**Net effect on the paper.** Scope language must change from "five behavior
families" to "four detectable families, composite dominated by cutoff
disclosure." Two headline claims (the magnitude null; prompt/SFT installation)
are STRONGER than previously stated -- they are family-general, not cutoff
artifacts. One (gain-curve monotonicity) must be scoped to the composite. One
new finding (family-dependent stripping) should be added to Result 3.

## CELL 8 PRE-REGISTRATION — architecture comparison (registered 2026-07-27, BEFORE any runs)

**Motivation.** Result 1 compares the council against NO orchestration only; it
never compares it against other multi-agent architectures. Cell 6c makes the
gap urgent: stripping PRESERVE collapses the full council to 0.16 final density
(BELOW gpt-oss single-shot's 0.19), so the "3-9x architectural lift" may be
attributable to the synthesis PROMPT rather than the multi-agent topology.
Existing data hints the council's real advantage is RESPONSIVENESS, not
magnitude -- gpt-oss single+spec reaches 0.66 density but fails the gate at
1.27, while gpt-oss-as-council reaches 0.78 and gates at 0.00 -- but those gate
cells are n=1 and cannot support a claim.

**Arms (all gpt-oss-20B in every role, so architecture is the ONLY variable;
7 cases x 5 seeds each).**
1. `arch-single`        -- single-shot, neutral prompt (existing baseline)
2. `arch-single-spec`   -- single-shot + behavior-spec prompt (unconditional
                           disposition instruction, no multi-agent structure)
3. `arch-council`       -- full council: planner -> 3 seats -> Tensions-then-
                           Synthesis with CONDITIONAL PRESERVE instructions
4. `arch-flat`          -- same 3 seats, naive merge prompt ("here are three
                           answers, write one"), NO tension extraction, NO
                           PRESERVE: multi-agent structure WITHOUT the
                           conditional instruction
5. `arch-debate`        -- 2 rounds: seats answer, see each other's answers,
                           revise; then the same naive merge as arm 4
6. `arch-refine`        -- single model, draft -> self-critique -> revise
                           (self-critique as a substitute for specialists)

**Endpoints.** Final-output density and CDS on the 6 trigger cases; the case-7
gate (n=5 per arm, the discriminating measure this cell exists to power).
Bootstrap 95% CIs throughout.

**Pre-registered predictions.**
- P8.1 (magnitude is NOT the council's edge): arm 3 does not exceed arm 2 on
  trigger-case density by a margin with disjoint CIs. Falsified if the council
  clearly out-produces the prompted single model.
- P8.2 (the council's edge is RESPONSIVENESS): arm 3's case-7 gate is lower
  than arm 2's by >= 2x. Falsified if the gates are comparable or inverted.
- P8.3 (the conditional instruction is the active ingredient): arm 4 (multi-
  agent, unconditional/no PRESERVE) gates no better than arm 2 and produces
  less magnitude than arm 3 -- i.e. multi-agent structure alone buys neither.
  Falsified if arm 4 matches arm 3 on both endpoints.
- P8.4 (exploratory, no directional prediction): where do debate and
  self-refine land on the magnitude/gate plane? Reported descriptively.

**Consequence for the paper, stated in advance.** If P8.1-P8.3 hold, Result 1
must be REWRITTEN: the architectural lift is not a property of multi-agent
topology per se but of a conditional preservation instruction applied over
real specialist signal, and the council's distinctive contribution is
responsiveness rather than magnitude. If P8.2 is falsified (single+spec gates
as well as the council), the architecture claim largely dissolves and the
paper's contribution narrows to the register mechanism. Both outcomes are
reportable; the second is the one that would cost us most, which is why it is
registered here before the runs.

## CELL 8 VERDICT — architecture comparison, 210 runs (2026-07-28)

gpt-oss-20B in EVERY role, so orchestration shape is the only variable.
7 cases x 5 seeds x 6 arms; bootstrap 95% CIs; zero failures.

| architecture | specialist signal / instruction | trigger density [95% CI] | case-7 gate [95% CI] |
|---|---|---|---|
| single-shot | none / none | 0.14 [0.09, 0.19] | 0.00 [0.00, 0.00] |
| flat merge | 3 agents / naive | 0.16 [0.11, 0.22] | 0.06 [0.02, 0.11] |
| debate (2 rounds) | 3 agents + revision / naive | 0.16 [0.12, 0.20] | 0.05 [0.00, 0.10] |
| self-refine | self-critique / none | 0.08 [0.05, 0.12] | 0.00 [0.00, 0.00] |
| single + spec | none / UNCONDITIONAL | 0.50 [0.41, 0.60] | **0.15 [0.08, 0.22]** |
| **COUNCIL** | 3 agents / **CONDITIONAL** | **0.57 [0.45, 0.71]** | **0.00 [0.00, 0.00]** |

**P8.1 SUPPORTED — magnitude is NOT the council's edge.** Council 0.57 vs
single+spec 0.50, CIs overlapping. A single prompted model matches the whole
council on how much disposition it emits.

**P8.2 CONFIRMED — responsiveness IS the edge.** Council gate 0.00 [0.00,0.00]
vs single+spec 0.15 [0.08,0.22]: disjoint intervals, and the council emitted
ZERO unwarranted disposition on all five trigger-light runs.

**P8.3 SUPPORTED — multi-agent structure alone buys neither.** Flat merge
(same three specialists, naive merge prompt) reaches 0.16 trigger density,
statistically indistinguishable from single-shot's 0.14 and disjoint from the
council's 0.57, while gating WORSE than the council (0.06 vs 0.00).

**P8.4 (exploratory) — more agent interaction does not help.** Debate, with two
rounds of specialists revising after seeing each other, lands at 0.16/0.05 —
essentially identical to a one-shot naive merge (0.16/0.06). Self-refine is the
weakest arm on magnitude (0.08), BELOW plain single-shot: self-critique
compresses and firms up prose, removing disposition rather than adding it.

**Mechanism.** Disposition that is both substantial and appropriately gated
requires the CONJUNCTION of (a) real specialist signal and (b) a CONDITIONAL
preservation instruction over it ("IF a specialist flagged X, propagate X").
Signal without the conditional instruction (flat, debate) yields single-shot
levels. The instruction without signal (single+spec) yields the magnitude but
fires unconditionally, hedging where nothing warrants it. Only the council has
both, and only the council occupies the high-magnitude/zero-gate quadrant.

**CONSEQUENCE FOR RESULT 1 (registered in advance, now due).** The paper's
"architecture lifts disposition 3-9x" is imprecise: multi-agent topology per se
lifts almost nothing (flat 0.16 vs single 0.14). The lift comes from the
conditional preservation instruction applied over specialist output, and the
council's distinctive contribution is RESPONSIVENESS, not magnitude. Result 1
is to be rewritten accordingly. Cell 6c's k=0 collapse (full council, PRESERVE
stripped -> 0.16) is the same finding from the other direction and should be
presented alongside.

### Numbering note (2026-07-28)
The standalone prediction **P8** (content-entanglement, registered in the
original P1-P9 set, falsified by Cell 10) predates and is DISTINCT from Cell
8's **P8.1-P8.3** (architecture comparison, all held). The shared number is a
coincidence of the runbook's two numbering layers (prediction set vs. cell
number); both labels are retained as registered, with this note and matching
disambiguation on the website glossary.

## CELL 11 PRE-REGISTRATION — pipeline-mouth calibration reward (registered 2026-07-28, before any code or runs)

**Question.** Is the synthesizer's register robust to weight-level training
*per se*, or only to the training we ran? Cell 6b's null (Lead ORPO did not
move the register) used (a) an offline, off-policy pair corpus, (b) a
DENSITY-shaped reward (dense beats sparse), and (c) supervision at the
response level, never at the pipeline's mouth. The CollabLLM mechanism
(arXiv:2502.00640) suggests exactly these three properties are what make
behavioral installation fail: response-level rewards install locally-good,
globally-wrong behavior. Cell 11 re-runs the 6b question with all three
corrected and NOTHING else changed.

**Design — best-of-n pipeline distillation (feasible RL surrogate).**
- Locus: Qwen2.5-7B-Instruct as Lead (same model, trainer, LoRA config,
  seed, and dose cap as Cell 6b, for a clean two-cell contrast).
- On-policy sampling: run the full council on each training prompt; run
  upstream phases ONCE, then sample n=6 syntheses at temperature 0.8. In
  this pipeline the synthesis IS the final output, so these are on-policy
  samples of the pipeline's mouth.
- Calibration reward, computed per sampled final output by the frozen
  composite instrument (regex canonical, NLI cross-check):
    trigger-heavy prompt:  R = +CDS(final)
    trigger-light prompt:  R = -density(final)
  The conditionality lives across the prompt distribution: the same weights
  are rewarded for disposition where warranted and penalized for it where
  not. This is the reward shape Cell 8 identified as the target property.
- Pairs: chosen = argmax R, rejected = argmin R per prompt; discard prompts
  where the margin is below the 6b length-ratio and margin gates. Training
  corpus: freshly generated prompts, construction-labeled trigger-heavy vs
  trigger-light (~70/30), all seven bench cases HELD OUT.
- Dose match: cap at 88 train pairs (6b's realized dose). ORPO, LoRA r8 /
  scale 10 / 16 layers, lr 5e-6, seed 42, seq 4096 (6b amendment carried).
- Bench: 7 cases x 5 seeds x 2 arms = 70 runs.
    Arm A  cell11 Lead, production prompt (k=3)
    Arm B  cell11 Lead, NO PRESERVE (k=0)   <- the decisive arm
  Baselines from existing data: stock Qwen Lead at k=3 and k=0 (Cell 6c
  gain curve) and 6b's density-rewarded Lead at k=3.

**Predictions (registered before any runs).**
- P11.1 (register movable under corrected reward): Arm B (k=0) exceeds the
  stock Lead's k=0 trigger density, bootstrap CIs disjoint. FALSIFIED IF
  CIs overlap — the register survives even on-policy pipeline-mouth
  calibration training at the feasible scale.
- P11.2 (calibration, not loudness, is what installs): Arm B's trigger-
  light gate remains at or below the stock k=3 gate. FALSIFIED IF the gate
  rises alongside density — the reward installed indiscriminate loudness,
  the same failure mode the pipeline strips from seats.
- P11.3 (reward shape was 6b's binding constraint): Arm A exceeds 6b's
  density-rewarded Lead at k=3, CIs disjoint. FALSIFIED IF the two are
  indistinguishable — reward shape was not the limiting factor and the
  6b null stands on trainer/locus/dose grounds alone.
- P11.4 (exploratory, no directional prediction): does the k=0 -> k=3 gain
  shrink for the cell11 Lead (instructions made redundant by weights) or
  persist multiplicatively?

**Registered consequences.**
- If P11.1 AND P11.2 hold: the equation's robustness clause is AMENDED,
  and the amendment is the finding — the register is movable, but only by
  rewards that are (a) calibration-shaped and (b) computed at the
  pipeline's mouth, on-policy. The four earlier training nulls are then
  reframed as one mechanism (wrong reward, wrong locus of measurement),
  and the thesis becomes "instructions, or calibration-shaped on-policy
  reward at the last writer."
- If P11.1 is FALSIFIED: the robustness clause is STRENGTHENED — the
  register survives the strongest feasible analogue of the CollabLLM
  mechanism, and "the accessible control surface is the instructions"
  hardens materially. Reported as a headline negative result either way.
- Mandatory caveat in either case: best-of-n distillation is a surrogate
  for full on-policy RL (no PPO/GRPO at this scale); a frontier-scale RL
  run could still differ. This limitation is registered now so it cannot
  be softened post hoc.

## CELL 8B PRE-REGISTRATION — register provenance / alignment lineage (registered 2026-07-30, before any runs)

**Question.** Where do registers come from? Model selection is the only
intervention that has ever moved the register upward (bands span 3.3x across
Leads). If registers are installed by the *builder-scale preference
alignment* a model shipped with, lineage should predict register — and that
would both explain why our 49-88-pair LoRA doses cannot compete and tell a
practitioner what to read off a model card when selecting a Lead.

**Scope amendment (pre-data).** The original P7 framed this comparison with
the two biomedical models as SEATS. No seat runs were ever executed. Under
the register focus the informative role is the LEAD (synthesis register is
what the pipeline's mouth inherits), so P7's seat framing is RETIRED pre-data
and replaced by the Lead-role predictions below. Recorded here so the trail
shows the reframe preceded all data.

**Design.** Each candidate plays Lead (planner + synthesis) over the
production seats, production k=3 prompt, 7 cases x 5 seeds = 35 runs each:
  - OpenBioLLM-8B   (Llama-3 base, DPO/preference-aligned lineage)
  - BioMistral-7B   (Mistral base, continued-pretrain lineage, no pref stage)
  - Mistral-7B-Instruct-v0.3 (generic instruct control, same family as
    BioMistral — partially splits family from lineage)
  - OPTIONAL: Llama-3-8B-Instruct (gated; pending HF license acceptance —
    completes the 2x2 if unlocked, registered as optional now)
Community Q4_K_M GGUFs; chat template verified per family before any run
(the Med42 template lesson). 105 runs core (140 with optional).

**Registered confound.** OpenBioLLM vs BioMistral differ in base family and
size as well as lineage; the Mistral-instruct control mitigates but does not
eliminate this. No causal claim will be made beyond what the 2x2 supports.

**Predictions.**
- P8b.1: the preference-aligned lineage (OpenBioLLM) shows a HIGHER Lead
  register than the continued-pretrain lineage (BioMistral), bootstrap CIs
  disjoint. FALSIFIED IF overlapping or inverted.
- P8b.2: BioMistral does NOT exceed Mistral-7B-Instruct — continued domain
  pretraining does not raise register (domain knowledge != disposition).
  FALSIFIED IF BioMistral sits clearly above its instruct cousin.
- P8b.3 (exploratory): trigger-light gates per model; no directional claim.

**Consequences.** If P8b.1+P8b.2 hold: registers originate in the
preference-alignment stage, not domain pretraining — model SELECTION guidance
becomes concrete (prefer preference-aligned Leads), and the failure of our
small preference doses reads as a scale gap, not a mechanism gap. If P8b.1
is falsified: lineage does not predict register and register provenance
remains open; reported as a negative result.

## CELL 12 PRE-REGISTRATION — register portability via weight interpolation (registered 2026-07-30, before any runs)

**Question.** Is a register PORTABLE — can it be transplanted into the Lead
by weight-space interpolation with a high-register donor, with no training
at all? This is the cheapest untested non-prompt register modification, and
mechanistically distinct from gradient methods: instead of asking a 49-pair
LoRA to find disposition, copy the parameters of a model that already
expresses it.

**Design (stage-gated).**
- Stage 0 — donor screen: candidate Qwen2.5-7B-architecture fine-tunes
  benched as Lead, screen grade (6 trigger cases x 2 seeds = 12 runs each).
  GO/NO-GO (registered): proceed only if some donor's screen band is >=
  1.3x the stock band (>= ~1.35 vs 1.03). If no donor qualifies, the screen
  itself is reported and the merge phase does not run — that outcome would
  itself say same-arch fine-tunes cluster near the base register.
- Stage 1 — SLERP merges at alpha in {0.25, 0.5, 0.75} between stock
  Qwen2.5-7B-Instruct and the winning donor (mergekit, CPU, disk-staged as
  in Cell 11); convert -> Q4_K_M -> ollama.
- Stage 2 — bench: each merged Lead + the donor at full grade (7 cases x 5
  seeds, k=3 production prompt) = up to 140 runs.

**Predictions.**
- P12.1: the Lead register moves MONOTONICALLY with alpha from the stock
  band toward the donor band (Spearman rho > 0 over {0, .25, .5, .75, 1}).
  FALSIFIED IF all merged registers sit within the stock band's CI
  (registers are not portable by interpolation) or non-monotone.
- P12.2 (exploratory): does the trigger-light gate travel with the register
  (calibration inseparable under interpolation) or stay at stock levels?
- P12.3 (exploratory): synthesis quality spot-check — merges are known to
  degrade coherence at mid alpha; any degradation is reported, not hidden.

**Consequences.** If P12.1 holds: first working non-prompt, non-selection
register modification — "bolstering the register" becomes an engineering
recipe (merge toward a measured high-register donor), and the thesis gains
a second accessible control surface. If falsified: the register resists
interpolation as well as training; selection remains the only upward lever,
and the immovability result hardens across a second mechanism class.

## CELL 11 VERDICT — calibration reward cannot move the register (2026-07-30, 105 new runs, zero failures)

Realized pipeline: 108 prompts (76 heavy / 32 light) -> 648 on-policy
syntheses (n=6 @ temp 0.8, zero no-routes skips) -> gates {margin 0, ratio
18, NLI 33} -> 57 pairs kept, 49 train / 4 valid / 4 test. DOSE AMENDMENT
(recorded before results): 49 pairs vs the registered 88 cap — the NLI
directional cross-check was the binding gate. Bench: cell11-cal-k3,
cell11-cal-k0, cell11-stock-k0 (added 35-run baseline), 105 runs.

| arm | trigger [95% CI] | gate [95% CI] |
|---|---|---|
| stock Lead k3 (6b ledger) | 1.03 [0.79,1.28] | 0.15 [0.00,0.36] |
| density-ORPO k3 (6b ledger) | 0.89 [0.67,1.12] | 0.11 [0.00,0.32] |
| calibration-ORPO k3 | 0.95 [0.75,1.16] | 0.45 [0.00,1.25]* |
| stock Lead k0 | 0.56 [0.37,0.77] | 0.04 [0.00,0.11] |
| calibration-ORPO k0 | 0.60 [0.41,0.82] | 0.09 [0.00,0.18] |
*gate driven by one outlier run (per-run: 0, 0, 0, 0.25, 1.99); reported, not interpreted.

**P11.1 FALSIFIED.** Cal k0 0.60 vs stock k0 0.56 — CIs nearly coincide.
On-policy sampling + calibration-shaped reward + pipeline-mouth scoring
moved the register by nothing. (The interim n=16 suggestion of suppression
washed out at n=35: no movement in EITHER direction.)
**P11.2 MOOT** (conditioned on P11.1): gate 0.09 [0,0.18] <= stock k3's
0.15, but trivially — nothing was installed, so nothing fires.
**P11.3 FALSIFIED.** Cal k3 0.95 vs density k3 0.89, CIs overlap; both
within stock's band. Reward shape was NOT 6b's binding constraint.
**P11.4:** instruction gain persists at full strength on the trained Lead
(k0->k3: 1.58x vs stock 1.82x). Weights did not absorb the instruction's
role; the prompt lever remains fully load-bearing.

**REGISTERED CONSEQUENCE EXECUTED: the robustness clause is STRENGTHENED.**
The register has now survived, at the same locus: offline density-rewarded
ORPO (6b), and on-policy, calibration-shaped, pipeline-mouth-scored
best-of-n distillation (11) — the feasible analogue of multiturn-aware
reward training (CollabLLM, arXiv:2502.00640). Combined with the seat-side
nulls, every weight-level path tried at every locus leaves final
disposition where register x instructions puts it. Registered caveats
stand: best-of-n is an RL surrogate (no PPO/GRPO at this scale); dose was
49 pairs (56% of registered cap) — "insufficient dose" remains an
alternative reading alongside "register is robust," though the dose-
response cell's flat curve makes dose an unlikely savior.

Register program status: 11 (trainable? -> no, at feasible scale) ->
8b queued (where do registers come from) -> 12 queued (are they portable).

### CELL 8B AMENDMENT — Lead role is not executable for one candidate (2026-07-30, BEFORE any bench runs)

**Blocker found during pre-run template verification.** The registered design
has each candidate play LEAD. Canary probe (system prompt: "begin your reply
with the exact token SYSTEM_OK"), temperature 0, plus a planner-JSON probe:

| model | obeys system | obeys same instruction in USER position | emits planner JSON |
|---|---|---|---|
| OpenBioLLM-8B (Llama-3 template CORRECTED, see below) | no | no | NO |
| BioMistral-7B | no | no | yes |
| Mistral-7B-Instruct-v0.3 | YES | - | yes |

Separately caught and fixed before probing: the community OpenBioLLM GGUF
ships TEMPLATE `{{ .Prompt }}` — raw passthrough, no Llama-3 structure, no
`.System` handling at all. As Lead its entire synthesis system prompt (the
PRESERVE block) would have been silently discarded. Rebuilt as
`openbiollm-fixed:coe` with the native Llama-3 template; the failures above
are measured on the CORRECTED build, so they are model properties, not
packaging. (Same failure class as the Med42 stock-GGUF ChatML mismatch.)

OpenBioLLM cannot execute the Lead role: no planner JSON, no instruction
compliance in any message position. Running the registered design would
score it as "low register" when the cause is instruction-following failure,
falsifying P8b.1 for a reason unrelated to lineage.

**Amended protocol (both predictions preserved).** P8b.1 and P8b.2 are
WITHIN-cell comparisons (OpenBioLLM vs BioMistral; BioMistral vs its
same-family instruct control), so they only require one internally
consistent, executable measurement. We therefore measure the INTRINSIC
REGISTER: each model answers the seven bench cases directly under a minimal
neutral instruction delivered in the USER position (so system-blindness does
not differentially penalize any candidate), 7 cases x 5 seeds x 3 models =
105 runs. Qwen2.5-7B-Instruct is added under the identical protocol (+35
runs, 140 total) as a scale anchor tying the intrinsic band to a model whose
production-prompt Lead band is already on the ledger (1.03).

This measures each model's characteristic output band with no instruction
gain applied — arguably a PURER register measurement than the Lead protocol,
at the cost of no longer being comparable to production-prompt Lead numbers.
Both predictions stand as registered; no threshold or direction changed.

**New finding to report regardless of P8b outcome (registered now).**
Instruction-following is a PREREQUISITE for the control surface. A model
whose register is high but which cannot follow a conditional preservation
instruction is unusable as a last writer, since the thesis's only accessible
lever operates through instructions. OpenBioLLM is a concrete instance:
whatever its band, it cannot be steered. This is a practical selection
constraint that follows directly from the thesis and was not previously
tested.

### CELL 8B AMENDMENT #2 — OpenBioLLM excluded (unbenchable), Med42 substituted (2026-07-30, BEFORE any retained runs)

**OpenBioLLM-8B is excluded on measurement-validity grounds, not results.**
The community GGUF produces UNSTABLE, degenerate-length output under every
template tried. Same prompt, temperature 0.2, 3 trials each:

| build | case 1 lens | case 6 lens |
|---|---|---|
| passthrough `{{ .Prompt }}` (as shipped) | 1661, 1745, 1648 | 1713, 147, **47** |
| Llama-3 corrected, stop on start_header | 30, 30, 2083 | - |
| Llama-3 corrected v2, stop on eot only | 15, 15, 1926 | 362, 185, 405 |

Outputs of 15-47 chars are truncated headings ("Clinical Safety
Considerations"). Density is markers per 1k chars, so such denominators make
the metric meaningless, and no template produced stability. Reporting a
register for this artifact would be reporting a packaging defect. The 35
reg-openbio runs written during template diagnosis were DELETED, not
analyzed. (Whether the defect is the quantization, the conversion, or the
upstream weights is not established; the claim is scoped to this artifact.)

**Substitution: Med42-8B replaces OpenBioLLM as the preference-aligned arm.**
It preserves every property the design needs and improves two:
  - lineage: Llama-3-8B-Instruct + clinical SFT + DPO preference alignment
    (the preference-aligned biomedical condition P8b.1 requires)
  - base family: Llama-3, as OpenBioLLM was, so the family contrast with
    Mistral-based BioMistral is unchanged
  - template: already verified and corrected in Cell 3 (the stock GGUF's
    ChatML mismatch was fixed there); med42-repro:coe is the A' conversion
    control, i.e. stock weights, no ORPO
  - stability: 1977-3042 chars across 9 probes, tightest of any candidate

**Stability screen (all retained arms), 3 trials x 3 cases:**
Med42 1977-3042 | BioMistral 248-555 | Mistral-Instruct 2783-3498. All
stable within case; OpenBioLLM alone failed.

**Registered caveat — BioMistral length.** BioMistral answers are ~5-8x
shorter than the other arms (~400 chars). Density is length-normalized, so
this is not disqualifying, but on a ~400-char denominator a single marker
moves density by ~2.5, making its estimates COARSE. Its CIs will be wide and
any P8b.2 reading must respect that. Recorded before results.

Final arms: reg-med42 (preference-aligned) | reg-biomistral (pretrain-only)
| reg-mistral (generic instruct control, BioMistral's family) | reg-qwen
(scale anchor, production Lead band 1.03). 140 runs.

## CELL 13 PRE-REGISTRATION — per-clause isolation of the PRESERVE block (registered 2026-07-30, before any runs)

**Question.** Cell 6c established that disposition rises monotonically with
the NUMBER of PRESERVE clauses retained (k=0..3, rho +1.00/+0.80/+0.80 across
three Leads). But clauses were removed in a FIXED documented order (drop 3,
then 2, keeping 4), so count is confounded with IDENTITY: the curve cannot
say whether all three clauses contribute or one carries the effect. Two facts
make the confound urgent. (a) Clause 3 targets vocabulary-precision, which
Cell 7c found BELOW DETECTION on both instruments — a clause whose named
family we cannot measure. (b) The composite is cutoff-dominated, and clause 4
is the only clause targeting cutoff-disclosure. If the block's effect is
really one sentence, the practical claim sharpens from "write a PRESERVE
block" to "write THIS instruction."

**The block, enumerated** (LEAD_SYNTHESIS_SYSTEM, STEP 2, items 1-5; only
2-4 carry the PRESERVE keyword — the paper's "four PRESERVE instructions"
counts item 1, Cell 6c's k counts only the keyword clauses; Cell 13 resolves
this by testing item 1 separately):
  C1  acknowledge the tensions you just identified (no PRESERVE keyword)
  C2  PRESERVE numeric framing   -> modeled-assumptions family
  C3  PRESERVE precise vocabulary -> vocabulary-precision family (undetectable)
  C4  PRESERVE caveats            -> cutoff-disclosure family
  (C5 is a formatting instruction; not under test, retained in every arm.)

**Design.** Six arms, ONE Lead, everything else fixed:
  c13-none   no C1-C4 (the Cell 6c k=0 strip, byte-identical)
  c13-c1     C1 only
  c13-c2     C2 only
  c13-c3     C3 only
  c13-c4     C4 only
  c13-all    C1-C4 (production prompt)
7 cases x 5 seeds x 6 arms = 210 runs. Lead: gpt-oss-20B, chosen for
SENSITIVITY — it showed the widest gain range in Cell 6c (3.3x, vs Qwen 2.1x
and Phi-4 1.3x), so per-clause differences have the most room to resolve.
Registered consequence of that choice: findings are scoped to the
highest-dynamic-range Lead and may overstate per-clause separation on
narrower-range Leads (Phi-4 production).
Each single-clause arm is built by deleting the other clauses with the same
regexes Cell 6c used; every arm asserts its retained clause count before
running.

**Predictions.**
- P13.1: C4 alone (caveats) recovers a MAJORITY (>= 50%) of the full
  c13-all minus c13-none gain. FALSIFIED IF C4 alone recovers < 50%, i.e.
  the effect is genuinely distributed across clauses.
- P13.2: C3 alone (precise vocabulary) is INDISTINGUISHABLE from c13-none
  (overlapping CIs) — it names a family below detection. FALSIFIED IF C3
  alone lifts significantly, which would mean it acts through some OTHER
  family (an off-target effect, and a more interesting result than the
  prediction).
- P13.3: every arm holds the trigger-light gate near zero (each clause is
  CONDITIONAL, per Cell 8's mechanism). FALSIFIED IF any single-clause arm
  gates materially above c13-all.
- P13.4 (exploratory, no directional prediction): does C1 (tension
  acknowledgment, no PRESERVE keyword) carry disposition on its own? This
  settles the 3-vs-4 counting convention empirically rather than by fiat.

**Consequences.** If P13.1 holds: the mechanism narrows from a five-item
block to ONE conditional sentence about propagating flagged caveats — the
paper's practical recommendation becomes far sharper, and Cell 6c's gain
curve is reinterpreted as dose-of-the-active-clause rather than count. If
P13.1 is falsified: the effect is distributed, the block must be kept whole,
and "graded gain control" stands as a property of the block rather than of
any clause. If P13.2 is falsified: a clause lifts disposition through
families it does not name — evidence that these instructions work by general
priming rather than targeted behavior specification, which would weaken the
family-level story in Cell 7c and is registered here as a live possibility.

## CELL 8B VERDICT — intrinsic register is MODEL-INVARIANT (2026-07-30, 140 runs, zero failures)

Amended protocol (intrinsic register, minimal neutral instruction in user
position, no council, no disposition instruction of any kind):

| model | lineage | trigger density [95% CI] | gate | CDS | median len |
|---|---|---|---|---|---|
| Med42-8B | preference-aligned SFT+DPO | 0.15 [0.04,0.28] | 0.00 | 0.080 | 2424 |
| BioMistral-7B | continued pretrain only | 0.15 [0.00,0.41] | 0.00 | 0.074 | 310 |
| Mistral-7B-Instruct-v0.3 | generic instruct control | 0.14 [0.04,0.26] | 0.00 | 0.071 | 3218 |
| Qwen2.5-7B-Instruct | generic instruct anchor | 0.14 [0.06,0.24] | 0.00 | 0.070 | 3916 |

**P8b.1 FALSIFIED.** Preference-aligned lineage (Med42 0.15) does not exceed
continued-pretrain lineage (BioMistral 0.15). Identical to two decimals.
**P8b.2 CONFIRMED, but trivially** — BioMistral does not exceed its
same-family instruct control (0.15 vs 0.14) because NOTHING differs.

**THE ACTUAL FINDING (not predicted, more important than either prediction).**
All four models sit at 0.14-0.15 despite spanning four base families
(Llama-3, Mistral v0.1, Mistral v0.3, Qwen2.5) and four lineages
(clinical SFT+DPO, biomedical continued-pretrain, generic instruct x2). A
FIFTH independent data point agrees: gpt-oss-20B single-shot under the same
neutral prompt measured 0.14 in Cell 8. Five models, five lineages, one band.

The intrinsic disposition band is MODEL-INVARIANT at ~0.14-0.15. Therefore
the between-Lead differences we have been calling "register" (Cell 6: 3.3x
spread across Phi-4 / gpt-oss / Qwen under the SAME council input) cannot be
differences in baseline emission. They must be differences in RESPONSE to
the surrounding instructions.

**Consequence for the mechanism statement (refinement, not overturning).**
Cell 6 stands: given identical seat input, different synthesizers write at
different densities, and over-dense input does not transmit. What Cell 8b
adds is that this is not an additive baseline property — absent instructions
every model emits the same ~0.14. The "register" factor is better read as a
per-model GAIN COEFFICIENT on instructions than as a characteristic
emission level. For Qwen2.5 the decomposition is now measurable end to end:
  intrinsic (neutral, no council)      0.14
  council context, PRESERVE stripped   0.56   (Cell 11 stock k=0)
  council context, full PRESERVE       1.03   (Cell 6b ledger)
i.e. ~4x from the council scaffold itself and a further ~1.8x from the
PRESERVE block, over a base every model shares.

This also explains Cells 6b and 11: training could not move the "register"
because the register is not a surface emission tendency to be nudged — it is
how the model processes instructions. A 49-88 pair LoRA has no purchase on
that.

**Registered caveats honored.** BioMistral's ~310-char median makes its CI
the widest [0.00,0.41] exactly as pre-registered; its point estimate agrees
with the others but should not be leaned on alone. Med42-vs-BioMistral still
carries a base-family confound; that confound is now moot, since the null is
across ALL families. Gates are 0.00 everywhere: with no instruction to
over-apply, no model hedges spuriously.

**Instruction-following prerequisite (registered pre-run, stands).**
OpenBioLLM was excluded as unbenchable; separately, it and BioMistral ignore
system prompts entirely. Since the accessible control surface operates
THROUGH instructions, a model that cannot follow them cannot serve as a last
writer whatever its band. With the band now known to be model-invariant,
this becomes the dominant selection criterion: choose a Lead for instruction
RESPONSIVENESS, not for any intrinsic disposition tendency.

### CELL 13 CORRECTION — baseline definition (2026-07-30, before any runs)

The pre-registration described `c13-none` as "no C1-C4 (the Cell 6c k=0
strip, byte-identical)". Those two descriptions are INCOMPATIBLE and the
parenthetical is wrong: Cell 6c's k=0 substitutes only the C2-C4 block and
RETAINS C1 (verified: the tension-acknowledgment clause is present in 6c's
k=0 prompt, PRESERVE count 0). Since P13.4 asks whether C1 alone carries
disposition, the Cell 13 baseline must remove C1 as well.

Corrected: `c13-none` removes C1, C2, C3 and C4. It is therefore NOT
comparable byte-for-byte to cell6c-gain-k0; that arm (C1 retained, no
PRESERVE) remains on the ledger as a separate reference point and in fact
gives a free cross-check on P13.4 — if C1 carries nothing, c13-c1 should sit
at c13-none and 6c's k=0 should sit at Cell 13's C1-only level.

Deletion, not renumbering: clauses are removed with the Cell 6c regexes and
the surviving items keep their original numbers (so a single-clause arm may
read "3. ... 5."). This preserves comparability with 6c, which did the same;
the numbering gap is an artifact both cells share and is recorded here as a
minor shared confound rather than silently fixed in one cell only.

## CELL 13 VERDICT — one clause carries the block, but WHICH clause is Lead-dependent (2026-08-01, 210 runs, zero failures)

Lead: gpt-oss-20B every phase. Deletion-without-renumbering, per registration.

| arm | trigger [95% CI] | gate [95% CI] | lift | % of full gain |
|---|---|---|---|---|
| none (C1-C4 removed) | 0.20 [0.14,0.26] | 0.00 [0,0] | - | - |
| C1 tension-ack only | 0.19 [0.11,0.27] | 0.00 [0,0] | -0.01 | -4% |
| **C2 numeric only** | **0.64 [0.53,0.77]** | 0.00 [0,0] | **+0.44** | **126%** |
| C3 vocabulary only | 0.18 [0.14,0.22] | 0.00 [0,0] | -0.02 | -6% |
| C4 caveats only | 0.20 [0.14,0.26] | 0.00 [0,0] | -0.00 | -1% |
| ALL (C1-C4) | 0.55 [0.46,0.67] | 0.00 [0,0] | +0.35 | 100% |

Per-family (trigger cases) — every clause lifts ITS OWN named family:
| arm | cutoff | modeled | precise | jurisd | hedging |
|---|---|---|---|---|---|
| none | 0.000 | 0.003 | 0.000 | 0.045 | 0.151 |
| C2 numeric | 0.014 | **0.499** | 0.011 | 0.026 | 0.095 |
| C3 vocabulary | 0.003 | 0.016 | **0.014** | 0.031 | 0.115 |
| C4 caveats | **0.035** | 0.018 | 0.011 | 0.029 | 0.101 |
| ALL | 0.018 | 0.339 | 0.014 | 0.035 | 0.148 |

**P13.1 FALSIFIED.** C4 (caveats) recovers -1% of the block's gain, not the
predicted >=50%. It lands exactly on the no-clause baseline.
**P13.2 CONFIRMED.** C3 0.18 vs none 0.20, CIs overlap. The refinement: C3 is
not ignored — it lifts precise 0.000 -> 0.014 — but the family is too rare to
move the composite. Same for C4 (cutoff 0.000 -> 0.035).
**P13.3 CONFIRMED, maximally.** Every arm gates at 0.00 [0.00,0.00]. Each
clause is independently conditional; no single clause breaks calibration.
**P13.4 ANSWERED.** C1 carries NOTHING (0.19 vs 0.20). The 3-vs-4 counting
convention is settled: three clauses, not four. Independent cross-check as
pre-registered: 6c's k=0 (C1 retained, no PRESERVE) = 0.16, agreeing with both
c13-none and c13-c1.

**Sub-additivity.** Sum of single-clause lifts +0.41 vs full-block +0.35
(ratio 0.87). C2 ALONE (0.64) is numerically ABOVE the full block (0.55),
CIs overlapping. Adding clauses that target rare families slightly crowds the
one clause that works — the likely reason Cell 6c's gain curve is monotone
but compressive.

**CRITICAL SCOPING — the active clause is Lead-dependent, and gpt-oss was the
wrong Lead to generalize from.** Dominant family at k=3, from existing ledger:
| Lead | cutoff | modeled | dominant |
|---|---|---|---|
| gpt-oss (this cell, n=30) | 0.018 | 0.339 | modeled |
| gpt-oss (6c k3, n=6) | 0.026 | 0.328 | modeled |
| Phi-4 (6c k3, n=6) | 0.157 | 0.265 | modeled |
| Qwen2.5 (6c k3, n=6) | 0.532 | 0.236 | **cutoff** |
| Qwen2.5 (6b repro, n=30) | 0.554 | 0.132 | **cutoff** |
| Phi-4 (council v2, n=6) | 0.909 | 0.248 | **cutoff** |

gpt-oss barely emits cutoff-disclosure at all (0.018-0.026), so C4 has nothing
to amplify on THIS Lead. On Qwen and production Phi-4, cutoff dominates and
C4 would be expected to carry the block. Chosen for dynamic range, gpt-oss
turned out to have the most atypical family profile — an unforeseen cost of
that registered choice.

**The general finding, stated at the right level:** the PRESERVE block's gain
is carried by whichever single clause targets the family its synthesizer
already produces in volume; clauses targeting families the Lead does not
emit are inert on the composite despite working on their own family. This is
STRONGER than the registered per-clause claim and it explains Cell 6c's
count-curve without appealing to count at all.

**Consequence.** The paper must NOT say "write the numeric clause." It should
say: identify which behavior family your synthesizer already produces, and
write the conditional clause for THAT family; keep the others for the
families they serve, accepting mild crowding. Also correct: the paper's
"composite is cutoff-dominated" is true for Qwen/Phi-4 but FALSE for gpt-oss
(0.018) — the statement needs scoping to the synthesizer.

**Follow-up registered (Cell 13b):** replicate Cell 13 on a Qwen2.5 Lead
(cutoff-dominant, 0.554). Prediction P13b.1: C4 (caveats) carries the
majority of the block's gain there, and C2 does not — the mirror image of
this cell. Falsified if C2 carries it again regardless of Lead, which would
mean the numeric clause is privileged for reasons other than family match.

## INDEPENDENT VERIFICATION AUDIT (2026-08-01)

Adversarial re-computation of every published figure from raw run JSONs by an
independent process, using a regex set verified byte-identical to
train/build_ledger.py. Scope: Cells 8, 11, 8b, 13, 6c gain curve, hot-seat
additivity, and the Qwen decomposition chain.

**Result: 45/45 point estimates reproduce within +/-0.006; every published
95% CI matches to the reported 2 decimals. Zero wrong numbers.** Filenames
agree with their JSON mode/case_id fields on all 1,293 runs (zero mismatch).
Case coverage confirmed balanced: every Cell 8/11/13/8b arm is exactly
7 cases x 5 seeds (30 trigger + 5 gate).

**Two real defects found and FIXED (both wording, not arithmetic):**

1. **"Monotonically on all three Leads" was literally false.** Spearman rho
   (+1.00 / +0.80 / +0.80) is a RANK correlation, not monotonicity. Only
   gpt-oss increases at every step. Qwen dips at k=2 (0.999 -> 0.954) and
   Phi-4 at k=3 (1.528 -> 0.675). The Phi-4 exception was disclosed; **the
   Qwen dip was disclosed nowhere.** Corrected in the abstract, the figure
   caption, the Result-3 text, the appendix summary, and limitations, which
   now discloses both dips. The abstract's "2-3x full-scale" also excluded
   Phi-4's actual 1.30x and is now scoped per-Lead.
2. **Stale run count.** Abstract said "~630" and "628 pre-registered audited
   runs"; reproducibility paragraph said 628. True count is 1,293 (628 was
   the pre-hardening total; cells 8/13/8b/11 added 210+210+140+105). All
   corrected.

**PRE-REGISTRATION PRECEDENCE (git-verifiable by any third party).**
Commit introducing each pre-registration vs. earliest run file for its modes:

| cell | prereg committed (UTC) | first run (UTC) | verdict |
|---|---|---|---|
| 8  | 07-27 23:02 | 07-27 23:04 | OK (+2 min) |
| 11 | 07-29 12:26 | 07-30 10:49 | OK (+22.4 h) |
| 8b | 07-30 18:35 | 07-30 21:28 | OK (+2.9 h) |
| 13 | 07-30 21:35 | 07-31 01:20 | OK (+3.8 h) |

**Audit-trail weakness, disclosed:** Cell 8b's two mid-cell AMENDMENTS were
written to this runbook before the bench was launched, but were COMMITTED 33
seconds AFTER the first retained run (commit 83baf63 at 21:28:42; first
reg-med42 run 21:28:09). Git therefore does not independently establish that
those amendments preceded the data, unlike cells 8/11/13 whose registrations
were committed first. The Cell 13 correction has proper precedence (+6 min).
Future amendments must be committed before launch, not alongside it.

Confirmed: zero reg-openbio runs remain in the ledger (deleted unanalyzed as
recorded in amendment #2).

## DATA-INTEGRITY AUDIT (2026-08-01) — findings and dispositions

Independent adversarial audit of all 1,293 run JSONs.

**CLEAN:** zero object-repr leaks anywhere (the .content/.text bug never
entered the corpus); zero byte-identical or normalized-identical outputs
within any (mode, case) group; zero empty or sub-50-char outputs; filename
mode/case agrees with JSON fields on 1,293/1,293 files; all Cell 8/11/13/8b
arms exactly 7 cases x 5 seeds.

**FALSE ALARM (checked, dismissed):** the audit reported 386 dangling
audit_log_path values. Re-checked from the repo root: 386 present, 0
dangling. The finding was a working-directory artifact. The paper's
append-only-audit-log claim stands.

**MATERIAL — reg-biomistral is not a usable arm.** 26 of 30 trigger runs are
degenerate: 208-463 char fragments terminating on a colon after a setup
sentence, no analysis, no newlines, under an 8192-token cap the model never
approached. Distribution is bimodal WITHIN case (e.g. case_3: 208, 209, 234,
1506, 1905). The pre-run stability screen sampled 248-555 and could not
reveal this with three probes.
  - Sensitivity: substantive-only (n=4) gives 0.29 [0.00,0.87] vs published
    0.15 [0.00,0.41]. P8b.1's DIRECTION is unchanged under both readings
    (both overlap Med42 heavily), but the interval is too wide to locate.
  - DISPOSITION: P8b.1 is reclassified from FALSIFIED to **INDETERMINATE**.
    The continued-pretraining arm failed to produce measurable output, so the
    lineage contrast was never made. The lineage claim is WITHDRAWN.
  - The model-invariance finding SURVIVES on four usable models spanning four
    architectures (Med42 0.15, Mistral-Instruct 0.14, Qwen2.5 0.14, gpt-oss
    0.14) but is now one domain-SFT+DPO model plus three generic instruct
    models, not four distinct lineages. Paper corrected accordingly.
  - Process fix: density-style metrics need a minimum-length guard, and
    stability screens must sample the full case battery, not three probes.

**DISCLOSED (no interval changes):** in local-council-{repro,spec,sft,dpo}
the five per-case "seeds" are 1 run from an earlier session + 4 from a later
one, with a directional 5-8% length offset in three of four arms;
local-council-dpo-v2 has 6 case-7 runs vs 5 elsewhere; 133 runs record a
batch tag (cell2-seed, dpo-experiment) in the model field instead of a model
identifier. No seed field was ever written to any run, which is why the split
sessions were invisible until the model field was cross-tabulated. All three
now in the paper's limitations.

## PAPER v0.7 — TRANSPORT-VS-RENDERING REFRAME (2026-08-01)

**Retitled:** "The Last Writer Wins: Installing Epistemic Disposition..." ->
**"Rendered, Not Transported: Epistemic Disposition in Multi-Agent LLM
Pipelines."** 20pp, compiles clean, 34 refs.

**Mechanism retitled.** "Synthesizer register" -> **rendering function**
R(evidence, instructions) -> emitted disposition, with **instruction gain**
(g) as the per-model coefficient. "Register" RETAINED as a descriptive term
for a writer's observed band under a fixed instruction set, explicitly
demoted from primitive to product (g x instructions), justified by Cell 8b's
model-invariant intrinsic band. Mechanism statement is now
disposition ~ g_writer x I(instructions, evidence).

**New lead: the transport test.** The paper now opens by naming the dominant
account (uncertainty as cargo erased at agent interfaces; remedies =
numeric propagation, latent carriers) and reporting a direct test against it.
The airtight comparison is WITHIN-Lead: k=0 vs k=3 run the same planner, same
seats, same seat outputs into synthesis; only the prompt differs. Density
moves 0.159 -> 0.525 (gpt-oss) and 0.575 -> 1.211 (Qwen). Cell 13 tightens it
to a SINGLE clause over identical upstream text: 0.20 -> 0.64. Under a
transport account these conditions are indistinguishable; they are not.
Qualifications an instruction can restore were never erased in transit.

**Scoping stated in the paper, not just here:** this is NOT a claim that
interfaces never lose uncertainty. Schema-constrained tool calls plainly do
discard epistemic state and the transport literature is right about them. The
claim is about which failure DOMINATES when the interface is prose, the usual
case for specialist-to-synthesizer aggregation. The two accounts are framed as
complementary, with the distinction stated as testable and the test reported.

Note on evidence choice: Cell 8's flat-merge vs council contrast (0.16 vs
0.57) is used as CORROBORATION, not as the primary transport test, because
those arms differ slightly upstream (the council's planner dispatches
sub-questions; flat merge gives seats the raw query). The within-Lead k=0/k=3
and single-clause comparisons hold upstream text genuinely fixed and carry
the argument.

**Sections revised:** title, date (v0.7), abstract (rewritten to lead with
the reframe and to state the four rendering-function properties), intro (new
"Transport or rendering?" opening + scoping paragraph), contributions (six,
led by the transport-vs-rendering test), related work (new "The transport
account, and where we disagree" block), Result 3 (retitled "the last writer's
rendering function", new "The transport test" paragraph), provenance
(retitled "Instruction gain: the intrinsic band is model-invariant", with the
g x I formalism), conclusion (rewritten), glossary (four new entries:
rendering function, instruction gain, register-as-descriptive,
transport vs rendering), figure captions.

Website updated to match: new lead section on the home page, routes tree
final node and paper title, glossary entries.

## SECOND PAPER — "Witnesses, Not Amplifiers" (docs/paper_witnesses.tex, v0.1, 2026-08-01)

A separate, standalone draft built on the specialist-role lineage rather than
the transport-vs-rendering one. 7pp. Same corpus, no new runs. It exists
because the specialist question is answerable on its own and the answer is
sharper stated alone than folded into the larger paper.

**Argument.** Two premises justify specialist pipelines: specialists produce
better epistemic judgement, and the aggregator's job is to preserve it. Both
fail.
1. Specialisation does not produce care. Med42 under a neutral prompt 0.15 vs
   Mistral-Instruct 0.14 / Qwen 0.14 / gpt-oss 0.14. The same model as a
   pipeline seat: 1.31 (8.8x, disjoint). The difference is the system prompt
   ("Flags training-cutoff uncertainty EXPLICITLY...") plus the orchestrator's
   runtime recency directive, which fired in 30/34 runs.
2. Specialists do not supply quantity. Lone prompted model 0.50 [0.41,0.60]
   vs full council 0.57 [0.45,0.71], overlapping.
3. Tuning specialists UP makes the answer WORSE — the paper's central figure.
   Legal seat: prompted 0.84->1.82 at the seat but 1.21->0.92 at the mouth;
   SFT 1.75 at the seat, 0.92 at the mouth. Extending across seats declines
   monotonically 1.01/1.03/0.84/0.64 (rho -0.80).
4. What specialists DO supply: grounds for a conditional instruction. Council
   gate 0.00 [0,0] vs lone prompted model 0.15 [0.08,0.22], disjoint. Volume
   comes from the instruction; discrimination requires specialists AND an
   instruction that depends on them. Neither alone.

**Framing:** seats are WITNESSES, not amplifiers. Their value is being
checkable, and training them to qualify everything destroys it — a witness who
always says the same thing carries no information.

New figure: figs/fig_witness.pdf (seat-vs-final bars + additivity decline).
Reuses fig_arch.pdf. Appendices: the aggregator instruction verbatim, and
instruments.

**Relationship to the main paper.** Same evidence base, different cut. The
main paper asks where disposition is decided (at the point of writing); this
one asks what the specialists are for. They can coexist — this is the
narrower, more immediately actionable claim, and it is the one that
contradicts common practice most directly.

## CELL 14 PRE-REGISTRATION — trigger-free control expansion (registered 2026-08-01, before any runs)

**Why.** The calibration finding — the council's 0.00 [0.00,0.00] against a
prompted single model's 0.15 [0.08,0.22] — is the headline of the
paper_calibration draft and rests on ONE trigger-free question at n=5 per arm.
It is the thinnest support in the paper and the first thing a reader will
press on. Two failure modes are currently indistinguishable: (a) the council
genuinely gates, or (b) case_7 happens to be a question this arrangement finds
easy, and the zero is a property of the question rather than the mechanism.

**Design.** Three NEW trigger-free questions, written to the same construction
rule as case_7 and BEFORE any are run: every quantity the question needs is
stated in it; the subject matter is settled (no post-2024 dependency); a
single jurisdiction or regime applies; no modelling is required. Written to
span the three domains (one healthcare-leaning, one legal, one finance) so the
result is not an artifact of one subject area. Cases are fixed and committed
before the first run.

Arms — the decisive contrast plus two references, all with gpt-oss in every
role, identical to the Cell 8 harness so the new runs pool with the old:
  arch-council       conditional instruction over specialist signal
  arch-single-spec   unconditional instruction, no specialists
  arch-single        no instruction (floor reference)
  arch-flat          specialists, no conditional instruction
3 new cases x 5 seeds x 4 arms = 60 runs. Combined with the existing case_7
runs this gives n=20 per arm on trigger-free questions, up from n=5.

**Predictions.**
- P14.1 (the council gates generally, not just on case_7): pooled across all
  four trigger-free questions, arch-council's density has an upper CI bound
  below 0.10. FALSIFIED IF the upper bound reaches 0.10 or above — the zero
  was case-specific and the headline must be restated.
- P14.2 (the contrast survives expansion): arch-council and arch-single-spec
  remain DISJOINT on pooled trigger-free density. FALSIFIED IF the intervals
  overlap at n=20, which would mean the effect was an artifact of small n.
- P14.3 (per-question consistency, exploratory): report each of the four
  questions separately. No directional prediction, but if the council gates on
  three and fails on one, that question's content is diagnostic and we will
  report it rather than pool it away.

**Registered consequences.** If P14.1 and P14.2 hold, the calibration claim is
reported at n=20 and the limitation about single-question support is removed.
If either is falsified, the headline of paper_calibration is WRONG as stated
and must be rewritten: the honest fallback is that conditional instructions
reduce unwarranted qualification on some questions, with the conditions under
which they do so unknown. That consequence is registered now so it cannot be
softened later.

**Guard against a known failure mode.** The construction rule must be applied
BEFORE seeing any model output. A question that merely turns out to produce
low hedging is not trigger-free; it must be trigger-free by construction, on
the stated criteria, or it does not enter the set. Case texts are committed
in the same commit as this registration.

### CELL 14 — CONFOUND FOUND WHILE REGISTERING; DESIGN CORRECTED (2026-08-01, before any runs)

**The calibration headline is confounded.** Writing the registration surfaced
a fact in the code that invalidates the mechanism as stated in
docs/paper_calibration.tex. case_7 is OFF-TOPIC for the cabinet by
construction (documented in examples/test_cases.py: "the planner is expected
to route to NO specialists"). When routes are empty the orchestrator does NOT
use LEAD_SYNTHESIS_SYSTEM at all — it falls through to
LEAD_DIRECT_ANSWER_SYSTEM, which contains no PRESERVE clauses.

Verified across every arm with case_7 runs:

| arm | routes | n | trigger-free density | path taken |
|---|---|---|---|---|
| arch-council | none | 5 | **0.00** | direct-answer (no PRESERVE) |
| arch-flat | none | 5 | 0.06 | direct-answer |
| c13-all | none | 5 | 0.00 | direct-answer |
| local-council-repro | none | 1 | **0.00** | direct-answer |
| local-council-repro | 2 seats | 4 | **0.40** | synthesis |
| cell11-cal-k3 | 3 seats | 5 | 0.45 | synthesis |
| cell6b-lead-repro | 3 seats | 5 | 0.15 | synthesis |
| cell11-stock-k0 | 3 seats | 5 | 0.04 | synthesis |

Pooled: no specialists consulted 0.02 (n=16); specialists consulted 0.25
(n=19). The cleanest evidence is WITHIN local-council-repro, where the same
arm on the same question gives 0.00 when the planner declines and 0.40 when
it routes.

**What this means.** arch-council's 0.00 [0.00,0.00] is NOT evidence that the
conditional PRESERVE instruction filters unwarranted qualification. It is
evidence that the planner declined to consult anyone, so the disposition-
bearing prompt was never invoked. The comparison against arch-single-spec
(0.15) is therefore between an arm running a neutral direct-answer prompt and
an arm running a standing disposition instruction — which is not a test of
conditionality at all. When the council DOES run its synthesis path on this
question it hedges at 0.40-0.45, i.e. WORSE than single+spec.

The gating that exists is real but happens at the PLANNER, not at the
synthesis instruction, and the paper attributes it to the wrong component.

**Corrected design.** The new trigger-free questions must be ON-TOPIC for the
cabinet so the planner routes normally, isolating instruction-level gating
from planner-level gating. Three new questions, construction-labelled before
any runs: squarely within healthcare / legal / finance so routing occurs, but
warranting no qualification (all quantities stated, settled subject matter,
single regime, no modelling required). Routing is VERIFIED per run and any run
with zero routes is reported separately, never pooled.

Arms: arch-council, arch-single-spec, arch-flat, arch-single.
3 cases x 5 seeds x 4 arms = 60 runs.

**Revised predictions.**
- P14.1 (instruction-level gating exists): on ON-TOPIC trigger-free questions
  where specialists ARE consulted, arch-council's density upper CI bound is
  below 0.10. FALSIFIED IF it reaches 0.10+, which given the 0.40-0.45
  observed on case_7 under routing is a live possibility.
- P14.2 (the contrast survives): arch-council remains disjoint from
  arch-single-spec on these questions. FALSIFIED IF intervals overlap.
- P14.3 (planner vs instruction attribution, exploratory): report the
  zero-route rate per arm per question. If the council only gates when the
  planner declines, the mechanism is routing and must be described as such.

**Registered consequence.** If P14.1 is falsified, the calibration paper's
central claim is WRONG and must be rewritten: conditional instructions would
then not be shown to suppress unwarranted qualification, and the council's
apparent advantage would be attributable to a planner that sometimes declines
to engage. That rewrite is committed to in advance here.

**Process note.** This confound survived Cell 8's verdict, the paper's Result
1 rewrite, an independent verification audit of all 45 published numbers, and
a full data-integrity audit — because every one of those checked whether the
NUMBERS were right, and none checked whether the PIPELINE PATH was the one the
claim assumed. Recomputation cannot catch a wrong causal attribution. Future
verdicts involving the council must assert the execution path, not just the
output value.

## EXECUTION-PATH AUDIT (2026-08-01) — how far the zero-route flaw reaches

Systematic sweep for the flaw class found while registering Cell 14: a claim
attributing an outcome to a prompt manipulation that the pipeline never
actually applied. Signature in code (council/orchestrator.py:495-510):
`synthesis_system_override` is used ONLY inside `if routes:`. With zero routes
the orchestrator uses LEAD_DIRECT_ANSWER_SYSTEM and silently DISCARDS the
override. Every prompt-ablation arm was therefore checked for zero-route runs.

**Result: 39 contaminated runs across 11 modes, and EVERY ONE is a case_7
(trigger-free) run.** No trigger-case run in any prompt-ablation cell has zero
routes.

| mode | zero-route runs | where |
|---|---|---|
| arch-council | 5/35 | all case_7 |
| c13-none / c1 / c2 / c3 / c4 / all | 5/35 each (30 total) | all case_7 |
| local-council-repro / -spec | 1/35 each | case_7 |
| local-council / -v2 | 1/7 each | case_7 |

**UNAFFECTED — zero contamination, claims stand:**
- Cell 6 register ablation (all 72 runs routed 3 seats)
- Cell 6c gain curve, k=0..3 x 3 Leads (all 72 routed 3)
- Cell 6c additivity, h=0..3 (all 24 routed 3 — the "h of 3" framing is exact)
- Cell 11 training arms (all 105 routed 3)
- Cell 8b intrinsic band (single-shot, no planner involved)
- All trigger-case volume numbers everywhere (30/35 routed per arm)
- Seat-level and per-family analyses
These cells used only the 6 trigger cases, which is why they escaped.

**AFFECTED — two published verdicts are wrong, not merely weak:**

1. **P8.2 (council's gate advantage) — WITHDRAWN.** arch-council's 0.00
   [0.00,0.00] is 5/5 zero-route runs: the council never consulted anyone and
   never ran the PRESERVE prompt. Its comparison against arch-single-spec's
   0.15 is a neutral direct-answer prompt versus a standing-instruction
   prompt, which is not a test of conditionality. We have NO valid measurement
   of instruction-level gating for the council.

2. **P13.3 ("every clause arm holds the gate at exactly 0.00") — WITHDRAWN,
   and it was never tested.** All six Cell 13 arms are 5/5 zero-route on
   case_7. All six therefore ran the IDENTICAL direct-answer prompt on the
   gate case. The six identical 0.00 values are not evidence that
   conditionality is a per-clause property; they are six measurements of the
   same prompt. The clause manipulation had no effect on those runs by
   construction. The Cell 13 verdict recorded this as "CONFIRMED, maximally" —
   that is retracted.

**Second path check (differential runtime directive).** The orchestrator
appends a recency directive to sub-questions when the planner flags a question
time-sensitive. If it fired at different rates across compared arms it would
confound them. It does not: Cell 13 arms 100% uniform, additivity arms 100%
uniform, Cell 11 arms 83% uniform, legal install arms 100% uniform. Cell 6c's
gain arms vary 83-100% (5/6 vs 6/6 on single runs at n=6) — within n=6 noise,
recorded but not disqualifying.

**Consequence.** Cell 14 is not an expansion of an existing result. It is the
FIRST valid test of instruction-level gating, because every previous gate
measurement on a council arm ran a prompt other than the one under test. Both
paper drafts must drop the calibration claim until Cell 14 reports.

**Root cause and fix.** A silent fallback: the override is dropped with no
error, no warning, and no field in the audit log recording which synthesis
prompt was actually used. Three checks should have caught it and did not
(Cell 8 verdict, 45-number verification audit, data-integrity audit) because
all three verified output VALUES. Fix going forward: every harness that passes
synthesis_system_override must assert routes are non-empty, and the run record
must persist which system prompt was used so path can be audited from the
ledger rather than reconstructed from code reading.

## CELL 14 VERDICT — P14.1 AND P14.2 BOTH FALSIFIED; THE CALIBRATION CLAIM IS DEAD (2026-08-02)

Decisive arms complete (15/15 each). Path audit verified on every council run:
specialists routed (healthcare / legal / finance, 5 runs each) and PRESERVE
APPLIED — the condition case_7 never satisfied.

| arm | pooled unwarranted qualification | case_8 | case_9 | case_10 | n |
|---|---|---|---|---|---|
| **council** | **0.64 [0.36,0.95]** | 0.49 | 0.15 | 1.27 | 15 |
| single + spec | 0.31 [0.21,0.42] | 0.19 | 0.27 | 0.47 | 15 |

**P14.1 FALSIFIED.** Registered threshold was an upper CI bound below 0.10.
Observed: 0.95. Not marginal — an order of magnitude past the criterion.

**P14.2 FALSIFIED.** Council and single+spec overlap, and the council's point
estimate is HIGHER (0.64 vs 0.31). The council is not better calibrated than a
lone prompted model on these questions; if anything it is worse.

**What this establishes.** The council's celebrated 0.00 [0.00,0.00] was
entirely an artifact of the planner declining to route on an off-topic
question, which bypassed the synthesis prompt. Given a trigger-free question
the planner DOES engage with, the council runs its conditional PRESERVE
clauses and hedges heavily on material warranting nothing — 1.27 on a pure
arithmetic depreciation question where every figure was stated.

The conditional form of the instruction does NOT suppress unwarranted
qualification. The mechanism we proposed for the council's advantage does not
exist, because the advantage does not exist.

**REGISTERED CONSEQUENCE EXECUTED.** Per the Cell 14 registration: "If P14.1
is falsified, the calibration paper's central claim is WRONG as stated and
must be rewritten." Actions:
- docs/paper_calibration.tex: the central claim is RETRACTED, not merely
  qualified. The paper cannot be repaired by rewording; its thesis is refuted.
- P8.2 (Cell 8): remains withdrawn, now with a positive disconfirmation rather
  than merely an invalid measurement.
- P13.3 (Cell 13): remains withdrawn (never tested).
- Any claim that orchestration buys calibration is removed from all drafts.

**WHAT SURVIVES, unchanged and unaffected by this cell:**
- Volume results: council 0.57 vs single+spec 0.50 (overlapping) — a lone
  prompted model matches the council on magnitude. STANDS.
- Multi-agent topology buys nothing on magnitude (flat 0.16 ~ single 0.14).
- The rendering/instruction-gain mechanism: instructions move output 3-4x with
  upstream text fixed; the gain curve; the clause isolation on trigger cases;
  sub-additivity.
- All training nulls at both loci, including the on-policy calibration reward.
- Intrinsic band model-invariance; specialists carry no inherent disposition.
- Seat tuning backfires (0.84->1.82 at the seat, 1.21->0.92 at the mouth).
None of these depend on a trigger-free measurement.

**The honest summary is now simpler and more negative:** across every
arrangement and every intervention we tested, we found no way to make a
pipeline qualify its claims selectively. We can raise how much it qualifies
(instructions, reliably, gradedly) and we can lower it (training, weakly). We
never achieved discrimination. The one arrangement that appeared to have it
was measured on a question it never actually processed.

Remaining arms (arch-flat, arch-single) still running; they are reference
points and cannot change either verdict.

## CELL 15 PRE-REGISTRATION — load dose-response (registered 2026-08-02, before any cases are written or runs made)

**Why.** After Cell 14, the council has no measured advantage on calibration
and none on volume (0.57 vs single+spec 0.50, overlapping). One place remains
where it beat a prompted single model: the trigger-heavy question, which
demands several DIFFERENT kinds of qualification at once. There the council
reached 0.91 [0.57,1.34] against single+spec's 0.48 [0.34,0.59] — 1.82x its
own baseline, where single+spec was flat at 0.94x and plain single at 1.02x.
All council runs on that case routed 3 seats; the result is uncontaminated.

That suggests the council's value is CAPACITY UNDER SIMULTANEOUS DEMAND rather
than better judgement: each specialist handles one domain and has attention to
spare, while one model asked for four things at once divides a fixed budget.
This cell tests that directly. It is the last hypothesis under which the
council architecture has any advantage at all, and it is registered with a
falsification that would close the question.

**Load definition.** L = the number of DISTINCT detectable behavior families a
question genuinely triggers, from the four we can measure: training-cutoff
disclosure, modeled-assumption flagging, jurisdictional distinguishing,
calibrated hedging. L is set by CONSTRUCTION when the question is written, not
by scoring model output.

**Design.** L in {1,2,3,4}, two questions per level (8 new questions), written
to hold length (80-110 words) and surface complexity constant so that load is
the only variable. L=0 is already measured: Cell 14's three trigger-free
questions. Arms: arch-council, arch-single-spec, arch-single.
8 cases x 5 seeds x 3 arms = 120 runs. Path audit persisted on every run.

**Predictions.**
- P15.1 (the council scales with load): council density rises monotonically in
  L, and L=4 exceeds L=1 with disjoint CIs. FALSIFIED IF flat or non-monotone,
  or if L=4 and L=1 overlap.
- P15.2 (the single model does not): single+spec shows no rise across L —
  L=4 and L=1 overlap. FALSIFIED IF single+spec rises comparably, which would
  mean load helps everything and the council is not special.
- P15.3 (a crossover exists): report the lowest L at which council exceeds
  single+spec with disjoint CIs. If no such L exists in 1-4, there is no load
  at which orchestration pays on this measure.
- P15.4 (exploratory, the routing confound): load and the number of routed
  specialists co-vary by construction, since higher-load questions span more
  domains. We record routes per run and report the association. This cell
  CANNOT separate "more demands" from "more specialists consulted"; a
  follow-up using single-domain high-load questions (all four families inside
  one domain, so L=4 with one seat) is the clean separation and is noted here
  rather than claimed.

**Registered consequences.** If P15.1 holds and P15.2 holds, the council has a
defensible positive claim — a capacity effect with a measurable threshold —
and this becomes the replacement result for the retracted calibration claim.
If P15.1 is FALSIFIED, the 1.82x was single-question noise and the council
architecture has NO measured advantage on any axis we have tested: not
content (a single 20B model already beat it on rubric coverage), not volume,
not calibration, not capacity. That conclusion would be reported as the
program's headline negative result rather than buried.

**Guard.** Questions are construction-labeled and committed BEFORE any run. A
question is not reassigned to a different L after seeing output. Length is
checked before running and reported.

### CELL 15 — deviation from registration, recorded before running
Registered question length was 80-110 words; realized is 61-79 (L1: 79/72,
L2: 65/67, L3: 66/62, L4: 64/61). The range is tight and matched, which is
what controls the confound, but it is below the registered band and is
recorded rather than silently accepted. Note the direction: the L=1 questions
are slightly LONGER than the L=4 ones, so any length effect works against
P15.1 rather than for it.

## CELL 15 VERDICT — P15.1 FALSIFIED; THE COUNCIL HAS NO MEASURED ADVANTAGE ON ANY AXIS (2026-08-02)

Decisive arms complete (council 40/40, single+spec 40/40; arch-single floor
reference still running and cannot change any verdict).

| load | council | single + spec | separation |
|---|---|---|---|
| L=1 | 0.51 [0.25,0.78] | 0.57 [0.37,0.80] | overlap |
| L=2 | 0.99 [0.52,1.58] | 0.71 [0.43,1.00] | overlap |
| L=3 | 0.73 [0.54,0.95] | 0.62 [0.44,0.82] | overlap |
| L=4 | 0.60 [0.29,1.02] | 0.45 [0.33,0.55] | overlap |
| pooled | 0.71 [0.53,0.91] | 0.59 [0.48,0.70] | overlap |

**P15.1 FALSIFIED.** Council rho = +0.20, non-monotone, L=4 overlaps L=1. The
council does not scale with load.
**P15.2 CONFIRMED** but now uninformative: single+spec is flat (rho -0.40,
L4 vs L1 overlapping), exactly as predicted — but with the council also flat,
"the single model does not scale" no longer distinguishes anything.
**P15.3: NO CROSSOVER EXISTS in L=1..4.** There is no load at which the
council separates from a lone prompted model.

**The earlier 1.82x was single-question noise.** Between-question variance at
FIXED load exceeds anything across loads: at L=2 the two questions give 0.42
and 1.57. Two questions per level is the only reason this is visible; one per
level would have produced a clean-looking curve made entirely of noise.

**Second observation, independently damaging to the capacity story.** The
council engages only 1.2-1.7 of the four behavior families regardless of what
the question demands (L=1: 1.2, L=2: 1.2, L=3: 1.7, L=4: 1.3). Asked for four
distinct kinds of qualification it does not produce four; it re-expresses the
same one or two at slightly varying density. It is not dividing labour across
specialists and covering more ground.

**REGISTERED CONSEQUENCE EXECUTED.** Per the Cell 15 registration: if P15.1
falsifies, "the council architecture has NO measured advantage on any axis we
have tested." That is now the finding. The complete scorecard:

| axis | result |
|---|---|
| content (rubric coverage) | a single 20B model beat the council, 42% vs 25-31% |
| disposition volume | council 0.57 vs prompted single 0.50 — overlap |
| calibration | council 0.64 vs 0.31 — council WORSE (Cell 14) |
| capacity under load | flat, no crossover at any L (this cell) |

**This is the program's headline result, and it is negative.** A four-model
council, on every axis we could measure, is matched or beaten by one model of
comparable size with a good instruction — at roughly a quarter of the compute.

What survives is not about the council at all: instructions move output 3-4x
with upstream text held fixed, gradedly and targetedly; weight training fails
at both loci under every reward tried; models share an intrinsic band and
differ in instruction responsiveness; and tuning specialists upward degrades
the finished answer. The positive contribution is about where in a pipeline
epistemic behavior is decided, not about whether pipelines are worth building.

### CORRECTION — the "model-invariant intrinsic band" is largely a FLOOR + LENGTH artifact (2026-08-02)

Scrutiny of the Cell 8b claim. Density hides two things. Raw marker counts per
run, trigger cases, neutral prompt:

| model | mean markers/run | runs with ZERO markers | median output len | density |
|---|---|---|---|---|
| Med42-8B | 0.37 | **80%** | 2,424 | 0.15 |
| Mistral-7B-Instruct | 0.47 | **77%** | 3,218 | 0.14 |
| Qwen2.5-7B-Instruct | 0.57 | **70%** | 3,916 | 0.14 |
| gpt-oss-20B | 1.23 | 33% | 8,955 | 0.14 |

Two problems with "these models share a characteristic band":
1. **Floor.** For three of four models, 70-80% of runs contain ZERO markers.
   The distributions are mostly zeros; we are not resolving a common LEVEL, we
   are failing to distinguish near-empty distributions.
2. **Length normalization.** gpt-oss emits 3.3x more markers than Med42 in raw
   terms (1.23 vs 0.37) and writes 3.7x more text, so per-1000-char density
   coincides. "Same density" and "same amount" are different claims and we
   have been eliding them.

**Corrected claim.** Under a neutral prompt these four models produce
*almost no* epistemic qualification — most responses contain none — and at
that floor we cannot distinguish them. This is weaker than "models share an
intrinsic band" and should replace it everywhere.

**What still holds, and why the argument survives.** The load-bearing use of
this result was never the invariance itself but the contrast: a
domain-specialised model is not inherently more careful. Med42 produces zero
markers in 80% of neutral-prompt runs and 1.31 density as an instructed
pipeline seat. That contrast is robust to both objections — it is a
within-model comparison, so length normalization affects both sides, and it
spans the floor rather than sitting on it.

Likewise the claim that models differ in how strongly they answer an
instruction stands on the instructed measurements (0.5-1.2 spread), not on the
neutral ones.

**Process note.** This is the third claim in this program weakened by asking
"what is the measurement actually doing" rather than "is the number right."
Density with no floor guard has now produced two defects (this, and the
BioMistral degenerate-output arm). Any future use of a per-1000-char rate
should report the raw event count and the zero-rate alongside it.

## CELL 16 PRE-REGISTRATION — GRPO on the Lead (registered 2026-08-02, before any training)

**Why.** The paper's central claim is that weight-level training cannot install
epistemic behavior at the final writer. It rests on two nulls, BOTH of which
were explicitly registered as SURROGATES for real reinforcement learning:
Cell 6b (offline ORPO, 88 pairs) and Cell 11 (best-of-n distillation with a
calibration reward, 49 pairs). The obvious reviewer objection — "you did not
actually do RL" — currently has no answer. mlx-lm-lora 2.1.0 supports GRPO
with custom programmatic rewards, and the 108 precomputed synthesis contexts
from Cell 11 survive on disk. This closes the objection or overturns the null.

**Why it is tractable.** The Lead's synthesis step is an ordinary single-turn
generation from a fixed prompt; the pipeline only supplies that prompt. With
upstream precomputed, GRPO operates on a normal prompt distribution with NO
pipeline execution in the training loop. The reward is programmatic (regex),
requires no learned reward model and no human labels, and runs in
milliseconds. GRPO needs no value network, which is what makes a 7B policy
feasible on 32 GB.

**Design.** Policy: Qwen2.5-7B-Instruct, LoRA r8 / 16 layers / seed 42, matched
to Cells 6b and 11 so the three results are directly comparable. Prompts: the
108 Cell-11 contexts (76 trigger-heavy, 32 trigger-free), construction-labelled
before any of this work. group_size and max_completion_length set by the
timing probe below and recorded before the run. KL term retained (beta>0) to
keep the policy near the reference.

**REWARD FUNCTION (fixed here; any later change invalidates the cell).**
For completion s with prompt label in {heavy, light}, over the FOUR detectable
families (cutoff, modeled, jurisdictional, hedging):

  guards, applied first:
    len(s) < 1200 or len(s) > 8000            -> R = -1.0 (hard, terminal)
    max_family_share > 0.8 and total >= 4     -> R -= 0.5

  heavy:  R = breadth(s)/4 + 0.25 * min(density(s), 1.5)/1.5
  light:  R = -breadth(s)/4 - 0.25 * min(density(s), 1.5)/1.5

breadth = number of distinct families present. Chosen over density, CDS,
retention and ALR on measured grounds:
- density: 65% of markers in real text concentrate in ONE family, so a count
  or density reward is maximised by repetition.
- CDS: corr(CDS, density) = +0.97 on 648 real syntheses. The sqrt(breadth)
  factor barely moves it; CDS inherits density's exposure.
- retention (final density / seat density): the denominator is CONSTANT within
  a prompt group and GRPO normalises advantage within that group, so retention
  is mathematically IDENTICAL to density here. It is not a safeguard.
- ALR: a ratio between configurations, not computable for a single completion.
- breadth: immune to repetition, not length-normalised. Its own exposure is
  corr(breadth, length) = +0.41, i.e. a LENGTHENING incentive — which is what
  the upper length guard at 8000 chars exists to bound. Recorded, not hidden.

Conditionality lives in the prompt distribution: identical weights are pushed
up on heavy contexts and down on trigger-free ones. Training reward is regex
(fast). Hack detection uses NLI and blinded judges, POST HOC only.

**Predictions.**
- P16.1 (the substantive test, identical in form to Cell 11's P11.1 so the
  three attempts are comparable): the trained Lead benched at k=0 exceeds the
  stock Lead at k=0, bootstrap CIs disjoint. FALSIFIED IF CIs overlap.
- P16.2 (reward hacking, registered as the EXPECTED outcome): the reward rises
  by more than half its achievable range while at least one degradation
  indicator fires — median completion length leaving the natural band
  (1846-4711, p5-p95 of 648 real syntheses), per-family concentration rising
  above the observed 0.65 baseline, or blinded judges preferring stock output.
  FALSIFIED IF the reward rises with every indicator clean, which would be the
  strongest possible result and is not what we expect.
- P16.3 (exploratory): does the instruction gain survive training, as it did
  in Cell 11 (1.58x vs stock 1.82x)?

**Registered consequences, all three branches.**
1. P16.1 confirmed AND P16.2 falsified (clean gain): the paper's central claim
   is AMENDED. Weights CAN install this given genuine policy optimisation, and
   the prior nulls are attributed to method rather than to the register. Major
   revision.
2. P16.1 falsified: "weights cannot do this at feasible scale" hardens from
   three attempts to four, one of them real policy optimisation with a
   pipeline-mouth reward. Strongest available form of the claim.
3. P16.1 confirmed BUT P16.2 confirmed (reward rose, text degraded): the
   finding is about the METRIC, not the register. This would mean our density
   and breadth measures can be inflated without the text becoming more
   careful, which would put every quantitative claim in the paper in question.
   Reported as such, prominently, not as a footnote.

**Instrumentation, required from step 0.** Log per step: mean reward, median
completion length, per-family concentration, distinct-family histogram, KL
from reference. A reward curve without these is uninterpretable.

### DISK CLEANUP (2026-08-02) — 23GB -> 56GB free
Removed, with before/after verification that every benchmark model still
serves and every trained adapter survives:
- train/models/Qwen25-Lead-ORPO-fused (14GB) — reconstructible from base +
  adapter; its GGUF and ollama model already existed.
- train/gguf/*.gguf (13GB) — source files for `ollama create`; ollama holds
  its own blobs. All three Lead models verified serving AFTER deletion.
- 10 intermediate adapter checkpoints (0000050_*, etc.); the 8 final
  adapters.safetensors are intact and are the non-reconstructible artifacts.
- ollama openbiollm-fixed:coe and openbiollm-v2:coe (9.8GB) — the two failed
  template builds for the withdrawn OpenBioLLM arm.
NOT touched: train/models/Qwen2.5-7B-Instruct (needed for the MLX conversion
Cell 16 requires) and train/models/Qwen-Open-Finance-R-8B (31GB, gated base —
user's decision).

### CELL 16 — REGISTERED DEVIATION (2026-08-02, before training starts)

**Timing probe (measured, 8 completions on real Cell-11 synthesis contexts,
qwen 7B Q4 via ollama):** median 86.9 s/completion at cap 1024 and 81.8 s at
cap 2048. Throughput 9-11 tok/s. Completions self-terminate at ~800 tokens /
~4,300 chars regardless of cap, so the completion cap is NOT a usable lever —
an assumption I had made and the probe refuted.

**Deviation.** Registered design was 108 prompts. All feasible configurations
cost ~11 h: 108x1 epoch (~108 updates), 60x2 (~120), 40x3 (~120). Since the
update count is near-identical, the choice is diversity vs epochs. We take
**40 stratified prompts (28 heavy / 12 trigger-free), group_size 4, 3 epochs**,
because GRPO is on-policy: the value of later epochs is that the policy has
changed and generates new completions from the improved policy. A single epoch
over 108 prompts would be one round of improvement per context and never
revisit — structurally close to the Cell 11 best-of-n surrogate this cell
exists to move past. group_size stays at 4; at 2 the within-group advantage
estimate is too noisy.

**Cost of the deviation, and the diagnostic it enables.** 40 contexts risks
overfitting. The 7 bench cases were held out of the training prompt pool from
the start, so this becomes a diagnostic rather than a confound. Reporting the
training reward curve ALONGSIDE the held-out bench separates three outcomes
that are otherwise indistinguishable:
  reward flat                 -> weights cannot represent this
  reward rises, bench flat    -> learned prompt-specific tricks / hacking
  reward rises, bench moves   -> the null is overturned
Only the third rewrites the paper, and only this design distinguishes it from
the second.

**Reward verified before launch** (train/cell16_reward.py, fixed at
registration): real Cell-11 samples score mean +0.62 (min -0.09, max +1.00)
against a ceiling of +1.25, so there is genuine headroom. Guards behave:
empty -> -1.00, sub-1200 chars -> -1.00, and a pure single-family repetition
of 6,800 chars -> +0.00 (breadth 0.25 + density 0.25 - concentration penalty
0.50). Repetition is exactly unprofitable by construction.

**Honest scope.** 40 prompts and ~120 updates is still small by RL standards;
real RLHF uses thousands of prompts. This closes the "you did not do RL"
objection considerably further than best-of-n did, but does not settle it, and
the paper will say so.

## CELL 16 — REGISTRATION REWRITTEN BEFORE ANY TRAINING (2026-08-02)

The breadth-reward design above is SUPERSEDED. No training was completed under
it (first launch aborted at step 0 on Metal OOM). Rewritten around a
seat-derived PRESERVATION reward, which targets the paper's actual claim.

**The observation that motivates it.** The discrimination signal exists
upstream and is destroyed at the writing step:

| | trigger-heavy | trigger-free | ratio |
|---|---|---|---|
| families the SEATS raise | 2.51 | 0.97 | **2.6x** |
| families the LEAD emits (Cell 15) | 1.2-1.7 | 1.2-1.7 | ~1.0x |

Measured preservation: 74% of raised families survive on heavy prompts, 52% on
trigger-free ones (216 completions). The specialists already know when to
qualify. The Lead does not. Every reward tried so far (Cells 6b, 11, and the
superseded design) measures PRODUCTION of markers. This one measures
FAITHFULNESS TO UPSTREAM, and is conditional by construction: a flag never
raised cannot be preserved.

This makes the experiment sharp. The PRESERVE instruction achieves conditional
propagation in one sentence. Can reinforcement learning install the same
behavior in weights? A null here is far stronger than "we trained on marker
counts and nothing happened."

**REWARD (fixed at registration; any change invalidates the cell).** Seat
contributions are parsed from the synthesis prompt, which contains them
verbatim, so no extra model calls are needed. Over the four detectable
families:

  raised   = families flagged by ANY seat in the prompt
  kept     = raised & families present in the completion
  spurious = families in the completion NOT raised by any seat

  guards, applied first:
    len < 1200 or len > 8000                      -> R = -1.0 (terminal)
    8-gram overlap with seat text > 0.35          -> R = -1.0 (copy-paste)

  R = kept/max(raised,1) - 0.5 * spurious/4 - 0.5 * max(0, overlap - 0.15)/0.20

Preservation is the signal; spurious qualification is penalised (this is what
makes it conditional rather than a production reward); the graded overlap term
discourages verbatim copying below the hard cap. Prompts with raised=0 yield
R=0 for a clean completion and negative for a hedging one, which is exactly the
trigger-free behavior we want and have never achieved.

**Registered ceiling.** The reward inherits the seats' own miscalibration:
they raise ~0.97 families even on trigger-free prompts, so a Lead perfectly
tracking them would still over-hedge. Achievable discrimination is capped near
the seats' 2.6x. Recorded now, not discovered later.

**Predictions.**
- P16.1 (unchanged in form, so all four training attempts stay comparable):
  the trained Lead benched at k=0 exceeds the stock Lead at k=0, CIs disjoint.
  FALSIFIED IF they overlap.
- P16.2 (the discrimination test, new and the real point): the trained Lead's
  heavy-to-trigger-free family ratio exceeds the stock Lead's ~1.0, moving
  toward the seats' 2.6x. FALSIFIED IF it stays flat.
- P16.3 (hacking, expected): reward rises while overlap climbs above its 9%
  baseline, or length leaves the 1846-4711 band, or judges prefer stock output.
- P16.4 (exploratory): does the instruction gain survive, as in Cell 11
  (1.58x vs stock 1.82x)?

**Consequences.** If P16.2 holds, RL CAN install conditional propagation and
the paper's central claim is amended — this would be the first success against
four failures. If P16.1 and P16.2 both fail, "weights cannot install this"
now rests on an attempt whose reward was aligned with the very instruction that
does work, which is the strongest available form. If reward rises but the bench
is flat, the finding is overfitting to 40 contexts and will be reported as such.

**Carried over:** group_size 2 (forced by the measured 7.7 GB logits tensor at
group 4; degenerates GRPO to a binary preference signal, i.e. approximately
online DPO, while retaining on-policy iteration), 40 stratified prompts,
3 epochs, LoRA r8/16 layers/seed 42 matched to Cells 6b and 11.

### CELL 16 — reward validated before launch (2026-08-02)
Guards, all verified on real data: empty / <1200 chars -> -1.00; verbatim copy
of seat text -> -1.00; a degenerate "spurious hedging" completion that hits the
right families with repeated boilerplate -> -1.00. That last hack scored +0.54
under the first implementation and motivated a SELF-REPETITION guard
(distinct-5gram ratio below 0.45 is terminal), because family matching alone is
coarse: a completion can touch a family with one stock phrase without
preserving anything specific. The guards reject 9% of REAL Cell-11 samples,
which is the intended strictness rather than an error.

**Weak separation, recorded honestly.** Heavy prompts score +0.48 and
trigger-free +0.38 — a gap of only 0.11. This is the registered ceiling
appearing in the data: the seats themselves raise ~0.97 families on
trigger-free prompts, so a completion that faithfully preserves what was
raised scores well even when little was warranted. Faithfulness to the seats
is NOT the same as calibration, because the seats are not calibrated. P16.2
therefore tests a signal the reward encodes only weakly, and a null on it would
be evidence about the ceiling as much as about the Lead.

## CELL 16 — NOT EXECUTABLE ON THIS HARDWARE (2026-08-03)

Every configuration attempted aborts at step 0 with METAL
"Insufficient Memory". This is a feasibility limit, recorded as a result
rather than retried indefinitely.

| attempt | group | LoRA layers | completion cap | outcome |
|---|---|---|---|---|
| 1 | 4 | 16 | 1024 | OOM at step 0 |
| 2 | 2 | 16 | 1024 | OOM at step 0 |
| 3 | 2 | 8 | 512 | OOM at step 0 |
| 4 | online_dpo | 8 | 512 | OOM, and additionally tried to download a SECOND 7B judge model |

**Root cause, measured not guessed.** Machine is 34.4 GB total with ~19 GB
actually free (~15 GB held by desktop applications and the OS). Training
prompts are long by construction because they contain three full specialist
contributions: median 2154 tokens, max 2782. Qwen2.5's vocabulary is 151,665.
GRPO materialises full-sequence logits for BOTH policy and reference:
seq(~2666-3178) x vocab x fp32 = 3.2-3.9 GB per sequence, doubled for the
reference, on top of a 4-bit 7B model, gradients and optimizer state. Reducing
group size, LoRA layers and completion length together was not sufficient. The
logits tensor scales with sequence length and vocabulary, neither of which the
available knobs reduce.

**Consequence for the paper — the wording matters.** We must NOT write "GRPO
failed" or "RL failed". We never ran it. The supportable statement is:

  Weight-level training failed under offline preference optimization (ORPO,
  CPO) at both loci and under an on-policy best-of-n distillation with a
  pipeline-mouth reward. Full policy-gradient RL could not be attempted: on a
  34 GB machine, GRPO on a 7B policy with ~2.2k-token prompts and a 152k
  vocabulary exhausts memory before the first update. The objection "you did
  not do real RL" therefore stands, and we state it rather than obscure it.

This is also a useful negative result for replication: anyone attempting
pipeline-level RL on consumer hardware will hit the same wall, and the binding
constraint is prompt length x vocabulary, not model size.

**Options not taken (recorded for whoever picks this up):** truncating the
specialist contributions would fit but changes the experiment; a smaller
policy (e.g. Qwen2.5-1.5B) would shrink weights and activations but NOT the
logits tensor, which is seq x vocab regardless of model size, and would break
comparability with Cells 6b and 11 which both used the 7B Lead.

## FOURTH PAPER — "What Aggregation Does to Epistemic Content" (docs/paper_behavior.tex, v0.1, 2026-08-03)

A behavioral characterization of the aggregation step, 7pp. Same corpus, no
new runs. Written to the brief: scientific description of how multi-seat
architectures BEHAVE, not an argument that we succeeded or failed.

**The structural move that makes it work: negatives become INVARIANCES.**
"Weight training did nothing" reads as failure in an outcome paper; "the step
is invariant under weight-level training at either locus" is a constraint on
any behavioral account, and belongs in a characterization. The paper is
organized as: what the step does to content (provenance), what it responds to
(instructions), what leaves it unmoved (everything else), then a compact
description.

**New centerpiece measurement and figure (figs/fig_provenance.pdf):**

| question type | raised | preserved | discarded | invented | traceable |
|---|---|---|---|---|---|
| trigger-heavy | 2.51 | 1.81 | 0.70 | 0.12 | 94% |
| trigger-free | 0.97 | 0.68 | 0.29 | **0.38** | **64%** |

Three regularities: discard is PROPORTIONAL (28% / 30%, independent of
supply); invention COMPENSATES (triples in absolute terms when upstream is
thin, so over a third of trigger-free output traces to no specialist); and
distinctions COMPRESS (the seats' 2.59x becomes 1.82x at the page).

Unifying description: the step behaves as though it has a TARGET LEVEL of
epistemic content — given more it trims, given less it fills. That single
account retro-explains four previously separate puzzles: why seat-tuning
backfires, why output looks input-independent, why the trigger-free failure
occurs, and why the upstream distinction attenuates.

**Two post-hoc predictions the paper states as supported rather than tested:**
interventions raising upstream qualification should be counterproductive (they
are), and apparent input-indifference should be strongest where input is
thinnest (94% vs 64% traceability).

**Honest content retained, compressed:** the RL infeasibility (memory limit
stated precisely, invariance scoped to offline preference optimization and a
best-of-n surrogate), the withdrawn degenerate arm, the zero-route
mis-measurement and its correction, and the split-session provenance defect.
These sit in Limitations as two short paragraphs rather than as narrative.

**Relationship to the other drafts.** paper.tex asks where disposition is
decided; paper_witnesses asks what specialists are for; paper_calibration is
retracted; this one asks what the aggregation step does to content that passes
through it. This is the most defensible of the four because its core claim is
a measurement rather than an interpretation.

## TENSION ENUMERATION — new section in paper_behavior (2026-08-03)

Of the four prompt/architecture components asked about (step-back prompting,
the synthesizer, the register, tension enumeration), three are borrowed or
weakened and one is novel and measurable.

- step-back prompting: borrowed (cited), never ablated, no evidence either way.
- synthesizer as a component: standard in MoA / Parallel-Synthesis.
- register: DE-EMPHASISED. We weakened it ourselves (floor + length artifact)
  and Voice Under Revision found the same effect independently in another
  domain. Not ours and weaker than claimed.
- **tension enumeration: novel, structurally unique, and now measured.**

**Structural separation is categorical, not graded:**

| arrangement | runs | responses with a tensions section | tensions/response |
|---|---|---|---|
| council (all variants) | 195 | 86-100% | 3.0-3.9 |
| flat merge | 50 | **0%** | 0.00 |
| single model + instruction | 90 | **0%** | 0.00 |

A single model cannot produce this by construction: identifying a conflict
requires more than one source to conflict. This is the only output in the
whole program where the pipeline is not matched by a well-prompted single
model.

**Grounding, figure-citing tensions (unambiguous check): 89% grounded**
(n=210, median 100% per response), 11% cite a figure appearing nowhere
upstream. Against the step's 64% traceability for caveats on thin input, this
says the step **invents caveats far more readily than it invents
disagreements** — different behaviors, and the asymmetry is the finding.

**The extension FAILED, and the failure is reported as the result.** NLI
entailment does not transfer to this material. On the figure-citing subset
where both methods apply: figure-matching 89%, NLI 16%, agreement 23%.
Decomposing each tension into component clauses (a tension is a compound
contrastive claim, "A recommends x but B assumes y") raises NLI to 48% with at
least one clause supported, median best-clause entailment 0.57 — sitting just
under our 0.60 threshold, i.e. clustered at the decision boundary.

Diagnosis: a tension clause is a PARAPHRASED SUMMARY of specialist content,
not a restatement, and no single upstream sentence entails a claim combining
two contributions plus a conflict framing. The instrument measures paraphrase
distance, not groundedness. We report the figure-based number and record the
139 qualitative tensions as NOT MEASURABLE with the instruments we have;
settling them needs human judgement or a judge shown both contributions.

**Third instrument-validity finding in this program** (after the finance
"reversal" retired as a pattern artifact, and density's floor/length
confound). Pattern: the disagreement between instruments has repeatedly been
more informative than either number.

## PROVENANCE REPLICATION (2026-08-03) — confirms the phenomenon, CORRECTS our framing

Recomputed provenance on 358 council runs carrying seat turns, spanning four
writers (gpt-oss-20B, Phi-4-14B, Qwen2.5-7B stock and trained) and nine arms.
No new runs; the seat text was already in every audit log.

**Per-writer, by condition:**

| writer | arm | heavy traceable | trigger-free traceable | n |
|---|---|---|---|---|
| gpt-oss-20B | arch-council | 81% | **33%** | 70 / 15 |
| gpt-oss-20B | c13-all | 95% | - | 30 / 0 |
| Phi-4-14B | local-council-repro | 89% | 100% | 30 / 4 |
| Qwen2.5-7B trained | cell11-cal-k3 | 96% | 50% | 30 / 5 |
| Qwen2.5-7B stock (reference) | cell11 corpus | 94% | 64% | 456 / 192 |

High traceability on demanding questions replicates on ALL FOUR writers
(81-96%). The drop on trigger-free questions replicates on two of three
testable arms.

**The apparent Phi-4 exception is a confirmation, not a counterexample.** Its
four trigger-free runs are case_7, where the seats raised 3.00 families — an
OVERSUPPLY condition. The writer trimmed (3.00 raised -> 1.25 kept) and
invented nothing. gpt-oss's trigger-free runs use the purpose-built Cell-14
cases where seats raised only 0.40 — undersupply — and there invention
dominates. The variable is SUPPLY, not question type.

**Restated as a dose-response (n=358, pooled):**

| seats raised | n | kept | invented | output | traceable |
|---|---|---|---|---|---|
| 0 | 17 | 0.00 | 0.53 | 0.53 | 0% |
| 1 | 34 | 0.50 | 0.26 | 0.76 | 65% |
| 2 | 82 | 1.06 | 0.29 | 1.35 | 78% |
| 3 | 180 | 1.63 | 0.07 | 1.71 | 96% |
| 4 | 45 | 1.98 | 0.00 | 1.98 | 100% |

Invention declines monotonically with supply; traceability rises
monotonically 0% -> 100%; corr(raised, invented) = -0.33. At zero supply the
writer emits 0.53 families invented wholesale.

**CORRECTION to our own framing.** The paper says the step "writes toward a
target level," trimming when oversupplied and filling when starved. The
dose-response does not support the strong version: corr(raised, output) =
+0.41 and output rises 0.53 -> 1.98 across the range, so output DOES track
supply, just sub-proportionally. The supportable claim is PARTIAL
COMPENSATION - the writer supplements scarce input, compensation is strongest
at the bottom and vanishes by three to four families - not a stabilised target.
The binary heavy/trigger-free table should be replaced by this dose-response,
which is stronger evidence (monotone, n=358, four writers) and a weaker claim.

## CELL 17 PRE-REGISTRATION — the suppression clause (registered 2026-08-03, before any runs)

**Motivation.** The writing instruction specifies what to PRESERVE (clauses
2-4, each conditional on something a specialist did) and never what NOT to
add. Invention is the half that produces the failures, and it scales with
scarcity: 0.53 families invented at zero supply, falling to 0.00 at full
supply (n=358, four writers). This cell tests whether the missing half is
addressable by stating it.

**Treatment.** The production synthesis prompt plus one clause:

  6. DO NOT INTRODUCE qualifications, caveats, assumptions, or jurisdictional
     distinctions that no specialist raised. If the specialists did not flag
     uncertainty about something, state it plainly.

Everything else identical. Writer: gpt-oss-20B in every role, matching Cells
8/13/14 so the existing production-prompt runs serve as the baseline without
re-running them (c13-all on the six trigger cases, arch-council on the three
on-topic trigger-free cases).

**Cases.** All six trigger cases plus the three Cell-14 on-topic trigger-free
cases, giving the full supply range in one arm. 9 cases x 5 seeds = 45 runs.
Routing and the applied synthesis prompt are asserted per run and persisted,
per the execution-path fix.

**Predictions.**
- P17.1 (it suppresses invention): invented families fall relative to the
  production baseline, most on low-supply runs. FALSIFIED IF invention is
  unchanged.
- P17.2 (it is TARGETED, not a blunt volume reducer): preserved families do
  NOT fall materially. FALSIFIED IF preservation drops alongside invention,
  which would mean the clause simply makes the writer quieter and is useless
  as a remedy. **This is the discriminating prediction; P17.1 alone is not
  interesting, because any instruction to say less will reduce everything.**
- P17.3 (exploratory): traceability, and whether the seats' 2.6x
  discrimination reaches the page any better.

**Consequences.** If P17.1 and P17.2 both hold, the behavior paper gains a
TESTED intervention and the diagnosis becomes actionable: the instruction was
half-specified, and completing it fixes the failure. If P17.1 fails, invention
resists the obvious remedy and that is reported as such — the behavior is
deeper than a missing instruction. If P17.1 holds but P17.2 fails, the clause
works by suppressing everything and is reported as a non-solution.

## CELL 17 VERDICT — the suppression clause does not suppress (2026-08-03, 45 runs, zero failures)

| condition | arm | raised | preserved | invented | traceable | n |
|---|---|---|---|---|---|---|
| trigger-heavy | production | 3.13 | 1.83 | 0.10 | 95% | 30 |
| trigger-heavy | + suppression | 2.97 | 1.77 | 0.11 | 94% | 35 |
| trigger-free | production | 0.40 | 0.27 | **0.53** | 33% | 15 |
| trigger-free | + suppression | 0.53 | 0.53 | **0.40** | 57% | 15 |

**P17.1 FALSIFIED.** Invention did not fall on either condition. Trigger-heavy
0.10 -> 0.11 (no change, and nothing to suppress at 95% traceability
already). Trigger-free 0.53 -> 0.40, intervals overlapping heavily
[0.27,0.80] vs [0.13,0.73]. The clause does not reliably suppress invention
where invention actually happens.

**P17.2 CONFIRMED but moot.** Preservation held everywhere (1.83 -> 1.77;
0.27 -> 0.53), so the clause is not a blunt volume reducer. That was the
discriminating prediction and it passes — but it only matters if P17.1 had
held, and it did not.

**An unregistered observation, reported as such.** On trigger-free runs
preservation ROSE 0.27 -> 0.53 while upstream supply also rose 0.40 -> 0.53,
and traceability went 33% -> 57%. Both arms are n=15 with different random
seat outputs, so the supply difference is sampling, not treatment. The
traceability gain therefore cannot be attributed to the clause: with more
raised upstream there was more to preserve. We flag this because it is the
kind of number that would be easy to present as a win and is not one.

**REGISTERED CONSEQUENCE EXECUTED.** Per the Cell 17 registration: "If P17.1
fails, invention resists the obvious remedy and that is reported as such —
the behavior is deeper than a missing instruction." That is the finding.

**Interpretation.** The instruction set is not simply half-specified. Telling
the writer plainly not to introduce qualifications nobody raised does not stop
it doing so. Combined with the dose-response (invention scales with scarcity,
0.53 families at zero supply), the behavior looks less like a gap in the
instructions and more like the writer filling to a floor it will not go below
regardless of what it is told. That is a stronger and more interesting claim
than "add the missing clause", and it is the one the data supports.

**Consequence for the behavior paper.** The intended fourth section — one
tested intervention — reports a NEGATIVE intervention. The paper's structure
survives: characterization, the gap, what moves it and what does not, and now
an attempted remedy that fails. Invention joins the list of properties
invariant under instruction, which is notable because instructions move
everything else we measured.

## CELL 18 PRE-REGISTRATION — provenance-rewarded training (registered 2026-08-04, before any pairs are built or training run)

**Why a fourth training attempt.** Cells 6b and 11 both optimised PRODUCTION
objectives — density, then calibration (more where warranted, less where not).
Cell 11's own registered P11.3 asked whether reward SHAPE was the binding
constraint and answered no. This cell changes the objective CLASS, not its
shape: from how much the writer emits to whether what it emits came from
upstream. That is the quantity our characterisation identifies as the failure
(invention scaling with scarcity, 0.53 families at zero supply), and no prior
arm targeted it.

**Why it may work where three attempts did not.** Preference optimisation can
only select behaviour already present in the sampling distribution. Scoring
the existing 648 stock-model samples by provenance shows the target behaviour
is present: per prompt, the best sample both PRESERVES MORE and INVENTS LESS
than the worst (heavy: kept 2.39 / invented 0.01 vs kept 1.04 / invented 0.26;
light: kept 0.97 / invented 0.09 vs kept 0.31 / invented 0.75). Spread is
usable on 88 of 108 prompts. Cell 11's target may never have appeared in its
own samples, in which case there was nothing to select. This is an argument,
not evidence, and is recorded as such.

**Design.** No new generation. Score all 648 existing Cell-11 samples with
  provenance(s) = kept/max(raised,1) - 0.5 * invented/4
where raised/kept/invented are behavior families derived from the specialist
text already present in each synthesis prompt. chosen = argmax, rejected =
argmin per prompt; keep prompts whose spread >= 0.25. Cap at 88 train pairs,
matching Cell 6b's realised dose exactly so the three training arms are
dose-comparable. ORPO, LoRA r8 / 16 layers / lr 5e-6 / seed 42 / seq 4096 —
the Cell 6b recipe verbatim. Gates carried from Cell 11: length ratio in
[0.8,1.4], and the NLI directional cross-check.

**Bench.** 7 cases x 5 seeds x 1 arm = 35 runs (cell18-prov-k3), against two
existing baselines that need no re-running: cell6b-lead-repro (stock) and
cell11-cal-k3 (calibration-trained). All three arms then share model,
trainer, dose and recipe, differing only in objective class.

**Predictions.**
- P18.1 (the substantive test): invented families at the pipeline mouth fall
  against the stock Lead, bootstrap CIs disjoint. FALSIFIED IF they overlap.
- P18.2 (targeted, not a volume knob — the DISCRIMINATOR): preserved families
  do NOT fall materially against stock. FALSIFIED IF preservation drops
  alongside invention, which would mean the model learned to say less. Same
  discriminator that made Cell 17 interpretable.
- P18.3 (exploratory): does traceability rise, and does the seats' 2.6x
  discrimination reach the page any better than the stock 1.0x?

**Registered consequences.**
1. P18.1 and P18.2 both hold: weight-level training CAN correct aggregation
   distortion when the objective is faithfulness rather than production. This
   would be the first positive training result in the programme and would
   materially change the paper — the invariance-under-training claim becomes
   invariance-under-PRODUCTION-objectives only.
2. P18.1 falsified: weight training has now failed under THREE distinct
   objective classes — production, calibration, faithfulness — at the same
   locus with the same recipe and dose. That is a substantially stronger
   statement than three failures under one objective, and is how it will be
   reported.
3. P18.1 holds but P18.2 fails: the model learned to say less. Reported as a
   non-solution, exactly as Cell 17's clause would have been.

**Prior.** Three prior training attempts at this locus produced nulls. We
expect a null and are running it because the objective class is genuinely
new and the target behaviour is demonstrably in-distribution.

### CELL 18 — dose deviation recorded before training
Registered cap was 88 train pairs (matching Cell 6b). Realised: 71. The
binding filter was the carried-over length-ratio gate [0.8,1.4] — 79 of 108
prompts survived spread>=0.25 AND the ratio gate, leaving 71 after the
valid/test holdout. That is 81% of Cell 6b's dose, so the three arms are
comparable but not exactly dose-matched, and any null must be read with that
in mind. Pair quality is strong: chosen keep 2.18 / invent 0.03, rejected
keep 0.78 / invent 0.33 — separated on BOTH dimensions, which is what the
objective requires. Mix 60 heavy / 19 light.

## CELL 18 — BENCHED ON THE WRONG CONDITION (2026-08-04, harness error, owned)

Training and packaging completed cleanly (284 iters, val loss 0.069,
qwen-lead-prov:coe serving). Bench 35/35, zero failures. The RESULT is
uninterpretable and the fault is in the bench design, not the data.

| arm | objective | raised | preserved | invented | traceability | n |
|---|---|---|---|---|---|---|
| stock (A') | none | 2.33 | 1.77 | **0.00** | **100%** | 30 |
| calibration-trained | production | 2.70 | 1.83 | 0.07 | 96% | 30 |
| provenance-trained | faithfulness | 2.63 | 1.73 | 0.07 | 96% | 30 |

**Stock invention is 0.00 on trigger cases.** There is nothing to correct in
the condition we benched. P18.1 is therefore not merely falsified — it was
UNTESTABLE as run. P18.2 (preservation held, 1.77 -> 1.73) is fine but
vacuous for the same reason.

**Cause.** run_cell18_bench.py was adapted from run_cell11_bench.py, which
uses the seven ORIGINAL cases. Invention lives on THIN-SUPPLY questions —
the on-topic trigger-free cases 8/9/10 built for Cell 14, where invention is
0.53 families and traceability 33%. Those were never benched here. case_7,
the only trigger-free case in the set, is the off-topic one that routes to
zero seats; its 5 runs were correctly quarantined by the analysis, leaving
only the condition where the phenomenon is absent.

This is exactly the failure the harness design (docs/HARNESS_DESIGN.md
section 5) says to guard against: the probe battery specifies that
trigger-free questions must be ON-TOPIC so routing occurs. The bench did not
follow the design written two hours earlier.

**Corrective runs registered (no change to predictions).** Bench BOTH the
provenance-trained Lead and the stock Qwen Lead on cases 8/9/10 (on-topic,
trigger-free, routing verified): 3 cases x 5 seeds x 2 arms = 30 runs. The
stock arm is required because no Qwen baseline exists on these cases —
arch-council's runs there use gpt-oss, a different writer.

P18.1 and P18.2 are re-tested on that data unchanged. The 30 trigger-case
runs above are retained and reported as showing no degradation on the
condition where the writer was already faithful, which is a real if minor
result: the training did not break high-supply behaviour.

## CELL 18 VERDICT (corrected bench) — P18.1 FALSIFIED (2026-08-04, 30 thin-supply runs)

Same writer model in both arms, on-topic trigger-free cases, routing verified
on every run, zero quarantined.

| arm | raised | preserved | invented | traceable | n |
|---|---|---|---|---|---|
| stock Qwen | 1.07 | 0.67 | 0.07 | 91% | 15 |
| provenance-trained | 1.40 | 0.60 | **0.27** | **69%** | 15 |

Supply comparable across arms (1.07 [0.47,1.73] vs 1.40 [0.73,2.00],
overlapping), so the comparison is not confounded by what the seats supplied.

**P18.1 FALSIFIED, and in the WRONG DIRECTION.** Invention did not fall; the
point estimate ROSE 0.07 -> 0.27 and traceability fell 91% -> 69%. Intervals
overlap ([0.00,0.20] vs [0.07,0.53]) so we do not claim the training made
things worse — only that it did not make them better, and there is no hint of
the intended effect.

**P18.2 held** (0.67 -> 0.60): not a volume knob. Vacuous again, since the
effect it discriminates is absent.

**REGISTERED CONSEQUENCE 2 EXECUTED.** Weight-level training at the writer
locus has now failed under THREE DISTINCT OBJECTIVE CLASSES with the same
model, trainer, recipe and near-identical dose:
  - production (density) — Cell 6b, 88 pairs
  - calibration (conditional production) — Cell 11, 49 pairs
  - faithfulness (provenance) — Cell 18, 71 pairs
Plus seat-locus failures across three lineages and two optimizers, and a
dose-invariance null at 3.2x. This is a materially stronger claim than three
failures under one objective and should be stated that way.

**The sharpest detail.** Training-time val loss was 0.069 — the model learned
to RANK provenance pairs well. It still did not BEHAVE more faithfully at the
pipeline mouth. This exactly reproduces Cell 11's pattern, where preference
accuracy rose 0.48 -> 0.94 with no behavioural change. Learning the preference
and acting on it are separable, and this is now observed twice under different
objectives.

**Retained from the first (mis-targeted) bench:** on trigger cases where the
writer was already 100% traceable, training changed nothing (preservation
1.77 -> 1.73). The intervention does not degrade behaviour where behaviour is
already good.

**Honest scope.** 15 runs per arm; intervals are wide. 71 pairs, 81% of Cell
6b's dose. LoRA r8/16 layers. A larger intervention could differ. What we can
say is that the objective class was not the binding constraint, which was the
specific hypothesis this cell registered.

## HARNESS BUILT + VALIDATED (2026-08-04) — and it immediately caught a cohorting defect

`harness/` package implemented per docs/HARNESS_DESIGN.md v0.2: lexicon
(byte-identical regexes to the canonical instrument), provenance audit with
floor guard, path assertion with quarantine, and the runtime gate (reactive,
evidence-specific feedback; annotation on residual; only the writer re-run).

**Validation against known numbers:** thin-supply arch-council runs reproduce
EXACTLY (raised 0.40 / kept 0.27 / invented 0.53 / 33%, n=15), and the path
assertion quarantines exactly the 5 known zero-route case_7 runs.

**Discrepancy found and resolved — the harness was right.** The trigger-case
check gave n=30/87% where the earlier replication table said n=70/81%.
Cause: the mode name `arch-council` was REUSED by three cells (8: original
battery; 14: thin cases; 15: load sweep), and the earlier inline analysis
pooled the 40 load-sweep runs into "trigger-heavy". Strict battery numbers:
raised 3.17, kept 1.60, invented 0.23, 87% traceable (n=30). Conclusions
unaffected (the pooled dose-response conditions on supply, not battery), but
the per-writer table's arch-council row mixed batteries. CORRECTION: 81% ->
87% for the strict battery. Harness lesson folded into design: Trace must
carry the experiment/cell id, because mode names get reused.

## CELL 19 PRE-REGISTRATION — the runtime provenance gate (registered 2026-08-04, before any runs)

**Question.** Invention resists a standing instruction (17) and preference
training under three objective classes (6b/11/18). The gate is the remaining
intervention class: REACTIVE, EVIDENCE-SPECIFIC feedback — audit the draft,
name the exact invented families and phrases, demand removal or grounding,
re-run only the writing call (upstream frozen), max 2 retries, annotate any
residual. Cell 17's clause was prophylactic and generic; the hypothesis is
that specificity and reactivity are the active difference. If the gate also
fails, even targeted runtime feedback cannot stop invention and annotation is
all that remains.

**Design.** Writer gpt-oss-20B in every role (matches the arch-council
baselines). Cases: the three thin-supply cases 8/9/10 (baseline invention
0.53, traceability 33%, n=15) plus trigger cases 1-6 (strict baseline
invented 0.23, kept 1.60, 87%, n=30) for the collateral check. One gated arm:
9 cases x 5 seeds = 45 runs. Path asserted per run. The verdict uses the
gate's POST-audit on the pre-annotation text — the annotation itself names
families ("training-cutoff") and would otherwise contaminate the regex count;
both texts are persisted.

**Predictions.**
- P19.1 (the gate suppresses invention where instruction could not): post-gate
  invented families on thin cases fall vs the 0.53 baseline, CIs disjoint.
  FALSIFIED IF overlap.
- P19.2 (no collateral damage — the standing discriminator): preserved
  families hold on BOTH conditions (thin 0.27 baseline, trigger 1.60).
  FALSIFIED IF preservation falls with disjoint CIs anywhere. Deletion of
  UNGROUNDED content is success, not damage; only loss of GROUNDED content
  falsifies.
- P19.3 (cost, reported not predicted): mean retries per run, fraction of
  runs needing any retry, added wall-clock.
- P19.4 (exploratory): residual-after-2-retries rate — how often annotation
  is the terminal state.

**Registered consequences.** If P19.1 and P19.2 hold: the harness has
demonstrated lift — runtime verification succeeds where prompt and weights
fail, the mechanism note (reactive+specific vs prophylactic+generic) enters
the behavior paper, and the gate becomes the recommended deployment pattern.
If P19.1 fails: invention resists even evidence-specific runtime feedback;
annotation is the only honest treatment, and the two-component description
hardens further. Either way the result completes the intervention picture:
prompt, weights, and now verification, all tested on the same phenomenon.

### CELL 19 AMENDMENT — instrument upgrade, registered before any gate outcomes were examined (2026-08-04)

**User-raised defect in the running design, accepted.** The gate audits with
the regex lexicon, quotes the matched phrases in its feedback, and re-audits
with the SAME regex. A reviser can therefore satisfy the gate by PARAPHRASE —
dropping the quoted phrase while keeping the behavior ("modeled at" -> "we
estimate"). Regex scores that as success; the behavior persists. The
instrument that generates the feedback cannot be the sole judge of
compliance. This is the same paraphrase blind spot already documented for the
lexicon (limitations of every paper), now load-bearing because the gate
CREATES selection pressure toward exactly that blind spot.

**Why NLI is the right second instrument here (and was not for tensions).**
The calibrated DeBERTa-v3-MNLI instrument with frozen per-family Youden
thresholds was validated for precisely this task — detecting FAMILY PRESENCE
in a response (chosen-vs-rejected AUC 0.929). Its documented failure was on
compound contrastive claims (tension grounding), a different task. Family
presence is what the gate needs.

**Amendment (Cell 19 continues; no arm changes):**
1. The running regex-gated arm completes as designed — its baselines are
   regex-scored, so the primary comparison stays internally consistent.
2. NEW P19.5 (the paraphrase-evasion check): all post-gate outputs are
   re-scored with the calibrated NLI instrument. If regex reports invention
   removed but NLI reports the family still present at threshold, the gate
   taught EVASION, not faithfulness. P19.1 is CONFIRMED only if the fall in
   invention holds under BOTH instruments; regex-only improvement with NLI
   disagreement is reported as evasion, a negative result.
3. Harness upgrade: audit becomes instrument-pluggable; the gate's verdict
   path gains a fast-screen (regex) + validated-confirm (NLI) mode. Judges
   remain verdict-level (pairwise, blinded), not per-retry — they are the
   third instrument for the final comparison, not a gate component.

Registered before examining any of the running cell's gate outcomes; the
only Cell 19 output seen at amendment time is the first run-start line.

## CELL 19 VERDICT — the gate taught EVASION. Your amendment caught it. (2026-08-05, 45 runs, 0 failures, 0 quarantines)

| condition | n | supply | regex inv pre->post | kept pre->post | retries | annotated |
|---|---|---|---|---|---|---|
| trigger | 30 | 2.97 | 0.17 -> **0.00** (disjoint) | 1.73 -> 1.73 | 0.20 | 0 |
| thin | 15 | 0.73 | 0.20 -> 0.07 (overlap) | 0.53 -> 0.53 | 0.27 | 1 |

**P19.1 FALSIFIED as registered** (thin-supply CIs overlap). Note the thin
condition did not reproduce its own baseline: seats raised 0.73 here vs 0.40
in the arch-council baseline, and per the compensation dose-response higher
supply means less invention (0.20 pre, vs the 0.53 baseline). So there was
less to remove than the cell was designed around — a sampling outcome, not a
gate property, and it makes P19.1 a weak test at n=15.

**P19.2 CONFIRMED.** Preservation held EXACTLY on both conditions
(1.73->1.73, 0.53->0.53). Not a volume knob.
**P19.3 cheap.** 8/45 runs intervened, mean 0.22 retries, +7% latency
(381s council + 28s gate).
**P19.4** 1/45 runs terminated in annotation.

**P19.5 — THE RESULT. The gate taught paraphrase evasion.**
On the 8 runs it actually intervened on:

| instrument | invented, pre -> post | removed |
|---|---|---|
| regex (the gate's own) | 1.00 -> 0.12 | **0.88** |
| calibrated NLI | 0.00 -> 0.00 | **0.00** |

Regex says the gate removed 88% of invented families. NLI says it removed
NOTHING. The behavior did not go away; the *matchable phrases* did. The
revisions rephrased "modeled at" into forms the lexicon cannot see and the
entailment model still detects.

The trigger-case result — 0.17 -> 0.00 disjoint, which looked like the
cell's clean success — is therefore **not a success**. It is the evasion
effect measured by the instrument that cannot see through it.

**This is precisely the failure mode the amendment was registered to catch,
and it would otherwise have been reported as the harness's headline win.**
The regex-only verdict (invention eliminated on trigger cases, preservation
untouched, +7% cost) is a publishable-looking result that is wrong. Two
instruments, one of them not the one driving the intervention, is what made
the difference.

**Consequence for the harness (design v0.3 required).** The gate as built is
unsafe: quoting matched phrases teaches the model to avoid the matcher.
Options, none yet tested: (a) NLI-in-the-loop despite ~30-60s per audit,
(b) feedback that names the BEHAVIOR without quoting phrases, (c) gate as
detector only — annotate, never request revision. Option (c) is the only one
we currently have evidence for, since annotation makes no demand the model
can game.

**Consequence for the intervention picture.** Prompt (17) failed. Weights
(6b/11/18) failed under three objective classes. Runtime revision (19) does
not fail so much as *appear to succeed while making things worse* — the
output now carries the same behavior in less detectable form. What survives
is detection and disclosure, not correction. That is a narrower and more
honest recommendation than the harness design assumed.

## CELL 20 PRE-REGISTRATION — the decision/attribution instruction (registered 2026-08-05, before any runs)

**Why.** The architecture's stated purpose is CEO-style adjudication: the
Lead weighs specialist input and renders a cited decision. Measured baseline
(60 council runs, first-pass proxies): tensions are enumerated (3.9/response,
89% figure-grounded) and their material is addressed in the body (97%), but an
EXPLICIT recommendation appears in only 13% of answers and a specialist is
cited by name in the body in 23% (0.3 citations/answer). The deliberation
happens; the verdict does not. The synthesis prompt asks the Lead to
acknowledge and preserve — NOTHING in it asks it to decide or cite. This is
the one rendering-side lever the programme never pulled, and instructions
demonstrably move rendering (gradedly, per-behavior, across writers).

**Reframe this cell operationalises.** Under the CEO frame, writer-added
judgment is legitimate WHEN ATTRIBUTED AS SUCH; the systemic defect is
unattributed judgment. A dropped caveat that is explicitly overruled ("legal
flagged X; I discount it because Y") is a NEW provenance category —
overruled-with-acknowledgment — distinct from silently dropped.

**Treatment.** Production synthesis prompt plus a DECIDE clause appended to
STEP 2:

  7. RENDER A DECISION. End with an explicit recommendation. Attribute the
     key supporting and opposing considerations to the specialists who raised
     them, by name ("the finance contribution models...", "legal flags...").
     Where you discount or overrule a specialist's caveat, say so explicitly
     and give your reason. Do not present your own judgment as a
     specialist's.

Writer gpt-oss-20B in every role. Cases: trigger 1-6 + thin 8/9/10 (same as
Cell 19), 9 x 5 = 45 runs, path asserted per run. Baselines: the existing
arch-council/c13-all corpus (decision 13%, citations 0.3/answer, citation
figure-accuracy 39/68 verified).

**Outcomes and instruments.**
- Decision presence (regex battery, plus blinded-judge validation on a
  20-answer subsample since the regex is a first-pass proxy).
- Attribution rate (citation sentences per answer).
- Attribution ACCURACY, tiered: figure-bearing citations verified exactly
  against the NAMED seat's text; qualitative citations scored by the judge
  tier; the exact-match checker itself validated on a judged subsample
  (normalization misses like "£5 million" vs "£5m" must not count as
  confabulation).
- Overrule-acknowledgment: of caveats absent from the answer, what fraction
  are explicitly acknowledged-and-overruled vs silently dropped.
- Disposition metrics reported alongside — a decisive answer may LOWER
  density, and that is not a regression under this frame; recorded so the
  two value systems are visible side by side.

**REGISTERED GUARDS.**
1. JOINT SCORING: attribution rate and accuracy are never reported
   separately in the verdict. The degenerate optimum of citation-checking is
   citing less; a rate collapse with an accuracy rise is a FAILURE.
2. NO RUNTIME FEEDBACK: verification is verdict-time only. Cell 19
   established that detector-visible revision requests teach evasion; here
   the evasion channel (stop citing) is cheaper still.
3. The citation-presence regex does not judge citation accuracy (different
   instruments, per the Cell 19 amendment rule).

**Predictions.**
- P20.1: decision presence rises from 13% to a majority of answers (>50%),
  judge-validated. FALSIFIED IF it stays a minority — deciding would then be
  the FIRST rendering behavior an instruction fails to elicit, which would
  itself be a major finding against the rendering/filling account.
- P20.2: attribution rate rises materially (>=1.5 citations/answer) AND
  figure-citation accuracy does not fall below the 57% baseline (39/68).
  FALSIFIED IF rate rises but accuracy collapses (instruction elicits
  confabulated citations) OR rate fails to rise.
- P20.3 (exploratory): overrule-acknowledgment rate on absent caveats; any
  drop in silent-dropping is the CEO-frame improvement.
- P20.4 (exploratory): effect on invention — attributed judgment may absorb
  what was previously unattributed invention ("I judge X" replacing bare X).

**Consequences.** If P20.1 and P20.2 hold: the architecture's stated purpose
is achievable by instruction, the CEO reframe enters the behavior paper with
measured support, and Cell 21 validates the manifest against the decision-
memo format including citation verification marks. If P20.1 falls: rendering
has a boundary instructions cannot cross, which revises the paper's central
dissociation. If P20.2 falls by accuracy collapse: the caution was right —
the instruction manufactures citations — and the manifest's verification
tier becomes the headline safeguard rather than an accessory.

## CELL 21 PRE-REGISTRATION — manifest accuracy (registered 2026-08-05; design finalised after Cell 20 reports)

**Question.** The epistemic manifest (harness v0.3) is deterministic,
quotation-only: it restores dropped qualifications with attribution, flags
writer-supplied ones, and marks citations verified/unverified. Is it
ACCURATE enough to attach to answers?

**Design (format-dependent parts finalised post-Cell-20, before any Cell 21
runs; this registration fixes the evaluation protocol).** Manifests are
generated for a stratified sample of existing runs (thin + trigger, gated
and ungated, plus Cell 20's arm in whichever format wins). Blinded judges
(both local judges, order-swapped, evidence-quoting, per the established
protocol) score each manifest item:
- restored item: is the quoted specialist text genuinely a qualification the
  answer omitted? (precision) — and on a per-run basis, did the manifest
  miss omitted qualifications? (recall, judged against the seat texts)
- flagged item: is the flagged passage genuinely unsupported by any
  specialist? (precision on invention flags)
- citation marks: agreement between the manifest's verified/unverified marks
  and judge assessment of the same citations.

**Predictions.**
- P21.1: restored-item precision >= 80% (judged).
- P21.2: invention-flag precision >= 80% (judged).
- P21.3 (exploratory): recall of omissions; citation-mark agreement.

**Consequence.** If P21.1/P21.2 hold, the manifest ships as the harness's
deliverable and the papers' recommendation ("detection and disclosure, not
correction") has a validated artifact behind it. If either falls below 80%,
the manifest is not attachable as-is and the failing tier is reported with
its error taxonomy.

## CELL 22 PRE-REGISTRATION — retrospective paired replay of the DECIDE clause (registered 2026-08-05, before Cell 20 has reported; execution contingent on Cell 20's outcome)

**What it is.** 1,130 archived runs carry the exact synthesis input_messages
plus the seat turns. The writing step can therefore be REPLAYED under the
DECIDE prompt with everything upstream frozen: swap the system message in the
stored synthesis input for the Cell-20 variant, re-call the SAME writer, one
model call per run. No planners, no specialists.

**Why paired replay beats new runs.** Seat-sampling variance has been this
programme's dominant noise source (Cell 15's within-load spread 0.42 vs 1.57;
Cell 18's cross-arm supply mismatch 0.73 vs 0.40). Replaying the same frozen
seat text under both prompts yields PAIRED comparisons in which nothing but
the prompt differs. Paired deltas with sign tests / bootstrap on differences,
not unpaired CIs. Pairing removes seat variance, not decode variance (replay
at the original temperature 0.2; generation noise remains within pairs).

**Writer identity caveat, found while designing this cell.** Every stored
synthesis turn records ollama_tag phi4:14b because the orchestrator hardcodes
the LEAD member on that turn regardless of which backend served it — the
THIRD instance of the model-identity incident class. The true writer is
recovered from deliberation.cabinet_backends["synthesis"]; replays MUST match
it, and any run whose backend tag is missing or ambiguous is excluded, with
the exclusion count reported.

**Execution gate.** Runs only if Cell 20's P20.1 holds (the DECIDE clause
elicits decisions on fresh runs). If P20.1 falls, this cell is void — there
is nothing to generalise — and this registration stands as the record of what
would have been run.

**Selection rule, fixed now (no post-hoc corpus shopping).** In priority
order, original-writer-matched:
1. TUNED-SEAT ARMS: local-council-spec, local-council-sft (35 each, Phi-4
   writer) — the seat-tuning backfire under the CEO lens.
2. LOAD SWEEP: the 40 arch-council case_l* runs (gpt-oss) — does decisiveness
   survive simultaneous demand?
3. THIN + BASELINE across writers: cell18-stock-thin (15, Qwen),
   local-council-repro (35, Phi-4), c13-all (35, gpt-oss).
Total 195 replays. Nothing else is replayed in this cell; extensions require
a new registration.

**Predictions.**
- P22.1 (the effect generalises): decision presence rises in the replayed
  arm vs its stored original for EACH of the three writers (paired, per-run
  judged/regex as in Cell 20). FALSIFIED IF any writer fails to move — the
  DECIDE effect would then be writer-specific.
- P22.2 (the backfire reinterpretation, the cell's sharpest question): on
  spec/sft pairs, dropped seat caveats convert from silently-dropped to
  ACKNOWLEDGED-OVERRULED at a materially higher rate than in the stored
  originals. FALSIFIED IF the writer still trims silently under DECIDE —
  the backfire would then stand as originally interpreted.
- P22.3 (load robustness, exploratory): decision presence by load level
  L1-L4; report whether the verdict dissolves under simultaneous demand.
- P22.4 (joint guard, carried from Cell 20): attribution rate AND accuracy
  reported jointly per writer; a rate rise with an accuracy collapse in any
  writer is that writer's FAILURE regardless of P22.1.

**Consequences.** If P22.1 and P22.2 hold: the DECIDE result is
writer-general, and the seat-tuning backfire is REINTERPRETED — the trimming
was a prompt defect (no sanctioned way to disagree), not a writer property;
the behaviour papers' invariance section gains that qualification. If P22.2
falls with P22.1 holding: deciding generalises but open disagreement does
not, and the backfire stands. Mixed writer results scope the claim to where
it held.

## CELL 20 VERDICT — the Lead renders the FORM of a decision but will not COMMIT (2026-08-05, 45 runs, 0 failures, 0 quarantines)

| outcome | baseline | DECIDE arm |
|---|---|---|
| decision presence (regex tier) | 16% [10,22] | 47% [33,60] |
| decision presence (gpt-oss judge, unanimous protocol) | 0/10 | **0/10** |
| decision presence (qwen judge) | 0/10 | 3/10 |
| citations/answer (same instrument both arms) | 1.1 | 2.3 |
| figure-citation accuracy | 57% [46,69] | 47% [33,61] |
| overrule language | 0/125 | **0/45** |
| provenance, trigger (kept / invented) | 1.83 / 0.10 | 2.07 / 0.07 |
| provenance, thin (kept / invented) | — | 0.27 / 0.53 |

**P20.1 FALSIFIED — decisively at the registered judge tier.** The regex rise
(16% -> 47%, disjoint CIs) is real but measures recommendation-SHAPED text.
The registered judge validation says commitment did not appear: the stricter
judge scored 0/10 DECIDE answers as containing a committed verdict; the more
lenient judge 3/10. Reading the endings confirms it: answers now carry
"Adopt X with cap Y" fragments embedded in conditional plan language ("by
embedding these safeguards ... can launch ... while remaining agile"), and
close on synthesis-speak, not a verdict.

**Fourth instrument-disagreement finding of the programme, and reported as
such:** regex 47%, qwen 30%, gpt-oss 0%. "Decision presence" is not a
well-defined binary — the construct has degrees (recommendation-shaped
content vs committed verdict), and the registered threshold sat on the
construct's fault line. Judge-instrument caveats: the strict judge is
gpt-oss judging gpt-oss output (self-judging), and unanimity was reached on
only 17/20 items.

**P20.2 FALSIFIED on the strict registered wording** (accuracy "does not
fall below the 57% baseline": point estimate 47%), with the honest
qualification that the CIs overlap heavily — a 10pp dip at n≈50-70 is not a
measured collapse, and the joint guard's catastrophic branch (rate up,
accuracy collapsed) did NOT occur. Rate doubled under the same instrument.

**P20.3: 0/45 answers contain overrule language** (first-pass regex, patterns
untuned — but zero, coherent with the judges' zero-commitment reading).
**P20.4: no invention interaction.** Trigger invention 0.10 -> 0.07,
preservation 1.83 -> 2.07 (mild rise, CIs surely overlap); thin invention
0.53 — identical to the ungated baseline. Attribution did not absorb
invention.

**REGISTERED CONSEQUENCES EXECUTED.**
1. Per the Cell 20 registration: "If P20.1 falls: rendering has a boundary
   instructions cannot cross, which revises the paper's central
   dissociation." That is now the finding. The instruction moved every
   SURFACE it touched — structure, citations doubled, recommendation-shaped
   sections tripled — and did not move the epistemic act underneath: the
   model neither commits to a verdict nor overrules a specialist. Combined
   with invention (Cell 17) this gives TWO instruction-resistant behaviors,
   and they rhyme: both are matters of epistemic POSTURE (what the model is
   willing to assert or forgo asserting) rather than text surface.
   Refined dissociation: instructions control what text appears; they do not
   control what the model commits to.
2. Per the Cell 22 registration: P20.1 fell, therefore CELL 22 IS VOID. No
   replays run. The registration stands as the record of what would have
   been tested.
3. Cell 21 (manifest accuracy) proceeds against the EXISTING output format,
   as its registration provided.

### CELL 21 — FIRST JUDGING PASS VOID: instrument implementation deviated from registration (2026-08-05)

92 items judged; results unusable. Judge polarization: on 55 restored items
gpt-oss answered NO to ALL and qwen YES to ALL (0 unanimous); citation marks
3/32 agreement. P21.2's nominal 3/3 CONFIRMED rides on 3 unanimous of 5 items.

**Cause is ours.** The registration specified judges "per the established
protocol" — PAIRWISE comparison, which produced 14/14 unanimity in the Cell
7b arbitration. The implementation used ABSOLUTE yes/no labels with a
compound criterion ((a) is it a qualification AND (b) is it absent), a
different and weaker instrument. Absolute labeling with ambiguous criteria is
exactly where acquiescence bias (qwen ~97% YES) and strictness bias (gpt-oss
~0% YES) run free. Fifth instrument-validity finding of the programme;
second where the defect was in OUR deployment of the instrument rather than
the instrument itself.

**Corrected instrument (registered before re-judging).** Forced-choice
pairwise, per the established protocol:
- RESTORED: judge sees two specialist sentences — the manifest's restored
  quote and a DISTRACTOR from the same run whose family IS present in the
  answer — plus the answer; picks which sentence's qualification is missing.
  Manifest correct when judges pick the restored quote. Items with no
  eligible distractor are skipped and counted.
- CITATION MARKS: judge sees two cited claims from the same seat — one
  manifest-verified, one manifest-unsupported — plus the seat's text; picks
  which is supported. Agreement = the verified one. Pairs formed within-run
  where possible, else within-seat across the sample; pairing basis reported.
- FLAGGED (n=5): retained absolute (no natural pair exists for "no
  specialist raised this"), reported descriptively, NOT as a P21.2 verdict —
  the item count is too thin regardless of protocol.
Order randomized per item; unanimity protocol; evidence clause required.
P21.1 threshold unchanged (>=80% of unanimous pairs pick the restored item).

### SIXTH INSTRUMENT FINDING — empty judge replies scored as NO; Cell 20's judge tier suspect (2026-08-05)

Probing the pairwise failure: gpt-oss (a reasoning model) returns an EMPTY
final at max_tokens=100-120 — the budget is consumed by its analysis channel.
Both judge scripts treated empty as NO (yes()/pick() defaulted on empty).
Consequences:
1. Cell 21 pass 1 "gpt-oss NO on all 55" was largely SILENCE, not
   strictness. The polarization diagnosis is amended: qwen acquiescence may
   be real; gpt-oss's contribution was empty.
2. **Cell 20's judge tier (0/10 decisions, called decisive) is SUSPECT** for
   the same reason and must be re-run with adequate token budget before the
   P20.1 verdict stands. Flagged immediately; verdict marked provisional in
   this note until re-judged.
3. Harness rule added to the incident ledger: NEVER default an empty
   instrument reply to a substantive label; empty = unparseable = excluded
   and counted.
Corrected judge protocol: max_tokens 2048, digit/label parsed from the full
reply, empty counted as unparseable. Cell 20 subsample re-judged FIRST (its
verdict is upstream of Cell 22's void), then Cell 21 pairwise.

### CELL 20 — JUDGE TIER RE-RUN with the corrected instrument (2026-08-05)

With adequate token budget (2048) gpt-oss now actually judges (0 unparseable,
previously silent). Corrected subsample results:
- unanimous labels 13/20 (was 17/20 with silence-as-NO)
- judge-unanimous DECISION rate: DECIDE 3/10, baseline 0/10
- regex agreement with unanimous judges 9/13

**P20.1 verdict REVISED in degree, not direction.** The corrected judge tier
shows the DECIDE clause DOES produce some judge-recognised committed
decisions (3/10 vs 0/10 baseline) — the earlier "zero commitment" reading
was an artifact of empty replies. But 3/10 remains far below the registered
>50% majority threshold: P20.1 stays FALSIFIED. The refined statement:
the clause elicits commitment OCCASIONALLY (~30% by either lenient judge or
corrected strict judge), reliably changes FORM (regex 47%), and never
produces overrule language (0/45). "Form moves, commitment lags" replaces
"form moves, commitment does not move at all". Cell 22 remains VOID (the
gate required P20.1 to HOLD; it did not).

## CELL 21 VERDICT — P21.1 FALSIFIED; the manifest does not ship as-is (2026-08-05)

Corrected pairwise protocol, 49 restored pairs + 10 citation pairs, both
judges at adequate token budget (0 unparseable).

**P21.1 restored-item precision: 18/27 unanimous-correct = 67% [48%,85%] —
below the registered 80%. FALSIFIED as registered.** Two instrument
limitations documented alongside, because they bound what this number means:
1. Split rate remained high (22/49 = 45%): judge unreliability on this task
   persists even in forced-choice form.
2. The forced-choice premise ("exactly ONE sentence is missing") is not
   guaranteed by construction. Distractors were selected as sentences whose
   FAMILY is present in the answer, but family-presence does not ensure the
   sentence's specific SUBSTANCE was conveyed. Pairs where both sentences
   were effectively missing force arbitrary answers. 67% is therefore a
   LOWER BOUND confounded with distractor construction — but a lower bound
   below threshold still fails the registration.
**P21.3 citation-mark agreement: 1/3 with 7 splits — uninformative.**
**P21.2 remains descriptive only** (3/5 items from the void first pass;
never a verdict).

**REGISTERED CONSEQUENCE EXECUTED: the manifest is NOT attachable as-is.**
The failing tier is family-granularity restoration: at family level,
restored-item correctness cannot be established at >=80% with the
instruments available. What remains validated in the harness: execution-path
assertion (exact quarantine of known-bad runs), corpus-level provenance
statistics (reproduced exact known values), and exact-match figure checking.
What is NOT validated: per-item family-level restoration and qualitative
citation marks. The honest deliverable is the harness as a MEASUREMENT and
AUDIT layer; the reader-facing manifest needs claim-level (not
family-level) extraction before it can clear its own bar. Recorded as the
open engineering item.

---

## CELL 23 PRE-REGISTRATION — NLI recalibration on FAMILY PRESENCE
Registered 2026-08-05, before any labelling or scoring. Frozen at commit time.

### Motivation
Sweep finding #7 (docs/ARCH_SWEEP_2026-08-05.md): across 225 runs the regex
and NLI instruments agree on which family was invented ZERO times, and
disagree on whether invention occurred at all in 26.2% of runs. The NLI
thresholds in `train/data/nli_thresholds.json` were calibrated for
chosen-vs-rejected DISCRIMINATION (Cell 7a, AUC 0.929 on that task) and have
been used off-label for family PRESENCE ever since. This cell calibrates
them for the task they are actually used on.

### Ground truth — the binding constraint
Labels MUST NOT be derived from the regex lexicon. Regex-derived labels would
train NLI to be a lexicon approximator, destroying the instrument independence
that is the entire reason for having a second instrument, and would guarantee
a spurious agreement improvement in P23.2. Labels come from two blinded LLM
judges scoring individual SENTENCES against the frozen family definitions
(the Cell 7a HYPOTHESES strings, unchanged).

Cell 21's first judging pass failed at absolute labelling of whole responses
for a holistic property. This task is different in kind — one sentence, one
crisp definition — but reliability is CHECKED (P23.3, anchors), not assumed.

### Sampling — 200 sentences, documented strata
Drawn from the 225-run adjudication set (writer outputs and upstream text):
- S1 (50) regex fires on the sentence
- S2 (50) some family scores NLI >= 0.5, regex silent
- S3 (50) regex fires, all families score NLI < 0.5
- S4 (50) uniform random from the pool

Strata are selected on instrument OUTPUT, which shifts prevalence but not
label validity. Thresholds are additionally reported on S4 alone as a
natural-prevalence robustness arm.

### Anchors
20 hand-written items (5 per family: 3 positives including at least one
paraphrase that deliberately avoids lexicon wording, 2 hard negatives).
Anchors are judged blind alongside the sample.

### Judging protocol
- Judges: gpt-oss:20b and qwen2.5:7b-instruct, temperature 0
- max_tokens 2048. Empty or unparseable replies are recorded as None and
  EXCLUDED — never scored as a substantive label (recorded defect: gpt-oss
  returns "" at low token budgets)
- one call per sentence, returning which of the four families apply
- judges see the definitions only: never the regex match, never the NLI score
- family order randomised per call to limit position bias
- a label is set only where both judges agree; disagreements are excluded and
  counted

### Threshold rule — FROZEN NOW
Per family, Youden's J: maximise (sensitivity + specificity - 1) over the NLI
entailment score. Ties resolve to the LOWER threshold. Report AUC,
sensitivity, specificity, n_pos and n_neg per family.

### Predictions
- **P23.1** Presence-calibrated thresholds differ materially from the Cell 7a
  values: >= 0.10 absolute change on >= 2 of 4 families.
  *Falsified if* all four move < 0.10 — the off-label use was harmless and
  the disagreement has another cause.
- **P23.2** Family-level regex/NLI agreement on invention over the 225-run
  adjudication set rises above zero.
  *Falsified if* it remains zero — the disagreement is not a threshold
  artefact and the two instruments measure genuinely different constructs.
- **P23.3** Judge-judge agreement on family presence >= 0.70, and both judges
  score >= 80% on the anchors.
  *Falsified if* below either bar.

### Consequences, fixed in advance
- If **P23.3 fails**: NO thresholds are shipped. The cell reports a null and
  recalibration requires human labels.
- If **P23.2 fails**: the phrase "confirmed by two instruments" must be
  weakened to "two independent measurements" everywhere in the paper and
  site, and the C3 ensemble arithmetic stays unusable for this pair.
- `train/data/nli_thresholds.json` is NOT overwritten — published Cell 7a
  results depend on it. New file: `train/data/nli_thresholds_presence.json`.

---

### CELL 19 AMENDMENT #2 — the "taught evasion" mechanism claim is corrected (2026-08-05, program audit)

The P19.5 verdict recorded: "the revisions rephrased 'modeled at' into forms
the lexicon cannot see and the entailment model still detects." The program
audit re-scored the 8 intervened runs and that sentence is WRONG on its
second half:

- NLI presence of the flagged families (frozen 7a thresholds): **0/8 pre-gate
  and 0/8 post-gate.** The entailment model detected NOTHING at either time.
  Its per-family max scores are unchanged pre→post on 7/8 rows (identical to
  3 dp) — the rewrites did not touch its top-scoring sentences. An instrument
  that never saw the behavior corroborates neither persistence nor removal;
  the "0.00 removed" row was insensitivity, not confirmation.
- What DOES establish phrase-level removal is manual inspection, now on
  record: case_3 "a *modeled assumption*" → "*assumed by the Finance
  contribution*", "(modeled assumption)" → "*as assumed by Finance*" —
  content intact, re-attributed, outside the lexicon's frames. case_4's
  sensitivity block survives renamed ("Finance also considered alternative
  scenarios").
- One flagged invention was a REGEX FALSE POSITIVE: case_5's "cutoff" was
  the action item "Verify current uncompensated care %" — an instruction to
  staff, not an epistemic disclosure. The gate spent a revision cycle
  rewording it.

**Amended P19.5:** the gate's removal is instrument-relative. Manual reading
shows a mixture of genuine phrase-evasion (content surviving in rewording)
and the instrument correcting its own overcounts. The design rule — the
feedback-generating instrument never grades compliance — STANDS, on
inspection evidence plus the structural argument. The two-instrument
corroboration story is WITHDRAWN, and this is retrospectively the first
observation of sweep finding #7 (the instrument pair does not share a
construct). Re-score under presence-calibrated thresholds when Cell 23
ships: two of the eight pre-gate scores (0.636, 0.903) sit near plausible
presence boundaries and may flip the picture for those runs.

**Also corrected in the same audit:** paper_behavior.tex's gate section
contained an ILLUSTRATIVE quote presented as observed — "'Modeled at' became
'we estimate'" appears in no intervened run. Replaced with the actual quotes
above. Fabricating an example, even a directionally-faithful one, is a
defect class of its own and is now in the audit checklist.

### PROGRAM AUDIT — all cells, against the full defect catalogue (2026-08-05)

Trigger: user-directed audit after repeated introduced errors. Full table in
docs/CELL_AUDIT_2026-08-05.md. Summary of standing verdicts: Cells 1-6c, 8
(as amended), 11, 13-15, 17-18, 20-22 SOUND; Cell 19 amended above; Cell 7a
sound on-label with presence use now formally off-label pending Cell 23;
Cell 7b low-risk open item (empty-reply handling unaudited, num_predict 8192
makes it unlikely). Ledger hygiene: 39 zero-route runs remain unmarked in
their files; the GST adapter now excludes them explicitly (previously only
as a require_upstream side effect). Corrections gated on Cell 23's verdict:
global "two-instrument" phrasing (registered consequence of P23.2), site
line ~1204 ("confirmed no behaviors are hiding behind paraphrase"), and the
P19.5 presence re-score.

---

## CELL 23 VERDICT — presence calibration FAILS; the judges are the instrument now (2026-08-05, 220 items x 2 judges, 0 unusable replies)

**P23.3 PASS, decisively.** Judge-judge agreement 0.86 (688/800 family
decisions); anchors gpt-oss 0.90 (72/80), qwen2.5 0.925 (74/80) — including
the paraphrase positives and the hard negatives. Zero empty/unparseable
replies at max_tokens 2048. 200/200 sampled sentences usable. The blinded
dual-judge protocol is a VALIDATED family-presence instrument.

**P23.1 technically SUPPORTED (3/4 families move >= 0.10) — but the
substantive result is stronger and worse: presence calibration FAILS.**
Against the validated labels, the entailment scores carry no presence
signal: AUC modeled 0.116 (INVERSE), hedging 0.236 (INVERSE), jurisd 0.552
(chance), cutoff unmeasurable (3 positives in sample). Youden thresholds
are degenerate (sens 1.00/spec 0.00 and sens 0.02/spec 0.99). No threshold
at any value makes this model + hypothesis set detect family presence.
`train/data/nli_thresholds_presence.json` is shipped as the registered
record with a DO-NOT-USE warning and per-family usable:false flags.

**P23.2 FALSIFIED, by the stronger route.** Agreement cannot rise via
recalibration because no presence-valid threshold exists. Per the
registration's own falsification interpretation: the regex/NLI disagreement
is NOT a threshold artifact; the two instruments never measured the same
construct. Sweep finding #7 is hereby explained, not repaired.

**REGISTERED CONSEQUENCE EXECUTED.** "Confirmed by two instruments" is
weakened to "two independent measurements": paper_behavior.tex Instruments
paragraph rewritten; site (index+results) edited at the two affected spots
(committed, NOT deployed — Netlify remains paused); C3 ensemble arithmetic
permanently unusable for this pair (INTERVENTION_DESIGN, HARNESS_DESIGN
updated; NLI retired from the gate for presence claims). P19.5's planned
NLI re-score is CLOSED as moot: NLI cannot adjudicate that construct at any
threshold; manual inspection remains the evidence.

**Unregistered but decisive by-product, reported as such: the regex report
card.** Grading the primary lexicon against the validated judge labels
(agreement-filtered, stratified sample; S4 = natural prevalence):

| family | n+ | n- | sens | spec | prec |
|---|---|---|---|---|---|
| modeled | 47 | 119 | 0.915 | 0.966 | 0.915 |
| jurisd | 30 | 148 | 0.300 | 1.000 | 1.000 |
| hedging | 44 | 111 | 0.250 | 0.946 | 0.647 |
| cutoff | 3 | 186 | 0/3 | 0.995 | — |

The lexicon is a HIGH-PRECISION, LOW-RECALL counter outside the modeled
family. Consequences, stated honestly: (a) modeled — the family carrying
the C2 clause result and most invention examples — is well-measured;
(b) rates for jurisd/hedging/cutoff are conservative undercounts, and all
published rates are lexicon-relative (already the paper's framing, now with
numbers); (c) the shrinkage regression's supply variable is undercounted,
and measurement error in the regressor attenuates slopes — the published
w = 0.35 is plausibly an UNDERESTIMATE of the true evidence weight. Recorded
as a limitation on the framework's parameter estimates, not a correction.

**Path forward for a true second instrument:** the dual-judge protocol
(validated, ~20s/sentence), or a lightweight classifier trained on the 200
labelled sentences this cell produced. Registered before use, either way.

---

## CELL 24 PRE-REGISTRATION — per-family robustness re-analysis of standing verdicts (registered 2026-08-05, before any numbers are computed)

### Motivation
Cell 23 graded the primary lexicon against validated judge labels: modeled
sens 0.915 / spec 0.966 / prec 0.915; jurisd sens 0.30; hedging sens 0.25 /
prec 0.65; cutoff 0/3. Every composite result in the program therefore sums
one well-measured channel with three lossy ones (and hedging contributes
~1/3 false positives among its hits). This cell re-analyzes the standing
verdicts on the modeled family alone — the validated channel — as a
robustness check. Zero new model calls; pure ledger recomputation.

### Frozen analysis rules
- **Modeled is primary.** Other families reported as secondary, always with
  their Cell 23 sens/prec attached, never as evidence on their own.
- **Estimator for the per-family analog of shrinkage:** family presence is
  binary per run, so the OLS refit is unidentifiable per family (2 supply
  levels). The registered per-family quantities are:
  T_f = P(f in output | f raised upstream), I_f = P(f in output | f not
  raised), discrimination D_f = T_f − I_f. Wilson 95% CIs on T and I;
  bootstrap (5,000 draws, seed 0) for the D_f CI and all arm differences.
- Populations identical to the original analyses: shrinkage 2×2 on the full
  1,260-run usable population; arm comparisons on the sweep's 9 shared
  cases, n=45/arm; Cell 14 decomposition on cases 8/9/10, n=15/arm, raw
  regex counts (single arms have no upstream, so no provenance decomposition
  there — presence rates only, as in the original).
- Floor guard unchanged (500 chars). No threshold, lexicon, or population
  choices may change after numbers are seen.

### Predictions
- **P24.1 (attenuation).** On the validated channel the writer's
  discrimination D_modeled will exceed the composite w: registered bar
  D_modeled ≥ 0.50 with its CI excluding 0.352. *Falsified if* the CI
  includes or sits below 0.352 — attenuation was not the explanation and
  the composite w = 0.35 stands as the honest system parameter without the
  underestimate caveat.
- **P24.2 (sweep robustness).** Modeled-only invention: no arm separates
  from arch-council (all bootstrap diff CIs include 0). *Falsified if* any
  arm separates — the composite null masked a family-specific effect and
  the sweep document must be amended.
- **P24.3 (Cell 17 robustness).** On the zero-modeled-supply stratum,
  c17-suppress does not separate from arch-council on modeled invention.
  *Falsified if* it does — P17.1's null was dilution and Cell 17 needs an
  amendment.
- **P24.4 (Cell 14 robustness).** Modeled presence on trigger-free cases:
  council does not separate BELOW single+spec (i.e., "the council is not
  better calibrated" holds on the clean family). *Falsified if* the council
  separates lower — P14.2 gains a family-scoped caveat.

### Consequences, fixed in advance
- P24.1 holds → framework docs amended: for narrow-lexicon instantiations,
  per-family D on a validated channel is the primary parameter; composite w
  reported beside it as a lower-bound-flavored summary. P24.1 falsified →
  the attenuation caveat added in the Cell 23 verdict is WITHDRAWN as
  overcautious.
- P24.2–P24.4 hold → standing verdicts annotated "modeled-robust," no text
  changes beyond the annotation. Any falsified → the named document is
  amended within the same working session, before any new work.
- **Scoping amendment, executed regardless of outcomes:** Cell 15's
  absolute breadth claim ("engages only 1.2–1.7 of four families") is
  scoped as instrument-limited — three of four families are detected at
  25–30% recall, so true breadth is understated by an unknown amount and
  the claim requires judge-based re-measurement before further use. The
  comparative claims of Cell 15 are unaffected.

---

## CELL 24 VERDICT — the validated channel shows MORE prior-dominance, not less; the attenuation caveat is withdrawn and reversed (2026-08-05, pure ledger recomputation, registered estimator)

Full report: bench/analysis/cell24_report.txt. Population 1,260; per-family
2x2 with Wilson CIs and seeded bootstrap, exactly as frozen.

| family | T_f (preserve) | I_f (invent) | D_f [95% CI] | instrument validity |
|---|---|---|---|---|
| **modeled** | 0.527 | 0.314 | **0.213 [0.155,0.271]** | validated (.92/.92) |
| cutoff | 0.451 | 0.043 | 0.408 [0.367,0.448] | undercount (0/3) |
| jurisd | 0.397 | 0.020 | 0.377 [0.326,0.428] | undercount (.30) |
| hedging | 0.599 | 0.071 | 0.527 [0.483,0.571] | undercount + FP (.25/.65) |

**P24.1 FALSIFIED — in the opposite direction.** Registered bar: D_modeled
>= 0.50 with CI excluding 0.352 from above. Observed: D_modeled = 0.213
[0.155,0.271] — the CI excludes 0.352 from BELOW. On the one channel whose
measurement is validated, the writer preserves a raised modeled
qualification only 53% of the time and invents one 31% of the time when no
seat raised it. **Registered consequence executed:** the Cell 23 attenuation
caveat ("published w=0.35 is plausibly an underestimate") is WITHDRAWN as
not merely overcautious but backwards — the clean channel shows LOWER
discrimination than the composite, so if anything the lossy families
flattered w. The shrinkage thesis (prior-heavy writer) is STRENGTHENED on
the best-measured family. Caveat kept honest: D_f and the composite w are
different estimands; the registered comparison bar was 0.352 and the result
is unambiguous against it.

**P24.2 FALSIFIED — by arch-flat, as the composite regex said and the (now
void) NLI adjudication denied.** Modeled-only invention on eligible runs
(modeled not raised upstream; n=9-18 per arm, small, stated): council 0.722,
flat 0.167, diff CI [-0.833,-0.250] disjoint. c17/c19/c20 all remain nulls.
**Registered consequence executed:** ARCH_SWEEP amended. Two things change
there: (a) flat's lower invention is REAL on the validated channel — but the
mechanism finding stands unchanged (feature-span 0.000: flat says nothing,
and silence cannot invent), so it remains a degenerate corner, not an
improvement; (b) independently, the sweep's NLI adjudication section is
VOID per Cell 23 — its "nothing survives an independent instrument"
conclusion rested on an instrument that measures no construct. The sweep's
surviving comparisons are regex-composite and modeled-only.

**P24.3 SUPPORTED.** c17-suppress vs council on the eligible stratum: diff
CI [-0.556,+0.222], no separation. Cell 17's null is modeled-robust.

**P24.4 SUPPORTED, with a strengthening reported as exploratory.** Council
does not separate below single+spec — and in fact separates ABOVE: modeled
presence on trigger-free cases 0.733 [0.48,0.89] vs 0.200 [0.07,0.45], diff
CI [+0.200,+0.800] disjoint. Cell 14's hedged "if anything worse" is now,
on the validated family and post-hoc (n=15/15), a disjoint interval: the
council IS worse at unwarranted modeled qualification than a lone prompted
model. Recorded as exploratory strengthening, not a new verdict.

**Scoping amendment executed regardless of outcomes (per registration):**
Cell 15's absolute breadth claim ("engages only 1.2-1.7 of four families")
is scoped as instrument-limited; comparative claims unaffected.

---

## CELL 25 PRE-REGISTRATION — the shrinkage law on a second architecture (Mixture-of-Agents), registered 2026-08-05 before any runs

### Purpose
The framework paper's central claim (the shrinkage law y = w·s + c at the
writing step) currently rests on one architecture. This cell measures the
law on a Mixture-of-Agents configuration. HONEST FRAMING, fixed now: same
lab, same case battery, same writer model — this is CORROBORATION on a
different architecture, not independent replication. It moves the evidence
from one parameter card to two; it does not substitute for external
validation (framework Part D).

### Architecture (frozen)
- **Proposers (layer 1):** phi4:14b, qwen2.5:7b-instruct,
  mistral:7b-instruct-v0.3-q4_K_M — three GENERAL instruct models, none of
  the council's domain specialists, no routing, no specialist system
  prompts. Temperature 0.7, max_tokens 4096, one pass per case.
- **Aggregator:** gpt-oss:20b with the canonical MoA aggregation prompt
  (Wang et al. 2024, verbatim in the harness) — no PRESERVE clause, no
  conditional instruction. Temperature 0.6, max_tokens 8192.
- Writer model matches the council arms BY DESIGN: holding the writer fixed
  isolates architecture; a different writer would confound both.
- MoA is route-free: path assertion is N/A and recorded as such (this is
  the "route-free by design" category from the audit, not a missing record).

### Supply variation (frozen — the design our own guards require)
Natural MoA runs do not span supply and would fail the identifiability
guard. Supply is manipulated by PROGRAMMATIC ABLATION of the proposer
texts (gst.corpus.supply_variants: sentence-level removal, deterministic
order), from full supply down to zero, per case. The aggregator runs on
each variant. Zero-supply coverage is therefore guaranteed by construction
(min_zero_supply >= 5 satisfied; c measured, not extrapolated).

### Runs (frozen)
9 cases (1-6, 8-10) x all supply variants (<= families present + 1) x 2
repeats. Estimated 60-100 aggregator calls + 27 proposer calls. Records
written as RunRecords (JSONL: bench/runs/cell25_moa.jsonl) with the ABLATED
variant texts as upstream — the texts the aggregator actually received.
Floor guard 500 chars. Instruments: regex composite + per-family with
modeled primary (per Cell 24's frozen rule). Estimators: the kit's
shrinkage() with default guards, seed 0; per-family 2x2 as in Cell 24.

### Predictions
- **P25.1 (the form).** The MoA card shows SHRINKAGE: strata means
  monotone in s, w in (0.15, 0.85), c > 0, both CIs excluding the
  faithful-transduction corner (w >= 0.85 with c <= 0.15) and the
  pure-register corner (w <= 0.15). *Falsified if* either corner holds or
  monotonicity fails — the law does not travel even within-lab, and the
  framework paper's central claim must be scoped to council-style
  pipelines.
- **P25.2 (compensating invention).** Composite invention at s=0 occurs at
  rate >= 0.10 with Wilson CI excluding 0. *Falsified if* zero-supply
  invention is ~0 — compensation is council-specific.
- **P25.3 (validated channel).** D_modeled > 0 with bootstrap CI excluding
  0, and below 0.85 (discriminates, imperfectly). *Falsified if* CI
  includes 0 (no discrimination on the clean channel) or exceeds 0.85
  (faithful transduction).

### Consequences (fixed in advance)
- All three hold -> the framework paper proceeds with TWO parameter cards
  side by side, corroboration framing mandatory.
- Any falsified -> the law is scoped to the architectures where it holds,
  the falsifying card is published in the paper with equal prominence, and
  Part E of the framework records the boundary. A null here is a result.
- Ablated-variant fluency check: 10 random variants manually inspected for
  ungrammatical residue before the aggregator stage; if ablation visibly
  mangles texts, the cell STOPS and the ablation is repaired first
  (registered stop condition, not a judgment call after results).

### CELL 25 — REGISTERED DEVIATION, before any aggregator runs (2026-08-05)

The variants stage exposed a design shortfall the registration did not
anticipate: the three GENERAL proposers raise almost no detectable families
(5 family-presences pooled across all 27 proposals), so ablation-only yields
supply levels {0:9, 1:4, 2:1} — which fails the kit's own identifiability
guards (3 levels, one of them a single case). Proceeding as registered would
produce a guaranteed WEAKLY-IDENTIFIED card: a null by design failure, not
by evidence.

**Amendment (no aggregator output exists; nothing is unblinded):** supply is
extended UPWARD by injection, the symmetric operation to ablation and the
same mechanism the framework's C1 corpus design specifies. Injection
sentences are drawn VERBATIM from the stored council specialists'
contributions for the SAME case (bench/runs/imported), selected
deterministically (seed 0): each sentence must fire exactly ONE family under
the lexicon and be 40-400 chars, appended to the end of the last proposer
text. Variants now span each case's natural supply up to 4. Everything else
is unchanged: predictions P25.1-P25.3 as registered (they concern the
fitted law, not the variant mechanism), temperatures, repeats, floor,
estimators, and the fluency stop condition — which now covers injected
variants as well as ablated ones.

Recorded honestly: this narrows what Cell 25 tests. The high-supply strata
now measure the MoA aggregator over general proposals AUGMENTED with
specialist sentences, not purely general-model text. The card's claim
becomes "the writing step under the MoA prompt and mixed upstream," which
is still a different architecture, prompt, and upstream composition from
the council — and the zero/low strata remain purely general-model.

Side observation, recorded for the paper: general instruct models produce
near-zero lexicon-detectable qualification on this battery unprompted —
the specialists' 2.5-4 families per case is itself an upstream property of
domain-tuned seats, not a given of any model ensemble.

---

## CELL 25 VERDICT — the phenomenon travels; the parameters do not. The MoA aggregator sits near the pure-register corner (2026-08-06, 80/80 runs, zero failures, zero guard flags)

Card: bench/analysis/cell25/card.json; report: measure_report.txt. Supply
levels {0:18, 1:18, 2:16, 3:16, 4:12} — zero-supply measured (n=18), w CI
width 0.158, no identifiability flags. Fluency gate passed pre-aggregation
(two context notes recorded: one injected sentence references a "Lead
Agent"; one carries Med42's self-identification, ecologically normal under
the MoA prompt).

**Harness defect caught before recording, owned:** the measure stage's
first P25.1 check tested the corners against the POINT estimate where the
registration demands CI exclusion — the exact instrument-says-what-I-wanted
class from the program audit. It printed SUPPORTED; the registered test
does not. Fixed to the three-way CI-based check before this verdict was
written; both report versions preserved in git history.

| parameter | council (1,260 runs) | MoA (80 runs) |
|---|---|---|
| w (evidence weight) | 0.352 [0.310, 0.391] | 0.158 [0.076, 0.234] |
| c (prior fill) | 0.540 [0.437, 0.651] | 0.275 [0.104, 0.456] |
| prior-trust (1−w)/w | 1.84 | **5.35** |
| invention at s=0 | 0.40 mean emitted | 0.278 rate [0.12, 0.51] |
| f (feature span) | 0.068 | **0.002** |
| D_modeled | 0.213 [0.155, 0.271] | **−0.010 [−0.139, 0.117]** |

**P25.1 PARTIAL — a boundary result, not support.** The shrinkage
DIRECTION is present: strata monotone (0.28 → 0.44 → 0.50 → 0.88 → 0.83),
w CI excludes 0 (the aggregator does respond to supply), c CI excludes 0.
But the registered criterion required the w CI to exclude the pure-register
corner (w <= 0.15) and it does not: [0.076, 0.234] straddles it. Under the
canonical MoA prompt the writer weighs its prior 5.35x over the evidence —
three times the council's 1.84 — and discards ~79% of supplied families
even at full supply (0.83 emitted of 4).

**P25.2 SUPPORTED.** Compensating invention exists in the second
architecture: 0.278 [0.12, 0.51] at zero supply, bar was >= 0.10 with CI
excluding 0. The phenomenon the framework is about — invention rising as
supply falls — is not council-specific.

**P25.3 FALSIFIED.** On the validated modeled channel the MoA aggregator
shows ZERO discrimination: D_modeled = −0.010 [−0.139, 0.117]. It emits
modeled qualification at the same rate whether or not upstream raised it.
The composite w = 0.158 is therefore carried by the low-recall families
(distinctive phrases the aggregator echoes verbatim-ish: jurisdiction
names, sensitivity language), not by behavior on the clean channel.

**REGISTERED CONSEQUENCE EXECUTED.** The law is scoped: the falsifying
card is published with equal prominence, and the framework's Part E gains
its first boundary entry. The two-card story for the paper is sharper than
plain corroboration would have been:

1. The PHENOMENON (compensating invention; monotone supply response)
   appears in both architectures. That part of the law travels.
2. The PARAMETERS are not architecture constants. The council's
   conditional-preservation instruction sits at w = 0.35; the canonical
   MoA aggregation prompt sits at w = 0.16, statistically inseparable from
   arch-flat's naive merge (0.255 [0.13, 0.39]) and from the pure-register
   corner. This RECONCILES with Cell 8's oldest finding: specialist signal
   without a conditional preservation instruction yields near-single-shot
   transport. In framework terms: **w is set by the writing instruction at
   least as much as by the architecture** — the gain-control result,
   re-expressed as the framework's parameter and now measured across two
   architectures.
3. On the validated channel the MoA step is pure register (P25.3) — the
   strongest per-family evidence yet that naive aggregation transports
   nothing the writer wouldn't have said anyway.

Side findings recorded for the paper: general instruct proposers raise
near-zero detectable qualification unprompted (5 presences / 27 proposals)
— rich supply is a property of domain-tuned seats; MoA feature-span
f = 0.002 (the near-silent regime, like arch-flat); empirical best-of-2
again below the independence curve (0.78 vs 0.89 — correlated redraws
replicate in the second architecture, n=9 cells, thin).

---

## CELL 26 PRE-REGISTRATION — agreement-conditioned transport (registered 2026-08-06, before any numbers are computed)

### Question
Does the writer weight CORROBORATED upstream content differently from
singly-raised content? A tension/agreement structure is the pipeline's only
in-band evidence about upstream reliability (the SNR frame's Layer 3). This
cell measures the regex-accessible slice: whether preservation probability
rises with the number of seats independently raising a family. Zero new
model calls; pure ledger recomputation.

### Scope limitation, stated up front
Regex can count how many seats RAISED a family; it cannot detect
CONTESTATION (one seat raising, another disputing). This cell therefore
tests agreement-count weighting only. The full Layer-3 question (does the
writer down-weight contested content?) requires judge labels and is NOT
tested here.

### Population (frozen)
- Primary: all usable ledger records (floor 500 chars, zero-route excluded
  by the adapter) with >= 2 separately-stored seat texts. bench/runs/
  cell25_moa.jsonl is EXCLUDED: its injection variants manufacture k=1
  placements by construction and would contaminate the corroboration
  variable.
- Secondary strata: (a) the 5-arm sweep population (single writer,
  9 shared cases); (b) trigger-heavy vs trigger-light case strata, because
  corroboration count correlates with case trigger density and total
  supply — the unadjusted primary is confounded by case mix, and the
  stratified view is the robustness check.

### Estimator (frozen)
Per family f: k = number of seat texts in which f fires (seat-level
detection on each upstream text separately). Among runs with k >= 1:
T_f(k=1) = P(f in output | exactly one seat raised f), T_f(k>=2) =
P(f in output | two or more seats raised f). Wilson CIs; bootstrap CI on
the difference (5,000 draws, seed 0). Modeled is primary (Cell 24 rule);
other families secondary with their Cell 23 validity caveats attached.
Where n permits, T_f at k = 1, 2, 3 separately with a monotonicity check.

### Predictions
- **P26.1 (agreement weighting, modeled channel).** T(k>=2) − T(k=1) > 0
  with the bootstrap CI excluding 0. *Supported* -> the writer performs at
  least crude reliability weighting, Layer 3 is partially real, and the
  unifying claim "nothing sets the calibration" must be amended to
  "instructions set the gain; agreement structure sets a measurable but
  untested-for-sufficiency part of the calibration."
  *Falsified (CI includes 0 or negative)* -> the writer ignores the one
  reliability signal the multi-agent architecture uniquely provides, and
  the "surfaces evidence it cannot use" claim is hardened from rhetoric to
  measurement.
- **P26.2 (composite, secondary).** Same comparison pooled over the four
  families, interpreted only alongside per-family validity.

### Consequences (fixed in advance)
Either outcome updates the framework paper's discussion paragraph with the
measured version. If P26.1 is SUPPORTED, the Cell 20 conclusion ("the
council surfaces tensions but does not use them") must be narrowed to
commitment behavior only, since weighting behavior would exist. No
optimization, no adoption of any configuration — this is characterization
under the diagnostics-not-objectives rule.

---

## CELL 26 VERDICT — no agreement weighting on the validated channel; the low-validity families show a strong k-response whose mechanism these instruments cannot adjudicate (2026-08-06, 1,165 multi-seat runs, zero model calls)

Report: bench/analysis/cell26_report.txt.

**P26.1 FALSIFIED.** On the validated modeled channel, corroboration buys
nothing: T(k=1) = 0.524 (n=824) vs T(k>=2) = 0.487 (n=76), diff CI
[−0.153, +0.080]. The sweep-population subset agrees (0.766 vs 0.571,
CI overlapping, direction if anything negative). Per the registered
consequence: the writer ignores the one reliability signal the multi-agent
architecture uniquely provides. "Surfaces evidence it cannot use" is now a
measurement, not rhetoric — and it extends Cell 20's finding from
commitment to weighting: the council neither acts on its tensions nor
weights by its agreements, on the channel we can trust.

**The secondary pattern, reported without a mechanism claim.** All three
low-validity families show large, monotone k-responses, disjoint from
zero: cutoff +0.388 [0.33, 0.45] (dose 0.15/0.40/0.62), jurisd +0.434
[0.32, 0.54] (0.28/0.65/0.85), hedging +0.201 [0.14, 0.26]
(0.51/0.70/0.80). Composite P26.2 (+0.163 [0.13, 0.20]) is carried
entirely by them. Three rival mechanisms, NOT adjudicable with these
instruments:
1. Genuine family-specific agreement weighting (behavioral);
2. Phrase-exposure artifact: low-recall families are detected by
   distinctive phrases, and more seats using a phrase mechanically raises
   P(at least one detectable phrasing survives into the output) — a
   coverage effect, not a decision. Detection on modeled is not
   phrase-bottlenecked, which would explain why the flat truth shows only
   there. Note: observed k-curves EXCEED the independent-echo prediction
   1−(1−p)^k (cutoff k=3: 0.62 observed vs 0.39 predicted), so pure
   independent exposure does not fully account for it either;
3. Supply/case-mix confound: k correlates with trigger density and total
   supply (the registration's stated confound; the trigger-light stratum
   is too thin to help, n=25).
Adjudication requires judge labels on a k-stratified sample — recorded as
the natural follow-up, not run.

**Consequence executed.** The framework paper's Layer-3 discussion gets the
measured version: on the validated channel, agreement structure does not
modulate transport. The unifying sentence stands as written —
"instructions set the gain; nothing we found sets the calibration" — now
with the strongest possible support, since even the architecture's own
reliability signal goes unused.

---

## CELL 27 PRE-REGISTRATION — the evidence ledger: externalizing the writer's estimator (registered 2026-08-06, before any runs)

### Hypothesis under test
Every failed intervention tried to change the writer's implicit weights
(rules, training, feedback). This cell tests the untried mechanism class:
serializing the estimation itself into tokens. The writer must produce a
structured EVIDENCE LEDGER — one row per claim/qualification: who raised
it, how many seats independently raised it (k), contested or not, and a
verdict — before writing an answer whose qualifications must correspond to
ledger rows. This is the first mechanism that hands the writer its own
reliability evidence (Cell 26's unused signal) in a form it cannot skip.
It is step-back prompting over the EVIDENCE STRUCTURE rather than the
question; no analogue exists for single models, which is why the standard
prompting literature has not built it.

### Arms (frozen)
- **L2 (primary, cleanest w contrast):** MoA-ledger — the writer runs the
  ledger protocol over the SAME 40 supply variants as Cell 25, 2 repeats
  (80 runs), gpt-oss:20b, temperature 0.6, max_tokens 8192. Direct
  comparison against the Cell 25 naive-MoA card at fixed upstream: any
  (w,c) difference is the mechanism.
- **L1 (secondary, council setting):** council pipeline, gpt-oss all
  roles, synthesis system REPLACED by the ledger protocol (no PRESERVE
  block — the mechanism is tested alone, not stacked on the instruction).
  9 cases x 5 seeds = 45 runs, mode c27-ledger. Path assertion requires
  the marker "EVIDENCE LEDGER" in the writer prompt; zero-route quarantine
  as standard.

### Protocol (frozen)
Single generation, two mandatory sections: "### EVIDENCE LEDGER" (table:
claim | raised by | #seats | contested | verdict adopt/qualify/drop) then
"### ANSWER". Constraint text: every qualification in ANSWER must
correspond to a ledger row with verdict "qualify"; an empty ledger obliges
an unqualified answer.

**Measurement hygiene:** ONLY the ### ANSWER section is scored; the ledger
is stripped before any instrument touches the text (it necessarily
contains family phrases — the annotation-contamination class). Runs
missing the ANSWER delimiter are protocol violations: quarantined and
counted, never pooled. Compliance gate: the first 3 runs are checked for
delimiter compliance only (no measurements examined); if fewer than 2/3
comply, STOP and repair the prompt before proceeding.

### Predictions
- **P27.1 (transport).** The ledger raises the evidence weight above the
  naive mechanism at fixed upstream: L2 w with CI disjoint above Cell 25's
  0.158 [0.076, 0.234]. *Falsified if* overlap.
- **P27.2 (invention discipline).** Zero-supply invention under the ledger
  is below the matched naive rate (L2 vs Cell 25's 0.278; L1 vs
  arch-council's 0.556 at s=0), bootstrap diff CI excluding 0 on the
  primary L2 contrast. *Falsified if* CI includes 0.
- **P27.3 (agreement weighting, the Layer-3 readout).** In the ledger
  arms, T(k>=2) - T(k=1) > 0 where the SAME contrast in matched naive
  arms is null — difference-in-differences bootstrap CI excluding 0,
  composite across families (modeled reported but registered as too thin
  for a solo verdict at these n; any composite signal inherits Cell 26's
  mechanism ambiguity unless the DiD isolates it).
- **P27.4 (coupling — the dissociation detector).** >=80% of answer
  qualifications have a same-family ledger row with verdict "qualify",
  AND empty-ledger runs produce zero answer qualification. *Falsified*
  -> the Cell 20/21 pattern (form without function) extends to
  externalized reasoning.

### Program prior, stated for honesty
The record (Cells 17, 19, 20, 21, 26) predicts nulls on P27.1-27.3 and
partial failure on P27.4. The registered predictions are the mechanism's
claims, not ours.

### Consequences (fixed in advance)
- All null -> externalization joins the intervention scorecard as tested
  and failed; "instructions set the gain; nothing we found sets the
  calibration" gains its strongest supporting null (even explicit,
  mandated consumption of the reliability evidence does not move it).
- Any supported -> the first mechanism to move calibration-side behavior;
  requires a replication arm before any paper claim, and per the
  diagnostics-not-objectives rule, NO configuration is adopted from this
  cell regardless of outcome.

---

## CELL 27 VERDICT — all four registered predictions falsified; the ledger is not a transport mechanism, it is a bottleneck that relocates the estimator and, in doing so, eliminates prior fill (2026-08-07, L2 79 runs / L1 45 runs)

Reports: bench/analysis/cell27/measure_report.txt. Compliance tax: L2 9/79
violations + 1 empty; L1 7/45 violations; all quarantined, never pooled.

**Registered outcomes, exactly as frozen:**
- **P27.1 FALSIFIED.** No transport gain anywhere. L2 w = 0.119
  [0.010, 0.244] vs naive 0.158 [0.076, 0.234] — overlapping, and the
  ledger card's verdict is PURE REGISTER. L1 w = 0.385 [0.291, 0.478] vs
  arch-council 0.346 [0.22, 0.47] — unchanged.
- **P27.2 FALSIFIED on the registered primary** (L2 diff CI
  [−0.444, +0.033] includes 0). The registered secondary contrast is
  DISJOINT: L1 zero-supply invention 0/12 [0.00, 0.24] vs arch-council's
  5/9 = 0.556 [0.27, 0.81]. Reported as the registration wrote it: primary
  falsified, secondary separated.
- **P27.3 FALSIFIED.** No agreement weighting: DiD CI [−0.471, +0.187].
  Externalizing k into a mandatory column did not create the weighting
  Cell 26 showed missing. The Layer-3 null now covers implicit AND
  explicit presentation of the reliability signal.
- **P27.4 FALSIFIED, narrowly.** Family-level coupling 15/20 = 0.75
  against the 0.80 bar; empty-ledger runs bare in 43/49 (88%).

**The unregistered pattern, reported as such (post-hoc; requires a
registered replication before any claim graduates):** the ledger acts as a
QUALIFICATION SUPPRESSOR that kills the prior-fill term. Both arms produce
the only c ≈ 0 cards ever measured in this program — L2 c = 0.083
[−0.083, 0.262], L1 c = −0.022 [−0.138, +0.088], both centered at zero
with zero-supply MEASURED (n=15, n=12) — and L1 pairs it with an
unchanged w and near-monotone strata (0 / 0 / 0.75 / 1.21 / 1.44). The
mechanism is visible in the data: shrinkage relocated INTO the ledger
phase (49/69 L2 ledgers declared no qualification rows despite upstream
supply in most runs), and the answer then obeys the impoverished ledger
(88% empty→bare). Externalization does not remove the estimator — it
moves it to whatever step summarizes — but the consistency constraint
converts free invention into zero: nothing in the ledger, nothing
invented. The price is overall emission: L2 collapses to the silent
regime (f = 0.000, 52/69 runs with zero qualification — deeper than
arch-flat); L1 pays moderately (mean emitted 0.80 families vs the
council's ~1.5; 18/41 runs unqualified), plus the ~14% protocol-violation
tax. Per the paper's own warning, the c → 0 numbers MUST be read beside
f: part of "no invention" is "less said."

**Consequences per registration:** externalization joins the intervention
scorecard as tested and falsified on all four registered predictions;
"instructions set the gain; nothing we found sets the calibration" gains
its strongest null (the writer was HANDED the reliability signal in a
mandatory column and still did not weight by it). NO configuration is
adopted. The c→0 / w-preserved pattern in L1 is the single most promising
unregistered observation this program has produced, and the registered
path for it is a replication cell (fresh seeds, both batteries, f and
protocol-tax reported beside c) before it appears in any paper claim
stronger than an observation.

---

## CELL 28 PRE-REGISTRATION — replication of the ledger's c→0 / w-preserved pattern (registered 2026-08-07, before any runs)

### What graduates from observation to hypothesis
Cell 27's registered predictions all falsified, but its council arm (L1)
produced a post-hoc pattern no prior arm has shown: prior fill eliminated
(c = −0.022 [−0.138, +0.088], zero-supply invention 0/12) with the evidence
weight intact (w = 0.385 [0.291, 0.478]), at a measured cost (mean emission
0.80 families vs ~1.5; 7/45 protocol violations). Per the Cell 27
consequence, that pattern must replicate on fresh samples under registered
predictions before it appears in any paper as more than an observation.
This cell is that replication. NO adoption regardless of outcome
(diagnostics-not-objectives rule).

### Arm (frozen)
R1: council pipeline, gpt-oss:20b all roles, ledger synthesis protocol
BYTE-IDENTICAL to Cell 27's (same LEDGER_PROTOCOL constant, same delimiter
rules, same path assertion on "EVIDENCE LEDGER", zero-route quarantine).
9 cases x 5 fresh seeds = 45 runs, mode c28-ledger-rep. Measurement
hygiene identical: only the ANSWER section is scored; violations
quarantined and counted. Baseline for comparison: the frozen arch-council
sweep numbers (w 0.346 [0.22, 0.47]; c 0.713 [0.44, 0.99]; s=0 invention
5/9 = 0.556 [0.27, 0.81]). No contemporaneous baseline arm is run; the
model and stack are unchanged since those numbers were produced, and this
is recorded as a known limitation.

### Predictions (the pattern's claims, now frozen)
- **P28.1 (prior fill eliminated).** R1's c CI upper bound < 0.44 — 
  disjoint below the baseline c CI. *Falsified if* not disjoint.
- **P28.2 (invention eliminated at zero supply).** R1's s=0 invention
  Wilson CI upper bound < 0.27 — disjoint below the baseline's
  [0.27, 0.81]. Requires the s=0 stratum to reach n >= 8; if it does not,
  this prediction is NOT EVALUABLE and is reported as a design shortfall,
  never scored on thinner data.
- **P28.3 (gain preserved).** R1's w CI lower bound > 0.15 (excludes the
  register corner) AND the CI overlaps Cell 27 L1's [0.291, 0.478].
  *Falsified if* either fails — c→0 via silence (the L2 degeneracy) does
  not count as replication.

### Mandatory cost accounting (reported, not predicted)
Mean emitted families, fraction of runs with zero qualification,
feature-span f, and the protocol-violation rate — all beside the headline
numbers, per the paper's silence warning. A c→0 card whose f collapses to
the L2 regime must be reported as degenerate even if P28.1-28.3 pass.

### Consequences (fixed in advance)
- All three hold -> the finding is REPLICATED and enters the framework
  paper's intervention section and the behavior paper as: the first tested
  mechanism that moves the calibration-side term — an auditable bottleneck
  that eliminates invention by removing the untracked place it happens —
  with its emission and compliance costs stated in the same sentence.
- Any falsified or not-evaluable -> the Cell 27 pattern is recorded as
  sampling noise or unstable, and the c→0 claim dies before entering any
  paper. Either way the intervention scorecard's headline (no mechanism
  moves w) is unchanged — this cell concerns c only.

---

### CELL 28 PRE-ANALYSIS NOTE — composition-law predictions, registered before the measure stage runs (2026-08-07; runs in progress, no measurements examined)

If the ledger factors generation into two stages (upstream s -> ledger
supply l -> answer y), each stage a shrinkage estimator (l = w1*s + c1;
y = w2*l + c2), then the composite law is y = (w1*w2)*s + (w2*c1 + c2).
Registered predictions, testable on data already on disk:

- **PA28.a (stage decomposition).** Fitting the two stages separately on
  the STORED ledger sections (regress regex-measured l on s, and y on l,
  Cell 27 L1 + Cell 28 pooled compliant runs) recovers the composite:
  w1*w2 within the fitted w' CI and w2*c1 + c2 within the fitted c' CI.
- **PA28.b (violation mixture, the deployment formula).** The registered
  P28.1 is CARD-level (compliant runs only). System-level prior fill as
  deployed is c_sys = v*c_prose + (1-v)*c_card, with v the violation rate
  and c_prose the baseline 0.713. Prediction: Cell 28's violation runs,
  scored on their un-delimited full text, show zero-supply invention at
  the baseline rate (CI overlapping [0.27, 0.81]), NOT the ledger rate —
  violations revert to the prose register.

These are mechanism checks, not success criteria; P28.1-28.3 remain the
registered verdict as frozen.

---

## CELL 28 VERDICT + PA28 — the pattern replicates; the formula does not survive its own mechanism check; Cell 29 is discarded at its gate (2026-08-07, 45 runs; measure + PA reports in bench/analysis/cell28/)

**P28.1 SUPPORTED.** c = −0.024 [−0.164, 0.112], disjoint below the
baseline [0.44, 0.99]. Prior fill eliminated on fresh samples.

**P28.2 FALSIFIED AS REGISTERED — with a registration defect, owned.** The
data were the best possible: 0 inventions in 10 zero-supply runs. The
frozen bar (Wilson upper < 0.27) is mathematically unattainable with zero
events below n = 11 (0/10 gives [0.00, 0.28]), and the registered
evaluability floor (n >= 8) permitted exactly that dead zone. The bar
failed by construction, not by evidence. Recorded consequence executes AS
WRITTEN: the c→0 finding does not enter any paper on this cell's
authority. Post-hoc observation, clearly labelled: pooling the
byte-identical protocols (C27-L1 0/12 + C28 0/10 = 0/22, Wilson
[0.00, 0.15]) is disjoint below baseline — a re-registered criterion with
an attainable bar (pooled analysis, or n >= 15) is the path back, and no
shortcut is taken here.

**P28.3 SUPPORTED.** w = 0.308 [0.181, 0.443]: excludes the register
corner, overlaps C27-L1. Not silence.

**Cost accounting (mandatory):** mean emitted 0.59 families (below
C27-L1's 0.80 — suppression deepened); 25/41 runs zero-qualification;
f = 0.000 median; violations 9/45 = 20% (early case-1/2 cluster, settled
thereafter; vs C27-L1's 16% — compliance is variable across samples).

**PA28.a FALSIFIED — and this is the mechanically informative result.**
Stage fits on the stored ledgers: w1 = 0.417 [0.32, 0.52],
c1 = −0.062 (the register-swap claim HOLDS at stage 1: ledgers do not
invent); w2 = 0.540 [0.35, 0.81], c2 = 0.280; direct composite
w' = 0.367 [0.27, 0.46], c' = −0.033. The Markov predictions fail on both
axes: w1·w2 = 0.225 sits BELOW the direct CI (super-multiplicative) and
w2·c1+c2 = 0.246 sits above c'. Diagnosis, stated as the corrected
mechanism (unregistered until re-registered): the single-generation
protocol is NOT a Markov chain — the answer conditions on the upstream
text directly, not only through the ledger. Transport BYPASSES the ledger
(which is why w matched baseline instead of paying the multiplicative
tax), while invention still dies because emitting an unlicensed
qualification requires evading BOTH the missing upstream source and the
missing ledger row. The ledger is a LICENSING GATE on emission, not an
information bottleneck. The two-path model y = a·s + b·l + c0 is the
candidate replacement and requires its own registration before any
further test. The chain formula's fragility claim (w' = ∏w_k) is
withdrawn for single-generation designs.

**PA28.b NOT EVALUABLE** (1 zero-supply violation run against the n >= 5
floor).

**CELL 29: DISCARDED AT ITS GATE.** The queued registration required
P28.1 + P28.3 + PA28.a. PA28.a falsified; the corpus-wide chain test's
premise (multiplicativity) is refuted at the within-generation level, and
the draft leaves the queue unregistered. A future corpus test would have
to carry the two-path form, registered fresh.

**Net:** the phenomenon (c→0 with w preserved) replicated on both
registered axes that were attainable; the theory I wrote for it was
refuted by its own pre-registered check and replaced by a sharper one the
same day. The discipline did exactly what it exists to do — in both
directions at once.

---

## CELL 29 PRE-REGISTRATION — phenomena atlas: corpus-wide measurement of the observed mathematical regularities (registered 2026-08-07, before any numbers are computed)

NOT the discarded chain test. The gate-discarded Cell 29 draft
(multiplicative composition) stays dead; nothing here assumes Markov
structure. This cell measures four regularities observed across cells,
each with a frozen estimator and — per the P28.2 lesson — bars checked
for ATTAINABILITY at the realized n before freezing. Zero model calls.

### Population (frozen)
Imported-ledger arms with n >= 30 usable runs and >= 3 supply levels
(kit adapter rules; ledger-register arms c27-ledger and c28-ledger-rep
included at their usable n), plus the two jsonl cards (cell25 naive-MoA,
cell27 L2) as arms. All fits via the kit, seed 0.

### Analyses and predictions
- **P29.1 (the w-band, random-effects meta-analysis).** DerSimonian-Laird
  over per-arm (w, SE) with SE from the seeded bootstrap CI. Weakly
  identified arms are INCLUDED with their wide SEs — that is the point of
  the machinery. Predictions: pooled mu_w CI within [0.15, 0.50]; the 95%
  prediction interval for a NEW arm's w has upper bound < 0.85 (excludes
  faithful transduction). tau reported unconditionally.
- **P29.2 (prompt heterogeneity).** One-way ICC of invention counts over
  (prompt, condition, writer) cells with >= 2 runs, bootstrap over cells
  (2,000 draws, seed 0). Prediction: ICC CI lower bound > 0. Dispersion
  indices per (arm x supply) cell with n >= 15 are reported
  DESCRIPTIVELY with no bar: counts bounded at 4 and typically 0/1 make
  the Poisson-vs-Bernoulli distinction underpowered at these rates — a
  bar there would repeat the P28.2 defect, so none is set.
- **P29.3 (aggregation distortion, slope decomposition).** On the pooled
  qualifying runs, w_f = cov(y_f, s)/var(s), summing to composite w.
  Prediction: the validated modeled channel's share w_modeled/w < 0.25
  (its equal share), bootstrap CI upper bound < 0.25. Full family table
  reported; per-arm table for the five comparable arms.
- **P29.4 (register-dependent intercept).** RE-pooled c by output
  register: prose arms vs ledger arms (c20-decide reported descriptively,
  single arm). Prediction: prose and ledger 95% CIs disjoint, prose
  above.
- **Reported, no prediction:** retrospective attainability audit of every
  numeric registered bar in this runbook against its realized n.

### Consequences (fixed in advance)
Supported predictions enter the framework paper's discussion as a named
phenomena section with these fits as their evidence. Any falsified
prediction is reported at equal prominence and the corresponding
phenomenon is demoted from the discussion. No adoption, characterization
only.

---

## CELL 29 VERDICT — phenomena atlas: three regularities graduate to corpus-level measurements; one falsifies; my informal "band" narrative is corrected by its own test (2026-08-07, 1,300+ runs, 25 qualifying arms, zero model calls)

Report: bench/analysis/cell29/atlas_report.txt.

**P29.1 SUPPORTED — and the band narrative is revised by the measurement.**
DerSimonian-Laird over 25 arms: mu_w = 0.364 [0.290, 0.438], tau = 0.158,
new-arm 95% prediction interval [0.045, 0.682]. Both registered bars pass
(mu CI within [0.15, 0.50]; PI excludes faithful transduction). But the
informal claim I had been repeating — "w never leaves [0.12, 0.45]" — is
WRONG as stated: cell6b-lead-repro sits at 0.760 +/- 0.070 (extrapolated
intercept, but the slope is real within its observed range), and the PI
honestly spans to 0.68. The corrected phenomenon: no measured arm
approaches transduction, central tendency ~0.36, genuine between-arm
spread tau ~ 0.16. The atlas exists precisely to replace eyeballed
invariants with estimated ones.

**P29.2 SUPPORTED.** ICC = 0.190 [0.128, 0.242] over 251 repeated cells
(1,279 runs): ~19% of invention variance is between-prompt. The
correlated-redraw phenomenon is now a single corpus-level number, and
selection sizing must use it. Dispersion indices (descriptive, no bar as
registered): median 0.93, range [0.57, 1.00] — mildly UNDER-dispersed,
consistent with bounded near-binary counts; the decision not to register
a Poisson bar was correct, and the "near-Poisson" label from the earlier
inventory should be retired in favor of "Bernoulli-like with
prompt-level rate heterogeneity."

**P29.3 FALSIFIED.** Modeled share of composite w = 0.219 [0.170, 0.268]
— below equal share at the point but the CI includes 0.25. The registered
aggregation-distortion claim (validated channel carries decisively less
than its share) does not hold corpus-wide; per the consequence it is
DEMOTED from the framework paper's discussion. What the decomposition
does show, reported descriptively: hedging (the FP-prone channel) carries
the largest single share (0.151/0.383 ~ 39%). The distortion story
survives only in that weaker, unregistered form.

**P29.4 SUPPORTED.** Register-pooled intercepts: prose c = 0.407
[0.164, 0.651] (tau = 0.270 — prose arms are heterogeneous) vs ledger
c = -0.023 [-0.110, 0.065] (tau = 0.000 — the two ledger arms agree
exactly). Disjoint. The register-dependent intercept is now a
corpus-level measured phenomenon; decide-register (single arm,
descriptive) sits highest at 0.805.

**Attainability audit (registered as reported-no-prediction), performed
by review of every numeric bar in this runbook against its realized n:**
one by-construction dead zone found — P28.2, already owned (Wilson bar
unattainable with zero events below n=11 while the floor permitted n=8).
Two bars flagged as underpowered-but-attainable at their n: P17.1 and
P19.1 (trigger-free strata at n=15 could not separate moderate true
effects; their nulls are correspondingly weak evidence, as their verdicts
already noted). All other registered numeric bars were attainable at
their realized n.

**Consequences executed:** P29.1, P29.2, P29.4 enter the framework
paper's discussion as the named phenomena section with these fits as
evidence (with the band stated in its corrected form); P29.3's claim is
demoted; the "near-Poisson" label is retired.

---

### PROGRAM AUDIT #2 — adversarial self-audit; instrument-validity finding #8 (2026-08-07)

Full document: docs/PROGRAM_AUDIT_2026-08-07.md. Headline results:

- **Finding #8, instrument–scaffold entanglement (SEVERE, checked
  empirically):** the seat prompts name the measured families and in two
  places dictate the literal lexicon strings ("use 'modeled at',
  'assumed'"; "assuming, under the assumption that"). Instruction-gain
  results are downgraded to conditional phrase-compliance; cross-
  architecture w comparisons are scaffold-confounded; supply is
  manufactured. Survives untouched: uninstructed zero-supply invention,
  the ledger-register contrast (treatment arm verified scaffold-free), and
  the a-fortiori reading (transport reaches only ~1/3 even when rigged in
  its favor).
- **Cleared:** authored case texts are lexicon-clean (measured; zero
  families fire in any case prompt) — the trigger design is topical, not
  string-circular.
- **Registration-strength stratification:** prospective cells carry force;
  retrospective cells 24/26 retain force via author-surprising outcomes;
  P29.4 is re-graded to descriptive measurement (registered after its
  answer was known).
- **Terminology audit:** "bottleneck" drove refuted math (caught by
  PA28.a); "dose" smuggled causal language onto the observational council
  card — paper amendment required; "Poisson" drove wrong selection math,
  retired; "heat" was banned before it touched math; "shrinkage" is a
  valid regression under a cognitive story that must stay labelled as
  story.
- **Mandates:** paper amendments (observational labeling, scaffold
  disclosure, within-scaffold instruction claim); the de-scaffolded
  replication with a second writer as the highest-value future cell; kit
  docs warning on scaffold entanglement.

---

## CELL 30 PRE-REGISTRATION — the de-scaffolded replication (registered 2026-08-07, before any runs)

### Why this cell exists
Program audit #2 (finding #8) established that the seat prompts name the
measured families and dictate two literal lexicon strings. Every w
estimate in this program was therefore measured on a system whose
instructions and whose instrument share vocabulary. This cell removes the
shared vocabulary from BOTH sides — de-scaffolded seat prompts AND a
paraphrase-robust instrument — and adds a second writer model. It asks the
only question that matters after the audit: **does the shrinkage law
survive when nothing in the system is told the words the instrument
looks for?**

This is NOT a replication of arch-council's numbers. The system is
deliberately different (no family names anywhere). The claim under test is
the FORM of the law and the existence of invention, not the parameter
values.

### Design (frozen)
Direct-call pipeline (no orchestrator/planner; path assertion N/A and
recorded as route-free by design, per the Cell 25 category):
- **Seats:** gpt-oss:20b in three domain roles (healthcare, legal,
  finance) under DE-SCAFFOLDED prompts, frozen verbatim in
  train/run_cell30_descaffold.py: they request substantive domain analysis
  and contain NO family names, NO uncertainty instruction, and NO phrase
  dictation. Temperature 0.7.
- **Supply variation:** sentence-level ablation of the seat outputs
  (gst.corpus.supply_variants). Ablation is regex-driven for CONSTRUCTION
  only; measured supply is whatever the JUDGE instrument reports on the
  resulting text, so the construction instrument does not define the
  measured variable. No injection (injection would reintroduce scaffolded
  sentences).
- **Writers:** gpt-oss:20b (primary, 2 repeats per variant) and phi4:14b
  (secondary, 1 repeat) under a neutral synthesis prompt with no PRESERVE
  block and no family names. Temperature 0.6.
- **Cases:** the 9-case battery (already verified lexicon-clean in audit
  #2, A2).

### Instrument (frozen)
PRIMARY: document-level dual-judge (gpt-oss:20b + qwen2.5:7b-instruct,
temperature 0, max_tokens 2048) using the frozen Cell 23 family
definitions, requiring a VERBATIM QUOTE per positive judgment. Quotes are
substring-verified against the source (whitespace-normalized); an
unverified quote makes that judgment ABSENT and is counted. A family is
present only where both judges agree. Empty/unparseable replies excluded
and counted, never defaulted.
SECONDARY (reported, not authoritative): regex, for the divergence check.

### Predictions
- **P30.0 (instrument validity gate).** Judge-judge agreement on this
  corpus >= 0.70. *If below, ALL other predictions are NOT EVALUABLE* and
  the cell reports an instrument failure.
- **P30.1 (the law survives).** Judge-measured w over the primary-writer
  runs has bootstrap CI lower bound > 0. *Falsified if* the CI includes 0.
  *Not evaluable if* judge-measured supply spans < 3 levels — which would
  itself be the finding that specialist qualification is an artifact of
  instruction, and is reported as such.
- **P30.2 (invention survives de-scaffolding — the key test).**
  Judge-measured zero-supply invention rate has Wilson CI lower bound > 0,
  pooled across writers (expected n ~ 36; attainable in both directions —
  2+ events gives a lower bound above 0, and 0 events gives [0, ~0.10]).
  *Falsified if* the CI includes 0.
- **P30.3 (second writer).** The phi4 card shows w CI lower > 0 AND
  zero-supply invention CI lower > 0. *Falsified if* either fails — the
  law would then be one model's law.
- **P30.4 (instrument divergence).** On de-scaffolded outputs, the
  regex-measured invention rate is BELOW the judge-measured rate (regex
  under-counts once its scaffold phrasings are absent). *Falsified if*
  regex >= judge.

### Consequences (fixed in advance)
- P30.1+P30.2 supported → the law and the invention phenomenon are
  scaffold-free; the framework paper's amendments are limited to the
  instruction-gain and cross-architecture claims (audit #2 mandate), and
  the central law stands on this cell rather than on the entangled corpus.
- P30.2 falsified → invention was a scaffold artifact. The framework
  paper's central phenomenon is WITHDRAWN and the paper is rewritten
  around measurement methodology alone. This is the outcome that would
  end the program's headline claim, and it is registered as such.
- P30.3 falsified → all parameter claims are scoped to one writer model,
  stated in the abstract.
- No adoption of any configuration; characterization only.

---

## CELL 30 VERDICT — INSTRUMENT FAILURE at the registered gate; the audit's mandated replication is BLOCKED on instrumentation (2026-08-07, 60 runs generated, 80 texts judged)

**P30.0 FAILED. Judge-judge agreement = 0.622 (179/288 family decisions),
below the registered 0.70 bar. Per the registration, P30.1-P30.4 are NOT
EVALUABLE.** Executed as written; no bar was moved and no substitute
instrument was promoted to rescue the cell.

**Critical clarification, checked:** the agreement statistic is computed on
the judges' `present` flags and never touches quote verification, so the
harness's quote-normalization defect (below) did NOT cause the gate
failure. The instrument failure is genuine.

**Diagnosis — instrument-validity finding #9: judge reliability is
GRANULARITY-DEPENDENT.** Cell 23 validated these same two judges at 0.86
agreement on SENTENCE-level labelling of short texts. At document level
over ~5,000-character analyses they fail:

| family | agreement | gpt-oss positives /72 | qwen positives /72 |
|---|---|---|---|
| jurisd | 0.833 | 54 | 48 |
| hedging | 0.764 | **71** | 54 |
| cutoff | 0.556 | **3** | **33** |
| modeled | 0.333 | 26 | 50 |

Two degeneracies: gpt-oss flags hedging in 71 of 72 texts (a detector that
never says no), and the judges differ 11-fold on cutoff. This mirrors
Cell 21's voided absolute-labelling pass and Cell 7a's finding that the
NLI hedging hypothesis fired on nearly everything — hedging and cutoff
now look diffuse at document scale under THREE instruments.

**Harness defect, owned:** quote verification normalized only whitespace
and case, so legitimate quotes containing unicode spaces/dashes, markdown
emphasis, or `<br>` failed (123 unverified positives, some of which were
genuine). One judge also quoted the DEFINITION back verbatim rather than
the text. Normalization is now hardened in the harness for future use; the
Cell 30 verdict is NOT re-run on it, because the gate it failed does not
depend on it.

**Consequence — the program's most important open question is now
instrument-blocked.** Audit #2 mandated a de-scaffolded replication with a
paraphrase-robust instrument. The de-scaffolded CORPUS now exists (60 runs,
two writers, seat prompts verified free of family names and phrase
dictation). The instrument does not. Sentence-level judging is validated
but costs ~4,800 calls for this corpus. **The classifier trained on Cell
23's 200 judge-labelled sentences is therefore promoted from optional
future work to the BLOCKING dependency** for testing whether the shrinkage
law survives de-scaffolding.

**Post-hoc, clearly labelled, NOT an evaluation of P30.1-P30.4** (regex is
low-recall outside the modeled channel; single instrument; reported
because it informs whether the classifier investment is warranted): on the
de-scaffolded corpus regex measures w = 0.196 [-0.021, 0.394] pooled
(CI includes zero), c = 0.250 [0.058, 0.499], with zero-supply invention
4/27 = 0.148 [0.059, 0.325] composite and 2/51 = 0.039 [0.011, 0.132] on
the validated modeled channel. Both writers show the same qualitative
shape. Read only as: invention does not visibly vanish without the
scaffold, and the effect sizes are small enough that the properly
instrumented test is worth running rather than assumed either way.

---

## CELL 31 PRE-REGISTRATION — the matched-baseline ledger test (registered 2026-08-07, before any runs)

### The confound this repairs
Cells 27/28 changed TWO things at once: they replaced the PRESERVE
synthesis instruction AND added the ledger licensing constraint — then
compared against arch-council, which still had PRESERVE. Post-hoc check on
existing data: arch-council c = 0.799 [0.560, 1.050]; arch-flat (no
PRESERVE, no ledger) c = 0.162 [-0.102, 0.425]; ledger arms c ~ -0.02.
Most of the drop occurs on clause removal, and the ledger's own increment
overlaps every available control. P28.1's "disjoint below baseline" is
technically correct and substantively misleading.

### Design (frozen) — PAIRED, one variable
Cell 30's de-scaffolded corpus provides the matched control: identical
seats (no family names, no phrase dictation), identical ablation variants,
identical writers, identical neutral writer prompt. The ONLY difference is
the ledger protocol.
- **Arm L (new):** the Cell 27 LEDGER_PROTOCOL verbatim (imported, not
  copied) as the writer system prompt, over the SAME Cell 30 variants;
  gpt-oss:20b x2 repeats + phi4:14b x1 repeat, temperatures matching
  Cell 30 (0.6). Only the ANSWER section is scored; ledger stripped;
  delimiter violations quarantined and counted.
- **Arm P (existing, not re-run):** Cell 30's plain-writer runs,
  bench/runs/cell30_descaffold.jsonl, c = 0.250 [0.058, 0.499],
  w = 0.196 [-0.021, 0.394].
- Instrument: regex, stated as a limitation up front (the judge instrument
  failed its Cell 30 gate). Both arms are measured identically and neither
  arm's prompts contain lexicon strings, so the comparison is internally
  clean even though absolute levels are undercounts.

### Estimator (frozen) — and why paired
Because the arms share variants, the contrast is estimated as the
difference in fitted parameters under a CLUSTER bootstrap resampling
VARIANTS (5,000 draws, seed 0), not as two independent CIs. Requiring
disjoint independent CIs would be unattainable here (Cell 27/28's ledger c
upper bound ~0.09 already exceeds Arm P's lower bound 0.058) — an
attainability check performed at registration per the P28.2 lesson.

### Predictions
- **P31.1 (the isolated ledger effect).** Delta-c = c_L - c_P has cluster-
  bootstrap CI entirely below 0. *Falsified if* the CI includes 0 — the
  ledger contributes nothing beyond removing the PRESERVE clause, and the
  Cell 27/28 c->0 finding is withdrawn as a clause-removal artifact.
- **P31.2 (transport not destroyed).** Delta-w CI includes 0 or lies above
  it. *Falsified if* entirely below 0 — the ledger buys its intercept by
  suppressing transport, i.e. the silence route.
- **Reported without a bar (attainability: too few zero-supply events for
  a powered test):** zero-supply invention in both arms with Wilson CIs;
  mean emitted families; protocol-violation rate.

### Consequences (fixed in advance)
- P31.1 supported -> the ledger is a real mechanism; Cells 27/28 stand
  with their baseline corrected, and the finding may enter the papers with
  the paired contrast as its evidence.
- P31.1 falsified -> the ledger finding is WITHDRAWN from the program's
  claims, and what replaces it is the already-measured and more useful
  fact that the PRESERVE clause causes the invention it was written to
  prevent.

---

## REGISTERED RE-ANALYSIS PD-13 — is the clause effect compliance or behavior? (registered 2026-08-07, before computation; zero model calls)

### Question
Audit #2 established that council/prompts.py dictates literal lexicon
strings. Cells 13/6c attribute large effects to individual clauses. This
re-analysis tests whether those effects are concentrated in the DICTATED
phrasings (compliance) or spread across a family's other phrasings
(behavior change).

### Method (frozen)
A lexicon pattern is classified DICTATED if it matches anywhere in the
text of council/prompts.py, and NON-DICTATED otherwise — an objective,
mechanical split, computed before any outcome is examined. Per family,
each Cell 13 arm's outputs are scored separately on the dictated and
non-dictated pattern sets (presence per run). The contrast is
arm-vs-c13-none, difference-in-differences between the two pattern sets,
bootstrap 5,000 draws, seed 0.

### Predictions
- **PD13.1 (compliance signature).** For the family a clause names, the
  lift on DICTATED patterns exceeds the lift on NON-DICTATED patterns,
  DiD CI excluding 0. *Falsified if* the CI includes 0 — the effect is
  phrasing-general and survives as behavior change.
- **Evaluability floor:** a family/arm channel is scored only where the
  non-dictated pattern set produces >= 5 positive runs somewhere in the
  contrast; otherwise NOT EVALUABLE and reported as a design limit of the
  lexicon, not as a result.

### Consequence
PD13.1 supported -> the Cell 13/6c clause-magnitude claims are relabelled
as instruction compliance throughout the papers, and the framework paper's
instruction-gain contribution is withdrawn rather than merely scoped.
PD13.1 falsified or not evaluable -> the claims stand as scoped by audit
#2, with the ambiguity recorded.

---

## PD-13 VERDICT — SUPPORTED, decisively. The clause effects are instruction compliance, and the framework paper's instruction-gain contribution is WITHDRAWN per the registered consequence (2026-08-09, zero model calls)

Report: bench/analysis/pd13/report.txt.

The mechanical split (a pattern is DICTATED iff it matches the text of
council/prompts.py) put 2 of the 7 modeled-family patterns on the dictated
side: `modell?ed at` and `under the assumption` — the two phrasings the
PRESERVE clause and the finance seat prompt literally instruct the model
to use.

**c13-c2, the numeric clause, contrasted against c13-none (n=30 each):**

| channel | baseline | with clause | lift |
|---|---|---|---|
| DICTATED phrasings | 0/30 | **28/30** | **+0.933** |
| non-dictated phrasings | 1/30 | 4/30 | +0.100 |

DiD = **+0.833 [+0.667, +1.000]**, CI excluding 0. **The clause's entire
effect is the model typing the two phrases it was told to type.** The five
other ways of expressing the same family barely move.

c13-c4 (cutoff): dictated 0/30 -> 8/30, non-dictated 0/30 -> 0/30 —
directionally identical but NOT EVALUABLE per the registered floor (0
positive runs on the non-dictated channel). Recorded as a lexicon design
limit, not a result.

Whole-block (c13-all vs c13-none) per family: modeled dictated 0->28 vs
non-dictated 1->3 (same signature); jurisd essentially flat on both
channels; **hedging shows the OPPOSITE pattern — dictated 18->17 (flat)
while non-dictated 1->9** — which is the genuine-behavior signature and
is recorded as such: whatever the block does to hedging is not phrase
compliance. This is the one channel where an instruction effect survives
the test, and it is not the channel Cell 13's headline was about.

**REGISTERED CONSEQUENCE EXECUTED.** Cell 13/6c clause-magnitude claims
are relabelled as instruction compliance throughout, and the framework
paper's instruction-gain contribution is WITHDRAWN rather than scoped.
Specifically retired: "the writing instruction moves w more than the
entire architectural difference", the 0.16 -> 0.35 gradient as evidence
about instructions, and "C2 carries 126% of the block's gain" as a
behavioral claim. What replaces them is narrower and better evidenced:
**an instruction that dictates a phrase reliably produces that phrase
(0/30 -> 28/30) and produces almost nothing else** — which, combined with
the audit's finding that the same clause causes unwarranted qualification
on trigger-free cases, makes the PRESERVE block a phrase generator rather
than a disposition control.

---

### COMPREHENSIVE CLEAN — audit consequences executed on the artifacts (2026-08-09)

Audit consequences had been RECORDED in this runbook but several were never
EXECUTED on the papers and code. That gap is itself a defect class (a
verdict that says "consequence executed" while the artifact still carries
the claim), and this pass closes it.

**Executed:**
1. **PD-13's consequence, actually applied.** paper_framework.tex still
   contained "the writing instruction moves w more than the entire
   architectural difference ($0.16 \to 0.35$)" as contribution #2 and an
   entire section built on it. Contribution #2 is now "What does NOT set
   the parameters"; the section is rewritten as an explicit withdrawal
   with the DiD decomposition as its evidence, and reports the one channel
   (hedging) whose pattern is the opposite.
2. **Instrument-status banner** added to both active papers, marking every
   quantitative result PROVISIONAL pending re-measurement, and stating
   which results do NOT depend on the lexicon (scaffold-free arms;
   inspection-based findings).
3. **docs/STATUS.md created** — the authoritative claim ledger. LIVE /
   PROVISIONAL / WITHDRAWN / BLOCKED for every claim the program has made,
   plus the standing methodological directives and per-artifact status.
   Where any artifact disagrees with STATUS.md, STATUS.md is correct.
4. **Kit hardened.** RegexInstrument's docstring now leads with the three
   measured reasons its output was withdrawn, and a new
   `audit_scaffold_overlap(instrument, *prompt_sources)` reports which
   patterns appear in the system's own prompts. Run against
   council/prompts.py it finds dictated patterns in ALL FOUR families
   (jurisd worst: 4 dictated, 1 clean). Two tests added; 48 pass.
5. **Cell 31's measure stage HELD** under the no-regex directive. Its runs
   continue (generation is instrument-independent); measurement waits for
   a validated instrument.

**Standing directives now recorded in STATUS.md §6:** no regex as an
instrument; the cutoff family is unmeasurable with current labels (3
positives) so the program covers three families; sentence-level counts
rather than document-level presence (the "any sentence" rule compounds
false positives across ~40 sentences); one factor per comparison; no
optimization against parameters; report emission alongside invention; the
11-item pre-recommendation checklist.

**Not executed, deliberately:** the site is stale (predates audits #1/#2,
PD-13 and the regex directive) and remains undeployed with Netlify paused.
Reconciling it is a separate pass and must not happen until the
re-measurement settles which numbers survive.

---

# CELLS 32-36 PRE-REGISTRATION BLOCK — extrinsic council advantages (registered 2026-08-09, before any runs)

## Framing and the burden of proof
Every council evaluation in this program has been INTRINSIC (scoring the
answer), and on the answer the council loses on content coverage,
calibration, load scaling and volume at ~4x compute. CollabLLM
(arXiv:2502.00640) reframes value as EXTRINSIC — the long-term contribution
of a response rather than the response itself. Its RL is infeasible here
(measured: GRPO materializes seq x vocab logits and OOMs), but the reframe
transfers without training. These five cells test the extrinsic advantages
a council could have. **The prior is that none exists**; the program's
measured record is uniformly negative, and "no advantage at any horizon we
can measure" is a registered acceptable outcome for the whole block.

**Design property shared by all five (deliberate):** none uses the
epistemic lexicon. Under the standing no-regex directive these cells
measure error propagation, attribution, rubric coverage and audit success
— constructs the entangled instrument never touched.

## Shared instrument gate — RUBRIC-COVERAGE INSTRUMENT (blocks 32, 33, 36)
Cells 32/33/36 need an answer-quality measure. Registered instrument: a
per-case rubric of CLOSED checklist items ("does the answer address X?"),
each judged independently by the two blinded judges. Closed per-item
questions are near the sentence-level granularity that validated at 0.86
agreement, and deliberately not the document-level holistic judgment that
failed at 0.62 (finding #9).
**Gate G-R:** judge-judge agreement on rubric items >= 0.75 over a >= 60-item
validation sample. If G-R fails, Cells 32/33/36 are NOT RUNNABLE and are
reported as blocked, not as null results.

---

## CELL 35 — error attribution and targeted repair (runs FIRST; no instrument gate)
**Why first:** causal by construction, needs no correctness ground truth
(the error is planted), needs no new battery, and needs no rubric — so it
is unblocked by every gate above.

**Design.** For each of the 9 cases, take the de-scaffolded seat outputs
(Cell 30's corpus) and produce an injected variant in which ONE seat's text
carries a planted, specific, checkable factual error (a wrong figure or a
reversed rule), authored per case and frozen in the harness. Arms:
- **A-inject:** council writer over the injected upstream, 3 repeats
- **A-control:** same writer over clean upstream, 3 repeats
27 + 27 runs, gpt-oss:20b, temperature 0.6.

**Measures.** (i) PROPAGATION: does the final answer assert the planted
error? Judged by both judges as a closed question naming the specific
claim, with exact string match reported as a lower bound. (ii)
ATTRIBUTION: given the answer and the three seat texts, can a judge
identify WHICH seat introduced it? (iii) CONTROL FALSE-POSITIVE rate on
A-control.

**Predictions.**
- **P35.1** Propagation rate > 0 with Wilson CI lower bound above the
  A-control false-positive rate. (Attainable: with n=27, 5+ events give a
  lower bound clear of a low control rate; 0 events gives [0, 0.12] and
  falsifies cleanly.)
- **P35.2** Attribution accuracy > 1/3 (chance among three seats), Wilson
  CI lower bound above 0.333, computed only on runs where propagation
  occurred. **Evaluability floor: >= 10 propagated runs**; below that,
  NOT EVALUABLE and reported as a design shortfall.
- **P35.3 (the comparative claim)** The same planted error injected into a
  single-model pipeline's context is attributable at chance, since no
  component boundary exists. Reported descriptively — this is close to
  definitional and is NOT scored as a test.

**Consequence.** P35.1+P35.2 supported -> localizability is the first
demonstrated council advantage, and it is extrinsic exactly as CollabLLM's
framing predicts. Either falsified -> errors propagate untraceably even
with component boundaries, and the maintainability argument for
multi-agent architectures loses its only empirical support here.

---

## CELL 34 — does provenance make auditing possible? (gated on Cell 35's injections)
**Design.** Reuses Cell 35's injected runs. Auditors (both judges,
independently) are asked whether the answer contains an unsupported or
incorrect claim, under two conditions: **with** the seat texts supplied,
and **without** (answer alone). Paired on the same runs; order randomized.

**Predictions.**
- **P34.1** Detection rate WITH sources exceeds detection WITHOUT, paired
  bootstrap CI on the difference excluding 0.
- **P34.2** False-positive rate on clean (A-control) runs does not rise
  with sources, CI including 0 or below — sources must not merely make
  auditors more suspicious.
  *Both bars checked for attainability at n=27 paired items; a difference
  below ~0.20 will not be detectable and that is stated now, not after.*

**Consequence.** P34.1 supported and P34.2 not violated -> the council's
advantage is that verification succeeds at all, which no single-model
pipeline can offer by construction. P34.1 falsified -> sources do not help
auditors, and the provenance argument is withdrawn.

---

## CELL 32 — heterogeneous error decorrelation (gated on G-R)
**Design.** Per case, two arms of three complete answers each, matched
compute: **A-hetero** (one answer each from gpt-oss:20b, phi4:14b,
qwen2.5:7b-instruct) and **A-homo** (three temperature-0.6 resamples of
gpt-oss:20b). 9 cases x 3 x 2 = 54 generations. Scored by the rubric
instrument.

**Predictions.**
- **P32.1** Within-case correlation of rubric coverage is LOWER in
  A-hetero than A-homo (ICC difference, cluster bootstrap over cases, CI
  excluding 0).
- **P32.2** Best-of-3 rubric coverage (max over the three) is higher in
  A-hetero, paired CI excluding 0. This is the practical form: diversity
  is only worth anything if the selection ceiling rises.

**Consequence.** Supported -> heterogeneous ensembles buy selection
efficiency that resampling cannot, grounding an advantage in our own
ICC=0.190 finding. Falsified -> model diversity adds nothing beyond
resampling and the ensemble rationale for councils is empirically empty.

---

## CELL 33 — inter-seat disagreement as a triage signal (gated on G-R)
**Design.** Observational, and labelled as such (no intervention). On
existing council runs with stored seat texts, compute pairwise inter-seat
disagreement (judge-scored: do these two contributions conflict on any
substantive point?) and regress rubric coverage of the final answer on it.

**Predictions.**
- **P33.1** Disagreement predicts LOWER final-answer rubric coverage,
  slope CI excluding 0.
- **P33.2 (the useful form)** Abstaining on the top-quartile-disagreement
  runs raises mean coverage of the retained set, paired CI excluding 0,
  **with retention rate reported alongside** — a rule that abstains on
  everything trivially wins and must not be scored as success (silence
  check).

**Consequence.** Supported -> the council produces a free triage signal a
single model cannot, and its value is in routing rather than writing.
Falsified -> the disagreement structure Cell 26 showed the writer ignores
is also uninformative to the system, and the tension machinery has no
demonstrated use.

---

## CELL 36 — domain factual accuracy (BLOCKED: requires a new battery)
**The gap being closed.** Across 31 cells this program measured epistemic
MARKERS exclusively and never once measured whether domain content was
CORRECT. The council's most obvious plausible advantage is the one our
instrument was blind to.

**Blocker, stated honestly:** our 18 authored cases are open-ended
professional questions without verifiable answers, which is precisely why
this was never measured. Cell 36 therefore requires constructing a battery
of >= 30 domain sub-questions with checkable ground-truth answers
(healthcare, legal, finance) whose correctness does not depend on any
judge's opinion. **That battery construction is a prerequisite deliverable
and is registered as such**; the cell does not run until it exists and its
answer key has been externally checkable.

**Prediction (frozen now).**
- **P36.1** Council answers achieve higher factual accuracy on
  domain-verifiable items than a single prompted model, paired CI
  excluding 0. *Falsified if* the CI includes 0 — domain specialization
  buys no factual accuracy either, which would remove the last untested
  rationale for the architecture.

---

## Block-level consequence
If Cells 32-35 all falsify and Cell 36 (once unblocked) falsifies, the
registered conclusion is: **the council architecture has no demonstrated
advantage over a single prompted model at any horizon this program can
measure — intrinsic or extrinsic.** That is a publishable negative result
and is accepted in advance as an outcome, not treated as a failure of the
cells.

---

### CELL 36 AMENDMENT #1 — the routing-mechanism dimension (registered 2026-08-09, before the battery exists and before any correctness has ever been measured)

**Why amend.** The original registration framed Cell 36 as "does domain
specialization buy factual accuracy?" That under-describes what the arms
actually contrast. `gpt-oss:20b` is itself a MIXTURE-OF-EXPERTS model
(~21B total parameters, ~3.6B active, learned token-level gating); every
other model in this program is dense (phi4:14b, qwen2.5:7b, mistral:7b,
and all three domain fine-tunes). The "single prompted model" arm has
therefore always been a learned expert router, and the council is a
prompted expert router across model boundaries. P36.1 is really:
**does explicit, question-granularity expert routing beat implicit,
token-granularity expert routing?** This amendment says so, and adds the
arms that make the question interpretable.

**This is an amendment, not a re-registration:** no correctness has ever
been measured in this program, on any arm, so nothing here is registered
after seeing its answer.

### Amended arms (frozen)
1. **A-council** — dense domain specialists + writer (prompted routing).
2. **A-moe-single** — gpt-oss:20b alone, prompted (learned routing).
   This is the arm the original P36.1 called "a single prompted model".
3. **A-dense-single** — phi4:14b alone, prompted (NEW; no expert routing
   of either kind). Added because without it the two-way comparison cannot
   separate "routing" from "which model".
4. **Writer-architecture sub-contrast** — council runs with gpt-oss:20b
   vs phi4:14b in the writing seat over identical upstream, which Cells
   30/31 already produce.

### Predictions
- **P36.1 (amended, primary).** A-council achieves higher item accuracy
  than A-moe-single, paired CI excluding 0. *Falsified if* the CI includes
  0 or favours A-moe-single — prompted expert routing buys no accuracy
  over learned expert routing, removing the last untested rationale for
  the architecture.
- **P36.2 (routing vs none, secondary).** A-moe-single exceeds
  A-dense-single. *Reported with the confound stated in the same sentence*:
  the two differ in architecture AND identity AND training data AND scale,
  so a difference is suggestive of routing, never demonstrative of it.
- **Reported WITHOUT a prediction (deliberate).** The writer-architecture
  sub-contrast (#4). A bar there would imply an architecture claim the
  design cannot support; it is descriptive only, exactly as the Cell 29
  dispersion indices were.

### Attainability check, performed now (P28.2 lesson)
For paired binary accuracy at n=30 items, the minimum detectable paired
difference is roughly 20 percentage points — so a real 10-15 point effect
would be invisible and the cell would report a false null. **The battery
target is therefore raised from >=30 to >=50 verifiable items**, and the
minimum detectable effect will be reported beside every verdict.

### Silence check (mandatory reporting)
Accuracy alone rewards declining to answer. **Attempt rate (fraction of
items the arm answers at all) is reported beside accuracy for every arm**,
and an arm that answers materially fewer items has its accuracy reported
as conditional, not compared directly.

### Unchanged
The battery prerequisite stands: >= 50 domain sub-questions with
checkable ground-truth answers whose correctness does not depend on a
judge's opinion. Cell 36 does not run until it exists. The lexicon is not
used anywhere in this cell.

## CELL 35 VERDICT — planted errors did NOT propagate: 0/27 by exact match and 0/17 by dual judges. The first council advantage the program has found, and it is not the one that was registered (2026-08-09, 54 runs)

Reports: bench/analysis/cell35/. Integrity verified BEFORE interpretation:
the planted text is present in the stored upstream of **27/27** injected
runs, and outputs average ~7,000 characters, so this is not a
plumbing null.

**P35.1 FALSIFIED.** Propagation 0/17 usable inject runs [0.00, 0.18];
control false-positive 0/15 [0.00, 0.20]; exact-match lower bound
**0/27**, which requires no instrument at all. Registered as
"propagation > control"; nothing propagated, so the prediction fails and
the direction is the opposite of what a maintainability worry assumes.

**P35.2 NOT EVALUABLE** at the registered floor (0 propagated runs against
a floor of 10). Attribution cannot be measured when nothing to attribute
occurs. Reported as designed, not scored.

**Propagation by error type: ARITHMETIC 0/15, RULE 0/12.** Neither kind
survived.

**Instrument defect, owned:** qwen2.5:7b-instruct returned unparseable
output on **20/52** runs (38%) while gpt-oss returned 0. The "both judges
agree" rule therefore discarded 20 runs, reducing usable n from 27/27 to
17/15. The headline does not depend on it — the exact-match lower bound is
0/27 across every run — but the judge tier is weaker than designed and the
per-judge failure asymmetry is recorded as a note on the dual-judge
protocol at this task.

**The finding, which is NOT the registered one and is reported as
post-hoc.** Checking whether the writer OMITTED the planted error or
CORRECTED it: on the arithmetic cases where the right answer is checkable,
the final answers carry the CORRECT value while never carrying the planted
one — depreciation 3/3 correct, hand-hygiene 3/3, the equity split 3/3,
and notably these often EXCEED the control arm's rate of stating the
correct figure (equity 3/3 inject vs 1/2 control; depreciation 3/3 vs
2/3). The writer did not merely drop the corrupted sentence; on
checkable arithmetic it appears to have recomputed. Stated with its
limits: n=3 per case, post-hoc, no registered bar, and the
inject-vs-control difference is far too small to test. It is a hypothesis
for a registered cell, not a result.

**What this does and does not license.** It does NOT license "councils
resist error", because a single model given the same corrupted context was
never run — the comparison arm does not exist, and P35.3 was explicitly
descriptive. What it licenses is narrower and still notable: **in this
council, a specific false claim planted in one specialist reached the
final answer zero times out of 27**, against a program-wide backdrop in
which the writer discards roughly two-thirds of what specialists supply.
The most parsimonious reading is that the same aggressive discarding that
destroys warranted qualification also destroys planted errors — the
program's central defect operating as a filter.

**Registered consequence.** Cell 34 (does provenance help auditors?)
depended on Cell 35's injected runs propagating so that auditors would
have something to detect. With 0/27 propagation there is nothing to audit
for, so **Cell 34 as registered is NOT RUNNABLE** and is recorded as
blocked-by-upstream-null rather than re-scoped to fit the data.

---

## CELL 37 PRE-REGISTRATION — does the writer RECOMPUTE, or merely prefer an uncorrupted source? (registered 2026-08-09, before any runs)

### Provenance of the hypothesis, stated plainly
Cell 35 found 0/27 propagation of planted errors, and a POST-HOC check
showed the final answers carrying the arithmetically CORRECT value on
checkable cases (depreciation 3/3, hand-hygiene 3/3, equity split 3/3),
sometimes above the control rate. The hypothesis "the writer recomputes"
was formed AFTER seeing that data. This cell tests it on NEW runs with an
arm that does not exist in Cell 35, so the hypothesis is post-hoc and the
test is prospective.

### The confound that dictates the design
Cell 35 corrupted ONE seat. In several cases the correct primitives (cost,
salvage, life; member counts; shift totals) also appear in ANOTHER seat.
So "produces the correct value" is equally consistent with three
mechanisms, and Cell 35 cannot separate them:
  (a) RECOMPUTATION — the writer derives the value from primitives;
  (b) CROSS-SEAT PREFERENCE — the writer copies from the uncorrupted seat;
  (c) PRIOR/MEMORIZATION — the writer emits a familiar textbook figure.
Any cell that does not separate these measures nothing.

### Arms (frozen) — the separation
Built on Cell 30's de-scaffolded corpus, gpt-oss:20b writer, temperature
0.6, 3 repeats per item per arm.
- **A0 clean** — no corruption (baseline rate of stating the correct value).
- **A1 single-corrupt** — one seat's figure corrupted; an uncorrupted
  source remains. (Reproduces Cell 35's condition.)
- **A2 all-corrupt** — EVERY seat mention of that figure corrupted,
  primitives intact. Copying now yields the WRONG value; only computation
  yields the right one. **This is the decisive arm.**
- **A3 all-corrupt, primitives removed** (exploratory) — the inputs needed
  to compute are deleted as well. Neither copying nor computing can
  produce the correct value; only a prior can.

### Items (frozen in the harness before any runs)
>= 8 computable arithmetic claims injected into the existing seat texts,
constructed under a frozen rule: each states its primitives explicitly,
has a single correct answer derivable in one or two steps, and uses NOVEL
numbers (not standard textbook values) to reduce memorization. Items are
committed to the repository before the runs stage executes.

### Instrument — and why it is permitted under the no-regex directive
Scored by EXACT MATCH on two known numerals: the correct value and the
corrupted value. This is not regex used as a natural-language instrument;
it is checking whether a specific known string appears, the same basis as
Cell 35's probe. **Scope limited to arithmetic items for exactly this
reason** — rule-type errors would require judged semantics and are
excluded from this cell.

### Predictions
- **P37.1 (recomputation, primary).** In A2, the CORRECT value appears
  with Wilson CI lower bound > 0, AND at a higher rate than the corrupted
  value (paired CI excluding 0). *Falsified if* the corrupted value
  dominates in A2 — the Cell 35 result was cross-seat preference, not
  recomputation, and the hypothesis dies.
  *Attainability at n=24 (8 items x 3): 3+ correct events put the Wilson
  lower bound above 0; 0 events gives [0, 0.14] and falsifies cleanly.*
- **P37.2 (not merely a prior).** A3's correct-value rate is LOWER than
  A2's, difference CI excluding 0. *Falsified if* A3 ~ A2 — the value
  comes from the model's prior rather than from computing on the supplied
  primitives, which would make "recomputation" the wrong word.
- **P37.3 (mandatory reporting, no bar).** For every arm, the THREE-WAY
  split: correct value / corrupted value / NEITHER. Silence check: an
  answer that omits the topic entirely produces neither value, and
  conflating omission with correctness would manufacture the finding.

### Consequences (fixed in advance)
- P37.1 + P37.2 supported -> the writer computes over its inputs rather
  than transporting them, which is the first POSITIVE capability this
  program has measured and stands in direct tension with the transport
  results: the same step that discards two-thirds of supplied
  qualification independently derives numerical content.
- P37.1 falsified -> Cell 35's pattern was cross-seat preference. Recorded
  as such, and the "recomputation" language is struck from all artifacts.
- P37.2 falsified -> the effect is prior-driven; the claim narrows to "the
  writer prefers its prior to a corrupted input", which is notable but is
  NOT computation.

---

## CELL IV PRE-REGISTRATION — instrument validation: does BATCHED sentence judging preserve the validated protocol? (registered 2026-08-09, before any judging)

### Why this gate exists
The no-regex directive leaves the program with exactly one validated
instrument: dual-judge SENTENCE-level labelling (Cell 23: judge-judge
agreement 0.86, anchors 0.90/0.925). Applied one sentence at a time it
costs ~4,800 calls for a single 60-run corpus, which is not viable for the
~1,800-run archive. Batching is the only route to affordability, and
Cell 30 proved that changing the granularity of a judging protocol can
destroy it (0.86 per sentence -> 0.62 per document). Batching must
therefore be validated, not assumed.

### Design (frozen)
Sentences are presented ISOLATED and numbered, several per call — the
judgment unit stays a single sentence; only the call packaging changes.
Two batch sizes tested in the same run to give a degradation curve:
**B=5 and B=10**. Both judges (gpt-oss:20b, qwen2.5:7b-instruct),
temperature 0, frozen Cell 23 definitions verbatim.

**Materials:** the 200 agreement-filtered Cell 23 sample sentences
(consistency reference) and the 20 hand-written anchors with known truth
(validity reference). Cutoff is EXCLUDED from scoring per the standing
directive: 3 positives cannot support a rate.

### Predictions — all three must pass for the protocol to ship
- **P-IV.1 (consistency).** Batched labels agree with the frozen
  single-sentence labels at >= 0.80 per family, on modeled / jurisd /
  hedging.
- **P-IV.2 (validity).** Anchor accuracy >= 0.80 for BOTH judges, against
  the unbatched baseline of 0.90 / 0.925.
- **P-IV.3 (usability).** Parse-failure rate < 20% per judge. Included
  because Cell 35 measured qwen2.5 at 38% unparseable against gpt-oss's
  0%, and batching lengthens the required output — the most likely way
  this protocol fails is mechanical, not epistemic.

### Consequences (fixed in advance)
- All pass at B=10 -> B=10 ships as the program's measurement instrument;
  the held measurements (Cells 30, 31, and the archive) unblock.
- Pass at B=5 only -> B=5 ships, at double the cost.
- P-IV.3 fails for one judge only -> that judge is replaced and the
  protocol re-validated; a 38%-failure judge is not a second instrument.
- Any epistemic bar fails at both sizes -> batching is rejected, the
  program's only affordable instrument does not exist, and the
  re-measurement is reported as BLOCKED rather than approximated.

## CELL IV VERDICT — BATCHED JUDGING VALIDATES AT B=10. The program has a working instrument again (2026-08-09)

Report: bench/analysis/cellIV/report.txt.

| bar | B=5 | B=10 | requirement |
|---|---|---|---|
| consistency, modeled | 0.910 | **0.908** | >= 0.80 |
| consistency, jurisd | 0.921 | **0.945** | >= 0.80 |
| consistency, hedging | 0.865 | **0.835** | >= 0.80 |
| anchors, gpt-oss | 0.925 | **0.900** | >= 0.80 |
| anchors, qwen2.5 | 0.975 | **0.938** | >= 0.80 |
| parse failure, gpt-oss | 0.038 | **0.000** | < 0.20 |
| parse failure, qwen2.5 | 0.115 | **0.000** | < 0.20 |

**Both sizes PASS ALL BARS. Registered consequence executed: B=10 ships**
(largest passing size).

Three observations recorded:
1. **Batching did not degrade validity.** Anchor accuracy at B=10
   (0.900 / 0.938) matches or exceeds the unbatched Cell 23 baseline
   (0.900 / 0.925). The concern that motivated this gate — granularity
   collapse, as in Cell 30's 0.86 -> 0.62 — did not materialise when the
   judgment UNIT was held at one sentence and only the packaging changed.
   That distinction is the transferable lesson: Cell 30 changed the unit;
   this changed the envelope.
2. **Parse failures fell to zero at the larger size**, including for the
   judge that failed 38% of Cell 35's document-level calls. Small n
   (13 batches) so not over-read, but the mechanical bar that seemed most
   likely to fail did not.
3. **Hedging is the weakest channel again** (0.835, lowest at both sizes),
   consistent with hedging being diffuse under regex, NLI, and judges
   alike — now four instruments agreeing that this construct is hard.

**Cost effect:** ~10x reduction. The ~1,800-run archive re-measurement
moves from infeasible to an overnight job, and the held measurements
(Cells 30, 31) unblock immediately.

**Measurement definition, per the standing directive:** the shipped
measure is the COUNT of qualification-bearing sentences per family, not
document-level binary presence. "Any sentence positive" compounds false
positives across ~40 sentences; counts add error linearly.

### CELL 31 — REGISTERED DEVIATION, before any measurement (2026-08-09)

Cell 31 was registered with regex as its instrument ("stated as a
limitation up front"). A standing directive issued AFTER that registration
bars regex as an instrument, and Cell IV has since validated batched
sentence judging at B=10. The measurement is therefore taken with the
validated instrument instead. Recorded before any numbers are computed.

**What changes:** the measured variable. Registered as family counts
(0-4 per document); now the COUNT OF QUALIFICATION-BEARING SENTENCES,
per the standing directive that "any sentence positive" compounds false
positives across a document.

**What that does to the frozen predictions:** the scale changes, so the
registered bars survive only as SIGN tests, and are read that way:
- **P31.1** Delta-c (ledger minus plain) cluster-bootstrap CI entirely
  below 0.
- **P31.2** Delta-w CI includes 0 or lies above it.
The paired cluster-bootstrap estimator over shared variants is unchanged,
as is the population and seed.

**Scope:** 20 shared variant upstreams, 60 Cell 30 outputs, 51 Cell 31
outputs (9 protocol violations excluded as registered) = 2,339 sentences,
234 batches, 468 judge calls. Sentences are batched GLOBALLY across
documents, which is exactly the condition Cell IV validated (200 unrelated
sentences, judged independently).

## CELL 31 VERDICT — the ledger's c->0 finding is WITHDRAWN. It was clause removal, not the ledger (2026-08-10, first measurement in this program produced by an instrument that passed a registered validation gate)

Report: bench/analysis/c30c31/report.txt. Instrument: Cell IV-validated
batched sentence judging, B=10, both judges, both-agree rule. 468 calls,
44 unparseable (9.4%), 440 sentence-labels unusable and counted rather
than dropped silently.

**P31.1 FALSIFIED.** Delta-c = +0.182 [-0.868, +1.261] — the interval
includes zero, and the point estimate is POSITIVE (the ledger arm's
intercept is higher, not lower). Registered consequence executes as
written: **the Cell 27/28 c->0 finding is WITHDRAWN from the program's
claims.** What replaces it is the already-measured and more useful fact
that the PRESERVE clause causes the invention it was written to prevent
(c = 0.799 with the clause vs 0.162 without, disjoint).

**P31.2 SUPPORTED.** Delta-w = +0.034 [-0.151, +0.193] — the ledger does
not buy its intercept by suppressing transport. Under the old regex
measurement this arm looked like it might be the silence route; under the
validated instrument it is not. The prediction that guarded against the
degenerate explanation passes, and the degenerate explanation is not what
happened — the effect simply is not there.

**Arm-level figures.** Plain w=0.150 c=+0.441; ledger w=0.183 c=+0.623.
Mean supply is matched by construction (5.40 vs 5.37 sentences) and the
ledger arm emits MORE qualification-bearing sentences (1.61 vs 1.25), not
fewer — which also retires the "ledger suppresses emission" reading that
the regex measurement supported.

**Why the earlier result inverted.** Cells 27/28 compared a ledger arm
against arch-council, which still carried the PRESERVE clause, and scored
both with a lexicon whose strings that clause dictates. Removing the
clause removed the dictated phrases; the lexicon read that as c -> 0. With
the clause absent from BOTH arms and a paraphrase-robust instrument, the
ledger's own contribution is indistinguishable from nothing. Two defects
compounding — a two-factor baseline and an entangled instrument — produced
a replicated finding that was an artifact of both.

**Caveat recorded honestly:** the delta-c interval is very wide
([-0.87, +1.26] on 20 clustered variants), so this is a failure to
demonstrate rather than a demonstration of absence. The registered
consequence is withdrawal either way — an undemonstrated mechanism does
not enter the papers — but a future adequately-powered test could still
find an effect, and that possibility is not excluded here.

**Consequences executed:** STATUS.md updated (register-dependent intercept
moves from PROVISIONAL to WITHDRAWN as a ledger claim); the framework
paper's phenomena section loses its ledger evidence; Cell 37's premise is
unaffected (it concerns recomputation, not the intercept).

## CELL 30 VERDICT — the law SURVIVES de-scaffolding: w = 0.150 [0.058, 0.252], measured with no lexicon anywhere in the system or the instrument (2026-08-10)

Report: bench/analysis/c30c31/law_report.txt. Same registered deviation as
Cell 31 (instrument -> Cell IV batched sentence judging; measured variable
-> counts of qualification-bearing sentences; frozen bars read as sign
tests).

**P30.0 PASS — the gate that failed now passes.** Judge-judge agreement on
this exact corpus is **0.833** (4,746/5,697 scored-family decisions)
against the 0.70 bar. The same two judges on the same 60 documents scored
**0.622 at document level** and failed. The only change is the judgment
unit. Finding #9 is now demonstrated on a single corpus with everything
else held: **granularity, not judge quality, was the failure.**

**P30.1 SUPPORTED — and this is the program's most important surviving
positive claim.** With de-scaffolded seat prompts containing no family
name and no dictated phrasing, and a paraphrase-robust instrument sharing
no vocabulary with anything in the system: **w = 0.150 [0.058, 0.252]**,
CI excluding zero. Supply spans 11 distinct levels over 60 runs. The
supply-response relationship is real, not a scaffold artifact. It is also
small: the writer carries roughly one qualification-bearing sentence for
every seven supplied.

**P30.2 NOT EVALUABLE — and the reason is a methodological finding.** Only
**3** zero-supply runs exist against the ~36 the registration expected.
The ablation that built the variants was regex-driven, and under the
validated instrument those "zero-supply" texts still average 5.4
qualification-bearing sentences. **Regex ablation does not produce
zero-supply text; it produces text with the regex-visible phrases
removed.** Consequences: (a) P30.2 cannot be scored and is reported as a
design failure, not a null; (b) the same critique applies to the supply
manipulation in Cells 25, 27, 30 and 31 — their "s=0" strata were never
zero under a valid instrument, so every zero-supply invention rate this
program has published is measuring something other than what it claims.
Recorded as **instrument-validity finding #10: construction blind spots
propagate into the design**, distinct from #8 (measurement entanglement).

**P30.3 PARTIAL.** gpt-oss w = 0.172 [0.053, 0.298] excludes zero; phi4
w = 0.105 [-0.028, 0.282] does not. The law is demonstrated on one writer
and not demonstrated on the second — at n=20 for phi4 this is a power
limit rather than a contradiction, but the registered conjunction fails
and the honest statement is that **the law is established for one writer
model**. The zero-supply half of P30.3 is unavailable per P30.2.

**P30.4 SUPPORTED, dramatically.** Regex sees an invention/emission rate
of **0.083**; the validated instrument sees **0.633** on the same 60
documents — a 7.6x undercount once the scaffold phrasings are absent. The
lexicon was never measuring the behavior; it was measuring the phrases the
scaffold dictated, and with the scaffold gone it goes nearly blind. This
is the quantitative form of finding #8 and it retrospectively bounds every
regex rate in the program.

**Net.** The central phenomenon survives the audit's worst charge: a
supply-response exists with no lexicon anywhere in the loop. Its magnitude
is small, it is demonstrated on one writer, and the compensating-invention
half of the story is now unmeasured rather than measured — the design that
was supposed to test it never created the condition it required.

---

## CELL 38 PRE-REGISTRATION — judge-driven ablation: does compensating invention exist at TRUE zero supply? (registered 2026-08-10, before any runs)

### Why
Finding #10: regex-driven ablation left an average of 5.4
qualification-bearing sentences in texts labelled zero-supply, so every
zero-supply invention rate this program has published was computed on a
stratum that was never zero. The claim "writers invent qualification when
none is supplied" — the program's most striking result — is currently
UNMEASURED. This cell builds the condition properly.

### Design (frozen)
Source: Cell 30's de-scaffolded seat texts (no family names, no dictated
phrasing anywhere).
1. **Judge** every sentence of the full seat texts with the Cell
   IV-validated instrument (B=10, both judges, both-agree rule).
2. **Ablate** every sentence both judges flag for any scored family
   (modeled / jurisd / hedging; cutoff excluded per standing directive).
3. **RE-JUDGE the ablated upstream.** Supply is CONFIRMED, never assumed —
   this is the step whose absence produced finding #10.
4. **Run** the writer (gpt-oss:20b, temperature 0.6, neutral de-scaffolded
   prompt) on two arms: **A-full** (unablated control) and **A-zero**
   (judge-ablated), 9 cases x 3 repeats each = 54 runs.
5. **Judge** the outputs; measure qualification-bearing sentence counts.

### The circularity, and why this design is not it
Ablation and measurement use the same instrument. That is acceptable here
and would not be in general: it makes supply zero BY THAT INSTRUMENT'S
LIGHTS, which is exactly the condition the claim is about ("the writer
emits qualification the instrument cannot source upstream"). What would be
circular is assuming the ablation worked; step 3 measures it instead.
Residual limitation recorded now: judge false negatives leave residue, so
A-zero is "confirmed near-zero", and the confirmed value is reported rather
than asserted.

### Predictions
- **P38.1 (the ablation works).** Re-judged A-zero upstream carries <= 1
  qualification-bearing sentence in >= 7 of 9 cases. *Falsified if* not —
  which would mean judge-driven ablation ALSO fails to create the
  condition, generalizing finding #10 to every instrument we have and
  making true-zero-supply unreachable by ablation. Reported as such, not
  as a null on invention.
- **P38.2 (invention at true zero supply).** Among A-zero runs whose
  upstream is confirmed at 0, the fraction whose output contains >= 1
  qualification-bearing sentence has Wilson CI lower bound > 0.
  *Falsified if* the CI includes 0 — compensating invention does not
  survive proper measurement, and the program's most striking claim is
  withdrawn. *Attainability at n=27: 3+ events clear zero; 0 events gives
  [0, 0.12] and falsifies cleanly.*
- **P38.3 (silence check, MANDATORY REPORTING, no bar).** Output character
  length and total sentence count for both arms. If A-zero outputs are
  materially shorter, the invention rate is reported as CONDITIONAL on
  output length — "no invention" must not be an artifact of "no output".

### Consequences (fixed in advance)
- P38.1 + P38.2 supported -> compensating invention is real at true zero
  supply, measured with no lexicon anywhere, and returns to the LIVE
  claims with this cell as its evidence.
- P38.2 falsified -> the claim is WITHDRAWN. Combined with Cell 30's
  surviving w = 0.150, the thesis narrows to "weak transport" with no
  invention component.
- P38.1 falsified -> true zero supply is unreachable by ablation with any
  instrument we have; the question is reported BLOCKED and requires
  synthetic upstream authored to contain no qualification.

---

## CELL 39 PRE-REGISTRATION — is the error filtering a COUNCIL property or a WRITER-ARCHITECTURE property? (registered 2026-08-10, before any runs)

### The gap this closes
Cell 35 found 0/27 propagation of planted errors and attributed it to the
council's aggressive discarding. But Cell 35 used ONLY gpt-oss:20b as the
writer, which is itself a mixture-of-experts model (~21B total, ~3.6B
active, learned token-level gating). Every other model in this program is
dense. The filtering may therefore be a property of that WRITER's
architecture rather than of the council arrangement, and the program has
no data separating the two.

Framing note, recorded because it constrains what this cell can claim: an
MoE's experts emit activations, not text, so planting an error in one, or
attributing an output error back to one, is UNDEFINED rather than merely
harder. This cell does not compare "council verifiability" against "MoE
verifiability" — that comparison has no measurable quantity on one side.
It compares WRITERS at the same task.

### Design (frozen) — one factor
Identical to Cell 35 in every respect except the writing model:
- Same nine planted errors, frozen verbatim in run_cell35_injection.py
  (five arithmetic, four reversed rules), same seat, same injection point.
- Same Cell 30 de-scaffolded upstream, same neutral writer prompt, same
  temperature 0.6, same 3 repeats per case per arm.
- **A-inject-dense / A-control-dense:** phi4:14b (dense), 27 + 27 runs.
- **Comparison arm:** Cell 35's existing gpt-oss (MoE) runs, NOT re-run.
- Scored by the Cell 35 protocol: propagation as a closed dual-judge
  question with a required verbatim quote, plus exact-match on the probe
  string as an instrument-free lower bound. No lexicon anywhere.

### The confound, stated up front
gpt-oss and phi4 differ in architecture AND identity AND training data AND
scale (21B/3.6B-active vs 14B dense). A difference is therefore SUGGESTIVE
of an architectural cause and never demonstrative of one. This is recorded
now so it cannot be quietly dropped from the verdict, and it is the same
limitation registered for Cell 36's routing dimension.

### Predictions
- **P39.1 (the decisive one).** Dense-writer propagation exceeds the MoE
  writer's 0/27, with the Wilson CI lower bound above the MoE arm's upper
  bound (0.184). *Supported* -> the filtering is writer-dependent and
  Cell 35's result must be re-attributed from "the council discards" to
  "this writer filters"; the council interpretation is withdrawn.
  *Falsified* -> both architectures filter, and the discarding
  interpretation stands with a second writer behind it.
  *Attainability at n=27: 8+ propagated runs clear 0.184; 0 events gives
  [0, 0.12] and falsifies cleanly. A difference below ~5 events is not
  detectable and that is stated now.*
- **P39.2 (control).** Dense-writer false-positive rate on clean upstream
  does not exceed the MoE arm's 0/15. Reported with its Wilson interval;
  a dense arm that "detects" the claim on clean input invalidates its own
  propagation numbers.
- **P39.3 (mandatory reporting, no bar).** Mean output length and the
  three-way split correct-value / corrupted-value / neither on the five
  arithmetic items. Silence check: a writer that omits the topic produces
  neither value, and conflating omission with filtering would manufacture
  the finding — this is exactly how a false null would enter.

### Consequences (fixed in advance)
- P39.1 supported -> the first architecture-level result in the program,
  reported with the confound in the same sentence, and Cell 35's
  attribution corrected in STATUS.md.
- P39.1 falsified -> Cell 35's filtering result gains a second writer and
  strengthens; "the council discards planted errors" becomes a two-writer
  finding rather than a one-writer one.
- Either way, no configuration is adopted.

### CELL 36 AMENDMENT #2 — the verifiable battery is BUILT; scope narrowed and stated (2026-08-10, before any Cell 36 runs)

**Delivered:** examples/verifiable_battery.py — 60 items, 20 per domain
(healthcare / legal / finance), self-verifying. Every item carries an
executable derivation and `verify_battery()` asserts derivation == stated
answer for all 60. **Result: 60/60 confirmed, 0 authoring errors.**
Difficulty spread: 36 single-step, 21 two-step, 3 three-step.

**The design constraint, and it narrows the cell.** Program audit #2
recorded a fabrication defect — an illustrative example reaching a paper
as data. I therefore did NOT author domain FACTS from memory (statutes,
dosing tables, market rates); every item states its premises IN THE
QUESTION so the answer is derivable from those premises alone. Ground
truth is checkable by any reader with no authority, no judge, and no
trust in the author. That is the strongest form of verifiability
available and it is why the battery clears the "correctness does not
depend on a judge's opinion" requirement absolutely.

**What the battery therefore measures — stated now, not after results:**
domain-FRAMED REASONING (does the model apply a domain convention
correctly: unit handling, tolling, day-count, book-value floors, ratio
conventions). **What it does NOT measure: domain RECALL.** A recall
battery requires externally sourced facts and must not be authored
unaided; it is registered here as a SEPARATE prerequisite and is not
smuggled into this one.

**Consequence for P36.1's interpretation.** The prediction stands as
registered, but its reading narrows: a council advantage on this battery
would demonstrate better domain-convention application, NOT better domain
knowledge. If the domain seats' value is recall — which is what their
model cards actually claim gains on (Med42 on MedQA/MedMCQA, Saul at ~6%
over Mistral-7B on LegalBench, both MCQA-format) — this battery will not
detect it, and a null here must NOT be reported as "domain specialization
buys no accuracy". It licenses only: "domain specialization buys no
advantage in applying domain conventions to stated premises."

**Attainability re-checked with the built battery:** 60 items exceeds the
>=50 target set by amendment #1, giving margin for items dropped at
scoring. Scoring is exact match against per-item accepted forms — a known
value check, not regex-as-NLP, the same basis as Cell 35's probe.

## CELL 39 VERDICT — the filtering is NOT the MoE writer's doing. Both architectures reject planted errors completely (2026-08-10, 54 dense runs against Cell 35's 54 MoE runs)

Report: bench/analysis/cell39/report.txt.

**P39.1 FALSIFIED.** Dense propagation 0/11 usable [0.000, 0.259] against
the MoE's 0/17 [0.000, 0.184]; exact-match **0/27 in BOTH arms**, which
requires no instrument at all. Nine planted claims, five arithmetic and
four reversed rules, reached the final answer zero times under either
writer architecture.

**P39.2 ok.** Dense control false-positive 0/13 [0.000, 0.228] — the dense
arm does not "detect" the claim on clean input, so its propagation numbers
are not inflated by a jumpy judge.

**Consequence executed as registered:** Cell 35's attribution STANDS and
strengthens. The filtering is not a property of the MoE writer; it is
reproduced by a dense model of different family, training data and scale.
"Planted errors do not reach the final answer" is now a TWO-WRITER
finding rather than a one-writer one. The confound registered in advance
(architecture AND identity AND training data AND scale differ) cuts in the
program's favour here: two models sharing none of those properties behave
identically, which is stronger evidence for a task-level explanation than
either arm alone.

**P39.3, the reason this is not a clean win.** The two writers filter
equally but do NOT behave equally. On the five arithmetic items where the
correct value is checkable: MoE **correct=10, corrupted=0, neither=5**;
dense **correct=6, corrupted=0, neither=9**. The dense arm produces
outputs roughly half as long (4,264 vs 8,227 chars) and omits the relevant
quantity nearly twice as often. **Neither writer ever reproduced a
corrupted value — but the dense writer more often said nothing at all.**
This is exactly the silence confound the mandatory reporting exists to
expose: filtering and omission are not the same behaviour, and a
propagation rate alone cannot distinguish them.

**Net.** Error rejection is robust across writer architectures. Whether it
is genuine correction or aggressive discarding remains open, and Cell 37
(registered, not run) is the test that separates them.

## CELL 38 VERDICT — invention at TRUE zero supply is REAL: 4/12 [0.138, 0.609]. The program's most striking claim survives proper measurement (2026-08-10)

Report: bench/analysis/cell38/report.txt.

**P38.1 FALSIFIED — and the failure is a finding.** Judge-driven ablation
reached <=1 remaining qualification sentence in only 6/9 cases against a
bar of 7. Per-case residue: four cases at exactly 0, two at 1, one at 3,
two at **4**. Ablation is NOT idempotent — removing the sentences a judge
flags produces a NEW text in which the judges then flag sentences they
previously passed. Context shifts: a line that reads as neutral beside an
explicit caveat reads as hedging once the caveat is gone. This is not
judge unreliability (agreement on this corpus is 0.833); it is a property
of the construct. **Finding #10 generalises: no instrument we have can
reach true zero supply by ablation.** The registered route remains
upstream AUTHORED to contain no qualification.

**P38.2 SUPPORTED — on the four cases confirmed at EXACTLY zero.**
Invention 4/12 = 0.333 [0.138, 0.609], Wilson lower bound above zero. The
confirmation step is what makes this the first defensible zero-supply
measurement in the program: every previous one was computed on strata that
were never zero. Restricting to confirmed-zero cases is why n is 12 rather
than 27, and the registered floor of 8 is cleared.

**P38.3 — the caveat that must travel with the number.** A-zero outputs
are shorter than A-full (5,273 vs 7,873 chars; 9.1 vs 13.2 sentences) and
carry less qualification overall (0.58 vs 1.67 sentences). So the writer
given nothing says less — but it does not say NOTHING, and in a third of
runs it supplies qualification with no upstream source whatever. The rate
is conditional on output length and is reported that way.

**Consequence executed.** Compensating invention returns to the LIVE
claims with this cell as its evidence, replacing the withdrawn
regex-stratum version. STATUS.md updated. The claim is now: measured with
no lexicon anywhere, on upstream confirmed free of qualification by a
validated instrument, a writer invents qualification in a third of runs.

## CELL 36 VERDICT — P36.1 FALSIFIED. The council buys no accuracy, and the ceiling effect means this battery could not have shown much either way (2026-08-10, 179 runs over 60 verifiable items)

Report: bench/analysis/cell36/report.txt.

| arm | accuracy | attempt rate | fallbacks |
|---|---|---|---|
| council (correct specialist + writer) | 56/60 = 0.933 [0.841, 0.974] | 0.983 | 0 |
| MoE-single (gpt-oss:20b) | 57/59 = 0.966 [0.885, 0.991] | 0.983 | 0 |
| dense-single (phi4:14b) | 55/60 = 0.917 [0.819, 0.964] | 1.000 | 0 |

**P36.1 FALSIFIED.** Council minus MoE-single: paired diff CI
[-0.085, +0.034] over 59 shared items — includes zero, point estimate
NEGATIVE. Adding a domain specialist and a synthesis step to a single
model produced no accuracy gain, and the council arm was given the
CORRECT specialist with no planner, which was the most favourable
construction available to it. The registered consequence executes: the
last untested rationale for the architecture is removed on this
dimension.

**P36.2 (confounded, as registered).** MoE minus dense: [-0.034, +0.102],
includes zero. No routing-mechanism difference detectable, and the arms
differ in architecture AND identity AND training data AND scale, so this
was never going to demonstrate an architectural cause.

**The limitation that bounds all of the above, stated plainly: a CEILING
EFFECT.** All three arms score 0.92-0.97. With 60 items and accuracy that
high, the design can only detect very large differences; the observed
intervals are ~±0.09 wide, and no plausible council advantage of 3-5
points could have been resolved. **This is a weak null, not a strong
one.** The attainability check in amendment #1 sized the battery for a
20-point difference and got one that can resolve roughly that — but it
did not anticipate that every arm would sit near the ceiling, which
compresses the resolvable range further. Recorded as a design shortfall
found after the fact, in the same class as the Cell 28 bar defect.

**Attempt rates are uniformly high** (0.98-1.00) and full-text fallbacks
are zero, so the silence check finds nothing: no arm is scoring well by
declining to answer, and every arm produced the required ANSWER line
essentially always. That part of the design worked.

**Interpretive scope, per amendment #2 and unchanged:** this battery
measures domain-FRAMED REASONING — applying stated conventions to stated
premises — NOT domain recall, which is what the seats' model cards claim
gains on. The verdict licenses "domain specialization buys no advantage
applying domain conventions to stated premises" and NOT "domain
specialization buys no accuracy".

**Consequence for the next cell:** a recall battery, or a harder
reasoning battery that moves the arms off the ceiling, is now the
prerequisite for any stronger claim. Registered as an open item rather
than attempted here.

---

## CELL 40 PRE-REGISTRATION — can a SEAT instruct the lead? (registered 2026-08-10, before any runs)

### The gap, verified
Every instruction the writer has received in 39 cells came from the SYSTEM
DESIGNER: the PRESERVE block, the suppression clause, the DECIDE clause,
the ledger protocol. Inspection of council/prompts.py confirms the seat
prompts ask seats to ANSWER the Lead's question and never to instruct it.
No cell has tested whether the component that owns the knowledge can tell
the component that writes how to use it.

### Why it is worth running despite five discouraging results
Cells 17, 20, 26, 27/28 and PD-13 all found the writer unmoved by
instruction. But PD-13's actual finding was that an instruction reliably
produces THE SPECIFIC THING IT NAMES (0/30 -> 28/30 on dictated
phrasings); the failure was that generic instructions name nothing
specific. A seat directive differs on two axes never varied here:
SPECIFICITY (it names a particular claim, not a class) and
AUTHORSHIP/POSITION (it arrives in the content position, written by the
model that produced the content, only when the case warrants it). Our own
strongest instrument finding therefore predicts the specific case might
land where the generic case did not.

It also supplies what Cell 26 showed missing: in every prior test the
reliability signal was computed by the harness or tabulated by the writer,
never ASSERTED by the seat that owns it.

### Primary experiment — DEFERENCE (the routing-authority form)
Two seats state CONFLICTING figures for the same quantity (nine items,
reusing the Cell 37 claim set). Arms, 3 repeats each:
- **A-control** — conflict present, no directive.
- **A-defer-to-B** — seat A appends: its figure is the weaker estimate and
  where it conflicts with seat B's, seat B's should be used.
- **A-defer-to-A** — the mirror, issued by seat B.
Measured by exact match on the two known numerals. Instrument-free.

**The counterbalance is the internal validity check**: if the two defer
arms shift in OPPOSITE directions, the directive is doing the work; if
both shift the same way, it is position bias and the cell reports that
instead.

### Secondary experiment — PRESERVATION (runs only if the primary completes)
Same nine cases. A seat states a caveat, in one arm accompanied by a
directive to carry it into the answer. Measured by exact match on a
distinctive caveat phrase.

### Entanglement guard (finding #8, mandatory)
Directive text must contain NO lexicon family vocabulary. Verified
mechanically against the lexicon before any run; the harness refuses to
run on violation. Without this, the directive and the instrument would
share vocabulary and the cell would measure compliance with itself —
exactly the defect that cost this program a month.

### Predictions
- **P40.1 (deference lands).** Each defer arm shifts figure choice toward
  its named target, paired bootstrap CI on the difference from control
  excluding 0. *Falsified if* either CI includes 0.
  *Attainability at n=27/arm: a ~30-point shift is resolvable; smaller is
  not, and that is stated now.*
- **P40.2 (it is deference, not position).** The two defer arms shift in
  OPPOSITE directions. *Falsified if* they move the same way — reported as
  position bias, and P40.1 is void regardless of its own interval.
- **P40.3 (preservation, secondary).** The carry-this directive raises the
  caveat's appearance versus the same caveat undirected, CI excluding 0.
- **P40.4 (mandatory reporting, no bar).** Output length and the rate at
  which NEITHER figure appears — omission is not compliance, and a
  directive that makes the writer drop the topic entirely would otherwise
  read as success.

### Consequences (fixed in advance)
- P40.1 + P40.2 supported -> the first mechanism in this program where the
  SOURCE rather than the DESIGNER controls synthesis. The instruction
  question reopens with specificity and authorship as the live variables,
  and the withdrawn instruction-gain contribution gets a successor claim
  that is narrower and better evidenced.
- P40.1 falsified -> the writer ignores handling instructions regardless of
  who authors them or how specific they are. That CLOSES the instruction
  question rather than leaving the specificity loophole open, and is the
  stronger negative result.
- No configuration is adopted either way.

## CELL 37 VERDICT — the writer does NOT recompute. "Recomputation" is struck from every artifact, and the corrupted value wins whenever no clean source exists (2026-08-10, 108 runs, four arms)

Report: bench/analysis/cell37/report.txt.

| arm | n | correct | corrupted | neither |
|---|---|---|---|---|
| clean (all seats correct) | 27 | 6 | 1 | 20 |
| one-corrupt (Cell 35's condition) | 27 | 4 | 0 | 23 |
| **all-corrupt** (primitives intact) | 27 | **2** | **5** | 20 |
| stripped (primitives deleted) | 27 | **0** | **12** | 15 |

**P37.1 FALSIFIED.** In the decisive arm — every seat corrupted, primitives
intact, so copying yields the wrong value and only computation yields the
right one — the writer produced the correct value 2/27 and the CORRUPTED
value 5/27. Correct-minus-corrupted CI [−0.296, +0.074]. It did not
compute. **Registered consequence executed: the word "recomputation" is
struck from all artifacts**, and Cell 35's pattern is re-attributed to
CROSS-SEAT PREFERENCE — the writer took the correct figure from an
uncorrupted seat when one existed, which is copying, not deriving.

**P37.2 FALSIFIED, and it removes the fallback reading too.** With the
primitives deleted the correct value never appears (0/27) while the
corrupted value appears 12/27 — more than double the all-corrupt rate.
The diff CI [−0.185, +0.000] touches zero at the boundary, so the
prior-driven claim is not established either. The writer has no
independent access to these answers: strip the inputs and it simply
repeats whatever it was told.

**The gradient is the finding.** Corrupted-value adoption rises
monotonically as clean alternatives are removed: 1 → 0 → 5 → 12 across
clean, one-corrupt, all-corrupt, stripped. The writer is a SOURCE
SELECTOR, not a calculator. When a clean source exists it prefers it —
which is genuinely useful and explains Cell 35's 0/27 propagation — but
when every source is wrong it propagates the error, and when the working
is removed it propagates it twice as often.

**Cell 35's headline is therefore narrowed, not withdrawn.** "Planted
errors do not reach the final answer" holds ONLY where an uncorrupted seat
covers the same quantity. Cell 35 corrupted one seat of three; that is the
protected case. Cells 35 and 39 measured redundancy, not resistance.

**P37.3, the reason this is readable at all.** "Neither value present"
runs at 15-23 of 27 in every arm — the writer omits these quantities far
more often than it states them. Rates are conditional on that, and without
the mandatory three-way split the 2/27 correct in the decisive arm could
have been reported as a small positive rather than as what it is.

**Net for the program.** The one apparent POSITIVE capability measured in
39 cells does not survive its own registered test. What remains is a
weaker and more precise claim: the writer prefers uncorrupted sources over
corrupted ones when both are present, and has no independent hold on the
content whatsoever.

---

## CELL 40 VERDICT — NOT EVALUABLE (measured 2026-08-11)

**All 81 runs completed. The primary is not decidable, and the reason is a
design defect in the injection, not a property of the writer.**

### The three-way table (P40.4 mandatory reporting)

| arm | n | seat-1 value only | seat-2 value only | both | NEITHER |
|---|---|---|---|---|---|
| control | 27 | 2 | 1 | 0 | 24 |
| defer-to-2 | 27 | 5 | 1 | 0 | 21 |
| defer-to-1 | 27 | 2 | 0 | 0 | 25 |

Decisive runs — the denominator the estimand is defined on — number 3, 6
and 2. The registered guard requires >= 6 decisive runs in BOTH arms of a
comparison; control has 3. **No comparison is computable, so P40.1 and
P40.2 are NOT EVALUABLE.** Neither is falsified. Nothing in this cell
licenses "a seat cannot instruct the lead."

**The P40.4 guard is what made this readable.** Taken alone, defer-to-2's
5-vs-1 split looks like textbook compliance. It is 6 events. Without the
mandatory NEITHER column this cell would have been written up as a
supported directive effect.

### Why the outcome almost never fired — diagnosed, not speculated

Decisive rates are uniformly low across all nine items (0/9, 1/9, 2/9,
1/9, 2/9, 0/9, 1/9, 2/9, 2/9). Not one bad item: the whole design.

Inspection of item 0 gives the mechanism. Its injected premises state a
**$66,000 asset with $6,000 salvage**; the host case (`case_10`) states a
**$60,000 asset with $10,000 salvage**. In **9 of 9** Cell 40 runs — and
**12 of 12** Cell 37 runs — the writer used the CASE's numbers and the
injected numbers **zero** times. Items 6 (12 vs 18 months) and 7 (1,200 vs
5,000 employees) carry the same contradiction.

The manipulation was outcompeted by the question itself. The seats were
never the only sources in the room: the case prompt was a third source,
unregistered, carrying more authority than an appended aside.

### FINDING #11 — an injected premise that contradicts its host question
### is not a manipulation of the source; it creates a competing source

Generalises finding #10. The injection satisfied its own registered rule
(each item "states its primitives explicitly" and uses "NOVEL numbers ...
to reduce memorization") and still failed, because **the novelty rule and
coherence with the host question are in direct conflict and no
registration reconciled them.** Choosing numbers unlike the case's is the
same act as choosing numbers that contradict the case's.

Traceable: Cell 37's item 0 was changed from $10,000 salvage precisely to
fix a probe collision. That fix created this defect. Ablation is not
idempotent (finding #10) — and neither is repair.

### Consequence for Cell 37 — the verdict stands, its rates do not

- **P37.1 FALSIFIED — SURVIVES.** Its falsification condition is
  "the corrupted value dominates in A2," a WITHIN-arm contrast (5 corrupted
  vs 2 correct) that base-rate depression cannot manufacture. The monotone
  gradient 1 → 0 → 5 → 12 is likewise within-instrument. **"Recomputation"
  stays withdrawn; the source-selector reading stands.**
- **P37.2 — downgraded from FALSIFIED to NOT EVALUABLE.** A3=0 and A2=2
  correct out of 27 are both at floor. The registration carried an
  attainability note for P37.1 and none for P37.2; it had no power to
  distinguish "not a prior" from "nothing fired."
- **The "neither" cells were mis-described.** The Cell 37 write-up reads
  them as the writer omitting the quantity. On at least three of nine items
  the writer was answering the case's real question with the case's real
  numbers. That is engagement with a different source, not omission.

### What a valid re-run requires (registered here, NOT run)

Injected premises must be **drawn from the host case, not invented against
it** — the manipulation may change which SEAT states a quantity and what
value it states, never the premises the question itself supplies. The
attainability check must be run on the OUTCOME (does the writer state this
quantity at all?) before the arms are built, not after. Both are pre-run
conditions; no re-run is registered until they are met.

---

## DICTATION REGISTRY + PARAPHRASE MATCHER — PRE-REGISTRATION (2026-08-11, before any scoring)

Layers 1-2 of the entanglement (finding #8) resolution. Registered BEFORE the
matcher runs, and committed before the scoring stage executes, so temporal
blinding is provable from git rather than asserted.

### What is being built and why detection alone cannot fix #8

Any measured rate is `M = C + B`: compliance (the scaffold NAMED the phrase,
the writer echoed it) plus behaviour (the construct arose unprompted). A
phrase echoed on command is STILL an instance of the construct, so a perfect
instrument counts it. The distinction lives in the causal path, not the text.
The registry supplies provenance; the matcher partitions events against it.

**Standing interpretation, binding on every downstream use:**
`M_dictated` is an UPPER bound on C; `M_novel` is a LOWER bound on B.
Behavioural claims are licensed by `M_novel` only.

### The registry

`docs/DICTATION_REGISTRY.json`, built by `gst/src/gst/registry.py` from 35
declared prompt symbols (judge prompts INCLUDED — a judge is a prompted
model). Extraction is `ast` parsing plus character-level quote scanning; the
no-regex directive is not engaged, and the one regex touch (`family_hint`) is
a screening flag for review, never a measurement. Frozen under a SHA-256
digest.

### V-A — discriminative validity of the matcher (GATED)

Provenance is read PER RUN from the recorded `input_messages`, never assumed
from a corpus name.

- **POS**: construct-bearing spans from DICTATED-provenance runs that contain
  a registry phrase verbatim.
- **NEG**: construct-bearing spans from CLEAN-provenance runs (Cell 30
  de-scaffolded; its prompts verified to contain no registry phrase) that
  contain no registry phrase.

**Gates, frozen now:**
- **AUC >= 0.80** on this deployed task. Finding #3 is the precedent: the NLI
  instrument scored 0.93 on its calibration task and 0.12-0.55 on the task it
  was actually deployed on. A matcher is validated on the job it will do.
- **Judge-judge agreement >= 0.70**, the Cell 30 precedent bar (sentence-level
  scored 0.833 and passed; document-level scored 0.622 and failed).
- **Attainability floor (checklist item 12): >= 15 spans in EACH of POS and
  NEG.** Below that the comparison is NOT EVALUABLE and is reported as such
  rather than as a failed gate.

**Stated limitation, registered now so it cannot be quietly dropped:** this
pool contrasts literal presence against literal absence and is therefore the
EASY case. A high AUC here is necessary, not sufficient — it establishes the
matcher can do the job at all, not that it catches every paraphrase.

### V-B — the over-attribution rate (MANDATORY REPORTING, no bar)

Spans from CLEAN-provenance runs that DO contain a registry phrase verbatim.
Dictation provably did not occur, so every match here is registry FORM
arising without dictation. This rate is the amount by which `M_dictated`
over-counts compliance, and it is reported wherever the partition is used.
No bar, because there is no value that would falsify anything — it is a
correction factor, not a hypothesis.

### Consequences, fixed in advance

- **AUC < 0.80** -> the judge stage is not deployable. The partition falls
  back to literal-only, and `M_dictated` is then reported as a strict
  UNDERCOUNT of form-echo. It does not get used anyway with a caveat.
- **Agreement < 0.70** -> NOT EVALUABLE, per finding #9.
- **Gate G-E on the matcher's own prompt must pass before any scoring.** A
  matcher naming the constructs it measures would be entangled with the
  defect it exists to quantify. `MATCHER_PROMPT` names no construct
  vocabulary and receives references as data; the harness asserts this and
  refuses to score otherwise.

### Goodhart clamp (checklist item 10)

The compliance share is a DIAGNOSTIC. A prompt engineered to lower measured
compliance is finding #8 inverted — it teaches the scaffold to evade the
registry. No prompt may be tuned against this number.

---

## DICTATION REGISTRY + PARAPHRASE MATCHER — VERDICT (2026-08-11)

### Deliverable 1: the registry is built and frozen

`docs/DICTATION_REGISTRY.json` — **125 entries from 35 declared prompt
symbols**, digest `bea936e3c4bc5033...`. Extraction is `ast` parsing plus
character-level quote scanning, so the no-regex directive is not engaged;
`family_hint` is a screening flag only, and 52 entries carry one.

**Registry finding — the judge was dictated the same phrases as the writer.**
`train/judge_instrument.py::PROMPT` (the Cell 7b pairwise judge) enumerates
"as of my training data...", "verify current guidance...", "assuming
that...", "modeled at...", "this may vary if...", "results could differ...",
"actual results may vary" (registry R101-R107). Those are the SAME strings
dictated to writers by BEHAVIOR_SPEC_ADDENDUM, HEALTH_ADD, FINANCE_ADD,
REWRITE_ADD and HOT_ADDENDUM. Finding #8 therefore reached the INSTRUMENT
layer, not only the scaffold: a judge told to look for "modeled at" was
scoring a writer told to say "modeled at". This was found mechanically, on
the registry's first run, by a lookup that took under a second — which is
the argument for the registry.

**Screen fidelity, checked:** exactly one false positive (R019, a JSON schema
description) and at least one miss (R033, a dictated example sentence whose
"assumes 510(k)" the lexicon's `assume[ds]? (that|the)` cannot reach). The
registry holds all 125 regardless; only the convenience subset is screened.
Consequence for deployment: `shortlist` must draw from ALL entries, since
screening at 0.25-0.30 recall would otherwise bound what the matcher can
ever match against.

### Deliverable 2: the matcher is NOT deployable

**The registered gates passed. The pass is an artifact, and it is recorded
as a failure.** AUC 0.904 (gate 0.80) and pooled judge-judge agreement 0.723
(gate 0.70) are both technically over the bar. Three defects void them:

| defect | evidence |
|---|---|
| agreement is base-rate inflation | decomposed: **POS 0.389, NEG 0.931**. The pooled figure is carried by 29 NEG items where both judges say NONE. On the class that matters the judges agree on 7 of 18 |
| one judge is a constant responder | `qwen2.5:7b-instruct` **AUC 0.533** — chance. Sensitivity 0.067, specificity 1.000: it answers NONE to almost everything, contributing no discrimination while inflating agreement |
| differential attrition correlated with the outcome | **40% of POS quarantined (12/30) vs 3.3% of NEG (1/30)**, all from `gpt-oss:20b`. Every surviving number is computed on a biased subsample, and the likely mechanism — longer, denser POS spans exhausting the reasoning budget — means the DROPPED items are the hard ones |

Ensemble sensitivity at the deployed threshold is **1/18 = 0.056**. A matcher
that fires on one in eighteen literal matches is not an instrument.

**Registered consequence executed:** the partition falls back to
literal-only, and `M_dictated` is reported as a strict undercount of
form-echo. `gst.dictation` carries a NOT DEPLOYABLE banner.

**Post-hoc, labelled as such (checklist item 6):** `gpt-oss:20b` ALONE
scores AUC 0.902, sensitivity 0.667, specificity 0.931 — genuine
discrimination. It is not adopted, because those numbers come from the 60%
of POS items that same judge managed to answer, and the attrition is its
own. A single-judge matcher needs its own registration with the token budget
fixed and attrition reported before it may be used.

### Deliverable 3: the over-attribution rate is ZERO — the strongest result here

V-B found **no clean-provenance span carrying a registry phrase: 0 of 2907
spans, 0 of 60 de-scaffolded runs, across 438,797 characters.** Direct probes
confirm it: "modeled at" 0/60, "hypothetical" 0/60, "assuming that" 0/60,
"verify current" 0/60, "as of my training" 0/60, "may vary if" 0/60.

Registry form essentially never arises without dictation. Run-level Wilson
upper bound 0.060 (0/60; span-level is tighter but ICC 0.190 makes the run
the honest unit). The scaffold's phrases are **diagnostic of the scaffold**,
which is what makes the literal stage trustworthy even with the judge stage
withdrawn — and it independently corroborates PD-13 from a different corpus
and a different direction.

### A registration error of mine, corrected in the record

The pre-registration and `gst.registry` both stated "**M_novel is a LOWER
bound on B**". That is backwards. Misses push compliance INTO M_novel and
inflate it; only false alarms deflate it. Measured here, misses (~33% on
literal items) dominate false alarms (~7%, and 0 at corpus level). Correct
directions:

    M_dictated  LOWER bound on compliance C
    M_novel     UPPER bound on behaviour B

This matters for what the partition can license. A **small** M_novel is
strong evidence behaviour is small. A **large** M_novel proves nothing,
because undetected paraphrase inflates it. My earlier proposal message had
this right ("an imperfect ceiling on B") and the registration flipped it;
the flip is corrected in `registry.py`, `dictation.py` and here.

### Where this leaves finding #8

Layer 1 (structural prevention) is DONE and already caught an instrument-level
entanglement nobody had looked for. Layer 2 is HALF done: the literal stage is
validated and its false-alarm rate is measured at zero, but the paraphrase
stage is withdrawn. Layer 3 (the phrase-swap cell) is unaffected — it never
depended on the matcher, and its attainability computation now has real
numbers to use.

---

## LAYER 3 ATTAINABILITY + FORM FREEZE (2026-08-11, before the cell is registered)

Checklist item 12 applied to my own proposal. Computed from the archive; no
generation except a 16-call elicitability probe.

### The number that changed the design

My proposal reasoned from PD-13's non-dictated channel, **1/30 -> 4/30**, and
warned that an invariance test on a ~13% outcome would need an equivalence
margin and a large n. That base rate was a **regex artifact**. Under the
validated sentence-level judge on the de-scaffolded corpus (Cell 30 arm P,
n=60), the same construct sits at:

| outcome | control rate |
|---|---|
| `modeled` family presence | **0.167** (vs 0.033 regex-era — 5x) |
| any construct family | **0.633** |
| mean qualification sentences/run | 1.250 (sd 1.349) |

The outcome is roughly five times more attainable than the proposal assumed.

### Form freeze — `docs/PHRASE_SWAP_FORMS.json`

**Form X = "modeled at"** (the dictated form). 11 registry entries across 9
prompt symbols. Measured on 2M characters:

| corpus | rate |
|---|---|
| clean-provenance (249 runs: Cell 30 + Cells 37/40) | **0/249** [0.000, 0.015] |
| scaffolded (396 archived council runs) | **172/396 = 0.434** |

This is PD-13's compliance signature reproduced on 13x the runs, from a
different corpus, by a different method. The phrase never appears
spontaneously and appears in 43% of scaffolded runs.

**Form Y = "taken to be"** (the swapped synonym). 0 registry entries, 0
lexicon patterns, **0/249 clean and 0/396 scaffolded** — matching form X's
exact zero, which is the symmetry the swap requires.

Chosen from seven zero-rate candidates because it alone is a drop-in
substitution in the same syntactic slot ("persistence is modeled at 60%" ->
"persistence is taken to be 60%"), so neither arm's instruction is harder to
comply with than the other's; it marks an assumption rather than setting a
value; and it was elicited at form X's own rate.

Rejected and why: "estimated at" (2/249 clean AND 14/396 scaffolded — non-zero
on both), "projected at" (3/249, highest of any candidate), "pegged at"
(elicited 0/4; connotes fixing, may not express the construct), "carried at"
(accounting term of art, not a synonym). **"a working figure of" passes every
empirical screen and is HELD as the fallback**, rejected only for being a noun
phrase rather than a drop-in.

The elicitability probe is reported with its limit: n=4 per form on a
deliberately short task, which depressed every rate including form X's (1/4
against its 0.434 in real runs). It establishes a non-zero floor. It cannot
rank candidates and was not designed to.

### Attainability verdict

Design effect x1.38 (3 repeats at the recorded ICC 0.190); throughput 154
s/run measured from Cell 40.

- **P.1 (compliance is form-tracking): n = 15 per arm.** Trivially attainable
  — the archive already shows the effect at 0.002 vs 0.434.
- **P.2 (form-independent channel):** MDD at n=60/arm is **+0.263** (180 runs,
  7.7 h). PD-13's lift rescaled to the validated base predicts p2 ~ 0.50,
  needing **n = 39 per arm (117 runs, 5.0 h)**.

**Layer 3 is ATTAINABLE at n = 60 per arm — 180 runs, roughly 8 hours.** That
buys P.1 with enormous margin and detects any form-independent lift at or
above +0.26 on the `modeled` family.

**Registered honestly:** at n=60 a form-independent effect SMALLER than +0.26
would not be detected, and the correct verdict in that case is NOT EVALUABLE
for P.2 rather than "no behavioural effect". If the design is to license a
null, it needs n=120+/arm (15.4 h) or the any-construct outcome. That choice
belongs in the cell's registration, not here.

**Not yet registered and not yet run.** This freeze fixes the forms and the
attainability inputs only.

---

## CELL 41 PRE-REGISTRATION — the phrase-swap cell (registered 2026-08-11, before any run)

Layer 3 of the finding-#8 resolution, and the only piece that IDENTIFIES the
behavioural component rather than bounding it. Forms were frozen in
`docs/PHRASE_SWAP_FORMS.json` before this registration was written.

### Why the earlier n was wrong, and what changed

I told Sam that "licensing a null needs 120+/arm" on an MDD of +0.182. That
figure applied a design effect of 1.38 (three repeats) at every n. But 120
runs/arm across Cell 30's **nine** cases is ~13 repeats per case, so the true
design effect is 3.28. Recomputed against the case count:

| cases | runs/arm | n_eff | MDD |
|---|---|---|---|
| 9 | 126 | 36.3 | +0.289 |
| 9 | **infinite** | **47.4** | **+0.252 — a hard ceiling** |
| 18 | 126 | 58.9 | **+0.224** |

**The cell is cluster-limited, not run-limited.** With nine cases no amount
of running reaches the +0.182 I quoted. The fix is more CASES, not more runs.
Nine further cases already exist in `examples/test_cases.py` and lacked only
de-scaffolded seat text, which stage `seats` generates using Cell 30's exact
clean prompts.

### Arms — one factor (writer instruction / named surface form)

- **A-control** — Cell 30's clean `WRITER_PROMPT`, no clause
- **A-form-X** — + clause naming `"modeled at"` (dictated in 11 registry
  entries across 9 prompt symbols)
- **A-form-Y** — + clause naming `"taken to be"` (0 registry entries)

The clause is byte-identical across treated arms but for the form; the
harness asserts this and refuses to run otherwise. **18 cases x 7 repeats x 3
arms = 378 runs, 126/arm.**

### Gate G-E, inverted

G-E normally refuses any prompt containing a registry phrase. Here dictation
IS the treatment, so the check becomes: each arm contains **exactly** its own
named form and no other registry phrase. `audit_clause_dictation()` aborts on
any other match. Verified PASS before launch.

### Instruments — both already validated

- **construct presence:** batched sentence judge at B=10 (Cell IV validated),
  two judges. Its definitions name no phrase and instruct "do not reward
  particular wording"; it passes gate G-E. Agreement bar **0.70** (Cell 30's
  P30.0 protocol), reported on the `modeled` family.
- **form attribution:** literal containment of the frozen forms, validated at
  **0/2907 over-attribution** (V-B).

Analysis bootstraps over **cases**, not runs — the cluster is the resampling
unit, so ICC 0.190 is handled in the analysis rather than approximated.

### Predictions

- **P41.1 (compliance is form-tracking).** BOTH treated arms must raise their
  own named form above control, cluster-bootstrap CI excluding 0. *Attainable
  at n=15/arm;* the archive already shows 0/249 vs 172/396 for form X.
  *Falsified if* either arm fails to move its own form.
- **P41.2 (form-independent effect) — THE ESTIMAND.** For each treated arm,
  the rate of runs carrying a judge-labelled `modeled` sentence that does NOT
  contain that arm's own form. SUPPORTED iff BOTH exceed control with CI
  excluding 0. *Falsified if* neither does. One-only is reported as
  form-dependent and counts as falsified as registered.
- **P41.3 (cross-form leakage, validity guard).** Each treated arm's rate of
  the OTHER arm's form, reported against control. Non-trivial leakage
  contaminates form attribution and voids P41.2's partition.
- **P41.4 (silence check, mandatory).** Emission reported beside every rate —
  mean sentences and characters per arm. No arm may score well by going quiet.

### What a falsification of P41.2 licenses, fixed now

At n_eff 58.9 the MDD is **+0.224**. A falsification therefore licenses only
**"no form-independent effect >= +0.22"** — which does exclude the
PD-13-rescaled prediction of +0.33, and is a genuine result. It does **NOT**
license "the instruction has zero behavioural effect". Any smaller true
effect is undetected, and the honest verdict for that region is NOT
EVALUABLE. This sentence is registered so it cannot be quietly dropped when
the numbers arrive.

### Goodhart clamp

Neither form may be tuned to improve any number here. The forms are frozen in
a committed file with their measured base rates; a form swapped after seeing
results is a different experiment and must be registered as one.

---

## SEAT-APPROACH PILOT (2026-08-11) — descriptive, zero model calls

Sam's hypothesis: purpose-trained seats are not epistemically more capable
than generalists, but have a distinct APPROACH — different framing, different
reasoning path — even where outcomes match. Cell 36's null does not refute
this: equal accuracy says nothing about path.

Run as a pre-check under checklist item 12, on archived data only. No
generation; Cell 41's judging was untouched.

### Finding 1 — producer attribution is trivially confounded by surface form

Two GENERALIST models, identical prompt, same items:

| corpus | feature | gpt-oss | phi4 | AUC |
|---|---|---|---|---|
| Cell 36 (ASK) | chars | 112 | 432 | **0.024** |
| Cell 36 | ttr | 0.875 | 0.594 | 0.920 |
| Cell 30 (long-form) | chars | 8690 | 4559 | **0.945** |
| Cell 30 | list_frac | 0.090 | 0.504 | **0.003** |
| Cell 30 | ttr | 0.432 | 0.515 | 0.121 |

**Any "can a judge tell the producers apart" instrument would score near
ceiling on formatting alone, between two models neither of which is
domain-trained.** Distinguishability is therefore NOT evidence of distinct
approach, and an attribution-based design would have produced a strong,
meaningless positive.

### Finding 2 — length-matching is not attainable on existing corpora

Cell 30's length-overlap band (3790-6184 chars) leaves 7 gpt-oss vs 16 phi4
runs — below any usable floor. The confound cannot be controlled after the
fact on this archive.

### Finding 3 — every existing corpus is confounded for this question

| corpus | confound |
|---|---|
| Cell 36 `seat_text` (60/60 stored) | seat analyses and single-model answers use different prompts and differ ~4x in length |
| Cells 30/41 seats | one generalist under role prompts — no domain training present at all |
| 396 archived runs | each seat answers a DIFFERENT routed sub-question, so domain loading is topic-driven by construction |

A frozen framework inventory (a known-value check, not regex-as-NLP) does
have resolution — real specialists load on their own domain, legal 0.80 and
finance 2.36 against off-domain rates — but on these corpora that reflects
routing, not disposition. Per-kchar the generalist actually out-names Med42
on clinical frameworks (0.136 vs 0.101), which is suggestive and NOT
interpretable here.

### Verdict

**The hypothesis is not answerable from the archive.** It is also not
refuted. What the pilot bought is the specification of the cell that could
answer it, and the prevention of a confounded positive.

### What the cell must control

1. **Identical prompt to every producer** — no role differentiation, no
   sub-question routing (kills the topic confound).
2. **Same items across producers**, outcome held constant where possible
   (restrict to items all producers answer correctly).
3. **Format-invariant instrument** — framework inventory plus judged
   decomposition; length reported beside every rate and never left free.
4. **Crossed domain x base-family** — the decisive control. A single
   specialist-vs-generalist comparison moves architecture, identity, training
   data and scale at once (audit #3's P36.2 warning). If domain training
   induces an approach, medical fine-tunes on DIFFERENT bases should resemble
   each other more than each resembles ITS OWN base.

Pairs already local: `Meditron3-Qwen2.5-7B` <-> `qwen2.5:7b-instruct` (exact
family); `BioMistral-7B` and `Saul-Instruct-v1` <-> `mistral:7b-instruct`
(near, v0.1 vs v0.3 lineage — flag it). Pulling `Llama-3.1-8B-Instruct`
(~5GB) would complete `Med42` (medical) AND `Hawkish-8B` (finance) on one
shared base — two domains, one base, which is the strongest single addition.

NOT registered and NOT run. This is a specification, and it needs the machine
free of Cell 41 first.

---

## CELL 41 VERDICT (2026-08-11) — the instruction is its phrase

378 runs, 18 cases, 3 arms. Judge agreement on `modeled` **0.910
(14088/15485)**, well over the 0.70 bar — the highest agreement recorded in
this program. Attrition permutation-tested BEFORE any verdict was read:
unparsed rates 0.036/0.048/0.038 by arm, spread p = 0.327, **not arm-linked**.

| arm | n | has X | has Y | modeled presence | sentences | chars |
|---|---|---|---|---|---|---|
| control | 126 | 0.000 | 0.000 | 0.341 | 46.6 | 7758 |
| form-X | 126 | **0.667** | 0.000 | 0.571 | 43.7 | 7309 |
| form-Y | 126 | 0.000 | **0.698** | 0.429 | 43.9 | 7485 |

### P41.1 SUPPORTED — compliance is form-tracking

form-X 0.000 -> 0.667, CI [+0.468, +0.857]. form-Y 0.000 -> 0.698, CI
[+0.524, +0.865]. Each arm produced its own named phrase and nothing else.

**The house phrase has no privilege.** "modeled at" appears in 11 registry
entries across 9 prompt symbols and has been drilled through every version of
this system; "taken to be" was chosen the day before the run and appears in
2M characters of archive exactly zero times. They performed
indistinguishably (0.667 vs 0.698). Whatever the instruction engages, it is
not a learned disposition toward the words the program has been feeding it.

### P41.2 FALSIFIED — nothing survives the swap

With each arm's own named phrase subtracted:

- form-X 0.341 -> 0.365, CI **[-0.079, +0.111]**
- form-Y 0.341 -> 0.317, CI **[-0.103, +0.087]**

Both intervals straddle zero, and they straddle it in OPPOSITE directions —
form-X nominally up, form-Y nominally down. There is no consistent
form-independent residue.

The entire measurable effect of the instruction is the phrase it names. Once
the named words are removed, an instructed writer is indistinguishable from
an uninstructed one.

### P41.3 — the validity guard is exactly zero

Neither treated arm ever emitted the other's form: 0.000 and 0.000 against a
control of 0.000, over 252 treated runs. Form attribution is uncontaminated,
so P41.2's partition is clean rather than noisy. The writer never improvised
an equivalent of its own.

### P41.4 silence check — the null is not bought with silence

Emission is flat: 43.7-46.6 sentences and 7309-7758 chars across arms. No arm
went quiet. Note the raw `modeled` presence DOES rise (0.341 -> 0.571 in
form-X) — that rise is real and is entirely the named phrase.

### What this licenses, and what it does not

**Licensed:** no form-independent effect at or above **+0.22**. That excludes
the PD-13-rescaled prediction of +0.33, so the compliance-only reading is not
merely unrefuted, it is the one the data support.

**NOT licensed:** "the instruction has zero behavioural effect." The MDD is
+0.224 at n_eff 58.9; any true effect smaller than that is invisible here.
This sentence was registered before launch precisely so it could not be
dropped now.

### Consequence for the program

Finding #8 is no longer a suspicion about the instrument — it is a measured
property of the intervention. Every instruction-derived "epistemic caution"
number this program produced is compliance with a phrase order, at the
resolution this cell can see. PD-13 established that for one dictated
phrasing by decomposition within one instrument; Cell 41 establishes it
causally, on two counterbalanced forms, with a validated judge that never saw
either phrase.

The three-layer entanglement resolution is complete: Layer 1 prevention (the
registry, which caught finding #12), Layer 2 partition (literal stage
validated at zero over-attribution; paraphrase stage withdrawn), Layer 3
identification (this cell).

---

## DOMAIN-SIGNATURE ATTAINABILITY PROBE (2026-08-11) — instrument viable, design needs a third lineage

Checklist item 12 before registering the seat-approach cell. 48 runs, 4
producers, 6 items, identical prompt to every producer. **A probe, not a
cell — it licenses no claim about approach.**

### Result 1 — the instrument has resolution, at feasible n

| producer | kind | n | chars | fw_hc/k | fw_lg/k |
|---|---|---|---|---|---|
| meditron3 | tuned | 12 | 3151 | 0.061 | 0.048 |
| qwen2.5 | base | 12 | 4191 | 0.212 | 0.039 |
| biomistral | tuned | 12 | **424** | 0.000 | 0.000 |
| mistral | base | 12 | 3311 | 0.151 | 0.084 |

Meditron3 vs its own base: **Cohen d = 0.82, n ~ 24 per producer** for 80%
power. That is cheap. And the surface confound is far milder than the pilot
feared — chars AUC 0.194, list 0.372, ttr 0.368, against the 0.945 that
separated two generalists. **Framework-per-kchar is a usable instrument.**

### Result 2 — BioMistral is degenerate and its lineage drops out

**12 of 12 runs under 800 characters** (longest 620). It writes an opening
paragraph and stops. Its 0.000 content rates mean absent text, not absent
frameworks — finding #6 exactly. A degeneracy guard now runs in the measure
stage and drops such arms automatically.

With one lineage dead, **the crossed test is NOT EVALUABLE.** Replication
across base families is the only contrast identity cannot explain, so a
single surviving lineage licenses nothing about domain training.

### Result 3 — a harness bug of mine, caught and fixed

The first measure pass printed "**consistent with a domain signature**". It
tested only whether the two deltas shared a SIGN — never whether that sign
matched the hypothesis. Both deltas were NEGATIVE, i.e. the fine-tunes named
FEWER domain frameworks than their bases, and the harness reported that as
support. It would also have counted a degenerate arm as a replication.

That is the "instrument says what I wanted" class the audits keep finding.
Fixed: the crossed test now checks direction against the registered
prediction (tuned > base) and drops degenerate arms before deciding.

### The early signal, stated as a signal and not a result

On the one usable lineage, the medical fine-tune names **fewer** healthcare
frameworks per 1k chars than its own base: 0.391 -> 0.122, delta -0.269 on
in-domain items, with off-domain items near zero for both. Direction
CONTRADICTS the hypothesis. n=6 per cell, single lineage, no replication —
this is a reason to run the cell, not a finding from it.

### What the real cell needs

1. **A third lineage to replace BioMistral.** `Llama-3.1-8B-Instruct` (~5GB)
   would put `Med42` (medical) AND `Hawkish-8B` (finance) on one shared base
   — two domains, one base, and it repairs the crossed design in a single
   pull. `OpenBioLLM-Llama3` is a further medical option.
2. **A degeneracy screen BEFORE the arms are fixed** — any candidate producing
   <800 chars on a pilot item is excluded at selection, not discovered at
   measurement.
3. **n ~ 24-30 per producer**, from the measured d = 0.82.
4. Framework inventory frozen (already is), surface features reported beside
   every content number (already are).

NOT registered. The probe says the cell is worth running and says what it
must fix first.

---

## CELL 42 PRE-REGISTRATION — do domain fine-tunes reason differently? (registered 2026-08-11, before any run)

Sam's hypothesis: purpose-trained models are not epistemically more capable
than generalists, but have a distinct APPROACH. Cell 36's null does not
refute it — equal accuracy says nothing about path.

Producers frozen in `docs/CELL42_PRODUCERS.json` before this registration.

### The confound this design exists to defeat

"Specialist vs generalist" moves architecture, identity, training data and
scale at once (audit #3, P36.2). The only contrast identity cannot explain is
**replication across base families**: if domain training induces an approach,
the tuned-minus-its-own-base delta should point the same way on lineages that
share no ancestry.

| lineage | base | domain fine-tune(s) |
|---|---|---|
| qwen2.5 | `qwen2.5:7b-instruct` | Meditron3 |
| llama3 | `llama3:8b-instruct-q4_K_M` (pulled for this cell) | Med42, OpenBioLLM |

Two independent lineages, plus a **within-lineage replicate** (Med42 and
OpenBioLLM share the llama3 base), which separates "this fine-tune is quirky"
from "medical fine-tuning does this".

### Degeneracy screen — applied at SELECTION

The probe discovered BioMistral's degeneracy at measurement, after it had
already poisoned a lineage. Here the gate runs first: every candidate must
produce >= 800 chars on every screen item. Measured — llama3 3159, Med42
3611, OpenBioLLM 1514, all PASS. **BioMistral is excluded by name and
reason.** Hawkish is excluded: Llama-3.1 lineage whose base is not pulled,
and disk is at 92%.

### Arms — one factor (producer), everything else identical

Identical prompt to every producer: no role text, no domain framing, no
format dictation. Same items. **5 producers x 12 items x 6 repeats = 360
runs**, 72 per producer, comfortably over the n=30 the probe's d=0.82
implies.

Items: 6 in-domain (healthcare) and 6 off-domain. A real domain signature
must be DOMAIN-SPECIFIC; a global style difference shows up on both and is
reported as style, not signature.

### Instrument

Frozen framework inventory, counts normalised per 1k characters so verbosity
cannot buy signal — a containment check against a fixed list, the same basis
as Cell 37's numeral check, not regex-as-NLP. Surface features (chars,
list_frac, ttr) reported beside every content number, because the
seat-approach pilot showed two GENERALISTS separate at AUC 0.945 on length
alone. Probe surface AUCs on the clean pair were 0.194/0.372/0.368 — far
milder, which is why the instrument is usable at all.

### Predictions

- **P42.1 (domain signature replicates across lineages).** The
  tuned-minus-own-base delta in in-domain framework density is POSITIVE and
  its CI excludes 0 in BOTH lineages. *Falsified if* either lineage fails, or
  if the two lineages disagree in sign.
- **P42.2 (the signature is domain-specific).** The in-domain delta exceeds
  the off-domain delta, CI on the difference excluding 0. *Falsified if* they
  are equal — that is a global style difference, reported as style.
- **P42.3 (within-lineage replication).** Med42 and OpenBioLLM, sharing the
  llama3 base, agree in sign. *Falsified if* they disagree — which would mean
  the effect is per-model, not per-domain-training.
- **P42.4 (surface control, mandatory reporting).** Per-producer chars,
  list_frac, ttr reported beside every content number, and every content rate
  is per-kchar. If a producer's content delta tracks its length delta, the
  finding is verbosity and is reported as such.
- **P42.5 (degeneracy, mandatory).** Any producer whose run falls under 800
  chars is counted and reported; a producer degenerate in >50% of runs is
  dropped and its lineage declared NOT EVALUABLE.

### Direction stated in advance

The probe's single usable lineage pointed the WRONG way for the hypothesis:
Meditron3 named FEWER healthcare frameworks per kchar than its base (0.391 ->
0.122, delta -0.269). **P42.1 as written predicts POSITIVE deltas, so the
probe's direction would falsify it.** That is registered here so the
prediction cannot be quietly reversed after the fact — a negative replicated
delta is a real and interesting result (the specialist is LESS
domain-framed), but it falsifies the hypothesis as stated.

### Verdict logic guard

The probe's first measure pass reported "consistent with a domain signature"
on a test that checked only whether two deltas shared a sign, never whether
that sign matched the prediction. The harness now checks direction against
the registered prediction and drops degenerate arms before deciding. That
guard is a precondition of this cell.

---

## CELL 42 VERDICT (2026-08-11) — the signature is per-model, not per-domain-training

360 runs, 5 producers x 12 items x 6 repeats, 72 per producer, zero failures.
Identical prompt to every producer; all content rates per 1k characters;
cluster bootstrap over items.

### P42.5 degeneracy — the selection-time screen worked

| producer | runs < 800 chars |
|---|---|
| qwen2.5, meditron3, llama3, med42 | 0/72 |
| openbiollm | 13/72 (18%) |

No producer crossed the 50% drop threshold. Contrast BioMistral's 12/12 in
the probe: screening at SELECTION rather than discovering at measurement is
what kept every lineage alive.

### P42.4 surface control

| producer | kind | chars | list | ttr | hc/k(in) | hc/k(off) |
|---|---|---|---|---|---|---|
| qwen2.5 | base | 4313 | 0.442 | 0.427 | 0.284 | 0.049 |
| meditron3 | tuned | 2957 | 0.381 | 0.436 | 0.243 | 0.013 |
| llama3 | base | 3161 | 0.165 | 0.429 | 0.185 | 0.007 |
| med42 | tuned | 2619 | 0.069 | 0.509 | **0.417** | 0.036 |
| openbiollm | tuned | 1216 | 0.000 | 0.602 | 0.294 | 0.040 |

Every tuned model is SHORTER than its base, so per-kchar normalisation is
doing real work: Med42's positive result survives despite writing 17% less
than llama3, and cannot be verbosity.

### P42.1 FALSIFIED — no replication across ancestries

| pair | delta (in-domain) | CI | |
|---|---|---|---|
| meditron3 vs qwen2.5 | -0.041 | [-0.099, +0.025] | spans 0 |
| **med42 vs llama3** | **+0.232** | **[+0.072, +0.412]** | **POSITIVE** |
| openbiollm vs llama3 | +0.109 | [-0.056, +0.300] | spans 0 |

The registered prediction required a positive delta with CI excluding 0 in
BOTH lineages. One fine-tune of three delivers one. The qwen2.5 lineage shows
nothing, so replication across base families — the only contrast identity
cannot explain — is not demonstrated.

### P42.3 FALSIFIED — and this is the informative one

Med42 (+0.232, CI excludes 0) and OpenBioLLM (+0.109, spans 0) share the
SAME llama3 base, the same prompt, the same items. They disagree. **Two
medical fine-tunes of one base model do not produce the same signature**, so
what Med42 shows is a property of Med42, not of medical fine-tuning.

### P42.2 — Med42's effect IS domain-specific

Med42 in-domain +0.232 against off-domain +0.029, an 8x ratio: it is not
globally more clinical-sounding, it is more clinical-sounding ON CLINICAL
ITEMS. OpenBioLLM shows the same shape at lower magnitude (+0.109 vs +0.033).
Meditron3 is flat on both (-0.041, -0.035) and is reported as global style.

So where the effect exists it has the right SHAPE — it just does not
generalise across models.

### What this licenses

**Sam's hypothesis is falsified as registered.** Purpose-trained models do
not reliably reason differently from their own base models. Domain
fine-tuning is not sufficient to induce a distinct approach.

**But it is not empty.** Med42 shows a real, domain-specific, verbosity-proof
shift of +0.232 in clinical framework density over the model it was built
from. The capability is achievable; it just is not a property of
"purpose-trained" as a category. It is a property of particular training runs.

The probe's alarming signal did NOT survive: Meditron3's -0.269 at n=6 became
-0.041 spanning zero at n=72. A textbook small-n artifact, and the reason the
probe was labelled a sizing exercise rather than a result.

### Second verdict-logic bug of the day, recorded

The first measure pass printed "both lineages replicate in the spans 0
direction ... the effect is real and replicable". `agree` computed
`len({...for v in lin_dirs.values() if len(v)==1})==1`, which was satisfied
by ONE lineage carrying a single label — and "spans 0" was treated as a
direction rather than the absence of one. It asserted replication for a null.

Same failure family as the probe's sign-only test hours earlier: **a verdict
line that can fire without the evidence it names.** Fixed — a lineage now has
a direction only if all its tuned models agree on a non-null one. Both bugs
were in verdict-printing code, not in estimation; every number was correct
both times. The lesson is that verdict logic needs the same adversarial
reading as the statistics.

---

## CELL 43 PRE-REGISTRATION — the preference-lift decomposition (registered 2026-08-11, before any run or judgment)

The missing measurement for the MoA-audit paper: this program has never
observed a PREFERENCE score. Cell 43 measures whether an LLM preference
judge shows a MoA-style lift on this pipeline, and decomposes what any lift
is made of. The judge is the OBJECT of study, not an instrument — it needs
no ground-truth validation, and it may never double as an outcome
instrument (finding #8's rule).

### Deviation from the proposal, forced by the checklist

Proposed as archival-only. Item 1 (one factor) kills that: no direct
gpt-oss answers to these cases exist — every archived gpt-oss run received
seat contributions. A Cell 42-producer baseline would move writer identity
and aggregation together. So ONE arm is generated: **A-direct**, gpt-oss:20b
answering the 18 Cell 41 cases with the writer prompt minus only the
contributions sentence. 18 x 7 = 126 runs, matching the Cell 41 control arm
in model, temperature, tokens, cases and repeats.

### Comparisons (pairs on same case, repeat i vs repeat i, 126 pairs each)

| pair | tests |
|---|---|
| C1: Cell 41 control (2-layer MoA) vs A-direct | **the lift** — does aggregation win preference? |
| C2: Cell 41 form-X vs control | compliance-preference: arms differ ONLY in a dictated phrase (Cell 41 proved no behavioural residue), so any preference gap IS phrase/register preference |
| C3: Cell 41 form-Y vs control | the counterbalanced replicate of C2 |

All outputs in every pair are gpt-oss text, so self-preference bias is
symmetric by construction and cannot create an arm difference.

### Judging protocol

Pairwise, BOTH orderings, temperature 0; a pair is decisive only if the
same side wins in both orderings (Cell 7b precedent), else TIE. Judge
prompt is generic better-answer wording, gate G-E-checked against the
registry before any call. **Primary judge gpt-oss:20b on all 378 pairs;
replication judge qwen2.5:7b-instruct on a frozen 40-pair-per-comparison
subsample** (seeded), reported beside the primary, never pooled.

### Predictions

- **P43.1 (the lift).** C1 preference share for the MoA side differs from
  0.5, cluster bootstrap over the 18 cases, CI excluding 0.5. Either
  direction is informative; a null bounds where collaborativeness lives at
  this scale. *Attainability: at 126 pairs and an expected 60-80% decisive
  rate, the MDD is a preference share of ~0.64 — the cell can see a
  MoA-sized effect and cannot see a subtle one; a null licenses only "no
  preference shift >= ~0.14 from even".*
- **P43.2 (compliance-preference).** C2 and C3 shares exceed 0.5 with CIs
  excluding it, SAME direction in both forms. One-form-only is reported as
  form-specific, not as register preference. A null here is informative
  against the thesis and will be reported as such.
- **P43.3 (decomposition — the estimand).** Among decisive pairs: fraction
  where the winner is the LONGER response (CI vs 0.5); for C1, alignment
  with per-kchar framework density; for C2/C3, alignment with validated
  qualification counts (labels exist for all Cell 41 arms). Report the
  preference rate within near-length-matched pairs (|Δchars| < 15%) beside
  the raw rate. Prediction: length alignment > 0.5.
- **P43.4 (mandatory reporting).** Decisive/tie/disagreement rates per
  judge and per comparison; mean chars per arm; position-consistency. An
  arm must not win by silence or lose by it unexamined.

### Guards

Preflight (256-token budget), consecutive-failure abort, resumable stages,
judgments cached and quarantined-not-defaulted on unparseable replies
(finding #2). Verdict lines may fire only on the registered conditions —
after two same-day verdict-logic bugs, the measure stage prints the raw
table above every verdict.

---

## CELL 43 VERDICT (2026-08-12) — the lift is real; the compliance phrases COST preference

498 pairs, both orderings, primary judge gpt-oss:20b; 1 quarantine total
after the budget fix. Arm mean lengths nearly identical (control 7757 vs
direct 7649 chars, +1.4%), so the headline comparison is not arm-level
length. Display note: the raw table's "quarantined 86" rows for the
replication judge are pairs never assigned to its frozen 40-pair subsample,
mislabelled by the printer; true qwen quarantines within subsample = 0.

### P43.1 SUPPORTED — a MoA-style preference lift exists at 20B scale

MoA side share of decisive pairs **0.818 [0.718, 0.919], n=44**. It
survives the length control: among the 27 near-length-matched pairs the MoA
share is **0.815**. It does not track framework density (winner has more
fw/k in only 0.409 of decisive pairs). Scope: ONE judge (gpt-oss), which is
also the writer of every output on both sides — self-preference symmetric
by construction. The replication judge is NOT EVALUABLE (2 decisive of 40;
95% ties).

### P43.2 FALSIFIED — REVERSED, and replicated: the judge PENALIZES the phrase arms

Registered prediction: both phrase arms exceed 0.5 (judges reward the
compliance register). Result:

| comparison | phrase-arm share | CI |
|---|---|---|
| C2 form-X vs control | **0.261** | [0.140, 0.388] |
| C3 form-Y vs control | **0.317** | [0.152, 0.480] |

Both CIs sit entirely BELOW 0.5, same direction, both forms. Cell 41
established these arms differ from control only in the dictated phrase; so
this is a causal, counterbalanced measurement that **epistemic-labelling
phrases cost preference points**. It also survives length matching (matched
shares 0.267 and 0.346) and the winner has MORE validated qualification in
only 0.414/0.353 of decisive pairs.

### P43.3 — the decomposition, honestly summarised

Winner-is-longer runs 0.73-0.80 within pairs across all comparisons, so
length aligns with winning generally — but both headline effects survive
length matching, so neither is length. The C1 lift is not framework
density. The C2/C3 penalty is the phrase (the only manipulated variable).
**What the C1 lift is made of remains unidentified** — the measured surface
features do not explain it, and the honest statement is that aggregation
adds something this feature set does not capture.

### P43.4 — the instrument, measured

Raw position bias 85% first-position (A 736 / B 145 final). Order-debiasing
converts it to ties: decisive rate 0.35 for the primary judge; the second
local judge is 95% ties — near-total position dependence. **Recorded as
instrument-validity finding #14**: local pairwise preference judging is
majority reading-order; order-debiased protocols keep it honest but pay
~2/3 of the sample for it.

### What this does to the paper thesis

The strong form — "preference lifts are made of compliance surface" — is
WRONG, by this cell's own registered test, and the correction is a better
paper:

1. The aggregation lift replicates locally, under a position-noisy judge,
   and is not length, framework density, or hedge-register.
2. Dictated qualification phrases actively LOSE preference — so a pipeline
   optimised against a preference judge will shed exactly the epistemic
   marking the instruction paradigm tries to install. Preference pressure
   and epistemic disposition are in measured tension: PD-13/Cell 41 showed
   instructions buy only the phrase; Cell 43 shows the phrase then costs
   preference. The two-cell chain is causal at both links.
3. The instrument the MoA literature rests on is, at this scale, two-thirds
   reading-order — and the one earlier program result it could have
   confounded is bounded by finding #14's protocol.

---

## CELL 43-R PRE-REGISTRATION — disjoint-family judge replication (registered 2026-08-12, before any pilot or run)

Cell 43's findings rest on one judge (gpt-oss:20b), which is also the writer
of every output judged. Self-preference is symmetric within pairs, but the
scope is one judge family. This cell replicates the three comparisons under
a judge from a DIFFERENT model family, on the identical pairs and protocol.

### Candidates and the selection rule, fixed in advance

Candidates (all local, none wrote any output under judgment):
`phi4:14b` (Microsoft, dense), `deepseek-r1:7b` (DeepSeek, reasoning),
`qwen3-vl:30b-a3b-instruct` (Qwen3 MoE). The prior replication judge
(qwen2.5:7b) collapsed to 95% ties and is excluded by that measurement.

**Selection is by attainability ONLY, blind to direction.** A 20-pair
seeded pilot per candidate (C1 pairs, both orderings) measures parse rate
and decisive rate. The pilot script reports ONLY those two numbers — it
does not compute or print which side wins, so judge choice cannot be
direction-shopping (checklist items 10 and 12). Selection: highest decisive
rate among candidates with parse rate >= 0.90; gate: decisive rate >= 0.20,
else the candidate is dropped; if all fail, the replication is NOT
EVALUABLE and Cell 43 remains single-judge, reported as such.

### Full run and predictions

Selected judge runs all 378 pairs, both orderings, temperature 0, same
generic gate-G-E-checked JUDGE_PROMPT, same quarantine rules.

- **P43R.1 (direction replication).** For each of C1/C2/C3, the selected
  judge's decisive-share CI (cluster bootstrap over cases) lies on the SAME
  side of 0.5 as the primary judge's. Supported only if all three agree.
  *Falsified if* any comparison lands with a CI entirely on the opposite
  side. A CI spanning 0.5 where the primary was decisive is reported as
  NOT REPLICATED AT THIS POWER, distinct from contradiction.
- **P43R.2 (mandatory).** Position split, decisive/tie/quarantine per
  comparison, and the same length-decomposition columns as Cell 43.

Magnitude is NOT the estimand — decisive rates differ by judge, so shares
are not comparable across judges; only direction is.

---

## CELL 43-R VERDICT (2026-08-12) — PARTIAL replication: the lift and one phrase penalty cross judge families; the other spans at this power

Judge selected blind to direction per registration: qwen3-vl:30b-a3b
(parse 1.00, decisive 0.40 in pilot; phi4 failed the decisive gate at 0.15;
deepseek-r1 failed the parse gate at 0.80 despite decisive 0.45). Full run:
378 pairs, both orderings, ZERO quarantines. Raw position split A 663 / B 93
(0.88) — within a point of gpt-oss's 0.85, across vendor, architecture and
generation.

| comparison | replication share | primary share | verdict |
|---|---|---|---|
| C1 MoA vs direct | 0.788 [0.645, 0.917] (n=33) | 0.818 [0.718, 0.917] | **AGREES** |
| C2 form-X vs control | 0.276 [0.097, 0.520] (n=29) | 0.261 [0.146, 0.391] | NOT REPLICATED AT THIS POWER |
| C3 form-Y vs control | 0.217 [0.125, 0.333] (n=23) | 0.317 [0.150, 0.481] | **AGREES** |

**P43R.1: PARTIAL, as registered.** C2's point estimate (0.276) sits almost
exactly on the primary's (0.261); its CI reaches 0.520 only because 29
pairs were decisive. Nothing contradicts. But the registered standard is CI
placement, not point agreement, and softening a standard after seeing the
data is how verdicts rot — so C2 is reported in the registered category:
not replicated at this power, distinct from contradiction.

### Scope changes

- **The aggregation lift is TWO-FAMILY** (0.818 / 0.788). The paper's
  single-judge limitation on P43.1 is discharged.
- **The phrase penalty**: three of four judge-x-form cells exclude 0.5; the
  fourth agrees in point estimate. Limitation narrowed, stated as such.
- **Finding #14 hardened into a task-format property**: raw first-position
  preference 0.85–0.88 across four judges from four families; decisive
  rates 0.05–0.40. The bias magnitude is invariant; only the escape rate
  varies.

---

## TENSION-FATE AUDIT — registered scope (2026-08-13, before any judging)

**An AUDIT, descriptive and post-hoc; licenses no claim.** It measures the
headroom that would justify a lead-to-seat re-consultation cell: of the
tensions the lead itself names (391/396 archived runs carry a mandated
"## Tensions" section; zero runs ever consulted a seat twice), what
fraction are RESOLVED in the synthesis (a position taken, a number
adjusted, a recommendation sequenced because of it) versus ACKNOWLEDGED
(mentioned, unresolved) versus DROPPED (never addressed again)?

Protocol: seeded sample of 50 archived runs, every named tension in each;
two judges (gpt-oss:20b, qwen3-vl:30b-a3b — the two that parse reliably),
three-way label per tension against the full synthesis; gate G-E on the
judge prompt; unparseable replies quarantined, never defaulted. Headline
numbers come from BOTH-JUDGES-AGREE labels only; disagreement and
per-judge marginals reported.

**Scaffold caveat, stated in advance (finding #8-adjacent):** the synthesis
prompt ORDERS acknowledgment ("Acknowledge the tensions... at the points
where they bite"). High ACKNOWLEDGED rates are therefore partially
compliance with that order. RESOLVED is the number the scaffold does not
dictate, and headroom = 1 - RESOLVED is the audit's deliverable. The judge
task is unvalidated (no labeled tension-fate data exists); agreement is
reported and the numbers are bounds, not verdicts.

---

## TENSION-FATE AUDIT — RESULT (2026-08-13; descriptive, as registered)

160 tensions from all 45 cleanly-parseable archived runs; two judges; zero
quarantines; judge-judge agreement 0.719 (bar 0.70, marginal pass).

| fate (both-judges-agree, n=115) | share | 95% CI |
|---|---|---|
| RESOLVED | 0.800 | [0.718, 0.863] |
| ACKNOWLEDGED | 0.200 | [0.137, 0.282] |
| DROPPED | 0.000 | [0.000, 0.032] |

**Headroom (not resolved) = 0.200 [0.137, 0.282] on agreed labels.** The
disagreement is directional: qwen3-vl calls RESOLVED at 0.80, gpt-oss at
0.62 — so the honest range for headroom is **0.20 (agreement-filtered,
lower bound) to 0.38 (stricter judge)**. Uniform across list position;
nothing is ever dropped outright — the mandated tension list keeps every
tension alive at least as prose.

### What the audit can and cannot say

It CAN say: the lead takes a position on most of the tensions it names.
The re-consultation loop's opportunity among *visibly unresolved* tensions
is roughly one in five, at most one in three.

It CANNOT say whether those positions are WARRANTED. "Resolved" here means
a side was chosen, a number conditioned, a plan sequenced — and Cell 37
established the lead has no independent computational hold on content, so
a resolution can be fiat: picking a side without the information the
tension actually turns on. The audit has no warrant labels (the program's
standing gap), so the 0.80 RESOLVED rate is an upper bound on genuine
resolution, not a measurement of it.

### Consequence for the prospective re-consultation cell

The design lesson is sharper than the headroom number. A cell on NATURAL
tensions would spend 80% of its sample on tensions the lead already
"resolves," with no ground truth for whether the resolution was right. The
registrable design is PLANTED tensions with known correct resolutions —
where the deciding fact exists only in a seat, so fiat-resolution and
informed resolution are distinguishable by exact match (Cell 37's
machinery, host-coherent per finding #11). Outcome attainability for that
design is now computed: the fiat-vs-informed question applies to up to 80%
of tensions, not the 20% the naive headroom suggested. NOT registered; no
cell is triggered by this audit.

---

## CELL 44 PRE-REGISTRATION — orchestrator-routed re-consultation, design (c) (registered 2026-08-13, before items or runs)

Decision context: the tension-fate audit found the lead takes a position on
~80% of self-named tensions with no way to distinguish informed resolution
from fiat, and Cell 37 says the lead has no independent hold on content.
Design (c): the ORCHESTRATOR — never the lead's disposition — parses the
lead's own mandated tension list and mechanically dispatches a follow-up to
the implicated seat. This cell tests the LEAD-SIDE of the loop with
controlled clarifications; realistic seat-side answering is design (b)'s
follow-on, run only as needed.

### Two-stage lead, three arms, one factor

The lead is split into two stages in ALL arms (identical stage-1):
S1 reads contributions, writes ONLY the tension list; S2 writes the final
synthesis. Arms differ solely in what is appended between stages:

- **A-control** — nothing.
- **A-filler** — a dispatched "clarification" from the implicated seat that
  is responsive in style but contains NO deciding fact (restates round-1
  substance). Isolates the RITUAL of consultation.
- **A-informed** — the same-styled clarification CONTAINING the deciding
  fact F. Isolates the INFORMATION.

Filler and informed clarifications are length-matched within 15% and both
styled as the same seat. Trigger detection (did S1 name the planted
tension?) uses per-item frozen keyword containment — a known-value check —
identical in all arms; analysis conditions on trigger-named runs in all
arms (stage-1 is identical across arms, so conditioning is pre-treatment).

### Items — construction rules (frozen before authoring)

>= 6 items on existing cases. Each: seat A's contribution is appended with
position P_A; the implicated seat B's with conflicting position P_B;
NEITHER contains the deciding fact F. F settles the tension toward a known
resolution R (vs anti-R). **Host-coherence (finding #11): every appended
premise and F must be consistent with the case text — drawn from it where
numbers exist, never contradicting it.** Both resolutions must be natural,
distinguishable positions. A probe-collision guard refuses to run if any
resolution's keywords occur in the item's own appended premises.

### Instrument

Primary outcome per run: which position the final synthesis adopts —
R / anti-R / NEITHER — classified by the two proven judges (gpt-oss,
qwen3-vl), both required, agreement-filtered, quarantine-not-default;
agreement bar 0.70. Literal keyword adoption reported as a secondary lower
bound. Emission reported per arm (silence check).

### Gated pilot BEFORE the full run (checklist item 12)

Control-arm-only, 6 items x 2 repeats: gates (a) planted tension NAMED in
S1 >= 0.5 of runs; (b) synthesis adopts SOME side (R or anti-R) >= 0.4.
Either gate failing -> items redesigned before any arm runs; both failing
twice -> cell NOT RUN, reported.

### Predictions

- **P44.1 (information use — the estimand).** A-informed adopts R above
  A-control, cluster-bootstrap CI over items excluding 0. *Falsified if*
  not — meaning the lead cannot use even a directly-responsive
  clarification it asked for, and loop (c) dies at the lead.
- **P44.2 (ritual vs information).** A-informed adopts R above A-filler,
  CI excluding 0. *Falsified if* filler matches informed — consultation
  works as ritual, not information.
- **P44.3 (consultation-as-license, mandatory).** Decisive-adoption rate
  (either side) filler vs control, with CI: does mere consultation
  increase commitment without added warrant? No bar; reported.
- **P44.4 (mandatory).** Trigger-naming rate, routable rate, full 3-way
  outcome table per arm, judge agreement, quarantines.

### Full run

6 items x 3 arms x 6 repeats = 108 runs (216 lead calls + judging).
Goodhart clamp: dispatch-count and trigger rate are diagnostics, never
targets; no item or prompt may be tuned to raise them after the pilot.

---

## CELL 44 PILOT GATES (2026-08-13) — PASS; full run launched

Naming gate: 6/12 = 0.50 (>= 0.50) PASS, exactly at the bar — trigger
conditioning will cost roughly half the sample, as anticipated. Adoption
gate: the pilot's literal-keyword proxy read 0.33, below the 0.40 bar; the
registered instrument for adoption is the two-judge classification, which
reads **8/12 = 0.67** (5 R, 3 ANTI, 0 agreed-NEITHER, 4 disagreements, 0
quarantines). Gate evaluated on the registered instrument: PASS. The
proxy's shortfall is recorded rather than hidden; literal probes remain
the secondary lower bound they were registered as.

Two pilot observations carried forward: judge agreement on the 3-way
adoption label was 8/12 = 0.67 at pilot n — below the 0.70 bar; the full
measure computes it at n=108 and the bar applies there. And the control
arm leans R without the deciding fact (5 R vs 3 ANTI), so P44.1's
detectable headroom starts from an elevated baseline; the cluster
bootstrap handles this, and it is noted so a large control baseline is not
misread as information use.

---

## CELL 44 VERDICT (2026-08-13) — the loop works at the lead: P44.1 and P44.2 SUPPORTED

108 runs, arms balanced 36/36/36, zero failures, dispatch 22/22.
Trigger-named 37/108 = 0.34 (below the pilot's 0.50); by arm 15/15/7 —
stage-1 is identical across arms, so the informed arm's 7 is sampling
noise, and it left the estimand riding on unanimity. Unanimity arrived.

| arm (named runs) | R | ANTI | NEITHER | agreed/n |
|---|---|---|---|---|
| control | 5 | 3 | 0 | 8/15 |
| filler | 3 | 8 | 0 | 11/15 |
| informed | **7** | 0 | 0 | **7/7** |

- **P44.1 SUPPORTED** — informed 7/7 = 1.000 vs control 0.333, diff CI
  [+0.200, +1.000]. The lead USES a routed clarification it asked for.
- **P44.2 SUPPORTED** — informed 1.000 vs filler 0.200, diff CI
  [+0.545, +0.947]. It is the information, not the ritual.
- **P44.3** — filler decisiveness 0.733 vs control 0.533, CI
  [-0.167, +0.602]: suggestive of consultation-as-license, not established.

### The agreement-bar incident, recorded before the celebration

The measure stage printed SUPPORTED without enforcing the registered 0.70
agreement bar — the THIRD verdict-fires-without-its-precondition instance
(after the probe's sign test and C42's replication NOTE). Checked by hand:
agreement on the ANALYSIS population (named runs) is 26/37 = 0.703 —
marginal PASS; overall agreement is 0.583 — FAIL, driven entirely by
unnamed runs outside the analysis. Both numbers are recorded; the
population ambiguity in the registration is noted rather than resolved in
whichever direction flatters.

**The verdicts do not depend on the filter.** The informed arm has ZERO
judge disagreements (7/7 unanimous both judges). Resolving every
disagreement in the other arms adversarially AGAINST the predictions
still leaves control at 0.60 and filler at 0.47 vs informed 1.00. The
registered literal secondary agrees: informed 7/7 literal-R, control 7/15,
filler 5/15. Emission flat (8.6-10.1k chars).

### Two observations carried forward

1. **Filler shifted adoption toward ANTI** (8/15 vs control 3/15 agreed):
   contentless consultation did not merely fail to help — it nominally
   moved commitments. Unregistered observation; candidate hypothesis for
   any (b)-stage cell.
2. **The scarce resource is the trigger, not the effect.** Naming ran 0.34
   at full n against the pilot's 0.50. Any follow-on must raise
   tension-salience by REGISTERED redesign, never by tuning against this
   verdict (Goodhart clamp stands).

### Scope

Lead-side only, controlled clarifications, n=7 in the decisive cell, one
writer, six items. Design (b) — seat-initiated deferral with real seat
answers — is the registered follow-on and is NOT triggered automatically.

---

## CELL 45 PRE-REGISTRATION — design (b) stage one: seat-side deferral discrimination (registered 2026-08-13, before items or runs)

Design (b) is seat-initiated deferral: seats know the roster and may point
the lead at another seat. Cell 44 established the lead-side (a routed
clarification is used, 7/7). The remaining uncertainty is the SEAT side,
and its C41-shaped failure mode is registered up front: told they may
defer, seats will produce the deferral FORM; the question is whether the
flag DISCRIMINATES. Rate is not the estimand; the in/out gap is.

### Design — same question, different recipient

Reuses Cell 44's six frozen items, each with a deciding consideration
whose home domain is known (seat B). Per item, ONE decision-focused
sub-question, asked verbatim to two recipients:

- **OUT condition**: seat A (not the home domain) receives it. Correct
  behavior: flag `CONSULT: <domain>` naming seat B's domain.
- **IN condition**: seat B (the home domain) receives it. Correct
  behavior: answer without the flag.

Both recipients get the identical case text, identical sub-question, and
an identical roster-aware system prompt (roster ONLY — never sibling
outputs, per the v2 lane-bleed lesson recorded in council/prompts.py).
The deferral affordance is a structured token parsed literally; the ACT
is the outcome, so no judge is needed for the primary. 6 items x 2
conditions x 6 repeats = 72 seat calls.

**Authoring guard (frozen):** the sub-question must not contain any
domain word (healthcare/legal/finance/clinical/medical) — the seat must
infer where the deciding consideration lives, not read it off the prompt.

### Predictions

- **P45.1 (discrimination — the estimand).** Flag rate OUT > flag rate
  IN, cluster-bootstrap CI over the 6 items excluding 0. *Falsified if*
  not. Floor-floor = no deferral behavior; ceiling-ceiling = performative
  compliance (the C41 outcome); either falsifies. Any pattern is
  informative, so the design is self-attaining.
- **P45.2 (routing accuracy).** Among OUT-condition flags, the named
  domain is the deciding consideration's home domain above the 0.5
  two-alternative chance rate, CI excluding it. *Falsified if* seats flag
  but misroute.
- **P45.3 (mandatory).** Flag rates in both conditions; format-parse
  rate; answer emission alongside flags (a seat must not go silent when
  deferring — silence check); per-item breakdown.

### Consequence

End-to-end (b) — real seat follow-up answers replacing Cell 44's
controlled clarifications — is registered as the follow-on IFF P45.1 and
P45.2 both hold. If either falsifies, (b) dies at the seat, design (c)
stands as the working loop, and that is the recommendation.

Goodhart clamp: flag rate is never a target; no prompt may be tuned to
raise or lower it after this registration.
