#!/usr/bin/env python3
"""Convert British spellings to American in plain-language JSON files (text values only)."""
import json
import re
import sys

MAP = [
    (r"\bbehaviour", "behavior"), (r"\bBehaviour", "Behavior"),
    (r"\banalysed\b", "analyzed"), (r"\banalysing\b", "analyzing"), (r"\banalyse\b", "analyze"),
    (r"\bre-analysed\b", "re-analyzed"), (r"\bRe-analysed\b", "Re-analyzed"), (r"\bre-analyse\b", "re-analyze"),
    (r"\blabelled\b", "labeled"), (r"\blabelling\b", "labeling"), (r"\bLabelled\b", "Labeled"),
    (r"\bfavoured\b", "favored"), (r"\bfavouring\b", "favoring"), (r"\bfavours\b", "favors"), (r"\bfavourable\b", "favorable"),
    (r"\bfavourite\b", "favorite"), (r"\bfavour\b", "favor"),
    (r"\bpenalise\b", "penalize"), (r"\bpenalised\b", "penalized"), (r"\bpenalises\b", "penalizes"), (r"\bpenalising\b", "penalizing"),
    (r"\bartefact", "artifact"), (r"\bcancelled\b", "canceled"), (r"\bprogramme\b", "program"),
    (r"\brecognise", "recogniz"), (r"\borganise", "organiz"), (r"\bsummarise", "summariz"), (r"\bprioritise", "prioritiz"),
    (r"\boptimise", "optimiz"), (r"\bminimise", "minimiz"), (r"\bmaximise", "maximiz"), (r"\bnormalise", "normaliz"),
    (r"\bgeneralise", "generaliz"), (r"\bcharacterise", "characteriz"), (r"\bstandardise", "standardiz"),
    (r"\bcategorise", "categoriz"), (r"\butilise", "utiliz"), (r"\brandomise", "randomiz"),
    (r"\bjudgement", "judgment"), (r"\bmodelled\b", "modeled"), (r"\bmodelling\b", "modeling"), (r"\bcentre\b", "center"),
]


def fix(s, counter):
    for pat, rep in MAP:
        s, n = re.subn(pat, rep, s)
        counter[0] += n
    return s


def walk(o, counter):
    if isinstance(o, dict):
        return {k: walk(v, counter) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v, counter) for v in o]
    if isinstance(o, str):
        return fix(o, counter)
    return o


for path in sys.argv[1:]:
    doc = json.load(open(path, encoding="utf-8"))
    c = [0]
    doc = walk(doc, c)
    json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%-16s %d changes" % (path, c[0]))
