"""Cell 62 — do the sentence judges agree with a person?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 62 PRE-REGISTRATION".

The two-judge sentence instrument (Cell IV) was accepted on raw agreement.
The board review found its chance-corrected agreement to be 0.19-0.41 on the
saved answers and that no label had ever been compared with a human one.
This cell compares it, and four added local judges, with blind labels from
one person (the author), on a stratified sample of 400 stored sentences.

Stages
  sample    draw the 400 sentences (seeded) from the stored, already-judged
            sentences of Cells 30/31, 41 and 46; write the blind labelling
            task and its key. No model call.
  judge     six local judges label the same 400 sentences in batches of ten
            (the frozen Cell IV prompt).
  measure   needs the person's labels (train/label_blind.py). Scores the
            deployed rule and the candidate rules against them.

Run:  .venv/bin/python train/run_cell62_instrument.py sample
      .venv/bin/python train/run_cell62_instrument.py smoke      (anchor sentences only)
      .venv/bin/python train/run_cell62_instrument.py judge
      .venv/bin/python train/label_blind.py bench/labels/cell62_sentences
      .venv/bin/python train/run_cell62_instrument.py measure
"""
from __future__ import annotations

import collections
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                              # noqa: E402
from gst.smallcluster import kappa, prf                             # noqa: E402
from train.cell23_presence_calib import ANCHORS, DEFS               # noqa: E402
from train.run_cellIV_batchjudge import ALL_FAMS, PROMPT, parse     # noqa: E402

REGISTRATION = runlog.registration_for("62", ROOT)
AN = ROOT / "bench" / "analysis"
OUT = AN / "cell62"
TASK = ROOT / "bench" / "labels" / "cell62_sentences"
CALLS = ROOT / "bench" / "runs" / "cell62_judge_calls.jsonl"
SEED = 62
FAMS = ("modeled", "hedging", "jurisd")     # priority order for strata: rarest first
STORED = ("gpt-oss:20b", "qwen2.5:7b-instruct")
JUDGES = ("gpt-oss:20b", "qwen2.5:7b-instruct", "phi4:14b",
          "qwen3-vl:30b-a3b-instruct", "llama3:8b-instruct-q4_K_M",
          "mistral:7b-instruct-v0.3-q4_K_M")
BIG3 = ("gpt-oss:20b", "phi4:14b", "qwen3-vl:30b-a3b-instruct")
N_FLAGGED_CELL = 17          # per (construct, both/one, source): 12 cells, about 200 in all
N_UNFLAGGED_CELL = 100       # per source: 2 cells
BATCH = 10


# ------------------------------------------------------------------ pool

def _pool() -> list[dict]:
    """Every stored sentence that both instrument judges labelled, once."""
    from train.run_cell46_writer_replication import split_sentences
    rows = []

    lab = json.loads((AN / "cell41" / "labels.json").read_text())
    for rid, e in lab.items():
        for i, s in enumerate(e["sentences"]):
            la, lb = e["judges"][STORED[0]].get(str(i)), e["judges"][STORED[1]].get(str(i))
            if la is not None and lb is not None:
                rows.append({"text": s, "source": "editor", "cell": "41", "a": la, "b": lb})

    lab = json.loads((AN / "cell46" / "labels.json").read_text())
    variants = json.loads((AN / "cell46" / "variants.json").read_text())
    vtext = {f"{v['case']}__v{v['variant_id']}":
             [s for t in v["upstream"] if t for s in split_sentences(t)] for v in variants}
    outs = {r["run_id"]: r["output"] for r in runlog.read_jsonl(ROOT / "bench" / "runs" / "cell46_writer.jsonl")}
    for k, e in lab.items():
        if k.startswith("UP::"):
            sents, src = vtext.get(k[4:], []), "specialist"
        else:
            sents, src = split_sentences(outs.get(k[5:], "")), "editor"
        a, b = e["judges"].get(STORED[0], {}), e["judges"].get(STORED[1], {})
        for i in range(min(e["n"], len(sents))):
            la, lb = a.get(str(i)), b.get(str(i))
            if la is not None and lb is not None:
                rows.append({"text": sents[i], "source": src, "cell": "46", "a": la, "b": lb})

    units = json.loads((AN / "c30c31" / "units.json").read_text())
    lab = json.loads((AN / "c30c31" / "labels.json").read_text())
    flat = [(s, u["kind"]) for u in units for s in u["sentences"]]
    for off in sorted({int(k.split("|")[1]) for k in lab}):
        a, b = lab.get(f"{STORED[0]}|{off}"), lab.get(f"{STORED[1]}|{off}")
        if not a or not b:
            continue
        for pos in range(1, BATCH + 1):
            i = off + pos - 1
            if i >= len(flat):
                break
            la, lb = a.get(str(pos)), b.get(str(pos))
            if la and lb:
                rows.append({"text": flat[i][0], "source": "specialist" if flat[i][1] == "upstream" else "editor",
                             "cell": "30/31", "a": la, "b": lb})
    seen, out = set(), []
    for r in rows:
        t = r["text"].strip()
        if t in seen or not (25 <= len(t) <= 400) or "\n" in t:
            continue
        seen.add(t)
        r["text"] = t
        out.append(r)
    return out


