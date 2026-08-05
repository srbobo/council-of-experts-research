"""RunRecord — the contract between your architecture and this kit.

Everything in `gst.measure` consumes `list[RunRecord]`. Adapting a new
architecture means writing a function that produces these; nothing else in
the kit needs to know how your pipeline works.

The fields are the minimum needed to estimate the framework's parameters.
Two of them exist because their absence silently invalidated published
numbers in the originating program:

  writer_prompt  the system prompt the writing model ACTUALLY received.
                 An orchestrator that substitutes a different prompt on some
                 code path (ours did, on empty routes) produces runs that
                 measure a condition that never executed.
  prompt_id      groups repeated samples of the SAME task. Required for the
                 best-of-n estimator, which is meaningless if samples of
                 different tasks are pooled as if they were redraws.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunRecord:
    """One execution of a lead-council pipeline."""

    run_id: str
    prompt_id: str
    upstream: list[str]
    output: str
    writer_prompt: str = ""
    routes: list[str] = field(default_factory=list)
    condition: str = ""
    writer_id: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def upstream_text(self) -> str:
        return "\n\n".join(t for t in self.upstream if t)


# Problems that make a record unusable vs. merely limited.
FATAL = "fatal"
WARN = "warn"


def validate(rec: RunRecord, *, min_output_chars: int = 500,
             require_writer_prompt: bool = False) -> list[tuple[str, str]]:
    """Return [(severity, message)]. Empty means clean.

    Callers should drop FATAL records and report WARN counts alongside any
    estimate. Silently pooling degenerate records is how a 208-character
    fragment produced an 18x distortion in the originating program.
    """
    out: list[tuple[str, str]] = []
    if not rec.output or not rec.output.strip():
        out.append((FATAL, "empty output"))
    elif len(rec.output) < min_output_chars:
        out.append((FATAL, f"output {len(rec.output)} chars < floor {min_output_chars}"))
    if not any(t and t.strip() for t in rec.upstream):
        out.append((FATAL, "no upstream text captured"))
    if require_writer_prompt and not rec.writer_prompt.strip():
        out.append((FATAL, "writer_prompt not captured (path assertion impossible)"))
    if not rec.prompt_id:
        out.append((WARN, "no prompt_id: best-of-n estimation unavailable"))
    return out


def partition(records: list[RunRecord], **kw) -> tuple[list[RunRecord], dict[str, int]]:
    """Split into (usable, dropped-reason-counts). Never drops silently."""
    keep: list[RunRecord] = []
    dropped: dict[str, int] = {}
    for r in records:
        problems = validate(r, **kw)
        fatal = [m for sev, m in problems if sev == FATAL]
        if fatal:
            key = fatal[0].split("(")[0].split(":")[0].strip()
            dropped[key] = dropped.get(key, 0) + 1
        else:
            keep.append(r)
    return keep, dropped
