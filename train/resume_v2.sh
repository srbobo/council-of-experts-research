#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv-train/bin/python
MODEL=train/mlx/saul-bf16; DATA=train/data/dpo_pairs
ADAPTERS=train/adapters/saul-dpo-v2; FUSED=train/models/Saul-7B-DPO-v2-fused
(ollama ps 2>/dev/null | awk 'NR>1 && $1!=""{print $1}' || true) | while read -r m; do ollama stop "$m" 2>/dev/null || true; done
latest=$(ls "$ADAPTERS"/0*_adapters.safetensors | sort | tail -1)
done_iters=$(basename "$latest" | sed 's/^0*//;s/_adapters.safetensors//')
remain=$(( 1056 - done_iters ))
echo "=== resuming from iter $done_iters, $remain remaining ==="
$PY -m mlx_lm_lora.train --model "$MODEL" --train --train-mode orpo --load-in-4bits \
  --train-type lora --data "$DATA" --beta 0.1 --batch-size 1 --gradient-accumulation-steps 4 \
  --learning-rate 5e-6 --iters "$remain" --num-layers 16 --adapter-path "$ADAPTERS" \
  --resume-adapter-file "$latest" --steps-per-report 20 --save-every 100 \
  --max-seq-length 1792 --grad-checkpoint --seed 42
echo "=== fuse -> GGUF -> ollama ==="
$PY -m mlx_lm fuse --model "$MODEL" --adapter-path "$ADAPTERS" --save-path "$FUSED"
mkdir -p train/gguf
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" --outfile train/gguf/saul-dpo-v2-f16.gguf --outtype f16
llama-quantize train/gguf/saul-dpo-v2-f16.gguf train/gguf/saul-dpo-v2-Q4_K_M.gguf Q4_K_M
cat > train/saul-dpo-v2.Modelfile << 'MF'
FROM ./gguf/saul-dpo-v2-Q4_K_M.gguf
TEMPLATE [INST] {{ if .System }}{{ .System }} {{ end }}{{ .Prompt }} [/INST]
PARAMETER stop [INST]
PARAMETER stop [/INST]
MF
cd train && ollama create saul-dpo-v2:coe -f saul-dpo-v2.Modelfile
echo "=== DONE — saul-dpo-v2:coe ready ==="
