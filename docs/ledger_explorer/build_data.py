#!/usr/bin/env python3
"""Data layer for the ledger explorer.

For every cell (and a few program-level entries) gather the model-level data
the ledger's verdict rests on — imported council traces (planner / seat /
synthesis inputs and outputs), the cell's own run records, judge outputs,
frozen item files, analysis cards, and the prompt constants in the cell's
script — and write one gzip+base64 chunk per entity under data/.

Called from build.py; returns a manifest that the page embeds.
"""
import ast
import base64
import glob
import gzip
import json
import os
import re
import sys

ROOT = "/Users/sambobo/Documents/Claude Projects/CoE"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
LONG = 160  # strings at least this long go to the shared string table

# ------------------------------------------------------------------ run modes → producing cell
MODE_RULES = [
    (r"^local-council-(repro|spec|dpo|sft)$", "2"),
    (r"^local-council-(health|finance)-(repro|orpo)$", "3"),
    (r"^local-council-cpo$", "5"),
    (r"^local-council-dpo-v2$", "@dose"),
    (r"^cell6-", "6"), (r"^cell6b-", "6b"), (r"^cell6c-", "6c"),
    (r"^arch-", "8"), (r"^reg-", "8B"), (r"^cell11-", "11"), (r"^c13-", "13"),
    (r"^c17-", "17"), (r"^cell18-", "18"), (r"^c19-", "19"), (r"^c20-", "20"),
    (r"^c27-", "27"), (r"^c28-", "28"),
    (r"^(local-council|local-council-v2|gptoss-single|gptoss-single-spec|gptoss-council|opus-single|opus-council|swap-.*)$", "@baseline"),
]
ANALYSIS_DIR_RULES = {
    "integration": "INTEGRATION RUN", "gates": "GATES", "pd13": "PD-13", "tension_fate": "TENSION-FATE",
    "dictation": "DICTATION REGISTRY", "probe_domain": "DOMAIN-SIGNATURE",
}


def mode_owner(mode):
    for pat, owner in MODE_RULES:
        if re.match(pat, mode):
            return owner
    return None


# ------------------------------------------------------------------ helpers
class Table:
    def __init__(self):
        self.strings = []
        self.index = {}

    def ref(self, s):
        i = self.index.get(s)
        if i is None:
            i = len(self.strings)
            self.strings.append(s)
            self.index[s] = i
        return {"$s": i}

    def walk(self, o):
        if isinstance(o, str):
            return self.ref(o) if len(o) >= LONG else o
        if isinstance(o, list):
            return [self.walk(x) for x in o]
        if isinstance(o, dict):
            return {k: self.walk(v) for k, v in o.items()}
        return o


def field_summary(records):
    fields = {}
    for r in records[:2000]:
        if not isinstance(r, dict):
            continue
        for k, v in r.items():
            f = fields.setdefault(k, {"name": k, "types": set(), "n": 0, "chars": 0, "values": {}})
            f["n"] += 1
            t = type(v).__name__
            f["types"].add(t)
            if isinstance(v, str):
                f["chars"] += len(v)
                if len(v) < 80:
                    f["values"][v] = f["values"].get(v, 0) + 1
            elif isinstance(v, (int, float, bool)) or v is None:
                f["values"][json.dumps(v)] = f["values"].get(json.dumps(v), 0) + 1
            elif isinstance(v, list):
                f["chars"] += len(json.dumps(v))
    out = []
    for f in fields.values():
        avg = f["chars"] / max(f["n"], 1)
        long = avg > 120
        nvals = len(f["values"])
        facet = (not long) and 1 < nvals <= 40 and f["n"] > 1 and nvals < f["n"]
        out.append({
            "name": f["name"], "types": sorted(f["types"]), "n": f["n"], "long": long,
            "facet": facet, "values": sorted(f["values"].keys())[:40] if facet else None, "avg": int(avg),
        })
    return out


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def script_prompts(path, seen_modules):
    """String constants (>= 80 chars) assigned at any level of a script, plus f-string templates."""
    out = []
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
        tree = ast.parse(src)
    except Exception:
        return out, []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            v = node.value
            name = node.targets[0].id
            if isinstance(v, ast.Constant) and isinstance(v.value, str) and len(v.value) >= 80:
                out.append({"name": name, "text": v.value, "kind": "constant", "line": node.lineno})
            elif isinstance(v, (ast.JoinedStr, ast.BinOp, ast.Call)):
                seg = ast.get_source_segment(src, v) or ""
                if len(seg) >= 120 and ("prompt" in name.lower() or "system" in name.lower() or "user" in name.lower() or "body" in name.lower() or "instruction" in name.lower() or "msg" in name.lower()):
                    out.append({"name": name, "text": seg, "kind": "template (source)", "line": node.lineno})
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
    models = sorted(set(re.findall(r"[\"']([a-z0-9][\w.-]*:[\w.-]+)[\"']", src)))
    return out, [m for m in imports if m.split(".")[0] in ("council", "harness", "gst", "bench")] + [{"models": models}]


