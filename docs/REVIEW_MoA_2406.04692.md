# Review — "Mixture-of-Agents Enhances Large Language Model Capabilities" (Wang et al., arXiv:2406.04692)

**Reviewed 2026-08-11 against the Council of Experts program.** Question put
by Sam: does this paper attempt the exact line of work this program was
aimed at supporting; why did it succeed where the program failed; what can
be built on it.

## 1. What the paper shows

Layered architecture: each layer holds n LLMs; every agent in layer i+1
receives all layer-i outputs as auxiliary information plus the original
prompt, under an "Aggregate-and-Synthesize" prompt (their Table 1). The
final layer is a single aggregator. No fine-tuning; prompting only.

- **Headline**: AlpacaEval 2.0 LC win rate 65.1% with six open-source
  proposers (Qwen1.5-110B/72B, WizardLM-8x22B, LLaMA-3-70B, Mixtral-8x22B,
  dbrx) and Qwen1.5-110B aggregating, vs GPT-4o's 57.5%. MT-Bench gains are
  marginal (their words: models already >9/10). FLASK: better robustness,
  correctness, factuality, insightfulness, completeness; **worse
  conciseness** ("marginally more verbose").
- **"Collaborativeness"**: models score higher when shown other models'
  responses, *even when those responses are worse than what the model would
  produce alone* (their Fig. 1) — measured by LLM-judge win rate.
- **Not-just-selection claim**: MoA beats an LLM-ranker that picks the best
  proposer answer, so aggregation is "not simply selection" (Fig. 4a); BLEU
  correlation shows the aggregator's output overlaps most with the
  best-scoring proposals — "MoA tends to incorporate the best proposed
  answers" (Fig. 4b).
- **Diversity and width** (Table 3): win rate rises monotonically with
  proposer count; multiple-proposer beats single-proposer (same model
  sampled n times) at every n — 61.3% vs 56.7% at n=6.
- **Cost** (Fig. 5): MoA sits on the cost-performance Pareto front;
  MoA-Lite matches GPT-4o cost at higher measured quality.
- **Stated limitation**: time-to-first-token, nothing else.

## 2. Sam's viewpoint: confirmed on architecture, denied on estimand

**Confirmed — and more literally than "same line of work."** Cell 25's
`MOA_PROMPT` is this paper's Table 1 prompt **verbatim**
(`train/run_cell25_moa.py:47`). Every writer cell since Cell 25 runs on a
`chat()` imported from that harness. The seats→lead pipeline IS a 2-layer
MoA with role-specialised proposers; the framework paper already carries a
Council-vs-MoA table and cites both this paper and its 2025 critique. The
architecture under study here and there is the same object.

**Denied — the success criterion is disjoint.** Every MoA number is an
LLM-judge preference score (AlpacaEval LC, MT-Bench, FLASK). There is no
verifiable ground truth anywhere in the paper, no error-propagation test, no
instrument validation, no compliance/behaviour decomposition. This program's
claims live almost entirely on the other side of that line: exact-match
batteries, planted errors, validated sentence judges, causal phrase swaps.
The two efforts share an architecture and do not share a question.

## 3. "Why they succeeded and our program failed" — the honest decomposition

The framing needs correction before it can be answered: **the program did
not fail at their task; it falsified claims they never tested.** Four
concrete differences do the explanatory work.

### 3.1 The metric is the largest single difference

MoA's gains are preference-judge gains. Their own FLASK panel shows the one
dimension MoA *loses* is conciseness — the outputs got longer. This program
spent three audits building instruments that verbosity cannot buy
(per-kchar normalisation, silence checks, exact match), precisely because
finding #8 showed judge-visible surface tracks the scaffold. Under
preference judges, style gains count; under this program's instruments,
they are stripped. Cell 36 is the direct contact point: on a verifiable
battery the council's "advantage" was 3 discordant items at ceiling.
**Nothing in the MoA paper shows the 65.1% survives an instrument that does
not reward comprehensiveness.** That is not a flaw in their engineering; it
is the open question their evaluation leaves.

### 3.2 Their proposers are genuinely diverse; ours were not

Their six proposers are heterogeneous 70–110B frontier-class models from
different families. This program's seats are 7–8B domain fine-tunes — and
the Cell 42 lineage check plus the council-diversity precondition showed
med42's distance *to itself across samples* (0.506) exceeds its distance to
openbiollm (0.427). Their Table 3 diversity gain is real *for their pool*;
the 2025 follow-up (Li et al., arXiv:2502.00674, "Self-MoA") showed that
aggregating repeated samples of the single best model **beats mixed MoA by
+6.6% LC on AlpacaEval** — independently converging with this program's
finding that council diversity is not automatic and quality dominates
mixing. The published literature has already walked back the part of MoA
this program's data contradicts.

