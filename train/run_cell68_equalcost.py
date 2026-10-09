"""Cell 68 — the founding question at equal cost, on public items with headroom.

Design: RUNBOOK_PAPER_HARDENING.md "CELL 68 PRE-REGISTRATION" (2026-10-01,
design only). Execution: "CELL 68 EXECUTION" (frozen before the screen).

Does a council of role-prompted specialists answer more accurately than the
same model working alone, when the comparison is fair on cost and the items
leave room to improve? One model (gpt-oss:20b) plays every part.

Items: MMLU-Pro test split (TIGER-Lab, MIT licence), categories law, health
and business; ten-option multiple choice with a fixed key, scored by script.

Arms, all on the same screened items, one model, one session:
  (a) direct     one answer                                        1 call
  (b) vote       four direct answers, plurality vote               4 calls
  (b2) selfmoa   three direct answers + the editor                 4 calls
  (c) pipeline   three role-prompted answers + the same editor     4 calls
  (d) chain      the assembled chain (plan, specialists, tension
                 list, one follow-up, final answer)                about 8 calls
Arms (a), (b) and (b2) share the four direct draws of a replicate: (a) is
their mean accuracy, (b) their vote, (b2) edits draws 0 to 2. (b2) and (c)
differ in one factor only: the proposers' system prompt.

Run:  .venv/bin/python train/run_cell68_equalcost.py smoke         (validation split only; timing and parser)
      .venv/bin/python train/run_cell68_equalcost.py screen
      .venv/bin/python train/run_cell68_equalcost.py screenreport
      .venv/bin/python train/run_cell68_equalcost.py runs           (arms a, b, b2, c)
      .venv/bin/python train/run_cell68_equalcost.py chain          (arm d)
      .venv/bin/python train/run_cell68_equalcost.py measure
      .venv/bin/python train/run_cell68_equalcost.py selftest      (offline checks of parser and vote)
"""
from __future__ import annotations

import collections
import hashlib
import json
import random
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gst" / "src"))

from gst import runlog                                               # noqa: E402
from gst.gates import FABRICATION_BLOCKLIST, blocklist_gate          # noqa: E402
from gst.smallcluster import sign_flip_p, t_interval                 # noqa: E402
from train.run_cell30_descaffold import SEATS                        # noqa: E402
from train.run_cell44_reconsult import S1_PROMPT                     # noqa: E402
from train.run_cell57_planner import PLANNER_PROMPT as IDENTIFY      # noqa: E402
from train.run_cell59_subquestions import parse_plan                 # noqa: E402
from train.run_cell60_accuracy import S2_ANSWER                      # noqa: E402
from train.run_integration_demo import FOLLOWUP, ROSTER, SUBQ_PROMPT, _THINK  # noqa: E402

REGISTRATION = runlog.registration_for("68", ROOT)
EXT = ROOT / "bench" / "external" / "mmlu_pro"
TEST = EXT / "test-00000-of-00001.parquet"
VALID = EXT / "validation-00000-of-00001.parquet"
TEST_SHA = "0e24a191921c2f453518a537a8b2117bd137e7714d4ef1565e9ba06c1ecb9ad8"
VALID_SHA = "139423c23722e480c807ac4a191409a710cfce4eba744c1d641cf88e730e2078"
OUT = ROOT / "bench" / "analysis" / "cell68"
SCREEN_RUNS = ROOT / "bench" / "runs" / "cell68_screen.jsonl"
RUNS = ROOT / "bench" / "runs" / "cell68_runs.jsonl"
MODEL = "gpt-oss:20b"
ROLES = ("healthcare", "legal", "finance")
CATS = ("law", "health", "business")
LETTERS = "ABCDEFGHIJ"

# ---- frozen in the execution entry
KEEP_PER_CAT = 50       # stop screening a category once this many items are kept
MAX_CAND = 400          # ... or once this many candidates have been screened
MIN_TOTAL = 60          # fewer kept items in all: the runs do not start
SCREEN_DRAWS = 6        # keep items right in 2 to 4 of 6 direct draws
REPS = 3                # replicates of every arm per kept item
N_DIRECT = 4            # direct draws per replicate
T_DRAW, T_EDIT = 0.7, 0.6
TOK_LONG, TOK_SHORT = 16384, 4096
SMALLEST = 0.05         # smallest difference worth detecting; P68.3's margin

