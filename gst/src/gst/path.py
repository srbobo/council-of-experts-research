"""Execution-path assertion -- what you configured vs. what actually ran.

In the originating program the orchestrator silently substituted a different
writer prompt whenever the planner routed to no components. Thirty-nine runs
measured a condition that never executed, and two published verdicts had to
be withdrawn. Nothing in the outputs looked wrong; the defect was only
visible by reading the orchestrator's source.

Assert the path per run, quarantine violations, and never pool a quarantined
run into an estimate. Quarantined runs are kept and counted -- a silently
dropped run is its own bias.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .record import RunRecord


@dataclass
class PathRecord:
    routes: list[str]
    writer_prompt: str
    quarantined: bool = False
    reason: str = ""


def assert_path(routes: list[str], writer_prompt: str, *,
                require_min_routes: int = 1,
                require_prompt_contains: str | None = None,
                forbid_prompt_contains: str | None = None) -> PathRecord:
    rec = PathRecord(routes=list(routes), writer_prompt=writer_prompt)
    if len(routes) < require_min_routes:
        rec.quarantined = True
        rec.reason = f"routes={len(routes)} < required {require_min_routes}"
    elif require_prompt_contains and require_prompt_contains not in writer_prompt:
        rec.quarantined = True
        rec.reason = f"writer prompt lacks required marker {require_prompt_contains!r}"
    elif forbid_prompt_contains and forbid_prompt_contains in writer_prompt:
        rec.quarantined = True
        rec.reason = f"writer prompt contains forbidden marker {forbid_prompt_contains!r}"
    return rec


@dataclass
class PathAudit:
    clean: list[RunRecord] = field(default_factory=list)
    quarantined: list[tuple[RunRecord, str]] = field(default_factory=list)

    @property
    def rate(self) -> float:
        n = len(self.clean) + len(self.quarantined)
        return len(self.quarantined) / n if n else 0.0

    def summary(self) -> str:
        if not self.quarantined:
            return f"path assertion: {len(self.clean)}/{len(self.clean)} clean"
        reasons: dict[str, int] = {}
        for _, r in self.quarantined:
            reasons[r] = reasons.get(r, 0) + 1
        return (f"path assertion: {len(self.quarantined)} quarantined "
                f"({self.rate:.1%}) -- " + "; ".join(f"{k} x{v}" for k, v in reasons.items()))


def audit_paths(records: list[RunRecord], **kw) -> PathAudit:
    out = PathAudit()
    for rec in records:
        p = assert_path(rec.routes, rec.writer_prompt, **kw)
        if p.quarantined:
            out.quarantined.append((rec, p.reason))
        else:
            out.clean.append(rec)
    return out
