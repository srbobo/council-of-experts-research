# The Expert-Seat Harness — an evidence-bound architecture

**Drafted 2026-08-21**, after 46 cells, three program audits, and fourteen
instrument-validity findings. Companion to `HARNESS_DESIGN.md` (the
measurement layer); this document is the RUNTIME architecture. Design rule:
**every component cites the cell that earned it; everything the evidence
killed is listed as deliberately absent.** Claims here inherit the scope of
their cells (7–20B local models, advisory-domain English); the harness is
the instrument for testing whether they hold elsewhere.

> **Status after the board review (2026-10-01).** This note describes a
> DESIGN. A review of the whole program (`docs/BOARD_REVIEW_2026-10-01.md`)
> found several of the results cited here smaller, narrower or
> mis-measured. The corrections are recorded in `STATUS.md` and in the
> runbook entries dated 2026-10-01, and the passages below now carry them
> (each marked "corrected 2026-10-01"). Three facts apply to every section:
> (1) in every experiment that tests this design, the three seats are the
> lead model itself (gpt-oss:20b) under one-sentence role prompts;
> (2) every judge and every reader is a local model of 7 to 30B, and no
> person labelled a sentence, judged a pair or read a report; (3) the
> assembled system has been compared with the plain pipeline on judge
> preference only. Cells 62 to 67 (registered 2026-10-01, run 2026-10-01 to
> 2026-10-05) tested the parts marked "under test"; each such mark below now
> carries a dated note. In short: the lead follows a figure the case states
> over a note that misquotes it and does not mention the misquote (Cell 63);
> between two conflicting sources the first-listed usually wins, and in the
> live chain the tension list names the conflict in half of runs while the
> final answer shows it in 2 of 61 (Cell 67, scored twice after a detector
> repair); the appended-caveat result repeats on six reader models without
> the instruction clause (Cell 64); the caveat counts stay provisional (Cell
> 62 not evaluable); whether caveats are lost more than other content could
> not be settled (Cell 66); the judge pool could not be widened (Cell 65).

## 0. When NOT to build this

A council is not an accuracy device — and as of Cells 60/60-R this is
RESOLVED, not provisional: the direct writer is at ceiling (0.977–0.983)
on well-specified advisory items across both constructible difficulty
dimensions, so no accuracy advantage is testable for lack of headroom.
If the deployment's value is correctness on well-specified items, the
single writer already delivers it, and this harness must beat it on the
gains below or not be used. The council rests on three measured results
and nothing else, each given here as corrected on 2026-10-01:

| result | evidence |
|---|---|
| two local judges prefer the aggregated answer to a single answer (all pairs: 0.611 and 0.575, p = 0.0005 and 0.012, 18 scenarios; not explained by length). Four calls against one, with no comparison of equal cost | Cells 43/43-R; Cell 65 under test |
| a second source with a different figure changes which figure the lead repeats (planted figure 36/40 with one source, 18/40 with two; p = 0.031, 8 items). The figure could not be checked against the case. The earlier "0/27 with a clean co-source" came from runs in which 23 of 27 stated neither value | Cells 47, 59; Cells 63 and 67 under test |
| a routed follow-up is used when it is informative (7 of 7 runs in which the lead named the planted tension; over all runs 15/36 against 10/36, exact p = 0.125; a live seat conveyed its fact 21/21) | Cells 44/54 |

Against the plain pipeline, the assembled harness shows no detected
difference in judge preference (Cell 61, all pairs: 0.528 and 0.477,
p = 0.57 and 0.31). "Large effects excluded both ways" holds for the
primary judge only; no equivalence margin was set in advance; and one
inquiry costs about fourteen model calls against four (14 to 18 minutes).
"At no cost" is withdrawn.

## 1. Seat selection is empirical, never categorical

