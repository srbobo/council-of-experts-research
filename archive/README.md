# Archive

Material that no longer drives the experiment, moved here on 2026-09-24 to keep
the top of the repo readable. Nothing live imports or reads these files; the Cell
Ledger does not cite any of them as evidence. Files were moved with `git mv`, so
`git log --follow <path>` shows their full history. The audit that decided each
move is [REPO_CLEANUP_AUDIT_2026-09-24.md](REPO_CLEANUP_AUDIT_2026-09-24.md).

| Folder | What it was | Retired | Replaced by |
|---|---|---|---|
| [poc_2026-05/](poc_2026-05/) | The May prototype: the v5 spec (`.docx`), `IMPLEMENTATION_PLAN.md`, the Opus hybrid swap plan, the FastAPI web UI (`server/`), its static-site builder (`scripts/`), the bench tests (`tests/`), and a one-off Claude answer (`exp/`). `runs/` holds the prototype's CLI logs locally (not in git). | July 2026, when the program became the $0, local-only paper-hardening campaign | `RUNBOOK_PAPER_HARDENING.md` |
| [dpo_2026-07/](dpo_2026-07/) | The DPO + prompt-transfer plan that came just before Cell 1 | 2026-07-11 | `RUNBOOK_PAPER_HARDENING.md` (its CDS/ALR definitions are copied into that runbook's glossary) |
| [sites/](sites/) | `site/` (public site until 2026-09-24), `site_v2/` (draft, never deployed) with its CI workflow (`site_v2_ci.yml`), and locally, the 2026-09-15 technical edition of the ledger explorer (not in git) | 2026-09-24 | `site_v3/`, built by `docs/ledger_explorer/build.py` |
| [papers/](papers/) | Earlier paper drafts: *Rendered, Not Transported* (`paper.tex`), *Knowing When to Hedge* (calibration, retracted), *Witnesses, Not Amplifiers*, *A Shrinkage Law* (framework), *What Aggregation Does* (behavior), the MoA-audit and harness-design papers, the Markdown first draft, and the figures they used | August–September 2026 | `docs/paper_combined.tex` |
| [design_2026-08/](design_2026-08/) | The GST framework design (`INTERVENTION_DESIGN.md`) and the regex-scored run table (`RUN_LEDGER.md`) with its generator | 2026-08-09, when regex stopped being accepted as a measuring tool | `docs/HARNESS_SEAT_ARCHITECTURE.md`; the site's Data tab |

To compile an archived paper: `cd archive/papers && tectonic <name>.tex` (the figures
are in `figs/` beside them). The regenerator for the run table works from the repo
root: `.venv/bin/python archive/design_2026-08/build_ledger.py`.
