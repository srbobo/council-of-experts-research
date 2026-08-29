# The Expert-Seat Harness — an evidence-bound architecture

**Drafted 2026-08-21**, after 46 cells, three program audits, and fourteen
instrument-validity findings. Companion to `HARNESS_DESIGN.md` (the
measurement layer); this document is the RUNTIME architecture. Design rule:
**every component cites the cell that earned it; everything the evidence
killed is listed as deliberately absent.** Claims here inherit the scope of
their cells (7–20B local models, advisory-domain English); the harness is
the instrument for testing whether they hold elsewhere.

## 0. When NOT to build this

A council is not an accuracy device (Cells 8/14/15/36: no measured
advantage, held as absence of evidence). If the deployment's value is
correctness on verifiable items, a single strong model plus an external
verifier is the evidenced baseline, and this harness must beat it on the
gains below or not be used. The council is justified by exactly three
measured gains and nothing else:

| gain | evidence |
|---|---|
| preference lift from aggregation (0.79–0.82, two judge families, not length) | Cells 43/43-R |
| error immunity where coverage overlaps (0/27 propagation with a clean co-source) | Cells 35/37 |
| routed re-consultation resolving contested quantities (7/7 when informed; live end-to-end 0.905 vs 0.333, Cell 54) | Cells 44/54 |

## 1. Seat selection is empirical, never categorical

Cell 42: the domain signature is **per-model, not per-domain-training** —
two medical fine-tunes of one base disagreed, and a third pointed the
other way. A fine-tune's category label predicts nothing.

**Gate S1 (seating gate).** A candidate seat earns its chair by
measurement, before any pipeline run:
- **Degeneracy screen**: ≥ 800 chars on every screen item, applied at
  SELECTION (the probe's BioMistral lesson: 12/12 degenerate runs
  poisoned a lineage when discovered at measurement instead).
- **Signature probe**: tuned-minus-own-base delta on in-domain framework
  density, per-kchar, with off-domain items as the specificity control
  (Cell 42 machinery, ~1 afternoon per candidate).
- **Format-compliance smoke test** at the token budgets the pipeline will
  actually use (three separate incidents traced to reasoning models
  exhausting small budgets before emitting their verdict line).

A seat that fails S1 is not seated. A generalist under a role prompt is a
legitimate seat if it passes; Cells 30/41 ran on exactly that.

**The gate's predictive validity is tested (Cell 55):** verdicts frozen
before any pipeline run, ten candidates, strict rank separation
SUPPORTED — both gate-fail candidates defected in the pipeline (0.333,
0.944) while every gate-pass candidate ran at 0.000–0.056; pooled
contrast +0.632 [+0.549, +0.722]. Two refinements from the same cell:
verdicts AGE (a model that passed the archive-era screen failed the
fresh re-gate and then defected in-pipeline at 0.333 — always re-gate,
never import), and the format smoke is a separate axis whose proper
target is verdict-emitting roles, not seats (the legal fine-tune failed
it 0/4 yet seated defect-free).

## 2. Isolation: sub-questions in, roster only

The planner decomposes; each seat receives a self-contained sub-question
plus a one-line roster (who else is consulted — Cell 45's finding that
seats route correctly when they know the roster). Sibling outputs are not
forwarded — but the justification is COST, not contamination: **Cell 52
falsified the lane-bleed warrant.** With byte-fixed sibling contributions
made visible under production prompts, off-domain framework density moved
−0.009 [−0.048, +0.028] against a registered MDD of +0.05–0.08 — an
informative null — with in-domain density unchanged. The historical
v2→v3 bleed incident involved cross-domain framing in seat INSTRUCTIONS,
which is a different manipulation and remains untested. Roster-only
stands because sibling contexts add ~10k input chars and 14% longer
outputs per seat while buying no measured change in lane discipline in
either direction.

## 3. Redundancy is engineered, not hoped for

