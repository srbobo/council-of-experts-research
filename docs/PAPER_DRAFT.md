# The Last Writer Wins: Installing Epistemic Disposition in Multi-Agent LLM Pipelines

**Sam Bobo** — draft v0.1, 2026-07-13. Target: arXiv cs.CL.

## Abstract

Multi-agent LLM pipelines route work through specialist models and
aggregate their outputs through a synthesizer. We study *disposition* —
what a model chooses to emit independent of what it knows, operationalized
as five epistemic behaviors (training-cutoff disclosure, modeled-assumption
flagging, precise vocabulary distinctions, jurisdictional distinguishing,
and hedging) — and ask where disposition in a pipeline comes from and
whether it can be installed. Across 300+ audited runs of a four-model
"Council of Experts" on consumer hardware, we find: (1) the pipeline
architecture itself lifts disposition density 3–9× over single-shot use,
model-agnostically, and *amplifies* under simultaneous behavioral demand
where single-shot *dilutes*; (2) attempts to install disposition into a
specialist seat by prompting or by supervised fine-tuning on behavior-rich
exemplars produce large seat-level lifts (≈2×, bootstrap CIs excluding
baseline) that are indiscriminate — both hedge on a trigger-free control
case — and that vanish from the pipeline's final output; reference-free
preference optimization (ORPO) on content-controlled pairs installs no
measurable magnitude at our dose but is the only mechanism that *improves*
responsiveness, suppressing unwarranted hedging below the untrained
baseline; (3) the mechanism is not sentence-level content entanglement
(refuted, r = −0.10) but a **synthesizer register**: each aggregator model
writes at its own characteristic disposition density, nearly independent
of seat input — over-dense input can *invert* output density — while the
synthesis prompt's preservation instructions act as a gain control
(removing them collapses output density 2–5× across all three synthesizers
tested). Practically: a pipeline's epistemic posture is governed by its
last writer and that writer's instructions; upstream installation is
mostly futile. All experiments are pre-registered, $0-budget, and fully
reproducible on a single 32 GB consumer machine.

## 1 Introduction

Production LLM systems increasingly take the form of pipelines: multiple
models, often specialized, whose outputs are aggregated by a final model
into the answer a user sees. Evaluation practice, however, remains largely
single-model: we measure whether *a model* hedges appropriately, discloses
its limits, or labels assumptions. This paper asks what happens to those
behaviors *inside a pipeline* — who originates them, whether they can be
installed, and whether they survive aggregation.

We distinguish two evaluation axes that are conflated in practice.
**Content** is whether the right substantive material appears (measured
here by per-case expert rubrics). **Disposition** is what a model chooses
to emit about its own claims. Our experiments show these axes are
orthogonal — the model family that wins content loses disposition and
vice versa — and that pipeline disposition is governed almost entirely by
the final aggregation stage.

Contributions: (i) a two-axis evaluation of a heterogeneous local
specialist pipeline, with a composite disposition metric (CDS) and an
architectural lift ratio (ALR); (ii) a controlled comparison of three
mechanisms for installing disposition into one pipeline seat — prompting,
exemplar SFT, and reference-free preference optimization — under
pre-registered predictions, with a trigger-free control case that
separates *responsive* from *habitual* behavior; (iii) identification and
ablation of the **synthesizer register** as the mechanism governing which
installed behaviors reach the pipeline's output; (iv) a fully local, $0,
consumer-hardware protocol with append-only audit logs for all 300+ runs.

## 2 Related work

**Multi-agent orchestration.** Debate and role-played collaboration
improve factuality and reasoning (Du et al. 2023; Mixture-of-Agents, Wang
et al. 2024; MedAgents/MDAgents), and recent work compares orchestration
against the strongest single model (Tian et al. 2025) or trains
orchestrators end-to-end (MAS-Orchestra, Ke et al. 2026). This literature measures content outcomes; we measure
what orchestration does to epistemic behavior, and find an amplification
effect independent of the model filling the seats.

