# Claim status ledger — the authoritative record

**Updated 2026-08-09**, after program audits #1 and #2, PD-13, Cell 30's
instrument failure, the ledger-baseline confound, and the standing
directive that regex not be used as an instrument in this program.

This file is the single source of truth for what the program claims. Where
a paper, the site, or the runbook disagrees with this file, **this file is
correct** and the other artifact is stale. Every row states its evidence
and its status.

## Status vocabulary

| status | meaning |
|---|---|
| **LIVE** | survives all audits; evidence is causal or internally fair; instrument-independent or measured on scaffold-free arms |
| **PROVISIONAL** | qualitative form supported, parameter values pending re-measurement under a validated instrument |
| **WITHDRAWN** | retracted; must not appear in any artifact except as a recorded correction |
| **BLOCKED** | question open; cannot be answered until an instrument exists |

---

## 1. LIVE claims

| claim | evidence | why it survives |
|---|---|---|
| The PRESERVE instruction causes unwarranted qualification | c = 0.799 [0.56,1.05] with clause vs 0.162 [-0.10,0.43] without, disjoint; Cell 14: conditional clause fired on trigger-free cases at 1.27 | contrast between two arms measured identically; direction does not depend on instrument recall |
| Writers invent qualification with no upstream source | Cell 25 MoA 0.278 [0.12,0.51]; Cell 30 de-scaffolded 4/27 | present in arms whose prompts contain no lexicon strings |
| An instruction produces the phrasing it names, not the behavior | PD-13: dictated 0/30→28/30 vs non-dictated 1/30→4/30, DiD +0.83 [+0.67,+1.00] | the decomposition is internal to one instrument and needs no cross-instrument validity |
| Detector-fed correction loops produce rewording | Cell 19 + manual inspection of the eight intervened runs | established by reading the rewrites, not by an instrument |
| Sequence-level preference training does not move the behavior | three objective classes; preference accuracy 0.48→0.94, behavior unchanged | the null is about the training outcome, measured on both sides identically |
| The council has no measured advantage over one prompted model | Cells 8/14/15 across content, volume, calibration, load | both arms carry the same scaffold; comparison internally fair |
| Corroboration does not increase transport | Cell 26: 0.487 vs 0.524 on the validated channel, CI spanning zero | null under a conservative instrument |
| Repeated attempts are correlated, not independent | ICC 0.190 [0.13,0.24] over 251 cells | structural property of the run design |
| Rich qualification is a property of instructed specialists | 5 detectable qualifications across 27 uninstructed analyses; de-scaffolded seats ~half of scaffolded | direction robust to recall |
| Silence scores well on invention metrics | best invention numbers belong to arms with feature-span 0.000–0.002 | definitional |
| Nine instrument-validity findings | see §4 | these are *about* measurement, so no instrument confound applies |

## 2. PROVISIONAL — form supported, values pending re-measurement

| claim | current value | what is pending |
|---|---|---|
| The shrinkage form $y = ws + c$ | council w=0.352, MoA w=0.158 | all values regex-derived; forms supported by scaffold-free arms |
| The parameter cards (both) | see framework paper Table 1 | re-measurement under a validated instrument |
| The w-band meta-analysis | mu_w 0.364 [0.29,0.44], tau 0.158 | pools mostly scaffolded arms; must be relabelled as instruction-compliance pooling even after re-measurement |
| Register-dependent intercept | prose 0.407 vs ledger −0.023, disjoint | treatment arm is scaffold-free, but measurement is regex; **also awaiting Cell 31's matched-baseline result** |
| Feature-span fraction f | 0.068 median | definitionally regex-bound |
| Aggregation/slope decomposition | modeled share 0.219 | falsified as registered; retained only descriptively |

## 3. WITHDRAWN — must not appear as claims

| claim | withdrawn by | replacement |
|---|---|---|
| "The instruction moves w more than the architectural difference" | PD-13 | "an instruction produces the phrase it names" |
| "C2 carries 126% of the block's gain" as behavioral | PD-13 | compliance with a phrase order |
| The 0.16→0.35 gradient as evidence about instructions | PD-13 + audit #2 | — |
| Cross-architecture w comparison as instruction evidence | audit #2 (four factors move at once) | — |
| The ledger as a demonstrated distinct mechanism | ledger-baseline confound | pending Cell 31 |
| The Markov composition law w'=∏w_k | PA28.a (own pre-registered check) | licensing-gate model, unregistered |
| "The gate taught evasion" as a two-instrument finding | audit #1 | inspection-based finding only |
| Aggregation-distortion claim | P29.3 falsified | hedging's 39% share, descriptive only |
| Ecological claims about natural specialist caution | audit #2 | supply is manufactured |
| The calibration paper's central claim | Cell 14 | paper retracted entire |
| Intrinsic-band model invariance | earlier correction | floor + length artifact |

## 4. Instrument-validity findings (all LIVE)

1. Zero-route contamination — 39 runs measured a prompt that never executed
2. Empty judge replies scored as substantive labels
3. Off-label instrument use — NLI at 0.93 AUC on its calibration task, 0.12–0.55 on the deployed task
4. Point estimates ranked without intervals — 21 of 27 arms never powered
5. Reused arm labels spanning different case batteries
6. Floor/length artifacts from degenerate outputs
7. Illustrative example presented as observed data
8. **Instrument–scaffold entanglement** — prompts dictate the measured strings
9. **Granularity-dependent judge reliability** — 0.86 per sentence, 0.62 per document

## 5. BLOCKED — open questions awaiting an instrument

- Does the supply→emission slope survive de-scaffolding? (Cell 30's corpus exists; instrument does not)
- Is the ledger a distinct mechanism? (Cell 31 running; measurement held)
- Do the clause effects survive on non-dictated phrasings for cutoff? (0 events; needs more labels)
- Is qualification *warranted*? (no warrant labels exist; caps every normative claim)

## 6. Standing methodological directives

1. **No regex as an instrument** (user directive, 2026-08-09). All prior regex measurements are provisional.
2. **Cutoff family is unmeasurable** with current labels (3 positives). The program covers three families until more labels exist.
3. **Sentence-level counts, not document-level presence** — "any sentence positive" compounds false positives across ~40 sentences.
4. **One factor per comparison**, using the nine-factor arm space; never reuse an arm label across batteries.
5. **Parameters are diagnostics, never optimization targets.**
6. **Report emission alongside any invention metric** — otherwise silence wins.
7. **The 11-item pre-recommendation checklist** runs before any proposed cell.

## 7. Artifact status

| artifact | status |
|---|---|
| `docs/paper_framework.tex` | active draft; instruction-gain contribution withdrawn; carries provisional banner |
| `docs/paper_behavior.tex` | active draft; needs the same provisional banner |
| `docs/paper.tex` | superseded by the framework paper; retain for history, do not submit |
| `docs/paper_calibration.tex` | RETRACTED |
| `docs/paper_witnesses.tex` | superseded; fold anything surviving into the behavior paper |
| `site/` | stale — predates audits #1/#2, PD-13, and the regex directive. **Do not deploy** (Netlify paused) until reconciled with this file |
| `gst/` kit | functional; ships regex as default instrument, which now requires a prominent warning |
