# Repository cleanup audit — 2026-09-24

> **Outcome (implemented 2026-09-24 on branch `repo-cleanup`).** This is the audit as
> written before the move, so its links point to the old locations. What changed from
> the plan below:
>
> - **All papers except `paper_combined` were archived**, including `paper_moa_audit`
>   and `paper_harness_design`, because the combined paper is now the current one.
> - **`train/run_phase3.sh`, `run_phase3_v2.sh` and `resume_v2.sh` stayed in `train/`.**
>   The Cell 1, 3 and 5 scripts name `run_phase3.sh` as their base training recipe.
> - `modelfiles/qwen-finance.Modelfile` moved to `train/qwen-finance.Modelfile`.
> - The CDS/ALR/seat-density definitions went into the runbook's glossary. That edit
>   kept the runbook's line count unchanged, because the site's plain-language
>   summaries are keyed by runbook line number.
> - The ledger technical edition and the prototype's `runs/` logs sit in `archive/`
>   but are listed in `.gitignore`.

This audit asks which files in the repo are stale or no longer used to run the experiment, so they can later move into an `archive/` folder. It checks the repo against the published **Paper-Hardening Cell Ledger** (built 2026-09-24 from 9,401 runbook lines, Cells 1–61).

**What the live experiment actually uses today:**

- **The notebook:** [`RUNBOOK_PAPER_HARDENING.md`](../RUNBOOK_PAPER_HARDENING.md), parsed by the ledger build.
- **The claims record:** [`docs/STATUS.md`](STATUS.md), which also feeds the ledger's claims page.
- **The harness write-up:** [`docs/HARNESS_SEAT_ARCHITECTURE.md`](HARNESS_SEAT_ARCHITECTURE.md), the source text for the ledger's harness page.
- **The site builder and its output:** [`docs/ledger_explorer/`](ledger_explorer/) builds [`site_v3/`](../site_v3/), which is the public site.
- **The papers:** [`paper_moa_audit`](paper_moa_audit.tex), [`paper_harness_design`](paper_harness_design.tex) and the new [`paper_combined`](paper_combined.tex), plus [`PLAIN_LANGUAGE_COMPANION.md`](PLAIN_LANGUAGE_COMPANION.md).
- **Code:** `train/run_cell*.py`, which imports `council/`, `gst/`, `examples/`, and one cell script from another.
- **Data:** `bench/runs/*.jsonl`, `bench/runs/imported/`, `bench/analysis/`, `train/data/` and the `docs/CELL*_*.json` item files. The ledger cites 143 repo paths and 64 data sources, all inside `train/`, `bench/` and `docs/`.

How the verdicts were reached: every candidate was checked for (1) last commit date, (2) whether the ledger cites it as a cell's evidence or data source, (3) whether any live script imports it, and (4) whether `STATUS.md`, the runbook, the site or a config file points to it.

---

## A. Archive: nothing live reads these

