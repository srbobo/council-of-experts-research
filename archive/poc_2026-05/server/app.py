"""FastAPI application: HTTP + SSE wrapper for the council and bench harness.

Endpoints
---------
- ``GET  /api/cases``               — the 5 canonical test cases
- ``GET  /api/budget``              — current cost-guard state
- ``POST /api/run``                 — kick off a deliberation; returns run_id
- ``GET  /api/runs``                — index of in-memory + on-disk runs
- ``GET  /api/runs/{run_id}``       — final results JSON
- ``GET  /api/runs/{run_id}/stream``— Server-Sent Events live progress
- ``GET  /``, ``/process``, ``/architecture`` — static HTML (placeholder until 3.2)

Localhost-only by design. CORS is locked to ``http://localhost:8000`` so the
backend cannot be embedded in third-party pages or driven from another origin.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env BEFORE importing modules that read env vars (BENCH_BUDGET_USD, etc.)
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from bench.cost_guard import CostGuard
from examples.test_cases import CASES, get_case

from .runs import STREAM_END, manager


# ----------------------------------------------------------------------------
# Pydantic request / response models
# ----------------------------------------------------------------------------


class RunRequest(BaseModel):
    """POST /api/run body."""

    # Either case_id (preset) or prompt (free-form) — at least one is required.
    case_id: str | None = None
    prompt: str | None = None
    # Modes to run. Default: all three.
    modes: list[str] = Field(default_factory=lambda: ["local-council", "opus-single", "opus-council"])


class RunResponse(BaseModel):
    """POST /api/run response."""

    run_id: str
    status: str  # "pending" | "running"


# ----------------------------------------------------------------------------
# App construction
# ----------------------------------------------------------------------------


app = FastAPI(
    title="Council of Experts",
    description="Local 4-model council vs Claude Opus 4.7 — A/B test harness.",
    version="0.1.0",
)

# Lock CORS to localhost. The frontend is served from the same origin (8000),
# so the only legitimate caller is the same-origin browser. No cross-origin
# allowance is intentional — the prompts aren't sensitive but the budget is.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------------
# /api/cases — list the canonical test cases
# ----------------------------------------------------------------------------


@app.get("/api/cases")
def list_cases() -> list[dict[str, Any]]:
    """Return the 5 test cases the UI's case selector populates from."""
    return [
        {
            "id": case.id,
            "title": case.title,
            "failure_mode": case.failure_mode.value,
            "prompt": case.prompt,
            "expected_routes": case.expected_routes,
            "rubric": [item.model_dump() for item in case.rubric],
        }
        for case in CASES
    ]


# ----------------------------------------------------------------------------
# /api/budget — current cost-guard state
# ----------------------------------------------------------------------------


@app.get("/api/budget")
def get_budget() -> dict[str, float]:
    """Return the current budget cap and how much has been spent so far.

    The UI reads this on page load and after each Opus call to update the
    budget progress bar. Note: spend is per-run-directory; this returns
    the global ``bench/runs/cost.json`` if it exists, or a fresh zero.
    """
    guard = CostGuard()  # default ledger path: bench/runs/cost.json
    return {
        "cap_usd": guard.cap_usd,
        "spent_usd": guard.spent_usd,
        "remaining_usd": max(0.0, guard.cap_usd - guard.spent_usd),
    }


# ----------------------------------------------------------------------------
# /api/run — start a deliberation
# ----------------------------------------------------------------------------


@app.post("/api/run", response_model=RunResponse)
async def start_run(req: RunRequest) -> RunResponse:
    """Kick off a deliberation. Returns immediately with a run_id; the actual
    work runs in the background and progress streams via /api/runs/{id}/stream.
    """
    # Resolve case_id vs prompt — exactly one must be set.
    if not req.case_id and not req.prompt:
        raise HTTPException(400, "Provide either case_id or prompt.")
    if req.case_id and req.prompt:
        raise HTTPException(400, "Provide case_id OR prompt, not both.")

    # Validate modes. The five baselines map one-for-one to the bench
    # CLI's BASELINE_MODES + MOE_MODES buckets; the swap variants don't
    # surface in the live A/B page (they're CLI-only for now since they
    # consume Opus $ at a different cadence than baselines).
    valid_modes = {
        "local-council",
        "opus-single", "opus-council",
        "gptoss-single", "gptoss-council",
    }
    invalid = [m for m in req.modes if m not in valid_modes]
    if invalid:
        raise HTTPException(400, f"Invalid mode(s): {invalid}. Allowed: {sorted(valid_modes)}")
    if not req.modes:
        raise HTTPException(400, "modes must not be empty.")

    # Resolve prompt text from case_id if needed
    if req.case_id:
        try:
            case = get_case(req.case_id)
        except KeyError as e:
            raise HTTPException(404, str(e))
        prompt = case.prompt
        case_id = case.id
    else:
        prompt = req.prompt or ""
        case_id = None

    state = manager.create(prompt=prompt, modes=req.modes, case_id=case_id)
    manager.schedule(state)
    return RunResponse(run_id=state.run_id, status=state.status)


