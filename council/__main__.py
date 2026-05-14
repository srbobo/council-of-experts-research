"""CLI entry point for the council.

Subcommands:
  list-models   show cabinet table; verify each model is present in Ollama
  cases         list the test cases defined in examples.test_cases
  deliberate    run the council on a query (--case <id> or --prompt "...")

Run via: ``uv run python -m council <subcommand>`` (or just ``council ...`` once
``uv sync`` has linked the entrypoint).
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys

# Load .env into os.environ before reading any config (OLLAMA_HOST, etc.)
from dotenv import load_dotenv

load_dotenv()

from rich.console import Console      # nice colored CLI output
from rich.panel import Panel
from rich.table import Table

from .cabinet import CABINET, all_industry_seats, LEAD
from .models import ensure_available
from .orchestrator import deliberate, save_audit_log
from .thermal import ThermalGuard

# Avoid importing examples.* at module top-level so `council` works without
# the examples submodule on the path. Imported lazily inside the relevant cmd.

console = Console()


# =============================================================================
# Subcommand: list-models
# =============================================================================

async def cmd_list_models() -> int:
    """Print the cabinet table and verify each model is present in Ollama."""
    table = Table(title="Council of Experts — cabinet", show_lines=False)
    table.add_column("Seat", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Quant", justify="right")
    table.add_column("Mem (GB)", justify="right")
    table.add_column("In Ollama?", justify="center")

    # Lead first, then industry seats — matches deliberation order in audit logs.
    members = [LEAD, *all_industry_seats()]
    all_present = True
    for member in members:
        present = await ensure_available(member)
        if not present:
            all_present = False
        table.add_row(
            member.seat,
            member.name,
            member.quantization,
            f"{member.memory_gb:.1f}",
            "[green]yes[/green]" if present else "[red]missing[/red]",
        )

    console.print(table)
    if not all_present:
        console.print(
            "[red]One or more models are missing from Ollama. "
            "Run the appropriate `ollama pull` commands "
            "(see IMPLEMENTATION_PLAN.md Phase 1.2) and try again.[/red]"
        )
        return 1
    console.print("[green]All cabinet models present.[/green]")
    return 0


# =============================================================================
# Subcommand: cases
# =============================================================================

def cmd_cases() -> int:
    """List the test cases from examples.test_cases."""
    # Lazy import — keeps `list-models` working even if examples/ is missing.
    from examples.test_cases import CASES

    table = Table(title="Test cases", show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title")
    table.add_column("Failure mode", style="dim")
    for case in CASES:
        table.add_row(case.id, case.title, case.failure_mode.value)
    console.print(table)
    return 0


# =============================================================================
# Subcommand: deliberate
# =============================================================================

def _slugify_prompt(prompt: str, max_len: int = 40) -> str:
    """Turn a free-text prompt into a filesystem-safe run id."""
    # Lowercase, replace non-alphanumerics with hyphens, collapse, trim.
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", prompt.lower()).strip("-")
    return (slug[:max_len] or "custom").rstrip("-")


async def cmd_deliberate(case_id: str | None, prompt: str | None) -> int:
    """Run the council on a single query and persist the audit log."""
    # Resolve query text + run id from --case or --prompt.
    if case_id:
        from examples.test_cases import get_case
        try:
            case = get_case(case_id)
        except KeyError as e:
            console.print(f"[red]{e}[/red]")
            return 2
        query = case.prompt
        run_id = case.id
        console.print(Panel.fit(f"[bold]{case.title}[/bold]\n\n{query}", title="Query"))
    elif prompt:
        query = prompt
        run_id = _slugify_prompt(prompt)
        console.print(Panel.fit(query, title="Query"))
    else:
        console.print("[red]must pass either --case <id> or --prompt \"...\"[/red]")
        return 2

    # Live progress callback — fed into the orchestrator's on_phase hook.
    def _on_phase(stage: str, detail: str) -> None:
        # The "dispatch" stage prints indented and dim italic so the per-seat
        # sub-questions visually attach to the plan_done line above them.
        if stage == "dispatch":
            console.print(f"   [dim italic]→ {detail}[/dim italic]")
            return
        # Color other stages distinctly so the user can tell what's happening at a glance.
        styles = {
            "plan": "yellow", "plan_done": "yellow",
            "consult": "cyan",
            "pause": "dim",
            "synthesize": "magenta",
        }
        style = styles.get(stage, "white")
        console.print(f"[{style}]●[/{style}] {detail}")

    thermal = ThermalGuard.from_env()
    result = await deliberate(query, thermal=thermal, on_phase=_on_phase)

    # Print the final output and a small summary.
    console.print(Panel(result.final_output, title="Final synthesis", border_style="green"))
    console.print(
        f"[dim]Total inference latency: {result.total_latency_ms / 1000:.1f}s "
        f"(plan {result.plan_latency_ms}ms, "
        f"{len(result.turns)} agent turn(s), "
        f"synthesis {result.synthesis.latency_ms if result.synthesis else 0}ms)[/dim]"
    )

    # Persist the audit log.
    log_path = save_audit_log(result, run_id=run_id)
    console.print(f"[dim]Audit log: {log_path}[/dim]")
    return 0


# =============================================================================
# Top-level dispatcher
# =============================================================================

def main() -> int:
    """Argparse-based CLI dispatcher. Routes to one of the cmd_* functions."""
    parser = argparse.ArgumentParser(
        prog="council",
        description="Council of Experts — local 4-model deliberation (Phase 1.4).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-models", help="Show cabinet table and verify Ollama presence")
    sub.add_parser("cases", help="List the test cases")

    p_del = sub.add_parser("deliberate", help="Run the council on a query")
    group = p_del.add_mutually_exclusive_group(required=True)
    group.add_argument("--case", help="Test case id (see `council cases`)")
    group.add_argument("--prompt", help="Free-text prompt to deliberate on")

    args = parser.parse_args()

    if args.cmd == "list-models":
        return asyncio.run(cmd_list_models())
    if args.cmd == "cases":
        return cmd_cases()
    if args.cmd == "deliberate":
        return asyncio.run(cmd_deliberate(args.case, args.prompt))

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