| File / directory | Description | Why it no longer matters |
|---|---|---|
| [`IMPLEMENTATION_PLAN.md`](../IMPLEMENTATION_PLAN.md) | May plan for the first prototype: Phi-4 lead cabinet, an A/B comparison against Claude Opus 4.7, a web app, and 5 use cases. | Last touched 2026-05-14, and its status box still says "awaiting Sam's approval." The program became the $0, local-only paper-hardening campaign, and none of these phases are tracked anymore. The README still calls it "the full plan," which misleads new readers. |
| [`Council_of_Experts_v5_FineTunedCabinet.docx`](../Council_of_Experts_v5_FineTunedCabinet.docx) | The original v5 spec for the fine-tuned cabinet. | Describes the cabinet design the cells went on to test and replace. Only the README and `IMPLEMENTATION_PLAN.md` refer to it. |
| [`RUNBOOK_SWAP_MATRIX.md`](../RUNBOOK_SWAP_MATRIX.md) | June "Pathway-3" plan: hybrid cabinets with one phase served by Opus. | Needs paid Opus calls, and the hardening campaign is $0 and local-only. No cell cites it. |
| [`exp/`](../exp/) | One file, `ClaudeSingleShot.md`: a pasted Claude answer to the GLP-1 case from May. | Scratch output that nothing cites. The Opus single-shot baselines that count are in `bench/runs/imported/*__opus-single.json`. |
| [`site/`](../site/) | The old public site (Results, Process, Architecture, Routes, Cells pages). It was live until 2026-09-24. | Replaced by `site_v3/`. `STATUS.md` §7 already calls it stale ("Do not deploy"), and `netlify.toml` now publishes `site_v3`. |
| [`site_v2/`](../site_v2/) | Draft scrollytelling site and experiment catalog, with Playwright tests. | Never deployed, per `netlify.toml`. Superseded by `site_v3/`. Its `node_modules/` also takes up 75 MB locally. |
| [`.github/workflows/site.yml`](../.github/workflows/site.yml) | GitHub CI that runs lint, unit tests and Playwright tests for `site_v2`. | Runs only on `site_v2/**` changes, so it becomes dead once `site_v2` moves. |
| [`scripts/`](../scripts/) (`build_site.py`) | Turns the `server/` API output into the static `site/`. | Builds only `site/`. `site_v3` is built by `docs/ledger_explorer/build.py`. |
| [`tests/`](../tests/) (`test_bench.py`) | May unit tests for the Opus bench runner and cost guard. | Last touched 2026-05-14. It covers only the Opus comparison path, and none of the 61 cells' code is tested here. |
| [`docs/PAPER_DRAFT.md`](PAPER_DRAFT.md) | Markdown v0.1 of the first paper. | Its first line says **SUPERSEDED**. |
| [`docs/paper.tex`](paper.tex) / [`.pdf`](paper.pdf) | *Rendered, Not Transported*, v0.7. | `STATUS.md` §7: "superseded … retain for history, do not submit." |
| [`docs/paper_calibration.tex`](paper_calibration.tex) / [`.pdf`](paper_calibration.pdf) | *Knowing When to Hedge*. | `STATUS.md` §7: **RETRACTED**. |
| [`docs/paper_witnesses.tex`](paper_witnesses.tex) / [`.pdf`](paper_witnesses.pdf) | *Witnesses, Not Amplifiers*. | `STATUS.md` §7: superseded. |
| [`docs/paper_framework.tex`](paper_framework.tex) / [`.pdf`](paper_framework.pdf) | *A Shrinkage Law for Epistemic Transport*, v0.1. | Built on keyword-counter (regex) measurements, which were no longer accepted after 2026-08-09, and its instruction-gain contribution was withdrawn. The papers now consolidate into the audit and harness papers. **Confirm first:** `STATUS.md` §7 still lists it as "active." |
| [`docs/paper_behavior.tex`](paper_behavior.tex) / [`.pdf`](paper_behavior.pdf) | *What Aggregation Does to Epistemic Content*, v0.1. | Same reason as the framework paper, and last touched 2026-08-09. `PLAIN_LANGUAGE_COMPANION.md` describes "the two papers," meaning audit and harness. **Confirm first**, because `STATUS.md` §7 still lists it as active. |
| [`docs/figs/`](figs/) + [`docs/make_figs.py`](make_figs.py) | The seven paper figures and the script that draws them. | Only the five retired papers use these figures. The three current papers use no figures at all. |
| [`docs/INTERVENTION_DESIGN.md`](INTERVENTION_DESIGN.md) | GST framework v1.2: the shrinkage law and five interventions. | Its parameters come from the regex counter that was dropped on 2026-08-09, and its paper (framework) is superseded. The runtime design now lives in `HARNESS_SEAT_ARCHITECTURE.md`. The `gst/` **code** stays, because Cells 56–61 import it. |
| [`docs/RUN_LEDGER.md`](RUN_LEDGER.md) + [`train/build_ledger.py`](../train/build_ledger.py) | A 524 KB table of every imported run with regex scores, plus the script that generates it. | Last regenerated 2026-08-05. Its scores come from the regex counter and are provisional. The ledger's Data tab now does the "browse every run" job. Archive it rather than delete it, because the 2026-08-01 verification audit in the runbook cites `build_ledger.py`. |
| [`train/run_phase3.sh`](../train/run_phase3.sh), [`run_phase3_v2.sh`](../train/run_phase3_v2.sh), [`resume_v2.sh`](../train/resume_v2.sh) | July "Phase 3" DPO training runs for Saul (`saul-dpo`, `saul-dpo-v2`). | Written before the cell ledger began (Cell 1 is 2026-07-11), and no cell cites them. They are the recipe for the `saul-dpo` versions in the imported data, so archive them rather than delete. |
| [`docs/ledger_explorer/archive/`](ledger_explorer/archive/) | A frozen copy of the 2026-09-15 technical edition of the ledger. It is 38 MB and untracked. | Already an archive, so move it into the new top-level `archive/` to keep one archive. Decide whether to commit it (38 MB) or add it to `.gitignore`. |
| `docs/VerbAI/` | An empty, untracked folder. | Belongs to a different project and holds nothing. **Delete it** rather than archive it. |

