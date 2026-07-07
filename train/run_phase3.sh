#!/bin/bash
# Phase 3 — LoRA-DPO train Saul on the behavior pairs, then convert to
# saul-dpo:coe. Run from the repo root:  bash train/run_phase3.sh
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
#   5. ollama create saul-dpo:coe  (same Modelfile template as saul-repro)
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv-train/bin/python
MODEL=train/models/Saul-7B-Instruct-v1
DATA=train/data/dpo_pairs
ADAPTERS=train/adapters/saul-dpo
FUSED=train/models/Saul-7B-DPO-fused

N_TRAIN=$(wc -l < $DATA/train.jsonl | tr -d ' ')
# ~1 epoch at batch 1 x grad-accum 4; cap for safety on the first run.
ITERS=$(( N_TRAIN > 400 ? 400 : N_TRAIN ))
echo "=== Phase 3: DPO training ($N_TRAIN pairs, $ITERS iters) ==="

$PY -m mlx_lm_lora.train \
  --model "$MODEL" \
  --train \
  --train-mode dpo \
  --train-type lora \
  --data "$DATA" \
  --beta 0.1 \
  --dpo-cpo-loss-type sigmoid \
  --batch-size 1 \
  --gradient-accumulation-steps 4 \
  --learning-rate 5e-6 \
  --iters "$ITERS" \
  --num-layers 16 \
  --adapter-path "$ADAPTERS" \
  --steps-per-report 10 \
  --steps-per-eval 50 \
  --save-every 100 \
  --max-seq-length 3072 \
  --seed 42

echo "=== fusing adapters ==="
$PY -m mlx_lm fuse \
  --model "$MODEL" \
  --adapter-path "$ADAPTERS" \
  --save-path "$FUSED"

echo "=== converting to GGUF f16 ==="
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" \
  --outfile train/gguf/saul-dpo-f16.gguf --outtype f16

echo "=== quantizing Q4_K_M ==="
llama-quantize train/gguf/saul-dpo-f16.gguf train/gguf/saul-dpo-Q4_K_M.gguf Q4_K_M

echo "=== creating ollama tag ==="
cat > train/saul-dpo.Modelfile << 'EOF'
# Arm C of the DPO + prompt-transfer experiment: Saul-7B with behavior-
# targeted LoRA-DPO fused in. Same conversion pipeline and template as
# saul-repro:coe — the only delta is the trained weights.
FROM ./gguf/saul-dpo-Q4_K_M.gguf
TEMPLATE [INST] {{ if .System }}{{ .System }} {{ end }}{{ .Prompt }} [/INST]
PARAMETER stop [INST]
PARAMETER stop [/INST]
EOF
cd train && ollama create saul-dpo:coe -f saul-dpo.Modelfile
echo "=== DONE — saul-dpo:coe ready; sanity-gate before benching ==="