DIRECT_SYS = ("You are an analyst answering a question for a decision-maker. "
              "Be careful and exact.")
ANSWER_LINE = ("\n\nWork step by step, then end your reply with a final line of exactly:\n"
               "ANSWER: <letter>")
EDITOR_SYS = ("You are the lead analyst. Three analysts have written the contributions "
              "below. Answer the decision-maker's question. Work step by step, then end "
              "your reply with a final line of exactly:\nANSWER: <letter>")
S2_LETTER = S2_ANSWER.replace("ANSWER: <number>", "ANSWER: <letter>")
assert S2_LETTER != S2_ANSWER


# ---------------------------------------------------------------- items

def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_items(path: Path, sha: str) -> list[dict]:
    """MMLU-Pro rows in the three categories. Options equal to 'N/A' are
    padding and are dropped; the key is remapped to the remaining list."""
    import pyarrow.parquet as pq
    if _sha256(path) != sha:
        raise SystemExit(f"{path.name}: SHA-256 differs from the manifest (docs/EXTERNAL_DATA.md)")
    out = []
    for r in pq.read_table(path).to_pylist():
        if r["category"] not in CATS:
            continue
        keep = [(i, o) for i, o in enumerate(r["options"]) if str(o).strip() != "N/A"]
        idx = [i for i, _ in keep]
        if r["answer_index"] not in idx:
            raise SystemExit(f"item {r['question_id']}: key points at a padding option")
        opts = [str(o).strip() for _, o in keep]
        letter = LETTERS[idx.index(r["answer_index"])]
        if len(opts) == len(r["options"]) and letter != r["answer"]:
            raise SystemExit(f"item {r['question_id']}: answer letter and index disagree")
        out.append({"id": f"q{r['question_id']}", "qid": r["question_id"], "category": r["category"],
                    "src": r["src"], "question": r["question"].strip(), "options": opts, "key": letter})
    return out


def candidate_order(items: list[dict]) -> dict[str, list[dict]]:
    """Per category, a fixed order that no one chose: sorted by a hash of the id."""
    by = collections.defaultdict(list)
    for it in items:
        by[it["category"]].append(it)
    return {c: sorted(v, key=lambda it: hashlib.sha256(f"cell68|{it['id']}".encode()).hexdigest())
            for c, v in by.items()}


def qtext(it: dict) -> str:
    return (it["question"] + "\n\nOptions:\n"
            + "\n".join(f"{LETTERS[i]}. {o}" for i, o in enumerate(it["options"])))


# ---------------------------------------------------------------- scoring

def parse_letter(txt: str | None, n_opts: int) -> str | None:
    """The letter on the LAST line that starts with 'ANSWER' (any case, after
    markdown marks). Accepts 'C', '(C)', '**C**', 'C.', 'C) text', 'Option C'.
    Anything else, or no such line, is no answer."""
    valid = LETTERS[:n_opts]
    for line in reversed((txt or "").splitlines()):
        s = line.strip().lstrip("*#>_ `").replace("**", "").replace("__", "")
        if not s.upper().startswith("ANSWER"):
            continue
        tail = s[6:].lstrip(" *_")
        if tail.startswith(("：", ":")):
            tail = tail[1:]
        elif tail[:2].lower() == "is":
            tail = tail[2:]
        tail = tail.strip().strip("*_`'\"[]{}()$\\ ")
        if tail.lower().startswith("option "):
            tail = tail[7:].strip("*_`'\"[]{}() ")
        if tail.startswith("\\boxed{") or tail.startswith("boxed{"):
            tail = tail.split("{", 1)[1]
        if tail and tail[0].upper() in valid and (len(tail) == 1 or not tail[1].isalpha()):
            return tail[0].upper()
        return None
    return None


def vote(letters: list[str | None]) -> str | None:
    """Plurality of the parsed letters; a tie goes to the tied letter that
    appears first in draw order. No parsed letter: no answer."""
    got = [x for x in letters if x]
    if not got:
        return None
    c = collections.Counter(got)
    top = max(c.values())
    return next(x for x in got if c[x] == top)


# ---------------------------------------------------------------- generation

