# Plain-language rewrite: style guide

This guide governs the plain-language edition of the Paper-Hardening Cell Ledger
explorer. The source of truth is `RUNBOOK_PAPER_HARDENING.md` (the lab notebook,
"the ledger") in the repository root, cross-checked against `docs/STATUS.md` (the
list of current claims). Do not use anything under `site_v2/`. It is out of scope.

## Who the reader is

A curious, intelligent reader who is not a scientist: a product manager, a
journalist, a co-author checking the record. They know what AI language models
are and recognize common AI terms. They do not know statistics, research-methods
vocabulary, or this project's in-house nicknames. This edition will eventually
replace the project's public website, so write for the public.

## What the project is (context you need)

The Council of Experts project tested a popular idea: instead of asking one AI
model a question, ask several specialist models and have one more model combine
their answers. Our version (the council) had three specialists (healthcare, legal
and finance) and an editor model that planned the work, sent each specialist a
part of the question, and then wrote the final answer. The models were small open
models (7 to 20 billion parameters) running on one machine, answering 18
business-advisory scenarios.

The early question was about caution: when a specialist flags uncertainty (a
number is an estimate, a rule differs by country, information may be out of
date), does that caution survive into the editor's final answer? Later work asked
whether the editor checks facts, whether instructions change behavior or only
wording, whether AI judges prefer combined answers, and finally rebuilt the
system (the harness) from only the parts that held up.

Every experiment is a numbered "cell". Before each cell ran, the team wrote down
what they expected and what result would prove them wrong. Afterwards they wrote
down what happened, including mistakes and changes to the plan.

## Voice

- Use American spelling (behavior, analyzed, labeled, favor).
- Write as "we" (the research team). Past tense for what happened.
- Plain, direct, concrete. Short sentences, most under 25 words. Active voice.
- Say what was done and what happened. Do not praise the method, the team, or
  the result. Never describe the work as honest, rigorous, careful or brave.
- No hype, no drama, no jokes, no cliffhangers, no rhetorical questions in the
  body text. Titles may be questions.
- Explain a necessary idea in words instead of naming a concept. "We showed each
  pair of answers in both orders and only counted it when the judge picked the
  same winner both times" beats "order-debiased decisive pairs".

## Keep these AI terms as they are

Standard AI vocabulary stays. Readers expect it and the papers use it. Explain a
term in a few words the first time it appears on a page if a reader might not
know it.

DPO, SFT, ORPO, CPO, GRPO, LoRA, RLHF, fine-tune / fine-tuning, preference
training, base model, instruct model, prompt, system prompt, temperature, tokens,
context window, reasoning model, parameters (7B, 20B), Mixture-of-Agents (MoA),
LLM, AI judge, NLI model (natural-language-inference model), position bias, and
model names exactly as the ledger gives them (Phi-4, gpt-oss-20B, Qwen2.5-7B,
Qwen3, Med42, Saul, Qwen-Open-Finance, BioMistral, OpenBioLLM, Mistral, Llama).

## Keep mathematical formulas

Formulas and their symbols stay exactly as the ledger writes them, for example
y = w·s + c, w = 0.158, c = 0.275, (1 − w)/w, or w' = ∏ w_k. Math symbols are
fine inside a formula (·, ×, =, +, −, /, ≥, ≤, ≈, →, ∏). The first time a formula
or symbol appears in a field, say in plain words what each symbol stands for. The
main one:

- y = w·s + c. Here s is how much caution the specialists handed over and y is
  how much appears in the editor's final answer. Cells scored with the keyword
  counter count kinds of caveat. Cells scored by AI judges (Cell 30 onward)
  count sentences that carry a caveat. w is the share the editor passes along
  (for each extra unit supplied, about w more appear), and c is how much the
  editor adds on its own when handed none.

Do not use the ledger's nicknames for these quantities ("transport
coefficient", "shrinkage law", "prior fill"). Use the symbol plus a plain
description. Do not use symbols as prose shorthand outside a formula: write
"fell from 0.96 to 0.15", not "0.96 → 0.15".

## Replace research and statistics jargon

