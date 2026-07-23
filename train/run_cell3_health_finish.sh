#!/bin/bash
# Cell 3 (healthcare) — packaging-only finish: fuse the trained ORPO adapter
# -> GGUF f16 -> Q4_K_M -> med42-orpo:coe. Skips A' and training (both done).
# Used to recover after the fuse step ran out of disk on the first pass; the
# adapter (the real training output) is intact, so this just repackages it.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv-train/bin/python
MODEL=train/mlx/med42-bf16
ADAPTERS=train/adapters/med42-orpo
FUSED=train/models/Med42-ORPO-fused

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

rm -rf "$FUSED"  # clear any partial from the disk-full crash
echo "=== fusing adapters ==="
$PY -m mlx_lm fuse --model "$MODEL" --adapter-path "$ADAPTERS" --save-path "$FUSED"

echo "=== converting to GGUF f16 ==="
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" \
  --outfile train/gguf/med42-orpo-f16.gguf --outtype f16

echo "=== quantizing Q4_K_M ==="
llama-quantize train/gguf/med42-orpo-f16.gguf train/gguf/med42-orpo-Q4_K_M.gguf Q4_K_M

cat > train/med42-orpo.Modelfile << EOF
FROM ./gguf/med42-orpo-Q4_K_M.gguf
TEMPLATE """$TEMPLATE"""
PARAMETER stop <|eot_id|>
PARAMETER stop <|start_header_id|>
EOF
(cd train && ollama create med42-orpo:coe -f med42-orpo.Modelfile)

# Reclaim the f16 intermediate immediately (Q4 + ollama now hold the weights).
rm -f train/gguf/med42-orpo-f16.gguf
echo "=== CELL3-HEALTH-FINISH DONE — med42-orpo:coe ready ==="
