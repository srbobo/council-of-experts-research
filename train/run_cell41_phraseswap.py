"""Cell 41 — the phrase-swap cell. Does the PRESERVE-style instruction have
any effect that survives swapping the phrase it names?

Pre-registration: RUNBOOK_PAPER_HARDENING.md "CELL 41 PRE-REGISTRATION".
Forms frozen in docs/PHRASE_SWAP_FORMS.json BEFORE this cell was registered.

Layer 3 of the finding-#8 resolution. Layers 1-2 supplied provenance (the
dictation registry) and a literal partition validated at ZERO
over-attribution. Neither can separate compliance from behaviour, because
the difference is causal, not textual. This cell intervenes on the dictation
itself.

  A-control   clean writer prompt, no form clause
  A-form-X    + clause naming "modeled at"   (the historically dictated form)
  A-form-Y    + clause naming "taken to be"  (a synonym never dictated)

The clause is IDENTICAL across the two treated arms but for the named
phrase, so exactly one factor moves (writer instruction / surface form).

INSTRUMENTS — both already validated, neither is regex-as-NLP:
  construct presence  the batched sentence judge at B=10 (Cell IV), two
                      judges, definitions that name no phrase and instruct
                      "do not reward particular wording". Passes gate G-E.
  form attribution    literal containment of the frozen forms. Validated at
                      0/2907 over-attribution (V-B), which is what makes
                      literal attribution trustworthy here.

Run:  .venv/bin/python train/run_cell41_phraseswap.py seats
      ... runs / judge / measure
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from train.run_cell25_moa import chat                              # noqa: E402
from train.run_cell30_descaffold import SEATS, WRITER_PROMPT       # noqa: E402

OUT = ROOT / "bench" / "analysis" / "cell41"
RUNS = ROOT / "bench" / "runs" / "cell41_phraseswap.jsonl"
SEATS_PATH = OUT / "seats.json"
C30_SEATS = ROOT / "bench" / "analysis" / "cell30" / "seats.json"
FORMS_PATH = ROOT / "docs" / "PHRASE_SWAP_FORMS.json"
WRITER = "gpt-oss:20b"
JUDGES = ["gpt-oss:20b", "qwen2.5:7b-instruct"]
REPEATS = 7                      # x 18 cases x 3 arms = 378 runs, 126/arm

_F = json.loads(FORMS_PATH.read_text())
FORM_X: str = _F["form_X"]["phrase"]          # "modeled at"
FORM_Y: str = _F["form_Y"]["phrase"]          # "taken to be"
ARMS = ("control", "form-X", "form-Y")
ARM_FORM = {"control": None, "form-X": FORM_X, "form-Y": FORM_Y}

# Identical in both treated arms but for {form}. That identity IS the
# one-factor guarantee; editing it mid-cell invalidates the comparison.
CLAUSE = (' When you state a number that is an estimate rather than an '
          'established fact, label it using the phrase "{form}".')


def arm_prompt(arm: str) -> str:
    f = ARM_FORM[arm]
    return WRITER_PROMPT if f is None else WRITER_PROMPT + CLAUSE.format(form=f)


def audit_clause_dictation() -> list[str]:
    """Gate G-E, inverted for a cell whose treatment IS dictation.

    G-E normally refuses any prompt containing a registry phrase. Here the
    clause deliberately contains one -- that is the independent variable. So
    the check is not "no registry phrases" but "EXACTLY the phrase this arm
    names, and nothing else". Any other registry phrase is an unintended
    leak and must abort the cell.
    """
    from gst.registry import gate_GE, load_frozen
    reg = load_frozen(ROOT / "docs" / "DICTATION_REGISTRY.json")
    problems: list[str] = []
    for arm in ARMS:
        text = arm_prompt(arm)
        viol = gate_GE({arm: text}, reg, construct_only=True)
        own = ARM_FORM[arm]
        for v in viol:
            # tolerate only entries whose phrase is contained in this arm's form
            phrase = v.split("re-dictates", 1)[1].split("'")[1] if "'" in v else v
            if own and phrase.lower() in own.lower():
                continue
            problems.append(f"UNINTENDED dictation in {arm}: {v}")
        if own and own not in text:
            problems.append(f"{arm}: clause does not contain its own form {own!r}")
    # the two treated clauses must differ ONLY in the form
    x = arm_prompt("form-X").replace(FORM_X, "<FORM>")
    y = arm_prompt("form-Y").replace(FORM_Y, "<FORM>")
    if x != y:
        problems.append("form-X and form-Y prompts differ by more than the form")
    return problems


def cases() -> list[str]:
    from examples.test_cases import CASES
    return [getattr(c, "case_id", getattr(c, "id", None)) for c in CASES]


# ------------------------------------------------------------------ stages

def stage_seats() -> None:
    """De-scaffolded seat text for every case, using Cell 30's CLEAN prompts.

    Cell 30's nine are copied verbatim rather than regenerated, so the
    existing corpus is untouched and only the nine new cases are produced.
    """
    from examples.test_cases import get_case
    OUT.mkdir(parents=True, exist_ok=True)
    done = json.loads(SEATS_PATH.read_text()) if SEATS_PATH.exists() else {}
    if not done:
        done = json.loads(C30_SEATS.read_text())
        print(f"seeded {len(done)} cases from Cell 30's de-scaffolded corpus")
    t0 = time.time()
    for case in cases():
        done.setdefault(case, {})
        for role, sysmsg in SEATS.items():
            if done[case].get(role):
                continue
            print(f"  seat {case[:38]} / {role} ({time.time()-t0:.0f}s)", flush=True)
            txt = chat(WRITER, sysmsg, get_case(case).prompt,
                       temperature=0.7, max_tokens=4096)
            if txt and txt.strip():
                done[case][role] = txt
                SEATS_PATH.write_text(json.dumps(done, ensure_ascii=False))
    have = sum(1 for c in cases() for r in SEATS if done.get(c, {}).get(r))
    print(f"seats: {have}/{len(cases())*len(SEATS)} across {len(cases())} cases")


def preflight() -> None:
    """Refuse to start against an unreachable backend.

    Added after the first launch: ollama died during seat generation and the
    run stage churned through all 378 cells writing nothing, then printed
    "runs complete". A stage that no-ops silently and reports success is the
    checkpdf.sh defect again -- fail loud instead.
    """
    # 256, not 16: WRITER is a reasoning model and spends a small budget
    # entirely on reasoning, returning empty. The first version of this guard
    # carried that exact defect and false-alarmed on a healthy backend --
    # measured 16 -> '' , 128 -> 'OK'. A preflight that cries wolf is worse
    # than none.
    t = chat(WRITER, "Reply with the single word OK.", "ping",
             temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit(f"PREFLIGHT FAILED — {WRITER} returned nothing. "
                         f"Is ollama running? Refusing to start.")
    print(f"preflight: {WRITER} responds")


def stage_seats_complete() -> bool:
    seats = json.loads(SEATS_PATH.read_text()) if SEATS_PATH.exists() else {}
    missing = [(c, r) for c in cases() for r in SEATS
               if not seats.get(c, {}).get(r)]
    if missing:
        print(f"SEATS INCOMPLETE — {len(missing)} missing: {missing[:6]}")
    return not missing


def stage_runs() -> None:
    from examples.test_cases import get_case
    preflight()
    if not stage_seats_complete():
        raise SystemExit("Refusing to run on an incomplete seat corpus — "
                         "arms would differ in which cases they cover.")
    bad = audit_clause_dictation()
    if bad:
        print("CLAUSE AUDIT FAILED — refusing to run:")
        for b in bad:
            print("  " + b)
        raise SystemExit(1)
    print("clause audit: PASS — each arm dictates exactly its own form, and "
          "the two treated prompts differ only in that form\n")

    seats = json.loads(SEATS_PATH.read_text())
    done = set()
    if RUNS.exists():
        for line in RUNS.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["run_id"])
    todo = [(c, arm, r) for c in cases() for arm in ARMS for r in range(REPEATS)
            if f"{c}__{arm}__r{r}" not in done]
    print(f"cell41: {len(todo)} runs to go ({len(done)} cached)", flush=True)
    t0 = time.time()
    consecutive_fail = 0
    with RUNS.open("a") as fh:
        for k, (case, arm, rep) in enumerate(todo):
            up = [seats[case][r] for r in SEATS if seats.get(case, {}).get(r)]
            body = "\n\n".join(f"--- SPECIALIST CONTRIBUTION ---\n{t}" for t in up)
            user = f"{body}\n\nQuestion:\n{get_case(case).prompt}"
            txt = None
            for attempt in range(3):          # transient backend errors
                txt = chat(WRITER, arm_prompt(arm), user,
                           temperature=0.6, max_tokens=8192)
                if txt and txt.strip():
                    break
                time.sleep(5 * (attempt + 1))
            if not txt or not txt.strip():
                consecutive_fail += 1
                print(f"  EMPTY {case}/{arm}/r{rep} "
                      f"(consecutive {consecutive_fail})", flush=True)
                if consecutive_fail >= 5:
                    raise SystemExit(
                        f"ABORTING — {consecutive_fail} consecutive failures. "
                        f"The backend is down; {len(done)} runs are on disk and "
                        f"the stage is resumable. Not churning the matrix.")
                continue
            consecutive_fail = 0
            fh.write(json.dumps({"run_id": f"{case}__{arm}__r{rep}", "case": case,
                                 "arm": arm, "repeat": rep, "output": txt},
                                ensure_ascii=False) + "\n")
            fh.flush()
            if (k + 1) % 10 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(todo)} {el:.0f}s "
                      f"~{el/(k+1)*(len(todo)-k-1):.0f}s left", flush=True)
    print("cell41 runs complete")


def split_sentences(text: str) -> list[str]:
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
    return [x for x in out if 25 <= len(x) <= 400]


def stage_judge() -> None:
    from train.run_cellIV_batchjudge import judge_batches
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    cpath = OUT / "judge_cache.json"
    cache = json.loads(cpath.read_text()) if cpath.exists() else {}
    labels: dict[str, dict] = {}
    t0 = time.time()
    for i, r in enumerate(rows):
        items = [{"sentence": s} for s in split_sentences(r["output"])]
        if not items:
            continue
        per = {}
        for j in JUDGES:
            got, fails = judge_batches(items, 10, j, cache, r["run_id"])
            per[j] = got
            if fails:
                print(f"  {r['run_id']}: {fails} unparsed batches from {j}", flush=True)
        labels[r["run_id"]] = {"sentences": [x["sentence"] for x in items],
                               "judges": {j: {str(k): v for k, v in per[j].items()}
                                          for j in JUDGES}}
        cpath.write_text(json.dumps(cache, ensure_ascii=False))
        (OUT / "labels.json").write_text(json.dumps(labels, ensure_ascii=False))
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            print(f"  judged {i+1}/{len(rows)} {el:.0f}s "
                  f"~{el/(i+1)*(len(rows)-i-1):.0f}s left", flush=True)
    print("cell41 judging complete")


def stage_measure() -> None:
    import random
    from gst.stats import wilson_ci
    rng = random.Random(0)
    rows = [json.loads(x) for x in RUNS.read_text().splitlines() if x.strip()]
    labels = json.loads((OUT / "labels.json").read_text())

    # per-run outcomes ------------------------------------------------------
    rec = []
    agree_n = agree_k = 0
    for r in rows:
        lab = labels.get(r["run_id"])
        if not lab:
            continue
        low = r["output"].lower()
        sents = lab["sentences"]
        a, b = (lab["judges"].get(j, {}) for j in JUDGES)
        modeled_idx = []
        for i in range(len(sents)):
            la, lb = a.get(str(i)), b.get(str(i))
            if not la or not lb:
                continue
            agree_n += 1
            agree_k += (la["modeled"] == lb["modeled"])
            if la["modeled"] and lb["modeled"]:
                modeled_idx.append(i)
        rec.append({
            "case": r["case"], "arm": r["arm"],
            "has_X": FORM_X in low, "has_Y": FORM_Y in low,
            "modeled_any": len(modeled_idx) > 0,
            # construct present in a sentence that does NOT carry the arm's form
            "modeled_not_X": any(FORM_X not in sents[i].lower() for i in modeled_idx),
            "modeled_not_Y": any(FORM_Y not in sents[i].lower() for i in modeled_idx),
            "n_sent": len(sents), "chars": len(r["output"]),
        })

    def rate(arm, field):
        v = [x[field] for x in rec if x["arm"] == arm]
        return (sum(v) / len(v) if v else float("nan")), len(v)

    def cluster_boot(arm_a, arm_b, field_a, field_b):
        """Bootstrap over CASES -- the cluster -- not over runs. This is what
        handles ICC 0.190 in the analysis; the design-effect arithmetic was
        for planning only."""
        cs = sorted({x["case"] for x in rec})
        by = {}
        for x in rec:
            by.setdefault((x["case"], x["arm"]), []).append(x)
        ds = []
        for _ in range(5000):
            samp = [cs[rng.randrange(len(cs))] for _ in cs]
            na = [y[field_a] for c in samp for y in by.get((c, arm_a), [])]
            nb = [y[field_b] for c in samp for y in by.get((c, arm_b), [])]
            if not na or not nb:
                continue
            ds.append(sum(na) / len(na) - sum(nb) / len(nb))
        ds.sort()
        return (ds[int(.025 * len(ds))], ds[int(.975 * len(ds))]) if ds else None

    print("=" * 78)
    print(f"CELL 41 — form X {FORM_X!r} vs form Y {FORM_Y!r}")
    print(f"runs scored: {len(rec)}   judge agreement on `modeled`: "
          f"{agree_k/agree_n:.3f} ({agree_k}/{agree_n})"
          f"  -> {'PASS' if agree_k/agree_n >= 0.70 else 'FAIL (bar 0.70)'}")
    print("=" * 78)
    print(f"  {'arm':<10}{'n':>5}{'has X':>9}{'has Y':>9}{'modeled':>10}"
          f"{'sent':>7}{'chars':>8}")
    for arm in ARMS:
        v = [x for x in rec if x["arm"] == arm]
        if not v:
            continue
        print(f"  {arm:<10}{len(v):>5}"
              f"{sum(x['has_X'] for x in v)/len(v):>9.3f}"
              f"{sum(x['has_Y'] for x in v)/len(v):>9.3f}"
              f"{sum(x['modeled_any'] for x in v)/len(v):>10.3f}"
              f"{sum(x['n_sent'] for x in v)/len(v):>7.1f}"
              f"{sum(x['chars'] for x in v)/len(v):>8.0f}")

    print()
    print("P41.1 COMPLIANCE IS FORM-TRACKING (both required)")
    ok1 = True
    for arm, field, form in (("form-X", "has_X", FORM_X), ("form-Y", "has_Y", FORM_Y)):
        ci = cluster_boot(arm, "control", field, field)
        r_, n_ = rate(arm, field)
        c_, _ = rate("control", field)
        hit = ci is not None and ci[0] > 0
        ok1 &= hit
        print(f"  {arm:<8} {form!r:<16} {c_:.3f} -> {r_:.3f}  "
              f"CI [{ci[0]:+.3f},{ci[1]:+.3f}]  {'MOVED' if hit else 'no move'}")
    print(f"  P41.1: {'SUPPORTED' if ok1 else 'FALSIFIED'}")

    print()
    print("P41.2 FORM-INDEPENDENT EFFECT — THE ESTIMAND (both required)")
    ok2 = True
    for arm, field in (("form-X", "modeled_not_X"), ("form-Y", "modeled_not_Y")):
        ci = cluster_boot(arm, "control", field, field)
        r_, _ = rate(arm, field)
        c_, _ = rate("control", field)
        hit = ci is not None and ci[0] > 0
        ok2 &= hit
        print(f"  {arm:<8} non-named construct {c_:.3f} -> {r_:.3f}  "
              f"CI [{ci[0]:+.3f},{ci[1]:+.3f}]  {'LIFT' if hit else 'no lift'}")
    print(f"  P41.2: {'SUPPORTED — the instruction has an effect beyond its phrase'
                     if ok2 else 'FALSIFIED — no form-independent effect detected'}")
    print("  Registered MDD +0.224 at n_eff 58.9. A falsification licenses only")
    print("  'no form-independent effect >= +0.22', which excludes the")
    print("  PD-13-rescaled prediction of +0.33. It does NOT license 'zero'.")

    print()
    print("P41.3 CROSS-FORM LEAKAGE (validity guard, mandatory reporting)")
    for arm, foreign, form in (("form-X", "has_Y", FORM_Y), ("form-Y", "has_X", FORM_X)):
        r_, _ = rate(arm, foreign)
        c_, _ = rate("control", foreign)
        print(f"  {arm:<8} carries the OTHER form {form!r}: {r_:.3f} "
              f"(control {c_:.3f})")
    print("  Non-trivial leakage would contaminate form attribution and void "
          "P41.2's partition.")

    print()
    print("P41.4 SILENCE CHECK (mandatory reporting, no bar)")
    for arm in ARMS:
        v = [x for x in rec if x["arm"] == arm]
        if v:
            k = sum(x["modeled_any"] for x in v)
            lo, hi = wilson_ci(k, len(v))
            print(f"  {arm:<10} modeled presence {k}/{len(v)} "
                  f"[{lo:.3f},{hi:.3f}]  mean {sum(x['n_sent'] for x in v)/len(v):.1f} "
                  f"sentences, {sum(x['chars'] for x in v)/len(v):.0f} chars")

    (OUT / "scored.json").write_text(json.dumps(rec, indent=1))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "seats"
    {"seats": stage_seats, "runs": stage_runs,
     "judge": stage_judge, "measure": stage_measure}[stage]()
