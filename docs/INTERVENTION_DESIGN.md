# GST — Grounded Synthesis Training

**Status:** design v1.0, 2026-08-05. An intervention against the three
systematic failures measured in this program: compensating invention,
probabilistic erring toward caution, and adversarial bypass of instrumented
instruction. Every component is derived from a formalized failure mechanism;
nothing is a technique for its own sake.

---

## 1. The three failures, formalized from our data

### 1.1 The writer is a shrinkage estimator, not a transducer

Let `s = |Q_E|` be the number of qualification families the specialists
raise, and `y` the number in the final answer. Pooled over 493 runs, 12 arms,
4 writers:

```
s:      0     1     2     3     4
y:    0.46  0.92  1.41  1.76  2.01
OLS:  y = 0.393·s + 0.527        (R² of the 5 cell means ≈ 0.99)
```

This is precisely the posterior-mean form of a normal-normal Bayesian
estimator: if the writer treats observed seat caution `s` as noisy evidence
of "warranted caution" θ with prior θ ~ N(μ₀, τ²),

```
E[θ | s] = w·s + (1−w)·μ₀ ,   w = τ²/(τ²+σ²)
```

Measured: **w = 0.39**, prior-fill `(1−w)·μ₀ = 0.53`. The writer weights its
prior **1.54×** more than the evidence. Every headline pathology is a
corollary:

- **Invention** = the prior-fill term dominating when `s` is small
  (measured invention: 0.53 at s=0 → 0.00 at s=4).
- **Erring toward caution** = shrinkage toward μ₀ > 0: the model was trained
  on text where answers of this register carry caution, so caution is
  *predictive* and the prior is doing its statistical job.
- **Discrimination compression** = slope < 1: the seats' 2.6× distinction
  exits at 1.8× because y compresses toward μ₀ from both sides.

**Root cause:** in the model's training distribution, topic/register predicts
qualification level, so a prior-weighted estimator is *loss-optimal*. The
model is not misbehaving; it is generalizing correctly from a world where
the prior works. No instruction changes what is loss-optimal.

### 1.2 The learning–acting dissociation is a credit-assignment failure

Twice (Cells 11, 18) the model *learned* the preference (accuracy 0.48→0.94;
val loss 0.069) with zero behavioral change. The mechanism is visible in the
loss. Sequence-level preference objectives (DPO/ORPO) optimize a margin

```
Δ = Σ_t [log π(y_w,t | ·) − log π(y_l,t | ·)]
```

summed over **all** tokens. We measured the feature-bearing span: sentences
containing qualification markers are a **median 10%** of completion
characters (p25 5%, p75 18%). So ≥ ~90% of the margin's token mass is
style/content covariates. A margin M is achievable by distributing per-token
log-prob shifts of order `M / (0.9·N)` across non-feature tokens — minute
stylistic adjustments — while the feature-conditional distribution
`π(qualification | evidence)` stays fixed. The optimizer takes the cheap
path; the ranking is learned (the margin exists) and the behavior is not
(the feature distribution never moved). Our pair construction made this
worse: best-vs-worst whole samples differ in style, length residue, and
family concentration — a rich supply of off-feature margin.

### 1.3 Evasion is Goodhart's law with an exposed detector

Cell 19: feedback quoted the detector's matched phrases; the revision
removed **0.88** families by the detector's own count and **0.00** by an
independent instrument. Formally, with detector D having blind-spot region B
(paraphrases invisible to D), the revision objective

```
max_π  E[ 1 − D(A) ]   s.t. small KL(π ‖ π₀)
```

is optimized by moving probability mass *into B*, not by removing the
behavior — strictly cheaper in KL, since rephrasing is a smaller
distributional move than deletion. Exposing D's features in-context hands
the policy a map of B. The structural fix is information-theoretic, not
detector quality: **the policy must have no channel from D** (selection
conditions the *output*; feedback conditions the *policy input* — only the
latter enables evasion learning), and the measurement must ensemble
instruments with near-disjoint blind spots.

