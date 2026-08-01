#!/bin/bash
# Compile check that catches BOTH errors and unresolved references.
cd "/Users/sambobo/Documents/Claude Projects/CoE/docs"
tectonic paper.tex 2>&1 | grep -icE "^error|error:" | xargs echo "latex errors:"
n=$(pdftotext paper.pdf - 2>/dev/null | grep -cE "\[\?\]|§\?|Fig\. \?|Table \?|Appendix \?")
echo "unresolved refs: $n"
[ "$n" -gt 0 ] && echo "*** FAIL: unresolved references ***" && exit 1
grep -c bibitem paper.tex | xargs echo "bibitems:"
pdfinfo paper.pdf | grep Pages
