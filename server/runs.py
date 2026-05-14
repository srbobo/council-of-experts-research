"""In-memory run manager.

Each ``POST /api/run`` creates a ``RunState`` and kicks off an asyncio task
that executes the requested modes (local-council, opus-single, opus-council).
The task feeds progress events into a per-run ``asyncio.Queue`` so the SSE
endpoint can stream them to the browser in real time.

Disk persistence is delegated:
- Council runs land in ``runs/<timestamp>_<id>.json`` via the orchestrator's
  ``save_audit_log()`` (Phase 1 artifact, unchanged).
- Bench runs land in ``bench/runs/<timestamp>/<case-id>__<mode>.json`` via the
  bench runner's ``_save_run()`` (Phase 2 artifact, unchanged).

This module just coordinates — it does not duplicate persistence logic.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any

from bench.cost_guard import BudgetExceeded, CostGuard
from bench.opus_council import run_opus_council
from bench.opus_single import run_opus_single
from council.orchestrator import deliberate as council_deliberate, save_audit_log
from council.thermal import ThermalGuard


# Sentinel queue value the SSE endpoint uses as its "stream is done" signal.
# An explicit object is clearer than checking event["type"] == "done" everywhere.
STREAM_END = object()


def _now_iso() -> str:
    """Timezone-aware ISO-8601 timestamp for events and run records."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunState:
    """Per-run state held in memory while the run is active.

    `events` is a complete history (so a client connecting late can replay
    via /api/runs/{id} + /api/runs/{id}/stream). `queue` is the live SSE feed
    for clients that connect while the run is still in progress.
    """

    run_id: str
    case_id: str | None
    prompt: str
    modes: list[str]
    status: str = "pending"  # pending | running | completed | failed
    events: list[dict[str, Any]] = field(default_factory=list)
    results: dict[str, dict[str, Any]] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    started_at: str | None = None
    finished_at: str | None = None
    # asyncio.Queue is per-run; SSE clients drain it. Not serialized.
    queue: asyncio.Queue = field(default_factory=asyncio.Queue, repr=False)

    def to_summary(self) -> dict[str, Any]:
        """Serialize for /api/runs/{id} (no queue, no per-event detail)."""
        d = asdict(self)
        d.pop("queue", None)
        return d