def gen(system: str, user: str, *, temp: float, toks: int, tag: str, audit: list) -> str | None:
    for attempt in range(4):
        if attempt:
            time.sleep(10 * attempt)
        text, meta = runlog.chat_logged(MODEL, system, user, temperature=temp, max_tokens=toks,
                                        seed=runlog.seed_for(tag) + attempt)
        audit.append({"step": tag.rsplit("|", 1)[-1], **meta})
        if text and text.strip():
            return _THINK.sub("", text).strip()
    return None


def _ctx(audit: list) -> bool:
    return any(a.get("ctx_hit") for a in audit)


def _tok(audit: list) -> int:
    return sum((a.get("prompt_tokens") or 0) + (a.get("output_tokens") or 0) for a in audit)


def _row(it: dict, rep: int, unit: str, reply: str | None, audit: list, **extra) -> dict:
    letter = parse_letter(reply, len(it["options"]))
    row = {"run_id": f"{it['id']}|r{rep}|{unit}", "item": it["id"], "category": it["category"],
           "src": it["src"], "rep": rep, "unit": unit, "letter": letter, "ok": letter == it["key"],
           "ctx_hit": _ctx(audit), "tokens": _tok(audit), "calls": len(audit), "output": reply,
           **extra, "steps": audit}
    return runlog.stamp(row, None, root=ROOT, script=Path(__file__), registration=REGISTRATION)


def direct_draw(it: dict, tag: str) -> tuple[str | None, list]:
    audit: list = []
    return gen(DIRECT_SYS, qtext(it) + ANSWER_LINE, temp=T_DRAW, toks=TOK_LONG, tag=tag, audit=audit), audit


def editor(it: dict, texts: list[str], tag: str, audit: list) -> str | None:
    pile = "\n\n".join(f"--- ANALYST {LETTERS[i]} ---\n{t}" for i, t in enumerate(texts))
    return gen(EDITOR_SYS, f"{pile}\n\nQuestion:\n{qtext(it)}", temp=T_EDIT, toks=TOK_LONG, tag=tag, audit=audit)


def pipeline(it: dict, rep: int, prefix: str = "") -> dict | None:
    """(c): three role-prompted proposers, same user message as a direct draw,
    then the same editor as (b2). Pile order shuffled per item and replicate."""
    key = f"{prefix}{it['id']}|r{rep}"
    order = list(ROLES)
    random.Random(f"cell68|{it['id']}|{rep}").shuffle(order)
    audit: list = []
    texts = []
    for role in order:
        t = gen(SEATS[role], qtext(it) + ANSWER_LINE, temp=T_DRAW, toks=TOK_LONG, tag=f"{key}|seat-{role}", audit=audit)
        if t is None:
            return None
        texts.append(t)
    out = editor(it, texts, f"{key}|pipe-editor", audit)
    if out is None:
        return None
    return _row(it, rep, "pipeline", out, audit, order=order,
                proposer_letters=[parse_letter(t, len(it["options"])) for t in texts], proposals=texts)


def chain(it: dict, rep: int, prefix: str = "") -> dict | None:
    """(d): the assembled chain of Cells 60 and 67, unchanged except that the
    final line asks for a letter."""
    key = f"{prefix}{it['id']}|r{rep}"
    q = qtext(it)
    audit: list = []
    ids = gen(IDENTIFY, f"Question:\n{q}", temp=0.7, toks=TOK_SHORT, tag=f"{key}|identify", audit=audit)
    if ids is None:
        return None
    quants = [l.strip() for l in ids.splitlines() if l.strip()][:6]
    plan = None
    for n in range(3):
        t = gen("Follow the output format exactly.",
                SUBQ_PROMPT.format(quantities="\n".join(quants)) + f"\n\nQuestion:\n{q}",
                temp=0.7, toks=TOK_SHORT, tag=f"{key}|plan{n}", audit=audit)
        plan = parse_plan(t)
        if plan:
            break
    if not plan:
        return _row(it, rep, "chain", None, audit, invalid="plan-parse")
    contribs = {}
    for role in ROLES:
        a, b = tuple(r for r in ROLES if r != role)
        c = gen(SEATS[role], f"Case:\n{q}\n\nYour sub-question:\n{plan[role]}\n\n" + ROSTER.format(a=a, b=b),
                temp=0.7, toks=TOK_SHORT, tag=f"{key}|seat-{role}", audit=audit)
        if c is None:
            return None
        contribs[role] = c
    pile = "\n\n".join(f"--- {r.upper()} SPECIALIST CONTRIBUTION ---\n{contribs[r]}" for r in ROLES)
    s1 = gen(S1_PROMPT, f"{pile}\n\nQuestion:\n{q}", temp=0.6, toks=TOK_SHORT, tag=f"{key}|tensions", audit=audit)
    if s1 is None:
        return None
    route, tension = None, None
    for line in (l.strip() for l in s1.splitlines() if l.strip()):
        for r in ROLES:
            if r in line.lower():
                route, tension = r, line
                break
        if route:
            break
    reply_block = ""
    if route:
        reply = gen(SEATS[route], f"Case:\n{q}\n\nYour earlier contribution:\n{contribs[route]}\n\n"
                    + FOLLOWUP.format(tension=tension), temp=0.7, toks=TOK_SHORT, tag=f"{key}|followup", audit=audit)
        if reply is not None and not blocklist_gate(reply, FABRICATION_BLOCKLIST):
            reply_block = f"--- FOLLOW-UP CLARIFICATION (from the {route} specialist) ---\n{reply}\n\n"
    s2 = gen(S2_LETTER, f"{pile}\n\n--- YOUR TENSION LIST ---\n{s1}\n\n{reply_block}Question:\n{q}",
             temp=0.6, toks=TOK_LONG, tag=f"{key}|answer", audit=audit)
    if s2 is None:
        return None
    return _row(it, rep, "chain", s2, audit, route=route)


