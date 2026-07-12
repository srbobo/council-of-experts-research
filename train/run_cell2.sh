#!/bin/bash
# Cell 2 — variance pass: bring every (case × mode) to 5 imported runs.
# Idempotent: counts existing imports and only runs the shortfall, so it
# can be killed and relaunched until complete.
set -uo pipefail
cd "$(dirname "$0")/.."
TARGET=5
MODES="local-council-repro local-council-spec local-council-dpo local-council-sft"
CASES="case_1_clinical_decision_support case_2_cross_border_digital_therapeutic case_3_capitated_risk_contract case_4_glp1_employer_coverage case_5_nonprofit_hospital_pe_conversion case_6_trigger_heavy_biotech_ma case_7_trigger_light_baseline"
for case in $CASES; do
  for mode in $MODES; do
    have=$(ls bench/runs/imported/*"${case}__${mode}.json" 2>/dev/null | wc -l | tr -d ' ')
    need=$(( TARGET - have ))
    for i in $(seq 1 $need); do
      echo "=== $case / $mode  run $((have+i))/$TARGET  ($(date +%H:%M:%S)) ==="
      .venv/bin/python -m bench compare --case "$case" --modes "$mode" >/dev/null 2>&1
      f=$(ls -t bench/runs/*/"${case}__${mode}.json" 2>/dev/null | head -1)
      [ -n "$f" ] && .venv/bin/python -m bench.import_run --case "$case" --mode "$mode" --model "cell2-seed" --from-audit-log "$f" | tail -1
    done
  done
done
echo "=== CELL 2 COMPLETE ==="