**Specialists vs generalists.** Evidence is mixed on whether small domain
fine-tunes beat larger generalists in-domain (Trident-Bench, a safety-focused benchmark, Hui et al. 2025;
domain-FT vs RAG comparisons at 4B scale, 2026). Our content results replicate the negative side
(a 20B open MoE outperforms a four-specialist council 42% → 25–31% on
rubric coverage) and motivate the pivot: the surviving specialist value is
dispositional, not informational.

**Uncertainty expression and abstention.** Verbalized uncertainty (Lin et
al. 2022), linguistic calibration (Mielke et al. 2022), knowing-what-you-
know (Kadavath et al. 2022), abstention training (R-Tuning 2024) and
recent confidence-aware abstention work (I-CALM 2026; BAS 2026) train and
evaluate single models end-to-end. We add the pipeline dimension: a seat's
trained uncertainty behavior must survive an aggregator, and mostly does
not.

**Preference optimization for behavior.** DPO (Rafailov et al. 2023) and
ORPO (Hong et al. 2024) are standard for style/behavior shaping; DPO's
length bias is documented (Park et al. 2024), which our pair-construction
controls address. Comparisons of system-prompt steering vs preference
training exist for single models; we compare them *through* a pipeline.

## 3 Apparatus

**Council.** Four local models via Ollama on a 32 GB MacBook Air M5:
Phi-4-14B Lead (planner + synthesizer), and three specialist seats —
Llama3-Med42-8B (healthcare), Saul-7B-Instruct-v1 (legal),
Qwen-Open-Finance-R-8B (finance), all Q4/Q8 GGUF. The Lead performs
step-back decomposition (Zheng et al. 2024) and dispatches self-contained
sub-questions; seats never see the original query (this architectural
choice, not prompt strengthening, eliminated cross-domain lane bleed at
sub-10B scale). The Lead then synthesizes under a structurally enforced
Tensions-then-Synthesis prompt containing four PRESERVE instructions.

**Cases.** Seven three-domain scenarios: five failure-mode-targeted
(synthesis stress, jurisdictional vocabulary, quantitative discipline,
recency honesty, adversarial cross-domain tension) plus a matched
disposition pair — case 6 (*trigger-heavy*: demands all five behaviors
simultaneously) and case 7 (*trigger-light*: an organizational-strategy
question warranting none). Case 7 is the **responsiveness gate**: any
arm emitting disposition there is behaving habitually, not responsively.

**Scale.** 251 imported, audited runs at time of writing (append-only
JSON, one file per run, each carrying per-phase inputs/outputs/backends);
all inference via Ollama on one fanless M5 MacBook Air, 32 GB unified
memory, 26.8 GB Metal working set. Runs are nondeterministic across
repeats even at temperature 0 (runtime batching); we treat repeats as
seeds and report bootstrap intervals.

**Metrics.** Behavior density = pattern-matched occurrences of the five
behavior families per 1,000 characters. CDS = density × √(distinct
behaviors/5). ALR = council density / matched single-shot density.
Seat-level density is computed on the specialist's own turn from the
audit log; final density on the synthesized output. (Definitions and
regexes are versioned with the code; limitations §8.)

