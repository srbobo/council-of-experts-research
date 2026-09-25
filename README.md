# Council of Experts

A research program asking whether a *council* of specialist LLMs, whose answers
an editor model combines into one report (a Mixture-of-Agents design), gives
better answers than one model answering directly. Everything runs locally on
Apple Silicon with Ollama, and no paid API is used.

It started in May 2026 as a prototype. From July it became a series of
61 experiments ("cells"), each with its expectations written down before it ran.
The result is one paper and a redesigned system (the harness) built only from
the parts that held up.

**Public site:** <https://councilofexperts.netlify.app> shows every cell in plain
language, the claims, a glossary, the harness, and the saved run data.

## Where to start

| If you want… | Read |
|---|---|
| The findings, in plain language | [docs/PLAIN_LANGUAGE_COMPANION.md](docs/PLAIN_LANGUAGE_COMPANION.md) or the public site |
| The paper | [docs/paper_combined.pdf](docs/paper_combined.pdf) (source: [paper_combined.tex](docs/paper_combined.tex)) |
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
| `gst/` | Measurement kit (gates, statistics, dictation registry) used by later cells |
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

# compile the paper and check for errors or unresolved references
cd docs && ./checkpdf.sh paper_combined.tex
```

**Editing the runbook:** the site's plain-language summaries are keyed by runbook
line number, so edit existing lines in place rather than inserting or deleting
lines above entries that already have summaries.

**Deploying:** Netlify builds are paused (`[build.ignore]` in `netlify.toml`).
To publish, remove that block for a single push, then put it back.

## House rules for new experiments

- Local models only, $0 API spend.
- Write down what you expect, and what would prove it wrong, before running.
- Change one thing per comparison.
- No keyword-counting (regex) measurements (since 2026-08-09).
- Run the pre-recommendation checklist before proposing a cell (STATUS.md §6).

## Status

Personal research, not a product. Current paper draft: v0.2, September 2026.