def _stratum(r: dict) -> str:
    for f in FAMS:
        if r["a"].get(f) and r["b"].get(f):
            return f"{f}|both|{r['source']}"
    for f in FAMS:
        if r["a"].get(f) or r["b"].get(f):
            return f"{f}|one|{r['source']}"
    return f"none|none|{r['source']}"


def stage_sample() -> None:
    pool = _pool()
    by = collections.defaultdict(list)
    for r in pool:
        by[_stratum(r)].append(r)
    rng = random.Random(SEED)
    items, key, strata = [], {}, {}
    for name in sorted(by):
        rows = sorted(by[name], key=lambda r: hashlib.sha256(r["text"].encode()).hexdigest())
        want = N_UNFLAGGED_CELL if name.startswith("none") else N_FLAGGED_CELL
        take = rng.sample(rows, min(want, len(rows)))
        strata[name] = {"pool": len(rows), "sampled": len(take)}
        for r in take:
            sid = "s" + hashlib.sha256(f"{SEED}|{r['text']}".encode()).hexdigest()[:8]
            items.append({"id": sid, "text": r["text"]})
            key[sid] = {"stratum": name, "source": r["source"], "cell": r["cell"],
                        "stored": {STORED[0]: {f: bool(r["a"].get(f)) for f in FAMS},
                                   STORED[1]: {f: bool(r["b"].get(f)) for f in FAMS}}}
    items.sort(key=lambda it: it["id"])
    print(f"pool: {len(pool)} distinct labelled sentences; sample: {len(items)}")
    for name, s in sorted(strata.items()):
        print(f"  {name:<28} pool {s['pool']:>6}  sampled {s['sampled']:>4}")
    TASK.mkdir(parents=True, exist_ok=True)
    practice = [{"id": f"anchor{i}", "text": t,
                 "intended": ", ".join(sorted(f for f in truth if f in FAMS)) or "none of the three"}
                for i, (t, truth) in enumerate(ANCHORS)]
    task = {
        "task": "cell62_sentences", "kind": "sentence_constructs", "retest_gap_days": 7,
        "intro": ("You will see one sentence at a time, taken from saved specialist texts and "
                  "editor answers. For each sentence, switch on every property it has. Judge only "
                  "what the sentence itself does, in any wording. Most sentences have none."),
        "instructions": "Which of these does the sentence do? Press a number to switch it on or off.",
        "definitions": {f: DEFS[f] for f in ("modeled", "jurisd", "hedging")},
        "items": items, "practice": practice}
    (TASK / "task.json").write_text(json.dumps(task, indent=1, ensure_ascii=False))
    (TASK / "key.json").write_text(json.dumps({"seed": SEED, "strata": strata, "items": key}, indent=1))
    print(f"wrote {TASK}/task.json ({len(items)} items) and key.json (do not open while labelling)")


# ------------------------------------------------------------------ judging