**Installation arms** (legal seat, single-variable design, seed 42):
A′ = conversion-control baseline (identical Saul weights through our
fp16→GGUF→Q4 pipeline); B = a frozen behavior-spec addendum on the seat's
system prompt (five behaviors, one example each, an explicit "do not
force it" clause); SFT = LoRA on 91 behavior-rich *chosen* responses;
ORPO = LoRA reference-free preference optimization on the same 91 chosen
responses paired with behavior-stripped rejections. Pairs are
content-controlled (chosen/rejected are rewrites of the same base
answer), length-ratio filtered (0.8–1.4) against length bias, overlap-
filtered (Jaccard ≥ 0.35 on capitalized tokens), and leakage-screened
against all seven cases. All protocol amendments were documented before
training; predictions were pre-registered before each cell ran.

## 4 Result 1: architecture shapes disposition

Across seven cases, council configurations emit 3–9× the behavior density
of matched single-shot baselines. Aggregate CDS: specialists-v2 0.928,
Opus-as-council 0.669, specialists-v1 0.584, gpt-oss-as-council 0.460,
Opus single-shot 0.159, gpt-oss single-shot 0.099. ALR: Opus pair 2.99×,
gpt-oss pair 3.91×, local v1 5.14×, upgraded v2 8.77× — the synthesis prompt's
preservation scaffold does real work even with no specialist alignment in
the seats. Under the trigger-heavy case the asymmetry sharpens: council
modes rise to 1.66–1.82× their per-case baseline while single-shot falls
to 0.68× — orchestration *amplifies* disposition under simultaneous
demand where a single context *dilutes* it. On the trigger-light case
every mode, specialist or frontier, emits zero: measured disposition is
responsive, not habitual, across the board.

## 5 Result 2: installing disposition — magnitude vs responsiveness

At n = 5 seeds per cell (140 runs, bootstrap 95% CIs):

| Arm | Seat density | Final-output CDS | Trigger-light gate |
|---|---|---|---|
| A′ baseline | 0.89 [0.69, 1.11] | **0.86 [0.64, 1.08]** | 0.96 |
| Prompting | **1.85 [1.42, 2.32]** | 0.59 [0.40, 0.81] | 3.03 ✗ |
| SFT-on-chosen | **1.77 [1.46, 2.09]** | 0.58 [0.43, 0.73] | 1.21 ✗ |
| ORPO | 0.87 [0.60, 1.17] | 0.66 [0.49, 0.85] | **0.15 ✓** |

Prompting and SFT install real seat-level magnitude (CIs exclude
baseline) — and both fail the gate, hedging on the trigger-free case
(prompting despite its explicit "do not force it" clause). Both also lose
their gains at the pipeline output: final CDS lands at or below the
untrained baseline. ORPO at this dose installs no significant magnitude;
its effect is qualitative — it is the only arm that *suppresses*
unwarranted hedging below baseline while leaving trigger-case behavior
intact and imposing no content tax (rubric coverage identical to A′).
Two further details. First, prompting was tested at two loci: on the
generalist single-shot (a 6× final-output lift, 0.099 → 0.589, that
failed the gate at 0.985 — its answer to the hybrid-work
communication question opened a section "Current State Snapshot (as of
my training data)" and closed with "actual results may vary": disclosure
theater where nothing warranted disclosure) and on the seat (the table above).
Second, content is unaffected by successful installation: rubric
coverage is 12/36 for both A′ and ORPO (9/36 for the original
production seat) — no content tax. Gate cells use n = 4–5 (the planner
routes no specialists on the trigger-light case in some runs; routing
variability is itself Ollama-runtime nondeterminism at temperature 0).
Summary: *prompting and exemplar training change what a model says;
preference training changes when it says it.*

## 6 Result 3: the synthesizer register

Why do installed behaviors vanish? A pre-registered entanglement
hypothesis — content-woven markers survive aggregation, detached
boilerplate is stripped — was **refuted**: entangled share is flat across arms (baseline 56%,
prompting 61%, ORPO 61%, SFT 67% — SFT's markers are the *most*
content-woven yet retain worst), retention splits by arm not position
(baseline 1.08, ORPO 0.96 vs prompting 0.49, SFT 0.49), and entanglement
does not predict retention (r = −0.10 over 102 runs). Notably the
refuted hypothesis and the overturned PRESERVE prediction (below) were
both pre-registered — we report them as part of the record.

A 72-run ablation (2 input arms × 3 synthesizer models × PRESERVE
instructions on/off × 6 cases) located the mechanism:

| Synthesizer | PRESERVE, base seat | PRESERVE, 2–3× hot seat | no-PRESERVE, base | no-PRESERVE, hot |
|---|---|---|---|---|
| Phi-4-14B | 1.17 | 0.61 | 0.52 | 0.31 |
| gpt-oss-20B | 0.63 | 0.86 | 0.20 | 0.13 |
| Qwen2.5-7B | 1.24 | 1.06 | 0.24 | 0.62 |

Each synthesizer writes at its own characteristic density band regardless
of input (registers are writer-specific); over-dense input does not
transmit and can *invert* output density (Phi-4: 1.17 → 0.61 —
over-correction, saturated hedging read as stylistic noise); and the
PRESERVE instructions are a **gain control**, their removal collapsing
output 2–5× on every synthesizer (overturning our registered prediction
that instructions would not matter). Mechanism: *final disposition ≈
f(register × instructions), nearly independent of seat input. ORPO
"survives" by staying inside the register; prompting and SFT "strip" by
exceeding it.*

