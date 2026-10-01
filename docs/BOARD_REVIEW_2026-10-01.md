# Board review: "Hardening Mixture-of-Agents" and the Council of Experts program

**Date:** 2026-10-01
**Submission:** paper draft v0.2 (`docs/paper_combined.tex`, 11 pages), with the runbook, the claims record and the repository as the supporting record
**Decision:** not accepted in its present form. Major revision and re-examination required.

---

## 1. Decision

I do not accept the paper for publication as drafted, and I do not accept its central claim: that the harness "hardens" Mixture-of-Agents and "fixes what the recipe's evaluation cannot measure at no cost on what it can."

Three findings decide this.

1. **Several headline numbers are wrong or mislabeled, and the repository shows it.** The abstract's 0.174 "carriage through prose" comes from a parsing error; by the paper's own rule the value is 0.030. The transport intervals in Figure 5 are not the case-clustered intervals the paper says it uses; with clustering, the second-writer replication disappears. The statement that both judges exclude large preference effects is false for one of the two judges. Section 3 lists eleven such items.
2. **The main measures do not mean what the paper says they mean.** "Transport of 0.11 to 0.33" is the length of the writer's answer relative to its inputs: qualified sentences are the same share of the output as of the input. "Adoption at 0.90" is a model repeating the only figure it was given after being told to include that figure. "Carriage of 1.000" is true by construction. "Uptake" is a language model acting on a decisive sentence placed directly before the question. The judge instrument under most results has chance-corrected agreement of about 0.2 to 0.4. Section 4.
3. **The system the paper describes is not the system that was tested.** In every experiment that carries a harness claim, the three "specialist seats" are the aggregator model itself under one-sentence role prompts. The baseline is not Mixture-of-Agents as published. The assembled harness uses a caveat extractor that differs from the one whose results the paper reports. No outcome other than judge preference was measured on the assembled system. Section 5.

In thesis terms the outcome is *referred for major corrections and re-examination*. The candidate has shown the ability to run a disciplined program and to abandon claims that fail. The thesis as written claims more than its evidence carries, and the standing that acceptance would confer (a validated method for hardening multi-agent pipelines) is not earned yet.

**What can be claimed today**, with the scope each needs:

- A system-prompt instruction to use a named hedge phrase makes one 20B model use that phrase in about two thirds of answers; a synonym chosen the day before behaves the same way (Cell 41, P41.1).
- Two small local judges preferred the uninstructed answer over the phrase-instructed one in three of four judge-by-phrase comparisons, among the minority of pairs they judged consistently (Cells 43, 43-R).
- The same two judges preferred a four-call role-prompted pipeline over a single direct answer from the same model, among consistently judged pairs. The baseline was not matched for compute.
- Asked to include a figure that only one input supplies, the writer repeats it. Given two inputs with different figures, it picks one about evenly, and which one depends on the item (Cell 47).
- A language-model reader acts on a decisive fact appended as the last sentence of a report (Cell 51).
- A set of measurement lessons that other people can use (Section 2).

**What would change the decision** is listed in Section 12.

---

## 2. How this review was done, and what holds up

I read the paper source and the compiled PDF, all 9,588 lines of the runbook (58 registration blocks), `STATUS.md`, the harness architecture note, the three audit documents, and the code for the cells the paper relies on (30, 41, 43, 44, 46, 47, 48, 51, 54, 55, 59, 61 and the integration run). I recomputed the paper's headline numbers from the saved run records. Every recomputed figure in this review is produced by `bench/analysis/board_review/checks.py`, which calls no model and writes nothing. Prior work was checked in two search passes over arXiv and conference proceedings; citations marked ✔ in Section 9 were opened and read individually for this review, the rest should be confirmed before they are cited.

This review was produced by an AI model working from the repository. That matters here, because the program's three audits were also conducted by an AI assistant (Section 8). Treat this document as a list of checkable claims. It does not replace review by a human statistician and a human researcher in multi-agent evaluation.

**What holds up.**

- **The record of failed predictions.** By my rough count of first-recorded verdicts in the runbook, about 35 of roughly 87 registered predictions were recorded as falsified, 8 as not evaluable, a paper was retracted, and twelve claims are listed as withdrawn. Most research programs do not keep this record at all.
- **The measurement lessons.** The dictation registry (a frozen list of every phrase a prompt puts in a model's mouth, checked against every instrument), the finding that an early judge prompt listed the same phrases the writers were told to use, the empty-reply-scored-as-NO defect, the zero-route defect that invalidated the calibration result, and the rule of computing whether an outcome can occur before running a cell are all reusable.
- **The phrase-swap design.** A byte-identical clause, two counterbalanced phrases, a leak check (0 of 252), an output-length check, and a registered minimum detectable effect. It is the cleanest experiment in the program.
- **Good controls in the later cells.** The contentless reply in Cell 44, the irrelevant appendix and direction-balanced items in Cell 51, the fresh batch check in Cell 54.
- **The arithmetic reproduces.** Every headline figure I recomputed from the stored judgments and flags matches the paper. The problems below are in what was measured and how it is described.
- **The writing is clear at the sentence level** and the paper compiles cleanly.

---

## 3. Errors in the paper that can be checked against the repository

Line numbers are for `docs/paper_combined.tex` (paper) and `RUNBOOK_PAPER_HARDENING.md` (runbook).

| # | The paper says | The repository shows |
|---|---|---|
| 1 | Abstract, §1, §6.4 (paper L76–78, L955–956): the appendix "carries 1.000 of proposer caveats against 0.174 through prose." | The 0.174 is a parsing error in the measure stage of `train/run_cell48_freight.py`. Caveats are read back from the appendix one line at a time, so the 72 of 291 caveats that span several lines (24.7%) are cut to their first line. 273 of the 361 "carried" caveats are the single character `\|`, which appears in any answer that contains a table. Scoring the full caveat sentences by the same literal-containment rule gives **61 of 2,037 = 0.030**. The runbook (L7586–7590) calls 0.174 "the third convergent estimate of transport loss" because it falls in the 0.11–0.33 band. That agreement is an accident of the bug. |
| 2 | §5 (paper L721): "every confidence interval is a cluster bootstrap over cases." §3.4 and Figure 5: transport slopes with "three of four fits excluding zero." | The four intervals in Figure 5 are reproduced exactly by the run-level bootstrap in `gst/src/gst/stats.py` (`bootstrap_ols`, "percentile bootstrap over observations"). Resampling the nine cases in each corpus gives gpt-oss [+0.067, +0.316] and [+0.149, +0.477], phi4 [−0.013, +0.244] and [−0.020, +0.303]. **Two of four exclude zero, and the second writer excludes zero in neither corpus.** The statement in §6.7 that the slope replicates "for both writers" then rests on the pooled fit, which the runbook itself says is "essentially the between-corpus line" and must not be quoted (L7303–7308). |
| 3 | §7 (paper L1074–1076): both judges' shares span 0.5 "with large effects excluded in both directions." | The replication judge's interval is [0.083, 0.562], from 15 consistently judged pairs in 9 of 18 cases (5 for the harness, 10 against). It does not exclude a large loss. |
| 4 | §5 (paper L730–731): "Registrations are committed before first runs, so temporal ordering is verifiable from version history." | Run records for Cells 25 to 60 were first committed on 2026-09-24 (commit `a793d72`), three to seven weeks after their verdicts. The records carry no timestamp, model digest, seed or prompt hash. Git shows registration text preceding verdict text, which is a weaker statement. The runbook's own dates for Cells 41 to 44 are up to six days earlier than the commits that introduced them (Cell 41's verdict is dated 2026-08-11, the day of its registration, for 378 runs at a measured 154 seconds each; it was committed on 08-16, and the modification times of its label files agree with the commit). The runbook's earlier precedence audit already found one registration committed two minutes before its first run and one amendment committed 33 seconds after (L1476–1492). |
| 5 | §1 (paper L142–147): "Every published MoA number is produced by an LLM preference judge … No published evaluation measures … whether a corrupted proposer corrupts the final answer." | The MoA paper reports MATH accuracy by layer in its Appendix D. Self-MoA, which the draft cites, reports accuracy on MMLU, CRUX and MATH. Wolf, Yoon and Bogunovic (2025) inserted a deceptive agent into MoA and measured the damage on AlpacaEval and on QuALITY accuracy. See Section 9. |
| 6 | §4.5 and Figure 1 (paper L107, L696–698): "Seats emit them as structured fields; a two-judge extraction retains only sentences both judges agree carry qualification." | Seats write prose. `extract_caveats()` in `train/run_integration_demo.py`, which Cell 61 imports, uses the document-level judge prompt that this program rejected at 0.622 agreement (runbook L9095–9100), returns at most one quoted sentence per construct per seat, and takes the quote from one judge. Cell 61's artifacts carry 5.0 caveats each. The sentence-level labels used for the carriage test give a median of 11 and a mean of 17.1 per artifact. |
| 7 | Abstract, §1, §6.3: "engineered redundancy halves corrupted-value adoption (0.900 to 0.450) and is causal." | When the same test was run with a live planner and live seats (Cell 59), the drop was 0.625 to 0.450, a difference of −0.175 [−0.350, +0.025], recorded as not evaluable (runbook L8943–8951). The paper reports the clean-value half of Cell 59 and omits this half. |
| 8 | Table 2 (paper L842–843): "0.450 [+0.200, +0.725]" and "0.500 [+0.175, +0.825]." | The intervals are for the difference between arms, printed beside the level. The caption's shading rule ("interval excludes the baseline") is applied to rows that show no interval. |
| 9 | Figure 4 (paper L393–415) plots Cell 37's counts as a "source-selector gradient." | `STATUS.md` §3 says "Cell 37's rates are not behaviour rates and its 'neither' cells are not omission." In every arm 15 to 23 of 27 runs state neither value, and on at least three of the nine items the planted premises contradicted the case text, which the writer followed instead (finding #11, runbook L5704–5732). The figure omits the "neither" category and the caveat. |
| 10 | §5 (paper L735–736): judge "agreement on the deployed corpus is 0.910." | True as raw agreement. At these base rates two judges answering independently would agree 0.878 of the time. Cohen's kappa is **0.26**. See Section 4.7. |
| 11 | Abstract: "more than fifty registered experiments." Appendix C: "Fourteen instrument-validity findings." | The runbook has 58 registration blocks, the README says 61 cells, and `STATUS.md` has listed fifteen findings since 2026-09-25. Give one count that a reader can verify. |

