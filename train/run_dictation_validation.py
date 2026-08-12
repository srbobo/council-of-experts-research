"""Validate the paraphrase matcher against the frozen dictation registry.

Pre-registration: RUNBOOK_PAPER_HARDENING.md
"DICTATION REGISTRY + PARAPHRASE MATCHER — PRE-REGISTRATION", committed
before this file's scoring stage was ever run.

  pools    build POS / NEG / OVER pools from archived runs, provenance read
           PER RUN from recorded input_messages. Prints the attainability
           check. Generates NOTHING and calls no model.
  score    run the two judges over the pools (V-A) and report AUC,
           agreement, and the V-B over-attribution rate against the frozen
           gates.

Run:  .venv/bin/python train/run_dictation_validation.py pools
      .venv/bin/python train/run_dictation_validation.py score
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst.dictation import (MATCHER_PROMPT, build_query, literal_hits,  # noqa: E402
                           parse_reply, shortlist)
from gst.registry import gate_GE, load_frozen                          # noqa: E402
from train.run_cell25_moa import chat                                  # noqa: E402

REGISTRY = ROOT / "docs" / "DICTATION_REGISTRY.json"
OUT = ROOT / "bench" / "analysis" / "dictation"
POOLS = OUT / "pools.json"
JUDGES = ["gpt-oss:20b", "qwen2.5:7b-instruct"]
AUC_GATE, AGREE_GATE, FLOOR = 0.80, 0.70, 15
MAX_PER_POOL = 30


# --------------------------------------------------------------------------
# Pool construction — provenance from recorded prompts, never from corpus name
# --------------------------------------------------------------------------

def writer_system(rec: dict) -> str | None:
    """The system prompt the WRITER actually received, from the run record."""
    d = rec.get("deliberation") or {}
    syn = d.get("synthesis") or {}
    for m in syn.get("input_messages") or []:
        if m.get("role") == "system":
            return m.get("content") or ""
    return None


def sentences(text: str) -> list[str]:
    """Sentence split on terminal punctuation followed by whitespace.

    Segmentation, not classification -- it decides units, never labels. The
    program measures at sentence granularity throughout (finding #9).
    """
    out, buf = [], []
    for i, ch in enumerate(text):
        buf.append(ch)
        if ch in ".!?" and i + 1 < len(text) and text[i + 1].isspace():
            s = "".join(buf).strip()
            if s:
                out.append(s)
            buf = []
    s = "".join(buf).strip()
    if s:
        out.append(s)
    return [x for x in out if 40 <= len(x) <= 400]


def validated_clean_spans() -> list[str]:
    """Cell 30 writer sentences BOTH judges marked construct-bearing.

    The Cell 30 corpus is clean-provenance (its prompts are verified against
    gate G-E in `stage_pools`), and these labels come from the validated
    sentence-level protocol -- agreement 0.833, P30.0 PASS. Labels are stored
    per batch of ten (the Cell IV B=10 instrument), keyed `judge|offset` into
    the flattened sentence list, so they are reassembled here in that order.
    """
    c = ROOT / "bench" / "analysis" / "c30c31"
    units = json.loads((c / "units.json").read_text())
    lab = json.loads((c / "labels.json").read_text())
    flat, kind = [], []
    for u in units:
        for s in u["sentences"]:
            flat.append(s)
            kind.append(u["kind"])
    fams = ("cutoff", "modeled", "jurisd", "hedging")
    out: list[str] = []
    for off in sorted({int(k.split("|")[1]) for k in lab}):
        a, b = lab.get(f"{JUDGES[0]}|{off}"), lab.get(f"{JUDGES[1]}|{off}")
        if not a or not b:
            continue
        for j in range(1, 11):
            i = off + j - 1
            if i >= len(flat):
                break
            la, lb = a.get(str(j)), b.get(str(j))
            if not la or not lb or kind[i] != "output":
                continue
            if any(la.get(f) and lb.get(f) for f in fams):
                if 40 <= len(flat[i]) <= 400:
                    out.append(flat[i])
    return out


def stage_pools() -> None:
    reg = load_frozen(REGISTRY)
    construct = [e for e in reg if e.family_hint]
    OUT.mkdir(parents=True, exist_ok=True)

    # --- gate G-E on the matcher's own prompt, BEFORE anything else --------
    viol = gate_GE({"MATCHER_PROMPT": MATCHER_PROMPT}, reg, construct_only=True)
    if viol:
        print("GATE G-E FAILED — the matcher re-dictates registry phrases:")
        for v in viol:
            print("  " + v)
        raise SystemExit(1)
    print(f"gate G-E: PASS — matcher prompt names no registry phrase "
          f"({len(construct)} construct-bearing entries checked)\n")

    dictated_spans, clean_spans = [], []

    # --- archived council runs: provenance read per run -------------------
    n_runs = n_dict = n_clean = 0
    for f in sorted(ROOT.glob("bench/runs/2026*/case_*.json")):
        try:
            rec = json.loads(f.read_text())
        except Exception:
            continue
        sysmsg = writer_system(rec)
        out = ((rec.get("deliberation") or {}).get("synthesis") or {}).get("output_text")
        if not sysmsg or not out:
            continue
        n_runs += 1
        low = sysmsg.lower()
        dictated = any(e.phrase.lower() in low for e in construct
                       if len(e.phrase) >= 8)
        (dictated_spans if dictated else clean_spans).extend(
            (s, str(f.relative_to(ROOT))) for s in sentences(out))
        n_dict += dictated
        n_clean += (not dictated)

    # --- Cell 30 de-scaffolded corpus: prompts VERIFIED clean -------------
    from train.run_cell30_descaffold import SEATS, WRITER_PROMPT
    c30_prompts = {"WRITER_PROMPT": WRITER_PROMPT,
                   **{f"SEATS[{k}]": v for k, v in SEATS.items()}}
    c30_viol = gate_GE(c30_prompts, reg, construct_only=True)
    if c30_viol:
        print("Cell 30 corpus is NOT clean-provenance:", c30_viol)
        raise SystemExit(1)
    print("Cell 30 prompts verified clean-provenance (gate G-E passes on them)")

    c30 = ROOT / "bench" / "runs" / "cell30_descaffold.jsonl"
    n_c30 = 0
    if c30.exists():
        for line in c30.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            txt = r.get("output") or r.get("text") or ""
            if txt:
                n_c30 += 1
                clean_spans.extend((s, "cell30") for s in sentences(txt))

    print(f"\narchived council runs: {n_runs}  "
          f"(dictated-provenance {n_dict}, clean {n_clean})")
    print(f"cell30 de-scaffolded runs: {n_c30}")
    print(f"spans: dictated-provenance {len(dictated_spans)}, "
          f"clean-provenance {len(clean_spans)}")

    # --- partition by literal registry containment ------------------------
    rng = random.Random(0)

    def has_lit(s: str) -> bool:
        return bool(literal_hits(s, construct))

    pos = [(s, src) for s, src in dictated_spans if has_lit(s)]
    neg = [(s, src) for s, src in clean_spans if not has_lit(s)]
    over = [(s, src) for s, src in clean_spans if has_lit(s)]

    # NEG must EXPRESS the construct, or the contrast is construct-vs-nothing
    # rather than dictated-vs-novel.
    #
    # Selection uses the VALIDATED sentence-level judge labels from the Cell 30
    # corpus (both judges agreeing a family is present; protocol agreement
    # 0.833, P30.0). It deliberately does NOT use the regex screen: that
    # lexicon has 0.25-0.30 sensitivity on three of four families, so screening
    # with it would sample only novel spans that happen to look like the
    # lexicon -- and the lexicon derives from the scaffold. That would smuggle
    # the entanglement under test into the validation set itself.
    neg = [(s, "cell30-validated") for s in validated_clean_spans()]

    for name, pool in (("POS", pos), ("NEG", neg), ("OVER", over)):
        rng.shuffle(pool)
        print(f"  {name:<5} available {len(pool)}")

    doc = {"pos": pos[:MAX_PER_POOL], "neg": neg[:MAX_PER_POOL],
           "over": over[:MAX_PER_POOL],
           "available": {"pos": len(pos), "neg": len(neg), "over": len(over)}}
    POOLS.write_text(json.dumps(doc, indent=1, ensure_ascii=False))

    print("\n--- ATTAINABILITY (checklist item 12), registered floor "
          f"{FLOOR} per class ---")
    ok = len(doc["pos"]) >= FLOOR and len(doc["neg"]) >= FLOOR
    print(f"  POS {len(doc['pos'])}  NEG {len(doc['neg'])}  -> "
          f"{'PROCEED' if ok else 'NOT EVALUABLE — below floor'}")
    print(f"  OVER pool for V-B: {len(doc['over'])}")


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

def auc(pos: list[float], neg: list[float]) -> float:
    """Mann-Whitney AUC with ties at 0.5."""
    if not pos or not neg:
        return float("nan")
    tot = sum((1.0 if p > n else 0.5 if p == n else 0.0)
              for p in pos for n in neg)
    return tot / (len(pos) * len(neg))


def stage_score() -> None:
    reg = load_frozen(REGISTRY)
    construct = [e for e in reg if e.family_hint]
    doc = json.loads(POOLS.read_text())
    if len(doc["pos"]) < FLOOR or len(doc["neg"]) < FLOOR:
        print("NOT EVALUABLE — pools below the registered floor")
        return

    cache_path = OUT / "judged.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    items = ([(s, "pos") for s, _ in doc["pos"]]
             + [(s, "neg") for s, _ in doc["neg"]]
             + [(s, "over") for s, _ in doc["over"]])
    t0 = time.time()
    for i, (span, cls) in enumerate(items):
        refs = shortlist(span, construct, k=8)
        q = build_query(span, refs)
        for j in JUDGES:
            key = f"{j}||{cls}||{span[:120]}"
            if key in cache:
                continue
            # 512, not 64: gpt-oss:20b is a reasoning model and spends a small
            # budget entirely on reasoning, returning empty. The quarantine
            # caught that (60/60) rather than scoring the blanks as NONE --
            # finding #2's guard doing its job.
            txt = chat(j, MATCHER_PROMPT, q, temperature=0.0, max_tokens=512)
            g, ref = parse_reply(txt or "")
            cache[key] = {"grade": g, "ref": ref,
                          "ref_id": refs[ref - 1].id if 1 <= ref <= len(refs) else None}
            cache_path.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            print(f"  {i+1}/{len(items)} {el:.0f}s", flush=True)

    # --- assemble ---------------------------------------------------------
    by_cls: dict[str, list[float]] = {"pos": [], "neg": [], "over": []}
    quarantined = 0
    agree_n = agree_k = 0
    for span, cls in items:
        gs = []
        for j in JUDGES:
            c = cache.get(f"{j}||{cls}||{span[:120]}")
            if c and c["grade"] >= 0:
                gs.append(c["grade"])
        if len(gs) < len(JUDGES):
            quarantined += 1
            continue
        agree_n += 1
        # agreement on the DEPLOYED binary decision: is this dictated material?
        agree_k += ((gs[0] >= 2) == (gs[1] >= 2))
        by_cls[cls].append(sum(gs) / len(gs))

    print("=" * 74)
    print("V-A — DISCRIMINATIVE VALIDITY (registered gates: AUC >= 0.80, "
          "agreement >= 0.70)")
    print("=" * 74)
    print(f"  quarantined (unparseable from a judge): {quarantined}")
    agr = agree_k / agree_n if agree_n else float("nan")
    print(f"  judge-judge agreement on the deployed binary decision: "
          f"{agr:.3f} ({agree_k}/{agree_n})  -> "
          f"{'PASS' if agr >= AGREE_GATE else 'FAIL'}")
    a = auc(by_cls["pos"], by_cls["neg"])
    print(f"  mean grade POS {sum(by_cls['pos'])/max(len(by_cls['pos']),1):.2f} "
          f"(n={len(by_cls['pos'])})   NEG "
          f"{sum(by_cls['neg'])/max(len(by_cls['neg']),1):.2f} "
          f"(n={len(by_cls['neg'])})")
    print(f"  AUC = {a:.3f}  -> {'PASS' if a >= AUC_GATE else 'FAIL'}")
    print()
    print("  REGISTERED LIMITATION: this pool contrasts literal presence "
          "against literal\n  absence — the EASY case. A high AUC is "
          "necessary, not sufficient.")

    print()
    print("=" * 74)
    print("V-B — OVER-ATTRIBUTION RATE (mandatory reporting, no bar)")
    print("=" * 74)
    ov = by_cls["over"]
    if not ov:
        print("  no clean-provenance spans carry registry phrases verbatim")
    else:
        fired = sum(1 for g in ov if g >= 2)
        from gst.stats import wilson_ci
        lo, hi = wilson_ci(fired, len(ov))
        print(f"  clean-provenance spans containing a registry phrase: {len(ov)}")
        print(f"  matcher calls them dictated: {fired}/{len(ov)} = "
              f"{fired/len(ov):.3f} [{lo:.3f},{hi:.3f}]")
        print("  -> this is the amount by which M_dictated OVER-COUNTS "
              "compliance C.\n     Registry form arose here with no dictation "
              "in the pipeline at all.")

    print()
    gates = (a >= AUC_GATE) and (agr >= AGREE_GATE)
    print("VERDICT:", "matcher DEPLOYABLE for the paraphrase stage" if gates
          else "matcher NOT deployable — partition falls back to literal-only, "
               "and M_dictated is then reported as a strict UNDERCOUNT of "
               "form-echo")
    (OUT / "report.txt").write_text("see stdout")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "pools"
    {"pools": stage_pools, "score": stage_score}[stage]()