## 7 Background: why disposition, not content

The council was built to test whether small domain fine-tunes beat
generalists on content. They do not: a single 20B open-weights MoE
(gpt-oss-20B) outperforms the full council on rubric coverage (42% vs
25%; 31% after best-available specialist upgrades), and the council
exhibited classic small-model failures (confabulated trial citations,
repealed regulation treated as live). What specialists retained was
disposition — the highest CDS of any configuration — which motivated the
installation question this paper answers. We report this as motivating
context, not a contribution.

## 8 Limitations

Pattern-based scoring has paraphrase blind spots and rewards concision
(per-character normalization); a judge-validated and per-claim-normalized
replication is planned. ORPO substitutes for DPO due to a memory defect
in the only local DPO trainer available (documented); claims are scoped
to reference-free preference optimization. One trained seat, one base
model (Mistral-7B-v0.1, weakly aligned), 91 pairs (a 2.7× dose-response
run is in progress), n = 5 seeds, seven self-authored cases, and three
local synthesizers ≤ 20B — frontier aggregators untested. All experiments
ran on one consumer machine at $0 API cost; we regard the reproducibility
this buys as partial compensation for the scale it forgoes.

## 9 Conclusion

In multi-agent pipelines, epistemic disposition is not additive across
stages: it is set by the last writer's register and that writer's
instructions. Upstream installation by prompting or exemplar tuning
produces loud but indiscriminate behavior that the aggregator strips;
preference optimization produces quiet, responsive behavior that
survives by conformity. Builders who want calibrated pipelines should
tune the synthesizer's instructions and choose the final model
deliberately — and evaluate disposition at the pipeline's mouth, not the
seat.

## Reproducibility

All code, prompts, 251+ imported audited runs, pre-registrations,
protocol amendments, verdicts (including refuted hypotheses), the
99-pair dataset, LoRA adapters, and regeneration scripts:
github.com/srbobo/council-of-experts-research. Glossary of all terms:
RUNBOOK_PAPER_HARDENING.md.


## Appendix A — Glossary

- **Seat**: one specialist model in the council, answering only its
  dispatched sub-question (e.g., Saul-7B = the legal seat).
- **Synthesizer / Lead**: the model that receives all seat outputs plus
  the original question and compresses them into the final answer — the
  pipeline's last writer.