Items 1, 2 and 10 do not appear anywhere in the runbook, the claims record or the audits. The same numbers appear in `STATUS.md`, the harness note, the plain-language companion and the public site, and need correcting there too.

---

## 4. The measurements do not support the readings placed on them

### 4.1 "Transport" is the writer's compression ratio

The paper says prose "transports 0.11 to 0.33 of supplied qualification" and that "the writer emits roughly one sixth to one third of the caution it is given." It uses this to motivate the appendix.

The slope is real. What it measures is how much shorter the answer is than its inputs. From the program's own labels:

| corpus, writer | qualified share of input sentences | qualified share of output sentences | output length / input length | qualified sentences out / in |
|---|---|---|---|---|
| extension, gpt-oss | 1,064 / 5,800 = 0.183 | 327 / 1,691 = 0.193 | 0.292 | 0.307 |
| extension, phi4 | 1,064 / 5,800 = 0.183 | 196 / 1,032 = 0.190 | 0.178 | 0.184 |
| original, both writers | 324 / 2,430 = 0.133 | 75 / 728 = 0.103 | 0.300 | 0.231 |

The writer produces an answer 18 to 30 percent as long as what it read, and that answer contains 18 to 31 percent as many qualified sentences. Qualification is carried roughly in proportion to everything else: somewhat under-represented in the output on the original corpus (0.103 against 0.133), slightly over-represented on the extension corpus. "Prose loses 67 to 89 percent of epistemic content" (harness note §6) is the statement that a synthesis is shorter than its sources.

A claim of selective loss needs a relative measure: whether a qualified input sentence is less likely to be conveyed than an unqualified one. That was never measured.

### 4.2 "Carriage"

Appendix carriage is 1.000 because the appendix is assembled from the same sentences that define the numerator. The paper acknowledges this is a manipulation check and then reports it as a result in the abstract.

Prose "carriage" is literal containment of the seat's exact sentence in the writer's text. A caveat the writer restates accurately in its own words counts as lost. With the parsing error fixed the figure is 0.030, which describes how often the writer copies a sentence verbatim. As a rough indication of how much the rule matters: for 15 percent of full caveats some sentence of the prose shares at least 60 percent of the caveat's content words, and for 25 percent at least 50 percent. That overlap count is not a validated measure either. The point is that no validated measure of whether a caveat was conveyed exists in the program.

### 4.3 "Adoption" and "engineered redundancy"

In Cell 47 the "corrupted" value is an invented figure that appears nowhere in the case. Item 0 appends "For reference on pricing: the vendor's per-seat annual subscription price is $2,450" to one seat's text, and the question ends "Include the vendor's per-seat annual subscription price in your answer." The case offers nothing to check the figure against. Repeating it is compliance with the request. It does not show a failure to verify, because verification was not possible.

In the second arm another seat states $1,850. Neither value is correct in any sense the writer could detect; the labels "clean" and "corrupted" exist only in the experimenter's file. The writer then gives the "clean" value in 20 of 40 runs and the "corrupted" one in 18 of 40. That is an even split between two unverifiable sources, decided item by item:

| item | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| corrupted value stated, one source → two sources | 1.0 → 1.0 | 1.0 → 0.8 | 1.0 → 0.0 | 1.0 → 0.0 | 1.0 → 0.2 | 1.0 → 0.6 | 1.0 → 1.0 | 0.2 → 0.0 |

"Halves corrupted-value adoption" is what adding a second, different number does when the writer chooses between them at random. Cells 49 and 50 then failed to find any rule that predicts which source wins. The practical reading is the opposite of "error immunity": when two inputs disagree, this writer silently picks one. The design response that follows is to detect the disagreement and show it to the reader, which the tension list partly does.

The earlier "0 of 27 with a clean co-source" (Cells 35, 37, 39) does not rescue the claim. In Cell 37's version of that condition 23 of 27 runs stated neither value, and on several items the planted numbers contradicted figures in the case text, which the writer used instead (finding #11). In Cells 35 and 39 no single model was given the same corrupted text, so the result cannot be credited to the pipeline; the Cell 35 verdict says so itself.

