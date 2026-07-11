#!/bin/bash
# Cell 1 of RUNBOOK_PAPER_HARDENING.md — SFT-on-chosen control.
# Single-variable change from run_phase3.sh: --train-mode sft (+--mask-prompt),
# chosen-only data. Same package/loader/LoRA/iters/seed → saul-sft:coe.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv-train/bin/python
MODEL_HF=train/models/Saul-7B-Instruct-v1
MODEL=train/mlx/saul-bf16
DATA=train/data/sft_chosen
ADAPTERS=train/adapters/saul-sft
FUSED=train/models/Saul-7B-SFT-fused

echo "=== unloading ollama models ==="
(ollama ps 2>/dev/null | awk 'NR>1 && $1 != "" {print $1}' || true) | while read -r m; do ollama stop "$m" 2>/dev/null || true; done

if [ ! -d "$MODEL_HF" ]; then
  echo "=== re-downloading Saul HF (recovery path) ==="
  $PY -c "from huggingface_hub import snapshot_download; snapshot_download('Equall/Saul-7B-Instruct-v1', local_dir='$MODEL_HF', ignore_patterns=['*.bin'])"
fi
if [ ! -d "$MODEL" ]; then
  echo "=== converting HF -> MLX bf16 ==="
  $PY -m mlx_lm convert --hf-path "$MODEL_HF" --mlx-path "$MODEL" --dtype bfloat16
fi

N_TRAIN=$(wc -l < $DATA/train.jsonl | tr -d ' ')
ITERS=$(( N_TRAIN * 4 > 400 ? 400 : N_TRAIN * 4 ))
echo "=== SFT-on-chosen: $N_TRAIN completions, $ITERS iters ==="
$PY -m mlx_lm_lora.train \
  --model "$MODEL" --train --train-mode sft --load-in-4bits \
  --train-type lora --data "$DATA" --mask-prompt \
  --batch-size 1 --gradient-accumulation-steps 4 \
  --learning-rate 5e-6 --iters "$ITERS" --num-layers 16 \
  --adapter-path "$ADAPTERS" --steps-per-report 20 \
  --save-every 200 --max-seq-length 1792 --grad-checkpoint --seed 42

echo "=== fuse -> GGUF -> ollama ==="
$PY -m mlx_lm fuse --model "$MODEL" --adapter-path "$ADAPTERS" --save-path "$FUSED"
mkdir -p train/gguf
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" --outfile train/gguf/saul-sft-f16.gguf --outtype f16
llama-quantize train/gguf/saul-sft-f16.gguf train/gguf/saul-sft-Q4_K_M.gguf Q4_K_M
cat > train/saul-sft.Modelfile << 'MF'
FROM ./gguf/saul-sft-Q4_K_M.gguf
TEMPLATE [INST] {{ if .System }}{{ .System }} {{ end }}{{ .Prompt }} [/INST]
PARAMETER stop [INST]
PARAMETER stop [/INST]
MF
cd train && ollama create saul-sft:coe -f saul-sft.Modelfile
echo "=== DONE — saul-sft:coe ready ==="
