"""Cell 6b — generate content-controlled preference pairs for the SYNTHESIZER.

One level up from the seat pairs: the prompt is the REAL synthesis input
recorded in the audit logs (Tensions-then-Synthesis system prompt + the user
block carrying the question and every seat's actual contribution), and the
base answer is the synthesis that pipeline actually produced. chosen =
REWRITE_ADD, rejected = REWRITE_STRIP -- same five behavior families, same
gates as every seat arm, so the only variable is the locus (Lead vs seat).

Leakage: syntheses come from the 7 canonical cases by construction, so the
usual prompt-level leakage screen cannot apply. Instead we hold out ALL runs
of case 7 (the trigger-light gate) and case 6 (trigger-heavy) from pair
generation, training only on syntheses from cases 1-5. This keeps both
disposition-critical evaluation cases unseen.

Run: .venv-train/bin/python train/gen_lead_pairs.py [--limit N]
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "train"))

from gen_pairs import BEHAVIORS, chat  # noqa: E402  (shared regexes + ollama call)

OUT_DIR = ROOT / "train" / "data" / "dpo_pairs_lead"
RAW_LOG = ROOT / "train" / "data" / "dpo_pairs_lead_raw.jsonl"
IMPORTED = ROOT / "bench" / "runs" / "imported"

# Held out entirely from pair generation (the two disposition-critical cases).
HELD_OUT = ("case_6_trigger_heavy", "case_7_trigger_light")

REWRITE_ADD = """You are editing the FINAL synthesized answer produced by the lead \
agent of an expert council. Rewrite it so that it additionally exhibits these \
professional-discipline behaviors WHEREVER RELEVANT -- without changing its \
substantive content, structure, or approximate length:

1. Training-cutoff disclosure: where a rule, rate, guideline, or approval may have \
changed recently, say so explicitly ("as of my training data...", "verify current status").
2. Modeled-assumption flagging: label any estimate or assumed quantity as an \
assumption ("assuming that...", "modeled at...").
3. Precise vocabulary: make terms of art exact and distinguish near-synonyms \
explicitly where confusion is possible.
4. Jurisdictional distinguishing: where more than one jurisdiction or regulatory \
regime is in play, treat each separately and never blend them.
5. Hedged uncertainty: where a recommendation depends on contestable premises, say \
what would change it ("this may vary if...").

Preserve the two-part structure (Tensions, then Synthesis) exactly. Do NOT add new \
substantive claims. Do NOT lengthen by more than ~15%. Output ONLY the rewritten answer.

ANSWER:
{base}"""

REWRITE_STRIP = """You are editing the FINAL synthesized answer produced by the lead \
agent of an expert council. Rewrite it to REMOVE all of the following, without \
changing its substantive content, structure, or approximate length:

- any mention of training cutoffs, knowledge limits, or "verify current status" caveats
- any labeling of numbers as assumptions or estimates ("assuming", "modeled at")
- any explicit distinguishing of near-synonym terms of art
- any explicit jurisdiction-by-jurisdiction separation language (keep the substance, \
remove the meta-commentary about treating regimes separately)
- any hedging about what might vary, differ, or change

State everything with plain confidence. Preserve the two-part structure (Tensions, \
then Synthesis). Keep all substantive content. Do NOT shorten by more than ~15%. \
Output ONLY the rewritten answer.

ANSWER:
{base}"""


def behavior_counts(text: str) -> dict[str, int]:
    return {b: sum(len(re.findall(p, text, re.I)) for p in pats)
            for b, pats in BEHAVIORS.items()}


def load_syntheses() -> list[dict]:
    """Every recorded synthesis with its full input messages, cases 1-5 only."""
    out = []
    for f in sorted(IMPORTED.glob("*.json")):
        if any(h in f.name for h in HELD_OUT):
            continue
        try:
            d = json.loads(f.read_text())
        except Exception:  # noqa: BLE001
            continue
        syn = d.get("deliberation", {}).get("synthesis") or {}
        msgs = syn.get("input_messages")
        base = (syn.get("output_text") or "").strip()
        if not msgs or len(base) < 800:
            continue
        sys_p = next((m["content"] for m in msgs if m.get("role") == "system"), "")
        usr_p = next((m["content"] for m in reversed(msgs) if m.get("role") == "user"), "")
        if not sys_p or not usr_p:
            continue
        out.append({"file": f.name, "system": sys_p, "user": usr_p, "base": base})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()

    random.seed(42)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_LOG.parent.mkdir(parents=True, exist_ok=True)

    items = load_syntheses()
    # de-duplicate near-identical syntheses (same case, repeated seeds) by base prefix
    seen: set[str] = set()
    uniq = []
    for it in items:
        key = it["base"][:400]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    random.shuffle(uniq)
    uniq = uniq[:args.limit]
    print(f"synthesis pool: {len(items)} recorded -> {len(uniq)} unique (cases 1-5)", flush=True)

    done: set[str] = set()
    if RAW_LOG.exists():
        for line in RAW_LOG.open():
            try:
                done.add(json.loads(line)["file"])
            except Exception:  # noqa: BLE001
                pass
        print(f"resuming: {len(done)} already generated", flush=True)

    kept = 0
    with RAW_LOG.open("a") as raw:
        for i, it in enumerate(uniq):
            if it["file"] in done:
                continue
            t0 = time.time()
            chosen = chat([{"role": "user", "content": REWRITE_ADD.format(base=it["base"])}])
            rejected = chat([{"role": "user", "content": REWRITE_STRIP.format(base=it["base"])}])
            cb, rb = behavior_counts(chosen), behavior_counts(rejected)
            c_distinct = sum(1 for v in cb.values() if v > 0)
            r_total = sum(rb.values())
            ratio = len(chosen) / max(len(rejected), 1)
            ok = (c_distinct >= 2 and r_total == 0 and 0.8 <= ratio <= 1.4)
            rec = {"file": it["file"], "system": it["system"], "user": it["user"],
                   "base": it["base"], "chosen": chosen, "rejected": rejected,
                   "chosen_behaviors": cb, "rejected_behaviors": rb,
                   "len_ratio": round(ratio, 3), "pass": ok}
            raw.write(json.dumps(rec, ensure_ascii=False) + "\n")
            raw.flush()
            kept += int(ok)
            print(f"[{i+1}/{len(uniq)}] {'PASS' if ok else 'drop'} "
                  f"(chosen {c_distinct}/5, rejected {r_total}, ratio {ratio:.2f}, "
                  f"{time.time()-t0:.0f}s) kept={kept}", flush=True)

    print(f"generation done: {kept} passing (strict gate)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
