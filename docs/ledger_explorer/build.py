#!/usr/bin/env python3
"""Parse RUNBOOK_PAPER_HARDENING.md (the cell ledger) into structured JSON.

Output: ledger.json in the scratchpad, consumed by the explorer HTML.
"""
import glob
import json
import os
import re
import sys

ROOT = "/Users/sambobo/Documents/Claude Projects/CoE"
SRC = os.path.join(ROOT, "RUNBOOK_PAPER_HARDENING.md")
STATUS = os.path.join(ROOT, "docs", "STATUS.md")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ledger.json")
TEMPLATE = os.path.join(HERE, "template.html")
HTML_OUT = os.path.join(HERE, "index.html")

text = open(SRC, encoding="utf-8").read()
lines = text.split("\n")

HEAD_RE = re.compile(r"^(#{1,3}) (.+?)\s*$")
CELL_RE = re.compile(r"\bCELLS?\s+(\d+[A-Za-z]?(?:-R)?|IV)\b")
RANGE_RE = re.compile(r"\bCELLS\s+(\d+)-(\d+)\b")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# ---------------------------------------------------------------- headings
heads = []
for i, ln in enumerate(lines):
    m = HEAD_RE.match(ln)
    if m:
        heads.append({"line": i, "level": len(m.group(1)), "text": m.group(2)})

SPECIAL = {
    "P1 VERDICT": "1",
    "P8 VERDICT": "10",
}


def norm_id(s):
    s = s.strip()
    if s.upper() == "IV":
        return "IV"
    m = re.match(r"(\d+)([A-Za-z]?)(-R)?$", s)
    if not m:
        return s
    n, letter, r = m.groups()
    # 8B is written uppercase, 6b/6c/7a/7b/7c lowercase — keep canonical spelling
    canon = {"8b": "8B", "6B": "6b", "6C": "6c", "7A": "7a", "7B": "7b", "7C": "7c"}
    key = n + letter
    key = canon.get(key, key)
    return key + (r or "")


def cell_ref(t):
    up = t.upper()
    for k, v in SPECIAL.items():
        if up.startswith(k):
            return v, False
    if RANGE_RE.search(up):
        return None, True  # block heading
    m = CELL_RE.search(t)
    if m:
        return norm_id(m.group(1)), False
    return None, False


# first pass: which ids have a pre-registration heading (to decide 60-R folding)
prereg_ids = set()
for h in heads:
    cid, _ = cell_ref(h["text"])
    if cid and "PRE-REGISTRATION" in h["text"].upper():
        prereg_ids.add(cid)


def fold(cid):
    if cid and cid.endswith("-R") and cid not in prereg_ids:
        return cid[:-2]
    return cid


# locate the CELLS 32-36 block: from its H1 to the next H2 with a ref and a kind keyword
block_start = block_end = None
for idx, h in enumerate(heads):
    _, is_block = cell_ref(h["text"])
    if is_block:
        block_start = idx
        for j in range(idx + 1, len(heads)):
            hj = heads[j]
            cj, _ = cell_ref(hj["text"])
            if hj["level"] <= 2 and cj and re.search(r"VERDICT|PRE-REGISTRATION", hj["text"].upper()):
                block_end = j
                break
        break


def kind_of(t, in_block):
    u = t.upper()
    if "PRE-REGISTRATION" in u:
        return "prereg"
    if "AMENDMENT" in u and "VERDICT" not in u:
        return "amendment"
    if "VERDICT" in u:
        return "verdict"
    if "NOT EXECUTABLE" in u:
        return "verdict"
    if "DOES NOT PROCEED" in u or "HALT" in u:
        return "halt"
    if "DEVIATION" in u:
        return "deviation"
    if "PILOT" in u:
        return "pilot"
    if "AMENDMENT" in u:
        return "amendment"
    if "CORRECTION" in u:
        return "correction"
    if "VOID" in u or "WRONG CONDITION" in u or "INCIDENT" in u:
        return "incident"
    if "RE-RUN" in u:
        return "rerun"
    if in_block:
        return "prereg"
    if "REGISTRATION REWRITTEN" in u or "CONFOUND" in u or "ITEMS FROZEN" in u or "REWARD VALIDATED" in u or "PRE-ANALYSIS" in u or "READ" in u or "NUMBERING" in u:
        return "note"
    if "DECOMPOSITION" in u or "RESULT" in u or "TELEMETRY" in u:
        return "analysis"
    return "note"


