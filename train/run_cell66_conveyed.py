"""Cell 66 — are caveats lost more than ordinary content?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 66 PRE-REGISTRATION".

Cell 48's corrected figure says 3.0% of the specialists' caveat sentences
appear word for word in the editor's answer. Word-for-word matching misses
paraphrase, and a low figure means little by itself: the editor shortens
everything to about 30% of the input. This cell asks the comparative
question. For each caveat sentence the editor received, and for an ordinary
sentence of matching length from the same specialist text, is the content
conveyed in the editor's answer?

Material (all stored, nothing is generated): the Cell 41 control answers,
repeats 0-2, for the 17 scenarios that have caveat sentences; the specialist
sentences and their stored two-judge labels (Cells 30/31 and 46).

Instrument: the three answer sentences closest to the statement (embedding
similarity) are shown to two judges, who answer FULLY / PARTLY / NO. A
statement counts as conveyed when both judges answer FULLY or PARTLY. The
rule is checked against one person's blind labels on 120 pairs before the
comparison is read (P66.0).

Stages
  build       pick the sentences and their matches (no model call)
  shortlist   embeddings: the three closest answer sentences per pair
              (`shortlist smoke` does only the two smoke pairs)
  smoke       two pairs on repeat 6, which the cell does not use
  judge       two judges on every pair
  sample      draw the 120 pairs for blind labelling (after judging)
  misscheck   a judge reads the whole answer for 60 pairs the rule called
              not conveyed, to estimate what the shortlist misses
  measure
"""
from __future__ import annotations

import collections
import hashlib
import json
import math
import random
import re
import statistics as st
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                              # noqa: E402
from gst.smallcluster import kappa, sign_flip_p, t_interval         # noqa: E402

REGISTRATION = runlog.registration_for("66", ROOT)
AN = ROOT / "bench" / "analysis"
OUT = AN / "cell66"
CALLS = ROOT / "bench" / "runs" / "cell66_conveyed.jsonl"
MISS = ROOT / "bench" / "runs" / "cell66_misscheck.jsonl"
TASK = ROOT / "bench" / "labels" / "cell66_conveyed"
STORED = ("gpt-oss:20b", "qwen2.5:7b-instruct")          # the judges whose labels define a caveat
FAMS = ("cutoff", "modeled", "jurisd", "hedging")
JUDGES = ("gpt-oss:20b", "qwen3-vl:30b-a3b-instruct")
EMBED = "nomic-embed-text"
REPS = (0, 1, 2)
SMOKE_REP = 6
TOP = 3
MIN_CAVEATS = 5              # a scenario enters the main comparison with at least this many
BAND = 0.10
SEED = 66
MAX_TOKENS = 2048

PROMPT = """You are checking whether one statement from a specialist's note is conveyed in an editor's final answer.

STATEMENT (from the specialist):
{statement}

{label}:
{passages}

Is the content of the STATEMENT conveyed there? Judge the content, not the wording: a paraphrase counts; a mere mention of the same topic does not.

FULLY  - the main point of the statement is conveyed, including its condition or limit if it has one.
PARTLY - part of the point is conveyed, but a condition, limit, number or scope is dropped or changed.
NO     - the point is not conveyed.

Reply with exactly one line:
VERDICT: FULLY
or
VERDICT: PARTLY
or
VERDICT: NO"""
SHORT_LABEL = "PASSAGES (the parts of the editor's answer closest to the statement)"
FULL_LABEL = "THE EDITOR'S ANSWER (complete)"
CHOICES = {"fully": "FULLY: the main point is conveyed, including its condition or limit if it has one.",
           "partly": "PARTLY: part of the point is conveyed, but a condition, limit, number or scope is dropped or changed.",
           "no": "NO: the point is not conveyed (a mere mention of the same topic does not count)."}


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("*", "")).lower()


# ------------------------------------------------------------------ build

