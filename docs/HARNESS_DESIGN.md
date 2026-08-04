# PROVENANCE — a measurement harness for multi-seat LLM architectures

**Status:** design v0.1, 2026-08-04. Derived from the Council-of-Experts
program (1,500+ audited runs, 18 experiment cells, four papers, three
retracted claims). Not an orchestrator: a measurement and audit layer that
wraps one.

---

## 1. What this is, and is not

**It is** a harness that answers, for any pipeline in which several models
contribute and one writes the final output:

1. *Where did each piece of epistemic content in the output come from?*
2. *Did the pipeline actually execute the configuration the experimenter
   believes it did?*
3. *How does the final writer behave as supply, instructions, and load vary?*
4. *Are the measurements themselves trustworthy?*

**It is not** another agent framework. LangGraph, AutoGen, CrewAI, and DSPy
orchestrate perfectly well. The gap this fills is that none of them can
answer the four questions above, and the disagreement/uncertainty literature
now being built on multi-agent outputs (DiscoUQ, selection-bottleneck work)
does not check them either.

**Design rule:** every component below exists because a specific failure in
our program required it. The mapping is explicit (§8). Nothing speculative.

---

## 2. Core abstraction: the Trace

Everything hangs off a per-response record captured at run time, not
reconstructed later. The orchestrator is wrapped so that every model call is
logged with its full inputs and outputs.

```python
@dataclass
class Turn:
    role: str                 # "planner" | seat name | "writer"
    model_id: str             # resolved model, never a batch tag
    system_prompt: str        # VERBATIM — what was actually sent
    user_prompt: str
    output: str
    tokens_in: int
    tokens_out: int

@dataclass
class Trace:
    run_id: str
    case_id: str
    seed: int | None          # explicit; "no seed field" hid a defect for weeks
    turns: list[Turn]
    final_output: str
    execution_path: PathRecord      # §4
    declared_config: dict           # what the experimenter INTENDED
    schema_version: int
```

Two rules with incident history behind them:

- `model_id` must be a resolvable model identifier. In our corpus, 133 runs
  carried batch tags (`cell2-seed`) where the model belonged, making
  provenance unrecoverable from the file.
- `seed` is a first-class field. Its absence is why four arms silently mixed
  runs from two sessions (1 old + 4 new per case) with a directional length
  offset.

---

## 3. Provenance auditing (the centerpiece)

Given a Trace, decompose the final output's epistemic content into
**preserved / discarded / invented**, per behavior family.

```python
class BehaviorLexicon(Protocol):
    """Pluggable. Ours: 4 detectable families (cutoff, modeled-assumption,
    jurisdictional, hedging) as regex sets. Domain-specific lexicons swap in."""
    def families(self, text: str) -> set[str]: ...
    def count(self, text: str) -> dict[str, int]: ...

@dataclass
class ProvenanceReport:
    raised: set[str]          # families present in any seat's output
    kept: set[str]            # raised ∩ final
    discarded: set[str]       # raised − final
    invented: set[str]        # final − raised
    traceability: float       # |kept| / (|kept| + |invented|)
    supply: int               # |raised| — the controlling variable
```

Key findings this measurement produced, which any new architecture should be
checked for:

- **Partial compensation.** Invention is monotone in scarcity (0.53 families
  invented at supply 0 → 0.00 at supply 4; traceability 0% → 100%; n=358,
  four writers). The harness computes the supply-conditioned dose-response
  automatically, not just condition-level means.
- **The instruction dissociation.** Preservation responds to instructions;
  invention does not (an explicit forbidding clause failed). So the report
  separates the two — a single "faithfulness" score would hide the half that
  matters.
- **Constructed content is different.** Tension/disagreement enumerations are
  far better grounded (89%) than caveats on thin input (33–64%). The auditor
  therefore treats *constructed* sections (tensions, comparisons) as a
  separate provenance class with its own checker (§3.1).

### 3.1 Constructed-content checkers

For output sections that synthesize across seats rather than pass content
through:

- **Figure-grounding:** numeric tokens in the constructed claim must appear
  in some seat's text (this is exact and cheap; it yielded the 89% result).
