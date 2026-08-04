"""Execution-path assertion — declared configuration vs what actually ran.

Mandated by the zero-route incident: the orchestrator silently substituted a
different system prompt when the planner routed to no seats, and 39 runs
measuring a prompt that never executed contaminated two published verdicts.
"""
from dataclasses import dataclass


@dataclass
class PathRecord:
    routes: list[str]
    writer_prompt: str          # verbatim system prompt actually used
    quarantined: bool = False
    reason: str = ""


def assert_path(routes: list[str], writer_prompt: str, *,
                require_min_routes: int = 1,
                require_prompt_contains: str | None = None) -> PathRecord:
    rec = PathRecord(routes=list(routes), writer_prompt=writer_prompt)
    if len(routes) < require_min_routes:
        rec.quarantined = True
        rec.reason = f"routes={len(routes)} < required {require_min_routes}"
    elif require_prompt_contains and require_prompt_contains not in writer_prompt:
        rec.quarantined = True
        rec.reason = f"writer prompt lacks required marker {require_prompt_contains!r}"
    return rec