| ledger says | write instead |
|---|---|
| pre-registered, registered, frozen, in advance | we wrote down the plan and what we expected before running it |
| prediction, hypothesis, P25.1 | expectation (keep the id only in the `id` field) |
| supported, confirmed | held up |
| falsified | did not hold up, turned out wrong |
| reversed | the opposite happened |
| partial | partly held up |
| not evaluable, NE at power, CI spans | too close to call with the amount of data we had |
| confidence interval, bootstrap, Wilson, [0.12, 0.51] | plausibly anywhere from 12% to 51% (only when the range matters) |
| significant, CIs disjoint | a clear difference |
| within noise, CIs overlap | no clear difference |
| n = 35 | 35 runs, 35 answers |
| arm, condition | version, setup (for example "the version with the extra instruction") |
| baseline, control | the comparison version, the untouched version |
| endpoint, outcome measure | what we measured |
| confound | a second difference that could explain the result |
| ceiling effect | scores were already near perfect, so there was no room to improve |
| dose, dose-response | amount; does more of it help |
| selectivity, responsiveness, discrimination | knowing when a caveat is called for and when it is not |
| descriptive, exploratory, post-hoc | measured and reported without a pass/fail test |
| deviation, amendment | a change to the plan, written down before seeing results |
| halt, stop condition, gate (in a plan) | a checkpoint we set in advance |
| instrument, measure | measuring tool, scoring method |
| regex, lexicon | keyword counter |
| calibration set, validation | checking the tool against answers we already knew |
| replication, replicate | repeat, check again, second test |
| ablation, ablate | removing (a sentence, a clause, a step) to see what changes |
| corpus | collection of saved answers |
| decisive pairs | matchups where the judge picked the same winner both times |
| null result | no effect, no difference |

## Replace the project's in-house nicknames

| ledger says | write instead |
|---|---|
| seat, seats | specialist, specialists (name the model if it matters: "the legal specialist, Saul") |
| Lead, synthesizer, writer, aggregator | the editor (the model that writes the final answer) |
| planner, orchestrator | the planning step |
| synthesis, synthesis step | the editor's write-up |
| case, cases, battery | scenario(s), set of scenarios |
| trigger-light / trigger-free case, case-7 gate | a simple control question that calls for no caveats |
| qualification, hedging, disposition, epistemic marking | caveats, cautious language, flagging uncertainty |
| the five families (cutoff, modeled, precise, jurisdictional, hedging) | five kinds of caveat: "my information may be out of date", "this number is an estimate", "these two terms mean different things", "the rules differ by place", and general hedging |
| density, CDS | how much cautious language (per 1,000 characters) |
| register, intrinsic register, band | the editor's habitual level of caution |
| transport, transport coefficient, shrinkage law | keep the formula and symbols (y = w·s + c, w), described in words: the share of the specialists' caution that reaches the final answer |
| prior fill, invention, compensating invention | caution the editor adds on its own, with nothing prompting it (the symbol c may be kept) |
| supply | how much caution the specialists handed over |
| PRESERVE clause / instruction | the instruction telling the editor to keep the specialists' caveats |
| gain control | a volume knob |
| freight, appendix channel, out-of-band | a separate caveats section attached to the end of the report, which the editor never touches |
| harness | the rebuilt system (introduce it as "the rebuilt system, which we call the harness") |
| re-consultation, routed follow-up, dispatch | sending a follow-up question back to a specialist |
| tension, tension list | a disagreement between specialists; a required list of those disagreements |
| ritual, filler reply | a reply that sounds helpful but adds no new information |
| deferral | a specialist saying "this is not my area, ask the X specialist" |
| seating gate, S1 screen | the screening test a model must pass before it can serve as a specialist |
| degenerate output | garbled, repetitive or empty output |
| blocklist gate | a filter that blocks known made-up citations |
| content gate | a filter meant to catch replies with no real content |
| fabrication, backfill | made-up details; filling a gap with invented specifics |
| provenance | labels showing where each statement came from |
| dictated phrase, scaffold | the exact wording our prompt told the model to use; scripted wording in the prompts |
| de-scaffolded | with all scripted wording removed from the prompts |
| entanglement | whether a caveat is tied to a specific fact in the same sentence |
| corroboration, agreement weighting | whether a point several specialists agree on is more likely to survive |
| attainability | whether the test could realistically detect the effect with the data available |
| Goodhart | the risk that pushing a number up distorts the thing it is meant to measure |
| budget exhaustion | the model used up its length allowance while thinking and returned nothing |
| item-bimodal | it worked completely on some questions and not at all on others |

## Never use

These read as machine-written or as insider jargon. The checker flags them.

load-bearing, honest, honestly, honesty, owned (as in "error, owned"), on the
record, full prominence, graduate(d), travel(s/led) for results, buy/buys as a
metaphor, ship/ships/shipping, lever, surface as a verb, signal, crucial(ly),
notably, importantly, genuine(ly), fundamental(ly), delve, landscape, nuanced,
robust, worth noting, in other words, upshot, punchline, headline (as a metaphor),
verdict, falsified, registered, registration, estimand, confound, ablation,
bootstrap, CI, statistically, significant, arm/arms, seat/seats, synthesizer,
aggregator, "the Lead", transport, prior fill, register, freight, ritual,
disposition, qualification, epistemic, provenance, scaffold, entangled,
attainability, Goodhart, bimodal, instrument, regex, lexicon, decisive,
descriptive, exploratory, null, corpus, cohort, strata, variance, tension, gate,
replicate/replication, shrinkage, e.g., i.e., vs.

