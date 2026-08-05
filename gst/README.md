# GST — a measurement kit for what aggregation does to epistemic content

When a model writes a final answer over other components' prose — a council
lead, a Mixture-of-Agents aggregator, a RAG synthesizer — it does not
transport their epistemic content. It emits a *shrinkage estimate* of how much
qualification an answer like this ought to carry, weighting its own prior
against the evidence in front of it.

That behavior is measurable in three parameters. This kit measures them, tells
you which of five interventions your system needs, and refuses to give you a
number when your run set could not have identified one.

```
y = w·s + c        s  qualification level supplied by upstream components
                   y  qualification level in the writer's output
                   w  evidence weight      c  prior fill
```

`w = 1, c = 0` is faithful transduction. Everything below that is compensating
invention at low supply, trimming at high supply, and compression of whatever
distinction the upstream components drew.

The core has **no dependencies**. That is a design constraint: running the
measurements should never be blocked by an environment problem.

## Install

```bash
pip install -e .
```

Optional second instrument (needed before reporting any verdict — see
"Two instruments" below):

```bash
pip install -e '.[nli]'
```

## Quickstart

```python
from gst import measure_all
from gst.adapters import FieldMap, from_jsonl

# Map your log's shape onto the kit's contract. Dotted paths or callables.
fmap = FieldMap(upstream="specialist_outputs", output="final_answer",
                prompt_id="task_id", condition="arm")

records = from_jsonl("runs.jsonl", fmap)
card = measure_all(records, system="my-pipeline")

print(card.render())
for line in card.recommendations(can_train=True):
    print("-", line)
```

Or from the command line:

```bash
gst measure runs.jsonl --system my-pipeline --upstream specialists --output final
```

## What it measures

| Parameter | Question it answers | Estimator |
|---|---|---|
| `w`, `c` | Does the writer transport upstream qualification, or overwrite it with a prior? | `shrinkage()` |
| `f` | What fraction of the output actually carries the property? | `span_fraction()` |
| `ε` | How often does each instrument miss the behavior it is supposed to detect? | `blindspot()` |
| `p₀` | How often is a single sample invention-free, and what does selection buy? | `clean_rate()` |

Each estimator carries its own identifiability guard and reports the guard's
verdict beside the number. A parameter your design could not have identified
comes back marked `UNIDENTIFIABLE`, never as a point estimate.

## What it recommends

The decision rule is keyed to measured values and to what access you have:

- **Black-box writer** → C5 verifier-blind best-of-n (`gst.select`). No
  training, no weight access, deployable today.
- **Training access** → C1 counterfactual corpus (`gst.corpus`) + C2
  minimal-pair span-masked preference training (`gst.pairs`).
- **Residual-stream access** → C4 conditional activation steering.
- **RL infrastructure** → C3 ensemble-reward RL, last and gated on C1/C2.

## Two instruments, and the rule that costs the most to follow

No verdict from this kit is valid on one instrument. And the instrument that
generates corrective feedback may never grade compliance with that feedback.

That rule exists because of a measured result. A revision loop that quoted a
regex detector's matched phrases back to the model removed **0.88** families
by that detector's own count and **0.00** by an independent instrument. The
model had not stopped doing the thing; it had learned to paraphrase, which is
a cheaper distributional move than removal.

This is why `gst.select.select` takes a **zero-argument** sampler and raises
`TypeError` if you hand it anything that could receive feedback. Selection
conditions the *output*; feedback conditions the *policy input*. Only the
second one can be gamed, because only the second one is observable to the
model.

```python
from gst import select

res = select(lambda: my_writer(prompt), upstream, n=3)   # fine
res = select(lambda draft: my_writer(draft, hint), ...)  # TypeError
```

Residual failures are **annotated**, never revised. Annotation discloses to
the reader; revision is a feedback channel wearing a different name.

## Reference results

Running the kit on the originating system's 1,260-run ledger:

```
A1  SHRINKAGE   y = w*s + c
    w = 0.352 [0.310, 0.391]      evidence weight
    c = 0.540 [0.437, 0.651]      prior fill
    prior-trust ratio (1-w)/w = 1.84
    supply -> emitted: 0:0.40  1:0.81  2:1.32  3:1.62  4:1.83

A2  FEATURE SPAN
    f = 0.068 chars   verdict: HIGH DILUTION (~15:1)

p0  CLEAN-SAMPLE RATE AND SELECTION
    p0 overall = 0.885   worst stratum s=0: 0.597 [0.477, 0.706]
    best-of-n (independence): n=1:0.597  n=2:0.838  n=3:0.935
    best-of-n (empirical):    n=1:0.562  n=2:0.727  n=3:0.827
    ! redraws are positively correlated; use the empirical curve for sizing
```

That last line is the kit doing its job. The independence formula
`1-(1-p₀)ⁿ` says best-of-3 reaches 0.94; the measured curve over real
repeated runs says 0.83, because a writer that invents on a given task tends
to invent again on redraws. Sizing from the formula would have under-provisioned
selection by a full sample.

Reproduce it with `gst selftest bench/runs/imported`, or `pytest tests/`.

## Running a replication

1. Write an adapter (usually under ten lines — see `gst.adapters.frameworks`
   for MoA, LangGraph, AutoGen, and RAG shapes).
2. `gst preregister --system my-system --out PREREGISTRATION.md`, fill it in,
   and **commit it before running anything**.
3. Estimate the parameters. Publish the full card, including guards that fired.
4. Run the interventions your access level permits.
5. Publish the outcome in either direction. A null is a result; the framework
   names in advance what each null would mean.

Swapping the property class is a one-liner — the kit ships
`SOURCE_ATTRIBUTION` beside `EPISTEMIC_QUALIFICATION` specifically so that
"this is really just about hedging" is a testable objection rather than a
rhetorical one:

```python
from gst.instruments import RegexInstrument, SOURCE_ATTRIBUTION
card = measure_all(records, system="rag", instrument=RegexInstrument(SOURCE_ATTRIBUTION))
```

## What would falsify the framework

- **A1** — a system with `w ≈ 1, c ≈ 0` under an ordinary writer, or a
  supply response no monotone estimator reading survives.
- **A2** — whole-sequence preference training moving a small-`f` behavior at
  modest dose.
- **A3** — a feedback loop whose improvement survives an independent
  instrument, or selection producing improvement a second instrument denies.

The framework is a scientific object, not a lens. If your card refutes it,
that is the most useful thing you can publish with this kit.

## Provenance and honest limits

The kit comes out of a 21-experiment program on a four-model local council
(1,673 audited runs, 18 cases, four writers ≤20B). Its reference numbers are
one instantiation, not constants — a regex lexicon tuned to legal, medical,
and financial prose, authored cases rather than sampled traffic, and a
linearity check that only covers supply 0–4. The *forms* are what generalize;
your card's job is to test whether they do.

Six defects in that program's own measurements were found only by
instruments like these — a silently substituted writer prompt that
contaminated 39 runs, an intervention benchmarked on a condition where the
target behavior was already absent, a detector that taught paraphrase. Each
is now a guard in this package rather than a lesson in a paper.

MIT licensed.
