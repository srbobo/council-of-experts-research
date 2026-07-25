#!/bin/bash
# Cell 3 (finance) — packaging-only finish: fused ORPO model -> GGUF f16 -> Q4
# -> qwen-finance-orpo:coe. Recovers after the first Q4 truncated on disk-full.
# The adapter + fused model are intact; this just repackages with room to spare.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv-train/bin/python
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

echo "=== GGUF f16 ==="
$PY train/llama.cpp/convert_hf_to_gguf.py "$FUSED" \
  --outfile train/gguf/qwen-finance-orpo-f16.gguf --outtype f16
echo "=== quantize Q4_K_M ==="
llama-quantize train/gguf/qwen-finance-orpo-f16.gguf train/gguf/qwen-finance-orpo-Q4_K_M.gguf Q4_K_M
rm -f train/gguf/qwen-finance-orpo-f16.gguf   # reclaim ~16G immediately

# sanity: refuse to register a truncated Q4 (A' is ~5.0G; guard at 4.5G)
sz=$(stat -f%z train/gguf/qwen-finance-orpo-Q4_K_M.gguf)
echo "Q4 size: $sz bytes"
if [ "$sz" -lt 4500000000 ]; then echo "ERROR: Q4 looks truncated ($sz)"; exit 1; fi

cat > train/qwen-finance-orpo.Modelfile << EOF
FROM ./gguf/qwen-finance-orpo-Q4_K_M.gguf
TEMPLATE """$TEMPLATE"""
PARAMETER stop <|im_start|>
PARAMETER stop <|im_end|>
EOF
(cd train && ollama create qwen-finance-orpo:coe -f qwen-finance-orpo.Modelfile)
echo "=== CELL3-FINANCE-FINISH DONE — qwen-finance-orpo:coe ready ==="
