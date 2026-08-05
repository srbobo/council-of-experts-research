"""Adapters -- turn your architecture's logs into RunRecords.

Writing one is the entire integration cost of this kit. The contract is
small on purpose, but two fields are easy to get wrong in ways that quietly
invalidate the measurements:

  upstream       must be the VERBATIM text the writer received, not a summary,
                 not a re-serialization, and not the components' internal
                 reasoning if that never reached the writer. The provenance
                 decomposition asks whether a property in the output has a
                 source upstream; feeding it text the writer never saw
                 fabricates sources and understates invention.
  prompt_id      must group repeated samples of the SAME task. If every run
                 gets a unique id, the empirical best-of-n estimator silently
                 has nothing to work with and the kit falls back to the
                 optimistic independence curve.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from ..record import RunRecord

__all__ = ["from_dicts", "from_jsonl", "from_callable", "FieldMap"]


class FieldMap:
    """Declarative mapping from your row shape to RunRecord.

    Each value is either a dotted path into the row ("state.messages") or a
    callable taking the row. Paths traverse dicts, lists (by integer index),
    and object attributes.
    """

    def __init__(self, *, upstream: str | Callable, output: str | Callable,
                 run_id: str | Callable | None = None,
                 prompt_id: str | Callable | None = None,
                 writer_prompt: str | Callable | None = None,
                 routes: str | Callable | None = None,
                 condition: str | Callable | None = None,
                 writer_id: str | Callable | None = None):
        self.spec = {"upstream": upstream, "output": output, "run_id": run_id,
                     "prompt_id": prompt_id, "writer_prompt": writer_prompt,
                     "routes": routes, "condition": condition,
                     "writer_id": writer_id}

    def apply(self, row: Any, index: int) -> RunRecord:
        g = {k: (_resolve(row, v) if v is not None else None)
             for k, v in self.spec.items()}
        up = g["upstream"]
        if isinstance(up, str):
            up = [up]
        return RunRecord(
            run_id=str(g["run_id"] or index),
            prompt_id=str(g["prompt_id"] or ""),
            upstream=[str(x) for x in (up or []) if x],
            output=str(g["output"] or ""),
            writer_prompt=str(g["writer_prompt"] or ""),
            routes=list(g["routes"] or []),
            condition=str(g["condition"] or ""),
            writer_id=str(g["writer_id"] or ""),
        )


def _resolve(row: Any, spec: str | Callable) -> Any:
    if callable(spec):
        return spec(row)
    cur = row
    for part in spec.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, (list, tuple)) and part.lstrip("-").isdigit():
            i = int(part)
            cur = cur[i] if -len(cur) <= i < len(cur) else None
        else:
            cur = getattr(cur, part, None)
    return cur


def from_dicts(rows: Iterable[Any], fmap: FieldMap) -> list[RunRecord]:
    return [fmap.apply(r, i) for i, r in enumerate(rows)]


def from_jsonl(path: str | Path, fmap: FieldMap) -> list[RunRecord]:
    rows = []
    with Path(path).open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return from_dicts(rows, fmap)


def from_callable(fn: Callable[[Any], RunRecord],
                  rows: Iterable[Any]) -> list[RunRecord]:
    return [fn(r) for r in rows]
