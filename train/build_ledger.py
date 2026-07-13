"""Regenerable run ledger: every imported run with prompt, output excerpt,
and disposition scores. Run: .venv/bin/python train/build_ledger.py"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from examples.test_cases import CASES as CASE_OBJS
BEH = {"cutoff":[r'training[- ]?cut[- ]?off',r'knowledge cut[- ]?off',r'may (?:be |have )(?:stale|outdated|evolved)',r'post[- ]?cut[- ]?off',r'after my training',r'verify (?:current|latest|recent)',r'as of (?:my )?(?:training|knowledge|2024|2025)'],
 "modeled":[r'modell?ed at',r'\bassume[ds]? (?:that|the)',r'\bassuming (?:that|the|a |an |\d)',r'under the assumption',r'this assume[ds]',r'\bwe assume\b',r'\bhypothetical[ly]?\b'],
 "precise":[r'(?:approval).*?(?:vs\.?|versus|not).*?(?:clearance)',r'distinguish(?:es|ing|ed)? between',r'standard[- ]of[- ]care',r'(?:510\(k\)|de novo|PMA)\s+(?:clearance|approval|pathway)',r'\b(?:NDA|BLA)\s+approval\b'],
 "jurisd":[r'\bUK\s?GDPR\b',r'\bEU\s?GDPR\b',r'post[- ]Brexit',r'each\s+(?:jurisdiction|country|state|regime)',r'preempt(?:ion|s|ed)'],
 "hedging":[r'(?:false[- ]positive|false[- ]negative)',r'alert fatigue',r'real[- ]world\s+(?:evidence|data)',r'sensitivity (?:analysis|range|to|of)',r'low/?high (?:case|scenario|estimate)',r'\b±\s?\d',r'(?:may|might|could)\s+(?:vary|differ|change)']}
def dens(t): return sum(len(re.findall(p,t,re.I)) for ps in BEH.values() for p in ps)/len(t)*1000 if t else 0.0
def cds(t):
    if not t: return 0.0
    k = sum(1 for ps in BEH.values() if any(re.search(p,t,re.I) for p in ps))
    return dens(t)*((k/5)**0.5)
def ex(t, n=180): return t[:n].replace("\n"," ").replace("|","/")

out = ["# Run Ledger — every imported run, prompt, output, and score",
 "",
 "Regenerate with `.venv/bin/python train/build_ledger.py`. Full outputs and",
 "per-phase audit trails live in the JSON files referenced per row and are",
 "browsable in the Results UI. Static system prompts: `council/prompts.py`",
 "(planner, 3 seats, synthesis, direct-answer, behavior-spec addendum);",
 "single-shot prompt: `bench/opus_single.py`; pair-generation prompts:",
 "`train/gen_pairs.py` (REWRITE_ADD / REWRITE_STRIP). Scoring definitions:",
 "Results page 'Aggregate Disposition Scores' + runbook glossary.", ""]
imported = sorted(Path('bench/runs/imported').glob('*.json'))
by_case = {}
for f in imported:
    d = json.load(open(f))
    by_case.setdefault(d.get('case_id','?'), []).append((f.name, d))
for case in CASE_OBJS:
    runs = by_case.get(case.id, [])
    if not runs: continue
    out += [f"## {case.id} — {case.title}", "", f"**Prompt:** {case.prompt}", "",
            f"**Rubric items:** {len(case.rubric)} (see `examples/test_cases.py`)", "",
            "| file | mode | chars | density | CDS | seat(legal) dens | output excerpt |",
            "|---|---|---|---|---|---|---|"]
    for name, d in runs:
        t = d.get('final_output','')
        legal = [x for x in d.get('deliberation',{}).get('turns',[]) if x.get('seat')=='legal'] if d.get('deliberation') else []
        sd = f"{dens(legal[0]['output_text']):.2f}" if legal else "—"
        out.append(f"| {name} | {d.get('mode','?')} | {len(t)} | {dens(t):.2f} | {cds(t):.3f} | {sd} | {ex(t)}… |")
    out.append("")
Path('docs/RUN_LEDGER.md').write_text("\n".join(out))
print(f"ledger: {len(imported)} runs across {len(by_case)} cases -> docs/RUN_LEDGER.md")
