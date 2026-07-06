"""Phase 2 — generate content-controlled DPO preference pairs.

Produces train/data/dpo_pairs/{train,valid,test}.jsonl in the format
mlx_lm_lora's DPODataset expects: {"prompt", "chosen", "rejected"}.

No "system" key: Saul's Mistral chat template rejects the system role, so
LEGAL_SYSTEM is folded into the prompt text — which exactly matches how the
Ollama runtime renders it at inference ([INST] {{.System}} {{.Prompt}} [/INST]).

Pair-construction protocol (RUNBOOK_DPO_PROMPT_TRANSFER.md):
  1. base    — gpt-oss-20b answers a legal sub-question plainly
  2. chosen  — rewrite of base WEAVING IN the disposition behaviors
  3. rejected— rewrite of base STRIPPING all disposition behaviors
The pair differs in behavior, not content or quality.

Filters (all must pass):
  - chosen exhibits >= 2 target behaviors (regex, same patterns as
    server/static/js/disposition.js)
  - rejected exhibits 0 of the 5 behaviors
  - length ratio chosen/rejected in [0.8, 1.3]  (DPO length-bias guard)
  - prompt passes the canonical-case leakage screen

Run:  .venv/bin/python train/gen_pairs.py            # needs only stdlib
      (talks to Ollama's HTTP API directly; ~5-7 h unattended for 200 prompts)
"""

from __future__ import annotations

import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "gpt-oss:20b"
OUT_DIR = Path(__file__).parent / "data" / "dpo_pairs"
RAW_LOG = Path(__file__).parent / "data" / "dpo_pairs_raw.jsonl"

# The seat prompt folded into every training prompt — must match
# council/prompts.py LEGAL_SYSTEM verbatim at training time.
sys.path.insert(0, str(Path(__file__).parent.parent))
from council.prompts import LEGAL_SYSTEM  # noqa: E402

# ---------------------------------------------------------------------------
# Behavior regexes — Python port of server/static/js/disposition.js.
# Keep in sync; these gates define pair validity.
# ---------------------------------------------------------------------------
BEHAVIORS: dict[str, list[str]] = {
    "cutoff": [
        r"training[- ]?cut[- ]?off", r"knowledge cut[- ]?off",
        r"may (?:be |have )(?:stale|outdated|out[- ]of[- ]date|evolved)",
        r"post[- ]?cut[- ]?off", r"after my training",
        r"verify (?:current|latest|recent) (?:rates|guidance|regulations|status)",
        r"as of (?:my )?(?:training|knowledge|2024|2025)",
    ],
    "modeled": [
        r"modell?ed at", r"\bassume[ds]? (?:that|the)",
        r"\bassuming (?:that|the|a |an |\d)", r"under the assumption",
        r"this assume[ds]", r"\bwe assume\b", r"\bhypothetical[ly]?\b",
    ],
    "precise": [
        r"(?:approval).*?(?:vs\.?|versus|not).*?(?:clearance)",
        r"(?:clearance).*?(?:vs\.?|versus|not).*?(?:approval)",
        r"distinguish(?:es|ing|ed)? between",
        r"(?:510\(k\)|de novo|PMA)\s+(?:clearance|approval|pathway)",
        r"\b(?:NDA|BLA)\s+approval\b",
        r"(?:regulation).*?(?:vs\.?|versus|not).*?(?:directive)",
        r"standard[- ]of[- ]care",
        r"\bholding\b.*?\bdicta\b|\bdicta\b.*?\bholding\b",
    ],
    "jurisd": [
        r"\bUK\s?GDPR\b", r"\bEU\s?GDPR\b", r"post[- ]Brexit",
        r"each\s+(?:jurisdiction|country|state|regime)",
        r"in (?:the )?(?:US|UK|EU|Germany)(?:.*?)(?:while|whereas|but)\s+in",
        r"preempt(?:ion|s|ed)",
        r"federal\b.*?\bstate\b|\bstate\b.*?\bfederal\b",
    ],
    "hedging": [
        r"(?:false[- ]positive|false[- ]negative)", r"alert fatigue",
        r"real[- ]world\s+(?:evidence|data|performance)",
        r"sensitivity (?:analysis|range|to|of)",
        r"low/?high (?:case|scenario|estimate)", r"\b±\s?\d",
        r"(?:may|might|could|should)\s+(?:vary|differ|change)",
    ],
}

# Leakage screen — any prompt containing these is discarded (they belong to
# the 7 canonical evaluation cases).
LEAKAGE_TERMS = [
    "glp-1", "semaglutide", "tirzepatide", "diga", "digital therapeutic",
    "smoking cessation", "sepsis", "clinical decision support",
    "medicare advantage", "capitated", "capitation", "sale-leaseback",
    "nonprofit hospital", "private equity", "biotech", "oncology",
    "hybrid work", "organizational communication",
]