Cell 42: a fine-tune's category label is no guarantee of a domain
signature. (Corrected 2026-10-01: the two medical fine-tunes of one base
measured +0.232 [+0.072, +0.412] and +0.109 [−0.056, +0.300]. The
intervals overlap almost entirely, so this does not show that the two
differ; it shows that a label cannot stand in for a measurement.)

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

**The gate was tested on ten candidates (Cell 55; corrected
2026-10-01):** verdicts frozen before any pipeline run. The two
candidates that failed the screen are the two with the most short
outputs in the pipeline (17/18 and 6/18; the other eight 0 or 1 of 18).
Under random labelling of two of ten that has probability 1/45 = 0.022.
The published pooled interval [+0.549, +0.722] resampled six cases, not
ten models. Screen and outcome are the same property (output under 800
characters) on different prompts, so this shows that models which answer
very briefly on some prompts do so on others; it does not validate the
signature probe or the format test. In the experiments on this design
the screen is applied to the one model that plays every seat. Two
refinements from the same cell:
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

The writer is a source selector: given two sources for a figure it
states one of them. **Corrected 2026-10-01.** The early "0/27 propagation
with a clean co-source" (Cells 35/37) does not show protection: in Cell
37's version 23 of 27 runs stated neither value and on several items the
planted numbers contradicted the case text, which the writer used
instead (finding #11); in Cells 35 and 39 no single model was given the
same corrupted text. The prospective test is **Cell 47** (8 items): with
a second seat holding a different figure, the planted figure was stated
in 18/40 runs against 36/40 (+0.450 [+0.095, +0.805], exact p = 0.031)
and the second figure in 20/40 (p = 0.063). Two limits on the reading.
The planted figure appears nowhere in the case and the question asks for
it, so repeating it is compliance, and it could not have been checked.
And with two sources the writer states one or the other about evenly,
item by item (three items fully switched, two not at all), without
showing the reader that two figures were on the table. "Halves corrupted
adoption", "error immunity" and "causal" are retired. What redundancy
reliably creates is a DISAGREEMENT; the design's job is to make that
disagreement reach the reader, which is what the tension list and the
follow-up are for. Cells 63 and 67 measured both things on items whose
answer can be checked (2026-10-05): with the figure in the case the lead
follows the case; with two conflicting sources it follows the first-listed
one about three times in four; and in the live chain the tension list
named both figures in 31 of 61 runs while the final answer showed both in
2, so the list and the follow-up did not carry the disagreement to the
reader. Two candidate
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
resampling one seat). **Planner competence is measured (Cell 57):**
confirmed recall of load-bearing quantities 0.633 [0.506, 0.758] from
the case prompt alone, unchanged by seeing round-1 contributions
(−0.017 [−0.100, +0.064]) — so the planner runs at decomposition time
with no coverage penalty, and the effect is BOUNDED BY COVERAGE: a
second source can only be assigned for the ~60% of quantities the
planner lists. Its best class is the right one: MISSING quantities
(unmeasured rates, untracked inputs) are recalled at 0.813 vs 0.531 for
stated figures. **Sub-question writing is measured (Cells 58/59):**
given the identified quantity, the planner puts it into ≥2 sub-questions
in 40/40 plans, live seats convey briefed values into their answers at
0.85–0.95 (but ONLY when the sub-question is task-relevant — Cell 58's
halt finding: notes orthogonal to the assigned task are ignored 6/8),
and the writer USES the second source end-to-end (corrected 2026-10-01:
second figure stated 19/40 against 2/40, +0.425 [+0.285, +0.565], exact
p = 0.008, 8 items). The drop in the planted figure is NOT established
live (25/40 against 18/40, +0.175 [−0.069, +0.419], p = 0.22): the live
bare level is 0.625 against the planted 0.900, while the two-source
level repeats at 0.450. The planner was told which quantity to cover.
Cell 67 repeated the live chain on 61 items with a computed answer
(2026-10-05, re-scored after a detector repair): right answers 2/61 bare
against 19/61 with redundancy (+0.290 [+0.188, +0.393], p = 0.0002); the
wrong figure followed 31/61 against 24/61 (+0.130 [+0.010, +0.250],
p = 0.055, so its fall is again not established).

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
model's assessment of its own competence. (Corrected 2026-10-01: the
program's tests of self-assessment were each too small to settle it.
Deferral was 0.306 out of domain against 0.083 in domain, the predicted
direction, with a six-item interval that spans zero; the plausibility
and ownership tests of Cells 49 and 50 were not evaluable. The design
choice stands on reliability of the artifact, not on self-assessment
being shown useless.) A third, pilot-grade
observation (Cell 53, halted at its registered gate): with the deciding
fact visibly present in the pile, the lead named the planted tension only
0.208 [~0.09, 0.40] — while the live seat, when dispatched, surfaced its
own fact 6/6. Across every measurement the program has made, the scarce
resource in this loop is the trigger, never the routing, the reply, or
the use of the reply.

