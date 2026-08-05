# GST — Grounded Synthesis Training
## A framework for measuring and correcting epistemic distortion in lead–council architectures

**Status:** v1.2, 2026-08-05. Parameters in Part B re-estimated over the full
1,260-run population by the shipped kit (`gst/`), and the C5 sizing claim
corrected downward after measuring the independence assumption it rested on.
Restructured for generality in v1.1: Part A states the
framework as architecture-level hypotheses with **measurable system
parameters**; Part B reports our instantiation's measurements as *one data
point*, not as constants of the framework; Part C gives the intervention
menu keyed to mechanisms and parameterized by Part A's quantities; Part D
specifies cross-architecture validation and the publication path; Part E
states what would falsify the framework itself.

Scope: any pipeline in which upstream components produce prose consumed by a
final writing model ("lead–council" broadly: Mixture-of-Agents stacks,
planner/specialist/synthesizer systems, RAG-with-synthesis, multi-draft
aggregation). The framework is about the *writing step*; it is agnostic to
how upstream content is produced.

---

## Part A — The framework: three mechanism hypotheses and their parameters

The framework claims that epistemic distortion at a prose-aggregation step is
governed by three mechanisms, each with parameters that must be **estimated
per system** before any intervention is chosen. The parameters, not our
values of them, are the framework.

### A1. The shrinkage hypothesis

**Claim.** A writing model's emission of any countable epistemic property
behaves as a shrinkage estimator of "warranted level" rather than a
transducer of the supplied level:

```
y  =  w·s  +  c  + ε          0 ≤ w ≤ 1,  c ≥ 0
```

where `s` is the property's level in the upstream material, `y` its level in
the output, `w` the **evidence weight**, and `c` the **prior fill**
(= (1−w)·μ₀ under the normal-normal reading, with μ₀ the model's learned
prior for text of this register).

**System parameters to estimate:** (w, c), the fit's linearity, and their
per-property decomposition. Estimation requires only that the system log
upstream text — vary or stratify `s`, regress.

**Interpretation grid** (what parameter values mean for any system):
- `w → 1, c → 0`: faithful transduction; no intervention needed.
- `w < 1, c > 0`: compensating invention at low supply, trimming at high
  supply, discrimination compression by factor ≈ w + c/ȳ. Intervene per C.
- `c > 0` with `w ≈ 0`: pure register (output independent of input);
  the writer ignores upstream entirely.

**Root-cause claim (the part that generalizes):** shrinkage is not a defect
but the loss-optimal policy on any training distribution where
register/topic predicts the property. Therefore *no instruction and no
reward that leaves that correlation intact* should durably move w — a
falsifiable, architecture-general prediction.

### A2. The credit-dilution hypothesis

**Claim.** Sequence-level preference optimization fails to move a behavior
whose token span is a small fraction of the sequence, because the preference
margin Δ = Σ_t [log π(y_w,t) − log π(y_l,t)] is satisfiable off-feature.

**System parameter:** `f` = feature-span fraction (feature-bearing tokens /
total tokens). **Prediction:** behavioral transfer of sequence-level DPO/
ORPO/best-of-n distillation degrades with f; at small f, models exhibit the
*learning–acting dissociation* (preference/ranking metrics improve, emitted
behavior unchanged). Remedy effectiveness scales with how much of the margin
is forced on-feature (minimal pairs → all of it).

### A3. The exposed-detector (Goodhart) hypothesis

**Claim.** Any correction loop that (i) measures a behavior with an
instrument D having blind-spot rate ε and (ii) passes D's findings into the
policy's context, optimizes detectability rather than behavior — mass moves
into the blind spot because rephrasing is KL-cheaper than removal.

**System parameters:** the blind-spot vector (ε₁…ε_k) of the available
instruments, and their dependence structure. **Predictions:**
1. Feedback loops produce instrument-relative improvement with
   instrument-independent stagnation (measurable by any second instrument).
2. Selection (post-hoc conditioning of outputs, no information flow to the
   policy) cannot produce this signature. This is a sharp asymmetry any lab
   can test: same verifier, used two ways, opposite outcomes predicted.