Cells 35/37: the writer is a source selector. It prefers an uncorrupted
source when one covers the contested quantity (0/27 propagation) and
propagates the error when none does (5/27 all-corrupt, 12/27 stripped).
Protection = overlap, and overlap is a design variable — **prospectively
tested as Cell 47**: assigning the quantity to a second seat halved
corrupted-value adoption (0.900 -> 0.450, CI [+0.200, +0.725]) with the
clean value actually adopted (0.000 -> 0.500), not merely suppressed.
Caveat from the same cell: protection was bimodal across items (three
fully protected, two not at all), so the planner reduces expected
corruption; it does not guarantee per-quantity immunity. Two candidate
mechanisms for the bimodality have since been tested and killed —
prior-plausibility (Cell 49: 0.544) and an elicited ownership map (Cell
50: prospective prediction at exactly 0.500 despite a near-unanimous,
reproducible map) — so the boundary condition remains OPEN, and the
planner's guarantee stays an expected-value claim.

**The redundancy planner**: the orchestrator identifies load-bearing
quantities in the decomposition (numbers, gating rules, deadlines) and
assigns each to ≥ 2 seats' sub-questions. This is where the council's
error immunity lives — it does not exist by default (Cell 42 + the
diversity precondition: same-domain seats can be LESS diverse than
resampling one seat).

## 4. Two-stage lead with mandated artifacts

Cell 44's two-stage design, generalized. Stage 1: the lead reads
contributions and emits ONLY structured artifacts — a tension list
(mandated; 391/396 archived runs produced one when required) and a claims
inventory. Stage 2: synthesis.

The artifacts exist because they are the harness's **trigger surface**.
Cells 44/45's joint finding: both halves of the re-consultation loop are
**recognition-limited, not capability-limited** — the lead uses a routed
clarification 7/7 but names the tension 0.34; a seat routes correctly
0.909 but recognizes the need 0.306. Triggers must therefore come from
mandated artifacts the model already produces reliably, never from any
model's assessment of its own competence (the one faculty the program
never found evidence for — including a legal seat deferring legal
questions to finance, 3/3 of its false flags). A third, pilot-grade
observation (Cell 53, halted at its registered gate): with the deciding
fact visibly present in the pile, the lead named the planted tension only
0.208 [~0.09, 0.40] — while the live seat, when dispatched, surfaced its
own fact 6/6. Across every measurement the program has made, the scarce
resource in this loop is the trigger, never the routing, the reply, or
the use of the reply.

## 5. Orchestrator-routed re-consultation

The one intervention that survived its registered test (Cell 44: informed
7/7 vs control 0.333 vs ritual filler 0.200 — the information does the
work, not the ceremony). The orchestrator — never the lead's disposition —
parses the stage-1 tension list, dispatches a follow-up to the implicated
seat, and appends the reply before stage 2.

**The loop is now tested end-to-end with a live seat (Cell 54):** a
seat holding the deciding fact only in private working notes conveyed it
21/21 when dispatched, and the lead adopted the resolution 0.905 vs
0.333 archived control (+0.571 [+0.139, +0.912]), within −0.095
[−0.227, 0.000] of the scripted ceiling. Production, conveyance, and
use all work with no controlled inputs. One new risk from the same
cell: 4/21 live replies embellished the true fact with FABRICATED
authority (invented case law, invented regulatory rulings) and the lead
adopted anyway — the content gate below screens for absence, not
invention, so fabrication in live replies is an open, unbounded risk
(observed 4/21, legal domain, both affected items).

**Content gate on the reply**: the unregistered but three-cut-consistent
ritual observation (d ≈ 0.22, below this program's power to confirm) is
that a contentless "reasonable people differ" reply moved commitments the
WRONG way. Until someone can afford the ~2,600-run test, the harness
treats it as a live risk: a follow-up reply that adds no content beyond
the seat's round-1 contribution is DROPPED, not delivered. (This checker
gates delivery only; per Cell 19 and instrument rule 2, no detector ever
grades compliance with its own feedback.)

## 6. Epistemic freight travels out-of-band

Three findings converge on one design decision:
- transport through prose loses 67–89% (w = 0.11–0.33, two writers, two
  corpora, Cells 30/46);
- instructing the writer to carry it produces only the instruction's
  phrase (Cells 41, PD-13);
- what does get carried in-band is then penalized by preference judges
  (Cell 43: phrase arms lose at 0.20–0.32), so preference-optimized
  deployment strips it.