# ----------------------------------------------------------------------------
# /api/runs — list in-memory runs (for the history sidebar)
# ----------------------------------------------------------------------------


@app.get("/api/runs")
def list_runs() -> list[dict[str, Any]]:
    """Return summaries of in-memory runs, newest first.

    Disk-only runs (from prior CLI invocations) are not included here —
    they're separately browsable via the orchestrator's audit logs at
    ``runs/`` and the bench harness output at ``bench/runs/``. The UI's
    history sidebar only needs the in-memory ones for now.
    """
    runs = manager.list()
    return [r.to_summary() for r in reversed(runs)]


# ----------------------------------------------------------------------------
# /api/runs/{id} — final results
# ----------------------------------------------------------------------------


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    """Return the run's full state, including all events and results."""
    state = manager.get(run_id)
    if state is None:
        raise HTTPException(404, f"No run with id={run_id!r}.")
    return state.to_summary()


# ----------------------------------------------------------------------------
# /api/runs/{id}/stream — Server-Sent Events live progress
# ----------------------------------------------------------------------------


@app.get("/api/runs/{run_id}/stream")
async def stream_run(run_id: str) -> StreamingResponse:
    """Stream events for a run as they happen, plus replay all past events
    once on connect (so a late-connecting client doesn't miss the start).

    The frontend opens this endpoint with EventSource; events arrive as
    JSON-encoded SSE messages. The stream ends with a final `done` event
    when the run finishes (or when an error frame arrives).
    """
    state = manager.get(run_id)
    if state is None:
        raise HTTPException(404, f"No run with id={run_id!r}.")

    async def event_gen():
        # Replay past events first so a late-connecting client sees the full
        # history. The current backlog snapshot is taken before we start
        # draining the live queue, so we don't double-emit.
        backlog = list(state.events)
        for event in backlog:
            yield f"data: {json.dumps(event)}\n\n"

        # Now drain live events. The producer puts a STREAM_END sentinel when
        # the run finishes — we use that to break cleanly.
        # Note: events that arrived between snapshotting the backlog and
        # starting this loop will appear in the queue as well; the frontend
        # de-duplicates by event timestamp + type if needed (and in practice
        # the backlog snapshot is fast enough that gaps are rare).
        seen_ts = {(e.get("ts"), e.get("type"), e.get("stage"), e.get("mode")) for e in backlog}
        while True:
            event = await state.queue.get()
            if event is STREAM_END:
                yield "data: {\"type\": \"stream_end\"}\n\n"
                break
            # Token events are NEVER stored in state.events (they'd balloon
            # the history) so they're not in the backlog and can't be
            # collisions — skip dedupe for them entirely. All other event
            # types get the (ts, type, stage, mode) dedupe.
            if event.get("type") != "token":
                key = (event.get("ts"), event.get("type"), event.get("stage"), event.get("mode"))
                if key in seen_ts:
                    continue  # don't re-emit events the backlog already contained
                seen_ts.add(key)
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            # Tell intermediaries not to buffer SSE — would defeat live streaming.
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ----------------------------------------------------------------------------
# Static frontend mount + page routes
# ----------------------------------------------------------------------------