# ---------------------------------------------------------------- stages

def _preflight() -> None:
    t, _ = runlog.chat_logged(MODEL, "Reply with the single word OK.", "ping", temperature=0.0, max_tokens=256)
    if not t or not t.strip():
        raise SystemExit("PREFLIGHT FAILED")


def stage_smoke() -> None:
    """Validation split only (70 few-shot exemplars, not in the test pool).
    One item per category through every arm, and one direct draw on each of
    the other validation items of these categories, for timing and for a
    manual read of the parser. Written to bench/analysis/cell68/smoke.jsonl;
    not registered data."""
    items = load_items(VALID, VALID_SHA)
    _preflight()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "smoke.jsonl"
    path.unlink(missing_ok=True)
    t_all = time.time()
    first = {}
    for it in items:
        first.setdefault(it["category"], it)
    for it in items:
        if first[it["category"]] is it:
            continue
        t0 = time.time()
        reply, audit = direct_draw(it, f"SMOKE|{it['id']}|d")
        row = _row(it, 0, "direct", reply, audit)
        runlog.append_jsonl(path, row)
        print(f"  direct {it['id']:<8} {it['category']:<9} letter {row['letter']} key {it['key']} "
              f"{time.time()-t0:.0f}s tokens {row['tokens']}", flush=True)
    for cat, it in first.items():
        t0 = time.time()
        drafts = []
        for k in range(N_DIRECT):
            reply, audit = direct_draw(it, f"SMOKE|{it['id']}|r0|direct{k}")
            row = _row(it, 0, f"direct{k}", reply, audit)
            runlog.append_jsonl(path, row)
            drafts.append(row)
        audit = []
        out = editor(it, [d["output"] or "" for d in drafts[:3]], f"SMOKE|{it['id']}|r0|selfmoa", audit)
        runlog.append_jsonl(path, _row(it, 0, "selfmoa", out, audit))
        for name, fn in (("pipeline", pipeline), ("chain", chain)):
            row = fn(it, 0, prefix="SMOKE|")
            if row is None:
                raise SystemExit(f"smoke: {name} failed on {it['id']}")
            runlog.append_jsonl(path, row)
        print(f"  all arms {it['id']} ({cat}): {time.time()-t0:.0f}s", flush=True)
    rows = runlog.read_jsonl(path)
    by = collections.defaultdict(list)
    for r in rows:
        by[r["unit"].rstrip("0123456789")].append(r)
    print(f"\n  {'unit':<10}{'n':>4}{'parsed':>8}{'right':>7}{'median s':>10}{'median tokens':>15}{'ctx hit':>9}")
    for u, v in by.items():
        walls = [sum(a.get("wall_s") or 0 for a in r["steps"]) for r in v]
        print(f"  {u:<10}{len(v):>4}{sum(r['letter'] is not None for r in v):>8}{sum(r['ok'] for r in v):>7}"
              f"{st.median(walls):>10.0f}{st.median([r['tokens'] for r in v]):>15.0f}{sum(r['ctx_hit'] for r in v):>9}")
    print(f"\n  smoke total {time.time()-t_all:.0f}s; replies in {path.relative_to(ROOT)} for the parser read")