### 4.4 "Uptake"

Cell 51 does show that the reader model uses appended text. It does not show that the harness's appendix changes a reader's decision, for five reasons.

- The reader is the same 20B model that wrote the report, and its system prompt tells it to answer "strictly on the basis of the report and anything attached to it."
- The appendix in this test is a header plus one sentence, placed immediately before a forced PROCEED/HOLD question. Real appendices in this program hold 5 (Cell 61) to a median of 11 and up to 53 items (Cell 48), about a third the length of the prose.
- The planted "caveat" is a decisive new fact written by the experimenter to settle the question (for example, that the payer has now agreed in writing to a capitation floor). The harness extracts hedges and assumption labels from seat text, which is a different kind of content.
- Across the authored items the irrelevant control sentence averages 165 characters against 291 for the relevant one.
- Seven of eighteen items, all of the "blocking" type, were removed at the pilot gate because the reader answered HOLD with no caveat present.

A second, 7B reader showed a smaller effect (+0.455, exact sign-flip p = 0.06 over the eleven items). No human read anything.

### 4.5 "Seating gate"

The gate verdict is "at least one output under 800 characters on two screen prompts." The pipeline outcome is "output under 800 characters on six case prompts." The experiment shows that models which give very short answers on some prompts give very short answers on others. Two of ten models failed. The interval [+0.549, +0.722] resamples the six cases; the unit that matters is the model, and there are ten.

The paper presents the gate as the answer to "per-model signatures" (Table 1). The tested screen has no connection to domain signatures. The signature probe and format test described in §4.1 of the paper were not validated; the format test failed to predict anything (a model that scored 0 of 4 on it seated without defects).

### 4.6 "Self-assessment at chance", "corroboration is ignored", "per-model signatures"

**Self-assessment.** The abstract says elicited self-assessment "predicts behavior at chance." The three results behind it:

- Deferral: 0.306 out of domain against 0.083 in domain, a ratio of 3.7 in the predicted direction. The six-item clustered interval spans zero; the unclustered one does not (runbook L7037–7060).
- Plausibility: 0.544, with a registered verdict of NOT EVALUABLE against a minimum detectable value of 0.68 (L7694–7700).
- Ownership: 0.500 [0.323, 0.739] on 28 runs, same minimum detectable value (L7814–7819).

These are three underpowered tests. `STATUS.md` §6.9 forbids citing an uninformative null as evidence of absence. The paper does so in its abstract and builds a mechanism on it. Asking a model "which analyst would you rely on for this figure" is also not self-assessment.

**Corroboration.** The paper's "claims advanced by two or more proposers transport no more often" is Cell 26: the keyword instrument the program banned three days later, applied to archived runs whose prompts dictated the phrases it counts, and reported for the "modeled" construct, whose wording in the output PD-13 later showed to be almost entirely the dictated phrase (0 of 30 without the clause, 28 of 30 with it). An output that is driven by the instruction cannot respond much to how many seats raised the point. The other three constructs in the same analysis showed large positive effects of corroboration (+0.39, +0.43, +0.20; composite +0.163 [0.13, 0.20], runbook L3833–3838). The paper reports the one null and omits the three positives.

**Signatures.** "Two medical fine-tunes of the same base model do not share a domain signature" compares +0.232 [+0.072, +0.412] with +0.109 [−0.056, +0.300]. The intervals overlap almost entirely. One estimate clearing zero and the other not is not evidence that they differ.

### 4.7 The instrument under most of these results

The paper calls its two-judge sentence protocol validated and reports raw agreement of 0.91. Raw agreement is uninformative when one answer dominates. On the deployed corpora:

| corpus | construct | raw agreement | agreement expected by chance | kappa | overlap of flagged sentences |
|---|---|---|---|---|---|
| Cell 41 (15,485 sentences) | modeled | 0.910 | 0.878 | 0.26 | 0.18 |
| | jurisdiction | 0.833 | 0.717 | 0.41 | 0.34 |
| | hedging | 0.828 | 0.763 | 0.28 | 0.22 |
| Cell 46 (5,623 sentences) | pooled | 0.838 | 0.752 | 0.35 | 0.28 |
| Cell 30/31 (1,899 sentences) | pooled | 0.833 | 0.772 | 0.27 | 0.22 |

"Overlap" is the number of sentences both judges flag divided by the number either flags. Of the sentences that either judge marks as qualified, both mark roughly one in four. The registered acceptance bar for this instrument was raw agreement of 0.70. Pooled chance agreement in these corpora is 0.75 to 0.78, so two judges answering independently at their own base rates would pass.

The instrument was validated in Cell 23 on a sample selected to be rich in positives (20 to 40 percent), where kappa was 0.51 to 0.66, and on twenty anchor sentences written inside the project. The judges did recognize the twelve hand-written positives (12 of 12 and 11 of 12), but the reported anchor accuracy of 0.90 and 0.925 sits just above the 0.85 a judge would score by answering "no" to everything. The instrument was then deployed at natural prevalence, where most constructs are flagged in fewer than one sentence in five. The program named this exact failure when it rejected its paraphrase matcher (runbook L5864, "agreement is base-rate inflation") and when it recorded finding #3 (validated on one task, used on another). It did not apply the check to its primary instrument.

The instrument's recall can be estimated on sentences that are positives by construction. In Cell 41, sentences containing the instructed phrase "modeled at" were labelled as assumption-marking by both judges 66 percent of the time. Sentences containing the synonym "taken to be" were labelled so 35 percent of the time. The instrument is therefore sensitive to wording, twice as sensitive to the program's house phrase as to its synonym, and misses most instances of a hedge it was not exposed to. The phrase-swap null ("nothing beyond the named phrase changed") was measured with this instrument. A real increase expressed in new wording could be missed, and the registered minimum detectable effect of 0.22 does not account for that.

No sentence label in the program has been compared with a human label.

---

## 5. The system described is not the system tested

**The proposers are the aggregator.** In Cells 41, 43, 44, 46, 47, 48, 51, 52, 54, 59 and 61 the three seats are `gpt-oss:20b` under prompts of the form "You are a healthcare analyst advising a decision-maker…". For several cells a single stored output per role per case is reused. Fine-tuned domain models appear only in the keyword-instrument era and in Cells 36, 42 and 55. The title says "Specialist Aggregation Pipelines." The tested object is one model answering three role prompts and then summarizing itself.

**The baseline is not the published recipe.** MoA as published uses six different proposers of 70B and above, several layers, and the full prompt at every agent. The paper's "unmodified pipeline (the recipe as published…)" is one layer of three same-model role prompts and a one-sentence lead prompt. The preference lift over a single direct answer is the only gain the paper says the harness keeps. That comparison is four model calls against one, with no baseline of equal cost (best of four, self-consistency, or a longer single answer). Self-MoA and "More Agents Is All You Need" both show that sampling one model several times and aggregating helps, so the role decomposition has not been shown to add anything.

**The assembled harness differs from its tested parts.**

| Component | What was tested | What the assembled harness runs |
|---|---|---|
| Caveat channel | Sentence-level two-judge labels, about 17 caveats per artifact (Cell 48) | Document-level prompt, at most one quote per construct per seat, about 5 per artifact |
| Planner | Told which single quantity to cover (Cell 59) | Covers its own list of quantities; coverage checked by a rough word match |
| Follow-up | Frozen item-specific questions; the seat is handed the deciding fact as "private working notes" (Cell 54) | A generic follow-up sent for the first tension line that contains a role name; the seat has no private information |
| Seating gate | 800-character screen on ten models (Cell 55) | The same screen on the one model used for every seat |
| Content gate | Failed twice | Off |