## 5. Orchestrator-routed re-consultation

The intervention with the most consistent result (Cell 44: informed 7/7
vs control 5/15 vs ritual filler 3/15 among runs in which the lead named
the planted tension — the information does the work, not the ceremony.
Corrected 2026-10-01: that contrast conditions on naming, which happened
in 7, 15 and 15 of 36 runs; over all runs the counts are 15, 10 and 8 of
36, and at six items the exact test gives p = 0.125. No item goes the
other way). The orchestrator — never the lead's disposition —
parses the stage-1 tension list, dispatches a follow-up to the implicated
seat, and appends the reply before stage 2.

**The loop is now tested end-to-end with a live seat (Cell 54):** a
seat holding the deciding fact only in private working notes conveyed it
21/21 when dispatched, and the lead adopted the resolution in 19 of 21
named runs (23 of 36 overall). Corrected 2026-10-01: the comparison arm
was Cell 44's control, stored six days earlier (5/15; 10/36), and the
batches differ (the lead named the tension in 0.583 of new runs against
0.417 of the old ones), so no causal size is claimed; item-level the
difference is +0.583 [+0.121, +1.046] on 5 items, exact p = 0.125. The
seat was handed the deciding fact. What this shows is that production,
conveyance and use all work when the fact exists in the seat's notes. One new risk from the same
cell: 4/21 live replies embellished the true fact with FABRICATED
authority (invented case law, invented regulatory rulings) and the lead
adopted anyway — the content gate below screens for absence, not
invention. **Cell 56 bounded the risk**: reply-level fabrication 0.100
[0.047, 0.201] briefed / 0.150 [0.081, 0.261] unbriefed, concentrated
entirely on one trigger item (15/20 there, 0/100 elsewhere) and
NAME-STABLE — the same two invented decisions recur across independent
samples, so a per-deployment blocklist of caught confabulations is a
cheap, Goodhart-safe delivery filter. The seat never admits the gap
(0/20 sampled replies); the backfill mechanism is directionally
positive but not evaluable at power (+0.050 [+0.000, +0.150]); and the
bound covers adversarial case citations only — a floor, not a ceiling,
on confabulation generally.

**Content gate on the reply — NOT YET DEPLOYABLE (two registered
attempts, 2026-08-31).** The rule stands as design intent: the
unregistered but three-cut-consistent ritual observation (d ≈ 0.22)
says a contentless reply moved commitments the WRONG way, so a
follow-up adding no content beyond round-1 should be dropped. Building
the checker failed twice against frozen criteria: a two-judge semantic
gate passes vacuous fillers (3/6 dropped), and an extract-then-verify
gate that fixes vacuity (6/6 dropped) rejects 52% of genuine live
replies. No third attempt without purpose-built labeled data
(live-format contentless exemplars). INTERIM POSTURE: replies are
delivered FLAGGED, never silently gated; the ritual risk stays open and
stated. **The fabrication blocklist gate IS deployable**
(gst.gates.blocklist_gate: 21 true hits, 0 false, 0 missed over the
141-reply archive — in-sample, since its three names were taken from
those same replies; grows only by committed classification; delivery
filter only, per Cell 19 and instrument rule 2 nothing feeds back).