def _judge_chunk(judge: str, sentences: list[str], tag: str) -> dict | None:
    body = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    prompt = PROMPT.format(n=len(sentences), items=body,
                           defs="\n".join(f"- {f}: {DEFS[f]}" for f in ALL_FAMS))
    for attempt in range(2):
        text, meta = runlog.chat_logged(judge, None, prompt, temperature=0.0, max_tokens=4096,
                                        seed=runlog.seed_for(tag) + attempt)
        res = parse(text, len(sentences))
        if not tag.startswith("SMOKE"):          # smoke calls are not part of the cell's record
            runlog.append_jsonl(CALLS, runlog.stamp(
                {"tag": tag, "judge": judge, "n": len(sentences), "attempt": attempt, "parsed": res is not None},
                meta, root=ROOT, script=Path(__file__), registration=REGISTRATION))
        if res is not None:
            return res
    return None


def judge_sentences(judge: str, items: list[dict], store: dict, prefix: str) -> int:
    """Fills store[id] = {construct: bool}. Batches of ten; a batch that will
    not parse is retried once, then split into two batches of five."""
    fails = 0
    for start in range(0, len(items), BATCH):
        chunk = [it for it in items[start:start + BATCH] if it["id"] not in store]
        if not chunk:
            continue
        res = _judge_chunk(judge, [c["text"] for c in chunk], f"{prefix}|{judge}|{start}")
        if res is not None:
            for i, c in enumerate(chunk):
                store[c["id"]] = res[i + 1]
            continue
        half = (len(chunk) + 1) // 2
        for part, sub in enumerate((chunk[:half], chunk[half:])):
            if not sub:
                continue
            res = _judge_chunk(judge, [c["text"] for c in sub], f"{prefix}|{judge}|{start}|half{part}")
            if res is None:
                fails += len(sub)
                continue
            for i, c in enumerate(sub):
                store[c["id"]] = res[i + 1]
    return fails


def stage_smoke() -> None:
    """Parse and timing check on the 20 anchor sentences (not in the sample)."""
    items = [{"id": f"anchor{i}", "text": t} for i, (t, _) in enumerate(ANCHORS)]
    for judge in JUDGES:
        store: dict = {}
        t0 = time.time()
        fails = judge_sentences(judge, items, store, "SMOKE")
        ok = sum(1 for i, (_, truth) in enumerate(ANCHORS) for f in FAMS
                 if f"anchor{i}" in store and store[f"anchor{i}"][f] == (f in truth))
        print(f"  {judge:<34} labelled {len(store)}/20, unparsed {fails}, "
              f"anchor decisions right {ok}/{3*len(store)}, {time.time()-t0:.0f}s", flush=True)


