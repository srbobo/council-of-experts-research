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
