# Council of Experts v5 — Implementation Plan

**Goal.** Stand up the v5 Council of Experts on a MacBook Air M5 (32GB), build an A/B comparison harness against Claude Opus 4.7, and present the whole thing as a Speaker Coach-style web app with a technical page and a non-technical page — plus a static report covering 5 use cases.

**Source spec.** [`Council_of_Experts_v5_FineTunedCabinet.docx`](Council_of_Experts_v5_FineTunedCabinet.docx) (this directory).

**Status.** Drafted, awaiting Sam's approval. Update this section as phases complete.

- [x] Plan drafted
- [ ] Plan approved
- [ ] Phase 1 — local council working end-to-end via CLI
- [ ] Phase 2 — bench harness comparing Council vs Opus
- [ ] Phase 3 — web UI (A/B page + technical page + non-technical page)
- [ ] Phase 4 — final report covering all 5 test cases

---

## Decisions locked in

| #  | Decision                                                                                                | Source     |
| -- | ------------------------------------------------------------------------------------------------------- | ---------- |
| 1  | **Sequential execution** mode for the council; no parallel mode in v1                                   | Q1         |
| 2  | **Ollama** as the runtime for all four GGUF models                                                      | Q2         |
| 3  | Three-agent cabinet (Healthcare / Legal / Finance) plus Phi-4 Lead. **No Best Delegate / education agent** in v1 | Q3 |
| 4  | The council itself never calls cloud APIs (no escalation router)                                        | Q4         |
| 5  | **Thermal-aware execution policy**: inter-agent pauses + `asitop` monitoring, given fanless M5 Air      | Q5         |
| 6  | Final deliverable is a **web UI** (A/B page + non-technical process page + technical architecture page) plus an exportable **static report** | Q6 |
| 7  | Bench compares three modes: **Local Council**, **Opus single-shot**, **Opus-as-council**                | Q7         |
| 8  | Scoring is **subjective human review** in v1 (no LLM-as-judge)                                          | Q8         |
| 9  | **Low temperature**, single run per case in v1 (no variance analysis)                                   | Q9         |

## Resolved: Cost path and visual direction

**Cost path — Opus runs paused, budget cap set to $0.** Sam's directive 2026-05-05: hold on any Opus calls until further notice. Reference numbers preserved here for when the cap is raised. **Pricing corrected 2026-05-07** after the claude-api skill confirmed Opus 4.7 is $5/MTok input and $25/MTok output (the earlier $15/$75 was a wrong guess). Total estimate is now ~$0.93, not the ~$2.80 originally quoted:

| Mode            | Calls (5 cases) | Input tokens   | Output tokens | Est. cost (when re-enabled) |
| --------------- | --------------- | -------------- | ------------- | --------------------------- |
| `opus-single`   | 5               | ~5K            | ~15K          | ~$0.40                      |
| `opus-council`  | 25 (5 seats × 5)| ~45K (cached)  | ~47K          | ~$0.53                      |
| **Total**       | 30              | ~50K           | ~62K          | **~$0.93**                  |

**Current state of the bench harness:**
- `BENCH_BUDGET_USD=0` in `.env` — `bench/cost_guard.py` will refuse any Opus call while the cap is at zero
- The harness code itself can still be built and unit-tested in Phase 2, but no live Opus calls happen until Sam explicitly raises the cap
- Phase 4 (final report) initially runs with **Local Council results only**; Opus columns in the UI and report show as "Paused — budget cap at $0" placeholders
- When the cap is raised, re-running the bench fills in the missing columns without touching the local council results

**Why the Max subscription can't substitute.** The Claude Max plan cannot authenticate the Claude Agent SDK or direct Anthropic SDK calls from a long-running FastAPI backend (verified against current Anthropic docs). Max is for interactive claude.ai and Claude Code use only; the API is a separately-billed rail. So when Opus calls are eventually re-enabled, they go through metered API billing.

**Visual direction — lab-notebook / investigative-research aesthetic.** Fresh design, no carry-over from the personal site. Inspiration: Distill.pub, Observable, scientific publishing.