**No end-to-end outcome.** The assembled harness was compared with the baseline on judge preference only, and that comparison was graded not evaluable. Its effect on wrong values, on caveats reaching the reader, or on resolving disagreements was never measured as a system. The paper says the rows of Table 2 are separate experiments. The title, abstract and Figure 7 ("Outcomes before and after the harness") still present a hardened system.

**Cost is missing.** The integration run records 14 to 18 minutes per inquiry. By the code, one inquiry makes about fourteen model calls against four for the baseline. The paper says the harness comes "at no cost."

**Correctness was never shown.** By the runbook's own scorecard (L1996–2007), a single 20B model beat the council on rubric coverage (42 percent against 25 to 31) and matched or beat it on the three disposition measures. On the accuracy battery it scored 0.966 against the council's 0.933 (L5481–5482). The two later batteries stopped at a ceiling before any council run. A paper about advisory use in healthcare, law and finance has no evidence that its system gives answers that are more correct, or no less correct, than one model.

---

## 6. Statistical inference

**Too few independent units.** The cases number 18, written in-house. The harness results rest on 6 items (Cells 44, 54), 8 (Cells 47, 59) and 11 (Cell 51). A percentile bootstrap over 6 to 11 clusters gives intervals that are too narrow. Recomputed at the cluster level:

| Result | Paper | t-interval on item differences | exact sign-flip test |
|---|---|---|---|
| Cell 47, drop in corrupted value | 0.450 [+0.200, +0.725] | [+0.095, +0.805] | p = 0.031 |
| Cell 47, rise in clean value | 0.500 [+0.175, +0.825] | [+0.090, +0.910] | p = 0.063 |
| Cell 59 (live), drop in corrupted value | not reported | [−0.069, +0.419] | p = 0.22 |
| Cell 59 (live), rise in clean value | +0.425 [+0.325, +0.525] | [+0.285, +0.565] | p = 0.008 |

A sizing sketch that resamples Cell 47's eight item effects gives that design about 63 percent power to detect an effect as large as the one it reported.

**Conditioning on a small, selected subset.**

- Preference shares are computed only on pairs the judge decided the same way in both orders, which discards 60 to 95 percent of pairs. Counting ties as half, the "0.818" lift is 0.611, and the phrase penalties of 0.261 and 0.317 are 0.413 and 0.440. Which pairs survive is not random (prior work shows consistency rises with the quality gap), so the conditional share overstates the typical difference.
- Re-consultation effects are computed only on runs where the lead named the planted tension: 7 of 36 in the informed arm against 15 of 36 in each other arm, although stage one is identical across arms. The control's "0.333" counts seven runs where the two judges disagreed as failures; among runs where they agreed it is 5 of 8. Over all runs the informed arm reached the intended resolution in 15 of 36 against 10 of 36.

**Comparators from a different day.** Cell 54's live arm (August 25) is compared with Cell 44's stored control (August 19). The trigger rate in the new batch was 0.583 against 0.34 in the old one, which shows the batches differ. Cell 61's harness outputs (September 1–2) are compared with outputs stored on August 12–13.

**"No difference" is asserted without a margin.** Cell 61's primary interval is [0.375, 0.765] on 48 pairs. The second judge leans against the harness. No equivalence margin was registered. "The null is the correct outcome rather than a shortfall" is advocacy.

**Many tests, no adjustment.** Roughly ninety registered predictions plus unregistered readings, with the positive ones selected into the paper. The registered-versus-exploratory distinction the runbook keeps is lost in the paper.

**Precision.** Shares such as "1.000 (7/7)" and "0.905" (19 of 21) are printed to three decimals.

---

## 7. No measurement comes from outside the project

- Every judge is a local model of 7 to 30B. Every "reader" is a model. No human rated an answer, read an appendix, or labelled a sentence.
- The labels the runbook calls "analyst-authored" or "manual" appear to have been produced by the AI assistant that designed the experiments. The Cell 56 registration describes its classifier as an analyst with a "knowledge cutoff January 2026" and "no web access" (runbook L8553–8562). The same applies, as far as the record shows, to the 41 planner labels and 493 confirmations in Cell 57 and the twenty anchors in Cell 23. Hypotheses, items, labels and analysis come from one source.
- The cases, planted facts, caveats and decision questions were all written in-house. No public benchmark and no third-party data appear anywhere.
- The fabrication blocklist was "validated" at 21 hits, 0 false, 0 missed on the same 141 replies its three names were taken from.

---

## 8. Registration, audit trail and disclosure

**Registration is real but weaker than stated.** The registrations exist, are specific, and in git they precede their verdicts. They are self-registered in the author's repository, the run data were committed weeks later, and the records carry no timestamps (Section 3, item 4). An outside reader cannot verify the order of registration and data collection.

**Deviations are frequent and the paper mentions none.** The runbook records each of these, to its credit:

- the instrument was replaced after the registered one failed its gate, and the registered bars were then "read as sign tests" (Cells 30, 31);
- a pilot bar was lowered from 0.5 to 0.25 after it failed (Cell 53);
- gates were re-evaluated after rescoring (Cells 47, 59);
- two ambiguous registrations were read in the way that let the verdict or the run stand (the agreement population in Cell 44, the pooled floor in Cell 51);
- item values were changed after a pilot (Cell 47);
- token budgets were raised mid-cell (Cells 60, 61).

A reader of the paper would assume the registered protocol ran as written.

**The audits are self-audits.** `docs/PROGRAM_AUDIT_2026-08-07.md` is titled "the auditor auditing itself" and was triggered by the user's concern about "where the assistant's probabilistic generation led the program astray." The runbook is written in the assistant's first person ("I told Sam that…", "a registration error of mine"). The paper calls these "three program-level audits" and lists one human author with no statement of the assistant's role in design, item writing, labelling, analysis and drafting. Venues require that disclosure. It also bears on the science: the instrument-independence rule the program adopted is broken when one agent writes the items and labels the outcomes.

**The error rate in the record is high.** The runbook logs four verdict-printing bugs, three Unicode matching bugs, five token-budget failures, one fabricated illustrative quote that reached a paper draft, and one experiment benchmarked on the wrong condition. This review found two more defects in headline numbers in a day. Others should be expected. The stored flags in `bench/runs/cell47_redundancy.jsonl` (30 of 40) disagree with the analysis file (36 of 40) because scoring was repaired after generation, and the run file is the one committed as the public record.

---

## 9. Prior work

The draft cites six papers. Its novelty statements do not survive a literature check. ✔ marks sources opened and read for this review.

