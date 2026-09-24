#!/usr/bin/env python3
"""Cross-check the plain-language layer against the notebook.

1. Outcomes: an expectation the notebook grades explicitly ("P25.3 FALSIFIED")
   must carry a compatible plain outcome, and a cell's overall outcome must not
   contradict the parsed status.
2. Numbers: every number in a cell's plain text should appear in that cell's
   notebook entries (or in the later mentions of the cell), directly or as a
   proportion (82% <-> 0.82 / 0.818). Unmatched numbers are listed for review.

    .venv/bin/python docs/ledger_explorer/plain/check_consistency.py
"""
import contextlib
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
BUILD = os.path.join(os.path.dirname(HERE), "build.py")

src = open(BUILD, encoding="utf-8").read()
cut = src.index("# ---------------------------------------------------------------- build the explorer page")
g = {"__file__": BUILD, "__name__": "check"}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src[:cut], BUILD, "exec"), g)
data = g["data"]
runbook = open(os.path.join(ROOT, "RUNBOOK_PAPER_HARDENING.md"), encoding="utf-8").read()
status_txt = open(os.path.join(ROOT, "docs", "STATUS.md"), encoding="utf-8").read()

COMPAT = {
    "SUPPORTED": {"held"}, "CONFIRMED": {"held"}, "HOLDS": {"held"}, "HELD": {"held"}, "PASSES": {"held"},
    "FALSIFIED": {"failed", "reversed"}, "FAILS": {"failed", "reversed"}, "REVERSED": {"reversed", "failed"},
    "PARTIAL": {"partly"}, "NOT SUPPORTED": {"failed", "reversed", "unclear"}, "NOT CONFIRMED": {"failed", "reversed", "unclear"}, "NOT EVALUABLE": {"unclear", "not-tested", "not-graded"}, "WITHDRAWN": {"failed", "reversed", "unclear"},
}
STATUS_BAD = {  # parsed status -> plain outcomes that would contradict it
    "supported": {"failed", "not-run"}, "falsified": {"held", "not-run"}, "registered": {"held", "failed", "mixed"},
    "matrix-only": {"held", "failed", "mixed", "unclear"}, "not-executable": {"held", "failed"},
    "halted": {"held", "failed"},
}

NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(%?)")
SKIP_WORDS = {"2026", "2025", "2024"}
_ID = r"(?:\d+[A-Za-z]?(?:-R)?|IV)"
REF = re.compile(r"\bCells? " + _ID + r"(?:(?:, and |, | and | to | or )" + _ID + r")*|\bP-?[\w]+\.\d+|\bPD-13\b|\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December)\b")


def later_mentions(cid):
    pats = [r"\bCell %s\b" % re.escape(cid), r"\bCELL %s\b" % re.escape(cid), r"\bC%s\b" % re.escape(cid),
            r"\bP%s\." % re.escape(cid.replace("-R", "R"))]
    out = []
    for text in (runbook, status_txt):
        for ln in text.split("\n"):
            if any(re.search(p, ln) for p in pats):
                out.append(ln)
    return "\n".join(out)


def num_forms(tok, pct):
    t = tok.replace(",", "")
    forms = {t}
    try:
        v = float(t)
    except ValueError:
        return forms
    if pct:
        p = v / 100.0
        forms |= {("%.2f" % p).lstrip("0"), "%.2f" % p, ("%.3f" % p), ("%.1f" % p), t + "%", str(int(v)) + "%"}
        for d in range(0, 10):  # 82% matches 0.818 .. 0.824 and 0.815 .. 0.825 roughly
            forms.add("%.3f" % (p - 0.005 + d * 0.001))
    return forms


def check_numbers(where, texts, source):
    src_norm = source.replace(",", "")
    missing = []
    for t in texts:
        if not t:
            continue
        t = REF.sub(" ", t)
        for m in NUM.finditer(t):
            tok, pct = m.group(1), m.group(2)
            if tok in SKIP_WORDS:
                continue
            raw = tok.replace(",", "")
            if not pct and "." not in raw and int(float(raw)) <= 12:
                continue  # small counts ("two", ordinals, "3 of 4") are too common to check
            forms = num_forms(tok, pct)
            if not any(f and f in src_norm for f in forms):
                missing.append(tok + pct)
    if missing:
        print("  numbers not found in the notebook for %s: %s" % (where, ", ".join(sorted(set(missing)))))
    return len(set(missing))


issues = 0
unmatched = 0
for c in data["cells"]:
    p = c.get("plain")
    if not p:
        print("cell %s: MISSING plain text" % c["id"])
        issues += 1
        continue
    parsed = {x["id"]: x["outcome"] for x in c["grid"] if x.get("outcome")}
    for ex in p.get("expectations", []):
        want = parsed.get(ex.get("id"))
        if want and ex.get("outcome") not in COMPAT.get(want, {ex.get("outcome")}):
            print("cell %s %s: notebook says %s, plain says %s" % (c["id"], ex["id"], want, ex.get("outcome")))
            issues += 1
    bad = STATUS_BAD.get(c["status"], set())
    if p.get("outcome") in bad:
        print("cell %s: parsed status %s but plain outcome %s (check)" % (c["id"], c["status"], p.get("outcome")))
        issues += 1
    source = "\n".join(e["heading"] + "\n" + e["body"] for e in c["entries"]) + "\n" + (c.get("matrix") or "") + "\n" + later_mentions(c["id"])
    if c["id"] in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"):
        source += "\n" + runbook[:6000]
    texts = [p.get(k) for k in ("title", "description", "why", "found", "means", "later", "size")]
    texts += [x.get("text") for x in p.get("expectations", [])] + [x.get("note") for x in p.get("expectations", [])]
    texts += [v.get("summary") for v in (p.get("entries") or {}).values()] + [v.get("title") for v in (p.get("entries") or {}).values()]
    unmatched += check_numbers("cell " + c["id"], texts, source)

prog = {x["id"]: x for x in data["program"]}
for s in data["studies"]:
    p = s.get("plain")
    if not p:
        print("study %s: MISSING plain text" % s["id"])
        issues += 1
        continue
    source = "\n".join(prog[e]["heading"] + "\n" + prog[e]["body"] + "\n" + "\n".join(pt["heading"] + "\n" + pt["body"] for pt in prog[e].get("parts", [])) for e in s["entry_ids"] if e in prog)
    if s["id"] == "block-32-36":
        a = runbook.split("\n")
        source += "\n" + "\n".join(a[4624:4862])
    texts = [p.get(k) for k in ("title", "description", "why", "found", "means", "later", "size")]
    texts += [v.get("summary") for v in (p.get("entries") or {}).values()]
    texts += [x.get("text") for x in p.get("expectations", [])] + [x.get("note") for x in p.get("expectations", [])]
    unmatched += check_numbers("study " + s["id"], texts, source)

cell_text = {c["id"]: "\n".join(e["heading"] + "\n" + e["body"] for e in c["entries"]) for c in data["cells"]}
for it in data["status_items"]:
    if not it.get("plain"):
        continue
    src_txt = it["text"] + "\n" + "\n".join(cell_text.get(x, "") for x in it["cells"])
    unmatched += check_numbers("claim " + it["id"], [it["plain"].get("claim"), it["plain"].get("detail")], src_txt)

print("\n%d outcome issues, %d unmatched numbers to review" % (issues, unmatched))
