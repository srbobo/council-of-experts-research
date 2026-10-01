"""Model calls that leave an audit trail.

Added 2026-10-01 after the board review. Two gaps it closes:

  * run records before Cell 62 carry no timestamp, model digest, seed or
    prompt hash, so the order of registration and data collection cannot be
    checked from the records themselves;
  * no script ever set the context length. The server's default was 32,768
    tokens for the 20B writer when checked (2026-10-01, and in the server
    logs for July-August), which the prompts fit, but nothing in a record
    shows it. Here the context length is set on every call and the prompt
    token count the server reports is stored.

`chat_logged` returns the text and a metadata dict; `stamp` adds the fields
every run record should carry. Standard library only.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path

OLLAMA = "http://127.0.0.1:11434"
DEFAULT_CTX = 32768          # the server default the earlier cells ran under
_tags: dict[str, str] = {}
_ctx: dict[str, int] = {}


def _post(path: str, body: dict, timeout: int = 1800) -> dict:
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        return json.loads(fh.read())


def model_digest(model: str) -> str | None:
    """Content digest of the local model, so a re-pulled tag can be detected."""
    if not _tags:
        try:
            with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=30) as fh:
                for m in json.loads(fh.read()).get("models", []):
                    _tags[m["name"]] = m.get("digest", "")[:12]
        except Exception:                                      # noqa: BLE001
            return None
    return _tags.get(model) or _tags.get(model + ":latest")


def max_context(model: str) -> int:
    """The model's own maximum context length, from the server."""
    if model not in _ctx:
        try:
            info = _post("/api/show", {"model": model}, timeout=60).get("model_info", {})
            vals = [v for k, v in info.items() if k.endswith(".context_length")]
            _ctx[model] = int(vals[0]) if vals else DEFAULT_CTX
        except Exception:                                      # noqa: BLE001
            _ctx[model] = DEFAULT_CTX
    return _ctx[model]


def context_for(model: str) -> int:
    return min(DEFAULT_CTX, max_context(model))


def seed_for(run_id: str) -> int:
    """A fixed seed per run id: reruns of the same id draw the same sample."""
    return int(hashlib.sha256(run_id.encode()).hexdigest()[:8], 16) % (2 ** 31)


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def chat_logged(model: str, system: str | None, user: str, *, temperature: float,
                max_tokens: int, seed: int | None = None,
                timeout: int = 1800) -> tuple[str | None, dict]:
    """One chat call. Returns (content or None, metadata).

    metadata['ctx_hit'] is True when prompt plus output filled the context
    window, which means the prompt was cut or the output ran into the limit;
    such runs must be set aside and counted, never scored.
    metadata['budget_exhausted'] is True when the model stopped at the
    token limit with nothing in the visible reply (a reasoning model that
    spent its allowance thinking)."""
    msgs = ([{"role": "system", "content": system}] if system else []) + \
        [{"role": "user", "content": user}]
    num_ctx = context_for(model)
    options = {"temperature": temperature, "num_predict": max_tokens, "num_ctx": num_ctx}
    if seed is not None:
        options["seed"] = seed
    meta = {"t_utc": utc_now(), "model": model, "digest": model_digest(model),
            "temperature": temperature, "max_tokens": max_tokens, "seed": seed,
            "num_ctx": num_ctx,
            "prompt_sha256": hashlib.sha256(((system or "") + "\x1e" + user).encode()).hexdigest()[:16],
            "prompt_chars": len(system or "") + len(user)}
    t0 = time.time()
    try:
        d = _post("/api/chat", {"model": model, "messages": msgs, "stream": False,
                                "options": options}, timeout=timeout)
    except Exception as e:                                     # noqa: BLE001
        meta.update({"error": str(e)[:200], "wall_s": round(time.time() - t0, 1)})
        return None, meta
    text = (d.get("message") or {}).get("content")
    pe, ev = d.get("prompt_eval_count"), d.get("eval_count")
    meta.update({"prompt_tokens": pe, "output_tokens": ev,
                 "done_reason": d.get("done_reason"),
                 "wall_s": round(time.time() - t0, 1),
                 "ctx_hit": bool(pe is not None and ev is not None and pe + ev >= num_ctx - 8),
                 "budget_exhausted": bool(d.get("done_reason") == "length"
                                          and not (text or "").strip())})
    return text, meta


def registration_for(cell: str, root: Path) -> str:
    """The commit that holds a cell's registration, from
    docs/REGISTRATION_COMMITS.json (written right after the registration is
    committed). Falls back to a pointer to the runbook entry."""
    try:
        return json.loads((Path(root) / "docs" / "REGISTRATION_COMMITS.json").read_text())[str(cell)]
    except Exception:                                          # noqa: BLE001
        return f"see RUNBOOK 'CELL {cell} PRE-REGISTRATION'"


def git_head(root: Path) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=20).stdout.strip() or None
    except Exception:                                          # noqa: BLE001
        return None


def file_sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def stamp(row: dict, meta: dict | None, *, root: Path, script: Path,
          registration: str) -> dict:
    """Add the audit fields to a run record. `registration` is the commit
    that holds the cell's registration; `head` is the commit checked out when
    the run was made; `script_sha` shows the runner was not edited mid-cell."""
    out = dict(row)
    out["audit"] = {"registration": registration, "head": git_head(root),
                    "script_sha": file_sha(script), **(meta or {"t_utc": utc_now()})}
    return out


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()


def read_jsonl(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