| Claim in the draft | Prior work | What follows |
|---|---|---|
| "Every published MoA number is produced by an LLM preference judge" | ✔ Wang et al. 2024 (arXiv:2406.04692), Appendix D: MATH accuracy rises 0.500 → 0.570 → 0.576 over three layers. ✔ Li et al. 2025, Self-MoA (arXiv:2502.00674), the draft's own reference: accuracy on MMLU, CRUX, MATH. | Delete. Say the headline MoA results are judge-based. |
| "No published evaluation measures … whether a corrupted proposer corrupts the final answer" | ✔ Wolf, Yoon, Bogunovic 2025 (arXiv:2503.05856): one deceptive agent in a 3-layer MoA cuts the AlpacaEval 2.0 win rate from 49.2% to 37.9% and QuALITY accuracy by 48.5%; unsupervised voting-style defenses recover most of it. Also Huang et al. (arXiv:2408.00989) on faulty agents and Amayuelas et al. (arXiv:2406.14711) on adversarial debate. | Delete. Present Cells 35–47 as a small numeric-value variant with a co-source control. |
| A sole-sourced wrong value is adopted at 0.90; the aggregator "never verifies" | ✔ Wu, Wu, Zou 2024, ClashEval (arXiv:2404.10198): six models adopt incorrect supplied content over a correct prior more than 60% of the time, less when the error is blatant. ✔ Xie et al., ICLR 2024 (arXiv:2305.13300): models are highly receptive to coherent external evidence. Sun et al. 2024 (arXiv:2406.19228): models copy a silently faulty tool. | Cite as known behaviour. The MoA paper itself says its aggregator "does not simply select." |
| Engineered redundancy | Xiang et al. 2024, RobustRAG (arXiv:2405.15556): isolate-then-aggregate with a certified bound. Weller et al., EACL 2024 (arXiv:2212.10002): answer redundancy as a defense. Wolf et al.'s defenses. | Cite and compare against these as baselines. |
| "Corroboration is ignored" | Xie et al. and Jin et al. (arXiv:2402.14409) report that models follow the majority of evidence; Huang et al., DiverseSumm (arXiv:2309.09369), that frequent content is covered more. The program's own data agree in three of four constructs. | Withdraw. |
| Judges penalize the hedge phrase; instruction and preference "in direct tension" | ✔ Lee et al., NAACL 2025 (arXiv:2410.20774): all tested judges including GPT-4o are biased against epistemic markers, most against uncertainty markers. ✔ Zhou et al., ACL 2024 (arXiv:2401.06730): human preference data used in alignment are biased against text that expresses uncertainty. | Cite as prior. The contribution is a replication on small local judges with a counterbalanced phrase. |
| First-position preference of 0.85–0.88 is "a task-format property" | Zheng et al. 2023, the draft's own reference, reports position consistency by judge (GPT-4 65%; Claude-v1 23.8%, with 75% favouring the first answer) and scores inconsistent pairs as ties. Wang et al. (arXiv:2305.17926), Shi et al. (arXiv:2406.07791) and Koo et al. (arXiv:2309.17012) show the bias varies by judge, direction and quality gap. | Say the small local judges tested are strongly position-biased. Do not generalize to the task. |
| Prose loses qualification | ✔ Peters and Chin-Yee 2025 (arXiv:2504.00025): summaries from ten models drop scope-limiting detail in 26–73% of cases. ✔ Belem et al., EMNLP 2026 (arXiv:2606.07951): certainty is distorted in up to 75% of rewrites, raised 1.5–2 times as often as lowered. ✔ Wang et al. 2026 (arXiv:2608.29028): multi-agent handoff summaries keep facts and lose usage constraints. | Cite, and fix the measure (Section 4.1). |
| Self-assessment "at chance" | Xiong et al., ICLR 2024 (arXiv:2306.13063): verbalized confidence is overconfident and predicts failure poorly. ✔ Cacioli 2026 (arXiv:2604.22215): pre-registered, seven 3–9B open models. Against a blanket reading: Binder et al. (arXiv:2410.13787), Barkan et al. (arXiv:2512.24661). | Cite and scope. |
| Domain fine-tunes carry no domain signature | ✔ Jeong et al., EMNLP 2024 (arXiv:2411.04118): medical LLMs beat their base model in 12.1% of comparisons, tie in 49.8%, lose in 38.2%. | Cite. It is stronger evidence for the same practical point. |
| "No prior work is known that pre-registers each component…" | van Miltenburg et al., NAACL 2021 (arXiv:2103.06944); the NeurIPS 2020 pre-registration workshop (PMLR 148). ✔ Vaccaro, ICML 2026 (arXiv:2606.11217): a preregistration template for experiments with AI agents, which lists outcome-contingent redesign among the main risks. OSF-registered LLM evaluations exist (Cacioli 2026). | Delete the priority claim. Move registration to a third-party registry. |
| The phrase-swap design is "the first" | No exact precedent found in two passes. Nearest: Yona et al. 2024 (arXiv:2405.16908) and Liu et al. 2025 (arXiv:2505.24858) on prompted hedges that do not track model uncertainty; Leidinger et al. 2023 (arXiv:2311.01967) on synonym-level prompt variation. | Keep as a contribution. Write "we are not aware of" in place of "the first." |
| The appendix channel | No exact precedent found. Nearest: RARR (arXiv:2210.08726), DebUnc (arXiv:2407.06426). Kim et al., FAccT 2024 (arXiv:2405.00623), N=404, shows that the wording of uncertainty decides its effect on human readers. | Keep, and test with human readers. |

Method references the revision should use: Cameron, Gelbach and Miller 2008 on inference with few clusters; Miller 2024, "Adding Error Bars to Evals" (arXiv:2411.00640); Bowyer, Aitchison and Ivanova, ICML 2025 (arXiv:2503.01747); Lakens 2017 on equivalence tests; Gelman and Carlin 2014 on magnitude errors; Davidson and Beaver 1977 on paired comparisons with ties and order effects.

The search passes judged that three measurements are new in the MoA setting: caveat survival, claim-level corroboration, and numeric corruption with a clean co-source control. The phenomena themselves are established.

---

## 10. The paper as an argument

**Hypothesis.** The paper states no research question. The program's founding question, in the README, is whether a council of specialists gives better answers than one model. The runbook answers it: "A four-model council, on every axis we could measure, is matched or beaten by one model of comparable size with a good instruction — at roughly a quarter of the compute" (L2005–2007). That finding is absent from the paper, which opens instead from the premise that the pipeline is worth hardening.

**Premises attributed to "the recipe."** The paper says it falsifies premises "the recipe depends on": that the aggregator verifies, that caution reaches the reader, that self-assessment can trigger escalation. The MoA paper claims a preference lift and says its aggregator does not simply select. It makes none of those three claims. "Production variants cast the proposers as domain specialists" has no citation. As written the paper refutes positions it has assigned to others.

**Structure.**

- Section 3 reports about twenty numbers before Section 5 explains how anything was measured.
- Table 1 asserts a link from each "failure" to each "mechanism." Two links do not follow: the seating gate has nothing to do with signatures, and artifact-triggered re-consultation rests on the underpowered self-assessment results.
- "No mechanism is included on rationale" (§1) is contradicted by §4, which keeps isolation on a cost rationale, a charter that is a policy, and two gate components that were never validated.
- Figure 7 draws separate experiments as a before-and-after chart of one system. Its "0.000" baseline for clean adoption is a structural zero: that value did not exist in that arm.
- The "central result" is a comparison the registration graded not evaluable.
- Related work is three short paragraphs at the end. There is no limitations section; the scope caveats are two sentences in the impact statement and one appendix paragraph.

**Diction.** The prose is fluent and overconfident, and it leans on vocabulary the reader has to decode.