# ---------------------------------------------------------------- entries
entries = []
cur = None
for idx, h in enumerate(heads):
    cid, is_block = cell_ref(h["text"])
    cid = fold(cid)
    in_block = block_start is not None and block_start < idx < (block_end or 10 ** 9)
    starts = h["level"] <= 2 or cid is not None or is_block
    if not starts:
        continue
    # close previous entry
    if cur is not None:
        cur["end"] = h["line"]
    cur = {
        "line": h["line"],
        "level": h["level"],
        "heading": h["text"],
        "cell": cid,
        "is_block": is_block,
        "in_block": in_block or is_block,
        "kind": kind_of(h["text"], in_block),
    }
    entries.append(cur)
if cur is not None:
    cur["end"] = len(lines)

# strip the H1 title chunk (line 0) and the intro matrix sections: keep them as program entries
for e in entries:
    body = lines[e["line"] + 1 : e["end"]]
    # drop trailing '---' separators
    while body and body[-1].strip() in ("", "---"):
        body.pop()
    while body and body[0].strip() == "":
        body.pop(0)
    e["body"] = "\n".join(body)
    dates = DATE_RE.findall(e["heading"])
    if not dates:
        dates = DATE_RE.findall(e["body"][:400])
    e["date"] = dates[0] if dates else None

# the block's non-cell H2 sections are parts of the block entry
block_entry = None
merged = []
for e in entries:
    if e["is_block"]:
        block_entry = e
        e["parts"] = []
        merged.append(e)
        continue
    if e["in_block"] and e["cell"] is None and block_entry is not None:
        block_entry["parts"].append({"heading": e["heading"], "body": e["body"], "line": e["line"]})
        continue
    merged.append(e)
entries = merged


# ---------------------------------------------------------------- helpers
def clean_headline(h):
    """Strip 'CELL 25 VERDICT — ' / '(date...)' scaffolding from a heading."""
    t = h
    t = re.sub(r"^#+\s*", "", t)
    t = re.sub(r"^(?:CELLS?\s+[\w-]+(?:\s*\([^)]*\))?(?:\s*/\s*P\d+)?|P\d+)\s*", "", t, flags=re.I)
    t = re.sub(r"^(?:PRE-REGISTRATION(?:\s+BLOCK)?|FINAL VERDICT|VERDICT|AMENDMENT(?:\s*#\d+)?|CORRECTION|DEVIATION|PILOT(?: GATES| DEVIATION)?|REGISTERED DEVIATION|ASSEMBLY DEVIATION|PRE-ANALYSIS NOTE)\s*", "", t, flags=re.I)
    t = re.sub(r"^[—\-–:\s]+", "", t)
    return t.strip()


def paren_note(h):
    """Return the parenthetical that carries the date, minus the date itself."""
    for m in re.finditer(r"\(([^)]*\d{4}-\d{2}-\d{2}[^)]*)\)", h):
        inner = m.group(1)
        inner = DATE_RE.sub("", inner)
        inner = re.sub(r"^(?:registered|measured|recorded)?\s*[,;]?\s*", "", inner.strip(), flags=re.I)
        inner = re.sub(r"^[,;\s]+|[,;\s]+$", "", inner)
        return inner or None
    return None


