"""Cell 11 stage 1 — generate the construction-labeled training prompt corpus.

Targets 76 trigger-heavy + 32 trigger-light cross-domain analyst prompts
(~70/30 per the pre-registration). "Construction-labeled" means the label
comes from how the prompt is generated, not from post-hoc scoring:

  heavy: turns on post-2024 developments, uncertain/unstated quantities,
         or multi-jurisdiction regulatory conflict — disposition warranted.
  light: settled definitions, stable mechanics, single well-established
         regime — disposition NOT warranted.

All seven bench cases are held out by topic (the generator is shown their
themes and told to avoid them).

Idempotent: counts existing prompts per label and generates the shortfall.
Run: .venv/bin/python train/gen_cell11_prompts.py
"""
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from council.cabinet import GPT_OSS_20B  # noqa: E402
from council.models import chat as local_chat  # noqa: E402

OUT = Path("train/data/cell11_prompts.jsonl")
TARGETS = {"heavy": 76, "light": 32}
BATCH = 6

BENCH_TOPICS = (
    "clinical decision support alerting; cross-border digital therapeutic "
    "launch (US/EU/UK); capitated risk contracts for provider groups; GLP-1 "
    "employer coverage decisions; nonprofit hospital private-equity "
    "conversion; biotech M&A with a pivotal trial pending; hospital cafeteria "
    "vendor selection"
)

GEN_SYSTEM = (
    "You generate benchmark questions for evaluating multi-domain analyst "
    "assistants. Each question must genuinely span at least two of: "
    "healthcare, law/regulation, finance. Output STRICT JSON: an array of "
    "strings, nothing else."
)

HEAVY_USER = f"""Write {BATCH} distinct analyst questions (3-6 sentences each, concrete
scenario framing) whose correct answers UNAVOIDABLY depend on at least two of:
(a) regulatory guidance, reimbursement rates, or case law that may have
changed after 2024; (b) quantities the question deliberately leaves unstated
so any analysis must assume or model them; (c) obligations that differ across
at least two named jurisdictions or regimes.

Do NOT reuse these reserved themes: {BENCH_TOPICS}.
Return a JSON array of {BATCH} strings."""

LIGHT_USER = f"""Write {BATCH} distinct analyst questions (3-6 sentences each, concrete
scenario framing) that span healthcare/legal/finance domains but are fully
answerable from SETTLED, STABLE knowledge: established definitions, long-fixed
mechanics, single well-established regimes. A careful answer needs NO
training-cutoff caveats, NO assumed quantities, NO jurisdiction-splitting —
the facts involved have been stable for a decade or more and every needed
number is stated in the question itself.

Do NOT reuse these reserved themes: {BENCH_TOPICS}.
Return a JSON array of {BATCH} strings."""


def parse_array(raw: str) -> list[str]:
    """Extract a JSON string-array, tolerating fences and leading prose."""
    for candidate in (raw.strip(),):
        try:
            v = json.loads(candidate)
            if isinstance(v, list):
                return [s for s in v if isinstance(s, str)]
        except json.JSONDecodeError:
            pass
    m = re.search(r"\[[\s\S]*\]", raw)
    if m:
        try:
            v = json.loads(m.group(0))
            if isinstance(v, list):
                return [s for s in v if isinstance(s, str)]
        except json.JSONDecodeError:
            pass
    return []


def norm(p: str) -> str:
    return re.sub(r"\W+", " ", p.lower()).strip()[:160]


async def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(x) for x in OUT.read_text().splitlines()] if OUT.exists() else []
    seen = {norm(r["prompt"]) for r in rows}
    for label, user in (("heavy", HEAVY_USER), ("light", LIGHT_USER)):
        stall = 0
        while sum(1 for r in rows if r["label"] == label) < TARGETS[label] and stall < 12:
            r = await local_chat(GPT_OSS_20B, [
                {"role": "system", "content": GEN_SYSTEM},
                {"role": "user", "content": user},
            ], max_tokens=4096, temperature=0.9)
            fresh = [p for p in parse_array(r.content)
                     if len(p) > 120 and norm(p) not in seen]
            if not fresh:
                stall += 1
                continue
            stall = 0
            for p in fresh:
                if sum(1 for x in rows if x["label"] == label) >= TARGETS[label]:
                    break
                seen.add(norm(p))
                row = {"id": f"c11-{label}-{sum(1 for x in rows if x['label'] == label):03d}",
                       "label": label, "prompt": p}
                rows.append(row)
                with OUT.open("a") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"{label}: {sum(1 for x in rows if x['label'] == label)}"
                  f"/{TARGETS[label]}", flush=True)
    h = sum(1 for x in rows if x["label"] == "heavy")
    li = sum(1 for x in rows if x["label"] == "light")
    print(f"=== CELL11 PROMPTS DONE: {h} heavy / {li} light ===", flush=True)


asyncio.run(main())