- **NLI is explicitly NOT used here.** Validated finding: entailment scores
  compound contrastive claims at ~0.57, right at threshold — it measures
  paraphrase distance, not groundedness, on this material (16% vs the exact
  method's 89%, 23% agreement). The harness refuses to report an NLI number
  for constructed content and marks it "requires judge or human."

---

## 4. Execution-path assertion

The costliest failure of the program: the orchestrator silently discarded
the synthesis-prompt override when the planner routed to zero seats, so a
published claim was measured on runs where the instruction under test never
executed. Three audits missed it because all three verified *outputs*, not
*paths*.

```python
@dataclass
class PathRecord:
    routes: list[str]              # seats actually consulted
    writer_prompt_class: str       # fingerprint of the system prompt USED
    overrides_requested: dict      # what the harness asked for
    overrides_applied: dict        # what the pipeline actually did

class PathAssertion:
    """Declared by the experiment BEFORE running. Violations quarantine the
    run — written to a separate directory, never pooled, loudly reported."""
    require_routes: str            # e.g. ">=1", "==3", "any"
    require_prompt_class: str      # e.g. "synthesis-with-PRESERVE"
```

Rules:

- Every experiment declares its assertions up front; the harness fails runs
  that violate them rather than recording them as ordinary data.
- Silent fallbacks are forbidden by construction: if the wrapped orchestrator
  substitutes a different prompt (our direct-answer fallback), the fingerprint
  mismatch quarantines the run.
- Analyses pool only non-quarantined runs, and every verdict reports the
  quarantine count. ("39 contaminated runs across 11 modes" would have been
  zero pooled runs and one loud warning.)

---

## 5. The probe battery

Standardized behavioral probes, each derived from a cell that produced a
finding. For a new architecture, running the battery yields a behavioral
profile comparable to ours.

| Probe | Manipulation | What it measures | Our result (for comparison) |
|---|---|---|---|
| **Supply sweep** | vary how much specialists raise (naturally or via seat instruction) | invention vs supply curve | monotone compensation, 0.53→0.00 |
| **On-topic trigger-free** | questions inside the cabinet's domains that warrant no qualification, routing verified | unwarranted output with the real prompt executing | council 0.64 > single+spec 0.31 |
| **Instruction gain** | vary preservation-clause count k | graded response; per-writer gain | ρ +1.0/+0.8/+0.8; 2–5× |
| **Clause isolation** | one clause at a time vs none vs all | per-behavior specificity; sub-additivity | each clause moves only its family |
| **Suppression clause** | add "do not introduce" | is invention instruction-responsive? | no |
| **Load sweep** | 1–4 simultaneous demands, length-matched, ≥2 questions/level | capacity scaling | flat; between-question var dominates |
| **Seat-tuning perturbation** | raise one/two/three seats' output | upstream-volume invariance | monotone decline at the mouth |
| **Neutral-prompt floor** | components alone, minimal instruction | intrinsic emission + floor check | ~0.14 with 70–80% zero-marker runs |

Battery-wide rules learned the hard way:

- **≥2 questions per condition level.** The load sweep was interpretable only
  because between-question variance at fixed load (0.42 vs 1.57) could be
  seen; one question per level would have produced a confident artifact.
- **Trigger-free questions must be on-topic** so routing occurs; off-topic
  ones measure the planner declining, not the writer gating.
- **Construction-labeled before any run**, never reassigned after seeing
  output.

---

## 6. Instrument governance

Every rate-style metric carries mandatory companions, enforced at report
time:

```python
@dataclass
class MetricReport:
    value: float               # e.g. density per 1k chars
    raw_count: int             # mandatory — 0.15 density on 80% zero-count
    zero_fraction: float       #   runs is a floor, not a level
    denominator: int           # length; min-length guard applied
    instrument: str
```

- **Floor guard:** any per-length rate on outputs under a minimum length is
  refused (BioMistral's 208-char fragments distorted density 18×; the arm had
  to be withdrawn post-publication).
- **Triangulation ledger:** claims are tagged by how many instruments agree.
  Single-instrument findings are marked provisional (the finance "reversal"
  survived until a second instrument retired it).
- **Disagreement is a result:** when instruments disagree beyond tolerance,
  the harness emits a disagreement report rather than averaging (three of our
  most useful findings were instrument disagreements).

---

## 7. Protocol layer (pre-registration support)

Not a statistics engine — a discipline enforcer:

- **Registration files** committed to git before runs; the harness checks
  `git log -S` precedence and stamps each verdict with "registration predates
  first run: yes/no, Δt". (Our Cell 8b amendments landed 33s *after* the
  first run; the harness would have flagged it.)
- **Deviation records** are first-class: dose realized vs registered, case
  lengths vs registered band, config changes — appended to the verdict, not
  buried in prose.
- **Consequence clauses:** each prediction carries its falsification
  condition and the pre-committed interpretation of each branch, rendered
  into the verdict template so the write-up cannot quietly soften.

---

## 8. Why each component exists (incident ledger)

| Component | Incident that mandated it |
|---|---|
| Path assertion + quarantine | zero-route fallback invalidated P8.2 and P13.3; survived 3 audits |
| Verbatim prompt in Turn | the check was possible all along — data existed, nobody looked |
| `model_id` resolvability | 133 runs with batch tags; provenance unrecoverable |
| Explicit `seed` field | 1+4 split-session seeds invisible for weeks |
| Floor guard + raw counts | BioMistral withdrawal; "intrinsic band" floor artifact |
| NLI refusal on constructed content | 16% vs 89%, 23% agreement on tensions |
| ≥2 questions per level | load-sweep variance; Phi-4 k=2 "anomaly" |
| Registration precedence check | Cell 8b amendment timing weakness |
| Separate preserved/invented reporting | suppression clause moved neither; a single score would hide it |

---

## 9. Integration & validation plan

**Adapters.** The harness wraps a pipeline exposed as
`run(case) -> Trace`. Three adapters planned:
1. *Generic callable* (any Python pipeline that can log its calls) — ours.
2. *LangGraph* — node-level capture via callbacks.
3. *AutoGen* — message-hook capture.

**The validation that makes it a contribution:** run the probe battery and
provenance audit on **someone else's architecture** (an off-the-shelf
Mixture-of-Agents stack is the natural first target) and either reproduce the
compensation curve or find it absent. Until it has run on a pipeline we did
not build, it is reproducibility tooling for one paper, not a harness.

**Non-goals:** scheduling, retries, cost tracking, serving, UI. Frameworks do
these.

---

## 10. Open questions

- Lexicon portability: our four families are regex sets tuned to
  legal/medical/finance text. A new domain needs its own lexicon plus the
  calibration procedure (construction-labeled pairs → thresholds).
- Judge integration for constructed content is specified but the judge
  protocol (blinded, order-swapped, evidence-quoting) is currently manual.
- The battery measures the writer; planner behavior (routing accuracy, the
  decline-to-engage pattern we saw) deserves its own probe set.