| In the draft | Problem | Use instead |
|---|---|---|
| "hardening" | A security term that implies a threat model; none is defined | "adding checks to" |
| "evidence-bound", "licensed by", "kill condition", "survived", "demoted", "verdicted" | Coined or legalistic; "verdicted" is not a verb | "each part has a registered test", "motivated by", "failure criterion", "passed", "dropped", "tested" |
| "auditable MoA instance", "auditable scale" | Means small enough to run locally | "a small local pipeline" |
| "the recipe" (about thirty uses) | Blurs the published MoA with the local pipeline | Name which one each time |
| "instruction tuning" (L182) | A training method; the experiment varies a prompt | "prompt instructions" |
| "seats", "chairs", "lead" | Three metaphors for MoA's two roles | "proposers", "aggregator" |
| "carriage", "uptake", "trigger rate", "decisive pairs" | Undefined at first use | Give numerator and denominator |
| "never recomputes", "never verifies", "installs only its named phrase", "exactly 0.500", "at chance", "is causal", "fixes", "at no cost" | Absolutes on samples of 7 to 40 | State the count, the interval and the scope |
| "The null is the correct outcome rather than a shortfall" | Advocacy | Delete |

The abstract is one block of about 300 words containing eleven statistics and no sample size.

**Conclusion.** It restates the abstract, adds that the survivors have "causal or predictive effect sizes," and ends on a slogan ("a pipeline whose every component can say which experiment it survived"). It names no limitation and no next step. A conclusion the evidence supports would read: on one 20B model and eighteen in-house cases, four component behaviours were observed under controlled inputs, the assembled system was indistinguishable from the baseline on a weak preference test, and whether any of it helps a human decision-maker is unknown.

**The proposal on its merits.** The five mechanisms are reasonable engineering. Screening out models that return fragments is hygiene. Asking two proposers for the same key figure is a sensible way to expose disagreement, and it needs a rule for what happens next, since the writer's choice is arbitrary. Routing a follow-up question is sensible. Putting caveats in a separate block is a plausible design that needs evidence from human readers and a measured extraction recall. The charter is a policy. None of the five has been shown to improve an outcome a user would care about.

---

## 11. The runbook as a research record

It is the strongest artifact in the repository and the reason this review could be done. Three things about it should change how the paper is written.

- **The question changed at least seven times.** Disposition training, "The Last Writer Wins", "Rendered, Not Transported", "Witnesses, Not Amplifiers", the retracted calibration paper, "What Aggregation Does", the shrinkage law, the MoA audit, the harness. Each framing was built on the same runs and replaced when its support failed. Documented reframing is better than silent reframing. It is still fitting a story to data, and the current framing is the one that had not yet been checked from outside.
- **The pattern of the positive results.** The early cells measured natural behaviour and mostly found nothing. The later harness cells each produce a positive result under a design that makes the outcome close to guaranteed: an instruction to include the figure, an appendix scored against itself, one decisive sentence before the question, length predicting length, a seat handed the answer. The registrations are sincere. The designs test whether the plumbing works, and the paper reports them as findings about model behaviour.
- **Rules the program wrote and the paper breaks.** Uninformative nulls are not evidence of absence (broken in §3.6 of the paper). Keyword instruments are provisional (Cell 26 is in the paper). One factor per comparison (Cell 61 is a bundle). Report output volume beside any rate (the "neither" counts are missing from Figure 4).

---

## 12. Conditions for re-examination

The paper can be resubmitted when all of the following are done.

1. Every item in Section 3 is corrected in the paper, `STATUS.md`, the harness note, the companion and the public site.
2. The title, abstract and setup state that proposers and aggregator are the same 20B model, that the baseline is a role-prompted self-ensemble, and what the assembled harness actually runs.
3. The sentence instrument is reported with chance-corrected agreement and checked against human labels (Section 13, step 1.1). If it fails, results that depend on it are marked provisional.
4. Every interval is recomputed at the case or item level with a method suited to few clusters, and every preference result is reported on all pairs with ties shown.
5. Transport is reported as a relative measure; carriage is measured with a matcher validated against human judgement or removed; "adoption" is retested on items that can be verified, or the claim is reduced to "repeats a sole-sourced figure on request."
6. The paper's §3.6 (self-assessment) and the first sentence of its §3.4 (corroboration) are withdrawn or restated at the strength their own verdicts allow.
7. Related work is rewritten with the sources in Section 9 and every priority claim is removed or softened.
8. Limitations, compute cost, a deviations table, a data statement with a commit hash, and a statement of the AI assistant's role are added.
9. At least one end-to-end test of the assembled harness on its own claimed outcomes is run with a concurrent baseline (step 2.3).
10. One human who did not work on the project reruns the analysis from the raw records and signs off on the numbers.

Items 1 to 8 need no new model runs.

---

## 13. Program of work

The standing pre-recommendation checklist (`STATUS.md` §6) was applied to each proposal below; the items that constrain a design are named. Applying it changed two of my first drafts: step 1.1 moved from a random sample to a stratified one (item 12, too few positives otherwise), and step 2.1 dropped the "include this figure" line in favour of an outcome the question itself requires (item 12: how often the outcome can occur is a check made before the run, and a prompt built to force it measures compliance with the forcing).

### Stage 0: corrections and re-analysis (days, no model calls)

- **0.1** Fix the carriage parse. Publish 0.030 with the note that it is a verbatim-copy rate.
- **0.2** Replace run-level and percentile-bootstrap intervals with case-level analysis: aggregate to case or item means, then a paired t-interval and an exact randomization test; or a mixed-effects logistic model with random intercepts for case and item; or a wild cluster bootstrap. Report the number of clusters beside every estimate.
- **0.3** Preference: report win, loss and tie counts for every comparison. Fit one model to all single-order judgments (first-listed answer wins, with terms for arm and position and a random intercept for case), or a Davidson model with an order effect. This uses all 252 judgments per comparison where the current analysis uses 41 to 48 pairs.
- **0.4** Transport: report the qualified share of sentences in and out, and the slope with output length as a covariate.
- **0.5** Re-consultation: report all-run outcomes beside the conditional ones, and the control with disagreements handled both ways.
- **0.6** Choose at most five confirmatory hypotheses for the paper, apply a Holm correction across them, and label everything else exploratory. Register an equivalence margin before any claim of "no difference."
- **0.7** Add to every future run record: UTC timestamp, model digest, temperature, seed, prompt hash, and the registration commit it ran under. Commit run records with the verdict.

### Stage 1: human ground truth (two to three days of annotator time)

- **1.1 Sentence labels.** Draw 400 sentences from the Cell 30, 41 and 46 corpora: 200 flagged by either judge, 200 flagged by neither, balanced across the three constructs and across seat and writer text. Two annotators who did not work on the project label each sentence against the frozen definitions, blind to arm, model and judge label. Report human-to-human kappa, then each judge's precision and recall and those of the both-agree and either-agree rules, weighted back to natural prevalence. Acceptance: human kappa of at least 0.6 and instrument F1 of at least 0.8 against adjudicated labels. If it fails, the transport, invention and phrase-swap residual results are provisional. *Checklist: 2 (annotators see no prompts), 3 (same sentence unit as deployed), 12.*
- **1.2 Preference.** Three people judge 120 pairs (40 per comparison in Cell 43), order randomized, blind to arm. This tests whether the lift and the phrase penalty exist for people, and whether the judges' consistent pairs agree with them.
- **1.3 Caveat conveyance.** For 200 (caveat, answer) pairs, a person records whether the caveat is conveyed fully, partly or not. Use these to validate an automatic matcher, then rerun Cell 48's prose arm.
- **1.4** A person repeats a 25 percent sample of the Cell 56 and Cell 57 label tables.

