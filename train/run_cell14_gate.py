"""Cell 14 — the first valid test of instruction-level gating.

Every previous trigger-free measurement on a council arm used case_7, which is
off-topic for the cabinet: the planner routes to nobody and the orchestrator
silently falls back to LEAD_DIRECT_ANSWER_SYSTEM, discarding the synthesis
prompt entirely. Those runs therefore never exercised the PRESERVE clauses and
cannot speak to whether a conditional instruction suppresses unwarranted
qualification.

This cell uses three NEW trigger-free questions that are squarely ON-TOPIC for
a cabinet seat, so routing occurs and the synthesis prompt actually runs, while
still warranting no qualification (all quantities stated, settled subject
matter, one regime, nothing to model). Verified pre-run: each routes to one
seat with PRESERVE applied.

Arms match run_cell8_arch.py exactly so the trigger-case numbers remain
comparable; the new case_ids keep these runs separable from the contaminated
case_7 ones.

3 cases x 5 seeds x 4 arms = 60 runs. Idempotent.

PATH AUDIT: every record persists which synthesis prompt actually ran, so a
future analysis can verify the execution path from the ledger instead of
reconstructing it from orchestrator source. This is the fix for the flaw class
that produced the withdrawn P8.2 and P13.3 verdicts.

Run: .venv/bin/python train/run_cell14_gate.py
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

CASES = ['case_8_trigger_light_hand_hygiene',
         'case_9_trigger_light_nda_clauses',
         'case_10_trigger_light_depreciation']
SEEDS = 5
OUT = Path('bench/runs/imported')

NEUTRAL = ("You are a senior cross-domain analyst. Answer the question directly "
           "and substantively.")

SPEC = NEUTRAL + """

ADDITIONAL DISCIPLINE REQUIREMENTS — apply wherever relevant:
1. Disclose training-cutoff uncertainty explicitly ("as of my training data...").
2. Label every estimate or assumed quantity as an assumption ("modeled at", "assuming").
3. Distinguish near-synonym terms of art explicitly.
4. Treat each jurisdiction or regulatory regime separately; never blend them.
5. State what would change your conclusion ("this may vary if...").
Do not force these where they are not warranted."""

FLAT_MERGE = ("You are the lead analyst. Below are contributions from three "
              "specialists. Write one integrated final answer to the user's "
              "question. Use whatever structure best fits the question.")

SEAT_PROMPTS = [("healthcare", HEALTHCARE_SYSTEM), ("legal", LEGAL_SYSTEM),
                ("finance", FINANCE_SYSTEM)]


async def gptoss(messages, temperature=0.2) -> str:
    r = await local_chat(GPT_OSS_20B, messages, max_tokens=8192,
                         temperature=temperature)
    return r.content


def uniform_cabinet() -> CabinetBackends:
    async def chat_fn(_member, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(GPT_OSS_20B, messages, max_tokens=8192, **kw)
    fns = {p: chat_fn for p in PHASE_IDS}
    tags = {p: f"ollama:{GPT_OSS_20B.ollama_tag}" for p in PHASE_IDS}
    return CabinetBackends(**fns, name="c14-gptoss-uniform", backend_tags=tags)


async def seat_answers(question: str):
    out = []
    for seat, sys_prompt in SEAT_PROMPTS:
        r = await gptoss([{"role": "system", "content": sys_prompt},
                          {"role": "user", "content": question}])
        out.append((seat, r))
    return out


def merge_block(answers):
    return "\n\n".join(f"--- {s.upper()} SPECIALIST ---\n{t}" for s, t in answers)


def path_of(delib: dict | None) -> dict:
    """Record the execution path so it is auditable from the ledger."""
    if not delib:
        return {"routes": None, "synthesis_prompt": "n/a (single-shot arm)",
                "preserve_applied": False}
    routes = delib.get("plan", {}).get("routes", [])
    syn = delib.get("synthesis") or {}
    msgs = syn.get("input_messages") or []
    sp = msgs[0]["content"] if msgs else ""
    if not sp:
        kind = "unknown"
    elif "PRESERVE" in sp:
        kind = "LEAD_SYNTHESIS_SYSTEM (PRESERVE applied)"
    elif "Council of Experts" in sp:
        kind = "LEAD_DIRECT_ANSWER_SYSTEM (fallback — PRESERVE DISCARDED)"
    else:
        kind = "custom override"
    return {"routes": routes, "n_routes": len(routes),
            "synthesis_prompt": kind, "preserve_applied": "PRESERVE" in sp}


async def run_arm(mode: str, case: str, thermal):
    q = get_case(case).prompt
    if mode == "arch-single":
        return (await gptoss([{"role": "system", "content": NEUTRAL},
                              {"role": "user", "content": q}])), None
    if mode == "arch-single-spec":
        return (await gptoss([{"role": "system", "content": SPEC},
                              {"role": "user", "content": q}])), None
    if mode == "arch-council":
        d = await deliberate(q, thermal=thermal, cabinet=uniform_cabinet(),
                             cabinet_members=CABINET)
        return d.final_output, d.to_dict()
    if mode == "arch-flat":
        answers = await seat_answers(q)
        r = await gptoss([{"role": "system", "content": FLAT_MERGE},
                          {"role": "user", "content":
                           f"USER QUESTION:\n{q}\n\n{merge_block(answers)}"}])
        return r, {"turns": [{"seat": s, "output_text": t} for s, t in answers]}
    raise ValueError(mode)


async def main() -> None:
    thermal = ThermalGuard.from_env()
    arms = ["arch-council", "arch-single-spec", "arch-flat", "arch-single"]
    for mode in arms:
        for case in CASES:
            have = len(list(OUT.glob(f"*__{case}__{mode}.json")))
            for i in range(max(0, SEEDS - have)):
                print(f"=== {mode} / {case} [{have + i + 1}/{SEEDS}] "
                      f"({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
                try:
                    final, delib = await run_arm(mode, case, thermal)
                except Exception as e:  # noqa: BLE001
                    print("  FAILED:", e, flush=True)
                    continue
                path = path_of(delib)
                if mode == "arch-council":
                    print(f"    path: routes={path.get('routes')} "
                          f"preserve={path['preserve_applied']}", flush=True)
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                (OUT / f"{stamp}__{case}__{mode}.json").write_text(json.dumps({
                    "schema_version": 2, "imported": True, "source": "cell14",
                    "captured_at": stamp, "case_id": case, "case_title": case,
                    "mode": mode, "model": GPT_OSS_20B.ollama_tag,
                    "final_output": final, "notes": "on-topic trigger-free control",
                    "execution_path": path,
                    "deliberation": delib or {}}, ensure_ascii=False))
    total = len(list(OUT.glob("*__case_8_*.json"))) + \
        len(list(OUT.glob("*__case_9_*.json"))) + \
        len(list(OUT.glob("*__case_10_*.json")))
    print(f"=== CELL 14 COMPLETE: {total}/60 ===", flush=True)


asyncio.run(main())
