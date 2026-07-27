"""Cell 8 — architecture comparison. gpt-oss-20B in EVERY role, so the only
variable is the orchestration shape.

Arms (pre-registered in RUNBOOK_PAPER_HARDENING.md):
  arch-single       single-shot, neutral prompt
  arch-single-spec  single-shot + behavior-spec prompt (unconditional
                    disposition instruction, no multi-agent structure)
  arch-council      full council: planner -> 3 seats -> Tensions-then-Synthesis
                    with CONDITIONAL PRESERVE instructions
  arch-flat         same 3 seats, naive merge, NO tension extraction, NO
                    PRESERVE (multi-agent WITHOUT the conditional instruction)
  arch-debate       2 rounds (seats see each other's answers, revise), then the
                    same naive merge as arch-flat
  arch-refine       single model: draft -> self-critique -> revise

7 cases x 5 seeds x 6 arms. Idempotent: counts existing files per (case, mode)
and runs only the shortfall.

Run: .venv/bin/python train/run_cell8_arch.py
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from council.cabinet import CABINET, GPT_OSS_20B  # noqa: E402
from council.models import chat as local_chat  # noqa: E402
from council.orchestrator import PHASE_IDS, CabinetBackends, deliberate  # noqa: E402
from council.prompts import (  # noqa: E402
    FINANCE_SYSTEM, HEALTHCARE_SYSTEM, LEGAL_SYSTEM,
)
from council.thermal import ThermalGuard  # noqa: E402
from examples.test_cases import get_case  # noqa: E402

CASES = ['case_1_clinical_decision_support', 'case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract', 'case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion', 'case_6_trigger_heavy_biotech_ma',
         'case_7_trigger_light_baseline']
SEEDS = 5
OUT = Path('bench/runs/imported')

NEUTRAL = ("You are a senior cross-domain analyst. Answer the question directly "
           "and substantively.")

# Unconditional disposition instruction (arm 2) — deliberately NOT conditioned
# on any upstream signal, which is the contrast against the council's
# "IF a specialist flagged X, propagate X".
SPEC = NEUTRAL + """

ADDITIONAL DISCIPLINE REQUIREMENTS — apply wherever relevant:
1. Disclose training-cutoff uncertainty explicitly ("as of my training data...").
2. Label every estimate or assumed quantity as an assumption ("modeled at", "assuming").
3. Distinguish near-synonym terms of art explicitly.
4. Treat each jurisdiction or regulatory regime separately; never blend them.
5. State what would change your conclusion ("this may vary if...").
Do not force these where they are not warranted."""

# Naive merge (arms 4/5): multi-agent input, but no tension extraction and no
# conditional preservation instruction.
FLAT_MERGE = ("You are the lead analyst. Below are contributions from three "
              "specialists. Write one integrated final answer to the user's "
              "question. Use whatever structure best fits the question.")

SEAT_PROMPTS = [("healthcare", HEALTHCARE_SYSTEM), ("legal", LEGAL_SYSTEM),
                ("finance", FINANCE_SYSTEM)]


async def gptoss(messages, temperature=0.2) -> str:
    """Call gpt-oss and return its text. council.models.chat returns a
    ChatResponse whose payload lives on `.content` (verified empirically);
    reading the wrong attribute would silently persist an object repr."""
    r = await local_chat(GPT_OSS_20B, messages, max_tokens=8192,
                         temperature=temperature)
    return r.content


def uniform_cabinet():
    """Every phase routed to gpt-oss (the arch-council arm)."""
    async def chat_fn(_member, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(GPT_OSS_20B, messages, max_tokens=8192, **kw)
    fns = {p: chat_fn for p in PHASE_IDS}
    tags = {p: f"ollama:{GPT_OSS_20B.ollama_tag}" for p in PHASE_IDS}
    return CabinetBackends(**fns, name="arch-gptoss-uniform", backend_tags=tags)


async def seat_answers(question: str, peer_context: str | None = None):
    """Three specialist answers to the same question (optionally seeing peers)."""
    out = []
    for seat, sys_prompt in SEAT_PROMPTS:
        user = question
        if peer_context:
            user = (f"{question}\n\nOther specialists' initial answers:\n"
                    f"{peer_context}\n\nRevise your own answer in light of these.")
        r = await gptoss([{"role": "system", "content": sys_prompt},
                          {"role": "user", "content": user}])
        out.append((seat, r))
    return out


def merge_block(answers):
    return "\n\n".join(f"--- {seat.upper()} SPECIALIST ---\n{txt}" for seat, txt in answers)


async def run_arm(mode: str, case: str, thermal):
    q = get_case(case).prompt
    if mode == "arch-single":
        r = await gptoss([{"role": "system", "content": NEUTRAL},
                          {"role": "user", "content": q}])
        return (r), None
    if mode == "arch-single-spec":
        r = await gptoss([{"role": "system", "content": SPEC},
                          {"role": "user", "content": q}])
        return (r), None
    if mode == "arch-council":
        d = await deliberate(q, thermal=thermal, cabinet=uniform_cabinet(),
                             cabinet_members=CABINET)
        return d.final_output, d.to_dict()
    if mode in ("arch-flat", "arch-debate"):
        answers = await seat_answers(q)
        if mode == "arch-debate":
            answers = await seat_answers(q, peer_context=merge_block(answers))
        r = await gptoss([{"role": "system", "content": FLAT_MERGE},
                          {"role": "user", "content":
                           f"USER QUESTION:\n{q}\n\n{merge_block(answers)}"}])
        txt = r
        return txt, {"turns": [{"seat": s, "output_text": t} for s, t in answers]}
    if mode == "arch-refine":
        d0 = await gptoss([{"role": "system", "content": NEUTRAL},
                           {"role": "user", "content": q}])
        draft = d0
        c = await gptoss([{"role": "system", "content": NEUTRAL},
                          {"role": "user", "content":
                           f"Critique this answer for errors, overstatement, and "
                           f"unsupported claims.\n\nQUESTION:\n{q}\n\nANSWER:\n{draft}"}])
        crit = c
        rv = await gptoss([{"role": "system", "content": NEUTRAL},
                           {"role": "user", "content":
                            f"QUESTION:\n{q}\n\nDRAFT:\n{draft}\n\nCRITIQUE:\n{crit}\n\n"
                            f"Write the improved final answer."}])
        return (rv), {"turns": []}
    raise ValueError(mode)


async def main():
    thermal = ThermalGuard.from_env()
    arms = ["arch-single", "arch-single-spec", "arch-council",
            "arch-flat", "arch-debate", "arch-refine"]
    for mode in arms:
        for case in CASES:
            have = len(list(OUT.glob(f"*__{case}__{mode}.json")))
            for i in range(max(0, SEEDS - have)):
                print(f"=== {mode} / {case} [{have+i+1}/{SEEDS}] "
                      f"({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
                try:
                    final, delib = await run_arm(mode, case, thermal)
                except Exception as e:  # noqa: BLE001
                    print("  FAILED:", e, flush=True)
                    continue
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                (OUT / f"{stamp}__{case}__{mode}.json").write_text(json.dumps({
                    "schema_version": 2, "imported": True, "source": "cell8",
                    "captured_at": stamp, "case_id": case, "case_title": case,
                    "mode": mode, "model": GPT_OSS_20B.ollama_tag,
                    "final_output": final, "notes": "",
                    "deliberation": delib or {}}, ensure_ascii=False))
    total = len(list(OUT.glob("*__arch-*.json")))
    print(f"=== CELL 8 COMPLETE: {total}/210 ===", flush=True)


asyncio.run(main())
