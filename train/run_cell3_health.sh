#!/bin/bash
# Cell 3 (healthcare, P3) — build the Med42 A' conversion-control (med42-repro)
# and the ORPO-trained seat (med42-orpo), same pipeline, so the only delta is
# the trained weights. Mirrors run_phase3.sh (the legal seat) exactly:
# same LoRA config, iters, seed — clean cross-seat comparison for P2/P3.
#
# Both tags use Med42's NATIVE Llama-3 template (folded system-in-user to match
# the folded training pairs), NOT the mismatched ChatML the stock GGUF shipped.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv-train/bin/python
MODEL_HF=train/models/Llama3-Med42-8B
MODEL=train/mlx/med42-bf16
DATA=train/data/dpo_pairs_health
ADAPTERS=train/adapters/med42-orpo
FUSED=train/models/Med42-ORPO-fused

# Med42 Llama-3 template, system folded into the user turn (matches training).
read -r -d '' TEMPLATE << 'TPL' || true
{{ if .System }}<|start_header_id|>user<|end_header_id|>

{{ .System }}

{{ .Prompt }}<|eot_id|>{{ else }}<|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>

TPL

echo "=== unloading ollama models ==="
(ollama ps 2>/dev/null | awk 'NR>1 && $1 != "" {print $1}' || true) | while read -r m; do
  ollama stop "$m" 2>/dev/null || true
done

mkdir -p train/gguf train/adapters

# ---- A' conversion control: med42-repro (HF fp16 -> GGUF -> Q4, no training) ----
if ! ollama list 2>/dev/null | grep -q "med42-repro:coe"; then
  echo "=== A': converting base HF -> GGUF f16 ==="
  $PY train/llama.cpp/convert_hf_to_gguf.py "$MODEL_HF" \
    --outfile train/gguf/med42-repro-f16.gguf --outtype f16
  echo "=== A': quantizing Q4_K_M ==="
  llama-quantize train/gguf/med42-repro-f16.gguf train/gguf/med42-repro-Q4_K_M.gguf Q4_K_M
  cat > train/med42-repro.Modelfile << EOF
FROM ./gguf/med42-repro-Q4_K_M.gguf
TEMPLATE """$TEMPLATE"""
PARAMETER stop <|eot_id|>
PARAMETER stop <|start_header_id|>
EOF
  (cd train && ollama create med42-repro:coe -f med42-repro.Modelfile)
  echo "=== med42-repro:coe (A') ready ==="
fi

# ---- ORPO training (same recipe as legal run_phase3.sh) ----
N_TRAIN=$(wc -l < $DATA/train.jsonl | tr -d ' ')
ITERS=$(( N_TRAIN * 4 > 400 ? 400 : N_TRAIN * 4 ))
echo "=== ORPO training ($N_TRAIN pairs, $ITERS iters) ==="

if [ ! -f "$ADAPTERS/adapters.safetensors" ]; then
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
fi

echo "=== fusing adapters ==="
$PY -m mlx_lm fuse --model "$MODEL" --adapter-path "$ADAPTERS" --save-path "$FUSED"

echo "=== ORPO: converting to GGUF f16 ==="
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" \
  --outfile train/gguf/med42-orpo-f16.gguf --outtype f16

echo "=== ORPO: quantizing Q4_K_M ==="
llama-quantize train/gguf/med42-orpo-f16.gguf train/gguf/med42-orpo-Q4_K_M.gguf Q4_K_M

cat > train/med42-orpo.Modelfile << EOF
FROM ./gguf/med42-orpo-Q4_K_M.gguf
TEMPLATE """$TEMPLATE"""
PARAMETER stop <|eot_id|>
PARAMETER stop <|start_header_id|>
EOF
(cd train && ollama create med42-orpo:coe -f med42-orpo.Modelfile)
echo "=== CELL3-HEALTH DONE — med42-repro:coe + med42-orpo:coe ready ==="