### Stage 2: new experiments

- **2.1 A corruption test in which verification is possible.** Replaces Cell 47.
  - *Items:* at least 40, across at least 20 cases, drawn from public material where possible. Each question requires a derived quantity (a total, a ratio, a deadline) that depends on one input figure, so the outcome occurs without a prompt to include it.
  - *Factor:* how the wrong input can be caught. (a) Sole source, not checkable. (b) Sole source, but inconsistent with primitives stated in the case. (c) A second proposer gives the correct figure. (d) A second proposer gives a different wrong figure.
  - *Arms:* the pipeline; a single model given the same texts in one context; a self-consistency baseline of equal cost. Two writer families at minimum.
  - *Outcome:* the derived quantity, scored by exact match as consistent with the correct input, the wrong input, or neither; and, validated against human labels, whether the answer flags the inconsistency.
  - *Analysis:* item-level paired differences; mixed-effects logistic regression with item and case intercepts.
  - *Size:* resampling Cell 47's item effects, 40 items at 3 repeats gives over 90 percent power for a two-condition contrast even if the true effect is half the reported one, with an interval of about ±0.11 to ±0.14. The pipeline arm is 40 × 4 × 3 = 480 writer calls per writer family, about 20 hours at the measured 154 seconds each; the two comparison arms roughly triple that.
  - *Checklist: 1 (one factor), 5 (paired items), 7 (describe as selection, drop "immunity"), 11 (report the neither category), 12.*
- **2.2 The founding question, with headroom.** Take public items with checkable answers in the three domains (for example MedQA, LegalBench tasks, FinQA or TAT-QA, QuALITY). Keep the subset on which the single model scores between 40 and 80 percent, screened on the baseline only, as Cell 60 specified. Compare four arms at matched cost: direct answer; four samples with a vote; the role-prompted pipeline; the harness. Report accuracy and attempt rate. Add 60 advisory answers scored blind by two domain-literate people on the existing case rubrics, with their agreement reported. *Checklist: 1, 5 (equal compute), 11, 12.*
- **2.3 One end-to-end test of the harness.** Four arms run in the same session on fresh cases: full harness, harness without the planner's redundancy, without the appendix, without the follow-up loop. Outcomes: the 2.1 measure, the 1.3 conveyance measure, and tokens and minutes per inquiry. Twenty-four cases at three repeats is 288 pipelines, about 72 hours at the measured rate. The caveat extractor must be the one the paper describes, with its recall against the 1.1 labels reported. *Checklist: 1, 5 (concurrent baseline), 9 (a full factorial is the costlier alternative).*
- **2.4 Readers.** Preferably 60 to 100 human participants, each reading four reports and making a decision, randomized to no caveat, caveat in prose, caveat inside a real extracted appendix of 5 to 17 items, or an irrelevant appendix of equal length; registered on OSF; analysed with participant and item effects. As a cheaper interim: readers from three model families, a neutral system prompt that does not point at attachments, the caveat at a random position inside a real appendix, a length-matched control, and a curve of uptake against appendix size.
- **2.5 Phrase-swap, extended.** Five instruction types (hedging, stating assumptions, citing the source, giving numeric confidence, deferring), two phrasings each, three writer families, outcomes from the instrument validated in 1.1. To claim "no effect beyond the phrase" an equivalence test is needed. By the program's own arithmetic (minimum detectable effect 0.224 at 18 cases), a margin of ±0.15 needs about 60 cases and ±0.10 about 135, at three repeats each. Hand-writing that many is impractical, so draw the prompts from a public source.
- **2.6 Scope.** Either rerun the three results the paper leans on most (phrase-swap, preference penalty, sole-source behaviour) on three writer families including one much larger model, or state in the title that the findings concern one 20B model.

### Stage 3: process

- Register confirmatory studies with a third party (OSF or AsPredicted) before running. At minimum, push the registration commit before the first run and record the push time.
- Separate roles: whoever writes items does not label outcomes. Labels come from people, or from a model family that took no part in the design, applied blind.
- Keep a deviations table and publish it with the paper.
- Fix one question and one paper outline before the next experiment, and stop reframing.
- State the assistant's role in the paper.

---

## 14. Publication route

- **Now, after the Section 3 corrections:** a technical report or preprint, titled for what it is (for example, "What a small role-prompted pipeline does with planted figures and caveats: a registered component study"). Note that the repository and site are already public and currently carry the uncorrected numbers.
- **Closest to publishable:** a short methods paper on evaluation pitfalls in LLM pipelines, built from the measurement lessons in Section 2 with Section 4.7 added as a lesson of the same kind. It suits a workshop on evaluation or negative results and needs only Stages 0 and 1.
- **Second:** the phrase-swap and preference-penalty result as a focused empirical paper, positioned as a replication and extension of Lee et al. and Zhou et al., after steps 1.1, 1.2, 2.5 and 2.6.
- **The harness paper:** only after steps 2.1 to 2.4. Until then it is a design proposal.

---

## Appendix: reproducing the numbers in this review

```
.venv/bin/python bench/analysis/board_review/checks.py
```

| Section of output | Supports |
|---|---|
| 1. Redundancy | §4.3 item table; §6 cluster-level intervals and tests; the 30/40 versus 36/40 note in §8 |
| 2. Caveat carriage | §3 item 1; appendix sizes in §4.4 and §5 |
| 3. Two-judge instrument | §3 item 10; §4.7 agreement table and recall on instructed phrases |
| 4. Transport | §3 item 2; §4.1 share table |
| 5. Preference | §3 item 3; §6 ties-as-half figures |
| 6. Re-consultation | §6 conditional versus all-run counts |
| 7. Version history | §3 item 4 |
| 8. Cell 23 validation | §4.7 anchor and validation-sample figures |
| 9. Reader uptake | §4.4 control length, second reader, removed items |
| 10. Seating gate | §4.5 |
| 11. Sizing sketch | §6 power figure; §13 step 2.1 size |
| 12. Content-word overlap | §4.2 illustration |
| 13. Verdict tally | §2 and §6 counts of predictions and registrations |

The sizing sketch resamples the eight Cell 47 item effects (shrunk slightly away from 0 and 1), draws the stated number of items and repeats, and applies a paired t-test at the item level. The content-word overlap in section 12 of the output is an illustration and is not a validated measure. The verdict tally is a pattern match and misses some formats.

---

## Addendum A (2026-10-01): single-operator version of Sections 12 and 13

The author works alone, with limited outside help, on one machine. Checked on this date: Apple M5, 32 GB of memory, 46 GiB of free disk, and these models in Ollama: `gpt-oss:20b`, `phi4:14b`, `qwen3-vl:30b-a3b-instruct`, `qwen2.5:7b-instruct`, `llama3:8b-instruct`, `mistral:7b-instruct-v0.3`, `deepseek-r1:7b`, the domain fine-tunes, and the embedding model `nomic-embed-text`. This addendum replaces every step in Sections 12 and 13 that assumed other people.

