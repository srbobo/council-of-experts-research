#!/bin/bash
# Phase 3 — LoRA-DPO train Saul on the behavior pairs, then convert to
# saul-dpo-v2:coe. Run from the repo root:  bash train/run_phase3.sh
#
# Prereqs: train/data/dpo_pairs/{train,valid,test}.jsonl exist (Phase 2)
#          and the Phase-0 toolchain (.venv-train, train/llama.cpp clone).
#
# Pipeline (identical to the saul-repro:coe path except the LoRA step, so
# the only delta between the two tags is the trained weights):
#   1. mlx-lm-lora DPO  (LoRA rank 16, beta 0.1, sigmoid loss, ~1 epoch)
#   2. fuse adapters -> HF safetensors
#   3. convert_hf_to_gguf -> f16
#   4. llama-quantize -> Q4_K_M
#   5. ollama create saul-dpo-v2:coe  (same Modelfile template as saul-repro)
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv-train/bin/python
MODEL_HF=train/models/Saul-7B-Instruct-v1
MODEL=train/mlx/saul-bf16
DATA=train/data/dpo_pairs
ADAPTERS=train/adapters/saul-dpo-v2
FUSED=train/models/Saul-7B-DPO-v2-fused

# Free unified memory: the fp32 checkpoint is 27 GB; training needs the
# bf16 copy (~14 GB) plus activations, so Ollama's resident models must
# be evicted first (gpt-oss alone holds ~13.7 GB).
echo "=== unloading ollama models ==="
# `ollama ps` has no --format flag (that error killed this script once,
# under pipefail, with the failure masked by an outer `| tail`). Parse
# the table instead, and armor the whole block against set -e.
(ollama ps 2>/dev/null | awk 'NR>1 && $1 != "" {print $1}' || true) | while read -r m; do
  echo "  stopping $m"
  ollama stop "$m" 2>/dev/null || true
done
ollama ps || true

# Convert fp32 HF checkpoint -> MLX bf16 once (idempotent).
if [ ! -d "$MODEL" ]; then
  echo "=== converting HF fp32 -> MLX bf16 ==="
  $PY -m mlx_lm convert --hf-path "$MODEL_HF" --mlx-path "$MODEL" --dtype bfloat16
fi

N_TRAIN=$(wc -l < $DATA/train.jsonl | tr -d ' ')
# ~4 epochs of forward passes at batch 1 x grad-accum 4 over 91 pairs.
ITERS=$(( N_TRAIN * 4 ))  # epoch-matched: NO cap — 16 epochs like the 91-pair run
echo "=== Phase 3: DPO training ($N_TRAIN pairs, $ITERS iters) ==="

$PY -m mlx_lm_lora.train \
  --model "$MODEL" \
  --train \
  --train-mode orpo \
  --load-in-4bits \
  --train-type lora \
  --data "$DATA" \
  --beta 0.1 \
  --batch-size 1 \
  --gradient-accumulation-steps 4 \
  --learning-rate 5e-6 \
  --iters "$ITERS" \
  --num-layers 16 \
  --adapter-path "$ADAPTERS" \
  --steps-per-report 10 \
  --steps-per-eval 50 \
  --save-every 100 \
  --max-seq-length 1792 \
  --grad-checkpoint \
  --seed 42

echo "=== fusing adapters ==="
$PY -m mlx_lm fuse \
  --model "$MODEL" \
  --adapter-path "$ADAPTERS" \
  --save-path "$FUSED"

echo "=== converting to GGUF f16 ==="
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" \
  --outfile train/gguf/saul-dpo-v2-f16.gguf --outtype f16

echo "=== quantizing Q4_K_M ==="
llama-quantize train/gguf/saul-dpo-v2-f16.gguf train/gguf/saul-dpo-v2-Q4_K_M.gguf Q4_K_M

echo "=== creating ollama tag ==="
cat > train/saul-dpo-v2.Modelfile << 'EOF'
# Arm C of the DPO + prompt-transfer experiment: Saul-7B with behavior-
# targeted LoRA-DPO fused in. Same conversion pipeline and template as
# saul-repro:coe — the only delta is the trained weights.
FROM ./gguf/saul-dpo-v2-Q4_K_M.gguf
TEMPLATE [INST] {{ if .System }}{{ .System }} {{ end }}{{ .Prompt }} [/INST]
PARAMETER stop [INST]
PARAMETER stop [/INST]
EOF
cd train && ollama create saul-dpo-v2:coe -f saul-dpo-v2.Modelfile
echo "=== DONE — saul-dpo-v2:coe ready; sanity-gate before benching ==="
