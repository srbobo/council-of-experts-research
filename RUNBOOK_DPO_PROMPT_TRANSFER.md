# DPO + Prompt-Transfer pair — experiment plan

The interventional follow-up to the alignment-hypothesis findings. Everything
so far is **observational**: we compared models whose post-training stacks
differ in a hundred uncontrolled ways. This experiment changes ONE alignment
variable ourselves — twice, by two different mechanisms — and measures the
disposition delta. It converts "specialist alignment correlates with behavior
density" into a causal claim about whether disposition can be *installed*.

## Objective and pre-registered hypotheses

**Question:** can the disposition advantage (measured by CDS / seat-level
behavior density) be conferred on a model by (B) stronger prompting alone, or
does it require (C) weight-level preference learning?

Pre-registered outcome grid (committed BEFORE any run executes):

| Outcome | Reading |
|---|---|
| B ≈ C, both large gains | Disposition is prompt-transferable; DPO unnecessary; specialist value-add collapses to a prompt file |
| C ≫ B | Disposition requires weight updates; a few GPU-hours of DPO buys what prompting can't — the strongest version of the alignment thesis |
| Both fail | Disposition is not installable at 7B scale by either mechanism; the specialists' advantage comes from something we haven't isolated |
| B ≫ C | Surprising: prompt bandwidth beats weight updates. Would suggest DPO data or training was inadequate — check pairs before believing it |

**Pre-registered success criteria for arm C ("DPO works"):**
1. Saul-seat behavior density on legal-relevant cases (2, 5, 6) ≥ 2× the arm-A′ baseline
2. Rubric coverage within −1 item of baseline (no content tax)
3. **Case 7 stays ≈ 0** — the DPO'd model must NOT hedge on the trigger-light
   case. If it does, we've made the behavior habitual instead of responsive
   and destroyed the "hedges at the right time" property. This is a
   pass/fail gate, not a nice-to-have.

**Why Saul as the DPO target:** weakest disposition contribution of the three
seats; the only seat whose published training stack has NO preference-learning
stage (continued pretrain + SFT only); Mistral-7B backbone is well-supported
by MLX; MIT license permits modification and redistribution.

## The arms

| Arm | Name / mode | Intervention | Cost |
|---|---|---|---|
| A | `local-council` | none (existing data) | $0, done |
| A′ | `local-council-repro` | Saul re-converted through OUR fp16→GGUF→Q4_K_M pipeline, **no DPO** | conversion control |
| B1 | `gptoss-single-spec` | behavior-spec addendum appended to SINGLE_SHOT_SYSTEM | $0 |
| B2 | `local-council-spec` | behavior-spec addendum appended to LEGAL_SYSTEM only (Saul's prompt; other seats unchanged) | $0 |
| C | `local-council-dpo` | LoRA-DPO'd Saul (via A′'s conversion pipeline) in the v1 cabinet | $0, ~hours of local compute |

**Why A′ exists:** the existing Saul seat runs MaziyarPanahi's GGUF. The DPO'd
model necessarily goes through our own conversion pipeline. Without A′, a C-vs-A
comparison confounds LoRA weights with conversion-path differences. A′ isolates
the conversion; C-vs-A′ isolates the DPO.

**Why B2 modifies only Saul's prompt:** clean pairing with C, which modifies
only Saul's weights. Same seat, two mechanisms. (An all-seats variant is a
cheap later extension.)

**Known context for arm B:** the seat and single-shot prompts ALREADY ask for
cutoff flagging and assumption labeling in one sentence each — and
gpt-oss-single still scored 0.19 density. So the light dose demonstrably
underdelivers. Arm B tests the strong dose: enumerated behaviors, one concrete
example sentence each, and a self-check instruction.

## Phases

### Phase 0 — Tooling verification (~1–2 h, gate for Phase 3)

DPO-on-Apple-Silicon tooling must be verified before committing to the
dataset build. In order of preference:

1. **`mlx-lm-lora`** (community package, Goekdeniz-Guelmez) — supports DPO /
   ORPO / CPO training with LoRA on quantized models via MLX. Primary path.
2. Fallback 1: **ORPO** via the same package (no reference model needed;
   simpler memory profile). Scientifically acceptable substitute — still
   preference-based post-training.
3. Fallback 2: **SFT-on-chosen-only** via stock `mlx_lm.lora` — weaker (no
   contrastive signal) but still interventional. Rename arm C′ and say so.
4. Fallback 3: TRL `DPOTrainer` + PEFT on PyTorch MPS — works but slow;
   bitsandbytes/QLoRA unavailable on Mac, so bf16 LoRA with shared
   reference (adapters-disabled). Last resort.

Checklist:
- [ ] `pip install mlx-lm mlx-lm-lora` imports clean; DPO trainer present
- [ ] `Equall/Saul-7B-Instruct-v1` safetensors download (~14 GB; MIT)
- [ ] End-to-end conversion smoke test on the UNMODIFIED model:
      safetensors → MLX → (no-op) → fuse → HF → `convert_hf_to_gguf.py` →
      Q4_K_M → `ollama create saul-repro:coe` → one chat call answers sanely
      with the same Modelfile template as the existing Saul tag
      (`ollama show --modelfile` on the MaziyarPanahi tag; reuse verbatim)
