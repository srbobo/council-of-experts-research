# Council of Experts (Local PoC)

A multi-agent council with three domain fine-tunes plus a reasoning Lead, running entirely locally on Apple Silicon, with an optional A/B benchmark against Claude Opus 4.7.

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the full plan, decisions, and phase tracking.

## Cabinet

| Role        | Model                                | Backbone         | Quant   |
| ----------- | ------------------------------------ | ---------------- | ------- |
| Lead        | phi4:14b                             | Microsoft Phi-4  | Q4_K_M  |
| Healthcare  | Med42-v2 8B                          | Llama 3.1 8B     | Q4_K_M  |
| Legal       | SaulLM-7B-Instruct-v1                | Mistral 7B       | Q4_K_M  |
| Finance     | Qwen-Open-Finance-R 8B               | Qwen3-8B         | Q8_0    |

## Quickstart

```bash
# install (base deps only)
uv sync

# verify all 4 models are present in Ollama
uv run python -m council list-models

# run a single case end-to-end via the CLI (~5 min wall-clock)
uv run python -m council deliberate --case case_1_clinical_decision_support

# bench harness — compare local council vs Opus 4.7
# (refuses cleanly while BENCH_BUDGET_USD=0; raise to enable Opus)
uv sync --extra bench
uv run python -m bench compare --case case_1_clinical_decision_support

# web UI — same A/B comparison in the browser
uv sync --extra bench --extra server
uv run python -m server
# then open http://127.0.0.1:8000
```

## Status

This is a personal proof-of-concept following the v5 spec in `Council_of_Experts_v5_FineTunedCabinet.docx`. Not production-grade, not a product.