class RunManager:
    """Tracks active and recently-finished runs in memory.

    Bounded LRU: keeps the last N runs in memory; older ones are evicted but
    their disk artifacts remain readable via /api/runs (which reads the
    runs/ and bench/runs/ directories directly).
    """

    def __init__(self, max_runs: int = 50) -> None:
        self._runs: dict[str, RunState] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._max_runs = max_runs

    # ---- registration ----

    def create(
        self,
        *,
        prompt: str,
        modes: list[str],
        case_id: str | None = None,
    ) -> RunState:
        """Allocate a RunState; caller schedules the execution coroutine."""
        run_id = uuid.uuid4().hex[:12]  # short ID for UI; uniqueness is fine within a session
        state = RunState(run_id=run_id, case_id=case_id, prompt=prompt, modes=modes)
        self._runs[run_id] = state

        # LRU eviction so a long-running server doesn't grow unboundedly.
        if len(self._runs) > self._max_runs:
            oldest = next(iter(self._runs))
            self._runs.pop(oldest, None)
            t = self._tasks.pop(oldest, None)
            if t is not None and not t.done():
                t.cancel()

        return state

    def get(self, run_id: str) -> RunState | None:
        return self._runs.get(run_id)

    def list(self) -> list[RunState]:
        return list(self._runs.values())

    # ---- execution ----

    def schedule(self, state: RunState) -> asyncio.Task:
        """Kick off the execution coroutine; return the asyncio Task handle."""
        task = asyncio.create_task(self._execute(state))
        self._tasks[state.run_id] = task
        return task

    async def _emit(self, state: RunState, event: dict[str, Any]) -> None:
        """Append to history and push to the live queue. Single source of truth
        for "an event happened" — keeps history and live stream in lockstep."""
        event = {**event, "ts": _now_iso()}
        state.events.append(event)
        await state.queue.put(event)

    async def _execute(self, state: RunState) -> None:
        """Run the requested modes in sequence and stream events."""
        state.status = "running"
        state.started_at = _now_iso()
        await self._emit(state, {"type": "run_started", "modes": state.modes})

        # One CostGuard for the whole run so the cap covers cumulative Opus spend
        # across opus-single + opus-council. Ledger lives in a per-run subdir.
        ledger_dir = Path("bench/runs") / f"server_{state.run_id}"
        guard = CostGuard(ledger_path=ledger_dir / "cost.json")
        await self._emit(state, {
            "type": "budget",
            "cap_usd": guard.cap_usd,
            "spent_usd": guard.spent_usd,
        })

        for mode in state.modes:
            await self._emit(state, {"type": "mode_started", "mode": mode})
            try:
                if mode == "local-council":
                    result = await self._run_local_council(state)
                elif mode == "opus-single":
                    result = await self._run_opus_single(state, guard)
                elif mode == "opus-council":
                    result = await self._run_opus_council(state, guard)
                else:
                    raise ValueError(f"Unknown mode: {mode}")

                state.results[mode] = result
                await self._emit(state, {
                    "type": "mode_completed",
                    "mode": mode,
                    "result": result,
                    "spent_usd": guard.spent_usd,
                })
            except BudgetExceeded as e:
                state.errors[mode] = f"BudgetExceeded: {e}"
                await self._emit(state, {
                    "type": "mode_refused",
                    "mode": mode,
                    "reason": str(e),
                })
            except Exception as e:
                state.errors[mode] = f"{type(e).__name__}: {e}"
                await self._emit(state, {
                    "type": "mode_failed",
                    "mode": mode,
                    "error": f"{type(e).__name__}: {e}",
                })

        state.status = "completed" if state.results else "failed"
        state.finished_at = _now_iso()
        await self._emit(state, {
            "type": "run_finished",
            "status": state.status,
            "results_count": len(state.results),
            "errors_count": len(state.errors),
            "spent_usd": guard.spent_usd,
        })
        # Sentinel so SSE consumers can break their read loop cleanly.
        await state.queue.put(STREAM_END)

    # ---- per-mode execution ----

    def _make_phase_emitter(self, state: RunState, mode: str):
        """Build an `on_phase(stage, detail)` callback that pipes orchestrator
        events into the run's event stream, tagged with the current mode."""

        def on_phase(stage: str, detail: str) -> None:
            # asyncio.Queue.put_nowait: orchestrator runs on the same loop, so
            # this lands in the queue immediately and SSE drains it next tick.
            event = {
                "type": "phase",
                "mode": mode,
                "stage": stage,
                "detail": detail,
                "ts": _now_iso(),
            }
            state.events.append(event)
            # put_nowait is safe here because the queue is unbounded.
            state.queue.put_nowait(event)

        return on_phase

    def _make_token_emitter(self, state: RunState, mode: str):
        """Build an `on_token(phase_tag, delta)` callback that streams text
        deltas onto the SSE feed tagged with `(mode, phase)`.

        Token events deliberately do NOT append to ``state.events`` — a 5-min
        deliberation can produce thousands of tokens, and the replay-on-
        connect history would balloon for no benefit. Late-connecting SSE
        clients still get the final assembled text via the per-mode
        ``mode_completed`` event when the phase finishes.
        """

        def on_token(phase_tag: str, delta: str) -> None:
            if not delta:
                return
            event = {
                "type": "token",
                "mode": mode,
                "phase": phase_tag,
                "delta": delta,
            }
            # Live stream only — skip events history to keep memory bounded.
            state.queue.put_nowait(event)

        return on_token

    async def _run_local_council(self, state: RunState) -> dict[str, Any]:
        """Local Phi-4 + Med42 + Saul + Qwen-Finance via Ollama."""
        thermal = ThermalGuard.from_env()
        on_phase = self._make_phase_emitter(state, "local-council")
        on_token = self._make_token_emitter(state, "local-council")
        result = await council_deliberate(
            state.prompt, thermal=thermal, on_phase=on_phase, on_token=on_token,
        )
        # Persist via the same path the council CLI uses, for a unified runs/ dir.
        run_id = state.case_id or f"server_{state.run_id}"
        save_audit_log(result, run_id=run_id)
        return {
            "mode": "local-council",
            "final_output": result.final_output,
            "total_latency_ms": result.total_latency_ms,
            "deliberation": result.to_dict(),
        }

    async def _run_opus_single(self, state: RunState, guard: CostGuard) -> dict[str, Any]:
        """One Opus call, no council architecture."""
        # opus-single doesn't have natural phase events — emit a coarse
        # progress signal at start and let the wall-clock latency do the rest.
        on_phase = self._make_phase_emitter(state, "opus-single")
        on_phase("calling", "Opus 4.7 single-shot")
        result = await run_opus_single(state.prompt, cost_guard=guard)
        return {
            "mode": "opus-single",
            "final_output": result.final_output,
            "total_latency_ms": result.latency_ms,
            "tokens": {"input": result.input_tokens, "output": result.output_tokens},
            # Surface to the UI inspector so the system prompt and the raw
            # Opus payload (including adaptive-thinking blocks under
            # content[].type == "thinking") can be inspected.
            "system_prompt": result.system_prompt,
            "raw_response": result.raw,
        }

    async def _run_opus_council(self, state: RunState, guard: CostGuard) -> dict[str, Any]:
        """Opus playing all four seats via the council orchestrator + injected chat."""
        on_phase = self._make_phase_emitter(state, "opus-council")
        # opus_council injects an Anthropic chat_fn but does NOT take an on_phase
        # parameter directly — call deliberate ourselves so we can pipe events.
        from bench.anthropic_client import chat as opus_chat

        bound_chat = partial(opus_chat, cost_guard=guard)
        thermal = ThermalGuard.from_env()
        result = await council_deliberate(
            state.prompt,
            thermal=thermal,
            on_phase=on_phase,
            chat_fn=bound_chat,
        )
        return {
            "mode": "opus-council",
            "final_output": result.final_output,
            "total_latency_ms": result.total_latency_ms,
            "deliberation": result.to_dict(),
        }


# Module-level singleton. The FastAPI app picks this up at import time.
manager = RunManager()