# Static assets (CSS, JS, fonts) live under server/static/. In Phase 3.1 this
# directory is empty except for placeholder HTML; Phase 3.2 fills it in.
_STATIC_DIR = Path(__file__).parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Mount /static/* for assets. Page HTML is served from explicit routes below
# so we can swap implementations during 3.2 without changing the routing.
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


# Map each page route to its corresponding HTML file under static/. We serve
# them via FileResponse rather than mounting StaticFiles at root so the API
# routes (/api/*) take precedence and the SPA-style routing stays predictable.
def _serve(filename: str) -> FileResponse:
    """Return the named HTML page from static/. 404 if the file is missing.

    Sends a strict no-store cache header so the page is always re-fetched on
    navigation. Without this, some browsers will serve a stale HTML copy
    after the nav structure changes (adding a new tab, renaming a link), and
    the user has to hard-reload to see updates. Localhost-only dev tool —
    the cost of skipping the cache is negligible, and avoiding "why doesn't
    my new tab show up" debugging is worth it.
    """
    path = _STATIC_DIR / filename
    if not path.exists():
        raise HTTPException(404, f"Frontend asset {filename!r} not found.")
    # FastAPI infers the media_type from the extension; html → text/html.
    return FileResponse(
        path,
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/", response_class=HTMLResponse)
def page_root():
    return _serve("index.html")


@app.get("/process", response_class=HTMLResponse)
def page_process():
    return _serve("process.html")


@app.get("/architecture", response_class=HTMLResponse)
def page_architecture():
    return _serve("architecture.html")


@app.get("/results", response_class=HTMLResponse)
def page_results():
    return _serve("results.html")


# ----------------------------------------------------------------------------
# /api/prompts — the system prompts each phase actually saw
# ----------------------------------------------------------------------------


@app.get("/api/prompts")
def get_prompts() -> dict[str, str]:
    """Return the system prompts used by each phase of the council.

    These are the same prompts the local council uses; the bench harness
    injects an Anthropic-backed ``chat_fn`` into the same orchestrator, so
    opus-council sees these exact strings. opus-single uses a separate
    minimal system prompt from ``bench/opus_single.py``.

    The Results page inspector reads this so it can show what each phase
    actually saw — load-bearing for the article's claim that opus-council
    and local-council differ only in the model, not in the scaffolding.
    """
    # Local import to avoid forcing bench's optional anthropic dep at module
    # load — the bench module imports cleanly without anthropic installed,
    # but we still defer to keep the import path obvious.
    from bench.opus_single import SINGLE_SHOT_SYSTEM
    from council.prompts import (
        FINANCE_SYSTEM,
        HEALTHCARE_SYSTEM,
        LEAD_PLANNER_SYSTEM,
        LEAD_SYNTHESIS_SYSTEM,
        LEGAL_SYSTEM,
    )

    return {
        "lead_planner": LEAD_PLANNER_SYSTEM,
        "healthcare": HEALTHCARE_SYSTEM,
        "legal": LEGAL_SYSTEM,
        "finance": FINANCE_SYSTEM,
        "lead_synthesis": LEAD_SYNTHESIS_SYSTEM,
        "opus_single": SINGLE_SHOT_SYSTEM,
    }


# ----------------------------------------------------------------------------
# /api/imported/{case_id} — the captured Opus + local-council runs for a case
# ----------------------------------------------------------------------------

_IMPORTED_DIR = Path("bench/runs/imported")


@app.get("/api/imported/{case_id}")
def get_imported_runs(case_id: str) -> dict[str, Any]:
    """Return all imported runs for one case, grouped by mode.

    The Results page renders these in the same three-column shape as the
    A/B page. Within each mode bucket, the MOST RECENT file wins (sorted
    by the ISO-8601 timestamp prefix in the filename).
    """
    try:
        case = get_case(case_id)
    except KeyError as e:
        raise HTTPException(404, str(e))

    # Group all matching imported runs by mode; keep only the latest per mode.
    by_mode: dict[str, dict[str, Any]] = {}
    if _IMPORTED_DIR.exists():
        for path in sorted(_IMPORTED_DIR.glob(f"*{case_id}*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if data.get("case_id") != case_id:
                continue
            mode = data.get("mode") or "unknown"
            # `sorted` produces ascending order so the last assignment wins
            # for each mode — that's the most recent capture, which is what
            # we want to display.
            by_mode[mode] = data

    return {
        "case_id": case.id,
        "case_title": case.title,
        "case_prompt": case.prompt,
        "failure_mode": case.failure_mode.value,
        "modes": by_mode,
    }