def strip_md(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    return s.strip()


def chunks(body):
    """Split markdown into paragraph / bullet chunks."""
    out = []
    buf = []
    for ln in body.split("\n"):
        if ln.strip() == "":
            if buf:
                out.append("\n".join(buf))
                buf = []
            continue
        if re.match(r"^\s*[-*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln) or ln.startswith("#"):
            if buf:
                out.append("\n".join(buf))
                buf = []
        buf.append(ln)
    if buf:
        out.append("\n".join(buf))
    return out


PRED_ID = r"(P-?(?:\d+[A-Za-z]?|[A-Za-z]+)(?:-R|R)?\.\d+|L\d\.\d|T\d|V-[AB]|P\d+)"
PRED_LABEL = re.compile(r"^\s*(?:[-*]\s+|\d+\.\s+)?(?:###\s*)?\*{0,2}\s*(?:Prediction\s+)?" + PRED_ID + r"(?![\w.]\w)")


def extract_predictions(body):
    preds = []
    for ch in chunks(body):
        first = ch.split("\n", 1)[0]
        m = PRED_LABEL.match(first)
        if not m:
            continue
        pid = m.group(1).rstrip(".")
        txt = re.sub(r"^\s*(?:[-*]\s+|\d+\.\s+)?(?:###\s*)?", "", ch)
        preds.append({"id": pid, "md": txt.strip()})
    return preds


OUTCOME_WORDS = r"NOT SUPPORTED|NOT CONFIRMED|SUPPORTED|FALSIFIED|NOT EVALUABLE|PARTIAL|CONFIRMED|REVERSED|WITHDRAWN|HOLDS|HELD|PASSES|FAILS|BLOCKED|NOT TESTABLE"
OUT_RE = re.compile(r"\b" + PRED_ID + r"\b(?![.\d])")
WORD_RE = re.compile(r"\b(" + OUTCOME_WORDS + r")\b")


def extract_outcomes(txt):
    """Find 'P25.1 SUPPORTED'-style statements. Returns ordered {pid: outcome}."""
    found = {}
    for m in OUT_RE.finditer(txt):
        pid = m.group(1)
        # look ahead on the same line (and a bit beyond a bold close) up to 110 chars
        window = txt[m.end(): m.end() + 110]
        window = window.split("\n")[0] if "\n" in window[:1] else window
        # cut at the next prediction id to avoid stealing a neighbour's word (but allow 'AND P14.2 BOTH FALSIFIED')
        w = WORD_RE.search(window)
        if not w:
            continue
        between = window[: w.start()]
        nxt = OUT_RE.search(between)
        if nxt and not re.search(r"\b(and|AND|&|/|,)\s*$", between[: nxt.start()].rstrip() + " ") and "BOTH" not in between.upper() and "and" not in between.lower():
            continue
        if pid not in found:
            found[pid] = w.group(1)
    return found


def first_paragraph(body, prefer=("PURPOSE", "QUESTION", "WHY", "HYPOTHESIS", "MOTIVATION", "THE GAP", "FRAMING")):
    """A short 'question' summary: first paragraph of a preferred subsection, else first paragraph."""
    secs = re.split(r"\n(?=### )", "\n" + body)
    cand = None
    for s in secs:
        s = s.strip("\n")
        if s.startswith("### "):
            title, _, rest = s.partition("\n")
            if any(k in title.upper() for k in prefer):
                cand = rest
                break
    if cand is None:
        cand = body
    for ch in chunks(cand):
        if ch.startswith("#") or ch.startswith("|"):
            continue
        t = strip_md(re.sub(r"\s*\n\s*", " ", ch))
        if len(t) > 40:
            return t[:700] + ("…" if len(t) > 700 else "")
    return None


# ---------------------------------------------------------------- matrix (cells 1-10)
matrix = {}
m_sec = re.search(r"## Cells & success criteria\n(.*?)\n## ", text, re.S)
if m_sec:
    for item in re.findall(r"^(\d+)\. (.*?)(?=^\d+\. |\Z)", m_sec.group(1), re.S | re.M):
        matrix[item[0]] = strip_md(re.sub(r"\s*\n\s*", " ", item[1]))
ptable = {}
m_p = re.search(r"## Pre-registered predictions.*?\n(\|.*?)\n\n", text, re.S)
if m_p:
    for row in m_p.group(1).split("\n")[2:]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) >= 3:
            ptable[cells[0]] = {"id": cells[0], "md": cells[1] + "\n\n*Falsified if:* " + cells[2]}
MATRIX_P = {"1": ["P1"], "3": ["P2", "P3"], "4": ["P4"], "5": ["P5"], "6": ["P6"], "10": ["P8"]}
MATRIX_TITLE = {
    "1": "SFT-on-chosen control",
    "2": "Five seeds per cell — bootstrap CIs",
    "3": "Seat interventions — finance and healthcare seats",
    "4": "Cross-base — legal pairs on two aligned bases",
    "5": "CPO arm on Saul",
    "6": "Synthesizer ablation — 3 Leads × PRESERVE on/off",
    "7": "Scoring hardening",
    "8": "Architecture comparison",
    "9": "External anchor — public abstention benchmark",
    "10": "Marker-position analysis (P8, content entanglement)",
}

# ---------------------------------------------------------------- assemble cells
cells = {}


def cell_obj(cid):
    if cid not in cells:
        cells[cid] = {"id": cid, "entries": []}
    return cells[cid]


for e in entries:
    if e["cell"]:
        cell_obj(e["cell"])["entries"].append(e)

for cid in list(MATRIX_TITLE):
    cell_obj(cid)

KIND_ORDER = {"prereg": 0}


def sort_key(cid):
    m = re.match(r"(\d+)([A-Za-z]?)(-R)?$", cid)
    if cid == "IV":
        return (31.5, "", "")
    if not m:
        return (999, cid, "")
    return (int(m.group(1)), m.group(2).lower(), m.group(3) or "")


def derive_status(c):
    kinds = [e["kind"] for e in c["entries"]]
    verdicts = [e for e in c["entries"] if e["kind"] == "verdict"]
    halts = [e for e in c["entries"] if e["kind"] == "halt"]
    last_v = verdicts[-1] if verdicts else None
    if last_v:
        u = last_v["heading"].upper()
        if "NOT EXECUTABLE" in u:
            return "not-executable"
        if "INSTRUMENT FAILURE" in u or "BLOCKED" in u:
            # a later verdict may supersede — only if it is the last one
            return "blocked"
        if "NOT EVALUABLE" in u or "NO EVALUABLE" in u:
            return "not-evaluable"
        if "TWO-STRIKES" in u or "NO TESTABLE FORM" in u:
            return "not-testable"
        oc = list(c["outcomes"].values())
        oc_n = [o for o in oc if o]
        if oc_n:
            sup = sum(1 for o in oc_n if o in ("SUPPORTED", "CONFIRMED", "HOLDS", "HELD", "PASSES"))
            fal = sum(1 for o in oc_n if o in ("FALSIFIED", "REVERSED", "FAILS", "WITHDRAWN"))
            if sup == len(oc_n):
                return "supported"
            if fal == len(oc_n):
                return "falsified"
            return "mixed"
        return "verdict"
    if halts:
        return "halted"
    if "analysis" in kinds:
        return "analysis"
    if "prereg" in kinds or "pilot" in kinds:
        return "registered"
    if not c["entries"]:
        return "matrix-only"
    return "recorded"


out_cells = []
for cid in sorted(cells, key=sort_key):
    c = cells[cid]
    ents = c["entries"]
    preregs = [e for e in ents if e["kind"] == "prereg"]
    verdicts = [e for e in ents if e["kind"] == "verdict"]
    # title
    if preregs:
        title = clean_headline(preregs[0]["heading"])
        title = re.sub(r"\s*\(registered[^)]*\)\s*", " ", title, flags=re.I).strip()
        title = re.sub(r"^\(\d{4}-\d{2}-\d{2}\)\s*[—\-–]?\s*", "", title).strip()
    elif cid in MATRIX_TITLE:
        title = MATRIX_TITLE[cid]
    else:
        title = clean_headline(ents[0]["heading"])
    title = re.sub(r"\s*\((?:registered )?\d{4}-\d{2}-\d{2}[^)]*\)\s*$", "", title).strip()
    title = re.sub(r",?\s*(?:registered|recorded)\s+\d{4}-\d{2}-\d{2}.*$", "", title, flags=re.I).strip()
    title = re.sub(r"\s*\((?:registered|recorded)[^)]*\)", "", title, flags=re.I).strip()
    # display id
    disp = cid
    # predictions
    preds = []
    for p in preregs:
        preds.extend(extract_predictions(p["body"]))
    # some amendments register new predictions (e.g. Cell 36 amendment #1, Cell 16 rewrite)
    for e in ents:
        if e["kind"] in ("amendment", "note") and "### Predictions" in e["body"]:
            preds.extend(extract_predictions(e["body"]))
    inherits = None
    if preregs:
        mi = re.search(r"\(P(\d+)\.\d = P(\d+)\.\d", preregs[0]["body"])
        if mi and mi.group(1) == cid and not preds and mi.group(2) in cells:
            src = cells[mi.group(2)]
            inherits = mi.group(2)
            for p in [e for e in src["entries"] if e["kind"] == "prereg"]:
                for q in extract_predictions(p["body"]):
                    preds.append({"id": q["id"].replace("P" + inherits + ".", "P" + cid + "."), "md": q["md"], "inherited_from": inherits})
    if not preds and cid in MATRIX_P:
        preds = [ptable[p] for p in MATRIX_P[cid] if p in ptable]
    if any("." in p["id"] for p in preds):
        preds = [p for p in preds if "." in p["id"]]
    seen = set()
    uniq = []
    for p in preds:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        uniq.append(p)
    preds = uniq
    # outcomes: latest verdict/halt wins; keep history
    outcomes = {}
    history = []
    for e in ents:
        if e["kind"] in ("verdict", "halt"):
            oc = extract_outcomes(e["heading"] + "\n" + e["body"])
            for pid, o in oc.items():
                outcomes[pid] = o
                history.append({"pid": pid, "outcome": o, "date": e["date"], "entry_line": e["line"]})
    # grid = registered predictions + any ids only found in verdicts
    grid = []
    for p in preds:
        grid.append({"id": p["id"], "outcome": outcomes.get(p["id"])})
    def same_cell(pid):
        m = re.match(r"^P-?([A-Za-z0-9]+?)(?:-R|R)?\.\d+$", pid)
        if m:
            return m.group(1).lower() == cid.replace("-R", "r").lower() or m.group(1).lower() == cid.replace("-R", "").lower()
        if re.match(r"^P\d+$", pid):
            return cid in MATRIX_P and pid in MATRIX_P[cid]
        return re.match(r"^L\d\.\d$", pid) is not None and cid in ("47", "48")
    for pid, o in outcomes.items():
        if pid not in seen and same_cell(pid):
            grid.append({"id": pid, "outcome": o, "unregistered": True})
    if any("." in g["id"] for g in grid):
        grid = [g for g in grid if "." in g["id"]]
    c["outcomes"] = {g["id"]: g["outcome"] for g in grid}
    status = derive_status(c)
    # question / purpose
    question = first_paragraph(preregs[0]["body"]) if preregs else (matrix.get(cid) if cid in matrix else (first_paragraph(ents[0]["body"]) if ents else None))
    # result headline
    result = None
    result_note = None
    result_date = None
    if verdicts:
        v = verdicts[-1]
        result = clean_headline(v["heading"])
        result = re.sub(r"\s*\((?:[^()]*\d{4}-\d{2}-\d{2}[^()]*)\)\s*", " ", result).strip()
        result = re.sub(r"^\s*[—\-–:]\s*", "", result)
        result_note = paren_note(v["heading"])
        result_date = v["date"]
        result = re.sub(r"^(?:recorded|measured)\s+\d{4}-\d{2}-\d{2}\s*", "", result, flags=re.I).strip()
        result = re.sub(r"^\([^)]*\)\s*[—\-–:]?\s*", "", result).strip()
        if len(result) < 12:
            for ch in chunks(v["body"]):
                if ch.startswith("|") or ch.startswith("#"):
                    continue
                t2 = strip_md(re.sub(r"\s*\n\s*", " ", ch))
                if len(t2) > 20:
                    result = t2[:220] + ("…" if len(t2) > 220 else "")
                    break
    else:
        halts = [e for e in ents if e["kind"] == "halt"]
        if halts:
            result = clean_headline(halts[-1]["heading"])
            result = re.sub(r"\s*\((?:[^()]*\d{4}-\d{2}-\d{2}[^()]*)\)\s*", " ", result).strip()
            result_date = halts[-1]["date"]
    registered = preregs[0]["date"] if preregs else ("2026-07-11" if cid in MATRIX_TITLE else (ents[0]["date"] if ents else None))
    if registered is None and cid in ("32", "33", "34", "35", "36") and block_entry is not None:
        registered = block_entry["date"]
    # runs
    runs = None
    for e in reversed(ents):
        if e["kind"] == "verdict":
            m = re.search(r"(\d[\d,/]*)\s*(?:\w+[-\w]*\s+){0,2}?(?:runs|pipelines|pairs|items|calls)", e["heading"])
            if m:
                runs = m.group(0)
                break
    out_cells.append({
        "id": cid,
        "display": "Cell " + disp,
        "title": title,
        "status": status,
        "registered": registered,
        "verdict_date": result_date,
        "question": question,
        "matrix": matrix.get(cid),
        "predictions": preds,
        "inherits": inherits,
        "grid": grid,
        "history": history,
        "result": result,
        "result_note": result_note,
        "runs": runs,
        "block": ("block-32-36" if cid in ("32", "33", "34", "35", "36") else None),
        "entries": [
            {
                "line": e["line"] + 1,
                "end": e["end"],
                "kind": e["kind"],
                "date": e["date"],
                "heading": e["heading"],
                "body": e["body"],
            }
            for e in ents
        ],
    })

# ---------------------------------------------------------------- program (non-cell) entries
program = []
for e in entries:
    if e["cell"]:
        continue
    if e["line"] == 0:
        continue
    pid = "block-32-36" if e["is_block"] else "entry-%d" % (e["line"] + 1)
    program.append({
        "id": pid,
        "line": e["line"] + 1,
        "end": e["end"],
        "kind": e["kind"] if not e["is_block"] else "prereg",
        "date": e["date"],
        "heading": e["heading"],
        "body": e["body"],
        "parts": e.get("parts", []),
    })

# ---------------------------------------------------------------- STATUS.md: every claim, lesson, question and rule
STATUS_KIND = {1: "believe", 2: "tentative", 3: "withdrawn", 4: "tool-lesson", 5: "open", 6: "rule"}


def cell_refs(text):
    refs = set()
    for m in re.finditer(r"\bCells?\s+((?:\d+[A-Za-z]?(?:-R)?|IV)(?:\s*(?:[/,&]|and)\s*(?:\d+[A-Za-z]?(?:-R)?))*)", text):
        for r in re.split(r"\s*(?:[/,&]|and)\s*", m.group(1)):
            if r:
                refs.add(norm_id(r))
    for m in re.finditer(r"\bC(\d{1,2}[A-Za-z]?(?:-R)?)\b", text):
        refs.add(norm_id(m.group(1)))
    for m in re.finditer(r"\bP(\d{1,2}[A-Za-z]?)\.\d", text):
        refs.add(norm_id(m.group(1)))
    return {fold(r) for r in refs}


status_items = []
if os.path.exists(STATUS):
    st_lines = open(STATUS, encoding="utf-8").read().split("\n")
    sec_no = None
    sec_title = None
    header = None
    counters = {}
    for i, ln in enumerate(st_lines):
        m = re.match(r"^## (\d+)\.\s*(.+)$", ln)
        if m:
            sec_no = int(m.group(1))
            sec_title = m.group(2).strip()
            header = None
            continue
        if ln.startswith("## "):
            sec_no = None
            continue
        if sec_no not in STATUS_KIND:
            continue
        item = None
        if ln.startswith("|"):
            if re.match(r"^\|\s*-", ln):
                continue
            cols = [c.strip() for c in ln.strip().strip("|").split("|")]
            nxt = st_lines[i + 1] if i + 1 < len(st_lines) else ""
            if re.match(r"^\|\s*-", nxt):
                header = cols
                continue
            item = {"cols": cols, "header": header, "text": ln}
        else:
            m2 = re.match(r"^(?:\d+\.|-)\s+(.+)$", ln)
            if m2:
                item = {"cols": [m2.group(1)], "header": None, "text": m2.group(1)}
        if item is None:
            continue
        counters[sec_no] = counters.get(sec_no, 0) + 1
        item.update({
            "id": "S%d-%02d" % (sec_no, counters[sec_no]),
            "section": sec_no,
            "section_title": sec_title,
            "kind": STATUS_KIND[sec_no],
            "cells": sorted(cell_refs(item["text"]), key=sort_key),
            "line": i + 1,
        })
        status_items.append(item)

# ---------------------------------------------------------------- program entries grouped into studies
STUDIES = [
    ("setup", "setup", ["entry-7", "entry-21", "entry-41", "entry-46"]),
    ("writing-notes", "paper", ["entry-73", "entry-126"]),
    ("dose", "experiment", ["entry-209"]),
    ("verification-audit", "audit", ["entry-1448"]),
    ("data-integrity-audit", "audit", ["entry-1497"]),
    ("paper-v07", "paper", ["entry-1540"]),
    ("paper-witnesses", "paper", ["entry-1592"]),
    ("execution-path-audit", "audit", ["entry-1762"]),
    ("paper-behavior", "paper", ["entry-2343"]),
    ("tension-enumeration", "analysis", ["entry-2392"]),
    ("provenance-replication", "analysis", ["entry-2444"]),
    ("harness-built", "engineering", ["entry-2750"]),
    ("pd13", "analysis", ["entry-4491", "entry-4528"]),
    ("block-32-36", "setup", ["block-32-36"]),
    ("dictation", "tool", ["entry-5745", "entry-5827"]),
    ("phrase-forms", "tool", ["entry-5924"]),
    ("seat-pilot", "analysis", ["entry-6097"]),
    ("domain-probe", "tool", ["entry-6258"]),
    ("tension-fate", "analysis", ["entry-6739", "entry-6766"]),
    ("transport-battery", "analysis", ["entry-7088", "entry-7122"]),
    ("gates", "tool", ["entry-8972", "entry-9039"]),
    ("integration", "engineering", ["entry-9080"]),
]
sys.path.insert(0, HERE)
import build_data  # noqa: E402

build_data.build_baseline_entry(program)
STUDIES.append(("baseline-corpus", "data", ["baseline-corpus"]))
program_by_id = {p["id"]: p for p in program}
studies = []
claimed = set()
for sid, skind, eids in STUDIES:
    ents = [program_by_id[e] for e in eids if e in program_by_id]
    if not ents:
        continue
    claimed.update(e["id"] for e in ents)
    text = "\n".join(e["heading"] + "\n" + e["body"] + "\n" + "\n".join(pt["heading"] + "\n" + pt["body"] for pt in e.get("parts", [])) for e in ents)
    dates = sorted(d for d in (e["date"] for e in ents) if d) or (["2026-07-11"] if sid == "setup" else [])
    studies.append({
        "id": sid, "kind": skind, "entry_ids": [e["id"] for e in ents],
        "date": dates[0] if dates else None, "end_date": dates[-1] if dates else None,
        "related": sorted(cell_refs(text), key=sort_key),
        "heading": ents[0]["heading"],
    })
unclaimed = [p["id"] for p in program if p["id"] not in claimed]
if unclaimed:
    print("WARNING program entries not in any study:", unclaimed)

# ---------------------------------------------------------------- artifacts on disk
def artifacts_for(cid):
    key = cid.replace("-R", "R")
    found = []
    pats = [
        ("bench/analysis", r"^cell%s(?![0-9A-Za-z])" % re.escape(key)),
        ("train", r"cell%s(?![0-9A-Za-z])" % re.escape(key)),
        ("docs", r"^CELL%s_" % re.escape(key.upper())),
        ("bench/runs", r"^cell%s(?![0-9A-Za-z])" % re.escape(key)),
    ]
    for d, pat in pats:
        full = os.path.join(ROOT, d)
        if not os.path.isdir(full):
            continue
        for name in sorted(os.listdir(full)):
            if re.search(pat, name, re.I if d == "docs" else 0):
                p = os.path.join(full, name)
                rel = os.path.join(d, name)
                if os.path.isdir(p):
                    kids = sorted(os.listdir(p))
                    found.append({"path": rel + "/", "dir": True, "n": len(kids), "children": kids[:40]})
                else:
                    found.append({"path": rel, "dir": False, "size": os.path.getsize(p)})
    return found


for c in out_cells:
    c["artifacts"] = artifacts_for(c["id"])
    c["status_refs"] = [it["id"] for it in status_items if c["id"] in it["cells"]]

import datetime  # noqa: E402

data = {
    "source": "RUNBOOK_PAPER_HARDENING.md",
    "source_lines": len(lines),
    "generated": datetime.date.today().isoformat(),
    "cells": out_cells,
    "program": program,
    "studies": studies,
    "status_items": status_items,
}

# ---------------------------------------------------------------- plain-language layer (plain/*.json)
PLAIN_DIR = os.path.join(HERE, "plain")
CELL_OUTCOMES = {"held", "mixed", "failed", "unclear", "stopped", "not-run", "measured"}
EXP_OUTCOMES = {"held", "partly", "failed", "reversed", "unclear", "not-graded", "not-tested"}
ENTRY_LABELS = {"Plan", "Change to the plan", "Pilot", "Result", "Correction", "Mistake caught", "Stopped", "Note"}
plain_cells, plain_studies, plain_status = {}, {}, {}
glossary, site_copy, harness_page = [], {}, {}
if os.path.isdir(PLAIN_DIR):
    for f in sorted(glob.glob(os.path.join(PLAIN_DIR, "*.json"))):
        name = os.path.basename(f)
        if not (name.startswith("batch_") or name in ("status.json", "extra.json", "glossary.json", "site.json", "harness.json")):
            continue
        try:
            pj = json.load(open(f, encoding="utf-8"))
        except Exception as ex:  # noqa
            print("PLAIN: could not read", name, ex)
            continue
        if name == "glossary.json":
            glossary = pj.get("terms", [])
            continue
        if name == "site.json":
            site_copy = pj
            continue
        if name == "harness.json":
            harness_page = pj
            src_doc = os.path.join(ROOT, pj.get("source", ""))
            harness_page["source_text"] = open(src_doc, encoding="utf-8").read() if os.path.isfile(src_doc) else ""
            continue
        plain_cells.update(pj.get("cells", {}))
        plain_studies.update(pj.get("studies", {}))
        plain_status.update(pj.get("status", {}))

problems = []
for c in out_cells:
    p = plain_cells.get(c["id"])
    c["plain"] = p
    if not p:
        problems.append("cell %s: no plain text" % c["id"])
        continue
    if p.get("outcome") not in CELL_OUTCOMES:
        problems.append("cell %s: outcome %r" % (c["id"], p.get("outcome")))
    for ex in p.get("expectations", []):
        if ex.get("outcome") not in EXP_OUTCOMES:
            problems.append("cell %s: expectation %s outcome %r" % (c["id"], ex.get("id"), ex.get("outcome")))
    lines_have = {str(e["line"]) for e in c["entries"]}
    lines_plain = set((p.get("entries") or {}).keys())
    if lines_have - lines_plain:
        problems.append("cell %s: entries without plain summary %s" % (c["id"], sorted(lines_have - lines_plain)))
    for ln_, pe in (p.get("entries") or {}).items():
        if pe.get("label") not in ENTRY_LABELS:
            problems.append("cell %s entry %s: label %r" % (c["id"], ln_, pe.get("label")))
for st_ in studies:
    p = plain_studies.get(st_["id"])
    st_["plain"] = p
    if not p:
        problems.append("study %s: no plain text" % st_["id"])
        continue
    have = set(st_["entry_ids"])
    got = set((p.get("entries") or {}).keys())
    if have - got:
        problems.append("study %s: entries without plain summary %s" % (st_["id"], sorted(have - got)))
for it in status_items:
    it["plain"] = plain_status.get(it["id"])
    if not it["plain"]:
        problems.append("claim %s: no plain text" % it["id"])
        continue
    reviewed = [fold(norm_id(x)) for x in it["plain"].get("cells", []) if isinstance(x, str)]
    if isinstance(it["plain"].get("cells"), list):
        # the plain-language writer checked each reference against the notebook; the parser can misread
        # prompt-clause labels such as "C2" as cell ids, so the reviewed list wins
        it["cells"] = sorted({x for x in reviewed if any(c["id"] == x for c in out_cells)}, key=sort_key)
for c in out_cells:
    c["status_refs"] = [it["id"] for it in status_items if c["id"] in it["cells"]]
data["glossary"] = glossary
data["site"] = site_copy
data["harness"] = harness_page
data["plain_problems"] = problems
print("plain layer: %d cells, %d studies, %d claims, %d glossary terms; %d problems" % (
    sum(1 for c in out_cells if c["plain"]), sum(1 for x in studies if x["plain"]),
    sum(1 for x in status_items if x["plain"]), len(glossary), len(problems)))
for pr in problems[:60]:
    print("  PLAIN:", pr)
json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- report
print("cells:", len(out_cells), " program entries:", len(program), " studies:", len(studies), " claims items:", len(status_items))
for c in out_cells:
    g = " ".join("%s=%s" % (x["id"], x["outcome"] or "?") for x in c["grid"])
    print("%-8s %-15s reg=%s ver=%s ents=%d | %s | %s" % (c["display"], c["status"], c["registered"], c["verdict_date"], len(c["entries"]), c["title"][:60], g))


# ---------------------------------------------------------------- build the explorer page
def _fix(x):
    return re.sub(r"<(?=[A-Za-z/])", "&lt;", x) if isinstance(x, str) else x

for c in data["cells"]:
    for e in c["entries"]:
        e["body"] = _fix(e["body"])
    for p in c["predictions"]:
        p["md"] = _fix(p["md"])
for p in data["program"]:
    p["body"] = _fix(p["body"])
    for pt in p.get("parts", []):
        pt["body"] = _fix(pt["body"])
for r in data["status_items"]:
    r["cols"] = [_fix(x) for x in r["cols"]]
    r["text"] = _fix(r["text"])
# ---------------------------------------------------------------- model-level data chunks (data/*.js)
sys.path.insert(0, HERE)
import build_data  # noqa: E402
MANIFEST = os.path.join(HERE, "data_manifest.json")
if "--page-only" in sys.argv and os.path.exists(MANIFEST):
    print("page only: reusing data/ and", MANIFEST)
    data["data_index"] = json.load(open(MANIFEST))
    if not any(p["id"] == "baseline-corpus" for p in data["program"]):
        build_data.build_baseline_entry(data["program"])
else:
    print("building data chunks…")
    data["data_index"] = build_data.build(data)
    json.dump(data["data_index"], open(MANIFEST, "w"), indent=1)

js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
tpl = open(TEMPLATE, encoding="utf-8").read()
tpl = tpl.replace("/*__DATA_CSS__*/", open(os.path.join(HERE, "viewer_data.css"), encoding="utf-8").read())
tpl = tpl.replace("/*__DATA_JS__*/", open(os.path.join(HERE, "viewer_data.js"), encoding="utf-8").read().replace("</", "<\\/"))
open(HTML_OUT, "w", encoding="utf-8").write(tpl.replace("/*__DATA__*/", js))
print("wrote", HTML_OUT, os.path.getsize(HTML_OUT) // 1024, "KB")

# ---------------------------------------------------------------- standalone website (site_v3/)
# The artifact host wraps the page in its own document; a website needs a full one.
import shutil  # noqa: E402

SITE_DIR = os.path.join(ROOT, "site_v3")
page = open(HTML_OUT, encoding="utf-8").read()
split_at = page.index('<div class="wrap" id="app"')
head_part, body_part = page[:split_at], page[split_at:]
head_part = head_part.replace('<meta charset="utf-8">\n', "", 1).replace('<meta name="viewport" content="width=device-width, initial-scale=1">\n', "", 1)
title = "Paper-Hardening Cell Ledger"
desc = ("Every experiment in the Council of Experts research program, in plain language: what each one asked, "
        "what we expected, what happened, what we claim today, and the rebuilt system we call the harness.")
icon = "data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%93%92%3C/text%3E%3C/svg%3E"
doc = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
       "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
       f"<meta name=\"description\" content=\"{desc}\">\n"
       f"<meta property=\"og:title\" content=\"{title}\">\n<meta property=\"og:description\" content=\"{desc}\">\n"
       "<meta property=\"og:type\" content=\"website\">\n"
       f"<link rel=\"icon\" href=\"{icon}\">\n"
       + head_part + "</head>\n<body>\n" + body_part + "\n</body>\n</html>\n")
os.makedirs(SITE_DIR, exist_ok=True)
open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8").write(doc)
site_data = os.path.join(SITE_DIR, "data")
if os.path.isdir(site_data):
    shutil.rmtree(site_data)
shutil.copytree(DATA_DIR if "DATA_DIR" in globals() else os.path.join(HERE, "data"), site_data)
print("wrote", SITE_DIR, "(%d data files)" % len(os.listdir(site_data)))