def _decide(oks: list[bool]) -> str | None:
    c = sum(oks)
    w = len(oks) - c
    if c >= 2 and w >= 2:
        return "keep"
    if c >= SCREEN_DRAWS - 1 or w >= SCREEN_DRAWS - 1:
        return "reject"
    return None


def _screen_state() -> dict:
    draws = collections.defaultdict(list)
    for r in sorted(runlog.read_jsonl(SCREEN_RUNS), key=lambda r: r["k"]):
        draws[r["item"]].append(r["ok"])
    return draws


def stage_screen() -> None:
    """Direct draws only; never sees a pipeline answer. Draws stop as soon as
    the 2-to-4-of-6 decision is fixed, which gives the same decision as six
    draws. Categories are screened in turn, one candidate at a time."""
    order = candidate_order(load_items(TEST, TEST_SHA))
    _preflight()
    draws = _screen_state()
    t0, n_new = time.time(), 0
    for i in range(MAX_CAND):
        for cat in CATS:
            cands = order[cat]
            kept = sum(_decide(draws[it["id"]]) == "keep" for it in cands[:i])
            if kept >= KEEP_PER_CAT or i >= len(cands):
                continue
            it = cands[i]
            while _decide(draws[it["id"]]) is None:
                k = len(draws[it["id"]])
                reply, audit = direct_draw(it, f"c68|screen|{it['id']}|{k}")
                letter = parse_letter(reply, len(it["options"]))
                runlog.append_jsonl(SCREEN_RUNS, runlog.stamp(
                    {"run_id": f"screen|{it['id']}|{k}", "item": it["id"], "category": cat, "src": it["src"],
                     "k": k, "letter": letter, "ok": letter == it["key"], "ctx_hit": _ctx(audit),
                     "tokens": _tok(audit), "tail": (reply or "")[-600:], "steps": audit},
                    None, root=ROOT, script=Path(__file__), registration=REGISTRATION))
                draws[it["id"]].append(letter == it["key"])
                n_new += 1
            if n_new and n_new % 20 == 0:
                print(f"  {n_new} draws, {(time.time()-t0)/3600:.1f}h; candidate {i+1}", flush=True)
    stage_screenreport()


def stage_screenreport() -> None:
    order = candidate_order(load_items(TEST, TEST_SHA))
    draws = _screen_state()
    keep, report = [], {}
    print(f"  {'category':<10}{'screened':>9}{'kept':>6}{'right (all draws)':>19}{'draws':>7}")
    for cat in CATS:
        seen = [it for it in order[cat] if _decide(draws[it["id"]])]
        k = [it["id"] for it in seen if _decide(draws[it["id"]]) == "keep"]
        n = sum(len(draws[it["id"]]) for it in seen)
        acc = sum(sum(draws[it["id"]]) for it in seen) / n if n else float("nan")
        report[cat] = {"screened": len(seen), "kept": len(k), "draw_accuracy": acc, "draws": n}
        keep += k
        print(f"  {cat:<10}{len(seen):>9}{len(k):>6}{acc:>19.3f}{n:>7}")
    ok = len(keep) >= MIN_TOTAL
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "screen.json").write_text(json.dumps({"keep": keep, "by_category": report, "pass": ok}, indent=1))
    print(f"SCREEN: {len(keep)} items kept (runs need {MIN_TOTAL}) -> {'PASS' if ok else 'FAIL: runs do not start'}")


def _kept() -> list[dict]:
    p = OUT / "screen.json"
    if not p.exists() or not json.loads(p.read_text())["pass"]:
        raise SystemExit("the screen has not passed: runs not permitted")
    ids = json.loads(p.read_text())["keep"]
    by = {it["id"]: it for it in load_items(TEST, TEST_SHA)}
    return sorted((by[i] for i in ids), key=lambda it: hashlib.sha256(f"cell68run|{it['id']}".encode()).hexdigest())