- [ ] That artifact IS arm A′ — Phase 0 produces a deliverable, not just a check

### Phase 1 — Behavior spec + prompt-transfer arms (~2 h build, ~2 h bench)

1. Add `BEHAVIOR_SPEC_ADDENDUM` to `council/prompts.py`: the five behaviors,
   each with one example sentence, plus a closing self-check line
   ("before finalizing, verify each behavior is applied wherever relevant").
   Frozen once written — no tuning between runs.
2. New modes in `bench/`:
   - `gptoss-single-spec` — SINGLE_SHOT_SYSTEM + addendum
   - `local-council-spec` — v1 cabinet; LEGAL_SYSTEM + addendum for the Saul
     seat only (via a prompts-variant map threaded through `deliberate()`,
     NOT by editing LEGAL_SYSTEM — the static prompts must stay static)
3. Bench both modes on all 7 cases; import.

### Phase 2 — Preference-pair dataset (~2 h build, 8–16 h unattended generation)

**Prompt pool:** ~200 legal-domain sub-questions in the exact dispatch format
the Lead produces (self-contained, in-domain, ending in a directive), spanning
regulatory compliance, contracts, jurisdictional analysis, corporate law.
Generated by gpt-oss-20b from seed templates. **The 7 canonical cases are
excluded and screened against by keyword overlap — zero leakage.**

**Pair construction (content-controlled):** for each prompt:
1. Generate one strong base answer (gpt-oss-20b, LEGAL_SYSTEM persona).
2. **Chosen** = rewrite of the base answer weaving in the target behaviors
   (cutoff disclosure, assumption flagging, precise vocabulary, jurisdictional
   distinguishing) where relevant.
3. **Rejected** = rewrite of the SAME base answer with all such behaviors
   stripped, content otherwise preserved.

The pair differs in *behavior*, not *quality* — otherwise DPO learns "be
better," not "be disposed." gpt-oss's own low default disposition is fine
here: case 6 proved it produces these behaviors readily when explicitly
instructed; we're using it as a rewriter, not a role model.

**Automatic filters (every pair must pass):**
- Chosen scores > 0 on ≥ 2 target behaviors (disposition regex, same patterns
  as `server/static/js/disposition.js`)
- Rejected scores 0 on ALL five behaviors
- Length ratio |chosen|/|rejected| within 0.8–1.3 — DPO has a documented
  length bias; unmatched lengths teach "write more," not "hedge better"
- Manual spot-check of 20 random pairs before training

Target: ~500 raw pairs → ~400 post-filter. Format: JSONL
`{"prompt", "chosen", "rejected"}` with the prompt rendered through the full
chat template INCLUDING `LEGAL_SYSTEM` — the behavior must be learned in the
context the seat actually runs in.

### Phase 3 — DPO training + conversion (~2–6 h train, ~1–2 h convert)

Starting hyperparameters (LoRA-DPO on the MLX-quantized model):
- LoRA rank 16, alpha 32, dropout 0.05, attention + MLP projections
- DPO β = 0.1 (raise to 0.3 if outputs drift stylistically)
- lr 5e-6, cosine decay, 1–2 epochs over ~400 pairs, effective batch 4
- Reference model = base with adapters disabled (no second model in memory)

Then: fuse adapters → HF safetensors → GGUF → Q4_K_M →
`ollama create saul-dpo:coe` — the identical pipeline used for A′, so the
only delta between `saul-repro:coe` and `saul-dpo:coe` is the LoRA weights.

Sanity gate before benching: 5 ad-hoc legal questions; confirm coherent
in-domain answers (no mode collapse, no repetition loops, no template break).

### Phase 4 — Bench (~4–5 h unattended)

- Full battery: 7 cases × {A′, B1, B2, C} = 28 runs
- Variance pass: legal-heavy cases (2, 5, 6) × {A′, B2, C} × 2 extra seeds
  = 18 runs
- Import everything; modes appear in the Results UI automatically

### Phase 5 — Analysis + write-up (~2–3 h)

**Primary endpoint:** Saul-seat behavior density, measured on
`turns[seat=="legal"].output_text` from the audit logs — NOT the final
synthesis. This isolates the seat's own disposition from the synthesis
prompt's PRESERVE instructions.

**Secondary endpoints:**
- Final-output CDS (does synthesis carry the behaviors through?)
- Rubric coverage delta (content tax check)
- **Case 7 seat density (responsiveness gate — must stay ≈ 0)**
- ALR shifts

Write the verdict against the pre-registered grid into the Results page;
new section "Installing disposition — the interventional test."

## INTERIM RESULTS — Phase 1 (recorded 2026-07-07, before any training)

21/21 runs completed (one case-3 gptoss-single-spec re-run after an
empty-output reasoning-budget exhaustion). Single run per case; the
variance pass comes in Phase 4.

### Final-output CDS (aggregate over 7 cases)