def _labelled_variants() -> dict[str, list[list[tuple]]]:
    """case -> list of variants; a variant is a list of (sentence, label_a, label_b)
    in the order Cell 48's two caveat functions visit them."""
    from train.run_cell46_writer_replication import split_sentences
    out: dict[str, list] = collections.defaultdict(list)
    units = json.loads((AN / "c30c31" / "units.json").read_text())
    lab = json.loads((AN / "c30c31" / "labels.json").read_text())
    flat = [(u, s) for u in units for s in u["sentences"]]
    per: dict[tuple, list] = collections.defaultdict(list)
    for off in sorted({int(k.split("|")[1]) for k in lab}):
        a, b = lab.get(f"{STORED[0]}|{off}"), lab.get(f"{STORED[1]}|{off}")
        if not a or not b:
            continue
        for pos in range(1, 11):
            i = off + pos - 1
            if i >= len(flat):
                break
            u, s = flat[i]
            if u["kind"] == "upstream" and a.get(str(pos)) and b.get(str(pos)):
                per[(u["key"][0], u["key"][1])].append((s, a[str(pos)], b[str(pos)]))
    for (case, _vid), rows in sorted(per.items()):
        out[case].append(rows)
    lab46 = json.loads((AN / "cell46" / "labels.json").read_text())
    variants = json.loads((AN / "cell46" / "variants.json").read_text())
    vtext = {f"{v['case']}__v{v['variant_id']}": [s for t in v["upstream"] if t for s in split_sentences(t)]
             for v in variants}
    old_cases = set(out)
    for k, e in lab46.items():
        if not k.startswith("UP::"):
            continue
        case = k[4:].rsplit("__v", 1)[0]
        if case in old_cases:
            continue
        sents = vtext.get(k[4:], [])
        a, b = (e["judges"].get(j, {}) for j in STORED)
        out[case].append([(sents[i], a[str(i)], b[str(i)]) for i in range(min(e["n"], len(sents)))
                          if a.get(str(i)) and b.get(str(i))])
    return out


def _is_caveat(la, lb) -> bool:
    return any(la.get(f) and lb.get(f) for f in FAMS)


def _is_clean(la, lb) -> bool:
    return not any(la.get(f) or lb.get(f) for f in FAMS)


def _wordy(s: str) -> bool:
    return len(s.strip()) >= 40 and len(re.findall(r"[A-Za-z]{2,}", s)) >= 6