## B. Archive, but fix a reference first

| File / directory | Description | Why it no longer matters, and what to fix first |
|---|---|---|
| [`RUNBOOK_DPO_PROMPT_TRANSFER.md`](../RUNBOOK_DPO_PROMPT_TRANSFER.md) | July plan for the DPO and prompt-transfer experiment, written before the cells. | Superseded by the paper-hardening runbook. **But** [`RUNBOOK_PAPER_HARDENING.md:151`](../RUNBOOK_PAPER_HARDENING.md) sends readers here for the CDS, ALR and seat-density definitions. Copy those definitions into the runbook's glossary, or repoint the link to the archive path, then rebuild the ledger. |
| [`server/`](../server/) | FastAPI web UI for live A/B runs (local council vs Opus), plus the old Results page. | The only thing that runs it is `scripts/build_site.py`, which is also being archived. [`train/gen_pairs.py:18`](../train/gen_pairs.py) mentions its JS only in a comment. **Fix first:** in `pyproject.toml`, remove `server` from `packages`, the `coe-server` script and the `server` extra. |
| [`.claude/launch.json`](../.claude/launch.json), `site-preview` entry | A preview server that points at `site_v2`. | Delete that one entry when `site_v2` moves. Keep `ledger-explorer` and `site-v3`. |

## C. Looks old but should stay (to prevent a wrong move)

| File / directory | Why it stays |
|---|---|
| [`bench/`](../bench/) Python modules (`opus_*`, `runner`, `import_run`, `local_swap`, `upgraded_council`, `gptoss_*`, `dpo_experiment`, `cost_guard`, `anthropic_client`) | The campaign no longer uses them, but they import each other and older scripts depend on them. `train/run_cell2.sh` uses `bench.import_run`, which needs `bench.runner`, and `bench.opus_single` is imported by `build_ledger.py` and `gptoss_single.py`. Moving them breaks imports. Leave them until someone refactors. **`bench/runs/` and `bench/analysis/` are the evidence behind the ledger. Never move them.** |
| [`council/`](../council/) | Imported by cell scripts through Cell 36, including the orchestrator, cabinet, prompts and thermal guard. |
| [`harness/`](../harness/) | The measurement layer from before the redesign. Cells 19–20 import it, so it is needed to reproduce them. |
| [`gst/`](../gst/) | Cells 56, 57, 60 and 61 import `gst.gates`, `gst.registry` and `gst.stats`. |
| [`examples/`](../examples/) | `test_cases.py` is imported by Cells 55–61 and by the ledger's `build_data.py`. |
| [`modelfiles/qwen-finance.Modelfile`](../modelfiles/qwen-finance.Modelfile) | Dated May, but **live**. `MODEL_INVENTORY.md` uses it to rebuild the finance seat used in Cells 13–61. Consider moving it into `train/` next to the other Modelfiles, and update [`council/cabinet.py:88`](../council/cabinet.py) and `MODEL_INVENTORY.md` if you do. |
| `train/*.Modelfile`, including `openbiollm-*` | Recipes for rebuilding the Ollama models. OpenBioLLM was re-tested at the Cell 55 seating gate. |
| [`docs/HARNESS_DESIGN.md`](HARNESS_DESIGN.md) | Dated August, but the public site quotes it and `HARNESS_SEAT_ARCHITECTURE.md` names it as its companion. |
| `docs/*AUDIT*.md`, [`ARCH_SWEEP_2026-08-05.md`](ARCH_SWEEP_2026-08-05.md), [`REVIEW_MoA_2406.04692.md`](REVIEW_MoA_2406.04692.md) | Historical records, but the standing rules in `STATUS.md` cite them. Directive 9, for example, cites the attainability audit. You could move them into `docs/audits/` for tidiness, but not into the archive. |
| `docs/CELL*_*.json`, `PHRASE_SWAP_FORMS.json`, `DICTATION_REGISTRY.json` | Frozen test items and labels. The ledger's Data tab and Cell 57 read them. |

