# Ollama model inventory (2026-09-13)

Snapshot of `ollama list` at the time of the model audit, with each model's
role in the ledger and how it can be recovered if deleted. The ID column is
the Ollama digest prefix; a re-pulled tag should be checked against it, since
library tags and HF quantizations can be re-pushed with different bytes.

Sizes are as reported by `ollama list`. Disk at audit time: 159 GB in
`~/.ollama/models`, data volume at 100% with 3.9 GiB free.

## Irreplaceable (custom fine-tunes with no adapter on disk)

| Model | ID | Size | Role | Recovery |
|---|---|---|---|---|
| med42-repro:coe | 4b01b57acbcd | 4.9 GB | backs the live per-model-signature claim (`reg-` runs, 2026-07-30) | none; keep |
| saul-repro:coe | 7c99a2132b63 | 4.4 GB | superseded lead-tune era (cells 6/11/18, local) | none; retrain |
| qwen-finance-repro:coe | 7a9a002a1f49 | 5.0 GB | superseded lead-tune era | none; retrain |
| qwen-lead-repro:coe | 7c4fb321f2ea | 4.7 GB | superseded lead-tune era (cells 6b/11/18) | none; retrain |

## Rebuildable from `train/adapters` (superseded lead-tune era)

| Model | ID | Size | Adapter | Rebuild |
|---|---|---|---|---|
| qwen-lead-prov:coe | d0ba8e3b66dc | 4.7 GB | 3.9 GB merge; GGUF also in train/gguf | `ollama create` from train/qwen-lead-prov.Modelfile |
| qwen-lead-cal:coe | 63bcadd1c060 | 4.7 GB | 3.8 GB merge | quantize + `ollama create` |
| qwen-lead-orpo:coe | ca53b2b61ae6 | 4.7 GB | 3.8 GB merge | quantize + `ollama create` |
| saul-sft:coe | 6ed0c3b577da | 4.4 GB | 44 MB LoRA | export-lora + quantize |
| saul-dpo:coe | e68ed019adb0 | 4.4 GB | 44 MB LoRA | export-lora + quantize |
| saul-dpo-v2:coe | 5a9b1178175a | 4.4 GB | 44 MB LoRA | export-lora + quantize |
| saul-cpo:coe | 0b7fbd0e5ac3 | 4.4 GB | 44 MB LoRA | export-lora + quantize |
| med42-orpo:coe | c48ba0b2c7bf | 4.9 GB | 57 MB LoRA | export-lora + quantize |
| qwen-finance-orpo:coe | d70448a0736e | 5.0 GB | 52 MB LoRA | export-lora + quantize |

## Re-downloadable public models, currently unreferenced

| Model | ID | Size | Recovery |
|---|---|---|---|
| qwen3-vl:8b-instruct | 0533d74300e4 | 6.1 GB | `ollama pull` |
| qwen3-vl:8b | 901cae732162 | 6.1 GB | `ollama pull` |
| huggingface.co/bartowski/Llama-3.1-Hawkish-8B-GGUF:Q4_K_M | 1a62f0742403 | 4.9 GB | `ollama pull` |

## Re-downloadable public models backing live claims

| Model | ID | Size | Role | Needed by |
|---|---|---|---|---|
| gpt-oss:20b | 17052f91a42e | 13 GB | writer, primary judge | every council cell |
| phi4:14b | ac896e5b8b34 | 9.1 GB | second writer (transport), judge family, gate candidate | C30/C46 replication, C43, C55 |
| qwen3-vl:30b-a3b-instruct | c871fc73fabc | 19 GB | replication judge (fourth judge family) | C43-R and any judge replication |
| qwen2.5:7b-instruct | 845dbda0ea48 | 4.7 GB | judge family, signature base, gate candidate | C43, signature probe, C55 |
| huggingface.co/mradermacher/Llama3-Med42-8B-GGUF:Q4_K_M | fd9af25fd11f | 4.9 GB | healthcare seat | C13 through C61 |
| huggingface.co/MaziyarPanahi/Saul-Instruct-v1-GGUF:Q4_K_M | b7aa80544c1d | 4.4 GB | legal seat, gate candidate | C13 through C61, C55 |
| qwen-finance-r:coe | 3c30df8f8ff9 | 8.7 GB | finance seat | C13 through C61; rebuild from train/qwen-finance.Modelfile (FROM huggingface.co/pate2464/Qwen-Open-Finance-R-8B-FP8-Q8_0-GGUF) or train/models/Qwen-Open-Finance-R-8B |
| llama3:8b-instruct-q4_K_M | 9b8f3f3385bf | 4.9 GB | gate candidate (pass) | C55 re-gate |
| mistral:7b-instruct-v0.3-q4_K_M | 6577803aa9a0 | 4.4 GB | gate candidate; BioMistral's own base | C55, signature probe |
| deepseek-r1:7b | 755ced02ce7b | 4.7 GB | gate candidate (pass) | C55 re-gate |
| huggingface.co/mradermacher/Meditron3-Qwen2.5-7B-GGUF:Q4_K_M | 56fe1afd89dc | 4.7 GB | gate candidate; signature tune (Qwen lineage) | C55, signature probe |
| hf.co/mradermacher/OpenBioLLM-Llama3-8B-GGUF:Q4_K_M | a8e3e18aa5a1 | 4.9 GB | gate candidate (fail; "verdicts age") | C55 re-gate |
| hf.co/MaziyarPanahi/BioMistral-7B-GGUF:Q4_K_M | 61e57dc40f0c | 4.4 GB | gate candidate (fail; 12/12 degenerate); signature tune | C55, signature probe |
