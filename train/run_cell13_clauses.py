"""Cell 13 — per-clause isolation of the PRESERVE block.

Cell 6c dropped clauses in a FIXED order, so its monotone gain curve confounds
count with identity. Here each clause is tested ALONE against a true no-clause
baseline, with one Lead and everything else held fixed.

Arms (7 cases x 5 seeds x 6 = 210 runs):
  c13-none  no C1-C4          (NB: not byte-identical to cell6c-gain-k0,
                               which retains C1 — see runbook correction)
  c13-c1    C1 only  tension acknowledgment (no PRESERVE keyword)
  c13-c2    C2 only  PRESERVE numeric framing    -> modeled-assumptions
  c13-c3    C3 only  PRESERVE precise vocabulary -> vocabulary-precision
  c13-c4    C4 only  PRESERVE caveats            -> cutoff-disclosure
  c13-all   C1-C4    production prompt

Lead: gpt-oss-20B in every phase (widest Cell 6c dynamic range, 3.3x, so
per-clause differences have the most room to resolve; scoping caveat
registered). Clauses are removed with the Cell 6c regexes; surviving items
keep their original numbers, as in 6c.

Every variant asserts its exact retained-clause set before any run.
Idempotent. Run: .venv/bin/python train/run_cell13_clauses.py
"""
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from council.cabinet import CABINET, GPT_OSS_20B  # noqa: E402
from council.models import chat as local_chat  # noqa: E402
from council.orchestrator import PHASE_IDS, CabinetBackends, deliberate  # noqa: E402
from council.prompts import LEAD_SYNTHESIS_SYSTEM  # noqa: E402
from council.thermal import ThermalGuard  # noqa: E402
from examples.test_cases import get_case  # noqa: E402

CASES = ['case_1_clinical_decision_support', 'case_2_cross_border_digital_therapeutic',
         'case_3_capitated_risk_contract', 'case_4_glp1_employer_coverage',
         'case_5_nonprofit_hospital_pe_conversion', 'case_6_trigger_heavy_biotech_ma',
         'case_7_trigger_light_baseline']
SEEDS = 5
OUT = Path('bench/runs/imported')

CLAUSE = {
    "C1": re.compile(r"1\. Acknowledge the tensions[\s\S]*?bite the answer\.\n"),
    "C2": re.compile(r"2\. PRESERVE numeric framing[\s\S]*?as a fact\.\n"),
    "C3": re.compile(r"3\. PRESERVE precise vocabulary[\s\S]*?accessibility\.\n"),
    "C4": re.compile(r"4\. PRESERVE caveats[\s\S]*?into your synthesis\.\n"),
}
# Marker phrases used to verify what actually survived in a built variant.
MARK = {"C1": "Acknowledge the tensions", "C2": "PRESERVE numeric framing",
        "C3": "PRESERVE precise vocabulary", "C4": "PRESERVE caveats"}


def variant(keep: set[str]) -> str | None:
    """Build the synthesis prompt retaining exactly `keep`. None = production."""
    if keep == {"C1", "C2", "C3", "C4"}:
        return None
    s = LEAD_SYNTHESIS_SYSTEM
    for name, rx in CLAUSE.items():
        if name not in keep:
            s, n = rx.subn("", s)
            assert n == 1, f"{name}: expected 1 deletion, got {n}"
    # Verify the exact surviving set — catches a regex that silently over-deletes.
    survived = {k for k, phrase in MARK.items() if phrase in s}
    assert survived == keep, f"built {survived}, wanted {keep}"
    return s


ARMS = [
    ("c13-none", set()),
    ("c13-c1", {"C1"}),
    ("c13-c2", {"C2"}),
    ("c13-c3", {"C3"}),
    ("c13-c4", {"C4"}),
    ("c13-all", {"C1", "C2", "C3", "C4"}),
]


def uniform_cabinet() -> CabinetBackends:
    async def chat_fn(_member, messages, **kw):
        kw.pop("max_tokens", None)
        return await local_chat(GPT_OSS_20B, messages, max_tokens=8192, **kw)
    fns = {p: chat_fn for p in PHASE_IDS}
    tags = {p: f"ollama:{GPT_OSS_20B.ollama_tag}" for p in PHASE_IDS}
    return CabinetBackends(**fns, name="c13-gptoss-uniform", backend_tags=tags)


async def main() -> None:
    built = {mode: variant(keep) for mode, keep in ARMS}
    for mode, keep in ARMS:
        v = built[mode]
        print(f"{mode:<10} keep={(', '.join(sorted(keep)) or 'none'):<26} "
              f"PRESERVE={('production' if v is None else v.count('PRESERVE'))}", flush=True)
    thermal = ThermalGuard.from_env()
    for mode, _ in ARMS:
        for case in CASES:
            have = len(list(OUT.glob(f"*__{case}__{mode}.json")))
            for i in range(max(0, SEEDS - have)):
                print(f"=== {mode} / {case} [{have + i + 1}/{SEEDS}] "
                      f"({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
                try:
                    r = await deliberate(get_case(case).prompt, thermal=thermal,
                                         cabinet=uniform_cabinet(),
                                         cabinet_members=CABINET,
                                         synthesis_system_override=built[mode])
                except Exception as e:  # noqa: BLE001
                    print("  FAILED:", e, flush=True)
                    continue
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                (OUT / f"{stamp}__{case}__{mode}.json").write_text(json.dumps({
                    "schema_version": 2, "imported": True, "source": "cell13",
                    "captured_at": stamp, "case_id": case, "case_title": case,
                    "mode": mode, "model": GPT_OSS_20B.ollama_tag,
                    "final_output": r.final_output, "notes": f"clauses={sorted(_) or 'none'}",
                    "deliberation": r.to_dict()}, ensure_ascii=False))
    total = len(list(OUT.glob("*__c13-*.json")))
    print(f"=== CELL 13 COMPLETE: {total}/210 ===", flush=True)


asyncio.run(main())