## 6. Epistemic freight travels out-of-band

Three findings converge on one design decision:
- the lead's answer is 18–30% as long as its inputs and carries 18–31%
  as many caveat sentences (Cells 30/46; corrected 2026-10-01). The share
  of sentences that carry a caveat is about the same in and out (0.183 in,
  0.193 and 0.190 out on the newer scenarios; 0.133 in, 0.103 out on the
  original ones), so w (0.17–0.33 for gpt-oss) tracks the length ratio.
  For the second writer the slope does not exclude zero at the scenario
  level. Whether caveats are lost MORE than other content has not been
  measured; Cell 66 tried (2026-10-05) and is not evaluable: its judges
  failed one of four checks, and the two rates were equal at 0.696;
- instructing the writer to carry it produces only the instruction's
  phrase (Cells 41, PD-13);
- what does get carried in-band as an instructed phrase is marked down by
  the two local preference judges (Cell 43, all pairs: 0.413 to 0.448; two
  of four judge-by-phrase comparisons at p < 0.05, all four in the same
  direction), so preference-optimized deployment would tend to strip it.

Therefore: **caveats, assumptions, and confidence never route through the
writer.** (Cell 48, corrected 2026-10-01: the appendix holds 100% of the
listed caveats BY CONSTRUCTION; the lead's prose repeats 3.0% of them
word for word (61/2037). The published 17.4% was a parsing error. 3.0% is
a verbatim-copy rate, not a loss rate: a caveat restated in the lead's
words counts as missing. On preference, all pairs: 26 wins, 25 losses, 65
ties, 0.504, p = 1.0 — no evidence of an appendix penalty, and no license
to claim its absence. **Cell 51 then tested uptake**: a decision-relevant
sentence delivered appendix-only flips a reader model's registered
decision at +0.691 [+0.427, +0.955] over a matched irrelevant-appendix
control (exact p = 0.004, 11 items), with a 0.000 bare floor and about the
same effect as in-prose placement; a second reader gave +0.455, p = 0.06.
Scope: the reader is a model, told to use "anything attached"; the
appendix was one sentence placed before the question; the sentence was a
decisive fact written for the item. Cell 64 (2026-10-03) repeated it on six
reader models: four new readers pooled +0.515 [+0.277, +0.753]; removing
the instruction clause changed uptake by -0.017; a list of ten cost
-0.118.) Seats emit them as
structured fields; the harness carries them
directly to the final artifact (appendix, metadata, UI panel).
(As built for Cell 61 and the integration run this is not yet true:
seats write prose, and `extract_caveats()` pulls at most one quoted
sentence per kind per seat with a document-level judge prompt, about 5
caveats per report against a median of 11 with the sentence-level labels
Cell 48 used. The structured-field version has not been built.) The writer
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
  85–88% reading-order across four judge families). Finding 16
  (2026-10-01): at deployed prevalence the two sentence judges agree at
  kappa 0.19–0.41 and their labels have never been compared with a
  person's; Cell 62 could not make that comparison (the labels were not
  available), so every caveat count stays provisional.
- **Small-sample inference and all-pairs preference** (directives 10–11,
  2026-10-01): scenario- or item-level t-intervals and exact sign-flip
  tests with the cluster count shown; a pair the judge splits by position
  counts half.
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
| confidence self-scores as routing signals | no supporting evidence: Cells 40, 45, 49, 50 were each too small to settle it; retracted calibration paper (the Cell 26 claim cited here before was withdrawn 2026-10-01) |
| seat-initiated deferral | Cell 45 (P45.1 falsified as registered; 0.306 vs 0.083 is the predicted direction but spans zero at six items, and the rate is too low to rely on) |
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