def stage_judge() -> None:
    task = json.loads((TASK / "task.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "judge_labels.json"
    labels = json.loads(path.read_text()) if path.exists() else {}
    for judge in JUDGES:
        store = labels.setdefault(judge, {})
        t0 = time.time()
        fails = judge_sentences(judge, task["items"], store, "cell62")
        path.write_text(json.dumps(labels))
        print(f"cell62 judge {judge}: {len(store)}/{len(task['items'])} labelled, "
              f"{fails} unparsed, {time.time()-t0:.0f}s", flush=True)
    print("cell62 judging complete")


# ------------------------------------------------------------------ measure

RULES = {            # candidate rules: name -> (judges needed, decision from those judges' labels)
    "gpt-oss alone": (("gpt-oss:20b",), lambda v: v[0]),
    "qwen2.5 alone": (("qwen2.5:7b-instruct",), lambda v: v[0]),
    "phi4 alone": (("phi4:14b",), lambda v: v[0]),
    "qwen3-vl alone": (("qwen3-vl:30b-a3b-instruct",), lambda v: v[0]),
    "llama3 alone": (("llama3:8b-instruct-q4_K_M",), lambda v: v[0]),
    "mistral alone": (("mistral:7b-instruct-v0.3-q4_K_M",), lambda v: v[0]),
    "instrument pair re-judged, both": (STORED, all),
    "instrument pair re-judged, either": (STORED, any),
    "three largest, at least two": (BIG3, lambda v: sum(v) >= 2),
    "all six, at least two": (JUDGES, lambda v: sum(v) >= 2),
    "all six, at least three": (JUDGES, lambda v: sum(v) >= 3),
    "all six, at least four": (JUDGES, lambda v: sum(v) >= 4),
}
MIN_POSITIVES = 15


def _weighted_prf(rows, pred) -> dict:
    tp = sum(r["w"] for r in rows if r["truth"] and pred(r))
    fp = sum(r["w"] for r in rows if not r["truth"] and pred(r))
    fn = sum(r["w"] for r in rows if r["truth"] and not pred(r))
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if tp else 0.0
    return {"precision": prec, "recall": rec, "f1": f1}


def _boot(rows, pred, draws=2000) -> dict:
    rng = random.Random(SEED)
    by = collections.defaultdict(list)
    for r in rows:
        by[r["stratum"]].append(r)
    vals = collections.defaultdict(list)
    for _ in range(draws):
        s = [x for g in by.values() for x in (g[rng.randrange(len(g))] for _ in g)]
        m = _weighted_prf(s, pred)
        for k, v in m.items():
            if v == v:
                vals[k].append(v)
    out = {}
    for k, v in vals.items():
        v.sort()
        out[k] = (v[int(.025 * len(v))], v[int(.975 * len(v)) - 1])
    return out


def _committed(path: Path) -> bool:
    r = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", str(path)],
                       capture_output=True, text=True)
    t = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--error-unmatch", str(path)],
                       capture_output=True, text=True)
    return t.returncode == 0 and r.stdout.strip() == ""


def dawid_skene(votes: list[list[bool]], iters: int = 200) -> dict:
    """Two-class latent-class model: estimates prevalence and each rater's
    hit and false-alarm rate without any reference labels. A check that does
    not use the person's labels; it assumes raters err independently."""
    n, k = len(votes), len(votes[0])
    post = [sum(v) / k for v in votes]
    for _ in range(iters):
        prev = min(max(sum(post) / n, 1e-6), 1 - 1e-6)
        hit = [(sum(p for p, v in zip(post, votes) if v[j]) + 0.5) / (sum(post) + 1) for j in range(k)]
        fa = [(sum(1 - p for p, v in zip(post, votes) if v[j]) + 0.5) / (n - sum(post) + 1) for j in range(k)]
        new = []
        for v in votes:
            a, b = prev, 1 - prev
            for j in range(k):
                a *= hit[j] if v[j] else 1 - hit[j]
                b *= fa[j] if v[j] else 1 - fa[j]
            new.append(a / (a + b) if a + b else 0.5)
        if max(abs(x - y) for x, y in zip(new, post)) < 1e-9:
            post = new
            break
        post = new
    return {"prevalence": sum(post) / n, "hit": hit, "false_alarm": fa}


