# Pathway-3 swap matrix — runbook

Pathway-3 of the improvement roadmap: hybrid cabinets where one phase of the
council is served by Opus and the other four phases run locally. The goal is
to isolate **where the gap between the local council and the Opus modes
actually lives** — planner? one specific specialist? the synthesis step?

## Architecture (already committed)

- `council/orchestrator.py` — `CabinetBackends` dataclass routes each of the
  five deliberation phases (planner, three seats, synthesis) to its own
  ChatFn. Backward-compatible: `chat_fn=` still works.
- `bench/opus_swap.py` — five standard swap variants, one per phase. Each
  uses exactly one Opus call per deliberation.
- `bench/runner.py` — `compare` CLI now accepts the five swap modes plus
  the special aliases `all-swaps` and `everything`.
- `server/static/js/results.js` — Results page shows swap columns when
  imports exist; each column displays an "Opus · &lt;Phase&gt;" badge and
  per-turn backend tags in the inspector.

Total architectural code change: ~200 LOC.

## MoE local alternative — gpt-oss-20B (no Opus spend)

The bench harness ships a second pair of comparison modes that mirror
opus-single / opus-council but use gpt-oss-20B (OpenAI's first open-
weights release, MoE design, Apache 2.0) instead of Opus 4.7. Lets you
ask "what does the council architecture buy us on top of a strong open
local model?" without any API spend.

```bash
# One-time: pull gpt-oss-20B via Ollama (~14 GB download)
ollama pull gpt-oss:20b

# Run the MoE baselines on case 4 + case 2
python -m bench compare --case case_4_glp1_employer_coverage --modes all-moe
python -m bench compare --case case_2_cross_border_digital_therapeutic --modes all-moe
```

Why gpt-oss-20B as the top MoE pick over alternatives:

- **Fits comfortably alongside Phi-4 in sequential mode** — 14 GB
  baseline + 9 GB Phi-4 = 23 GB peak, well under the 26 GB Metal cap.
  Qwen3-30B-A3B (~18 GB) and Mixtral 8x7B (~26 GB Q4) are tighter.
- **MoE with ~3.6B active parameters** — per-token latency stays low
  even though total capacity is 20B.
- **Reasoning-tuned by a frontier lab** — matches the council's
  planning + synthesis use case better than instruction-only MoEs.
- **Apache 2.0** — clean license for research distribution.
- **Released for exactly this use** — OpenAI describes the 20B variant
  as designed for "lower latency, local, or specialized use-cases."

Two modes available:

- `gptoss-single` — one gpt-oss-20B call with a neutral system prompt
  (the same prompt opus-single uses, so the comparison isn't muddled
  by a prompt difference between baselines)
- `gptoss-council` — gpt-oss-20B plays every seat in the council
  orchestration. Same prompts, same loop as opus-council; only the
  model differs.

Both modes record `cabinet_backends` with `"ollama:gpt-oss:20b"` for
every phase so the audit log is honest about what ran. The Results UI
surfaces a "gpt-oss-20B · uniform cabinet" badge in the column header.

## Local-only plumbing validation (no Opus spend)

Before lifting the budget cap, you can validate the entire swap-matrix
pipeline using local-only inference. The `swap-<phase>-phi4` modes
substitute the Lead's Phi-4 14B for one specialist seat. Phi-4 is
already loaded (it plays planner + synthesis), so this adds one
extra inference per run, no model downloads.

```bash
# Validate the architecture with zero Opus spend
python -m bench compare --case case_4_glp1_employer_coverage --modes local-swaps
python -m bench compare --case case_2_cross_border_digital_therapeutic --modes local-swaps
```

Two local-swap variants are defined:

- `swap-legal-phi4` — Phi-4 plays Legal (Saul sidelined)
- `swap-finance-phi4` — Phi-4 plays Finance (Qwen-Finance sidelined)

(No `swap-planner-phi4` or `swap-synthesis-phi4`: Phi-4 already serves
those phases in the baseline, so a swap would be a no-op.
`swap-healthcare-phi4` was removed after the plumbing-validation run
on case 4 confirmed the CabinetBackends routing works end-to-end.)