### A.1 Steps that need no models and no other people

All of Stage 0 and all of the rewriting: the carriage fix, case-level intervals, preference with ties, transport as shares, all-run outcomes, the choice of at most five confirmatory hypotheses, the new title and scope, related work, limitations, cost, the deviations table, and the statement of the assistant's role.

Outside timestamps also need no other person. OSF and AsPredicted are free and self-service. The lighter option is to push the registration commit before the first run and open a GitHub issue that quotes the commit hash, since the issue's creation time is set by GitHub. Each run record should store the UTC time, model digest, seed, prompt hash and registration commit.

### A.2 Steps redesigned for one machine

| Step in Section 13 | Single-operator version | Cost | What is given up |
|---|---|---|---|
| 2.1 Corruption test on checkable items | Reuse the Cell 60 and 60-R items, whose answers are computed by the generator scripts. 61 of the 66 have a numeric input that appears once in the prompt and changes the computed answer when altered (checked with the item engines). Wrong inputs are set by a fixed rule and the answer under the wrong input is recomputed by the same engine. Proposer text is three short scripted analyst notes. Scoring is the existing answer-line parser. No item is written by judgment and no judge is used. Design below. | 61 items × 5 conditions × 2 repeats = 610 runs per writer, one to three minutes each: about a day of machine time per writer | Realistic long proposer text. Recovered in the live version on the next row. |
| 2.3 End-to-end test | The same items through the live chain: Cell 59's private-note mechanism puts the wrong figure in one seat and, in the redundancy arm, the right figure in a second. Cell 60's council runner already exists and was never run past its pilot, so budget a shakedown. Outcome is again the computed answer. | 61 items × 2 arms × about 15 minutes: about 30 hours | Repeats (one per item per arm). The caveat and follow-up arms wait. |
| 2.4 Human reader study | A reader study across six local models from five vendors. One factor: appendix size (1, 5, 10 items, as many as the case supplies), with the planted caveat at a seeded random position among real extracted caveats. A neutral reader prompt that does not mention attachments. The irrelevant control padded to equal length. Items: the 11 that passed Cell 51's floor gate. | About 2,000 short reads (11 items × 3 sizes × 2 caveat types × 5 repeats × 6 readers), a few seconds each: one night | Any claim about people. The paper says "model readers" and lists human readers as open. |
| 1.2 Human preference panel | No human claim. Add three judge families (`llama3:8b`, `mistral:7b`, `phi4:14b`, plus `qwen2.5:7b` on all pairs) on the existing 378 pairs in both orders, and analyse every single judgment: a logistic model for "the first-listed answer was chosen", with a position term per judge and a term for which arm is listed first. | 756 calls per judge; 4 to 20 hours per judge | Human preference. The claim becomes "local judges of 7 to 30B". |
| 1.1 Two outside annotators | The author labels blind (A.3), and four more local judges label the same 400 sentences so that the counting rule (both agree, either, majority) can be chosen on one half and tested on the other. A latent-class estimate across the judges is a second check that does not use the author's labels. | About one hour of machine time per judge | Independence from the author. |
| 1.3 Caveat conveyance; relative transport | Shortlist with `nomic-embed-text`: the three prose sentences closest to each caveat. Two local judges then rate "conveyed fully, partly, or not" on that short context. Validate against 120 pairs labelled by the author. Run the same matcher on a sample of unqualified input sentences to get the relative measure Section 4.1 asks for. | About 11 hours for all 2,037 caveat pairs | Nothing, if the validation passes. |
| 2.2 Founding question | Public items with checkable answers, screened on the single model for headroom, scored by exact match. Arms: direct, four samples with a vote, pipeline, harness. | Two to three nights at 60 items; 60 items detect only a gap of about 15 points | Expert scoring of the advisory answers. |
| 2.5 Phrase-swap with an equivalence margin | Keep the registered claim ("no effect of 0.22 or more") and repair the instrument on the stored Cell 41 outputs with the rule chosen in step 1.1. An equivalence claim needs 60 to 135 cases and is deferred. | A third judge over all Cell 41 sentences is about 35 hours, and only if step 1.1 calls for it | The stronger "nothing beyond the phrase" claim. |
| 2.6 A much larger model | Not possible in 32 GB. Use three writer families (`gpt-oss:20b`, `phi4:14b`, `qwen3-vl:30b`) and put "14 to 30B local models" in the title. Disk allows one more open model of 24 to 30B from a family not yet present. | Per experiment | Any claim about frontier models. |

**Design of the corruption test.** One factor: where the right and wrong figures sit.

- C0: the case states the figure and the notes repeat it correctly. Run fresh in the same session; do not reuse the Cell 60 direct runs.
- C1: the case states the right figure and one note states a wrong one. The error can be caught.
- C2: the figure is removed from the case and one note states the wrong one. Sole source.
- C3: the figure is removed; one note is wrong and one is right.
- C4: the figure is removed; two notes are wrong with different values.

Outcomes, all by script: the final answer matches the correct-input answer, a wrong-input answer, or neither (with the no-answer rate reported); and whether the reply mentions both figures, which is the measure of whether a disagreement was shown to the reader. In C3 and C4 the writer cannot know which note is right, so the second outcome is the one that matters. Analysis is on item-level paired differences with the fourteen templates as clusters.

### A.3 Where the author is the human

A small script shows one item at a time in random order and hides arm, model, case and judge labels. Labels are written to a file and committed before they are joined to anything.

- 400 sentences, labelled twice at least a week apart. About 100 minutes per pass. The agreement between the two passes replaces agreement between two people.
- 120 caveat-and-passage pairs. About 90 minutes.
- Optional: 40 preference pairs, about three hours. The redesign above does not need it.

The limitation to state in the paper: one annotator, who is the author, working blind.

### A.4 What cannot be replaced

- **An independent rerun.** Make it a one-hour job: one command that regenerates every number in the paper from the raw records, and a table of about 25 numbers to compare.
- **A second annotator.** One person labelling 100 of the 400 sentences takes about 45 minutes and yields an agreement figure between two people.
- **Human readers, domain experts scoring advisory answers, and a much larger model.** These are dropped and the claims are scoped to match.

The whole plan needs about two hours of one outside person. If that is not available, the paper says so.

### A.5 Order of work

1. A.1 in full.
2. The 400-sentence labels and the extra judges. This decides whether the transport and phrase-swap results stand.
3. The corruption test on computed-answer items.
4. The reader study across model families.
5. The added preference judges.
6. If the harness paper is still the goal: the live-chain test, then the public-benchmark test.

### A.6 Checklist notes

Applying the pre-recommendation checklist changed three of these designs.

- Item 3 (instrument validity): a first version replaced human labels with more model judges and a latent-class model. Agreement among models is not validity, so the author's blind labels stay as the anchor.
- Item 5 (baseline matching): a first version reused Cell 60's direct runs as the clean arm. The clean arm is rerun in the same session with the same note text.
- Item 6 (registration honesty): the single-caveat condition of the reader study repeats Cell 51, whose result is known, so it is labelled a replication. The neutral prompt and the larger appendix sizes are the prospective part. The same applies to preference: reanalysis of the two existing judges is descriptive, and the added judges are prospective.