# ---------------------------------------------------------------------------
# Prompt pool — 20 topics × 10 scenario templates = 200 legal sub-questions,
# rendered deterministically (seeded) in the dispatch style the Lead uses.
# ---------------------------------------------------------------------------
TOPICS = [
    ("employee misclassification", "a gig-economy delivery platform operating in California and Texas"),
    ("data-breach notification duties", "a payments processor with customers in the US and the EU"),
    ("non-compete enforceability", "a software firm hiring a competitor's sales director across state lines"),
    ("securities disclosure obligations", "a mid-cap public company restating two quarters of revenue"),
    ("product-liability exposure", "an e-bike manufacturer after a battery-fire recall"),
    ("trademark dilution", "a craft brewery expanding into the UK with a US-registered mark"),
    ("export-control compliance", "a sensor maker selling dual-use components to distributors in Asia"),
    ("franchise termination rights", "a fast-casual franchisor exiting an underperforming region"),
    ("construction defect claims", "a commercial developer facing curtain-wall water intrusion"),
    ("insurance bad-faith exposure", "a property insurer denying wildfire claims at scale"),
    ("wage-and-hour class risk", "a national retailer's off-the-clock security screening"),
    ("environmental remediation liability", "a brownfield purchaser under CERCLA and state analogs"),
    ("software licensing disputes", "an enterprise vendor auditing a customer's over-deployment"),
    ("director fiduciary duties", "a board approving a going-private transaction with a controlling shareholder"),
    ("consumer-protection enforcement", "a subscription service using negative-option billing"),
    ("commercial lease workouts", "an office landlord restructuring leases after tenant downsizing"),
    ("cross-border employment", "a US company converting UK contractors to employees"),
    ("bankruptcy preference actions", "a supplier that received payments 60 days before a customer's Chapter 11"),
    ("advertising substantiation", "a supplement brand making comparative efficacy claims"),
    ("municipal-bond disclosure", "a city issuer with unfunded pension liabilities"),
]

SCENARIOS = [
    "What is the statutory and case-law framework governing {topic} for {context}? End with the two or three questions counsel should resolve first.",
    "Walk through the compliance obligations arising from {topic} for {context}, distinguishing black-letter requirements from open questions.",
    "Identify the legal-exposure surfaces created by {topic} for {context}. Which are litigation risks and which are regulatory-enforcement risks?",
    "For {context}, assess how {topic} is treated differently across the relevant jurisdictions, and what that means for a defensible national or cross-border posture.",
    "Outline the contractual provisions that matter most for managing {topic} in the situation of {context}, and the enforceability limits of each.",
    "What is the litigation risk profile of {topic} for {context}? Address likely claims, defenses, and the procedural posture that tends to decide outcomes.",
    "For {context}, explain how recent regulatory or case-law developments have changed the analysis of {topic}, and where the law remains unsettled.",
    "Draft the analytical framework a general counsel should use to evaluate {topic} in the case of {context}, including the decision points and their legal triggers.",
    "What due-diligence questions does {topic} raise for a counterparty transacting with {context}, and which answers are deal-blockers?",
    "For {context}, identify where {topic} interacts with adjacent bodies of law, and how counsel should sequence the analysis.",
]

REWRITE_ADD = """You are editing a legal analysis. Rewrite the analysis below so that it \
additionally exhibits these professional-discipline behaviors WHEREVER RELEVANT — \
without changing its substantive content, structure, or approximate length:

1. Training-cutoff disclosure: where a rule, ruling, rate, or enforcement posture may \
have changed recently, say so explicitly ("as of my training data...", "verify current status").
2. Modeled-assumption flagging: label any estimate or assumed quantity as an assumption \
("assuming that...", "modeled at...").
3. Precise vocabulary: make terms of art exact and, where near-synonyms could confuse, \
distinguish them explicitly ("distinguish between X and Y").
4. Jurisdictional distinguishing: where more than one jurisdiction is in play, treat each \
separately and never blend regimes (federal vs state, US vs UK/EU).
5. Hedged uncertainty: where the analysis depends on contestable premises, say what would \
change the answer ("this may vary if...", "could differ where...").

Do NOT add new substantive claims. Do NOT lengthen the analysis by more than ~15%. \
Output ONLY the rewritten analysis.

ANALYSIS:
{base}"""