The audit log records `cabinet_backends.<phase> = "ollama:phi4:14b"`
for the swapped phase — explicitly labeled as Phi-4, NOT as an Opus
stand-in. The Results page surfaces this as a "Phi-4 · `<Phase>`"
cabinet badge so no later reader can mistake a 14B local model for
frontier capability.

The natural ablation question this answers, beyond plumbing
validation: **does a 14B generalist (Phi-4) outperform an 8B
specialist (Med42 / Saul / Qwen-Finance) when playing that seat?**
If yes, the specialist-fine-tune premise of the project is weaker
than assumed. If no, specialization beats raw capability at this
scale.

## Execution (when budget cap lifts)

The bench is currently held at `BENCH_BUDGET_USD=0`. To run the matrix:

```bash
# 1. Raise the cap. $5 is comfortable; expected spend is ~$1.30 for the
#    full 10-run matrix.
export BENCH_BUDGET_USD=5

# 2. Run all 5 swap variants on case 4 (GLP-1 employer coverage)
python -m bench compare --case case_4_glp1_employer_coverage --modes all-swaps

# 3. Run all 5 swap variants on case 2 (cross-border DTx launch)
python -m bench compare --case case_2_cross_border_digital_therapeutic --modes all-swaps
```

Each invocation creates `bench/runs/<timestamp>/` containing per-mode
JSON files plus a `cost.json` ledger and a `summary.json`.

## Importing into the Results UI

The Results tab reads from `bench/runs/imported/`. After the bench runs
complete, import each via the v2 audit-log path:

```bash
# Replace <timestamp> with the actual run dir name from step 2/3 above.
for variant in planner healthcare legal finance synthesis; do
  python -m bench.import_run \
    --from-audit-log "bench/runs/<timestamp>/case_4_glp1_employer_coverage__swap-${variant}-opus.json" \
    --mode "swap-${variant}-opus"
done
```

Then reload http://127.0.0.1:8000/results — the swap columns appear
automatically next to the three baselines, in phase order
(Planner → Healthcare → Legal → Finance → Synthesis).

## What to look for

Each swap variant should produce a synthesis-shaped output ("## Tensions"
then "## Synthesis"). Compare against the existing local-council baseline
for the same case:

- **If `swap-legal-opus` produces DiGA / pVE / §139e references on case 2**
  but the all-local council didn't — that's strong evidence the Legal
  seat is the single bottleneck for jurisdictional precision.
- **If `swap-healthcare-opus` produces STEP 4 / weight regain / SURMOUNT-4
  on case 4** but the all-local Healthcare seat invented SEMIMAN — that
  isolates confabulation to Med42's training corpus.
- **If `swap-planner-opus` significantly changes the rubric outcome**, the
  problem isn't the seats — it's that Phi-4 was asking the wrong
  sub-questions.
- **If `swap-synthesis-opus` substantially improves the synthesis but the
  per-seat content is still weak**, the local Lead is failing at
  integration rather than reasoning.

Rubric highlighting on the Results page (click any rubric row) automatically
flows over the new swap columns — that's how to read the variants side by
side.

## Budget math

Per-variant cost estimate (Opus 4.7 at $5/MTok input, $25/MTok output,
$0.50/MTok cached input — prompt caching is enabled on system prompts):

| Variant | Approx in (tok) | Approx out (tok) | Approx $ |
|---|---:|---:|---:|
| `swap-planner-opus`     | 4,000 | 1,000 | $0.045 |
| `swap-healthcare-opus`  | 3,500 | 4,000 | $0.118 |
| `swap-legal-opus`       | 3,500 | 4,000 | $0.118 |
| `swap-finance-opus`     | 3,500 | 4,000 | $0.118 |
| `swap-synthesis-opus`   | 9,000 | 5,000 | $0.170 |
| **Total per case**      |       |       | **$0.57** |
| **Total for case 4 + case 2** |       |       | **~$1.14** |

The `$5` cap leaves ~$3.85 of headroom for re-runs and any single-trial
variance probes (a preview of pathway-2 statistical work).