def _grid(units: tuple[str, ...]) -> None:
    items = _kept()
    _preflight()
    done = {r["run_id"]: r for r in runlog.read_jsonl(RUNS)}
    t0, fails, n_items = time.time(), 0, 0
    for it in items:
        for rep in range(REPS):
            for unit in units:
                rid = f"{it['id']}|r{rep}|{unit}"
                if rid in done:
                    continue
                if unit.startswith("direct"):
                    reply, audit = direct_draw(it, f"c68|{it['id']}|r{rep}|{unit}")
                    row = _row(it, rep, unit, reply, audit) if reply is not None else None
                elif unit == "selfmoa":
                    drafts = [done.get(f"{it['id']}|r{rep}|direct{k}") for k in range(3)]
                    if any(d is None for d in drafts):
                        continue
                    audit = []
                    out = editor(it, [d["output"] or "" for d in drafts], f"c68|{it['id']}|r{rep}|selfmoa", audit)
                    row = _row(it, rep, "selfmoa", out, audit) if out is not None else None
                elif unit == "pipeline":
                    row = pipeline(it, rep, prefix="c68|")
                else:
                    row = chain(it, rep, prefix="c68|")
                if row is None:
                    fails += 1
                    print(f"  EMPTY generation on {rid} (consecutive {fails})", flush=True)
                    if fails >= 3:
                        raise SystemExit("ABORTING — three consecutive failures; resumable.")
                    continue
                fails = 0
                runlog.append_jsonl(RUNS, row)
                done[rid] = row
        n_items += 1
        el = time.time() - t0
        print(f"  {n_items}/{len(items)} items, {el/3600:.1f}h, ~{el/n_items*(len(items)-n_items)/3600:.1f}h left",
              flush=True)


def stage_runs() -> None:
    _grid(tuple(f"direct{k}" for k in range(N_DIRECT)) + ("selfmoa", "pipeline"))
    print("cell68 runs (arms a, b, b2, c) complete")


def stage_chain() -> None:
    _grid(("chain",))
    print("cell68 chain (arm d) complete")


# ---------------------------------------------------------------- measure

def arm_scores(rows: list[dict], keys: dict) -> tuple[dict, dict]:
    """Per arm, per item: mean accuracy over replicates; and per arm: run
    counts. Runs that hit the context limit are set aside and counted."""
    by = collections.defaultdict(dict)
    for r in rows:
        by[(r["item"], r["rep"])][r["unit"]] = r
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    cnt = collections.defaultdict(collections.Counter)
    for (item, rep), u in by.items():
        direct = [u.get(f"direct{k}") for k in range(N_DIRECT)]
        if all(d is not None for d in direct):
            ds = [d for d in direct if not d["ctx_hit"]]
            for d in ds:
                acc["a"][item].append(float(d["ok"]))
                cnt["a"]["runs"] += 1
                cnt["a"]["answered"] += d["letter"] is not None
            cnt["a"]["set_aside"] += len(direct) - len(ds)
            if len(ds) == len(direct):
                v = vote([d["letter"] for d in direct])
                acc["b"][item].append(float(v is not None and v == keys[item]))
                cnt["b"]["runs"] += 1
                cnt["b"]["answered"] += v is not None
            else:
                cnt["b"]["set_aside"] += 1
        for unit, arm in (("selfmoa", "b2"), ("pipeline", "c"), ("chain", "d")):
            r = u.get(unit)
            if r is None:
                continue
            if r["ctx_hit"]:
                cnt[arm]["set_aside"] += 1
                continue
            acc[arm][item].append(float(r["ok"]))
            cnt[arm]["runs"] += 1
            cnt[arm]["answered"] += r["letter"] is not None
            cnt[arm]["invalid"] += bool(r.get("invalid"))
    return {a: {i: st.mean(v) for i, v in d.items()} for a, d in acc.items()}, cnt


def paired(scores: dict, hi_arm: str, lo_arm: str, items: list[str] | None = None) -> dict | None:
    a, b = scores.get(hi_arm, {}), scores.get(lo_arm, {})
    ids = [i for i in (items or a) if i in a and i in b]
    if len(ids) < 2:
        return None
    d = [a[i] - b[i] for i in ids]
    m, lo, hi = t_interval(d)
    return {"mean": m, "lo": lo, "hi": hi, "p": sign_flip_p(d), "n": len(ids)}


