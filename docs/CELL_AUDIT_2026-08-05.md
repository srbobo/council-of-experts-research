# Program audit — every cell, against the full defect catalogue

**Date:** 2026-08-05. **Trigger:** user-directed, after repeated introduced
errors across the program. **Method:** every recorded verdict re-examined
against the defect classes this program has itself documented, with
recomputation wherever the check was cheap enough to run.

## The defect catalogue (all previously observed here)

| class | defect | first observed |
|---|---|---|
| A | zero-route contamination (measured a prompt that never executed) | Cell 14 registration |
| B | empty judge replies scored as substantive labels | Cell 20/21 judge tier |
| C | instrument used off-label (NLI presence vs discrimination calibration) | sweep finding #7 |
| D | point estimates ranked without intervals / unidentifiable parameters | GST sweep |
| E | case-battery or mode-label pooling (comparing different batteries) | load-sweep table |
| F | floor/length artifacts (degenerate outputs pooled into rates) | BioMistral |
| G | illustrative example presented as observed data | **this audit** |

## Verdict-by-verdict status

| cell | verdict on record | status | notes |
|---|---|---|---|
| Phase 1 / P1 | DPO transfer null | SOUND | 1/35 zero-route run in repro & spec arms; nulls with CIs, one run cannot flip them |
| Cell 2 | variance/CI pass | SOUND | — |
| dose-response | 3.2× dose null | SOUND | — |
| Cell 3 (health) | diminishing returns | SOUND | — |
| Cell 3 (finance) | ORPO non-replication | SOUND | "reversal" framing already retired by 7a/7b as instrument-dependent |
| Cell 5 | CPO replicates suppression | SOUND | — |
| Cell 6 / 6c | register ablation; gain curve | SOUND | no zero-route runs found (class A checked, clean) |
| Cell 6b | register survives writer training | SOUND | — |
| Cell 7a | NLI calibration AUC 0.929 | SOUND on-label | discrimination task only; presence use was off-label from then on → Cell 23. Verdict itself flagged the construct issues — the flag was under-heeded, not absent |
| Cell 7b | pairwise judge arbitration | LOW-RISK OPEN | num_predict 8192 makes empty-reply unlikely; parse-failure accounting not fully re-audited |
| Cell 8 | P8.1/P8.3 supported | SOUND (as amended) | P8.2 withdrawn earlier (class A). Magnitude numbers come from routed trigger runs; the 5 zero-route council runs were the case-7 gate condition — exactly the withdrawn measurement |
| Cell 8b | lineage falsified | SOUND (as amended) | intrinsic-band overclaim corrected earlier; Cell 14's "what survives" list still cites the stale claim — historical text, left as written, noted here |
| Cell 11 | calibration reward null | SOUND | — |
| Cell 12 | registered, never run | N/A | — |
| Cell 13 | C2 carries the block | SOUND | trigger tables are n=30 routed runs (class A clean); C2-vs-none disjoint; "126%" is a point ratio and C2-vs-ALL overlap is stated in the verdict; P13.3 withdrawn earlier |
| Cell 14 | calibration claim dead | SOUND | falsification margin ×10 past criterion; "worse" correctly hedged as overlapping |
| Cell 15 | no advantage on any axis | SOUND | between-question variance handling correct; earlier 1.82× correctly retired as noise |
| Cell 16 | not executable | N/A | — |
| Cell 17 | suppression clause null | SOUND | regex-only, but a null under the tuned instrument is conservative; caveat: regex-invisible change would be missed |
| Cell 18 | provenance training null | SOUND | wrong-condition bench already corrected on record |
| **Cell 19** | gate "taught evasion" | **AMENDED** | P19.1–P19.4 stand. P19.5's mechanism claim corrected: NLI detected 0/8 pre-gate — insensitive, corroborated nothing (class C). Manual inspection now grounds the finding: mixture of genuine phrase-evasion and one regex false positive. Two-instrument corroboration story withdrawn |
| Cell 20 | form moves, commitment doesn't | SOUND | judge tier re-run already on record (class B fixed); judge reliability caveat pending Cell 23 anchors |
| Cell 21 | manifest not shippable | SOUND | first pass voided and re-run pairwise on record |
| Cell 22 | VOID per gate | N/A | — |
| GST sweep | nothing beats baseline | SOUND | post-hoc, self-corrected in-session; produced finding #7 |

## New corrections applied in this audit

1. **P19.5 mechanism (class C + G).** The entailment detector never saw the
   flagged behavior (0/8 pre-gate at frozen thresholds; max scores identical
   pre→post on 7/8). The "still detects" sentence was wrong. Persistence is
   now grounded in manual inspection of the revisions — real quotes on
   record — and one flagged invention was the checker's own false positive
   ("Verify current uncompensated care %" as a "cutoff" disclosure).
   Amended in the runbook; corrected in paper_behavior.tex, HARNESS_DESIGN,
   INTERVENTION_DESIGN, and the GST kit's README/docstrings.
2. **Fabricated illustrative quote (class G, new).** paper_behavior.tex
   claimed «"Modeled at" became "we estimate"» — that string appears in no
   intervened run. Replaced with observed quotes. Added to the checklist:
   every quoted example must substring-match a stored artifact.
3. **Ledger hygiene (class A).** 39 zero-route runs sit in ledger files with
   no quarantine marker; exclusion previously happened only as a side effect
   of the adapter's require_upstream. The GST adapter now excludes
   `plan.routes == []` explicitly.
4. **HARNESS_DESIGN gate rule.** "Reported as evasion, not success" was
   itself an overclaim template — corrected to "instrument-relative, with
   inspection deciding between evasion and detector overcount," and the NLI
   confirmation step inside the gate is suspended pending Cell 23.

## Corrections pending, gated on Cell 23 (in flight)

- P23.2 fail ⇒ weaken "confirmed by two instruments" throughout paper and
  site to "two independent measurements" (registered consequence).
- P19.5 re-score under presence thresholds (two pre-gate scores, 0.636 and
  0.903, sit near plausible boundaries).
- site/results.html ~line 1204 "NLI cross-check confirmed no behaviors are
  hiding behind paraphrase" — overstates the instrument's validated scope
  regardless of Cell 23's outcome; batched with the next site update
  (deploys remain paused).

## Honest scorecard

Two of ~22 recorded verdicts required amendment on audit (Cell 19's
mechanism claim today; Cell 8b/site claims earlier), and the fabrication
class (G) had one instance. The registered-consequence machinery worked:
every falsified prediction's consequence was executed. The recurring failure
mode is not the arithmetic — it is narrative overreach at the boundary
between what an instrument showed and what we wanted it to have shown. The
kit's guards (extrapolation, weak identification, instrument-relative
labels) now encode most of this catalogue; class G needs a human-process
rule, not code: **no quoted example ships without a substring match against
a stored artifact.**
