#!/bin/bash
# Cell 11 stage 4 — ORPO on calibration-reward pairs. Identical recipe to
# Cell 6b (LoRA r8/scale10/16 layers, lr 5e-6, seed 42, seq 4096, iters
# N*4 capped 400) — ONLY the pair corpus differs. Produces qwen-lead-cal:coe.
# Disk-staged: base weights were cleaned in the Tier-1 sweep, so this
# re-downloads HF (~15GB) then deletes each intermediate as soon as its
# consumer is done (43GB free is not enough to hold them all at once).
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv-train/bin/python
MODEL_HF=train/models/Qwen2.5-7B-Instruct
MODEL=train/mlx/qwen25-bf16
DATA=train/data/dpo_pairs_cell11
ADAPTERS=train/adapters/qwen-lead-cal
FUSED=train/models/Qwen25-Lead-Cal-fused
Q4=train/gguf/qwen-lead-cal-Q4_K_M.gguf

read -r -d '' TEMPLATE << 'TPL' || true
{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>
TPL

free_gb() { df -g / | awk 'NR==2 {print $4}'; }
echo "=== disk: $(free_gb)GB free ==="
if [ "$(free_gb)" -lt 36 ]; then echo "ABORT: need >=36GB free"; exit 1; fi

echo "=== unloading ollama models ==="
(ollama ps 2>/dev/null | awk 'NR>1 && $1 != "" {print $1}' || true) | while read -r m; do
  ollama stop "$m" 2>/dev/null || true
done
mkdir -p train/gguf train/adapters train/models train/mlx

if [ ! -d "$MODEL" ]; then
  if [ ! -d "$MODEL_HF" ]; then
    echo "=== downloading Qwen2.5-7B-Instruct ==="
    $PY -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-7B-Instruct', local_dir='$MODEL_HF', ignore_patterns=['*.bin'])"
  fi
  echo "=== converting HF -> MLX bf16 ==="
  $PY -m mlx_lm convert --hf-path "$MODEL_HF" --mlx-path "$MODEL" --dtype bfloat16
  echo "=== removing HF base (MLX conversion done; A' gguf already exists) ==="
  rm -rf "$MODEL_HF"
fi

N_TRAIN=$(wc -l < $DATA/train.jsonl | tr -d ' ')
ITERS=$(( N_TRAIN * 4 > 400 ? 400 : N_TRAIN * 4 ))
echo "=== ORPO on calibration pairs ($N_TRAIN pairs, $ITERS iters, seq 4096) ==="
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
echo "=== removing MLX base (fuse done) ==="
rm -rf "$MODEL"

echo "=== GGUF f16 -> Q4 ==="
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" \
  --outfile train/gguf/qwen-lead-cal-f16.gguf --outtype f16
llama-quantize train/gguf/qwen-lead-cal-f16.gguf "$Q4" Q4_K_M
rm -f train/gguf/qwen-lead-cal-f16.gguf

sz=$(stat -f%z "$Q4")
echo "Q4 size: $sz"
if [ "$sz" -lt 3800000000 ]; then echo "ERROR: Q4 looks truncated"; exit 1; fi
rm -rf "$FUSED"

cat > train/qwen-lead-cal.Modelfile << EOF
FROM ./gguf/qwen-lead-cal-Q4_K_M.gguf
TEMPLATE """$TEMPLATE"""
PARAMETER stop <|im_start|>
PARAMETER stop <|im_end|>
EOF
(cd train && ollama create qwen-lead-cal:coe -f qwen-lead-cal.Modelfile)
echo "=== CELL11 TRAIN DONE — qwen-lead-cal:coe ready ($(free_gb)GB free) ==="