def stage_measure() -> None:
    items = {it["id"]: it for it in load_items(TEST, TEST_SHA)}
    rows = runlog.read_jsonl(RUNS)
    scr = json.loads((OUT / "screen.json").read_text())
    scores, cnt = arm_scores(rows, {i: it["key"] for i, it in items.items()})
    names = {"a": "direct, one answer", "b": "vote of four direct", "b2": "three direct + editor",
             "c": "pipeline: three roles + editor", "d": "assembled chain"}
    print("=" * 78)
    print("CELL 68 — the founding question at equal cost, on public items with headroom")
    print("=" * 78)
    print(f"screen: {len(scr['keep'])} items kept; " + "; ".join(
        f"{c} {v['kept']} of {v['screened']} (draw accuracy {v['draw_accuracy']:.3f})"
        for c, v in scr["by_category"].items()))
    tok = collections.defaultdict(list)
    for r in rows:
        tok[{"selfmoa": "b2", "pipeline": "c", "chain": "d"}.get(r["unit"], "a")].append(r["tokens"])
    print(f"\n  {'arm':<34}{'items':>6}{'runs':>6}{'accuracy':>10}{'answered':>10}{'set aside':>11}{'tokens/run':>12}")
    for arm in ("a", "b", "b2", "c", "d"):
        s = scores.get(arm, {})
        c = cnt[arm]
        if not s:
            print(f"  {arm:<3}{names[arm]:<31}  not run")
            continue
        if arm == "b":
            t = N_DIRECT * st.mean(tok["a"])
        elif arm == "b2":
            t = st.mean(tok["b2"]) + 3 * st.mean(tok["a"])
        else:
            t = st.mean(tok[arm])
        print(f"  {arm:<3}{names[arm]:<31}{len(s):>6}{c['runs']:>6}{st.mean(s.values()):>10.3f}"
              f"{c['answered']/max(c['runs'],1):>10.3f}{c['set_aside']:>11}{t:>12.0f}")
    if cnt["d"]["invalid"]:
        print(f"  chain runs whose plan could not be parsed (scored as no answer): {cnt['d']['invalid']}")

    def fmt(d):
        return "n/a" if not d else (f"{d['mean']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}]  sign-flip p = {d['p']:.4f}"
                                    f"  (n = {d['n']} items)")
    p1, p2, p3 = paired(scores, "c", "a"), paired(scores, "c", "b2"), paired(scores, "d", "c")
    print(f"\nP68.1  pipeline minus one direct answer (system level, 4 calls vs 1): {fmt(p1)}")
    print(f"P68.2  pipeline minus three direct + the same editor (one factor):  {fmt(p2)}")
    print(f"P68.3  chain minus pipeline (system level; margin -{SMALLEST}):         {fmt(p3)}")
    print("\nVERDICT LINES (as registered)")
    for pid, d in (("P68.1", p1), ("P68.2", p2)):
        if not d:
            print(f"  {pid}: NOT EVALUABLE — arm not run")
        elif d["lo"] > 0:
            print(f"  {pid}: SUPPORTED — {fmt(d)}")
        elif d["hi"] < 0:
            print(f"  {pid}: FALSIFIED — the pipeline is less accurate: {fmt(d)}")
        else:
            small = " ; any advantage is below the smallest difference worth detecting" if d["hi"] < SMALLEST else ""
            print(f"  {pid}: NOT SHOWN — the interval includes zero{small}")
    if not p3:
        print("  P68.3: NOT EVALUABLE — arm (d) not run")
    elif p3["lo"] > -SMALLEST:
        print(f"  P68.3: SUPPORTED — no worse than the pipeline by more than {SMALLEST}: {fmt(p3)}")
    elif p3["hi"] < 0:
        print(f"  P68.3: FALSIFIED — the chain is less accurate: {fmt(p3)}")
    else:
        print("  P68.3: NOT SHOWN — the interval reaches below the margin and above zero")
    print("\ndescriptive (registered as descriptive, not tests)")
    for hi_, lo_, what in (("c", "b", "pipeline minus vote of four (the design's P68.2; two factors)"),
                           ("b", "a", "vote of four minus one answer"),
                           ("b2", "b", "three direct + editor minus vote of four (4 calls each)"),
                           ("b2", "a", "three direct + editor minus one answer")):
        print(f"  {what:<64}{fmt(paired(scores, hi_, lo_))}")
    print("\n  by category (P68.1, P68.2, P68.3 differences)")
    for cat in CATS:
        ids = [i for i in scores.get("a", {}) if items[i]["category"] == cat]
        print(f"   {cat:<10}" + "   ".join(
            f"{p}: {fmt(paired(scores, h, l, ids))}" for p, h, l in (("1", "c", "a"), ("2", "c", "b2"), ("3", "d", "c"))))
    print("\n  by original source, 10 or more items (P68.2 difference)")
    srcs = collections.Counter(items[i]["src"] for i in scores.get("a", {}))
    for src, n in srcs.most_common():
        if n >= 10:
            ids = [i for i in scores["a"] if items[i]["src"] == src]
            print(f"   {src:<34}{fmt(paired(scores, 'c', 'b2', ids))}")
    pr = [r for r in rows if r["unit"] == "pipeline" and not r["ctx_hit"]]
    if pr:
        agree = sum(1 for r in pr if r["letter"] and r["letter"] in r["proposer_letters"]) / len(pr)
        print(f"\n  pipeline: final letter is one a proposer gave {agree:.3f}; proposers' letters parsed "
              f"{sum(x is not None for r in pr for x in r['proposer_letters'])/(3*len(pr)):.3f}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "measured.json").write_text(json.dumps(
        {"arms": {a: {"items": len(s), "accuracy": st.mean(s.values()) if s else None, **cnt[a]}
                  for a, s in scores.items()},
         "P68.1": p1, "P68.2": p2, "P68.3": p3}, indent=1, default=float))


