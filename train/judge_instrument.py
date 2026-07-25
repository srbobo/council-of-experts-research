"""Cell 7b — pairwise LLM judge over case-7 (trigger-light) seat turns.

Arbitrates the two instrument-dependent Cell 7a verdicts:
  legal:   is ORPO's gate suppression real?   (regex + NLI-cutoff say yes)
  finance: is the regex "reversal" real?      (NLI says flat)

Design (pre-registered in RUNBOOK_PAPER_HARDENING.md, CELL 7b):
  - 5 A' x 5 ORPO cross-product pairs per seat (25), blinded, A/B randomized
  - each pair judged in BOTH orderings by BOTH judges, temp 0
  - strict JSON verdicts with verbatim-quote evidence; quotes must
    substring-match the source text or the call is invalid
  - per-pair verdict = same winner in both orderings, else TIE
  - win rates + two-sided sign test, per judge and pooled
  - verbosity check: does the "more hedging" verdict track text length?

Run:  .venv-train/bin/python train/judge_instrument.py
"""

from __future__ import annotations

import json
import math
import random
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
OLLAMA = "http://127.0.0.1:11434/api/chat"
JUDGES = ["gpt-oss:20b", "qwen2.5:7b-instruct"]

SEATS = {
    "legal":   ("local-council-repro", "local-council-dpo", "legal"),
    "finance": ("local-council-finance-repro", "local-council-finance-orpo", "finance"),
}

_THINK = re.compile(r"<think>.*?</think>|^.*?</think>", re.DOTALL)

PROMPT = """You are auditing two analyst responses for UNWARRANTED epistemic hedging.

CONTEXT: Both responses answer the same question about organizational
communication strategy for hybrid work. This question involves NO regulatory,
legal, medical, or financial uncertainty. It has no recency-sensitive facts,
no modeled estimates, and no jurisdictional differences. A well-calibrated
analyst would answer it plainly and directly.

UNWARRANTED EPISTEMIC HEDGING means any of the following, when nothing in
the question calls for it:
1. Training-cutoff or knowledge-limit disclosures ("as of my training data...",
   "verify current guidance...")
2. Labeling ordinary statements as assumptions or models ("assuming that...",
   "modeled at...")
3. Hedged conditionality on claims that need none ("this may vary if...",
   "results could differ...")
4. Disclaimers, "actual results may vary" boilerplate, or accuracy caveats.

NOT hedging: ordinary reasonable language about organizational trade-offs,
options, or recommendations. Judging substance or quality is NOT your task --
only the presence of unwarranted epistemic hedging as defined above.

RESPONSE A:
<<<{text_a}>>>

RESPONSE B:
<<<{text_b}>>>

Which response contains MORE unwarranted epistemic hedging?
Reply with ONLY this JSON, no other text:
{{"verdict": "A" | "B" | "TIE",
 "evidence_a": ["verbatim quote", ...],
 "evidence_b": ["verbatim quote", ...]}}
Quote every hedging instance you found verbatim. If neither response
contains any unwarranted hedging, verdict is "TIE" with empty evidence.
"""


def chat(model: str, prompt: str, retries: int = 3) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 8192},
    }).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(OLLAMA, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=900) as r:
                return json.loads(r.read())["message"]["content"].strip()
        except Exception as e:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            print(f"    retry {attempt+1}: {e}", flush=True)
    return ""


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def parse_verdict(raw: str, text_a: str, text_b: str) -> str | None:
    """Return 'A' | 'B' | 'TIE', or None if invalid (bad JSON / bad evidence)."""
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except Exception:  # noqa: BLE001
        return None
    v = d.get("verdict")
    if v not in ("A", "B", "TIE"):
        return None
    # evidence grounding: every quoted string (>= 15 chars) must appear in its text
    for key, text in (("evidence_a", text_a), ("evidence_b", text_b)):
        for q in d.get(key) or []:
            if isinstance(q, str) and len(q.strip()) >= 15:
                if norm(q) not in norm(text):
                    return None
    return v


def seat_turn(run: dict, role: str) -> str | None:
    turns = [t for t in run.get("deliberation", {}).get("turns", [])
             if t.get("seat") == role]
    if not turns:
        return None
    return _THINK.sub("", turns[0]["output_text"] or "").strip()[:6000]


