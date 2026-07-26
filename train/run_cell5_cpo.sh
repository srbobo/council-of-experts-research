#!/bin/bash
# Cell 5 (P5) — CPO train Saul on the ORIGINAL 91 legal pairs; everything else
# identical to the v1 ORPO arm (run_phase3.sh): same base, bf16, LoRA config,
# iters, seed. Only --train-mode differs. Hardened: file-based guards,
# self-cleaning f16 intermediates, Q4 truncation size-guard.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv-train/bin/python
MODEL_HF=train/models/Saul-7B-Instruct-v1
MODEL=train/mlx/saul-bf16
DATA=train/data/dpo_pairs_legal91
ADAPTERS=train/adapters/saul-cpo
FUSED=train/models/Saul-7B-CPO-fused

echo "=== unloading ollama models ==="
(ollama ps 2>/dev/null | awk 'NR>1 && $1 != "" {print $1}' || true) | while read -r m; do
  ollama stop "$m" 2>/dev/null || true
done
mkdir -p train/gguf train/adapters

if [ ! -d "$MODEL" ]; then
  echo "=== converting HF -> MLX bf16 ==="
  $PY -m mlx_lm convert --hf-path "$MODEL_HF" --mlx-path "$MODEL" --dtype bfloat16
fi

N_TRAIN=$(wc -l < $DATA/train.jsonl | tr -d ' ')
ITERS=$(( N_TRAIN * 4 > 400 ? 400 : N_TRAIN * 4 ))
echo "=== CPO training ($N_TRAIN pairs, $ITERS iters) ==="
if [ ! -f "$ADAPTERS/adapters.safetensors" ]; then
  $PY -m mlx_lm_lora.train \
    --model "$MODEL" --train --train-mode cpo --load-in-4bits --train-type lora \
    --data "$DATA" --beta 0.1 --dpo-cpo-loss-type sigmoid \
    --batch-size 1 --gradient-accumulation-steps 4 \
    --learning-rate 5e-6 --iters "$ITERS" --num-layers 16 --adapter-path "$ADAPTERS" \
    --steps-per-report 10 --steps-per-eval 50 --save-every 100 \
    --max-seq-length 1792 --grad-checkpoint --seed 42
fi

echo "=== fusing adapters ==="
rm -rf "$FUSED"
$PY -m mlx_lm fuse --model "$MODEL" --adapter-path "$ADAPTERS" --save-path "$FUSED"

echo "=== GGUF f16 -> Q4 ==="
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" \
  --outfile train/gguf/saul-cpo-f16.gguf --outtype f16
llama-quantize train/gguf/saul-cpo-f16.gguf train/gguf/saul-cpo-Q4_K_M.gguf Q4_K_M
rm -f train/gguf/saul-cpo-f16.gguf

sz=$(stat -f%z train/gguf/saul-cpo-Q4_K_M.gguf)
echo "Q4 size: $sz"
if [ "$sz" -lt 3800000000 ]; then echo "ERROR: Q4 looks truncated"; exit 1; fi

cat > train/saul-cpo.Modelfile << 'EOF'
# Cell 5 (P5): Saul-7B with behavior-targeted LoRA-CPO fused in. Same
# conversion pipeline and template as saul-repro/saul-dpo — the only delta
# vs saul-dpo is the training objective (CPO vs ORPO).
FROM ./gguf/saul-cpo-Q4_K_M.gguf
TEMPLATE [INST] {{ if .System }}{{ .System }} {{ end }}{{ .Prompt }} [/INST]
PARAMETER stop [INST]
PARAMETER stop [/INST]
EOF
(cd train && ollama create saul-cpo:coe -f saul-cpo.Modelfile)
echo "=== CELL5 DONE — saul-cpo:coe ready ==="