# ---------------------------------------------------------------- offline checks

def stage_selftest() -> None:
    cases = [("…\nANSWER: C", "C"), ("**ANSWER: C**", "C"), ("ANSWER: (C)", "C"), ("Answer: c", "C"),
             ("ANSWER: C. Because the statute", "C"), ("ANSWER: C) negligence", "C"), ("ANSWER: Option C", "C"),
             ("ANSWER: **(J)**", "J"), ("ANSWER: $\\boxed{D}$", "D"), ("ANSWER - B", None),
             ("ANSWER: Because of A", None), ("The answer is C", None), ("ANSWER: K", None),
             ("ANSWER: A\nANSWER: B", "B"), ("## ANSWER: E", "E"), ("ANSWER:F", "F"), ("ANSWER is G", "G"),
             ("ANSWER: none of these", None), ("", None), (None, None)]
    bad = [(t, want, parse_letter(t, 10)) for t, want in cases if parse_letter(t, 10) != want]
    for t, want, got in bad:
        print(f"  parser: {t!r} -> {got}, expected {want}")
    vcases = [(["A", "B", "A", "C"], "A"), (["B", "A", "A", "B"], "B"), ([None, "C", None, "D"], "C"),
              ([None] * 4, None), (["D", None, "E", "E"], "E")]
    vbad = [(v, w, vote(v)) for v, w in vcases if vote(v) != w]
    for v, w, got in vbad:
        print(f"  vote: {v} -> {got}, expected {w}")
    dc = [([True, True, False, False], "keep"), ([True] * 5, "reject"), ([False] * 5, "reject"),
          ([True] * 4 + [False], None), ([True, False, False, False, False], None), ([True] + [False] * 5, "reject"), ([True, True, True], None)]
    dbad = [(o, w, _decide(o)) for o, w in dc if _decide(o) != w]
    for o, w, got in dbad:
        print(f"  screen rule: {o} -> {got}, expected {w}")
    # the early stop gives the same decision as six draws, for every sequence
    import itertools
    mism = 0
    for seq in itertools.product((True, False), repeat=SCREEN_DRAWS):
        full = "keep" if 2 <= sum(seq) <= 4 else "reject"
        for k in range(1, SCREEN_DRAWS + 1):
            d = _decide(list(seq[:k]))
            if d:
                mism += d != full
                break
    print(f"  early stop agrees with six draws on all {2**SCREEN_DRAWS} sequences: {mism == 0}")
    print("SELFTEST", "PASSES" if not (bad or vbad or dbad or mism) else "FAILS")


if __name__ == "__main__":
    {"smoke": stage_smoke, "screen": stage_screen, "screenreport": stage_screenreport, "runs": stage_runs,
     "chain": stage_chain, "measure": stage_measure, "selftest": stage_selftest}[sys.argv[1]]()