## D. Local-only clutter (ignored by git, so it doesn't affect the GitHub view)

| Path | What it is | Suggestion |
|---|---|---|
| `runs/` | 30 deliberation logs from the May–June CLI runs (1.9 MB). | Archive locally or delete. They are not in git. |
| `bench/runs/<timestamp>/` | 427 raw per-run folders from 2026-05-07 to 2026-07-26 (31 MB). | These are the raw logs behind the checked-in `imported/` and `*.jsonl` files. Keep them locally as backup, or move them to cold storage. |
| `site_v2/node_modules/`, `site_v2/test-results/` | npm and Playwright output. | Delete when `site_v2` is archived. |
| `.pytest_cache/`, `.ruff_cache/`, `.DS_Store` | Tool caches. | Safe to delete at any time. |
| `train/models/` (45 GB), `train/adapters/` (12 GB), `train/gguf/` (4.4 GB) | Model weights. | Not a readability problem, but `MODEL_INVENTORY.md` records the disk at 100% full. Handle this separately. |

## E. Stale content to update in place (not archive)

1. **[`docs/STATUS.md`](STATUS.md) §7, "Artifact status," is out of date.** It lists `paper_moa_audit` as v0.1 when it is now v0.3. It calls framework and behavior "active." It does not list `paper_harness_design` or `paper_combined`. It describes `site/` as the site awaiting reconciliation. The header also still reads "Updated 2026-08-09," although the rows go through Cell 61. Because this file feeds the ledger's claims page, fix it before rebuilding the site.
2. **[`pyproject.toml`](../pyproject.toml)**: the description still reads "three domain fine-tunes plus Phi-4 lead, with optional A/B benchmark against Claude Opus 4.7."
3. **Uncommitted current work.** `docs/MODEL_INVENTORY.md`, `docs/PLAIN_LANGUAGE_COMPANION.md` and `docs/paper_combined.*` are untracked, and the edits to the harness and audit `.tex`/`.pdf` files are uncommitted. Commit these before any archive move, so the move commit contains only moves.

## F. Suggested archive layout

```
archive/
  README.md                  # one paragraph per folder: what it was, when retired, what replaced it
  poc_2026-05/               # IMPLEMENTATION_PLAN.md, the v5 .docx, RUNBOOK_SWAP_MATRIX.md, exp/, server/, scripts/, tests/
  dpo_2026-07/               # RUNBOOK_DPO_PROMPT_TRANSFER.md, train/run_phase3*.sh, train/resume_v2.sh
  sites/                     # site/, site_v2/ (+ its CI workflow), ledger_explorer technical edition
  papers_2026-08/            # paper.tex, calibration, witnesses, framework, behavior, PAPER_DRAFT.md, figs/, make_figs.py
  design_2026-08/            # INTERVENTION_DESIGN.md, RUN_LEDGER.md, build_ledger.py
```

