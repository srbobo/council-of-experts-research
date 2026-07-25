#!/bin/bash
# Cell 3 (finance seat, P2) — build the Qwen-Open-Finance A' conversion control
# (qwen-finance-repro) and the ORPO-trained seat (qwen-finance-orpo). Mirrors
# run_cell3_health.sh but with Qwen3 ChatML (folded system-in-user to match the
# folded training pairs). Hardened after the healthcare run: file-based guards
# (no flaky `ollama list`), self-cleans f16 intermediates to avoid disk-full.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv-train/bin/python
MODEL_HF=train/models/Qwen-Open-Finance-R-8B
MODEL=train/mlx/qwen-finance-bf16
DATA=train/data/dpo_pairs_finance
ADAPTERS=train/adapters/qwen-finance-orpo
FUSED=train/models/Qwen-Finance-ORPO-fused

read -r -d '' TEMPLATE << 'TPL' || true
{{ if .System }}<|im_start|>user
{{ .System }}

{{ .Prompt }}<|im_end|>
{{ else }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
TPL

echo "=== unloading ollama models ==="
(ollama ps 2>/dev/null | awk 'NR>1 && $1 != "" {print $1}' || true) | while read -r m; do
  ollama stop "$m" 2>/dev/null || true
done
mkdir -p train/gguf train/adapters

# ---- bf16 (shared by A' and ORPO) ----
if [ ! -d "$MODEL" ]; then
  echo "=== converting HF -> MLX bf16 ==="
  $PY -m mlx_lm convert --hf-path "$MODEL_HF" --mlx-path "$MODEL" --dtype bfloat16
fi

# ---- A' conversion control: qwen-finance-repro (file-based guard) ----
if [ ! -f train/gguf/qwen-finance-repro-Q4_K_M.gguf ]; then
  echo "=== A': HF -> GGUF f16 -> Q4 ==="
  $PY train/llama.cpp/convert_hf_to_gguf.py "$MODEL_HF" \
    --outfile train/gguf/qwen-finance-repro-f16.gguf --outtype f16
  llama-quantize train/gguf/qwen-finance-repro-f16.gguf train/gguf/qwen-finance-repro-Q4_K_M.gguf Q4_K_M
  rm -f train/gguf/qwen-finance-repro-f16.gguf
fi
cat > train/qwen-finance-repro.Modelfile << EOF
FROM ./gguf/qwen-finance-repro-Q4_K_M.gguf
TEMPLATE """$TEMPLATE"""
PARAMETER stop <|im_start|>
PARAMETER stop <|im_end|>
EOF
(cd train && ollama create qwen-finance-repro:coe -f qwen-finance-repro.Modelfile)
echo "=== qwen-finance-repro:coe (A') ready ==="

# ---- ORPO training (same recipe as legal/healthcare) ----
N_TRAIN=$(wc -l < $DATA/train.jsonl | tr -d ' ')
ITERS=$(( N_TRAIN * 4 > 400 ? 400 : N_TRAIN * 4 ))
echo "=== ORPO training ($N_TRAIN pairs, $ITERS iters) ==="
if [ ! -f "$ADAPTERS/adapters.safetensors" ]; then
  $PY -m mlx_lm_lora.train \
    --model "$MODEL" --train --train-mode orpo --load-in-4bits --train-type lora \
    --data "$DATA" --beta 0.1 --batch-size 1 --gradient-accumulation-steps 4 \
    --learning-rate 5e-6 --iters "$ITERS" --num-layers 16 --adapter-path "$ADAPTERS" \
    --steps-per-report 10 --steps-per-eval 50 --save-every 100 \
    --max-seq-length 1792 --grad-checkpoint --seed 42
fi

echo "=== fusing adapters ==="
rm -rf "$FUSED"
$PY -m mlx_lm fuse --model "$MODEL" --adapter-path "$ADAPTERS" --save-path "$FUSED"

echo "=== ORPO: GGUF f16 -> Q4 ==="
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" \
  --outfile train/gguf/qwen-finance-orpo-f16.gguf --outtype f16
llama-quantize train/gguf/qwen-finance-orpo-f16.gguf train/gguf/qwen-finance-orpo-Q4_K_M.gguf Q4_K_M
rm -f train/gguf/qwen-finance-orpo-f16.gguf

cat > train/qwen-finance-orpo.Modelfile << EOF
FROM ./gguf/qwen-finance-orpo-Q4_K_M.gguf
TEMPLATE """$TEMPLATE"""
PARAMETER stop <|im_start|>
PARAMETER stop <|im_end|>
EOF
(cd train && ollama create qwen-finance-orpo:coe -f qwen-finance-orpo.Modelfile)
echo "=== CELL3-FINANCE DONE — qwen-finance-repro:coe + qwen-finance-orpo:coe ready ==="