def module_prompts(modname):
    parts = modname.split(".")
    cands = [os.path.join(ROOT, *parts) + ".py", os.path.join(ROOT, *parts, "__init__.py"), os.path.join(ROOT, "gst", "src", *parts) + ".py"]
    for c in cands:
        if os.path.exists(c):
            ps, _ = script_prompts(c, set())
            rel = os.path.relpath(c, ROOT)
            return [{**p, "path": rel} for p in ps if p["kind"] == "constant"]
    return []


# ------------------------------------------------------------------ traces
def normalize_trace(o, fname, T):
    d = o.get("deliberation") or {}

    def msgs(ms):
        return [{"role": m.get("role"), "content": T.walk(m.get("content", ""))} for m in (ms or [])]

    def step(t):
        if not isinstance(t, dict):
            return None
        return {
            "seat": t.get("seat"), "member_name": t.get("member_name"), "ollama_tag": t.get("ollama_tag"),
            "backend": t.get("backend"), "messages": msgs(t.get("input_messages")),
            "output": T.walk(t.get("output_text", "")), "latency_ms": t.get("latency_ms"),
            "eval_count": t.get("eval_count"), "prompt_eval_count": t.get("prompt_eval_count"),
        }

    rec = {
        "file": fname, "case_id": o.get("case_id"), "case_title": o.get("case_title"), "mode": o.get("mode"),
        "model": o.get("model"), "captured_at": o.get("captured_at"), "notes": T.walk(o.get("notes", "")),
        "final_output": T.walk(o.get("final_output", "")), "final_chars": len(o.get("final_output", "") or ""),
        "query": T.walk(d.get("query", "")), "plan": T.walk(d.get("plan")), "plan_raw": T.walk(d.get("plan_raw", "")),
        "plan_messages": msgs(d.get("plan_input_messages")), "plan_latency_ms": d.get("plan_latency_ms"),
        "turns": [s for s in (step(t) for t in d.get("turns", [])) if s], "synthesis": step(d.get("synthesis")),
        "total_latency_ms": d.get("total_latency_ms"), "cabinet_name": d.get("cabinet_name"),
        "cabinet_backends": d.get("cabinet_backends"),
    }
    if d.get("system_prompt"):
        rec["system_prompt"] = T.walk(d["system_prompt"])
    if d.get("tokens"):
        rec["tokens"] = d["tokens"]
    rec["seats"] = ",".join(t["seat"] or "?" for t in rec["turns"])
    rec["n_turns"] = len(rec["turns"])
    return rec


BASELINE_ENTRY = {
    "id": "baseline-corpus", "line": 0, "end": 0, "kind": "analysis", "date": "2026-05-14",
    "heading": "Runs saved before the numbered experiments (14 May to 7 July 2026)",
    "body": "These runs were saved before the experiment plan was written on 11 July 2026. They cover the first council (Phi-4 14B as editor with Med42, Saul and Qwen-Open-Finance as specialists), a second council with different specialists, gpt-oss-20B answering alone and running every council role, and a few reference runs with Claude Opus. They were never an experiment of their own. They are listed here so every saved conversation in the project has a home.",
    "parts": [],
}


def build_baseline_entry(program):
    if not any(p["id"] == BASELINE_ENTRY["id"] for p in program):
        program.append(dict(BASELINE_ENTRY))


