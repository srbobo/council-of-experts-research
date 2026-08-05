#!/bin/bash
# Compile check that catches BOTH errors and unresolved references.
# Usage: ./checkpdf.sh [paper.tex]  — previously this script HARDCODED
# paper.tex and silently ignored its argument, so a caller could "check"
# an edit to a different paper and get a clean verdict on an unrelated file
# (2026-08-05 audit). It now fails loudly if the target does not exist.
cd "/Users/sambobo/Documents/Claude Projects/CoE/docs"
TEX="${1:-paper.tex}"
[ -f "$TEX" ] || { echo "*** FAIL: no such file $TEX ***"; exit 1; }
PDF="${TEX%.tex}.pdf"
echo "checking: $TEX"
tectonic "$TEX" 2>&1 | grep -icE "^error|error:" | xargs echo "latex errors:"
n=$(pdftotext "$PDF" - 2>/dev/null | grep -cE "\[\?\]|§\?|Fig\. \?|Table \?|Appendix \?")
echo "unresolved refs: $n"
[ "$n" -gt 0 ] && echo "*** FAIL: unresolved references ***" && exit 1
grep -c bibitem "$TEX" | xargs echo "bibitems:"
pdfinfo "$PDF" | grep Pages
