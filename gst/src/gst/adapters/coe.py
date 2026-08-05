"""Reference adapter -- the originating program's run ledger.

Kept in the kit as a worked example of a real adapter, and because the golden
test reproduces this program's published parameters from it. An external
replication that runs the golden test knows the kit itself is behaving before
trusting it on unfamiliar data.

Two ledger-specific hazards handled here, both of which are general lessons:

  annotation stripping   runs produced under an intervention carry a
                         reader-facing provenance note that NAMES families.
                         Measured naively, the note is counted as the families
                         it discloses, inflating the number it was written to
                         disclose.
  pre vs post output     to characterize the BASE system, measure the writer's
                         own draft, not the post-intervention text. Mixing the
                         two answers neither question.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..record import RunRecord
from ..select import strip_annotation

AS_SHIPPED = "as_shipped"
PRE_INTERVENTION = "pre_intervention"


def from_ledger(directory: str | Path, *, variant: str = PRE_INTERVENTION,
                modes: set[str] | None = None,
                sources: set[str] | None = None,
                require_upstream: bool = True) -> list[RunRecord]:
    """Load ledger JSON files into RunRecords.

    variant=PRE_INTERVENTION measures the writer as it behaves unaided, which
    is what the framework's parameters describe. variant=AS_SHIPPED measures
    whatever the pipeline actually returned.
    """
    out: list[RunRecord] = []
    for path in sorted(Path(directory).glob("*.json")):
        try:
            d = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if modes and d.get("mode") not in modes:
            continue
        if sources and d.get("source") not in sources:
            continue
        ep = d.get("execution_path") or {}
        if ep.get("quarantined"):
            continue                       # never pool a run that failed path assertion
        delib = d.get("deliberation") or {}
        turns = delib.get("turns") or []
        upstream = [str(t.get("output_text") or "") for t in turns]
        if require_upstream and not any(u.strip() for u in upstream):
            continue

        if variant == PRE_INTERVENTION:
            output = d.get("pre_gate_output") or d.get("final_output") or ""
        else:
            output = d.get("final_output") or ""
        output = strip_annotation(str(output))

        syn = delib.get("synthesis") or {}
        msgs = syn.get("input_messages") or []
        writer_prompt = str(msgs[0].get("content") or "") if msgs else ""
        plan = delib.get("plan") or {}
        routes = plan.get("routes") or ep.get("routes") or []

        out.append(RunRecord(
            run_id=path.stem,
            prompt_id=str(d.get("case_id") or ""),
            upstream=[u for u in upstream if u.strip()],
            output=output,
            writer_prompt=writer_prompt,
            routes=[str(r) for r in routes],
            condition=str(d.get("mode") or ""),
            writer_id=str(d.get("model") or ""),
            meta={"source": d.get("source"), "captured_at": d.get("captured_at")},
        ))
    return out