def stage_build() -> None:
    import train.run_cell48_freight as c48
    ref = c48.old_case_caveats()
    ref.update({k: v for k, v in c48.new_case_caveats().items() if k not in ref})
    seats = json.loads((AN / "cell41" / "seats.json").read_text())
    lab41 = json.loads((AN / "cell41" / "labels.json").read_text())
    variants = _labelled_variants()
    cases, pairs, dropped = {}, [], collections.Counter()
    for case in sorted(ref):
        best = max(variants[case], key=lambda rows: sum(_is_caveat(a, b) for _, a, b in rows))
        cav = [s for s, a, b in best if _is_caveat(a, b)]
        assert [c.strip() for c in cav] == [c.strip() for c in ref[case]], f"{case}: caveat list differs from Cell 48's"
        seen_text = _norm("\n\n".join(seats[case].values()))
        seen = lambda s: _norm(s.strip()) in seen_text                 # noqa: E731
        clean = [s.strip() for s, a, b in best if _is_clean(a, b) and _wordy(s) and seen(s)]
        clean = list(dict.fromkeys(clean))
        used, rows = set(), []
        for n, c in enumerate(cav):
            c = c.strip()
            if not seen(c):
                dropped["caveat not found in the text the editor received"] += 1
                continue
            cand = [(abs(len(x) - len(c)), i) for i, x in enumerate(clean) if i not in used and x != c]
            if not cand:
                dropped["no ordinary sentence left to match"] += 1
                continue
            _, i = min(cand)
            used.add(i)
            rows.append({"n": n, "caveat": c, "ordinary": clean[i]})
        cases[case] = {"n_caveats_cell48": len(cav), "n_matched": len(rows), "n_clean_available": len(clean)}
        for r in rows:
            for kind in ("caveat", "ordinary"):
                sid = f"{case}|{kind[0]}{r['n']}"
                for rep in list(REPS) + [SMOKE_REP]:
                    assert f"{case}__control__r{rep}" in lab41
                    pairs.append({"id": f"{sid}|r{rep}", "case": case, "rep": rep, "kind": kind,
                                  "match": r["n"], "statement": r[kind]})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "pairs.json").write_text(json.dumps({"cases": cases, "dropped": dict(dropped), "pairs": pairs},
                                               indent=1, ensure_ascii=False))
    reg = [p for p in pairs if p["rep"] in REPS]
    lens = {k: st.mean(len(p["statement"]) for p in reg if p["kind"] == k) for k in ("caveat", "ordinary")}
    print(f"scenarios {len(cases)}; matched caveat sentences {sum(c['n_matched'] for c in cases.values())} "
          f"of {sum(c['n_caveats_cell48'] for c in cases.values())}; dropped {dict(dropped)}")
    print(f"pairs to judge (repeats {REPS}): {len(reg)}; mean length caveat {lens['caveat']:.0f}, ordinary {lens['ordinary']:.0f} characters")
    print(f"scenarios with at least {MIN_CAVEATS} matched caveats: "
          f"{sum(1 for c in cases.values() if c['n_matched'] >= MIN_CAVEATS)}")
    for case, c in cases.items():
        print(f"  {case:<45} caveats {c['n_caveats_cell48']:>3}  matched {c['n_matched']:>3}  ordinary available {c['n_clean_available']:>4}")


def _pairs(reps=REPS) -> list[dict]:
    return [p for p in json.loads((OUT / "pairs.json").read_text())["pairs"] if p["rep"] in reps]


# ------------------------------------------------------------------ shortlist

def _embed(texts: list[str]) -> list[list[float]]:
    out = []
    for i in range(0, len(texts), 64):
        req = urllib.request.Request(runlog.OLLAMA + "/api/embed",
                                     data=json.dumps({"model": EMBED, "input": texts[i:i + 64]}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as fh:
            out.extend(json.loads(fh.read())["embeddings"])
    return out


def _cos(a, b) -> float:
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a) * sum(y * y for y in b)) or 1.0)


def stage_shortlist(smoke_only: bool = False) -> None:
    lab41 = json.loads((AN / "cell41" / "labels.json").read_text())
    pairs = _pairs([SMOKE_REP])[:2] if smoke_only else _pairs(REPS)
    path = OUT / "shortlist.json"
    short = json.loads(path.read_text()) if path.exists() else {}
    by = collections.defaultdict(list)
    for p in pairs:
        if p["id"] not in short:
            by[(p["case"], p["rep"])].append(p)
    t0 = time.time()
    for n, ((case, rep), ps) in enumerate(sorted(by.items())):
        sents = [s for s in lab41[f"{case}__control__r{rep}"]["sentences"] if s.strip()]
        ev = _embed(["search_document: " + s for s in sents])
        qv = _embed(["search_query: " + p["statement"] for p in ps])
        for p, q in zip(ps, qv):
            top = sorted(((_cos(q, e), i) for i, e in enumerate(ev)), reverse=True)[:TOP]
            short[p["id"]] = [{"i": i, "sim": round(s, 4), "text": sents[i]} for s, i in top]
        path.write_text(json.dumps(short, ensure_ascii=False))
        if (n + 1) % 10 == 0:
            print(f"  {n+1}/{len(by)} answers embedded, {time.time()-t0:.0f}s", flush=True)
    print(f"shortlist complete: {len(short)} pairs; embedding model digest {runlog.model_digest(EMBED)}")


# ------------------------------------------------------------------ judging