3. Ensembling instruments with weakly dependent blind spots multiplies the
   evasion cost: P(joint evasion) ≈ Π εᵢ (dependence-adjusted).

### A0. Measurement preconditions (from the companion harness)

Parameter estimation is only meaningful under: per-run capture of verbatim
upstream text and the writer's actual prompt (execution-path assertion);
resolvable model identity per turn; floor guards and raw counts beside any
rate; two instruments for any verdict, with the feedback-generating
instrument barred from grading; empty instrument replies excluded, never
defaulted. These are stated as preconditions of the framework because each
was, in our instantiation, individually responsible for a wrong published
number.

---

## Part B — One instantiation: what we measured (evidence, not constants)

Our system: 4 open-weight models ≤20B (planner/3 specialists/writer;
variants with gpt-oss-20B, Phi-4-14B, Qwen2.5-7B writing), 7+11 authored
cases, 1,673 audited runs. Property class: four detectable epistemic
families (cutoff disclosure, modeled assumptions, jurisdictional
distinction, hedging) with a regex lexicon + calibrated NLI detector +
pairwise judges.

- **A1 instantiated:** re-estimated by the shipped kit over the full usable
  population — 1,260 runs, all arms, 4 writers:
  `y = 0.352·s + 0.540`, w ∈ [0.310, 0.391], c ∈ [0.437, 0.651] (2,000-draw
  bootstrap); R² 0.976 across supply strata, 0.140 across individual runs.
  Prior-trust ratio (1−w)/w = **1.84**. Supply→emitted: 0.40, 0.81, 1.32,
  1.62, 1.83. The earlier 493-run figure (0.393·s + 0.527) sits inside the
  new interval; the full-population estimate supersedes it. *These are one
  writer-family, one domain battery, one lexicon; the framework predicts the
  form, not the values.*
  The kit's linearity probe fires here (quadratic CI −0.085…−0.020, excludes
  zero) and labels itself: supply reaches 4 of 4 available families, so the
  concavity is a ceiling artifact of a bounded count, not evidence against
  A1. Widening the property class is the fix; reporting the flag is the duty.
- **A1 on a second property class (exploratory):** re-running the same 1,260
  runs under a source-attribution lexicon gives `y = 0.333·s + 0.701`,
  prior-trust ratio 2.00 — the same form on a property that is not hedging.
  Held as suggestive only: the linear fit is visibly poorer (strata R² 0.849,
  strongly non-zero quadratic term) and the strata are badly unbalanced
  (n=832 at s=1 against n=18 at s=3), because the battery was never designed
  to vary attribution supply. A purpose-built design is required before this
  counts as cross-property evidence.
- **A2 instantiated:** f = 0.068 median (p25 0.021, p75 0.137) over 1,260
  runs — a ~15:1 margin dilution. The mechanism is now measured directly
  rather than inferred: the kit's pair diagnostic scores the whole-sequence
  pair shape used in the failed training cells at **0.866 off-feature**,
  against **0.000** for programmatically constructed minimal pairs. Two
  training attempts showed the predicted dissociation exactly (preference
  accuracy 0.48→0.94, val loss 0.069; behavior unmoved), and three objective
  classes were null at 49–88 whole-sequence pairs.
