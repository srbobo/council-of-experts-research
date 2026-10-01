"""Run the registered experiments back to back, unattended (Cells 62-67).

Registered in RUNBOOK_PAPER_HARDENING.md, 2026-10-01. Each step runs one or
more resumable stages of a cell's runner. When a step ends, the unedited
output of its scoring stage is appended to the runbook, the site is rebuilt
locally and the touched files are committed locally (train/queue_record.py).
Nothing is pushed and Netlify stays paused.

    .venv/bin/python train/run_queue.py start      run every step not yet done
    .venv/bin/python train/run_queue.py status     show where the queue is
    .venv/bin/python train/run_queue.py only STEP  run one step

Launch detached so it survives the terminal:

    nohup caffeinate -ims .venv/bin/python train/run_queue.py start >> bench/queue/queue.out 2>&1 &

Stop it with:  kill $(cat bench/queue/queue.pid)   (every stage resumes where it stopped)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
Q = ROOT / "bench" / "queue"
PY = sys.executable
OLLAMA = "http://127.0.0.1:11434"
ATTEMPTS = 3

# (step, [stage commands], scoring-stage command whose output is recorded, or None)
STEPS = [
    ("c62-judges", [["train/run_cell62_instrument.py", "judge"]], None),
    ("c63-primary", [["train/run_cell63_checkable.py", "runs", "gpt-oss:20b"],
                     ["train/run_cell63_checkable.py", "runs", "gpt-oss:20b"]],      # second pass fills any gaps
     ["train/run_cell63_checkable.py", "measure"]),
    ("c66-conveyed", [["train/run_cell66_conveyed.py", "shortlist"], ["train/run_cell66_conveyed.py", "judge"],
                      ["train/run_cell66_conveyed.py", "sample"], ["train/run_cell66_conveyed.py", "misscheck"]],
     ["train/run_cell66_conveyed.py", "measure"]),
    ("c64-readers", [["train/run_cell64_readers.py", "runs"]], ["train/run_cell64_readers.py", "measure"]),
    ("c65-judges", [["train/run_cell65_judges.py", "judge"]], ["train/run_cell65_judges.py", "measure"]),
    ("c63-repeat", [["train/run_cell63_checkable.py", "runs", "phi4:14b"],
                    ["train/run_cell63_checkable.py", "runs", "phi4:14b"],
                    ["train/run_cell63_checkable.py", "runs", "qwen3-vl:30b-a3b-instruct"],
                    ["train/run_cell63_checkable.py", "runs", "qwen3-vl:30b-a3b-instruct"]],
     ["train/run_cell63_checkable.py", "measure"]),
    ("c67-livechain", [["train/run_cell67_livechain.py", "runs"], ["train/run_cell67_livechain.py", "runs"]],
     ["train/run_cell67_livechain.py", "measure"]),
]
MODELS = ["gpt-oss:20b", "qwen2.5:7b-instruct", "phi4:14b", "qwen3-vl:30b-a3b-instruct",
          "llama3:8b-instruct-q4_K_M", "mistral:7b-instruct-v0.3-q4_K_M", "nomic-embed-text"]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def event(text: str) -> None:
    Q.mkdir(parents=True, exist_ok=True)
    with (Q / "events.log").open("a", encoding="utf-8") as fh:
        fh.write(f"{now()} {text}\n")
    print(f"{now()} {text}", flush=True)


def load_status() -> dict:
    p = Q / "status.json"
    return json.loads(p.read_text()) if p.exists() else {"steps": {}}


def save_status(st: dict) -> None:
    (Q / "status.json").write_text(json.dumps(st, indent=1))


def server_ready(wait: bool = True) -> bool:
    """True when the model server answers and holds every model the queue needs."""
    for _ in range(30 if wait else 1):
        try:
            with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=20) as fh:
                have = {m["name"] for m in json.loads(fh.read()).get("models", [])}
            missing = [m for m in MODELS if m not in have and m + ":latest" not in have]
            if not missing:
                return True
            event(f"MODELS MISSING {missing}")
            return False
        except Exception as e:                                  # noqa: BLE001
            event(f"model server not answering ({str(e)[:80]}); waiting")
            time.sleep(60)
    return False


def gate_c67() -> str | None:
    """Cell 67 runs only if Cell 63's clean-layout check passed for the editor model."""
    p = ROOT / "bench" / "analysis" / "cell63" / "measured.json"
    try:
        ok = json.loads(p.read_text())["gpt-oss:20b"]["P63.0"]["pass"]
    except Exception:                                           # noqa: BLE001
        return "Cell 63 has no scored result for the editor model"
    return None if ok else "Cell 63's clean-layout check (P63.0) did not pass for the editor model"


