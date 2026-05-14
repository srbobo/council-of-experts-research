"""Top-level bench CLI: run a case through one or more comparison modes.

Three modes:

  - ``local-council``  : the local Phi-4 + 3 fine-tunes (no API calls, no cost)
  - ``opus-single``    : one Opus 4.7 call, no council architecture
  - ``opus-council``   : Opus 4.7 plays all four council seats (same prompts,
                         same orchestration loop as local-council)

Each (case × mode) run produces a JSON file at
``bench/runs/<timestamp>/<case-id>__<mode>.json``. A combined ``summary.json``
in the same directory captures the side-by-side comparison metadata.

Run via:

    python -m bench compare --case case_1_clinical_decision_support
    python -m bench compare --case case_2_... --modes local-council,opus-single
    python -m bench compare --case case_3_... --modes all
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Load .env (for OLLAMA_HOST, BENCH_BUDGET_USD, ANTHROPIC_API_KEY)
from dotenv import load_dotenv

load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from council.orchestrator import deliberate as council_deliberate, save_audit_log
from council.thermal import ThermalGuard

from .cost_guard import BudgetExceeded, CostGuard
from .opus_council import run_opus_council
from .opus_single import run_opus_single

console = Console()

# Available modes. ``all`` is a convenience alias the CLI expands to all three.
ALL_MODES = ["local-council", "opus-single", "opus-council"]


def _stamp() -> str:
    """Compact UTC timestamp suitable for filesystem use."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