- **A3 instantiated (corrected 2026-08-05 by program audit):** feedback loop
  quoting detector phrases: 0.88 removed by the exposed instrument, no change
  per the independent one — but the audit established the independent
  instrument had never detected the flagged families pre-gate (0/8), so it
  corroborated neither persistence nor removal. Manual inspection of the
  revisions grounds the finding now: qualification content survives in
  rewording on most intervened runs ("a modeled assumption" → "assumed by
  the Finance contribution"), and one flagged invention was the detector's
  own false positive (an action item matching the cutoff lexicon). The
  structural claim stands on inspection + the KL argument; the
  two-instrument corroboration story is withdrawn. The quoted ε_NLI ≈ 0.15
  (AUC 0.929) was calibrated for chosen-vs-rejected discrimination, NOT
  family presence — presence calibration is Cell 23, and until it ships the
  C3 ensemble arithmetic must not be quoted for this instrument pair
  (sweep finding #7: zero family-level agreement across 225 runs).
- **Boundary observation (candidate A4, weakest evidence):** instructions
  moved every surface behavior tested and did not move commitment
  (decisions ~3/10 judge-recognized under an explicit instruction; zero
  overrules in 45). We flag "surface vs stance" as a hypothesis for
  cross-architecture testing rather than a framework claim; it rests on one
  writer and contested judge instruments.

Known limits of this instantiation, stated so others don't inherit them
silently: authored cases (not sampled from a task distribution); one
orchestrator implementation; lexicon tuned to legal/medical/finance prose;
all writers ≤20B; linearity checked over s ∈ [0,4] only; judge reliability
poor at item-level absolute labeling.

---

## Part C — Intervention menu, keyed to mechanisms, parameterized

Each intervention is chosen by measured parameters, not by default.

### C0. Diagnose first (always)

Estimate (w, c) via supply regression; f via span measurement; (ε₁…ε_k) via
held-out probes per instrument; p₀ = P(clean sample) at the worst-case
supply stratum. The companion harness computes all four from logged runs.

### C1. Counterfactual corpus → retraining (targets A1; use when w ≪ 1 and training is available)

Construct matched evidence variants of the *same* tasks spanning the supply
range (ablate/inject the property in upstream text — programmatic wherever
upstream is logged prose), with references satisfying `Q_out = Q_in`.
Within-corpus, register/topic no longer predicts the property; transduction
becomes the Bayes-optimal policy (w* = 1, c* = 0 minimizes loss **on the
constructed distribution** — the claim is about the training signal, not a
guarantee of transfer, which is what the held-out evaluation tests).
Generalization requirements: property must be detectable enough to ablate/
inject cleanly; scale target ≥10³ items (programmatic, so cheap in any
logging pipeline).

### C2. Minimal-pair, feature-masked preference optimization (targets A2; use when f is small — i.e., almost always)

Pairs byte-identical outside the feature span; loss masked to the span. This
makes 100% of the margin on-feature regardless of f. Architecture-general
recipe: diff-derived masks require no tokenizer-specific machinery beyond
span alignment.

### C3. Policy-blind ensemble reward RL (targets A1+A3 jointly; use when RL infra exists)

Reward = consensus of instruments with measured weakly-dependent ε's;
**no reward-derived text in the policy context, ever**; adversarial refresh
of instruments from consensus-pass/judge-fail mining. Expected evasion cost
Π εᵢ. Note the infra constraint that bit us: naive GRPO materializes
seq×vocab logits; use logprob-gather implementations or larger hardware.

### C4. Conditional activation steering (targets A1's mechanism directly; use when residual-stream access exists)

From C1's matched variants, estimate directions e (evidence present−absent)
and c⃗ (property expressed−not) per layer; gate expression on evidence:
`h → h − proj_c⃗(h)·(1 − σ(⟨h,e⟩/τ))`. Sharp parameterized prediction: the
supply regression under steering moves (w→1, c→0). Requires white-box
serving; not available for API-only writers — stated as a scope boundary,
not a footnote.

### C5. Verifier-blind best-of-n selection (targets A3-safely; universal — works on black-box writers, deployable without training)

Sample n, select by ensemble consensus, never reveal selection reasons.
Residuals are annotated (disclosure), never revised (A3 prediction 1).

**Correction, and the reason the kit exists.** v1.0 of this document sized
selection from the independence formula `P_clean(n) = 1 − (1 − p₀)^n` and
claimed ~96% clean at n=3. Building the estimator forced the assumption into
the open, and measuring it refutes it. Over real repeated runs of the same
task under the same configuration, the empirical curve at the worst supply
stratum is **0.562 / 0.727 / 0.827** at n = 1/2/3, against the formula's
**0.597 / 0.838 / 0.935**. Redraws are positively correlated: a writer that
invents on a given task tends to invent again on a redraw, so selection buys
materially less than independence predicts. Sizing from the formula would
have under-provisioned by roughly a full sample.

The corrected statement: at the worst supply stratum n=3 delivers ≈0.83
measured, and reaching 0.95 requires n≥4 on a basis the data cannot yet
confirm (beyond n=3 fewer than half the cells contribute, so those points
describe a different and easier subpopulation). Adopters must recompute from
their own p₀ **and their own empirical curve**; the kit reports both curves
side by side, with per-n cell counts, and refuses to size from unrepresentative
points. Latency multiplier ≈ 1 + (n−1)·(t_sample/t_pipeline) when sampling
serially, ≈1 when sampling concurrently.

**Decision rule summary:** black-box writer → C5 (+disclosure). Training
access, small budget → C1+C2. Residual-stream access → add C4. RL infra →
C3 last, gated on C1/C2 results.

---

## Part D — Cross-architecture validation and publication path

The framework is published as claims-with-parameters plus a measurement kit,
validated by instantiating on systems we did not build:

1. **Replication targets (minimum three, chosen for diversity):** an
   off-the-shelf Mixture-of-Agents stack (homogeneous frontier-API models —
   tests scale and black-box limits; C4 unavailable there by design); a
   LangGraph/AutoGen multi-agent app with tool use (tests the framework
   where upstream is not purely prose); a RAG-summarization pipeline (tests
   the property class swap: citations/attribution rather than hedging).
2. **Per-target protocol:** estimate (w, c, f, ε⃗, p₀) with the harness →
   pre-register the A1–A3 predictions for that system → run C5 (universal)
   and whichever of C1–C4 the access level permits → publish parameters and
   outcomes regardless of direction.
3. **Property-class generality:** repeat with a second property class
   (attribution accuracy, numeric-provenance) to show the framework is not
   about hedging specifically. The lexicon is a plug-in; the calibration
   procedure (construction-labeled pairs → thresholds) ships with the kit.
4. **Publication shape:** (i) framework paper — mechanisms, parameters,
   estimation kit, one full instantiation, N external replications of the
   *measurements*; (ii) intervention results as follow-up once C1/C2 runs
   exist on ≥2 systems. Negative intervention results are publishable under
   the framework because the failure pattern is diagnostic (see Part E).

Artifacts (built — `gst/`, installable as `gst-kit`, MIT, zero dependencies
in the core): parameter estimators with identifiability guards
(`gst.measure`), the parameter card (`gst.card`), adapters for MoA,
LangGraph, AutoGen, RAG, and arbitrary JSONL via a declarative field map
(`gst.adapters`), verifier-blind selection whose signature makes a feedback
channel a `TypeError` (`gst.select`), the counterfactual-corpus constructor
with a decorrelation check (`gst.corpus`), the minimal-pair generator, pair
diagnostic, and masked-loss recipe (`gst.pairs`), execution-path assertion
(`gst.path`), a pre-registration template carrying the two-instrument and
path-assertion rules, a `gst` CLI, and 39 tests including 8 golden tests that
reproduce this program's parameters from its own 1,260-run ledger.

The kit is deliberately adversarial toward its own author: on first run
against our data it flagged the ceiling artifact, refused to size selection
from unrepresentative points, and produced the best-of-n correction recorded
in C5 above. Two defects in the estimators themselves were caught the same
way — an empirical curve compared against a worst-stratum prediction it was
not drawn from, and a pair diagnostic measuring bare marker spans while the
loss mask covered whole sentences, which would have told every user their
correct minimal pairs were 90% diluted.

---

## Part E — What would falsify the framework

Stated so that the framework is a scientific object, not a lens:

- **A1 falsified** by a lead–council system whose supply regression is
  strongly non-linear in a way no monotone estimator reading survives, or a
  system with c ≈ 0, w ≈ 1 under a writer trained on ordinary text (i.e.,
  faithful transduction arising without intervention).
- **A2 falsified** by sequence-level preference training moving a small-f
  behavior at modest dose (would show credit dilution is not the binding
  mechanism — our identification claim, not just our dose claim, would be
  wrong).
- **A3 falsified** by a feedback loop whose improvement survives an
  independent instrument, or by selection producing instrument-relative
  improvement that a second instrument contradicts (the selection-safety
  asymmetry is the framework's cleanest falsifiable claim).
- **The framework is weakened, not refuted,** if parameters prove unstable
  within a system (w varying wildly across prompts of the same supply) —
  that would demand a distributional rather than scalar treatment.

Our own prior, earned over 21 cells: expect nulls, register consequences
before running, and treat the pattern of failures as the finding.