### 1.4 Why weight training failed at our scale

Three objective classes moved nothing. Under §1.1, the target is not a
surface emission habit but the estimator weight `w` — a property of how
evidence is read, implemented diffusely in attention. A rank-8 LoRA over 16
layers driven by 49–88 whole-sequence pairs is underdetermined for that
circuit: the gradient's projection onto "increase w" is diluted by §1.2 and
starved by dose. Prescription: fix identification (minimal pairs, token
masking), then scale dose 30–100× (counterfactual pairs are programmatic,
so thousands are cheap), then add capacity (r ≥ 64 or full-rank on the
final quarter of layers).

---

## 2. Design principles (each mapped to a mechanism)

| Principle | Kills | How |
|---|---|---|
| D1. Decorrelate the prior | §1.1 | training data in which topic/register does **not** predict Q; only Q_E does |
| D2. Localize credit | §1.2 | minimal pairs differing only in feature spans + token-masked loss |
| D3. Blind the policy to instruments | §1.3 | rewards/selection computed post-hoc; detector output never in context, never quoted |
| D4. Ensemble semantically | §1.3 | regex ∧ NLI ∧ embedding; consensus counting; adversarial refresh |
| D5. Selection over feedback | §1.3 | best-of-n conditions outputs, not the policy |
| D6. Dose and capacity floors | §1.4 | ≥2,000 pairs; r ≥ 64 / partial full-rank; register before running |
| D7. Two-instrument verdicts, path assertion, pre-registration | our own audit history | unchanged |

---

## 3. The intervention: five stages

### Stage 0 — Counterfactual corpus (the causal core; kills the prior)

From the 1,130 archived synthesis contexts: for each case, construct matched
evidence variants by **programmatic ablation/injection of seat-attributed
qualification sentences**, spanning s = 0…4 *for the same case content*.
Reference syntheses A\* are template-assembled so that `Q_{A*} = Q_E`
exactly, then judge-filtered pairwise (per our validated judge protocol).

Effect on the learning problem: within the corpus,
`Corr(topic, Q_target) = 0` and `Q_target = Q_E` deterministically. The
Bayes-optimal qualification channel under MLE is then `w = 1, prior-fill =
0` — faithfulness stops costing likelihood and starts earning it. Shrinkage
was optimal statistics under the old distribution; this makes transduction
the optimal statistics.

Scale: 108 contexts × ~5 evidence variants × 2–4 templates ≈ **2,000–4,000
items** — 30–100× the dose of every failed attempt, constructed without
model generation in the loop.

### Stage 1 — Minimal-pair, token-masked preference optimization (kills margin dilution)

Pairs: chosen = A\*; rejected = A\* with one qualification span injected
(invention) or deleted (unfaithful drop). **Chosen and rejected are
byte-identical outside the feature span** — length ratio 1.00, zero style
covariates. Loss: DPO/ORPO computed **only over masked feature tokens**:

```
Δ_masked = Σ_{t ∈ M} [ log π(y_w,t) − log π(y_l,t) ] ,  |M|/N ≈ 100% of Δ
```

With minimal pairs the two changes are redundant safeguards: even unmasked,
all margin lives in the feature span; masked, the gradient cannot leak
elsewhere. This is the direct repair of the dissociation: the only way to
satisfy the loss is to move `π(qualification | evidence)`.

### Stage 2 — Policy-blind ensemble-reward RL (optional; the scale bet)

GRPO/RLOO on the Stage-0 prompt distribution with reward computed post-hoc:

```
R(A | E) = β·|Q̂_A ∩ Q̂_E|  −  α·|Q̂_A \ Q̂_E|_consensus  −  guards
```

