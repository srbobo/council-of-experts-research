"""Cell 11 stage 2 — on-policy sampling at the pipeline's mouth.

For each training prompt: run the full council ONCE with the conversion-
control Lead (qwen-lead-repro:coe playing planner + synthesis, production
seats unchanged), capture the exact synthesis input_messages off the audit
trail, then sample n=6 syntheses at temperature 0.8 from those messages.
In this pipeline the synthesis IS the final output, so the 6 samples are
on-policy samples of the pipeline's mouth — the locus the calibration
reward is registered to score.

Prompts whose plan routes to zero seats take the direct-answer path, which
is not the synthesis distribution; they are recorded as skipped.

Idempotent: one JSON per prompt id under train/data/cell11_samples/.
Run: .venv/bin/python train/run_cell11_sample.py
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from council.cabinet import CABINET, CabinetMember  # noqa: E402
from council.models import chat as local_chat  # noqa: E402
from council.orchestrator import PHASE_IDS, CabinetBackends, deliberate  # noqa: E402
from council.thermal import ThermalGuard  # noqa: E402

N_SAMPLES = 6
SAMPLE_TEMP = 0.8
PROMPTS = Path("train/data/cell11_prompts.jsonl")
OUT = Path("train/data/cell11_samples")

# Conversion-control Lead: stock Qwen2.5-7B through the SAME HF->GGUF->Q4
# pipeline the trained model will use, so sampling is on-policy w.r.t. the
# base being trained (modulo quantization, identical on both sides).
LEAD_REPRO = CabinetMember(
    seat="lead", name="Qwen2.5-7B Lead (A' conversion control)",
    backbone="Qwen2.5 7B", fine_tune_type="conversion control",
    ollama_tag="qwen-lead-repro:coe", quantization="Q4_K_M",
    memory_gb=4.7, license="Apache 2.0")


def lead_cabinet() -> CabinetBackends:
    async def lead_chat(_m, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(LEAD_REPRO, messages, max_tokens=8192, **kw)
    fns = {p: local_chat for p in PHASE_IDS}
    tags = {p: "ollama" for p in PHASE_IDS}
    fns["planner"] = lead_chat
    fns["synthesis"] = lead_chat
    tags["planner"] = tags["synthesis"] = f"ollama:{LEAD_REPRO.ollama_tag}"
    return CabinetBackends(**fns, name="cell11-sampler", backend_tags=tags)


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    thermal = ThermalGuard.from_env()
    rows = [json.loads(x) for x in PROMPTS.read_text().splitlines()]
    for i, row in enumerate(rows):
        path = OUT / f"{row['id']}.json"
        if path.exists():
            continue
        print(f"=== {row['id']} [{i + 1}/{len(rows)}] "
              f"({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
        try:
            d = await deliberate(row["prompt"], thermal=thermal,
                                 cabinet=lead_cabinet(), cabinet_members=CABINET)
        except Exception as e:  # noqa: BLE001
            print("  FAILED (deliberate):", e, flush=True)
            continue
        if not d.plan.get("routes"):
            path.write_text(json.dumps({**row, "skipped": "no_routes"}))
            print("  skipped: planner routed to zero seats", flush=True)
            continue
        messages = d.synthesis.input_messages
        samples: list[str] = []
        ok = True
        for _ in range(N_SAMPLES):
            try:
                r = await local_chat(LEAD_REPRO, messages, max_tokens=8192,
                                     temperature=SAMPLE_TEMP)
                samples.append(r.content)
            except Exception as e:  # noqa: BLE001
                print("  FAILED (sample):", e, flush=True)
                ok = False
                break
        if not ok or len(samples) < N_SAMPLES:
            continue  # partial file not written; re-run resumes this prompt
        path.write_text(json.dumps({
            **row, "synthesis_messages": messages, "samples": samples,
        }, ensure_ascii=False))
    done = len(list(OUT.glob("*.json")))
    print(f"=== CELL11 SAMPLING COMPLETE: {done}/{len(rows)} prompts ===", flush=True)


asyncio.run(main())