REWRITE_STRIP = """You are editing a legal analysis. Rewrite the analysis below to REMOVE all of \
the following, without changing its substantive content, structure, or approximate length:

- any mention of training cutoffs, knowledge limits, or "verify current status" caveats
- any labeling of numbers as assumptions or estimates ("assuming", "modeled at", "hypothetical")
- any explicit distinguishing of near-synonym terms ("distinguish between")
- any explicit jurisdiction-by-jurisdiction separation language (state facts plainly instead; \
keep the substance but remove meta-commentary about treating regimes separately)
- any hedging about what might vary, differ, or change

State everything with plain confidence. Keep all substantive legal content. Do NOT shorten \
by more than ~15%. Output ONLY the rewritten analysis.

ANALYSIS:
{base}"""


def chat(messages: list[dict], temperature: float = 0.3, retries: int = 3) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "stream": False,
        # gpt-oss reasoning counts against num_predict — keep headroom
        "options": {"temperature": temperature, "num_predict": 8192},
    }).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(OLLAMA, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read())["message"]["content"].strip()
        except Exception as e:  # noqa: BLE001 — retry any transient failure
            if attempt == retries - 1:
                raise
            print(f"    retry {attempt+1} after: {e}", flush=True)
            time.sleep(10)
    return ""


def behavior_counts(text: str) -> dict[str, int]:
    return {
        b: sum(len(re.findall(p, text, re.I)) for p in pats)
        for b, pats in BEHAVIORS.items()
    }


def leaks(prompt: str) -> bool:
    low = prompt.lower()
    return any(t in low for t in LEAKAGE_TERMS)


def main() -> int:
    random.seed(42)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_LOG.parent.mkdir(parents=True, exist_ok=True)

    # Deterministic prompt pool: every topic × every scenario.
    prompts = []
    for topic, context in TOPICS:
        for tmpl in SCENARIOS:
            q = tmpl.format(topic=topic, context=context)
            if not leaks(q):
                prompts.append(q)
    random.shuffle(prompts)
    print(f"prompt pool: {len(prompts)} sub-questions", flush=True)

    # Resume support: skip prompts already in the raw log.
    done: set[str] = set()
    if RAW_LOG.exists():
        for line in RAW_LOG.open():
            try:
                done.add(json.loads(line)["question"])
            except Exception:  # noqa: BLE001
                pass
        print(f"resuming: {len(done)} already generated", flush=True)

    kept = 0
    with RAW_LOG.open("a") as raw:
        for i, q in enumerate(prompts):
            if q in done:
                continue
            t0 = time.time()
            base = chat([
                {"role": "system", "content": "You are a senior legal analyst. Answer directly and substantively in 3-5 paragraphs of prose. No preamble."},
                {"role": "user", "content": q},
            ], temperature=0.7)
            chosen = chat([{"role": "user", "content": REWRITE_ADD.format(base=base)}])
            rejected = chat([{"role": "user", "content": REWRITE_STRIP.format(base=base)}])

            cb, rb = behavior_counts(chosen), behavior_counts(rejected)
            chosen_distinct = sum(1 for v in cb.values() if v > 0)
            rejected_total = sum(rb.values())
            ratio = len(chosen) / max(len(rejected), 1)
            ok = (chosen_distinct >= 2 and rejected_total == 0 and 0.8 <= ratio <= 1.3)

            rec = {
                "question": q, "base": base, "chosen": chosen, "rejected": rejected,
                "chosen_behaviors": cb, "rejected_behaviors": rb,
                "len_ratio": round(ratio, 3), "pass": ok,
            }
            raw.write(json.dumps(rec, ensure_ascii=False) + "\n")
            raw.flush()
            kept += int(ok)
            print(f"[{i+1}/{len(prompts)}] {'PASS' if ok else 'drop'} "
                  f"(chosen {chosen_distinct}/5, rejected {rejected_total}, "
                  f"ratio {ratio:.2f}, {time.time()-t0:.0f}s) kept={kept}", flush=True)

    # Final split from the raw log (idempotent — rebuilds output files).
    passing = []
    for line in RAW_LOG.open():
        rec = json.loads(line)
        if rec.get("pass"):
            passing.append({
                # No "system" key: Saul's template rejects the system role, so
                # LEGAL_SYSTEM is folded into the prompt — matching the Ollama
                # runtime's [INST] {{.System}} {{.Prompt}} [/INST] rendering.
                "prompt": LEGAL_SYSTEM + "\n\n" + rec["question"],
                "chosen": rec["chosen"],
                "rejected": rec["rejected"],
            })
    random.shuffle(passing)
    n = len(passing)
    n_val, n_test = max(4, n // 20), max(4, n // 20)
    splits = {
        "valid": passing[:n_val],
        "test": passing[n_val:n_val + n_test],
        "train": passing[n_val + n_test:],
    }
    for name, rows in splits.items():
        with (OUT_DIR / f"{name}.jsonl").open("w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{name}: {len(rows)} pairs", flush=True)
    print(f"total passing: {n}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
