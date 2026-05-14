"""Ollama HTTP client wrapper.

Single point of contact between the orchestrator and Ollama. Swapping
inference backends later (llama.cpp directly, or MLX via LM Studio) means
rewriting just this file — every other module talks only to ``chat()``.

The underlying library is the ``ollama`` Python package (v0.4+), which posts
to ``/api/chat`` on the local Ollama daemon. The daemon URL is read from the
``OLLAMA_HOST`` env var, defaulting to ``http://localhost:11434``.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import ollama  # talks to /api/chat on the local Ollama daemon

from .cabinet import CabinetMember


@dataclass
class ChatResponse:
    """Trimmed response from a single Ollama chat call.

    The orchestrator's audit log captures ``raw`` for replay/debugging while
    the rest of the system uses the normalized fields.
    """

    content: str                                # the model's full response text
    latency_ms: int                             # wall-clock from request to last token
    eval_count: int                             # output tokens generated (Ollama metric)
    prompt_eval_count: int                      # input tokens processed
    raw: dict[str, Any] = field(default_factory=dict)  # full payload for the audit log


def _client() -> ollama.AsyncClient:
    """Construct a fresh AsyncClient. Honors OLLAMA_HOST (default localhost:11434)."""
    # Cheap to construct; httpx pools connections under the hood.
    return ollama.AsyncClient(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))


async def chat(
    member: CabinetMember,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,  # low temp per Q9 — keeps runs comparable across modes
    max_tokens: int = 2048,
    on_token: Callable[[str], None] | None = None,
) -> ChatResponse:
    """Run a single chat completion against an Ollama-served model.

    Parameters
    ----------
    member       : which cabinet member to call (drives the Ollama tag)
    messages     : OpenAI-style chat messages (``[{"role": ..., "content": ...}]``)
    temperature  : sampling temperature; default 0.2 keeps runs comparable
    max_tokens   : hard output cap (Ollama option name: ``num_predict``)
    on_token     : optional per-delta callback for streaming. When provided,
                   the underlying Ollama call switches to ``stream=True`` and
                   each text delta arriving from the model is forwarded to
                   the callback. The function still returns the assembled
                   final ``ChatResponse`` so callers don't need to handle
                   chunk reassembly. When ``None``, behavior is unchanged
                   (single non-streaming request).

    Returns a normalized ``ChatResponse``. The full Ollama payload is in ``.raw``.
    """
    client = _client()
    start = time.monotonic()
    options = {"temperature": temperature, "num_predict": max_tokens}

    # ---- Non-streaming path (existing behavior; default) ----
    if on_token is None:
        response = await client.chat(
            model=member.ollama_tag,
            messages=messages,
            options=options,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        raw: dict[str, Any] = (
            response.model_dump() if hasattr(response, "model_dump") else dict(response)
        )
        return ChatResponse(
            content=raw["message"]["content"],
            latency_ms=elapsed_ms,
            eval_count=int(raw.get("eval_count") or 0),
            prompt_eval_count=int(raw.get("prompt_eval_count") or 0),
            raw=raw,
        )

    # ---- Streaming path: accumulate deltas, forward each one to on_token ----
    # The Ollama SDK returns an async iterator when stream=True. Each chunk is
    # a partial ChatResponse with the new delta in `message.content`. The
    # FINAL chunk carries `done=True` plus the usage metadata (eval_count,
    # prompt_eval_count, etc.) — so we accumulate until then.
    content_parts: list[str] = []
    final_raw: dict[str, Any] = {}
    stream = await client.chat(
        model=member.ollama_tag,
        messages=messages,
        options=options,
        stream=True,
    )
    async for chunk in stream:
        chunk_raw: dict[str, Any] = (
            chunk.model_dump() if hasattr(chunk, "model_dump") else dict(chunk)
        )
        delta = (chunk_raw.get("message") or {}).get("content") or ""
        if delta:
            content_parts.append(delta)
            try:
                # User callback is sync; errors here must not abort the stream.
                on_token(delta)
            except Exception:
                # Swallow — token-level errors shouldn't kill the chat. The
                # full assembled response still comes back via the return.
                pass
        if chunk_raw.get("done"):
            final_raw = chunk_raw

    elapsed_ms = int((time.monotonic() - start) * 1000)
    # Synthesize the final response shape. The last streamed chunk carries
    # the message metadata except for `message.content` (which is the last
    # delta only) — we replace that with the assembled full text.
    final_raw.setdefault("message", {})["content"] = "".join(content_parts)
    return ChatResponse(
        content="".join(content_parts),
        latency_ms=elapsed_ms,
        eval_count=int(final_raw.get("eval_count") or 0),
        prompt_eval_count=int(final_raw.get("prompt_eval_count") or 0),
        raw=final_raw,
    )


async def ensure_available(member: CabinetMember) -> bool:
    """Return True if this cabinet member's model is present in the local Ollama daemon.

    Used by the CLI's pre-flight check so we fail fast with a clear error rather
    than letting the first ``chat()`` call blow up mid-deliberation.
    """
    client = _client()
    response = await client.list()
    raw: dict[str, Any] = (
        response.model_dump() if hasattr(response, "model_dump") else dict(response)
    )

    # Ollama list payload has either "models" key (v0.4+) or root list.
    models = raw.get("models", []) if isinstance(raw, dict) else raw
    available = {m.get("model") or m.get("name") for m in models if isinstance(m, dict)}

    # Ollama may store the model with a `:latest` suffix when no tag was specified
    # at pull time, so accept either form.
    needle = member.ollama_tag
    return needle in available or f"{needle}:latest" in available