def _to_jsonable(obj: Any) -> Any:
    """Recursively convert dataclasses / Pydantic models to plain dicts.

    The orchestrator's ``DeliberationResult`` is a dataclass; the bench's
    ``OpusSingleResult`` is also a dataclass; raw responses inside them
    are already plain dicts via ``model_dump``. Default ``json.dumps``
    chokes on dataclasses; this normalizes them before write.
    """
    if is_dataclass(obj) and not isinstance(obj, type):
        return _to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def _save_run(run_dir: Path, case_id: str, mode: str, payload: Any) -> Path:
    """Persist one (case × mode) run as JSON."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"{case_id}__{mode}.json"
    with path.open("w") as f:
        json.dump(_to_jsonable(payload), f, indent=2, default=str)
    return path


async def _run_local_council(query: str) -> dict[str, Any]:
    """Run the local Phi-4 + Med42 + Saul + Qwen-Finance council via Ollama."""
    thermal = ThermalGuard.from_env()
    result = await council_deliberate(query, thermal=thermal)
    # Convert to a dict that's symmetrical with the opus-single result shape.
    return {
        "mode": "local-council",
        "query": query,
        "final_output": result.final_output,
        "total_latency_ms": result.total_latency_ms,
        "deliberation": result.to_dict(),
    }


async def _run_opus_single(query: str, guard: CostGuard) -> dict[str, Any]:
    """One Opus call, no council. Returns the symmetric result dict."""
    result = await run_opus_single(query, cost_guard=guard)
    return {
        "mode": "opus-single",
        "query": query,
        "final_output": result.final_output,
        "total_latency_ms": result.latency_ms,
        "tokens": {"input": result.input_tokens, "output": result.output_tokens},
    }


async def _run_opus_council(query: str, guard: CostGuard) -> dict[str, Any]:
    """Opus plays all four seats via the council orchestrator."""
    result = await run_opus_council(query, cost_guard=guard)
    return {
        "mode": "opus-council",
        "query": query,
        "final_output": result.final_output,
        "total_latency_ms": result.total_latency_ms,
        "deliberation": result.to_dict(),
    }


async def _compare(case_id: str, modes: list[str]) -> int:
    """Run one case through the selected modes, persist results, summarize."""
    # Lazy import — keeps `python -m bench` workable even if examples/ moved.
    from examples.test_cases import get_case

    try:
        case = get_case(case_id)
    except KeyError as e:
        console.print(f"[red]{e}[/red]")
        return 2

    console.print(Panel.fit(f"[bold]{case.title}[/bold]\n\n{case.prompt}", title=f"Case: {case.id}"))
    console.print(f"[dim]Modes: {', '.join(modes)}[/dim]")

    # One run directory per `bench compare` invocation; all (case × mode)
    # outputs land here together. Create up-front so summary.json always lands
    # somewhere — even if every mode refuses or fails before any per-run JSON
    # is written.
    run_dir = Path("bench/runs") / _stamp()
    run_dir.mkdir(parents=True, exist_ok=True)

    # Single CostGuard shared across all Opus modes in this run, so the cap
    # applies to *cumulative* spend across both opus-single and opus-council.
    guard = CostGuard(ledger_path=run_dir / "cost.json")
    console.print(f"[dim]Budget cap: ${guard.cap_usd:.2f} (BENCH_BUDGET_USD)[/dim]")

    results: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}

    for mode in modes:
        console.print()
        console.print(f"[cyan]● Running {mode}...[/cyan]")
        try:
            if mode == "local-council":
                result = await _run_local_council(case.prompt)
            elif mode == "opus-single":
                result = await _run_opus_single(case.prompt, guard)
            elif mode == "opus-council":
                result = await _run_opus_council(case.prompt, guard)
            else:
                console.print(f"[red]Unknown mode: {mode}[/red]")
                continue

            path = _save_run(run_dir, case.id, mode, result)
            console.print(f"[green]  ✓ saved: {path}[/green]")
            results[mode] = result

        except BudgetExceeded as e:
            # Expected at $0 budget. Don't fail the whole run — record and continue
            # so local-council still produces output even when Opus is gated off.
            console.print(f"[yellow]  ⚠ {mode} refused: {e}[/yellow]")
            errors[mode] = f"BudgetExceeded: {e}"
        except Exception as e:
            console.print(f"[red]  ✗ {mode} failed: {type(e).__name__}: {e}[/red]")
            errors[mode] = f"{type(e).__name__}: {e}"

    # ---- Summary ----
    summary = {
        "case_id": case.id,
        "case_title": case.title,
        "modes_requested": modes,
        "modes_completed": list(results.keys()),
        "modes_failed": errors,
        "budget_cap_usd": guard.cap_usd,
        "spent_usd": guard.spent_usd,
        "timestamp": _stamp(),
    }
    summary_path = run_dir / "summary.json"
    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)

    # Side-by-side comparison table
    if results:
        console.print()
        table = Table(title=f"{case.id} — comparison", show_lines=False)
        table.add_column("Mode", style="cyan")
        table.add_column("Latency", justify="right")
        table.add_column("Output (chars)", justify="right")
        for mode, result in results.items():
            output = result.get("final_output", "")
            table.add_row(
                mode,
                f"{result.get('total_latency_ms', 0) / 1000:.1f}s",
                str(len(output)),
            )
        console.print(table)

    if errors:
        console.print()
        console.print(f"[yellow]Modes refused or failed: {', '.join(errors.keys())}[/yellow]")

    console.print()
    console.print(f"[dim]Run directory: {run_dir}[/dim]")
    console.print(f"[dim]Spent so far: ${guard.spent_usd:.4f} of ${guard.cap_usd:.2f}[/dim]")

    return 0 if results else 1


def main() -> int:
    """Argparse dispatcher for ``python -m bench``."""
    parser = argparse.ArgumentParser(
        prog="bench",
        description="Council vs Opus 4.7 benchmark harness.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_compare = sub.add_parser("compare", help="Run a case through selected modes")
    p_compare.add_argument(
        "--case",
        required=True,
        help="Case id (see `python -m council cases` for the list)",
    )
    p_compare.add_argument(
        "--modes",
        default="all",
        help=f"Comma-separated subset of {ALL_MODES} or 'all' (default)",
    )

    args = parser.parse_args()

    if args.cmd == "compare":
        modes_str = args.modes.strip()
        if modes_str == "all":
            modes = list(ALL_MODES)
        else:
            modes = [m.strip() for m in modes_str.split(",") if m.strip()]
            invalid = [m for m in modes if m not in ALL_MODES]
            if invalid:
                print(f"Invalid mode(s): {invalid}. Allowed: {ALL_MODES}", file=sys.stderr)
                return 2
        return asyncio.run(_compare(args.case, modes))

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