Punctuation: no em dashes or en dashes (use a period, a comma, or "to" for a
range), no semicolons, no exclamation marks, no "~" for "about". Math symbols
belong inside formulas only (see above). No markdown: no bold,
no headings, no bullet characters, no backticks. Separate paragraphs with a blank
line ("\n\n").

## Numbers

- Use numerals for counts and percentages. Turn proportions into percentages
  (0.818 becomes 82%). Round to whole percentages unless the difference would
  vanish.
- Counts read naturally: "7 out of 7", "4 of 12 runs", "about 1 in 5".
- Every number must come from the ledger entry for this cell (or follow directly
  from it). Never estimate, recompute or invent a number. If you are not sure a
  number is right, leave it out.
- Give a plausible range only when it changes the reading: "28% of runs
  (plausibly anywhere from 12% to 51%)".
- Keep the ledger's own units where they matter and say what they are ("a caveat
  score of 0.15, down from 0.96").
- Formula values can be quoted as the ledger gives them (w = 0.158) next to a
  plain reading (about 16% passed along).

## Accuracy

- Read every ledger entry listed for your cells in full before writing.
- Search the ledger for later mentions of each cell, for example
  `grep -n "Cell 25\|CELL 25\|C25\b\|P25\." RUNBOOK_PAPER_HARDENING.md docs/STATUS.md`.
  If a later cell, audit or correction overturned, withdrew or qualified the
  result, say so in `later`, naming the later cell or audit.
- If the ledger says the result was wrong, retracted, withdrawn or provisional,
  the plain text must say so too. Do not soften a failure or inflate a success.
- Keep the direction of every result exactly as the ledger states it.
- If a cell never ran, say so plainly and, if the ledger says why, say why.

## Fields (one JSON object per cell)

| field | what it holds | length |
|---|---|---|
| `title` | The question the cell asked, in plain words. Sentence case. End with "?" when it is a question. A check, audit or measurement can use a short noun phrase instead. Must make sense alone in a list. | at most 70 characters |
| `description` | For the overview table. What we did and what we found, in one or two sentences. Do not repeat the title. | 120 to 280 characters |
| `outcome` | One of the overall outcomes below. | |
| `size` | Scale in plain words: "80 runs", "140 runs over 7 scenarios", "No new runs, re-scored saved answers", "Never run". | at most 60 characters |
| `why` | Why we asked, at that point in the project, and what the idea was. | 200 to 900 characters |
| `expectations` | One object per expectation the ledger wrote down for this cell: `id` (exactly as in the ledger, for example "P25.1"), `text` (what we expected, one plain sentence, at most 240 characters), `outcome` (one of the expectation outcomes below), `note` (what actually happened for this expectation, one sentence, at most 260 characters). Use an empty list only if the cell wrote down no expectations. | |
| `found` | What happened, with the key numbers in plain form. One to three short paragraphs. | 250 to 1,500 characters |
| `means` | What it means and what changed because of it (a claim dropped, the next experiment chosen, a design rule adopted). | 120 to 800 characters |
| `later` | If later work overturned, withdrew or qualified this result, one or two sentences naming what and where. Otherwise `null`. | at most 500 characters |
| `entries` | One object per ledger entry listed for the cell, keyed by the entry's line number as a string: `label`, `title` (at most 80 characters), `summary` (one to three sentences, 60 to 450 characters). | |

Studies (non-cell entries) use the same fields plus `related`, a list of cell ids
the study is about (for example ["30", "37"]). A study may have an empty
`expectations` list and may use the outcome `measured`.

### Overall outcomes (`outcome`)

| value | shown as | use when |
|---|---|---|
| `held` | Held up | the main expectations held up |
| `mixed` | Mixed | some expectations held up and others did not, or could not be settled |
| `failed` | Didn't hold up | the main expectations did not hold up, or the opposite happened |
| `unclear` | Too close to call | it ran, but the data could not settle the question |
| `stopped` | Stopped early | halted at a checkpoint, could not run on our hardware, or blocked |
| `not-run` | Never run | planned but never carried out |
| `measured` | Measurement only | there was no pass/fail expectation, only a measurement, analysis or audit |

### Expectation outcomes (`expectations[].outcome`)

`held`, `partly`, `failed`, `reversed` (the opposite happened), `unclear` (too
close to call), `not-graded` (the ledger reported it without a pass/fail call),
`not-tested` (the cell stopped or never ran before this was tested).

