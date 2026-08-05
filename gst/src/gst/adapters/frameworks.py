"""Adapters for common multi-agent frameworks.

These are shape helpers, not integrations: each takes whatever object the
framework hands you at the end of a run and pulls out the writer's input and
output. They are deliberately tolerant, because every one of these frameworks
lets users restructure state freely -- if a helper returns empty upstream,
that is a signal to write six lines by hand rather than to fight the helper.

The measurement does not care which framework produced the run. It cares that
`upstream` is exactly what the final writing model read.
"""
from __future__ import annotations

from typing import Any

from ..record import RunRecord


def from_moa(layers: list[list[str]], final: str, *, prompt_id: str,
             run_id: str = "", writer_prompt: str = "",
             writer_id: str = "") -> RunRecord:
    """Mixture-of-Agents: proposers arranged in layers, one aggregator.

    Pass the LAST proposer layer as the upstream, not every layer: only the
    final layer's text reaches the aggregator, and crediting a property to a
    layer the aggregator never saw understates invention.
    """
    upstream = list(layers[-1]) if layers else []
    return RunRecord(run_id=run_id or prompt_id, prompt_id=prompt_id,
                     upstream=[t for t in upstream if t], output=final,
                     writer_prompt=writer_prompt, condition="moa",
                     writer_id=writer_id,
                     routes=[f"proposer_{i}" for i in range(len(upstream))])


def from_langgraph(state: Any, *, upstream_key: str = "specialist_outputs",
                   output_key: str = "final", prompt_id_key: str = "task_id",
                   run_id: str = "") -> RunRecord:
    """LangGraph / any state-dict graph.

    Reads a list of upstream strings and a final string from the terminal
    state. If your graph keeps messages rather than strings, pass a list of
    `msg.content` yourself instead of relying on this.
    """
    get = (lambda k: state.get(k)) if isinstance(state, dict) else (
        lambda k: getattr(state, k, None))
    up = get(upstream_key) or []
    if isinstance(up, str):
        up = [up]
    up = [t if isinstance(t, str) else getattr(t, "content", str(t)) for t in up]
    pid = str(get(prompt_id_key) or "")
    return RunRecord(run_id=run_id or pid, prompt_id=pid,
                     upstream=[t for t in up if t], output=str(get(output_key) or ""),
                     condition="langgraph",
                     routes=[f"node_{i}" for i in range(len(up))])


def from_autogen(messages: list[dict], *, writer_name: str,
                 prompt_id: str, run_id: str = "") -> RunRecord:
    """AutoGen-style group chat: a message list with speaker names.

    Upstream is every non-writer message preceding the writer's LAST message;
    output is that message. Messages after it are excluded -- they were not
    available to the writer and including them would credit the writer with
    sources it could not have used.
    """
    idx = max((i for i, m in enumerate(messages)
               if m.get("name") == writer_name or m.get("role") == writer_name),
              default=-1)
    if idx < 0:
        return RunRecord(run_id=run_id or prompt_id, prompt_id=prompt_id,
                         upstream=[], output="", condition="autogen")
    up = [str(m.get("content") or "") for m in messages[:idx]
          if (m.get("name") or m.get("role")) != writer_name]
    return RunRecord(run_id=run_id or prompt_id, prompt_id=prompt_id,
                     upstream=[t for t in up if t],
                     output=str(messages[idx].get("content") or ""),
                     condition="autogen",
                     routes=[str(m.get("name") or m.get("role") or "") for m in messages[:idx]])


def from_rag(chunks: list[str], answer: str, *, prompt_id: str,
             run_id: str = "", writer_prompt: str = "") -> RunRecord:
    """Retrieval-augmented summarization: retrieved chunks are the upstream.

    The framework applies unchanged with a different property class -- run it
    with `gst.instruments.SOURCE_ATTRIBUTION` to ask whether attribution
    survives the writing step, rather than whether hedging does.
    """
    return RunRecord(run_id=run_id or prompt_id, prompt_id=prompt_id,
                     upstream=[c for c in chunks if c], output=answer,
                     writer_prompt=writer_prompt, condition="rag",
                     routes=[f"chunk_{i}" for i in range(len(chunks))])