def parse_verdict(text: str | None) -> str | None:
    t = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).upper()
    m = re.findall(r"VERDICT:\s*(FULLY|PARTLY|NO)\b", t)
    return m[-1].lower() if m else None


def _passages(short: list[dict]) -> str:
    return "\n".join(f"({n}) {s['text'].strip()}" for n, s in enumerate(short, 1))


def _judge(judge: str, key: str, statement: str, label: str, passages: str) -> dict:
    text, meta = runlog.chat_logged(judge, None, PROMPT.format(statement=statement, label=label, passages=passages),
                                    temperature=0.0, max_tokens=MAX_TOKENS, seed=runlog.seed_for(key))
    return runlog.stamp({"key": key, "judge": judge, "verdict": parse_verdict(text)}, meta,
                        root=ROOT, script=Path(__file__), registration=REGISTRATION)


def preflight() -> None:
    from gst.registry import gate_GE, load_frozen
    viol = gate_GE({"PROMPT": PROMPT}, load_frozen(ROOT / "docs" / "DICTATION_REGISTRY.json"), construct_only=True)
    if viol:
        raise SystemExit("PROMPT GATE FAILED: " + "; ".join(viol))


def stage_smoke() -> None:
    preflight()
    short = json.loads((OUT / "shortlist.json").read_text())
    ps = _pairs([SMOKE_REP])[:2]
    for p in ps:
        for judge in JUDGES:
            r = _judge(judge, f"SMOKE|{judge}|{p['id']}", p["statement"], SHORT_LABEL, _passages(short[p["id"]]))
            print(f"  {judge:<28} {p['kind']:<9} verdict={r['verdict']} prompt_tokens={r['audit'].get('prompt_tokens')} "
                  f"wall={r['audit'].get('wall_s')}s top similarity={short[p['id']][0]['sim']}", flush=True)


def stage_judge(only: str | None = None) -> None:
    preflight()
    short = json.loads((OUT / "shortlist.json").read_text())
    pairs = _pairs()
    done = {r["key"] for r in runlog.read_jsonl(CALLS)}
    for judge in ([only] if only else JUDGES):
        jobs = [p for p in pairs if f"{judge}|{p['id']}" not in done]
        print(f"cell66 {judge}: {len(jobs)} pairs to go", flush=True)
        t0, errs = time.time(), 0
        for n, p in enumerate(jobs):
            row = _judge(judge, f"{judge}|{p['id']}", p["statement"], SHORT_LABEL, _passages(short[p["id"]]))
            if row["audit"].get("error"):
                errs += 1
                if errs >= 5:
                    raise SystemExit("ABORTING — five consecutive call errors; resumable.")
                continue
            errs = 0
            runlog.append_jsonl(CALLS, row)
            if (n + 1) % 100 == 0:
                el = time.time() - t0
                print(f"  {n+1}/{len(jobs)} {el:.0f}s ~{el/(n+1)*(len(jobs)-n-1)/60:.0f}m left", flush=True)
        print(f"cell66 {judge}: complete", flush=True)


def _verdicts() -> dict[str, dict[str, str | None]]:
    out: dict[str, dict] = collections.defaultdict(dict)
    for r in runlog.read_jsonl(CALLS):
        judge, pid = r["key"].split("|", 1)
        out[pid][judge] = None if r["audit"].get("ctx_hit") else r["verdict"]
    return out


def _rule(v: dict) -> bool | None:
    """Conveyed when both judges answer FULLY or PARTLY. None when a verdict is missing."""
    if any(v.get(j) is None for j in JUDGES):
        return None
    return all(v[j] in ("fully", "partly") for j in JUDGES)


# ------------------------------------------------------------------ blind sample, miss check