### Entry labels (`entries[].label`)

`Plan`, `Change to the plan`, `Pilot`, `Result`, `Correction`, `Mistake caught`,
`Stopped`, `Note`.

## Worked example (Cell 25)

This is the target voice and level of detail.

```json
{
  "title": "Does the same pattern show up in a Mixture-of-Agents setup?",
  "description": "We repeated our main measurement on the popular Mixture-of-Agents recipe. Its editor also added caveats nobody had raised, but it kept far fewer of the caveats it was handed than our council's editor did.",
  "outcome": "mixed",
  "size": "80 runs, none failed",
  "why": "Our main finding so far came from one design, the council. The editor passed along only part of the caution the specialists raised, and it also added some caution of its own. Before building a paper on that, we wanted to know whether the same pattern appears in Mixture-of-Agents (MoA), a widely used recipe where several general-purpose models answer and one model merges their answers. We kept the same scenarios and the same editor model, gpt-oss-20B, so this was a second look inside our own lab rather than an independent check.",
  "expectations": [
    {"id": "P25.1", "text": "The editor would pass along a middling share of the caveats it was given: more caveats in, more caveats out, but well short of all of them.", "outcome": "partly", "note": "More caveats in did mean more out, but the share passed along was so small that we could not rule out the editor mostly ignoring its input."},
    {"id": "P25.2", "text": "Given drafts with no caveats at all, the editor would still add some of its own in at least 10% of runs.", "outcome": "held", "note": "It added caveats nobody had raised in 28% of those runs (plausibly anywhere from 12% to 51%)."},
    {"id": "P25.3", "text": "For the kind of caveat our scoring handled best, saying a number is an estimate, the editor would flag estimates more often when the drafts did.", "outcome": "failed", "note": "It flagged estimates at the same rate whether or not any draft had done so."}
  ],
  "found": "All 80 runs completed. When the drafts carried more caveats, the final answers carried more too, so the basic pattern was there. The ledger describes it with the formula y = w·s + c. Here s is how many kinds of caveat the drafts contained and y is how many reached the final answer. The share passed along is w, and c is what the editor adds on its own. This editor's w was 0.158, roughly 16%, against 0.352 for the council's editor. Even with four kinds of caveat in the drafts, the final answer kept fewer than one on average.\n\nThe editor also added caution on its own. When the drafts contained no caveats at all, it added some in 28% of runs. For estimates in particular it showed no sign of reading its input.",
  "means": "The pattern is not unique to our council. A second design also produced an editor that adds caution nobody raised and passes along only part of what it is given. How much gets passed along is not fixed, though. The standard MoA prompt says nothing about keeping caveats. Under it, the editor passed along about as little as a plain merge of answers did in Cell 8. That suggests the editor's instructions matter at least as much as the design.",
  "later": "Later checks narrowed what this comparison can show. It used a keyword counter that the project later stopped trusting as a measuring tool, and it changed several things at once, so it cannot pin the difference on the instruction alone. The figures are treated as provisional.",
  "entries": {
    "3576": {"label": "Plan", "title": "Repeat our measurement on a Mixture-of-Agents setup", "summary": "Three general-purpose models (Phi-4 14B, Qwen2.5 7B and Mistral 7B) would answer each scenario and gpt-oss-20B would merge their answers using the standard MoA prompt. To vary how much caution the editor received, we would delete caveat sentences from the drafts, down to none."},
    "3644": {"label": "Change to the plan", "title": "Adding caveats, because the drafts had almost none", "summary": "The general models raised almost no caveats on their own, 5 across 27 answers, so deleting sentences could not create enough variety. Before running the editor we changed the plan to also add caveat sentences copied from our specialists' earlier answers to the same scenario."},
    "3681": {"label": "Result", "title": "The pattern appears, but this editor keeps far less", "summary": "All 80 runs completed. The editor added caveats nobody raised and passed along only about 16% of those it received, well below our council's editor. A mistake in our scoring script was caught and fixed before the result was written up."}
  }
}
```

## Output

Write one JSON file, UTF-8, exactly in this shape:

```json
{
  "batch": "<batch letter>",
  "cells": {"<cell id>": { ...fields... }},
  "studies": {"<study id>": { ...fields..., "related": ["..."] }}
}
```

Study `entries` are keyed by entry id (for example "entry-4491"), not by line
number.

Before finishing, run the checker and fix everything it reports:

```
python3 docs/ledger_explorer/plain/lint.py docs/ledger_explorer/plain/batch_<letter>.json
```

Do not edit any other file. Do not run the build, git, or anything under
`site_v2/`.