def stage_measure(allow_uncommitted: bool = False) -> None:
    from train.label_blind import done_info, read_labels
    task = json.loads((TASK / "task.json").read_text())
    key = json.loads((TASK / "key.json").read_text())
    p1 = TASK / "labels_pass1.jsonl"
    if not done_info(TASK, 1):
        raise SystemExit("Pass 1 of the blind labels is not finished: "
                         ".venv/bin/python train/label_blind.py bench/labels/cell62_sentences")
    if not allow_uncommitted and not _committed(p1):
        raise SystemExit("Commit the pass-1 labels before scoring (the tool printed the command).")
    human1 = {k: v["label"] for k, v in read_labels(p1).items()}
    human2 = ({k: v["label"] for k, v in read_labels(TASK / "labels_pass2.jsonl").items()}
              if done_info(TASK, 2) else None)
    jl = json.loads((OUT / "judge_labels.json").read_text())
    ids = [it["id"] for it in task["items"]]
    strata = key["strata"]
    kinds = ("modeled", "jurisd", "hedging")
    print("=" * 78)
    print("CELL 62 — do the sentence judges agree with a person?")
    print("=" * 78)
    print(f"sample {len(ids)} sentences; person's labels: pass 1" + (" and pass 2" if human2 else " only (INTERIM read)"))
    result = {"interim": human2 is None, "constructs": {f: {} for f in kinds}}

    print("\nP62.0  the person against themself, a week apart")
    for f in kinds:
        if human2:
            k = kappa([(human1[i][f], human2[i][f]) for i in ids])
            print(f"  {f:<8} raw {k['raw']:.3f}  kappa {k['kappa']:.3f}  positives {k['pos_a']:.3f}/{k['pos_b']:.3f}")
            result["constructs"][f]["retest_kappa"] = k["kappa"]
        else:
            print(f"  {f:<8} pending (pass 2 not done)")

    missing = {j: sum(1 for i in ids if i not in jl.get(j, {})) for j in JUDGES}
    usable = [j for j in JUDGES if missing[j] <= 0.2 * len(ids)]
    print("\njudge coverage (a judge missing more than 20% of sentences is left out of the candidate rules):")
    for j in JUDGES:
        print(f"  {j:<34} unlabelled {missing[j]}/{len(ids)}" + ("" if j in usable else "  LEFT OUT"))
    rules = {n: (need, fn) for n, (need, fn) in RULES.items() if all(j in usable for j in need)}
    half_a = set(ids[0::2])              # ids are hash-ordered, so this split is arbitrary and fixed

    def rule_pred(need, fn, f):
        def pred(r):
            if any(j not in r["L"] for j in need):
                return False
            return bool(fn([bool(r["L"][j][f]) for j in need]))
        return pred

    print("\nP62.1 / P62.2  rules against the person's pass-1 labels (weighted back to the stored pool)")
    for f in kinds:
        rows = []
        for i in ids:
            k = key["items"][i]
            st_ = strata[k["stratum"]]
            rows.append({"id": i, "stratum": k["stratum"], "w": st_["pool"] / st_["sampled"],
                         "truth": bool(human1[i][f]), "stored_both": all(k["stored"][j][f] for j in STORED),
                         "L": {j: jl[j][i] for j in JUDGES if i in jl.get(j, {})}})
        dep = _weighted_prf(rows, lambda r: r["stored_both"])
        ci = _boot(rows, lambda r: r["stored_both"])
        n_pos = sum(r["truth"] for r in rows)
        n_pos_b = sum(r["truth"] for r in rows if r["id"] not in half_a)
        print(f"\n  {f}: the person marked {n_pos} of {len(rows)} sampled sentences ({n_pos_b} in the second half)")
        print(f"    deployed rule (stored labels, both judges)  precision {dep['precision']:.3f} "
              f"[{ci['precision'][0]:.3f}, {ci['precision'][1]:.3f}]  recall {dep['recall']:.3f} "
              f"[{ci['recall'][0]:.3f}, {ci['recall'][1]:.3f}]  F1 {dep['f1']:.3f} [{ci['f1'][0]:.3f}, {ci['f1'][1]:.3f}]")
        res = {"n_positive": n_pos, "n_positive_second_half": n_pos_b, "deployed": dep, "deployed_ci": ci, "rules": {}}
        for name, (need, fn) in rules.items():
            pred = rule_pred(need, fn, f)
            cal = _weighted_prf([r for r in rows if r["id"] in half_a], pred)
            tst = _weighted_prf([r for r in rows if r["id"] not in half_a], pred)
            res["rules"][name] = {"calibration": cal, "test": tst}
            print(f"    {name:<36} first half F1 {cal['f1']:.3f}   second half P {tst['precision']:.3f} "
                  f"R {tst['recall']:.3f} F1 {tst['f1']:.3f}")
        result["constructs"][f].update(res)

    best = max(rules, key=lambda n: sum(result["constructs"][f]["rules"][n]["calibration"]["f1"] for f in kinds))
    result["chosen_rule"] = best
    print(f"\n  rule chosen on the first half (highest mean F1 over the three kinds): {best}")

    print("\nreported without a pass/fail")
    print("  each instrument judge against its own stored label, same sentence, new batch:")
    for j in STORED:
        if j not in usable:
            continue
        for f in kinds:
            k = kappa([(key["items"][i]["stored"][j][f], bool(jl[j][i][f])) for i in ids if i in jl[j]])
            print(f"    {j:<24} {f:<8} raw {k['raw']:.3f}  kappa {k['kappa']:.3f}")
    print("  kappa between judges (new labels):")
    for f in kinds:
        cells = []
        for x, a_ in enumerate(usable):
            for b_ in usable[x + 1:]:
                k = kappa([(bool(jl[a_][i][f]), bool(jl[b_][i][f])) for i in ids if i in jl[a_] and i in jl[b_]])
                cells.append(k["kappa"])
        if cells:
            print(f"    {f:<8} lowest {min(cells):.3f}  median {sorted(cells)[len(cells)//2]:.3f}  highest {max(cells):.3f}  ({len(cells)} pairs of judges)")
    print("  latent-class estimate (no human labels; assumes the judges err independently):")
    for f in kinds:
        votes = [[bool(jl[j][i][f]) for j in usable] for i in ids if all(i in jl[j] for j in usable)]
        ds = dawid_skene(votes)
        print(f"    {f:<8} share positive in the sample {ds['prevalence']:.3f}; hit rates "
              + ", ".join(f"{j.split(':')[0]} {h:.2f}" for j, h in zip(usable, ds["hit"])))

    v0, v1, v2, detail = [], [], [], []
    for f in kinds:
        c = result["constructs"][f]
        if c["n_positive"] < MIN_POSITIVES:
            detail.append(f"  {f}: not evaluable, the person marked {c['n_positive']} sentences (minimum {MIN_POSITIVES})")
            continue
        if human2 is not None:
            v0.append(c["retest_kappa"] >= 0.60)
            detail.append(f"  {f}: the person's two passes agree at kappa {c['retest_kappa']:.3f} (bar 0.60)")
            if c["retest_kappa"] < 0.60:
                detail.append(f"  {f}: the deployed rule and the chosen rule are not evaluable for this kind")
                continue
        f1 = c["deployed"]["f1"]
        v1.append(f1 >= 0.80)
        detail.append(f"  {f}: deployed rule F1 {f1:.3f} (bar 0.80), {'at or above' if f1 >= 0.80 else 'below'} the bar")
        if c["n_positive_second_half"] < MIN_POSITIVES:
            detail.append(f"  {f}: chosen rule not evaluable on the second half ({c['n_positive_second_half']} positives)")
        else:
            t = c["rules"][best]["test"]["f1"]
            v2.append(t >= 0.80)
            detail.append(f"  {f}: chosen rule F1 on the second half {t:.3f} (bar 0.80), {'at or above' if t >= 0.80 else 'below'} the bar")
    word = lambda v: "NOT EVALUABLE" if not v else "SUPPORTED" if all(v) else "FALSIFIED"      # noqa: E731
    gate = "PENDING (pass 2 not done)" if human2 is None else ("NOT EVALUABLE" if not v0 else "PASSES" if all(v0) else "FAILS")
    print("\nVERDICT LINES (as registered)" + ("  — INTERIM, pass 2 pending" if human2 is None else ""))
    print(f"  P62.0 {gate} — the person's two passes agree at kappa 0.60 or better for {sum(v0)} of {len(v0)} evaluable kinds")
    print(f"  P62.1 {word(v1)} — the deployed rule reaches F1 0.80 for {sum(v1)} of {len(v1)} evaluable kinds")
    print(f"  P62.2 {word(v2)} — the chosen rule ({best}) reaches F1 0.80 on the second half for {sum(v2)} of {len(v2)} evaluable kinds")
    print("\n".join(detail))
    result["P62.0"], result["P62.1"], result["P62.2"] = gate, word(v1), word(v2)
    (OUT / "measured.json").write_text(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "sample"
    if stage == "measure":
        stage_measure("--allow-uncommitted" in sys.argv)
    else:
        {"sample": stage_sample, "smoke": stage_smoke, "judge": stage_judge}[stage]()
