"""Blind labelling at the terminal, for the one human in the loop.

Built 2026-10-01 for the single-operator plan (docs/BOARD_REVIEW_2026-10-01.md,
Addendum A). The person labelling sees one item at a time in a fixed random
order and nothing else: no arm, no model, no case, no judge label. The answer
key lives in a separate file this tool never opens.

A labelling task is a folder that a cell's `sample` stage writes:

    task.json     {"task", "kind", "instructions", "choices"|"definitions",
                   "retest_gap_days", "items": [{"id", "text", ...}], "practice": [...]}
    key.json      what each item is. NOT read here. Do not open it while labelling.

and this tool adds:

    labels_pass1.jsonl, labels_pass2.jsonl     one line per answer (later lines
                                               for the same id replace earlier ones)
    labels_passN.done                          completion time and file hash

Kinds of task:
    sentence_constructs   switch each listed property on or off for one sentence
    single_choice         pick one of a few answers (for example: fully / partly / not)

Run:
    .venv/bin/python train/label_blind.py bench/labels/cell62_sentences
    .venv/bin/python train/label_blind.py bench/labels/cell62_sentences --pass 2
    .venv/bin/python train/label_blind.py bench/labels/cell62_sentences --practice
    .venv/bin/python train/label_blind.py bench/labels/cell62_sentences --status

Keys: digits switch a property (or pick an answer), Enter saves and moves on,
b goes back one item, q saves and quits. You can stop at any time and resume.
When a pass is finished, commit the labels file before any scoring is run.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import shutil
import sys
import textwrap
import time
from pathlib import Path

KINDS = ("sentence_constructs", "single_choice")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_task(folder: Path) -> dict:
    task = json.loads((folder / "task.json").read_text(encoding="utf-8"))
    if task.get("kind") not in KINDS:
        raise SystemExit(f"task.json: unknown kind {task.get('kind')!r}")
    ids = [it["id"] for it in task["items"]]
    if len(ids) != len(set(ids)):
        raise SystemExit("task.json: duplicate item ids")
    return task


def order_for(task: dict, pass_no: int) -> list[int]:
    """A fixed shuffle per task and pass, so stopping and resuming keeps the
    same order and the two passes use different orders."""
    idx = list(range(len(task["items"])))
    seed = int(hashlib.sha256(f"{task['task']}|pass{pass_no}".encode()).hexdigest()[:8], 16)
    random.Random(seed).shuffle(idx)
    return idx


def labels_path(folder: Path, pass_no: int) -> Path:
    return folder / f"labels_pass{pass_no}.jsonl"


def read_labels(path: Path) -> dict[str, dict]:
    """Latest answer per item id."""
    out: dict[str, dict] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if "id" in row:
                    out[row["id"]] = row
    return out


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def done_info(folder: Path, pass_no: int) -> dict | None:
    p = folder / f"labels_pass{pass_no}.done"
    return json.loads(p.read_text()) if p.exists() else None


# ------------------------------------------------------------------ keyboard

class Keys:
    """Single keypresses from a terminal; whole lines when input is piped
    (used by the self-test and by anyone who prefers typing an answer and
    pressing Enter)."""

    def __init__(self) -> None:
        self.tty = sys.stdin.isatty()

    def get(self) -> str:
        if not self.tty:
            line = sys.stdin.readline()
            if line == "":
                return "q"
            return line.strip() or "\n"
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        if ch in ("\r", "\n"):
            return "\n"
        if ch == "\x03":            # ctrl-c
            return "q"
        return ch


def clear() -> None:
    if sys.stdout.isatty():
        os.system("clear")
    else:
        print("\n" + "-" * 60)


def wrap(text: str, indent: str = "  ") -> str:
    width = min(100, shutil.get_terminal_size((100, 30)).columns - 4)
    out = []
    for para in text.split("\n"):
        out.append(textwrap.fill(para, width=width, initial_indent=indent,
                                 subsequent_indent=indent) if para.strip() else "")
    return "\n".join(out)


# ------------------------------------------------------------------ screens

def show_item(task: dict, item: dict, pos: int, total: int, pass_no: int,
              state: dict, note: str = "") -> None:
    clear()
    print(f"[ {pos + 1} / {total} ]   pass {pass_no}        b = back   q = save and quit")
    print()
    for label, key in (("", "text"), ("Passages from the answer:", "passages")):
        if key in item and item[key]:
            if label:
                print("  " + label)
            val = item[key]
            if isinstance(val, list):
                for n, p in enumerate(val, 1):
                    print(wrap(f"({n}) {p}", "    "))
                    print()
            else:
                print(wrap(val))
                print()
    if task["kind"] == "sentence_constructs":
        print("  " + task["instructions"])
        print()
        for n, (name, definition) in enumerate(task["definitions"].items(), 1):
            mark = "x" if state.get(name) else " "
            print(f"    [{mark}] {n}  {definition}")
        print()
        print("  Enter = save and go on (with nothing switched on, that records 'none')")
    else:
        print("  " + task["instructions"])
        print()
        for n, (name, text) in enumerate(task["choices"].items(), 1):
            mark = ">" if state.get("choice") == name else " "
            print(f"   {mark} {n}  {text}")
        print()
        print("  Press a number to answer; Enter confirms and goes on")
    if note:
        print()
        print("  " + note)


def blank_state(task: dict, prev: dict | None) -> dict:
    if prev is not None:
        return dict(prev["label"])
    if task["kind"] == "sentence_constructs":
        return {name: False for name in task["definitions"]}
    return {"choice": None}


def apply_key(task: dict, state: dict, key: str) -> str:
    """Update `state` for one keypress. Returns 'stay', 'save', 'back' or 'quit'."""
    if key == "q":
        return "quit"
    if key == "b":
        return "back"
    names = list(task["definitions"] if task["kind"] == "sentence_constructs" else task["choices"])
    if key == "\n":
        if task["kind"] == "single_choice" and state.get("choice") is None:
            return "stay"
        return "save"
    if task["kind"] == "sentence_constructs" and key == "0":
        for n in names:
            state[n] = False
        return "stay"
    if key.isdigit() and 1 <= int(key) <= len(names):
        name = names[int(key) - 1]
        if task["kind"] == "sentence_constructs":
            state[name] = not state[name]
        else:
            state["choice"] = name
        return "stay"
    return "stay"


# ------------------------------------------------------------------ passes

def run_pass(folder: Path, task: dict, pass_no: int, override_gap: bool) -> None:
    path = labels_path(folder, pass_no)
    if done_info(folder, pass_no):
        print(f"Pass {pass_no} is already finished ({path.name}). Nothing to do.")
        return
    if pass_no > 1:
        prev = done_info(folder, pass_no - 1)
        if not prev:
            raise SystemExit(f"Finish pass {pass_no - 1} first.")
        gap = task.get("retest_gap_days", 7)
        age = (dt.datetime.now(dt.timezone.utc)
               - dt.datetime.strptime(prev["finished_utc"], "%Y-%m-%dT%H:%M:%SZ")
               .replace(tzinfo=dt.timezone.utc)).total_seconds() / 86400
        if age < gap and not override_gap:
            raise SystemExit(f"Pass {pass_no - 1} finished {age:.1f} days ago. The plan asks for "
                             f"{gap} days between passes so the first answers are not fresh in "
                             f"mind. Come back later, or add --override-gap (it is recorded).")
        if age < gap:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"note": "gap overridden", "days_since_previous": round(age, 2),
                                     "t_utc": utc_now()}) + "\n")
    order = order_for(task, pass_no)
    items = task["items"]
    got = read_labels(path)
    pos = next((k for k, i in enumerate(order) if items[i]["id"] not in got), len(order))
    keys = Keys()
    if pos == 0 and not got:
        clear()
        print(wrap(task.get("intro", task["instructions"])))
        print()
        print("  Press Enter to start.")
        keys.get()
    while pos < len(order):
        item = items[order[pos]]
        state = blank_state(task, got.get(item["id"]))
        t0 = time.time()
        note = ""
        while True:
            show_item(task, item, pos, len(order), pass_no, state, note)
            action = apply_key(task, state, keys.get())
            if action == "stay":
                note = "" if task["kind"] == "sentence_constructs" or state.get("choice") else \
                    "Pick an answer first."
                continue
            break
        if action == "quit":
            print(f"\nSaved. {len(got)} of {len(order)} labelled. Run the same command to resume.")
            return
        if action == "back":
            pos = max(0, pos - 1)
            continue
        row = {"id": item["id"], "label": state, "pass": pass_no, "t_utc": utc_now(),
               "seconds": round(time.time() - t0, 1)}
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        got[item["id"]] = row
        pos += 1
    missing = [it["id"] for it in items if it["id"] not in got]
    if missing:
        print(f"{len(missing)} items still unlabelled; run again to finish.")
        return
    info = {"task": task["task"], "pass": pass_no, "n": len(items), "finished_utc": utc_now(),
            "sha256": sha256_of(path)}
    (folder / f"labels_pass{pass_no}.done").write_text(json.dumps(info, indent=1))
    clear()
    print(f"Pass {pass_no} finished: {len(items)} items.")
    print(f"File: {path}")
    print(f"sha256: {info['sha256']}")
    print()
    print("Commit the labels before any scoring is run:")
    print(f"  git add {folder}/labels_pass{pass_no}.jsonl {folder}/labels_pass{pass_no}.done")
    print(f"  git commit -m \"{task['task']}: blind labels, pass {pass_no}\"")


def run_practice(task: dict) -> None:
    practice = task.get("practice") or []
    if not practice:
        print("This task has no practice items.")
        return
    keys = Keys()
    for pos, item in enumerate(practice):
        state = blank_state(task, None)
        while True:
            show_item(task, item, pos, len(practice), 0, state, "PRACTICE. Nothing is saved.")
            action = apply_key(task, state, keys.get())
            if action != "stay":
                break
        if action == "quit":
            return
        if action == "back":
            continue
        print()
        print(wrap("Intended answer: " + item.get("intended", "(none given)")))
        print("\n  Press Enter for the next one.")
        keys.get()


def status(folder: Path, task: dict) -> None:
    print(f"task: {task['task']}   kind: {task['kind']}   items: {len(task['items'])}")
    for n in (1, 2):
        got = read_labels(labels_path(folder, n))
        d = done_info(folder, n)
        print(f"  pass {n}: {len(got)} labelled" + (f", finished {d['finished_utc']}" if d else ""))


def main() -> None:
    ap = argparse.ArgumentParser(description="Blind labelling at the terminal.")
    ap.add_argument("folder", type=Path)
    ap.add_argument("--pass", dest="pass_no", type=int, default=1, choices=(1, 2))
    ap.add_argument("--practice", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--override-gap", action="store_true")
    a = ap.parse_args()
    task = load_task(a.folder)
    if a.status:
        status(a.folder, task)
    elif a.practice:
        run_practice(task)
    else:
        run_pass(a.folder, task, a.pass_no, a.override_gap)


if __name__ == "__main__":
    main()