def run_stage(step: str, cmd: list[str], log: Path) -> int:
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"\n===== {now()} $ {' '.join(cmd)}\n")
        fh.flush()
        return subprocess.run([PY, *cmd], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT).returncode


def run_step(step: str, stages: list[list[str]], scoring: list[str] | None, st: dict) -> str:
    from train import queue_record
    (Q / "logs").mkdir(parents=True, exist_ok=True)
    log = Q / "logs" / f"{step}.log"
    rec = st["steps"].setdefault(step, {})
    rec.update({"state": "running", "started_utc": rec.get("started_utc") or now()})
    save_status(st)
    event(f"STEP START {step}")
    info = {"attempts": 0}
    if step == "c67-livechain":
        reason = gate_c67()
        if reason:
            info.update({"reason": reason, "finished_utc": now()})
            commit = _record(queue_record, step, "skipped", "", info)
            rec.update({"state": "skipped", "finished_utc": info["finished_utc"], "reason": reason, "commit": commit})
            save_status(st)
            event(f"STEP SKIPPED {step} ({reason}) commit {commit}")
            return "skipped"
    state = "done"
    for cmd in stages:
        code = 1
        for attempt in range(1, ATTEMPTS + 1):
            info["attempts"] = max(info["attempts"], attempt)
            if not server_ready():
                break
            code = run_stage(step, cmd, log)
            if code == 0:
                break
            event(f"stage failed ({step}: {' '.join(cmd)}), exit {code}, attempt {attempt} of {ATTEMPTS}")
            time.sleep(120)
        if code != 0:
            state = "failed"
            break
    output = ""
    if state == "done" and scoring:
        r = subprocess.run([PY, *scoring], cwd=ROOT, capture_output=True, text=True)
        output = r.stdout + (("\n[stderr]\n" + r.stderr[-1500:]) if r.returncode != 0 else "")
        (Q / "logs" / f"{step}.measure.txt").write_text(output, encoding="utf-8")
        if r.returncode != 0:
            state = "failed"
    elif state == "done":
        output = "\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-12:])
    if state == "failed" and not output:
        output = "\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-40:])
    info["finished_utc"] = now()
    commit = _record(queue_record, step, state, output, info)
    rec.update({"state": state, "finished_utc": info["finished_utc"], "attempts": info["attempts"], "commit": commit})
    save_status(st)
    event(f"STEP {'DONE' if state == 'done' else 'FAILED'} {step} commit {commit}")
    return state


def _record(queue_record, step: str, state: str, output: str, info: dict) -> str | None:
    try:
        return queue_record.record(step, state, output, info)
    except Exception as e:                                      # noqa: BLE001
        event(f"RECORD FAILED {step}: {type(e).__name__}: {str(e)[:200]}")
        return None


def preflight() -> None:
    reg = ROOT / "docs" / "REGISTRATION_COMMITS.json"
    if not reg.exists():
        raise SystemExit("docs/REGISTRATION_COMMITS.json is missing: commit the registrations first.")
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "train", "gst/src", "docs/CELL63_ITEMS.json",
                            "bench/labels/cell62_sentences/task.json", "bench/analysis/cell66/pairs.json"],
                           cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if dirty:
        raise SystemExit("Runners or frozen inputs differ from the committed versions:\n" + dirty)
    if not server_ready(wait=False):
        raise SystemExit("The model server is not ready or a model is missing.")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    st = load_status()
    if cmd == "status":
        for step, _, _ in STEPS:
            r = st["steps"].get(step, {})
            print(f"  {step:<14} {r.get('state', 'waiting'):<8} started {r.get('started_utc', '-'):<21} "
                  f"finished {r.get('finished_utc', '-'):<21} commit {r.get('commit', '-')}")
        pid = Q / "queue.pid"
        if pid.exists():
            alive = subprocess.run(["kill", "-0", pid.read_text().strip()], capture_output=True).returncode == 0
            print(f"  queue process {pid.read_text().strip()}: {'running' if alive else 'not running'}")
        return
    Q.mkdir(parents=True, exist_ok=True)
    pidfile = Q / "queue.pid"
    if pidfile.exists() and subprocess.run(["kill", "-0", pidfile.read_text().strip()], capture_output=True).returncode == 0:
        raise SystemExit(f"A queue is already running (pid {pidfile.read_text().strip()}).")
    preflight()
    pidfile.write_text(str(os.getpid()))
    try:
        todo = [s for s in STEPS if (cmd == "start" or s[0] == sys.argv[2])]
        st.setdefault("queue_started_utc", now())
        save_status(st)
        event(f"QUEUE START pid {os.getpid()} steps {[s[0] for s in todo]}")
        for step, stages, scoring in todo:
            if st["steps"].get(step, {}).get("state") in ("done", "skipped"):
                continue
            run_step(step, stages, scoring, st)
        event("QUEUE COMPLETE")
    finally:
        pidfile.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
