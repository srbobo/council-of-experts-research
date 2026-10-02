# Council of Experts

A research program asking whether a *council* of specialist LLMs, whose answers
an editor model combines into one report (a Mixture-of-Agents design), gives
better answers than one model answering directly. Everything runs locally on
Apple Silicon with Ollama, and no paid API is used.

It started in May 2026 as a prototype. From July it became a series of
experiments ("cells"), each with its expectations written down before it ran:
61 through September 2026, and 7 more planned on 1 October 2026 (Cells 62 to
68). The result so far is one paper draft and a redesigned system (the harness).

**October 2026 review.** A review of the whole program
([docs/BOARD_REVIEW_2026-10-01.md](docs/BOARD_REVIEW_2026-10-01.md)) did not
accept the paper as drafted. One widely quoted number came from a scoring bug,
several ranges were too narrow, and in most experiments the three "specialists"
were the editor model in three roles. The corrections are in STATUS.md and the
runbook, and the paper has been rewritten as draft v0.3 with a new title and
scope. Cells 62 to 67 are running to test what
recomputing could not fix. Two of them need blind labels from a person (see
"Blind labelling" below).

**Public site:** <https://councilofexperts.netlify.app> shows every cell in plain
language, the claims, a glossary, the harness, and the saved run data.

## Where to start

| If you want… | Read |
|---|---|
| The findings, in plain language | [docs/PLAIN_LANGUAGE_COMPANION.md](docs/PLAIN_LANGUAGE_COMPANION.md) or the public site |
| The paper (draft v0.3, rewritten after the October 2026 review; results of Cells 62 to 67 still to come) | [docs/paper_combined.pdf](docs/paper_combined.pdf) (source: [paper_combined.tex](docs/paper_combined.tex)) |
| The review and what it changed | [docs/BOARD_REVIEW_2026-10-01.md](docs/BOARD_REVIEW_2026-10-01.md); corrected figures in [bench/analysis/stage0/report.txt](bench/analysis/stage0/report.txt) |
| What the program claims today, and how sure it is | [docs/STATUS.md](docs/STATUS.md), the authoritative claims record |
| Every experiment, in order, with its full reasoning | [RUNBOOK_PAPER_HARDENING.md](RUNBOOK_PAPER_HARDENING.md), the lab notebook the site is built from |
| The redesigned system | [docs/HARNESS_SEAT_ARCHITECTURE.md](docs/HARNESS_SEAT_ARCHITECTURE.md) |
| Which local models are used, and how to rebuild them | [docs/MODEL_INVENTORY.md](docs/MODEL_INVENTORY.md) |

## Repository map

| Path | What's in it |
|---|---|
| `train/` | One script per cell (`run_cellNN_*.py`), training data, Modelfiles and adapter configs |
| `bench/runs/`, `bench/analysis/` | Saved run records and per-cell analysis: the evidence behind every result |
| `bench/*.py` | The prototype's comparison runner; older cells still import it |
| `council/` | The original council: cabinet, orchestrator, prompts |
| `gst/` | Measurement kit (gates, statistics, dictation registry) used by later cells; since October 2026 also small-sample statistics (`smallcluster`) and logged model calls (`runlog`) |
| `bench/labels/` | Blind labelling tasks for a person (Cells 62 and 66) and their labels |
| `bench/queue/` | Status and logs of the unattended run queue (`train/run_queue.py`) |
| `harness/` | Earlier measurement layer (Cells 19–20) |
| `examples/` | The advisory test cases every cell draws from |
| `docs/` | The paper, the claims record, design notes, audits, frozen test items |
| `docs/ledger_explorer/` | Builds the public site from the runbook and STATUS.md |
| `site_v3/` | The built public site (committed, and deployed as-is by Netlify) |
| `archive/` | Retired material: the May prototype, earlier sites and paper drafts (see [archive/README.md](archive/README.md)) |

## Common tasks

```bash
# install
uv sync

# re-run one stage of a cell (each script lists its stages in its docstring)
.venv/bin/python train/run_cell61_bundle_ab.py measure

# rebuild the public site after editing the runbook or STATUS.md
.venv/bin/python docs/ledger_explorer/build.py

# reproduce the review's numbers and the corrected figures (no model calls)
.venv/bin/python bench/analysis/board_review/checks.py
.venv/bin/python train/run_stage0_corrections.py

# see where the run queue for Cells 62 to 67 is
.venv/bin/python train/run_queue.py status

# compile the paper and check for errors or unresolved references
cd docs && ./checkpdf.sh paper_combined.tex
```

**Editing the runbook:** the site's plain-language summaries are keyed by runbook
line number, so edit existing lines in place rather than inserting or deleting
lines above entries that already have summaries.

**Deploying:** Netlify builds are paused (`[build.ignore]` in `netlify.toml`).
To publish, remove that block for a single push, then put it back.

**Blind labelling:** two experiments compare AI judges with one person's labels.
The tool shows one item at a time and nothing about where it came from. Do not
open `key.json` in a task folder until the labels are finished.

```bash
.venv/bin/python train/label_blind.py bench/labels/cell62_sentences --practice   # 20 practice sentences
.venv/bin/python train/label_blind.py bench/labels/cell62_sentences              # pass 1 (404 sentences)
.venv/bin/python train/label_blind.py bench/labels/cell62_sentences --pass 2     # at least 7 days later
.venv/bin/python train/label_blind.py bench/labels/cell66_conveyed               # 120 pairs, once the queue has drawn them
```

Commit each finished labels file before any scoring (the tool prints the command).

## House rules for new experiments

- Local models only, $0 API spend.
- Write down what you expect, and what would prove it wrong, before running.
- Change one thing per comparison.
- No keyword-counting (regex) measurements (since 2026-08-09).
- Run the pre-recommendation checklist before proposing a cell (STATUS.md §6).
- With few scenarios or items, analyse at the scenario or item level and print
  how many there are; count every pair in a preference comparison (since
  2026-10-01, STATUS.md §6 items 10 to 15).
- Every model call goes through `gst.runlog` so the record carries its time,
  model digest, seed and settings.

## Status

Personal research, not a product. Current paper draft: v0.3, October 2026
(corrected after the review; six planned experiments still running).