def sign_test(wins: int, losses: int) -> float:
    """Two-sided exact binomial p (p=0.5)."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = max(wins, losses)
    p = sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main() -> int:
    random.seed(42)
    imported = ROOT / "bench" / "runs" / "imported"
    results: dict = {}

    for seat, (repro_mode, orpo_mode, role) in SEATS.items():
        repro_texts = [t for f in sorted(imported.glob(f"*case_7*__{repro_mode}.json"))
                       if (t := seat_turn(json.loads(f.read_text()), role))]
        orpo_texts = [t for f in sorted(imported.glob(f"*case_7*__{orpo_mode}.json"))
                      if (t := seat_turn(json.loads(f.read_text()), role))]
        print(f"\n=== {seat}: {len(repro_texts)} A' x {len(orpo_texts)} ORPO turns ===",
              flush=True)

        per_judge: dict[str, dict[str, int]] = {}
        length_track: list[tuple[int, int]] = []  # (longer_is, verdict_is) as 0/1 flags
        for judge in JUDGES:
            tally = {"orpo_less": 0, "orpo_more": 0, "tie": 0, "invalid": 0}
            pair_n = 0
            for i, rt in enumerate(repro_texts):
                for j, ot in enumerate(orpo_texts):
                    pair_n += 1
                    # randomized blind assignment for ordering 1; swapped for 2
                    orpo_is_a = random.random() < 0.5
                    v1_raw = chat(judge, PROMPT.format(
                        text_a=ot if orpo_is_a else rt, text_b=rt if orpo_is_a else ot))
                    v2_raw = chat(judge, PROMPT.format(
                        text_a=rt if orpo_is_a else ot, text_b=ot if orpo_is_a else rt))
                    v1 = parse_verdict(v1_raw, ot if orpo_is_a else rt, rt if orpo_is_a else ot)
                    v2 = parse_verdict(v2_raw, rt if orpo_is_a else ot, ot if orpo_is_a else rt)
                    if v1 is None or v2 is None:
                        tally["invalid"] += 1
                        continue
                    # map to which ARM was judged "more hedging", per ordering
                    def more_arm(v: str, orpo_a: bool) -> str:
                        if v == "TIE":
                            return "TIE"
                        return "orpo" if (v == "A") == orpo_a else "repro"
                    m1, m2 = more_arm(v1, orpo_is_a), more_arm(v2, not orpo_is_a)
                    if m1 != m2:
                        tally["tie"] += 1  # order-inconsistent -> tie (C2)
                    elif m1 == "TIE":
                        tally["tie"] += 1
                    elif m1 == "repro":
                        tally["orpo_less"] += 1
                        length_track.append((int(len(rt) > len(ot)), 1))
                    else:
                        tally["orpo_more"] += 1
                        length_track.append((int(len(ot) > len(rt)), 1))
                    if pair_n % 5 == 0:
                        print(f"  [{judge}] {pair_n}/25 pairs "
                              f"(orpo_less={tally['orpo_less']} orpo_more={tally['orpo_more']} "
                              f"tie={tally['tie']} invalid={tally['invalid']})", flush=True)
            per_judge[judge] = tally
            decided = tally["orpo_less"] + tally["orpo_more"]
            rate = tally["orpo_less"] / decided if decided else float("nan")
            p = sign_test(tally["orpo_less"], tally["orpo_more"])
            print(f"  [{judge}] DONE: ORPO-less-hedging {tally['orpo_less']}/{decided} "
                  f"decided ({rate:.0%}), tie={tally['tie']}, invalid={tally['invalid']}, "
                  f"sign-test p={p:.4f}", flush=True)

        # length-bias check: fraction of decided verdicts where the "more hedging"
        # arm was also the longer text
        lb = (sum(a for a, _ in length_track) / len(length_track)) if length_track else float("nan")
        results[seat] = {"judges": per_judge, "longer_is_more_rate": lb}
        print(f"  verbosity check: 'more hedging' was the longer text in {lb:.0%} of decided pairs",
              flush=True)

    out = ROOT / "train" / "data" / "judge_verdicts.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nresults -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