Use `git mv` so each file's history follows it.

---

## G. Proposed README

The current README describes the May prototype: a Phi-4 lead, an Opus 4.7 A/B test and a web UI. It points to `IMPLEMENTATION_PLAN.md` and the v5 `.docx`, and says nothing about the cells, the ledger, the papers or the site. Suggested replacement:

````markdown
# Council of Experts

A research program asking whether a *council* of specialist LLMs, whose answers
an editor model combines into one report (a Mixture-of-Agents design), gives
better answers than one model answering directly. Everything runs locally on
Apple Silicon with Ollama, and no paid API is used.

It started in May 2026 as a prototype. From July it became a series of
61 experiments ("cells"), each with its expectations written down before it ran.
The result is two papers and a redesigned system (the harness) built only from
the parts that held up.

**Public site:** https://councilofexperts.netlify.app shows every cell in plain
language, the claims, a glossary, the harness, and the saved run data.

## Where to start

| If you want… | Read |
|---|---|
| The findings, in plain language | [docs/PLAIN_LANGUAGE_COMPANION.md](docs/PLAIN_LANGUAGE_COMPANION.md) or the public site |
| What the program claims today, and how sure it is | [docs/STATUS.md](docs/STATUS.md), the authoritative claims record |
| Every experiment, in order, with its full reasoning | [RUNBOOK_PAPER_HARDENING.md](RUNBOOK_PAPER_HARDENING.md), the lab notebook the site is built from |
| The papers | [docs/paper_moa_audit.pdf](docs/paper_moa_audit.pdf) · [docs/paper_harness_design.pdf](docs/paper_harness_design.pdf) · [docs/paper_combined.pdf](docs/paper_combined.pdf) |
| The redesigned system | [docs/HARNESS_SEAT_ARCHITECTURE.md](docs/HARNESS_SEAT_ARCHITECTURE.md) |
| Which local models are used, and how to rebuild them | [docs/MODEL_INVENTORY.md](docs/MODEL_INVENTORY.md) |

## Repository map

| Path | What's in it |
|---|---|
| `train/` | One script per cell (`run_cellNN_*.py`), training data, Modelfiles and adapter configs |
| `bench/runs/`, `bench/analysis/` | Saved run records and per-cell analysis: the evidence behind every result |
| `council/` | The original council: cabinet, orchestrator, prompts |
| `gst/` | Measurement kit (gates, statistics, dictation registry) used by later cells |
| `harness/` | Earlier measurement layer (Cells 19–20) |
| `examples/` | The advisory test cases every cell draws from |
| `docs/` | Papers, the claims record, design notes, audits, frozen test items |
| `docs/ledger_explorer/` | Builds the public site from the runbook and STATUS.md |
| `site_v3/` | The built public site (committed, and deployed as-is by Netlify) |
| `archive/` | Retired material: the May prototype, earlier sites and paper drafts |

## Common tasks

```bash
# install
uv sync

# re-run one stage of a cell (each script lists its stages in its docstring)
.venv/bin/python train/run_cell61_bundle_ab.py measure

# rebuild the public site after editing the runbook or STATUS.md
.venv/bin/python docs/ledger_explorer/build.py

# compile a paper and check for errors or unresolved references
cd docs && ./checkpdf.sh paper_moa_audit.tex
```

**Deploying:** Netlify builds are paused (`[build.ignore]` in `netlify.toml`).
To publish, remove that block for a single push, then put it back.

## House rules for new experiments

- Local models only, $0 API spend.
- Write down what you expect, and what would prove it wrong, before running.
- Change one thing per comparison.
- No keyword-counting (regex) measurements (since 2026-08-09).
- Run the pre-recommendation checklist in STATUS.md §6 before proposing a cell.

## Status

Personal research, not a product. Drafts dated September 2026.
````

**Optional follow-up:** once `server/` is archived, change the `pyproject.toml` description to match the README's first paragraph.
