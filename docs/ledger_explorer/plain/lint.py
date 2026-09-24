#!/usr/bin/env python3
"""Check a plain-language batch file against STYLE_GUIDE.md.

    python3 docs/ledger_explorer/plain/lint.py docs/ledger_explorer/plain/batch_A.json

Prints ERRORS (must fix) and WARNINGS (review). Exit code 1 when there are errors.
Also accepts status.json (claims) and glossary.json.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSIGN = os.path.join(HERE, "assignments.json")

CELL_OUTCOMES = {"held", "mixed", "failed", "unclear", "stopped", "not-run", "measured"}
EXP_OUTCOMES = {"held", "partly", "failed", "reversed", "unclear", "not-graded", "not-tested"}
ENTRY_LABELS = {"Plan", "Change to the plan", "Pilot", "Result", "Correction", "Mistake caught", "Stopped", "Note"}

BANNED = [
    r"load[- ]bearing", r"\bhonest(?:ly|y)?\b", r"\bhonesty\b", r"\bowned\b", r"on the record", r"full prominence",
    r"\bgraduat\w*", r"\btravel(?:s|led|ed|ling)?\b", r"\bbuys?\b", r"\bship(?:s|ped|ping)?\b", r"\blevers?\b",
    r"\bsurfac(?:e|es|ed|ing)\b", r"\bsignals?\b", r"\bcrucial(?:ly)?\b", r"\bnotably\b", r"\bimportantly\b",
    r"\bgenuine(?:ly)?\b", r"\bfundamental(?:ly)?\b", r"\bdelve\w*", r"\blandscape\b", r"\bnuanced?\b",
    r"\brobust\w*", r"worth noting", r"in other words", r"\bupshot\b", r"\bpunchline\b", r"\bheadlines?\b",
    r"\bverdicts?\b", r"\bfalsif\w*", r"\bpre-?regist\w*", r"\bregist(?:er|ered|ering|ers|ration|rations)\b",
    r"\bestimand\w*", r"\bconfound\w*", r"\bablat\w*", r"\bbootstrap\w*", r"\bstatistical\w*", r"\bsignifican\w*",
    r"\barms?\b", r"\bseats?\b", r"\bsynthesi[sz]er\w*", r"\baggregator\w*", r"\bthe lead\b", r"\btransport\w*",
    r"prior fill", r"\bfreight\b", r"\britual\w*", r"\bdisposition\w*", r"\bqualification\w*", r"\bepistemic\w*",
    r"\bprovenance\b", r"\bscaffold\w*", r"\bentangle\w*", r"\battainab\w*", r"\bgoodhart\b", r"\bbimodal\b",
    r"\binstruments?\b", r"\bregex\w*", r"\blexicon\w*", r"\bdecisive\w*", r"\bdescriptive\w*", r"\bexploratory\b",
    r"\bnull\b", r"\bcorp(?:us|ora)\b", r"\bcohorts?\b", r"\bstrat(?:um|a)\b", r"\bvariance\b", r"\btensions?\b",
    r"\bgat(?:e|es|ed|ing)\b", r"\breplicat\w*", r"\bshrinkage\b", r"\be\.g\.", r"\bi\.e\.", r"\bvs\b\.?",
]
BANNED_CASE = [r"\bCIs?\b", r"\bNE\b"]
WARN = [
    r"\bmoreover\b", r"\bfurthermore\b", r"\badditionally\b", r"\bultimately\b", r"\bunderscor\w*", r"\bhighlight\w*",
    r"\btestament\b", r"\bpivotal\b", r"\bintricate\b", r"\bmultifaceted\b", r"\bleverag\w*", r"\bseamless\w*",
    r"\bholistic\b", r"\brealm\b", r"\bjourney\b", r"\bunlock\w*", r"\bempower\w*", r"\bfoster\w*", r"\bbolster\w*",
    r"\bshowcas\w*", r"in essence", r"at its core", r"\btakeaway\b", r"key insight", r"it is important to",
    r"\bnot just\b", r"\bessentially\b", r"\bnotable\b", r"\bstriking\w*", r"\bremarkabl\w*", r"\bclearly\b",
]
PUNCT = [("—", "em dash"), ("–", "en dash"), (";", "semicolon"), ("!", "exclamation mark"), ("~", "tilde"),
         ("**", "markdown bold"), ("`", "backtick"), ("…", "ellipsis character")]

LIMITS_CELL = {"title": (8, 70), "description": (120, 280), "why": (200, 900), "found": (250, 1500),
               "means": (120, 800), "size": (3, 60)}
LIMITS_SHORT = {"title": (8, 70), "description": (100, 280), "why": (120, 900), "found": (60, 1500),
                "means": (60, 800), "size": (3, 60)}

errors, warnings, notes = [], [], []


def strip_quotes(t):
    quoted = re.findall(r"\"([^\"]{1,120})\"|“([^”]{1,120})”", t)
    for q in quoted:
        q = q[0] or q[1]
        for pat in BANNED:
            if re.search(pat, q, re.I):
                warnings.append("quoted text contains a banned word: \"%s\"" % q)
                break
    return re.sub(r"\"[^\"]{1,120}\"|“[^”]{1,120}”", "\"\"", t)


def check_text(where, t):
    if t is None:
        return
    if not isinstance(t, str):
        errors.append("%s: expected text, got %s" % (where, type(t).__name__))
        return
    t2 = strip_quotes(t)
    for pat in BANNED:
        for m in re.finditer(pat, t2, re.I):
            errors.append("%s: banned word %r" % (where, m.group(0)))
    for pat in BANNED_CASE:
        for m in re.finditer(pat, t2):
            errors.append("%s: banned abbreviation %r" % (where, m.group(0)))
    for pat in WARN:
        for m in re.finditer(pat, t2, re.I):
            warnings.append("%s: machine-sounding word %r" % (where, m.group(0)))
    for ch, name in PUNCT:
        if ch in t2:
            errors.append("%s: %s" % (where, name))
    for ln in t.split("\n"):
        if re.match(r"^\s*(?:[-*•]\s|#)", ln):
            errors.append("%s: markdown list or heading" % where)
    for sent in re.split(r"(?<=[.?])\s+", t):
        n = len(sent.split())
        if n > 38:
            warnings.append("%s: long sentence (%d words): %s…" % (where, n, sent[:70]))


def check_len(where, t, lo, hi):
    if not isinstance(t, str):
        errors.append("%s: missing" % where)
        return
    n = len(t)
    if n < lo or n > hi:
        (errors if (n > hi * 1.15 or n < lo * 0.6) else warnings).append(
            "%s: length %d, want %d to %d" % (where, n, lo, hi))


def check_item(where, obj, entry_keys, pids, never_ran, is_study):
    if not isinstance(obj, dict):
        errors.append("%s: missing" % where)
        return
    limits = LIMITS_SHORT if (never_ran or is_study) else LIMITS_CELL
    for f, (lo, hi) in limits.items():
        check_len("%s.%s" % (where, f), obj.get(f), lo, hi)
        check_text("%s.%s" % (where, f), obj.get(f))
    if obj.get("title", "").endswith("."):
        warnings.append("%s.title ends with a period" % where)
    if obj.get("outcome") not in CELL_OUTCOMES:
        errors.append("%s.outcome: %r not in %s" % (where, obj.get("outcome"), sorted(CELL_OUTCOMES)))
    lat = obj.get("later")
    if lat is not None:
        check_len("%s.later" % where, lat, 40, 500)
        check_text("%s.later" % where, lat)
    exps = obj.get("expectations")
    if not isinstance(exps, list):
        errors.append("%s.expectations: must be a list" % where)
        exps = []
    ids = []
    for i, ex in enumerate(exps):
        w = "%s.expectations[%s]" % (where, ex.get("id", i) if isinstance(ex, dict) else i)
        if not isinstance(ex, dict):
            errors.append("%s: must be an object" % w)
            continue
        ids.append(ex.get("id"))
        if ex.get("outcome") not in EXP_OUTCOMES:
            errors.append("%s.outcome: %r not in %s" % (w, ex.get("outcome"), sorted(EXP_OUTCOMES)))
        check_len(w + ".text", ex.get("text"), 30, 240)
        check_text(w + ".text", ex.get("text"))
        check_len(w + ".note", ex.get("note"), 20, 260)
        check_text(w + ".note", ex.get("note"))
    for p in pids:
        if p not in ids:
            errors.append("%s.expectations: no entry for %s" % (where, p))
    ents = obj.get("entries")
    if not isinstance(ents, dict):
        errors.append("%s.entries: must be an object keyed by %s" % (where, "entry id" if is_study else "line number"))
        ents = {}
    for k in entry_keys:
        if k not in ents:
            errors.append("%s.entries: missing %s" % (where, k))
    for k, pe in ents.items():
        w = "%s.entries[%s]" % (where, k)
        if k not in entry_keys:
            errors.append("%s: not an entry of this item (expected one of %s)" % (w, entry_keys))
        if not isinstance(pe, dict):
            errors.append("%s: must be an object" % w)
            continue
        if pe.get("label") not in ENTRY_LABELS:
            errors.append("%s.label: %r not in %s" % (w, pe.get("label"), sorted(ENTRY_LABELS)))
        check_len(w + ".title", pe.get("title"), 8, 80)
        check_text(w + ".title", pe.get("title"))
        check_len(w + ".summary", pe.get("summary"), 60, 450)
        check_text(w + ".summary", pe.get("summary"))
    if is_study:
        rel = obj.get("related")
        if not isinstance(rel, list):
            errors.append("%s.related: must be a list of cell ids" % where)


def main(path):
    doc = json.load(open(path, encoding="utf-8"))
    name = os.path.basename(path)
    assign = json.load(open(ASSIGN, encoding="utf-8")) if os.path.exists(ASSIGN) else {}
    if name == "status.json":
        want = [it["id"] for it in assign.get("status", {}).get("items", [])]
        got = doc.get("status", {})
        for sid in want:
            if sid not in got:
                errors.append("status: missing %s" % sid)
        for sid, it in got.items():
            if not isinstance(it, dict):
                errors.append("status.%s: must be an object" % sid)
                continue
            check_len("status.%s.claim" % sid, it.get("claim"), 20, 260)
            check_text("status.%s.claim" % sid, it.get("claim"))
            check_len("status.%s.detail" % sid, it.get("detail"), 40, 700)
            check_text("status.%s.detail" % sid, it.get("detail"))
    elif name == "harness.json":
        def walk(o, where):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k not in ("cells", "kind", "source", "study"):
                        walk(v, where + "." + k)
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, "%s[%d]" % (where, i))
            elif isinstance(o, str):
                check_text(where, o)
        walk(doc, "harness")
    elif name == "glossary.json":
        for i, t in enumerate(doc.get("terms", [])):
            check_text("glossary[%s].definition" % t.get("term", i), t.get("definition"))
    else:
        batch = doc.get("batch")
        spec = assign.get("batches", {}).get(batch)
        if not spec:
            errors.append("unknown batch %r (expected one of %s)" % (batch, sorted(assign.get("batches", {}))))
            spec = {"cells": [], "studies": []}
        for c in spec["cells"]:
            check_item("cell %s" % c["id"], doc.get("cells", {}).get(c["id"]), [str(e["line"]) for e in c["entries"]],
                       c["pids"], c["never_ran"], False)
        for st in spec["studies"]:
            check_item("study %s" % st["id"], doc.get("studies", {}).get(st["id"]), [e["id"] for e in st["entries"]],
                       [], False, True)
        extra = set(doc.get("cells", {})) - {c["id"] for c in spec["cells"]}
        if extra:
            errors.append("cells not in this batch: %s" % sorted(extra))
    for e in errors:
        print("ERROR  ", e)
    for w in warnings:
        print("warning", w)
    print("\n%s: %d errors, %d warnings" % (name, len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