def stage_sample() -> None:
    if (TASK / "task.json").exists():
        print(f"{TASK}/task.json exists; the sample is not drawn again")
        return
    short = json.loads((OUT / "shortlist.json").read_text())
    ver = _verdicts()
    rng = random.Random(SEED)
    strata = collections.defaultdict(list)
    for p in _pairs():
        r = _rule(ver.get(p["id"], {}))
        if r is not None:
            strata[f"{'conveyed' if r else 'not'}|{p['kind']}"].append(p)
    items, key, info = [], {}, {}
    for name in sorted(strata):
        rows = sorted(strata[name], key=lambda p: hashlib.sha256(p["id"].encode()).hexdigest())
        take = rng.sample(rows, min(30, len(rows)))
        info[name] = {"pool": len(rows), "sampled": len(take)}
        for p in take:
            iid = "p" + hashlib.sha256(f"{SEED}|{p['id']}".encode()).hexdigest()[:8]
            items.append({"id": iid, "text": "STATEMENT (from a specialist's note):  " + p["statement"],
                          "passages": [s["text"].strip() for s in short[p["id"]]]})
            key[iid] = {"pair": p["id"], "stratum": name, "kind": p["kind"], "judges": ver[p["id"]]}
    items.sort(key=lambda it: it["id"])
    TASK.mkdir(parents=True, exist_ok=True)
    task = {"task": "cell66_conveyed", "kind": "single_choice", "retest_gap_days": 7,
            "intro": ("Each screen shows one statement from a specialist's note and the three passages of the "
                      "editor's answer closest to it. Decide whether the content of the statement is conveyed "
                      "by the passages. Judge the content, not the wording: a paraphrase counts; a mere mention "
                      "of the same topic does not."),
            "instructions": "Is the content of the statement conveyed by the passages?",
            "choices": CHOICES, "items": items}
    (TASK / "task.json").write_text(json.dumps(task, indent=1, ensure_ascii=False))
    (TASK / "key.json").write_text(json.dumps({"seed": SEED, "strata": info, "items": key}, indent=1))
    # the strata sizes are the result of the comparison and stay in the key file only
    print(f"wrote {TASK}/task.json: {len(items)} pairs for blind labelling (the key is not printed)")


def stage_misscheck() -> None:
    """The shortlist shows three sentences. For 60 pairs the rule called not
    conveyed, one judge reads the whole answer instead."""
    preflight()
    runs = {(r["case"], r["repeat"]): r["output"] for r in runlog.read_jsonl(ROOT / "bench" / "runs" / "cell41_phraseswap.jsonl")
            if r["arm"] == "control"}
    ver = _verdicts()
    rng = random.Random(SEED + 1)
    done = {r["key"] for r in runlog.read_jsonl(MISS)}
    for kind in ("caveat", "ordinary"):
        rows = sorted((p for p in _pairs() if p["kind"] == kind and _rule(ver.get(p["id"], {})) is False),
                      key=lambda p: p["id"])
        for p in rng.sample(rows, min(30, len(rows))):
            key = f"{JUDGES[0]}|FULL|{p['id']}"
            if key in done:
                continue
            row = _judge(JUDGES[0], key, p["statement"], FULL_LABEL, runs[(p["case"], p["rep"])])
            row["kind"] = kind
            runlog.append_jsonl(MISS, row)
    print("cell66 misscheck complete")


# ------------------------------------------------------------------ measure

def _weighted(rows) -> dict:
    """rows: (weight, truth, pred). Agreement figures from the weighted 2x2 table."""
    w = collections.Counter()
    for wt, t, p in rows:
        w[(bool(t), bool(p))] += wt
    n = sum(w.values()) or 1.0
    tp, fp, fn, tn = w[(True, True)], w[(False, True)], w[(True, False)], w[(False, False)]
    raw = (tp + tn) / n
    chance = ((tp + fn) / n) * ((tp + fp) / n) + ((tn + fp) / n) * ((tn + fn) / n)
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    return {"raw": raw, "kappa": (raw - chance) / (1 - chance) if chance < 1 else float("nan"),
            "precision": prec, "recall": rec, "f1": 2 * prec * rec / (prec + rec) if tp else 0.0,
            "truth_share": (tp + fn) / n, "rule_share": (tp + fp) / n}


