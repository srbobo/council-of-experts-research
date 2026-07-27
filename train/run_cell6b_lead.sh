#!/bin/bash
# Cell 6b (P6b) — train the SYNTHESIZER. Qwen2.5-7B-Instruct as Lead:
# A' conversion control (qwen-lead-repro:coe) + ORPO on synthesis-level pairs
# (qwen-lead-orpo:coe). Identical recipe to every seat arm EXCEPT
# --max-seq-length 4096 (documented amendment: synthesis examples are ~3.3k
# tokens; 0% fit 1792, so training there would truncate the completion).
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv-train/bin/python
MODEL_HF=train/models/Qwen2.5-7B-Instruct
MODEL=train/mlx/qwen25-bf16
DATA=train/data/dpo_pairs_lead
ADAPTERS=train/adapters/qwen-lead-orpo
FUSED=train/models/Qwen25-Lead-ORPO-fused

# Qwen2.5 ChatML, system preserved (the Lead genuinely uses a system prompt).
read -r -d '' TEMPLATE << 'TPL' || true
{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>
TPL

echo "=== unloading ollama models ==="
(ollama ps 2>/dev/null | awk 'NR>1 && $1 != "" {print $1}' || true) | while read -r m; do
  ollama stop "$m" 2>/dev/null || true
done
mkdir -p train/gguf train/adapters train/models

if [ ! -d "$MODEL_HF" ]; then
  echo "=== downloading Qwen2.5-7B-Instruct ==="
  $PY -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-7B-Instruct', local_dir='$MODEL_HF', ignore_patterns=['*.bin'])"
fi

if [ ! -d "$MODEL" ]; then
  echo "=== converting HF -> MLX bf16 ==="
  $PY -m mlx_lm convert --hf-path "$MODEL_HF" --mlx-path "$MODEL" --dtype bfloat16
fi

# ---- A' conversion control ----
if [ ! -f train/gguf/qwen-lead-repro-Q4_K_M.gguf ]; then
  echo "=== A': HF -> GGUF f16 -> Q4 ==="
  $PY train/llama.cpp/convert_hf_to_gguf.py "$MODEL_HF" \
    --outfile train/gguf/qwen-lead-repro-f16.gguf --outtype f16
  llama-quantize train/gguf/qwen-lead-repro-f16.gguf train/gguf/qwen-lead-repro-Q4_K_M.gguf Q4_K_M
  rm -f train/gguf/qwen-lead-repro-f16.gguf
fi
cat > train/qwen-lead-repro.Modelfile << EOF
FROM ./gguf/qwen-lead-repro-Q4_K_M.gguf
TEMPLATE """$TEMPLATE"""
PARAMETER stop <|im_start|>
PARAMETER stop <|im_end|>
EOF
(cd train && ollama create qwen-lead-repro:coe -f qwen-lead-repro.Modelfile)
echo "=== qwen-lead-repro:coe (A') ready ==="

# ---- ORPO training (seq-len amended to 4096; see runbook) ----
N_TRAIN=$(wc -l < $DATA/train.jsonl | tr -d ' ')
ITERS=$(( N_TRAIN * 4 > 400 ? 400 : N_TRAIN * 4 ))
echo "=== ORPO training on SYNTHESIS pairs ($N_TRAIN pairs, $ITERS iters, seq 4096) ==="
if [ ! -f "$ADAPTERS/adapters.safetensors" ]; then
  $PY -m mlx_lm_lora.train \
    --model "$MODEL" --train --train-mode orpo --load-in-4bits --train-type lora \
    --data "$DATA" --beta 0.1 --batch-size 1 --gradient-accumulation-steps 4 \
    --learning-rate 5e-6 --iters "$ITERS" --num-layers 16 --adapter-path "$ADAPTERS" \
    --steps-per-report 10 --steps-per-eval 50 --save-every 50 \
    --max-seq-length 4096 --grad-checkpoint --seed 42
fi

echo "=== fusing adapters ==="
rm -rf "$FUSED"
$PY -m mlx_lm fuse --model "$MODEL" --adapter-path "$ADAPTERS" --save-path "$FUSED"

echo "=== GGUF f16 -> Q4 ==="
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" \
  --outfile train/gguf/qwen-lead-orpo-f16.gguf --outtype f16
llama-quantize train/gguf/qwen-lead-orpo-f16.gguf train/gguf/qwen-lead-orpo-Q4_K_M.gguf Q4_K_M
rm -f train/gguf/qwen-lead-orpo-f16.gguf

sz=$(stat -f%z train/gguf/qwen-lead-orpo-Q4_K_M.gguf)
echo "Q4 size: $sz"
if [ "$sz" -lt 3800000000 ]; then echo "ERROR: Q4 looks truncated"; exit 1; fi

cat > train/qwen-lead-orpo.Modelfile << EOF
FROM ./gguf/qwen-lead-orpo-Q4_K_M.gguf
TEMPLATE """$TEMPLATE"""
PARAMETER stop <|im_start|>
PARAMETER stop <|im_end|>
EOF
(cd train && ollama create qwen-lead-orpo:coe -f qwen-lead-orpo.Modelfile)
echo "=== CELL6B DONE — qwen-lead-repro:coe + qwen-lead-orpo:coe ready ==="
