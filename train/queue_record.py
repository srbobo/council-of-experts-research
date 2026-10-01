"""What the run queue writes down when a step finishes.

The queue (train/run_queue.py) runs the registered experiments unattended.
When a step ends, this module:

  1. appends an entry to the runbook holding the UNEDITED output of the
     step's registered scoring stage (verdict words come from rules fixed in
     the registration; no interpretation is added here);
  2. fills the plain-language layer for that entry from fixed templates
     (held up / did not hold up / too close to call, by the rule written
     down in advance);
  3. rebuilds the site (site_v3/ and the explorer page) from the runbook;
  4. commits exactly the files it touched, locally.

It never pushes and never touches netlify.toml, so nothing is deployed. The
analyst's reading of each result is a separate, later runbook entry.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
RUNBOOK = ROOT / "RUNBOOK_PAPER_HARDENING.md"
PLAIN = ROOT / "docs" / "ledger_explorer" / "plain"
BATCH = PLAIN / "batch_M.json"
Q = ROOT / "bench" / "queue"
PY = sys.executable
TRAILER = "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
VERDICT_RE = re.compile(r"\b(P6\d\.\d):?\s+(NOT EVALUABLE|SUPPORTED|FALSIFIED|REVERSED|PASSES|FAILS|MIXED)")
WORD_TO_OUTCOME = {"SUPPORTED": "held", "PASSES": "held", "FALSIFIED": "failed", "FAILS": "failed",
                   "REVERSED": "reversed", "NOT EVALUABLE": "unclear", "MIXED": "partly"}
NOTE = {
    "held": "Held up, by the rule written down in advance. A fuller account follows.",
    "failed": "Did not hold up, by the rule written down in advance. A fuller account follows.",
    "reversed": "The opposite happened, by the rule written down in advance. A fuller account follows.",
    "unclear": "Too close to call, by the rule written down in advance. A fuller account follows.",
    "partly": "Partly held up, by the rule written down in advance. A fuller account follows.",
    "not-graded": "Reported without a pass/fail test. The figures are in the result entry below.",
}

# step -> what to record. `reported` are expectation ids that carry no pass/fail rule.
STEPS = {
    "c62-judges": {
        "cell": "62", "kind": "note",
        "heading": "CELL 62 RUN RECORD ({date}) — the six judges have labelled the 404 sentences; scoring waits for the person's labels",
        "label": "Note", "title": "The six AI judges have labeled the sentences",
        "summary": ("The six AI judges finished labeling the 404 sentences on {long}. Nothing is scored until the author's "
                    "blind labels are finished and saved. The second round of labels can start a week after the first."),
        "size": "AI judging done, the person's labels pending",
        "found": ("The six AI judges finished labeling the 404 sentences on {long}. Scoring has not started. It waits for "
                  "the author's blind labels, two rounds a week apart, and the first round must be saved before any "
                  "comparison is computed. The sentences were drawn by a fixed rule from sentences the two original "
                  "judges had already labeled in Cells 30, 31, 41 and 46."),
        "paths": ["bench/analysis/cell62", "bench/runs/cell62_judge_calls.jsonl"],
    },
    "c63-primary": {
        "cell": "63", "kind": "verdict", "reported": ["P63.5"], "gate": "P63.0",
        "heading": "CELL 63 VERDICT ({date}) — main editor model, 610 runs; verdict lines as printed by the registered script, reading to follow",
        "label": "Result", "title": "Runs finished: results by the rules set in advance",
        "size": "610 runs with the main editor model",
        "what": "The main editor model finished its 610 runs on {long}.",
        "paths": ["bench/analysis/cell63", "bench/runs/cell63_checkable.jsonl"],
    },
    "c66-conveyed": {
        "cell": "66", "kind": "note",
        "heading": "CELL 66 RUN RECORD ({date}) — judging finished; the comparison waits for the person's 120 labels",
        "label": "Note", "title": "AI judging finished, the comparison waits for labels",
        "summary": ("The two AI judges finished all 1,710 cases on {long}, and 120 of them were drawn for the author to label "
                    "blind. No result of the comparison is computed or shown until those labels are finished and saved."),
        "size": "AI judging done, the person's 120 labels pending",
        "found": ("The two AI judges finished all 1,710 cases on {long}. A sample of 120 cases was then drawn for the author "
                  "to label blind. Nothing about the comparison between caveats and ordinary sentences is computed or shown "
                  "until those labels are finished and saved, so that knowing the result cannot influence the labels."),
        "paths": ["bench/analysis/cell66", "bench/runs/cell66_conveyed.jsonl", "bench/runs/cell66_misscheck.jsonl",
                  "bench/labels/cell66_conveyed"],
    },
    "c64-readers": {
        "cell": "64", "kind": "verdict", "reported": ["P64.4"],
        "heading": "CELL 64 VERDICT ({date}) — six reader models, 3,300 reads; verdict lines as printed by the registered script, reading to follow",
        "label": "Result", "title": "Reads finished: results by the rules set in advance",
        "size": "3,300 reads by six reader models",
        "what": "The six reader models finished their 3,300 reads on {long}.",
        "paths": ["bench/analysis/cell64", "bench/runs/cell64_readers.jsonl"],
    },
    "c65-judges": {
        "cell": "65", "kind": "verdict", "reported": ["P65.4"],
        "heading": "CELL 65 VERDICT ({date}) — four added judges, 3,024 judgments; verdict lines as printed by the registered script, reading to follow",
        "label": "Result", "title": "Judging finished: results by the rules set in advance",
        "size": "3,024 judgments by four added judges",
        "what": "The four added judges finished their 3,024 judgments on {long}.",
        "paths": ["bench/analysis/cell65", "bench/runs/cell65_judgments.jsonl"],
    },
    "c63-repeat": {
        "cell": "63", "kind": "note",
        "heading": "CELL 63 RUN RECORD ({date}) — two more editor models (phi4:14b, qwen3-vl:30b); tables as printed by the registered script",
        "label": "Note", "title": "Two more editor models ran the same test",
        "summary": ("Phi-4 and qwen3-vl ran the same 610 prompts, finishing on {long}. Their tables are in the notebook "
                    "entry. The pass or fail results stay those of the main editor model."),
        "paths": ["bench/analysis/cell63", "bench/runs/cell63_checkable.jsonl"],
    },
    "c67-livechain": {
        "cell": "67", "kind": "verdict", "reported": ["P67.4"], "gate": "P67.0",
        "heading": "CELL 67 VERDICT ({date}) — the live chain on 61 items; verdict lines as printed by the registered script, reading to follow",
        "label": "Result", "title": "Runs finished: results by the rules set in advance",
        "size": "61 questions, two versions each",
        "what": "The full live system finished both versions of the 61 questions on {long}.",
        "paths": ["bench/analysis/cell67", "bench/runs/cell67_livechain.jsonl"],
    },
}


def _sh(*args, check=False) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=ROOT, capture_output=True, text=True, check=check)


def _long(d: dt.date) -> str:
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def _append_runbook(heading: str, body: str) -> int:
    """Append one entry; return the 1-based line number of its heading."""
    text = RUNBOOK.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    line = text.count("\n") + 2                    # one blank line, then the heading
    RUNBOOK.write_text(text + "\n## " + heading + "\n\n" + body.rstrip("\n") + "\n", encoding="utf-8")
    return line


def _cell_outcome(graded: list[str], gate_failed: bool) -> str:
    if gate_failed:
        return "stopped"
    if not graded:
        return "measured"
    if all(g == "held" for g in graded):
        return "held"
    if all(g in ("failed", "reversed") for g in graded):
        return "failed"
    if all(g == "unclear" for g in graded):
        return "unclear"
    return "mixed"


def record(step: str, state: str, output: str, info: dict) -> str | None:
    """state: 'done' | 'failed' | 'skipped'. Returns the commit hash, or None."""
    meta = STEPS[step]
    today = dt.date.today()
    date, long = today.isoformat(), _long(today)
    head = _sh("git", "rev-parse", "--short", "HEAD").stdout.strip()
    cell = meta["cell"]
    doc = json.loads(BATCH.read_text(encoding="utf-8"))
    c = doc["cells"][cell]
    preface = (f"Recorded automatically by the run queue (step `{step}`, {info.get('finished_utc', '')}, commit {head} "
               f"checked out, {info.get('attempts', 1)} attempt(s)). ")

    if state == "skipped":
        heading = (f"CELL {cell} HALT ({date}) — not run: the condition stated in the registration was not met "
                   f"({info.get('reason', 'see the queue log')})")
        body = preface + "The step did not start. " + info.get("reason", "")
        line = _append_runbook(heading, body)
        c["outcome"], c["size"] = "stopped", "Not run: a checkpoint set in advance was not passed"
        c["found"] = (f"This cell did not run. Its plan said it would run only if an earlier check passed, and on {long} "
                      "that check had not passed. No runs were made and nothing was scored. The check exists because the "
                      "test is only meaningful if the editor can work out these answers when it is given the right figures. "
                      "The notebook entry below records the reason the queue gave for skipping it.")
        c["entries"][str(line)] = {"label": "Stopped", "title": "Not run: a checkpoint set in advance was not passed",
                                   "summary": (f"The plan for this cell said it would run only if an earlier check passed. "
                                               f"On {long} that check had not passed, so the queue skipped the cell and made no runs.")}
    elif state == "failed":
        heading = f"CELL {cell} RUN RECORD ({date}) — the step stopped with an error; the queue moved on (see bench/queue/logs/{step}.log)"
        body = (preface + "The step did not complete. The last lines of its log:\n\n```\n" + output[-3000:] + "\n```\n\n"
                "Records already written are kept; the stage is resumable.")
        line = _append_runbook(heading, body)
        c["entries"][str(line)] = {"label": "Note", "title": "The run stopped with an error",
                                   "summary": (f"On {long} this step stopped with an error after {info.get('attempts', 1)} "
                                               "attempts, and the queue moved on to the next one. The records already saved "
                                               "are kept, and the step can be resumed from where it stopped.")}
    else:
        body = (preface + "The block below is the unedited output of the registered scoring stage. Its verdict words come "
                "from rules fixed in the registration above; nothing in this entry is an interpretation. The analyst's "
                "reading follows as a separate entry.\n\n```\n" + output.rstrip("\n") + "\n```")
        line = _append_runbook(meta["heading"].format(date=date), body)
        if meta["kind"] == "verdict":
            words = {}
            for pid, word in VERDICT_RE.findall(output):
                words.setdefault(pid, word)
            graded = []
            for e in c["expectations"]:
                if e["id"] in meta.get("reported", []):
                    e["outcome"], e["note"] = "not-graded", NOTE["not-graded"]
                elif e["id"] in words:
                    e["outcome"] = WORD_TO_OUTCOME[words[e["id"]]]
                    e["note"] = NOTE[e["outcome"]]
                    if e["id"] != meta.get("gate"):
                        graded.append(e["outcome"])
            gate_failed = bool(meta.get("gate")) and words.get(meta["gate"]) == "FAILS"
            c["outcome"] = _cell_outcome(graded, gate_failed)
            n = {k: sum(1 for g in graded if g == k) for k in ("held", "failed", "reversed", "unclear", "partly")}
            c["size"] = meta["size"]
            c["description"] = re.sub(r"\s*Planned[^.]*\.(\s*It runs only[^.]*\.)?\s*$", "", c["description"]).rstrip() + \
                f" The runs finished on {long}."
            c["found"] = (meta["what"].format(long=long) + " By the rules written down in advance, "
                          f"{n['held']} of the {len(graded)} graded expectations held up, {n['failed'] + n['reversed']} did not, "
                          f"and {n['unclear'] + n['partly']} were too close to call or only partly held. The scoring script's "
                          "full output is in the notebook entry below. A fuller account, with the numbers in plain form, follows.")
            c["entries"][str(line)] = {
                "label": meta["label"], "title": meta["title"],
                "summary": (meta["what"].format(long=long) + f" Of the {len(graded)} graded expectations, {n['held']} held up, "
                            f"{n['failed'] + n['reversed']} did not and {n['unclear'] + n['partly']} were too close to call or "
                            "only partly held, by the rules written down in advance. A fuller account follows.")}
        else:
            if "size" in meta:
                c["size"] = meta["size"]
            if "found" in meta:
                c["found"] = meta["found"].format(long=long)
            c["entries"][str(line)] = {"label": meta["label"], "title": meta["title"],
                                       "summary": meta["summary"].format(long=long)}
    BATCH.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    log = []
    for cmd in ([PY, str(PLAIN / "make_assignments.py")], [PY, str(PLAIN / "lint.py"), str(BATCH)],
                [PY, str(ROOT / "docs" / "ledger_explorer" / "build.py")]):
        r = _sh(*cmd)
        log.append(f"$ {' '.join(cmd[1:])}\n{(r.stdout + r.stderr)[-1500:]}")
    (Q / "logs").mkdir(parents=True, exist_ok=True)
    (Q / "logs" / f"{step}.site.log").write_text("\n".join(log), encoding="utf-8")

    paths = ["RUNBOOK_PAPER_HARDENING.md", "docs/ledger_explorer/plain/batch_M.json",
             "docs/ledger_explorer/plain/assignments.json", "site_v3", "bench/queue"] + \
        [p for p in meta.get("paths", []) if (ROOT / p).exists()]
    _sh("git", "add", "--", *paths)
    what = {"done": "finished", "failed": "stopped with an error", "skipped": "not run (condition not met)"}[state]
    msg = (f"Queue: Cell {cell} step {step} {what}; runbook entry holds the registered script's unedited output, "
           f"site rebuilt locally (Netlify stays paused, nothing pushed); reading to follow\n\n{TRAILER}")
    r = _sh("git", "commit", "-m", msg, "--", *paths)
    if r.returncode != 0:
        (Q / "logs" / f"{step}.site.log").open("a").write("\nCOMMIT FAILED:\n" + r.stdout + r.stderr)
        return None
    return _sh("git", "rev-parse", "--short", "HEAD").stdout.strip()