# ------------------------------------------------------------------ main build
def build(ledger):
    os.makedirs(DATA_DIR, exist_ok=True)
    for f in glob.glob(os.path.join(DATA_DIR, "*")):
        os.remove(f)
    cells = {c["id"]: c for c in ledger["cells"]}
    program = ledger["program"]

    def program_id(keyword):
        hits = [p for p in program if keyword in p["heading"].upper()]
        # prefer verdict / result entries
        hits.sort(key=lambda p: (0 if re.search(r"VERDICT|RESULT", p["heading"].upper()) else 1, -p["line"]))
        return hits[0]["id"] if hits else None

    dose_id = program_id("DOSE-RESPONSE")
    baseline_id = "baseline-corpus"
    build_baseline_entry(program)

    entities = {}  # id -> {"sources": [], "prompts": [], "notes": []}

    def ent(eid):
        return entities.setdefault(eid, {"sources": [], "prompts": [], "notes": [], "imports": []})

    def add_source(eid, key, title, kind, path, role, payload):
        src = {"key": key, "title": title, "kind": kind, "path": path, "role": role}
        src.update(payload)
        e = ent(eid)
        if any(s["key"] == key for s in e["sources"]):
            return
        e["sources"].append(src)

    def attach_file(eid, full, role):
        rel = os.path.relpath(full, ROOT)
        key = "file:" + rel
        if any(s["key"] == key for s in ent(eid)["sources"]):
            return
        name = os.path.basename(full)
        size = os.path.getsize(full)
        if size > 40 * 1024 * 1024:
            add_source(eid, key, name, "skipped", rel, role, {"n": 0, "note": "file over 40 MB; not bundled", "size": size})
            return
        low = name.lower()
        try:
            if name.endswith(".jsonl"):
                recs = load_jsonl(full)
                kind = "runs" if "/runs/" in rel else "analysis"
                add_source(eid, key, name, kind, rel, role, {"n": len(recs), "_records": recs, "size": size})
            elif name.endswith(".json"):
                o = load_json(full)
                kind = "judgments" if re.search(r"judg|cache|label|verdict|confirm|match", low) else ("items" if rel.startswith("docs/") else "analysis")
                if isinstance(o, list):
                    add_source(eid, key, name, kind, rel, role, {"n": len(o), "_records": o, "size": size})
                elif isinstance(o, dict):
                    # a dict whose values are lists of records → expose the main list; else keyed entries
                    listy = [(k, v) for k, v in o.items() if isinstance(v, list) and v and isinstance(v[0], dict)]
                    if listy and len(o) <= 6:
                        k, v = max(listy, key=lambda kv: len(kv[1]))
                        meta = {kk: vv for kk, vv in o.items() if kk != k}
                        add_source(eid, key, name, kind, rel, role, {"n": len(v), "_records": v, "meta": meta, "list_key": k, "size": size})
                    else:
                        add_source(eid, key, name, kind, rel, role, {"n": len(o), "_keyed": o, "size": size})
                else:
                    add_source(eid, key, name, "json", rel, role, {"n": 1, "json": o, "size": size})
            elif name.endswith((".txt", ".md")):
                add_source(eid, key, name, "report", rel, role, {"n": 1, "text": open(full, encoding="utf-8", errors="ignore").read(), "size": size})
        except Exception as ex:  # noqa
            add_source(eid, key, name, "skipped", rel, role, {"n": 0, "note": "could not parse: %s" % ex, "size": size})

    # ---- imported traces grouped by mode
    imported = sorted(glob.glob(os.path.join(ROOT, "bench", "runs", "imported", "*.json")))
    by_mode = {}
    for f in imported:
        try:
            o = load_json(f)
        except Exception:
            continue
        by_mode.setdefault(o.get("mode", "?"), []).append((os.path.basename(f), o))
    mode_counts = {m: len(v) for m, v in by_mode.items()}

    def attach_traces(eid, modes, role, note=None):
        for m in modes:
            runs = by_mode.get(m)
            if not runs:
                continue
            key = "traces:" + m
            add_source(eid, key, "Conversations in the %s setup" % m, "traces", "bench/runs/imported/*__" + m + ".json", role,
                       {"n": len(runs), "_runs": runs, "note": note})

    for m in by_mode:
        owner = mode_owner(m)
        if owner == "@dose":
            if dose_id:
                attach_traces(dose_id, [m], "produced")
        elif owner == "@baseline":
            attach_traces(baseline_id, [m], "produced")
        elif owner:
            attach_traces(owner, [m], "produced")
            if owner == "2":
                attach_traces("1", [m], "shared", "Cell 1's result used one run per scenario from these setups. The notebook does not say which of the repeats it used.")

    # ---- scripts: prompts, referenced modes and paths
    def cell_key(cid):
        return cid.replace("-R", "R")

    script_map = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "train", "*cell*"))):
        b = os.path.basename(f)
        m = re.search(r"cell(\d+[A-Za-z]?R?|IV)(?![0-9A-Za-z])", b)
        if not m:
            continue
        k = m.group(1)
        cid = k[:-1] + "-R" if k.endswith("R") and k[:-1] + "-R" in cells else k
        cid = {"8b": "8B"}.get(cid, cid)
        if cid not in cells:
            continue
        script_map.setdefault(cid, []).append(f)

    for cid, files in script_map.items():
        for f in files:
            rel = os.path.relpath(f, ROOT)
            src = open(f, encoding="utf-8", errors="ignore").read()
            if f.endswith(".py"):
                ps, imps = script_prompts(f, set())
                models = [x for x in imps if isinstance(x, dict)]
                imps = [x for x in imps if isinstance(x, str)]
                for p in ps:
                    ent(cid)["prompts"].append({**p, "path": rel})
                for modname in imps:
                    for p in module_prompts(modname):
                        if not any(q["name"] == p["name"] and q.get("path") == p["path"] for q in ent(cid)["prompts"]):
                            ent(cid)["prompts"].append({**p, "kind": "imported constant"})
                if models and models[0]["models"]:
                    ent(cid)["notes"].append({"script": rel, "models": models[0]["models"]})
            else:
                head = src[:1500]
                ent(cid)["prompts"].append({"name": os.path.basename(f), "text": src if len(src) < 6000 else head + "\n…", "kind": "shell script", "path": rel, "line": 1})
            # modes referenced that exist in the imported corpus → reused traces
            refs = sorted(set(re.findall(r"[\"']((?:cell|c|arch|reg|local-council)[\w-]*)[\"']", src)))
            reused = [m for m in refs if m in by_mode and mode_owner(m) != cid]
            attach_traces(cid, reused, "referenced by script")
            # explicit paths referenced
            for p in sorted(set(re.findall(r"(?:bench|docs)/[\w./-]+", src))):
                if "imported" in p or re.fullmatch(r"(?:bench|docs)/?(?:runs|analysis)?/?", p):
                    continue
                full = os.path.join(ROOT, p.rstrip("."))
                if os.path.isdir(full):
                    for g in sorted(os.listdir(full)):
                        attach_file(cid, os.path.join(full, g), "referenced by script")
                elif os.path.isfile(full) and "imported" not in p:
                    attach_file(cid, full, "referenced by script")

    # ---- per-entity files: bench/runs/cell*.jsonl, bench/analysis/cell*/, docs/CELL*_*.json
    for cid in cells:
        k = cell_key(cid)
        for f in sorted(glob.glob(os.path.join(ROOT, "bench", "runs", "cell%s_*.jsonl" % k)) + glob.glob(os.path.join(ROOT, "bench", "runs", "cell%s.jsonl" % k))):
            attach_file(cid, f, "produced")
        for d in sorted(glob.glob(os.path.join(ROOT, "bench", "analysis", "cell%s" % k)) + glob.glob(os.path.join(ROOT, "bench", "analysis", "cell%s_*" % k))):
            if os.path.isdir(d):
                for g in sorted(os.listdir(d)):
                    attach_file(cid, os.path.join(d, g), "produced")
            else:
                attach_file(cid, d, "produced")
        for f in sorted(glob.glob(os.path.join(ROOT, "docs", "CELL%s_*.json" % k.upper()))):
            attach_file(cid, f, "frozen items")
    # c30c31 shared analysis
    for cid in ("30", "31"):
        d = os.path.join(ROOT, "bench", "analysis", "c30c31")
        if os.path.isdir(d):
            for g in sorted(os.listdir(d)):
                attach_file(cid, os.path.join(d, g), "produced (shared c30c31)")
    # program-level analysis folders
    for dname, kw in ANALYSIS_DIR_RULES.items():
        pid = program_id(kw)
        d = os.path.join(ROOT, "bench", "analysis", dname)
        if pid and os.path.isdir(d):
            for g in sorted(os.listdir(d)):
                attach_file(pid, os.path.join(d, g), "produced")
    nli = os.path.join(ROOT, "bench", "analysis", "nli_adjudication.json")
    if os.path.exists(nli):
        attach_file("7a", nli, "produced")
    # cell IV script + others without 'cell' in analysis dir name are covered by the glob above (cellIV)

    # ---- shared: cases and council prompts
    sys.path.insert(0, ROOT)
    cases = []
    try:
        from examples.test_cases import CASES  # type: ignore
        for c in CASES:
            cases.append({"id": c.id, "title": c.title, "prompt": c.prompt,
                          "rubric": [{"seat": r.seat, "description": r.description, "severity": r.severity} for r in (c.rubric or [])],
                          "expected_routes": list(getattr(c, "expected_routes", []) or []), "failure_mode": getattr(c, "failure_mode", None)})
    except Exception as ex:  # noqa
        cases = [{"id": "?", "title": "could not import examples.test_cases: %s" % ex, "prompt": "", "rubric": []}]
    council_prompts = module_prompts("council.prompts")

    # ---- write chunks
    manifest = {}
    total = 0
    for eid, e in entities.items():
        T = Table()
        sources = []
        for s in e["sources"]:
            out = {k: v for k, v in s.items() if not k.startswith("_")}
            if "_runs" in s:
                recs = [normalize_trace(o, fname, T) for fname, o in s["_runs"]]
                out["records"] = recs
                out["fields"] = field_summary(recs)
            elif "_records" in s:
                recs = s["_records"]
                out["fields"] = field_summary(recs) if recs and isinstance(recs[0], dict) else []
                out["records"] = T.walk(recs)
                if "meta" in out:
                    out["meta"] = T.walk(out["meta"])
            elif "_keyed" in s:
                out["keyed"] = T.walk(s["_keyed"])
                out["keys"] = list(s["_keyed"].keys())
            elif "text" in s:
                out["text"] = s["text"]
            elif "json" in s:
                out["json"] = s["json"]
            sources.append(out)
        # link keyed sources to run records by run_id substring
        keyed = [s for s in sources if "keys" in s]
        for s in sources:
            if "records" not in s or s["kind"] == "traces":
                continue
            for r in s["records"]:
                rid = r.get("run_id") if isinstance(r, dict) else None
                if not rid or not isinstance(rid, str):
                    continue
                links = {}
                for ks in keyed:
                    hits = [k for k in ks["keys"] if rid in k]
                    if hits:
                        links[ks["key"]] = hits[:60]
                if links:
                    r["$links"] = links
        order = {"traces": 0, "runs": 1, "items": 2, "judgments": 3, "analysis": 4, "report": 5, "json": 6, "skipped": 9}
        sources.sort(key=lambda s: (order.get(s["kind"], 8), s["path"]))
        chunk = {"entity": eid, "sources": sources, "prompts": e["prompts"], "notes": e["notes"], "strings": T.strings}
        raw = json.dumps(chunk, ensure_ascii=False).encode("utf-8")
        gz = gzip.compress(raw, 9)
        b64 = base64.b64encode(gz).decode("ascii")
        fname = "cell_%s.js" % re.sub(r"[^A-Za-z0-9]+", "_", eid)
        with open(os.path.join(DATA_DIR, fname), "w", encoding="utf-8") as fh:
            fh.write('window.__ledgerChunk(%s,"%s");' % (json.dumps(eid), b64))
        size = len(b64) + 40
        total += size
        manifest[eid] = {
            "file": "data/" + fname, "bytes": size, "raw_bytes": len(raw),
            "sources": [{"key": s["key"], "title": s.get("title"), "kind": s["kind"], "n": s.get("n", 0), "role": s.get("role"), "path": s["path"]} for s in sources],
            "n_prompts": len(e["prompts"]),
            "n_traces": sum(s.get("n", 0) for s in sources if s["kind"] == "traces"),
            "n_records": sum(s.get("n", 0) for s in sources if s["kind"] in ("runs", "analysis", "items", "judgments")),
        }
        print("  %-18s %6.1f MB raw → %5.2f MB chunk  sources=%d prompts=%d" % (eid, len(raw) / 2**20, size / 2**20, len(sources), len(e["prompts"])))
    shared = {"cases": cases, "council_prompts": council_prompts, "mode_counts": mode_counts}
    sraw = json.dumps(shared, ensure_ascii=False).encode("utf-8")
    sb64 = base64.b64encode(gzip.compress(sraw, 9)).decode("ascii")
    with open(os.path.join(DATA_DIR, "shared.js"), "w", encoding="utf-8") as fh:
        fh.write('window.__ledgerChunk("shared","%s");' % sb64)
    total += len(sb64)
    print("data total: %.1f MB across %d chunks" % (total / 2**20, len(manifest) + 1))
    return manifest


if __name__ == "__main__":
    ledger = json.load(open(os.path.join(HERE, "ledger.json"), encoding="utf-8"))
    m = build(ledger)
    json.dump(m, open(os.path.join(HERE, "data_manifest.json"), "w"), indent=1)
