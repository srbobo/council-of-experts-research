#!/usr/bin/env python3
"""Write plain/assignments.json: which cells, studies and claims each writer covers."""
import contextlib
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(os.path.dirname(HERE), "build.py")

BATCHES = {
    "A": (["1", "2", "3", "4", "5", "6", "6b", "6c", "7", "7a", "7b", "7c"], ["setup", "writing-notes", "dose"]),
    "B": (["8", "8B", "9", "10", "11", "12", "13"], ["verification-audit", "data-integrity-audit", "paper-v07", "paper-witnesses"]),
    "C": (["14", "15", "16"], ["execution-path-audit", "paper-behavior", "tension-enumeration", "provenance-replication"]),
    "D": (["17", "18", "19", "20", "21", "22"], ["harness-built"]),
    "E": (["23", "24", "25", "26", "27", "28"], []),
    "F": (["29", "30", "31", "IV", "32", "33", "34"], ["pd13", "block-32-36"]),
    "G": (["35", "36", "37", "38", "39", "40"], []),
    "H": (["41", "42"], ["dictation", "phrase-forms", "seat-pilot", "domain-probe"]),
    "I": (["43", "43-R", "44", "45", "46"], ["tension-fate", "transport-battery"]),
    "J": (["47", "48", "49", "50", "51", "52"], []),
    "K": (["53", "54", "55", "56", "57", "58"], []),
    "L": (["59", "60", "61"], ["gates", "integration"]),
}

src = open(BUILD, encoding="utf-8").read()
cut = src.index("# ---------------------------------------------------------------- build the explorer page")
g = {"__file__": BUILD, "__name__": "assign"}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src[:cut], BUILD, "exec"), g)
data = g["data"]
cells = {c["id"]: c for c in data["cells"]}
studies = {s["id"]: s for s in data["studies"]}
program = {p["id"]: p for p in data["program"]}

out = {"batches": {}, "status": {}}
seen = set()
for b, (cids, sids) in BATCHES.items():
    bc = []
    for cid in cids:
        c = cells[cid]
        seen.add(cid)
        pids = []
        for p in c["predictions"] + [{"id": g_["id"]} for g_ in c["grid"]]:
            if p["id"] not in pids:
                pids.append(p["id"])
        bc.append({
            "id": cid, "current_title": c["title"], "status_parsed": c["status"],
            "never_ran": not c["entries"] or c["status"] in ("registered", "matrix-only"),
            "pids": pids,
            "entries": [{"line": e["line"], "end": e["end"], "kind": e["kind"], "heading": e["heading"]} for e in c["entries"]],
            "matrix_row": c.get("matrix"),
        })
    bs = []
    for sid in sids:
        st = studies[sid]
        bs.append({"id": sid, "kind": st["kind"], "entries": [
            {"id": eid, "line": program[eid]["line"], "end": program[eid]["end"], "heading": program[eid]["heading"],
             "parts": [pt["heading"] for pt in program[eid].get("parts", [])]} for eid in st["entry_ids"]]})
    out["batches"][b] = {"cells": bc, "studies": bs, "output": "docs/ledger_explorer/plain/batch_%s.json" % b}
missing = set(cells) - seen
assert not missing, missing
out["status"] = {"output": "docs/ledger_explorer/plain/status.json", "items": [
    {"id": it["id"], "section": it["section"], "section_title": it["section_title"], "kind": it["kind"],
     "line": it["line"], "cells": it["cells"], "header": it["header"], "cols": it["cols"]} for it in data["status_items"]]}
json.dump(out, open(os.path.join(HERE, "assignments.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for b, spec in out["batches"].items():
    n = sum(e["end"] - e["line"] + 1 for c in spec["cells"] for e in c["entries"]) + \
        sum(e["end"] - e["line"] + 1 for s in spec["studies"] for e in s["entries"] if e["end"])
    print(b, "cells", [c["id"] for c in spec["cells"]], "studies", [s["id"] for s in spec["studies"]], "lines", n)
print("status items", len(out["status"]["items"]))
