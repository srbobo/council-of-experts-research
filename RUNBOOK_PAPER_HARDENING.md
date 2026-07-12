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