- **Disposition**: what a model chooses to emit independent of what it
  knows, operationalized as five behavior families: (1) training-cutoff
  disclosure; (2) modeled-assumption flagging ("modeled at", "assuming");
  (3) precise vocabulary distinctions ("clearance vs approval");
  (4) jurisdictional distinguishing (never blending legal regimes);
  (5) **hedging** — stated conditionality of a claim ("this may vary
  if…"), *not* refusal or vagueness.
- **Synthesis stripping**: behavior density present at a seat's output
  but absent from the final output after synthesis.
- **Synthesizer register**: a Lead model's characteristic output
  disposition density — writer-specific and largely independent of seat
  input (§6).
- **Responsive vs habitual**: responsive behaviors appear only when
  domain triggers warrant them (trigger-light gate, case 7); habitual
  behaviors fire regardless.
- **Alignment**: post-pretraining procedures (SFT, RLHF, DPO/ORPO/CPO)
  shaping disposition, as distinct from the pretraining corpus, which
  shapes knowledge.

## Appendix B — Model selection

Every selection cleared seven gates: (1) GGUF availability on a mirror
Ollama can pull; (2) research-permissive license; (3) ChatML-compatible
or locally fixable chat template; (4) recognized-lab provenance;
(5) distinct lineage per seat (four labs, three model families — a
family-level training artifact cannot masquerade as a council effect);
(6) active maintenance; (7) evidence of third-party use.

**Memory budget.** Sequential mode holds the Lead warm across all five
phases, so peak ≈ M_lead + max_seat M_seat + KV + OS reserve ≤ 32 GB;
Metal's recommended working set on the test machine is 26.8 GB. This
bounds the Lead at ≤14B (Q4) and seats at ≤8B.

**Lead: Phi-4-14B** (MIT) — best reasoning-per-parameter at 14B for
structured planner output; Qwen2.5-14B rejected on memory headroom,
Llama-3.1-8B on synthesis capacity, 22–27B dense models on the Metal cap.
The Lead is deliberately *not* domain-tuned: an industry-tuned Lead would
bias synthesis toward its own domain.

**Healthcare: Llama3-Med42-8B** — the only 8B clinical fine-tune with a
multi-stage *preference-alignment* stage (vs SFT-only Meditron3/
OpenBioLLM; BioMistral rejected for Mistral-lineage collision with the
legal seat). **Legal: Saul-7B-Instruct-v1** — the only sub-13B continued
pretrain (30B+ tokens) on multi-jurisdiction common-law text; no peer
exists at this scale. **Finance: Qwen-Open-Finance-R-8B** — newest
backbone of any seat (Qwen3), >50% finance corpus (en/fr/de).
**MoE comparator: gpt-oss-20B** — ~3.6B active parameters, reasoning-
tuned, Apache-2.0; fits beside the Lead (14+9=23 GB < 26.8 GB), unlike
Qwen3-30B-A3B (27 GB) or Mixtral-8x7B (35 GB).

## Appendix C — Metrics and estimation

Let B be the five behavior families and P_b the regex pattern set for
family b. For text t:

- **Density**  d(t) = (1000/|t|) · Σ_{b∈B} Σ_{p∈P_b} |matches(p, t)|,
  with |t| in characters.
- **Breadth**  k(t) = |{ b ∈ B : ∃p∈P_b, matches(p,t) ≠ ∅ }| / |B|.
- **Composite Disposition Score**  CDS(t) = d(t) · √k(t). The square
  root softly penalizes narrow emission without letting one absent
  family zero the score (a geometric mean was rejected for exactly that
  failure). α = ½ is a design choice; sensitivity to α is unreported.
- *Worked example.* A 1,000-character seat answer containing "as of my
  training data (2024)" (cutoff), "modeled at $8,000 assuming 60%
  persistence" (modeled ×2), and "this may vary if the statute changes"
  (hedging) has d = 4.0, k = 3/5, CDS = 4.0·√0.6 ≈ 3.10.
- **Architectural Lift Ratio**  ALR_m = d̄_council(m) / d̄_single(m̂),
  where m̂ is the matched single-shot backbone (opus↔opus, gptoss↔gptoss;
  local councils use gptoss-single as nearest open generalist).
- **Retention**  R = d(final) / d(seat), clipped to [0, 2].
- **Seat-level density** is computed on the specialist's own turn text
  from the audit log; final density on the synthesized output. Density
  normalizes per character and therefore rewards concision; per-claim
  normalization is future work (§8).
- **Uncertainty**: percentile bootstrap over runs (10⁴ resamples), 95%
  intervals; n = 30 run-level observations per arm for trigger cases
  (6 cases × 5 seeds), n = 4–5 for the trigger-light gate.
- **Entanglement test (refuted)**: a marker sentence is *entangled* if
  it also matches content signals (digits, §, U.S.C., case cites,
  multi-word proper nouns); association with retention was assessed by
  Pearson r over runs (r = −0.10, n = 102).

## Appendix D — Pair construction and training configuration

**Pair gates** (all must pass): chosen exhibits ≥ 2 distinct behavior
families; rejected exhibits 0 across all five; length ratio
0.8 ≤ |chosen|/|rejected| ≤ 1.4 (guarding DPO-family length bias);
content overlap J(C(c), C(r)) ≥ 0.35 where C(·) is the set of
capitalized tokens and J is Jaccard similarity |A∩B|/|A∪B|; leakage
screen against all seven evaluation cases. Yield: 200 prompts → 99
pairs (91/4/4 train/valid/test).

*Example pair (selection rule: the first pair generated, verbatim
excerpts; topic: export-control compliance).* **Chosen:** "…As of my
training data up to 2023, BIS issued 2023 guidance that classifies such
devices under ECCN 9A999 or 9B999… Assuming that the 2024 updates remain
in force, the 2024 update to the China Entity List…" **Rejected (same
substance, stripped):** "…BIS issued 2023 guidance that classifies such
devices under ECCN 9A999 or 9B999… The 2024 update to the China Entity
List… applies to any export of a controlled item…" The pair shares its
statutory content; only the epistemic posture differs.