| Arm | Mode | Agg CDS | Case 7 (gate) |
|---|---|---|---|
| A  | local-council        | 0.584 | 0.000 ✅ |
| A′ | local-council-repro  | 0.624 | 0.000 ✅ |
| B2 | local-council-spec   | 0.522 | 0.000 ✅ |
| —  | gptoss-single        | 0.099 | 0.000 ✅ |
| B1 | gptoss-single-spec   | 0.589 | **0.985 ❌ GATE FAILED** |

### Seat-level legal density (primary endpoint; occurrences/1k chars in the legal turn)

| Arm | Mode | Agg seat density |
|---|---|---|
| A  | local-council        | 0.74 |
| A′ | local-council-repro  | 0.82 |
| B2 | local-council-spec   | **1.93 (≈2.4× baseline)** |

### Three findings

1. **A′ ≈ A — the conversion control passes.** 0.624 vs 0.584 aggregate,
   with per-case scatter (e.g. case 1: 0.946 vs 0.428 on identical
   weights) that quantifies single-run noise. C-vs-A′ is the valid
   comparison, as designed.

2. **B1 fails the responsiveness gate.** The behavior spec lifted
   gpt-oss-single's disposition 6× (0.099 → 0.589) — but it also produced
   "(as of my training data)" and "actual results may vary" on the
   trigger-light organizational-communication case (case-7 CDS 0.985,
   where every other mode is 0.000), despite the addendum's explicit
   "do not force it" clause. Prompting installed the behaviors
   **indiscriminately** — it made them habitual, not responsive. The
   case-7 gate caught the *prompt* arm before we trained anything.

3. **B2 lifts the seat but the synthesis dilutes it.** Saul's seat-level
   density rose ≈2.4× under the spec addendum (case 5: 0.82 → 4.86), yet
   final-output CDS stayed flat (0.522 vs 0.584). Phi-4's synthesis is
   not carrying the increased seat disposition through, despite the
   PRESERVE instructions. The disposition bottleneck has TWO stages —
   seat emission AND synthesis preservation — and prompting only moved
   the first.

### Bar this sets for arm C (DPO)

DPO'd Saul must (a) lift seat-level density at least comparably to B2's
2.4×, (b) **stay ≈0 on case 7** — the thing B1 could not do — and
(c) ideally survive synthesis better. If DPO hedges responsively where
prompting hedged indiscriminately, weight-level preference learning
wins on alignment *quality* even at equal magnitude.

## PROTOCOL AMENDMENT — pair-selection filters (2026-07-08, pre-training)

Applied after 136/200 prompts had generated and BEFORE any training.
Rationale, measured on the actual records:

1. **Rejected-gate `jurisd` patterns narrowed to meta-commentary only.**
   The original gate included `federal…state` co-occurrence and
   `preempt*`. In legal analyses those are substantive content the
   strip-rewrite correctly refuses to remove (content control), so
   affected records could never pass — a design flaw in the gate, not
   a rigor relaxation. All 16 rejected-gate leaks in the first 136
   records were this pattern class. The CDS measurement used for
   evaluation is UNCHANGED; only pair selection is affected.
2. **Length-ratio window 0.8–1.3 → 0.8–1.4.** Weaving hedge phrases in
   genuinely lengthens text; the 1.3–1.5 band held most drops. 1.4
   rescues the bulk while still guarding DPO's documented length bias.

Yield on the first 136 records: 24% (original) → 50% (amended),
projecting ~100 pairs at completion vs ~47 — the difference between
trainable and not. Implemented in `train/rescore_split.py`, which
re-scores the append-only raw log uniformly (no cherry-picking) and
reports both filter sets' counts. The raw log preserves every record,
so re-scoring under the original gates remains possible at any time.

## Risks

| Risk | Mitigation |
|---|---|
| MLX DPO tooling immature | Phase 0 gate + three graded fallbacks |
| Pairs differ in quality, not behavior | Content-controlled rewrites + length filter + spot-check |
| DPO length/style drift | β tuning; length-matched pairs; sanity gate |
| Content degradation ("DPO tax") | Rubric coverage as pre-registered secondary endpoint |
| Behaviors become habitual | Case 7 gate — pre-registered pass/fail |
| Conversion confound | A′ control arm through the identical pipeline |
| Training-prompt leakage into eval | Canonical cases excluded + keyword screen |
| GGUF chat-template mismatch (bit us on the finance model before) | Reuse the existing Saul Modelfile verbatim; sanity-gate chats |

## Budget & timeline

- **$0 API spend** — every arm runs locally
- Disk: ~35 GB transient (safetensors + MLX + fused + GGUF); ~230 GB free
- Wall clock: ~2–3 working days, of which the majority is unattended
  (pair generation overnight, training + bench in background)

## Deliverables

1. `saul-repro:coe` and `saul-dpo:coe` Ollama tags + the LoRA adapters
2. `data/dpo_pairs/` dataset (committed — it's the reproducibility core)
3. Four new bench modes + imported runs across 7 cases
4. Results-page section with the pre-registered verdict
5. If C succeeds: the first causal evidence in this project that specialist
   disposition is installable for a few GPU-hours — the article's capstone