where `\_consensus` counts a family as invented only if ≥2 of {regex, NLI,
embedding-grounding} agree, and **no reward-derived text ever enters the
policy context**. Evasion cost under the ensemble: with single-instrument
evasion rates measured/estimated at `ε_regex ≈ 0.88 (demonstrated)`,
`ε_NLI ≈ 0.15 (FNR at Youden, AUC 0.929)`, `ε_emb ≈ 0.3 (assumed, to be
calibrated)`, joint evasion under weak dependence ≈ `0.88·0.15·0.3 ≈ 0.04`
— a ~20× harder target than any single instrument, with adversarial refresh
(mine consensus-passing/judge-failing outputs → extend instruments) making
it a moving target. Infrastructure note: our measured Metal OOM was the
`seq × vocab` logits materialization; a fused log-softmax-gather (per-token
logprob only) or a rented A100 is a prerequisite. Registered as the last
stage to run, not the first.

### Stage 3 — Conditional activation steering (attacks stance directly)

Stage 0's matched variants give, for free, activation pairs differing only
in evidence-of-uncertainty. Compute difference-in-means directions per
layer: `e` (evidence present−absent) and `c` (caution expressed−not). At
inference, gate caution on evidence in the residual stream:

```
h  →  h − proj_c(h) · (1 − σ(⟨h, e⟩/τ))
```

i.e., attenuate the caution direction exactly when the evidence direction is
absent. This bypasses token-level credit assignment entirely and operates on
the mechanism §1.1 locates (the estimator, not the surface). Runs on our MLX
stack; the steered writer serves the pipeline directly. Validation: the
dose-response slope under steering should approach 1 with intercept → 0 —
a two-parameter prediction from a one-parameter intervention.

### Stage 4 — Verifier-blind best-of-n (deployable immediately; no training)

Sample n syntheses; select the one passing ensemble consensus; **never
reveal selection reasons to the model** — selection is post-hoc conditioning
of the output distribution and, unlike feedback, carries no information
channel into the policy (the generator cannot learn to evade a signal it
never observes; Cell 19's failure mode is structurally absent).

Measured basis: at low supply (s ≤ 1, n=94 runs), empirical
`P(zero invention) = 0.66` per sample (Poisson e^{−0.35} = 0.70, consistent).
Clean-output probability under selection:

```
P_clean(n) = 1 − (1 − 0.66)^n :   n=2 → 0.88,  n=3 → 0.96,  n=4 → 0.987
```

Cost: +85 s per extra sample against a 381 s council run → n=3 ≈ **+45%
latency for ~96% clean at the worst-case supply level**, and cheaper at high
supply where the base rate is already ~0.9+. Residual non-clean outputs are
annotated, never revised (Cell 19).

---

## 4. Evaluation protocol and registered predictions

All stages evaluated under the standing rules: pre-registration with
git-precedence, path assertion per run, two-instrument verdicts with the
feedback-generator barred from grading, empty replies excluded, judge work
pairwise-only, ≥2 questions per condition level, raw counts and zero-rates
beside every rate.

Headline predictions (to be formally registered per stage before running):

- **P-S4** (first, cheapest): best-of-3 selection reduces measured invention
  on thin-supply cases from 0.53 to ≤ 0.15 families under BOTH regex and
  NLI, with preservation unchanged. Falsified if NLI disagrees with regex on
  the improvement (selection-Goodhart, which D5 argues cannot occur — this
  is the design's own falsifiable claim).
- **P-S0/S1**: after minimal-pair training at ≥2,000 pairs, the
  dose-response refit gives **w ≥ 0.7** (from 0.39) with intercept ≤ 0.2
  (from 0.53), on held-out cases, both instruments. Falsified if w moves
  < 0.15: identification was not the binding constraint either, and the
  stance claim hardens to "resists even identified, dosed training."
- **P-S3**: steering moves slope/intercept in the predicted direction with
  coherence intact (judge-checked); falsified if caution attenuation damages
  preserved qualifications (proj_c is not selective).

Expected-failure honesty: our prior for any single stage is a null. The
design's value is that each stage attacks a *different* formalized
mechanism, so the pattern of which stages fail is itself diagnostic: if
Stage 0/1 fails but Stage 3 works, the prior lives in inference-time
processing, not weights; if everything fails but Stage 4, disposition is
unfixable and only selectable — which would be the strongest version of the
paper's boundary claim yet.