| Element         | Choice                                                                |
| --------------- | --------------------------------------------------------------------- |
| Background      | Off-white `#FAFAF7` (paper-like)                                      |
| Body text       | Near-black `#1A1A1A`                                                  |
| Secondary text  | Warm gray `#6B6B66`                                                   |
| Accent          | Muted paper-amber `#C7793F` — links, active states, case fingerprints |
| Borders         | `#E5E2DC`                                                             |
| Type — body     | Inter (single family, multiple weights)                               |
| Type — mono     | JetBrains Mono — for tokens, costs, latencies, inline tags            |
| Hierarchy       | Size + weight only; no serif/sans pairing                             |
| Layout          | 720px column on explainer pages; full-width 3-column grid on A/B page |
| Rhythm          | 8px base grid, 1.6 line height                                        |

**One distinctive UI element: the case fingerprint** — a three-segment horizontal bar next to every case title, where each segment is filled or empty depending on which industry agents were consulted. Acts as a visual identity per case and a routing diagnostic at a glance. Appears in the live UI and the static report.

**Tone of voice.** Factual headlines ("What we tested," not "Putting AI to the test"). Numbers always shown with units. Footnote markers for caveats. The design reinforces: honest experiment, not sales pitch.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Browser (localhost)                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ A/B page     │  │ Process page │  │ Architecture     │   │
│  │ (query + run)│  │ (non-tech)   │  │ page (technical) │   │
│  └──────┬───────┘  └──────────────┘  └──────────────────┘   │
└─────────┼───────────────────────────────────────────────────┘
          │ HTTP + SSE
┌─────────▼───────────────────────────────────────────────────┐
│ FastAPI server (localhost:8000)                             │
│  ┌─────────────────────┐   ┌──────────────────────────┐     │
│  │ council/            │   │ bench/                   │     │
│  │  ├ orchestrator.py  │   │  ├ runner.py             │     │
│  │  ├ cabinet.py       │   │  ├ opus_single.py        │     │
│  │  ├ prompts.py       │   │  ├ opus_council.py       │     │
│  │  └ models.py        │   │  └ cost_guard.py ($10)   │     │
│  └─────────┬───────────┘   └──────────┬───────────────┘     │
└────────────┼──────────────────────────┼─────────────────────┘
             │                          │
             ▼                          ▼
   ┌──────────────────┐       ┌────────────────────────┐
   │ Ollama (local)   │       │ Anthropic API          │
   │  • phi4:14b      │       │  • claude-opus-4-7     │
   │  • med42-v2      │       │  (bench harness only)  │
   │  • saul-7b       │       └────────────────────────┘
   │  • qwen-fin-r-8b │
   └──────────────────┘
```

**Boundaries that matter.**
- `council/` never imports from `bench/`. The reverse is fine.
- `bench/` is the only place that touches the network.
- The web UI talks to one local server only; no third-party JS, no analytics, no CDN fonts that would leak prompts via Referer.

---

## Phase 1 — Local Council (≈ 2–3 days)

### 1.1 Prerequisites

| Tool       | Why                                          | Install                              |
| ---------- | -------------------------------------------- | ------------------------------------ |
| Homebrew   | Package manager                              | already installed (verify)           |
| llama.cpp  | One-time finance-model self-quantization     | `brew install llama.cpp`             |
| asitop     | Live CPU/GPU/memory/thermal monitoring       | `pip install asitop`                 |
| uv         | Python env + dependency manager              | `brew install uv`                    |
| Ollama     | Local model runtime                          | already installed (verify ≥ 0.4.x)   |
| LM Studio  | Side-by-side benchmark only; not in critical path | already installed                |

**Memory tuning (one-line, one-time, requires sudo):**
```bash
sudo sysctl iogpu.wired_limit_mb=26000
```
- Plain English: macOS reserves about a quarter of unified memory away from Metal by default. This raises the cap so the GPU side can grab up to ~26 GB, leaving ~6 GB for the OS. Single biggest perf knob on Apple Silicon for local LLMs. Reverts on reboot; persist via `/etc/sysctl.conf` later if we want it sticky.

### 1.2 Pull the four models

```bash
# Phi-4 14B (Lead) — Q4_K_M ≈ 9.0 GB
ollama pull phi4:14b

# Med42-v2 8B (Healthcare) — Q4_K_M ≈ 5.0 GB
# Hugging Face mirror: bartowski/Med42-v2-8B-GGUF
ollama pull hf.co/bartowski/Med42-v2-8B-GGUF:Q4_K_M