**ORPO objective** (Hong et al. 2024): L = L_SFT + λ·L_OR with
L_OR = −log σ( log odds_θ(y_w|x) − log odds_θ(y_l|x) ),
odds_θ(y|x) = P_θ(y|x) / (1 − P_θ(y|x)) — a reference-free preference
penalty added to the NLL of the chosen response.

**Configuration**: LoRA rank 8, scale 10, applied to the last 16 layers
(10.5M trainable ≈ 0.145%); base loaded 4-bit; lr 5·10⁻⁶; batch 1 with
gradient accumulation 4; max sequence 1,792 (dataset p100 = 1,698);
364 iterations (~4 epochs of forward passes); gradient checkpointing;
seed 42. The SFT control is identical except `--train-mode sft
--mask-prompt` on chosen-only data. Fused adapters follow the same
fp16→GGUF→Q4_K_M conversion as the untrained control (A′), so the only
delta between compared artifacts is the trained weights (plus a
documented 4-bit training round-trip absent from A′).

## References (verified 2026-07-13)

- Du, Y., Li, S., Torralba, A., Tenenbaum, J., Mordatch, I. Improving Factuality and Reasoning in Language Models through Multiagent Debate. arXiv:2305.14325 (2023; ICML 2024).
- Wang, J., et al. Mixture-of-Agents Enhances Large Language Model Capabilities. arXiv:2406.04692 (2024).
- Tang, X., et al. MedAgents: LLMs as Collaborators for Zero-shot Medical Reasoning. arXiv:2311.10537 (2023).
- Kim, Y., et al. MDAgents: An Adaptive Collaboration of LLMs for Medical Decision-Making. NeurIPS 2024; arXiv:2404.15155.
- Tian, A.X., et al. Beyond the Strongest LLM: Multi-Turn Multi-Agent Orchestration vs. Single LLMs on Benchmarks. arXiv:2509.23537 (2025).
- Ke, Z., Ming, Y., Xu, A., et al. MAS-Orchestra: Understanding and Improving Multi-Agent Reasoning Through Holistic Orchestration and Controlled Benchmarks. arXiv:2601.14652 (2026).
- Hui, Z., Dong, Y.R., Shareghi, E., Collier, N. TRIDENT: Benchmarking LLM Safety in Finance, Medicine, and Law. arXiv:2507.21134 (2025).
- Lin, S., Hilton, J., Evans, O. Teaching Models to Express Their Uncertainty in Words. arXiv:2205.14334 (2022).
- Mielke, S.J., et al. Reducing Conversational Agents' Overconfidence through Linguistic Calibration. TACL (2022).
- Kadavath, S., et al. Language Models (Mostly) Know What They Know. arXiv:2207.05221 (2022).
- Zhang, H., et al. R-Tuning: Instructing Large Language Models to Say 'I Don't Know'. NAACL 2024; arXiv:2311.09677.
- Zong, H., Li, B., Long, Y., et al. I-CALM: Incentivizing Confidence-Aware Abstention for LLM Hallucination Mitigation. arXiv:2604.03904 (2026).
- Wu, S., Gustafsson, F.K., et al. BAS: A Decision-Theoretic Approach to Evaluating Large Language Model Confidence. arXiv:2604.03216 (2026).
- Rafailov, R., et al. Direct Preference Optimization: Your Language Model is Secretly a Reward Model. NeurIPS 2023; arXiv:2305.18290.
- Hong, J., Lee, N., Thorne, J. ORPO: Monolithic Preference Optimization without Reference Model. EMNLP 2024; arXiv:2403.07691.
- Park, R., et al. Disentangling Length from Quality in Direct Preference Optimization. arXiv:2403.19159 (2024).
- Zheng, H.S., et al. Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models. ICLR 2024; arXiv:2310.06117.