def stage_measure(allow_uncommitted: bool = False) -> None:
    from train.label_blind import done_info, read_labels
    from train.run_cell62_instrument import _committed
    meta = json.loads((OUT / "pairs.json").read_text())
    pairs = _pairs()
    ver = _verdicts()
    print("=" * 78)
    print("CELL 66 — are caveats lost more than ordinary content?")
    print("=" * 78)
    usable = [p for p in pairs if _rule(ver.get(p["id"], {})) is not None]
    print(f"pairs {len(pairs)}; with both judges' verdicts {len(usable)}")
    result = {"n_pairs": len(pairs), "n_usable": len(usable)}
    check = OUT / "check_measured.json"                 # CELL 66 AMENDMENT (2026-10-02): the person's
    labels_done = (TASK / "task.json").exists() and done_info(TASK, 1)   # labels replaced by a registered check
    if not labels_done and not check.exists():
        print("\nP66.0 PENDING — neither the blind labels nor the amended check "
              "(train/run_cell66_check.py measure) is done.")
        print("Nothing about the comparison is computed or shown until one of them is committed.")
        return
    if labels_done and not allow_uncommitted and not _committed(TASK / "labels_pass1.jsonl"):
        raise SystemExit("Commit the pass-1 labels before scoring (the labelling tool printed the command).")
    if not labels_done and not allow_uncommitted and not _committed(check):
        raise SystemExit("Commit bench/analysis/cell66/check_measured.json before scoring.")

    k = kappa([(ver[p["id"]][JUDGES[0]] != "no", ver[p["id"]][JUDGES[1]] != "no") for p in usable])
    print(f"the two judges against each other (conveyed at all): raw {k['raw']:.3f}  kappa {k['kappa']:.3f}")
    result["judge_kappa"] = k["kappa"]

    if not labels_done:
        chk = json.loads(check.read_text())
        gate = bool(chk["pass"])
        parts = ", ".join(f"{k_} {'passes' if v else 'not evaluable' if v is None else 'fails'}" for k_, v in chk["parts"].items())
        print(f"\nthe rule against public human labels and known values (CELL 66 AMENDMENT): {parts}")
        print(f"P66.0 {'PASSES' if gate else 'FAILS'} — amended check; bars as registered")
        result["P66.0"] = {"amended_check": chk["parts"], "pass": gate}
    else:
        print("\nthe rule against one person's blind labels")
        human = {i: v["label"]["choice"] for i, v in read_labels(TASK / "labels_pass1.jsonl").items()}
        key = json.loads((TASK / "key.json").read_text())
        rows = []
        for iid, kk in key["items"].items():
            s_ = key["strata"][kk["stratum"]]
            rows.append((s_["pool"] / s_["sampled"], human[iid] != "no", kk["stratum"].startswith("conveyed")))
        g = _weighted(rows)
        gate = g["kappa"] >= 0.60 and g["f1"] >= 0.80
        print(f"  {len(rows)} labelled pairs, weighted back to all pairs: raw {g['raw']:.3f}  kappa {g['kappa']:.3f}  "
              f"precision {g['precision']:.3f}  recall {g['recall']:.3f}  F1 {g['f1']:.3f}")
        print(f"  share conveyed: the person {g['truth_share']:.3f}, the rule {g['rule_share']:.3f}")
        print(f"P66.0 {'PASSES' if gate else 'FAILS'} — bars: kappa 0.60 and F1 0.80")
        result["P66.0"] = {**g, "pass": gate}
        if done_info(TASK, 2):
            h2 = {i: v["label"]["choice"] for i, v in read_labels(TASK / "labels_pass2.jsonl").items()}
            kk = kappa([(human[i] != "no", h2[i] != "no") for i in human if i in h2])
            print(f"  the person against themself a week apart: raw {kk['raw']:.3f}  kappa {kk['kappa']:.3f}")
            result["retest_kappa"] = kk["kappa"]

    def rate(rows, level="any"):
        v = [(_rule(ver[p["id"]]) if level == "any" else all(ver[p["id"]][j] == "fully" for j in JUDGES)) for p in rows]
        return sum(v) / len(v) if v else None

    print("\nP66.2  how much is conveyed (the rule; all usable pairs)")
    for kind in ("caveat", "ordinary"):
        rows = [p for p in usable if p["kind"] == kind]
        print(f"  {kind:<9} n = {len(rows):>4}   conveyed at least partly {rate(rows):.3f}   conveyed fully {rate(rows, 'full'):.3f}")
        result[f"rate_{kind}"] = {"n": len(rows), "any": rate(rows), "full": rate(rows, "full")}

    print(f"\nP66.1  caveats minus matched ordinary sentences, scenario level "
          f"(scenarios with at least {MIN_CAVEATS} matched caveats)")
    main_cases = [c for c, v in meta["cases"].items() if v["n_matched"] >= MIN_CAVEATS]
    for level, name in (("any", "conveyed at least partly"), ("full", "conveyed fully")):
        for label, cs in (("main", main_cases), ("all scenarios", list(meta["cases"]))):
            d = []
            for c in cs:
                a = rate([p for p in usable if p["case"] == c and p["kind"] == "caveat"], level)
                b = rate([p for p in usable if p["case"] == c and p["kind"] == "ordinary"], level)
                if a is not None and b is not None:
                    d.append(a - b)
            if len(d) < 2:
                continue
            m, lo, hi = t_interval(d)
            p = sign_flip_p(d)
            print(f"  {name:<26} {label:<14} {m:+.3f} [{lo:+.3f}, {hi:+.3f}]  sign-flip p = {p:.4f}  (k = {len(d)})")
            result[f"P66.1_{level}_{label}"] = {"mean": m, "lo": lo, "hi": hi, "p": p, "k": len(d)}
    s = result.get("P66.1_any_main")
    if s:
        if not gate:
            word = "P66.1 NOT EVALUABLE — the rule failed its check (P66.0); recorded as blocked, not as a null"
        elif s["hi"] < 0:
            word = "P66.1 SUPPORTED — caveats are conveyed less often than matched ordinary sentences"
        elif s["lo"] > 0:
            word = "P66.1 REVERSED — caveats are conveyed more often than matched ordinary sentences"
        elif -BAND < s["lo"] and s["hi"] < BAND:
            word = f"P66.1 FALSIFIED — the interval spans zero inside ±{BAND}: conveyed about as often (proportional)"
        else:
            word = "P66.1 NOT EVALUABLE — the interval spans zero and is wider than the band"
        print(f"VERDICT LINE (as registered): {word}")
        result["P66.1_verdict"] = word

    miss = runlog.read_jsonl(MISS)
    if miss:
        print("\nwhat the three-sentence shortlist misses (one judge reads the whole answer; pairs the rule called not conveyed):")
        for kind in ("caveat", "ordinary"):
            v = [r["verdict"] for r in miss if r["kind"] == kind and r["verdict"]]
            c = collections.Counter(v)
            if v:
                print(f"  {kind:<9} n = {len(v)}   fully {c['fully']/len(v):.3f}   partly {c['partly']/len(v):.3f}   no {c['no']/len(v):.3f}")
                result[f"miss_{kind}"] = {x: c[x] / len(v) for x in ("fully", "partly", "no")}
    (OUT / "measured.json").write_text(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "build"
    if stage == "judge":
        stage_judge(sys.argv[2] if len(sys.argv) > 2 else None)
    elif stage == "shortlist":
        stage_shortlist(len(sys.argv) > 2 and sys.argv[2] == "smoke")
    elif stage == "measure":
        stage_measure("--allow-uncommitted" in sys.argv)
    else:
        {"build": stage_build, "smoke": stage_smoke,
         "sample": stage_sample, "misscheck": stage_misscheck}[stage]()