# SaulLM-7B-Instruct-v1 (Legal) — Q4_K_M ≈ 5.0 GB
# Hugging Face mirror: MaziyarPanahi/SaulLM-7B-Instruct-v1-GGUF
ollama pull hf.co/MaziyarPanahi/SaulLM-7B-Instruct-v1-GGUF:Q4_K_M

# Qwen-Open-Finance-R 8B (Finance) — Q8_0 ≈ 8.7 GB initially
# Hugging Face mirror: pate2464/Qwen-Open-Finance-R-8B-GGUF
ollama pull hf.co/pate2464/Qwen-Open-Finance-R-8B-GGUF:Q8_0
```
*Sam: each `ollama pull` will fetch several GB. Total disk ≈ 28 GB after all four.*

### 1.3 Self-quantize Finance to Q4_K_M (recommended even in sequential mode)

Per the v5 docs (`docs/QUANTIZATION.md` in the source package), this is a 30-min one-time procedure using `llama.cpp` tooling. Drops the finance model from ~8.7 GB to ~5 GB and speeds inference with negligible quality loss. Worth doing in Phase 1 even though sequential mode would survive without it.

### 1.4 Build the `council/` package

Following the file layout from the v5 spec (Appendix in source doc). Module breakdown:

| File                       | Purpose                                                                 |
| -------------------------- | ----------------------------------------------------------------------- |
| `council/cabinet.py`       | Lead + 3 IndustryAgent definitions, quantization metadata, hf_source    |
| `council/models.py`        | Ollama client (OpenAI-compatible)                                       |
| `council/prompts.py`       | Lead's planner + synthesis prompts; per-agent system prompts            |
| `council/orchestrator.py`  | 3-phase deliberation loop: plan → consult → synthesize, with audit log  |
| `council/thermal.py`       | Inter-agent pause policy; reads `pmset -g thermlog` and slows down on amber |
| `council/__main__.py`      | CLI entry: `python -m council deliberate --case <id>`                   |
| `examples/test_cases.py`   | The 5 test cases as Python data, with rubric metadata                   |

**Code style.** Per project CLAUDE.md, every function gets a header comment explaining purpose / inputs / outputs, plus inline comments naming the library on first use (e.g. "Ollama chat endpoint — OpenAI-compatible /v1/chat/completions"). Comments explain *why*, not *what*.

### 1.5 Smoke test via CLI

Run all 5 test cases through the CLI before any UI work. Confirm:
- Each agent returns coherent, on-character output (Med42 sounds clinical, SaulLM uses real legal vocabulary, Qwen-Finance reaches for frameworks)
- Sequential timing roughly matches doc estimate (~3–4 minutes for a 3-domain question on M5)
- `asitop` shows GPU staying loaded, no swap, thermal stays green or amber (not red)
- The audit log captures the routing plan, each agent's input + output, and the synthesis input

**Phase 1 exit criteria.** All 5 test cases run end-to-end via CLI, produce subjectively reasonable outputs, and stay within thermal limits on the M5 Air.

---

## Phase 2 — Bench Harness (≈ 1–2 days)

> **Status as of 2026-05-07: COMPLETE.** Bench harness fully built and unit-tested with mocked Opus responses; 6/6 tests pass. Budget cap remains $0 per Sam's directive — at $0, the harness refuses Opus calls before any HTTP request (verified end-to-end). Live runs are deferred until Sam raises `BENCH_BUDGET_USD`.
>
> **Files delivered:**
> - `council/orchestrator.py` — refactored with `chat_fn` injection point (backwards-compatible default)
> - `bench/anthropic_client.py` — Anthropic SDK wrapper with prompt caching, adaptive thinking, and cost-guard integration
> - `bench/cost_guard.py` — pricing corrected to actual Opus 4.7 rates ($5/$25, not $15/$75)
> - `bench/opus_single.py` — single-shot Opus mode
> - `bench/opus_council.py` — Opus playing all four council seats via injected `chat_fn`
> - `bench/runner.py` + `bench/__main__.py` — CLI: `python -m bench compare --case <id> [--modes ...]`
> - `tests/test_bench.py` — 6 tests covering response mapping, cost-guard integration, system-prompt caching, Opus 4.7 breaking-change compliance, and budget enforcement

### 2.1 Anthropic SDK integration

When this code is written I'll invoke the **claude-api** skill so the integration uses Anthropic's current best practices:
- Model ID `claude-opus-4-7`
- **Extended thinking enabled** for fairness — the local council leans on Phi-4's reasoning chain; Opus should get to think too
- **Prompt caching** on the system prompts and per-seat instructions, since we re-use them across cases and modes
- Per-call cost tracking
- A **`bench/cost_guard.py`** module that maintains a running total in `bench/runs/<timestamp>/cost.json` and aborts the run if total + projected next-call cost would exceed **$10**

**Plain-English of the cost guard.** Before each Opus call, estimate cost using current pricing × prompt token count (cached vs uncached) + max output tokens. Add to running total. If next call would push past $10, raise `BudgetExceeded` and exit cleanly without making the call. Default budget is `BENCH_BUDGET_USD=10` in `.env`; user can lower it but not raise it without editing the source.

### 2.2 Two Opus modes

| Mode             | What it does                                                                                                  |
| ---------------- | ------------------------------------------------------------------------------------------------------------- |
| `opus-single`    | One Opus call. The user query goes in, Opus answers directly. Tests "raw frontier vs whole council."          |
| `opus-council`   | Opus plays all four seats in sequence using the *same* planner / agent / synthesis prompts as the local council. Tests "real fine-tunes vs prompted generalist" with architecture held constant. |

### 2.3 Output format

Each run produces a JSON file at `bench/runs/<timestamp>/<case-id>__<mode>.json`:
```json
{
  "case_id": "case_1_clinical_decision_support",
  "mode": "opus-council",
  "prompt": "...",
  "model_versions": { "phi4": "14b@Q4_K_M", "opus": "claude-opus-4-7" },
  "stages": [ /* planner output, each agent output, synthesis output */ ],
  "final_output": "...",
  "latency_ms": 124300,
  "tokens": { "input": 4821, "output": 2103, "cached": 3200 },
  "cost_usd": 0.41,
  "timestamp": "2026-05-06T14:22:03Z"
}
```

**Phase 2 exit criteria.** A single CLI command runs all 5 cases × 3 modes (`local-council`, `opus-single`, `opus-council`) and produces 15 JSON files plus a cost ledger that came in under budget.

---

## Phase 3 — Web UI (≈ 3–4 days)

> **Status as of 2026-05-09: COMPLETE.** FastAPI backend (7 endpoints, SSE streaming, in-memory run manager) plus three-page static frontend (lab-notebook design system, self-hosted fonts, vanilla JS) shipped. Backend smoke-tested end-to-end — every endpoint returns the expected shape, SSE events arrive in the right order, $0 budget refuses cleanly without any network call. Visual verification in the browser is open as the only remaining check (Chrome MCP extension wasn't connected during dev; Sam to do a manual pass).
>
> **Files delivered:**
> - `server/app.py` — FastAPI app, 7 endpoints, CORS locked to localhost
> - `server/runs.py` — `RunManager` with asyncio task tracking + per-run event queue; reuses orchestrator's existing `on_phase` callback as the streaming source
> - `server/__main__.py` — uvicorn launcher (`python -m server` or `coe-server`)
> - `server/static/index.html` + `process.html` + `architecture.html` — three pages, shared header/footer markup
> - `server/static/css/styles.css` — full lab-notebook design system: paper-amber accent on off-white, Inter + JetBrains Mono, design tokens, layout primitives, components (`.fingerprint`, `.budget`, `.pill`, `.button`, `.card`)
> - `server/static/js/app.js` — A/B page logic: case loader, budget bar, run lifecycle, SSE event handler, three-column live render
> - `server/static/fonts/*.woff2` — self-hosted Inter Variable + JetBrains Mono Regular (374 KB total)


### 3.1 Backend (FastAPI)

| Endpoint                                  | Purpose                                                       |
| ----------------------------------------- | ------------------------------------------------------------- |
| `POST /api/run`                           | Body: `{ prompt, modes: [local, opus-single, opus-council] }` — kicks off runs, returns job ID |
| `GET /api/runs/{id}/stream` (SSE)         | Streams stage-by-stage updates so the UI can show live progress |
| `GET /api/runs/{id}`                      | Final results, all modes                                      |
| `GET /api/cases`                          | The 5 test cases with prompts and rubric notes                |
| `GET /api/budget`                         | Remaining bench budget in USD                                 |
| `GET /` `/process` `/architecture`        | Static page serving                                           |

Localhost only. No auth. CORS locked to localhost.

### 3.2 Frontend (static HTML/CSS/JS, in Sam's existing design language)

Three pages, all sharing one stylesheet:

**`/` — A/B testing page.** Big query input. Below it, three columns labeled "Local Council", "Opus single-shot", "Opus-as-council". Each column streams its output live. Bottom of each column shows latency, token count, and cost. Top-right of the page: cumulative session cost vs the $10 cap, as a thin progress bar.

**`/process` — non-technical explainer.** Single column, generous whitespace, large display heading. Sections:
1. *What is this* — two paragraphs, no jargon
2. *Why fine-tunes matter* — analogy: panel of specialist consultants vs one well-read generalist
3. *How the test works* — diagram of three columns
4. *What we're measuring* — privacy, cost, quality, latency, in plain language
5. *What we found* — placeholder until Phase 4

**`/architecture` — technical explainer.** Single column. Sections:
1. *Cabinet table* — same as the source doc's Part 1 table
2. *Memory budget* — same as Part 2 table, with the actual measured M5 numbers filled in after Phase 1
3. *Sequential vs parallel* — and why we're sequential
4. *Thermal policy* — what `council/thermal.py` does and why
5. *Bench methodology* — three modes, what's held constant, what isn't, the cost guard
6. *Honesty caveats* — training cutoffs, no LLM-as-judge, single run per case

**Visual language.** See the "Resolved: Cost path and visual direction" section near the top of this plan for the full design recipe (lab-notebook aesthetic, paper-amber accent, Inter + JetBrains Mono, case-fingerprint motif). The frontend implements that recipe consistently across all three pages, with one stylesheet and no external font CDNs (fonts self-hosted to avoid leaking prompt content via Referer headers).

### 3.3 UX flow on the A/B page

1. Sam opens `localhost:8000/`
2. Picks one of the 5 test cases from a dropdown, *or* writes a custom prompt
3. Hits "Run". Three columns light up with spinners and stream stage-by-stage:
   - Local Council column shows: planner output → each agent's output → final synthesis
   - Opus-as-council column shows the same shape with Opus playing each seat
   - Opus single-shot column streams a single response
4. When all three complete, a small "Notes" textarea appears at the bottom of each column for Sam's subjective rubric review
5. "Save run" persists everything (JSON + Sam's notes) to `bench/runs/<timestamp>/`
6. "Export report" assembles the static report (Phase 4)

**Phase 3 exit criteria.** Sam can run any of the 5 test cases through all three modes, watch the streams, write rubric notes, save the run, and reload the page to see prior runs.

---

## Phase 4 — Final Report (≈ 1 day)

### 4.1 Run all 5 cases

All three modes per case. Single run each (per Q9). Sam reviews each subjectively and writes rubric notes per case in the UI. Approximate budget: ~$2–4 of the $10 cap.

### 4.2 Static report artifact

Single-page HTML, exportable from the UI via "Export report". Mirrors the live UI's visual language and is fully self-contained (inlined CSS, no API keys, no external requests). Two top-level sections matching the live site's two pages.

**Non-technical section.**
- *Executive summary* — one paragraph: the question, the method, the headline finding
- *What we tested* — 5 cases with one-line each
- *What we found* — Sam's per-case judgments rolled up

**Technical section.**
- Methodology: three modes, what's constant, what isn't
- Per-case detail: prompt, three outputs side-by-side, Sam's rubric notes, latency / cost / token table
- Honest caveats: training cutoffs, single-run, subjective scoring, thermal observations
- Cost ledger

**Deployable.** No API keys baked in; pure static output. Can sit at `coe-report.netlify.app` (or wherever) without exposing anything sensitive. The live A/B UI cannot be deployed publicly because it depends on a local Ollama instance — that one stays on the M5.

**Phase 4 exit criteria.** A single HTML file under ~1 MB that Sam can open standalone, share, or deploy.

---

## Test cases (locked in)

All five force three-domain routing, divergent by failure mode tested.

| #  | Case                                             | Failure mode it stresses                              |
| -- | ------------------------------------------------ | ----------------------------------------------------- |
| 1  | AI clinical decision support rollout             | Pure synthesis under competing recommendations        |
| 2  | Cross-border digital therapeutic launch (US/UK/DE) | Jurisdictional vocabulary discipline                |
| 3  | Capitated Medicare Advantage risk contract       | Quantitative reasoning, framework discipline          |
| 4  | GLP-1 employer coverage decision                 | Recency / training-cutoff honesty                     |
| 5  | Nonprofit hospital → PE conversion               | Adversarial cross-domain tension; multi-stakeholder   |

Full prompts and per-case rubric notes live in `examples/test_cases.py`.

**Negative controls (deferred, optional).** Two extra cases not in the canonical suite but worth running once the harness exists:
- *Off-topic*: "How should I organize a small NYC closet?" — does the Lead correctly consult zero agents?
- *Single-domain depth*: a pure clinical edge case — does Med42 outperform a generalist on something none of the other domains touch?

---

## Risks and unknowns

- **Source-doc model paths were partially aspirational.** Discovered during Phase 1.2 pulls (2026-05-05): the specific GGUF mirror paths in `Council_of_Experts_v5_FineTunedCabinet.docx` (e.g. `bartowski/Med42-v2-8B-GGUF`, `MaziyarPanahi/SaulLM-7B-Instruct-v1-GGUF`, `pate2464/Qwen-Open-Finance-R-8B-GGUF:Q8_0`) returned 401/500 errors. The base models (m42-health/Llama3-Med42-8B, Equall/Saul-7B-Instruct-v1, DragonLLM/Qwen-Open-Finance-R-8B) are real and on HuggingFace; only the specific GGUF re-uploads were wrong or had different exact paths. Resolved by switching to verified community mirrors:
  - Healthcare: `mradermacher/Llama3-Med42-8B-GGUF:Q4_K_M`
  - Legal: `MaziyarPanahi/Saul-Instruct-v1-GGUF:Q4_K_M`
  - Finance: `pate2464/Qwen-Open-Finance-R-8B-FP8-Q8_0-GGUF` (still Q8_0, ~9 GB, per Sam's directive to keep the larger model)
- **Thermal throttling on M5 Air.** Mitigated by sequential execution + thermal-aware pauses + asitop. May still see degradation on case 5 (longest). Plan: measure during Phase 1 smoke test, tune pause length if needed.
- **Phi-4 14B reasoning quality vs Opus 4.7.** Opus likely wins subjectively on case 1 and case 5. The point of the experiment is to measure *how much* and *where the gap is narrowest* — that's the article-relevant finding.
- **Q8_0 finance model size.** Plan recommends self-quantizing to Q4_K_M in Phase 1.3. If Sam skips it, sequential mode still works but with less headroom.
- **Lab-notebook design direction.** This is my judgment call, not anchored to a prior reference. If the first rendered page feels off, easier to course-correct after Phase 1 than after Phase 3 is fully built.

## Out of scope for v1

- Education / Best Delegate fine-tune as a fourth agent
- LLM-as-judge automated scoring
- Multi-run variance analysis
- Hybrid cloud router (council escalating to Opus on demand during normal use)
- Public deployment of the live A/B UI (Ollama dependency makes this local-only by design — only the static report is shareable)
- Parallel execution mode

## Glossary (for the non-technical page; lives here so it's maintained alongside the plan)

- **Quantization** — compressing a model's weights from full precision to lower precision (Q4_K_M = 4-bit, Q8_0 = 8-bit). Smaller and faster, with small quality loss.
- **GGUF** — the file format Ollama and llama.cpp use for quantized local models.
- **Lead Agent** — the model that plans which specialists to consult and synthesizes their responses.
- **Industry Agent** — a model fine-tuned on a specific domain (medicine, law, finance).
- **Sequential mode** — only one industry agent in memory at a time, swapped in and out around the Lead.
- **Extended thinking** — Claude's mode where the model reasons before responding. Used in Opus runs for fairness against the council's planner stage.