### 3.3 Their "sophisticated aggregation" and our "source selector" are the same finding, framed from opposite sides

Their evidence: the aggregator's output overlaps most (BLEU) with the best
proposals, and beats a pick-one ranker. Cell 37's evidence: the writer
prefers an uncorrupted source when one exists (0/27 propagation), propagates
corruption when none does (5/27), and doubles that when working is stripped
(12/27) — the 1→0→5→12 gradient. Both say: **the aggregator blends and
prefers good sources; it does not verify.** They measured the upside of
source selection at the wording level; this program measured its failure
boundary at the fact level. Their collaborativeness-even-from-worse-inputs
claim is preference-level; Cell 37's stripped arm shows the fact-level
version is FALSE — worse auxiliary inputs made the writer factually worse,
adopting the wrong value 12/27 times. These are complementary, not
contradictory, and together they are a sharper account than either alone.

### 3.4 Their aggregate prompt is a scaffold this program can now audit

Table 1 instructs: "critically evaluate... recognizing that some of it may
be biased or incorrect... highest standards of accuracy and reliability."
Cell 41 demonstrated causally that such instructions produce their named
surface, not the behaviour: the entire measurable effect of a
label-your-estimates clause was the phrase it named. Whether "critically
evaluate" produces critical evaluation or produces *the register of*
critical evaluation is exactly the question this program is now uniquely
tooled to answer — gate G-E, the dictation registry, and the phrase-swap
design apply to their prompt without modification.

## 4. Scoreboard of direct contacts

| MoA claim | this program's result | relation |
|---|---|---|
| Aggregation is not mere selection (ranker comparison) | Writer is a source selector at the fact level (Cell 37) | complementary: wording-blend ≠ fact-verification |
| Collaborativeness even from worse inputs (judge-scored) | Worse inputs → wrong answers 12/27 when unprotected (Cell 37 stripped) | contradicts at fact level; metric-bound phenomenon |
| More proposers monotonically better; multi > single | Same-base specialists less diverse than resampling (C42 check); Self-MoA 2025 confirms at scale | program anticipates the published walk-back |
| Aggregator "critically evaluates" per prompt | Instructions produce their phrase, not the behaviour (Cell 41, PD-13) | untested by them; testable with our kit |
| FLASK factuality/correctness up, conciseness down | Preference judges reward surface; audits #1–#3 | their one negative dimension is our headline confound |
| MoE analogy (§2.3) | Cells 36/39: council vs MoE writer nulls | both find no clean MoE-vs-ensemble separation |

## 5. Opportunities (checklist-run; item 9 alternatives stated inline)

1. **The missing measurement appendix of MoA** — reproduce MoA-Lite at
   local scale (their exact Table 1 prompt, already in Cell 25), score with
   the validated instruments: exact-match on the verifiable battery,
   qualification transport w, invention at zero supply, per-kchar framework
   density. Question: *does any MoA gain survive instruments that verbosity
   cannot buy?* Cheapest high-value cell; most machinery exists.
2. **Planted errors through MoA layers** — Cell 37's injection machinery
   run through 1/2/3 MoA layers: does layered aggregation filter or amplify
   corruption as depth grows? Their monotone layer gains are judge-scored;
   the fact-level curve is unmeasured anywhere in the literature.
3. **Phrase-swap their aggregate prompt** — Cell 41's design on "critically
   evaluate / biased or incorrect": swap the named evaluative vocabulary for
   registry-clean synonyms and measure whether any behavioural residue
   survives. Directly tests whether MoA's prompt does work or names work.
4. **The diversity cell, now with published stakes** — the four-arm design
   (domain-tunes / role-prompted same base / MoA-style heterogeneous mix /
   single-model resample) is no longer just Sam's question: it arbitrates
   MoA Table 3 vs Self-MoA on epistemic instruments neither paper has.
   Blocked as before on a llama3-lineage legal/finance tune or accepting
   cross-base seats.
5. **Collaborativeness, causally** — their Fig. 1 with quality-CONTROLLED
   auxiliary responses (known-good vs known-corrupted, our injection kit),
   scored by both a preference judge and exact match, to show where the
   phenomenon is real and where it is metric artifact.

## 6. Verdict

Sam's reading is right that this is the same architecture — literally the
same prompt string — and right that they "succeeded" where this program
"failed," **but only under their metric**. They built the case that layered
aggregation lifts preference scores at good cost; this program built the
instruments that show what such lifts are made of, and falsified the
mechanism claims (recomputation, corroboration use, instruction-induced
behaviour) that the MoA narrative quietly assumes. The follow-up literature
(Self-MoA) has already conceded the diversity half of this program's
position. The opportunity is not to compete with MoA on AlpacaEval; it is
to publish the epistemic audit of MoA that nobody, including its authors,
has run — with a kit that was built, validated, and battle-tested here.