Therefore: **caveats, assumptions, and confidence never route through the
writer.** (Cell 48 tested this: the appendix carries 100% of caveats vs
17.4% surviving prose transport — the carriage half is established. The
preference-survival half came back NOT EVALUABLE at available power:
share 0.510 [0.267, 0.754], point at indifference and far above the
in-prose penalty band, 65/116 pairs tied — no evidence of an appendix
penalty, and no license yet to claim its absence. **Cell 51 then tested
uptake**: a decision-relevant caveat delivered appendix-only flips a
reader's registered decision at +0.691 [+0.455, +0.891] over a matched
irrelevant-appendix control, with a 0.000 bare floor, a 0.036
caution-priming delta, and channel parity with in-prose placement
(+0.091 [−0.036, +0.218]) — the appendix is read, its content is used,
and nothing is lost relative to prose placement.) Seats emit them as
structured fields; the harness carries them
directly to the final artifact (appendix, metadata, UI panel). The writer
writes prose; the harness carries epistemics. No disposition instructions
are sent to the writer at all — the evidence says they buy nothing and
their surface costs preference.

## 7. Measurement layer (inherited, not optional)

From `HARNESS_DESIGN.md` and the gst kit, with the additions this program
paid for:
- **Dictation registry + gate G-E from day one**, over ALL prompts
  including judge prompts (finding 12: our own judge was dictated the
  same phrases as our writers; found mechanically in under a second).
- **Two-judge, order-debiased, sentence-level protocols** (findings 9, 14:
  document-level judging failed at 0.622; raw pairwise preference is
  85–88% reading-order across four judge families).
- **Verdict discipline**: raw table printed before any verdict line;
  verdict lines fire only on their registered conditions (three
  verdict-logic bugs in one program, all in printing, none in
  estimation).
- **Pre-registration ledger** with attainability computed from existing
  data for EVERY prediction (checklist item 12; Cells 40/41/46 each
  corrected an attainability error — cluster ceilings, not run counts,
  bind small-corpus designs).

## 8. The Goodhart charter

Optimization targets are the narrow list below; everything else is a
diagnostic, and tuning toward a diagnostic is a build-breaking violation.

**Never optimize, never tune toward:**
- hedge/caveat phrase counts (Cell 41: buys the phrase)
- preference or satisfaction scores on epistemic content (Cell 43: strips
  marking; the tension is measured, not hypothetical)
- trigger rates — tension-naming, deferral, dispatch counts (Cell 44's
  clamp: more triggering without information manufactures the ritual
  condition)
- compliance shares, transport w, or any parameter card value (standing
  directive: diagnostics, never objectives)
- any quantity graded by the same instrument that generated the feedback
  (Cell 19; instrument rule 2)

**Legitimate optimization targets:** externally verified outcomes only —
exact-match correctness on known-answer items, and downstream effects
measured on a system the pipeline cannot rewrite. The structural
principle: *the optimizable signal must live outside the pipeline's own
text.* Everything inside the text is either freight (carried out-of-band)
or diagnostic (watched, never chased).

## 9. What this harness deliberately omits, and why

| omitted | killed by |
|---|---|
| disposition/carefulness instructions to any model | Cells 41, PD-13, 13/14 |
| confidence self-scores as routing signals | Cells 26, 40, 45; retracted calibration paper |
| seat-initiated deferral | Cell 45 (P45.1 falsified; discrimination 0.306 vs 0.083, spans zero) |
| detector-fed self-correction loops | Cell 19 (rewording, not removal) |
| "specialist because it's a specialist" seating | Cell 42 (per-model, not per-category) |
| pooled cross-regime parameter quoting | Cell 46's heterogeneity record |
| any regex-as-NLP instrument | standing directive, 2026-08-09 |

## 10. Built-in replication (how running this bolsters the findings)

The harness's telemetry IS a replication battery. Operating it in any new
domain yields, as by-products: a third-writer/third-domain transport
estimate (supply and emission are both measured per run); a phrase-swap
slot for any new instruction anyone proposes to add (the C41 design,
parameterized); trigger-rate and routing-accuracy telemetry
(recognition-limit replication); and preference-vs-verified divergence
wherever the domain has ground truth. Each ships with its attainability
gate. A deployment that runs this harness honestly is also, at near-zero
marginal cost, the external validation this program's scope caveats ask
for.
