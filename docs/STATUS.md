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
| Writers invent qualification with no upstream source | **Cell 38: 4/12 = 0.333 [0.138, 0.609]** on upstream CONFIRMED at exactly zero by the validated instrument | first defensible zero-supply measurement; no lexicon in system or instrument; earlier regex-stratum rates superseded |
| An instruction produces the phrasing it names, not the behavior | PD-13: dictated 0/30→28/30 vs non-dictated 1/30→4/30, DiD +0.83 [+0.67,+1.00] | the decomposition is internal to one instrument and needs no cross-instrument validity |
| Detector-fed correction loops produce rewording | Cell 19 + manual inspection of the eight intervened runs | established by reading the rewrites, not by an instrument |
| Sequence-level preference training does not move the behavior | three objective classes; preference accuracy 0.48→0.94, behavior unchanged | the null is about the training outcome, measured on both sides identically |
| No measured council advantage — **held as absence of evidence, not evidence of absence** (attainability audit 2026-08-11) | Cells 8/14/15 across content, volume, calibration, load; Cell 36 diff CI [-0.085,+0.034] | no positive evidence of advantage exists anywhere, which keeps the row LIVE — but Cell 36's paired comparison contained **3 discordant items of 59** (ceiling 0.92-0.97; the bootstrap resampled three coin-flips) and Cells 8/14/15 are regex-era and unaudited at run level. Weight accordingly; the harder battery decides |
| Corroboration does not increase transport | Cell 26: 0.487 vs 0.524 on the validated channel, CI spanning zero | null under a conservative instrument |
| Repeated attempts are correlated, not independent | ICC 0.190 [0.13,0.24] over 251 cells | structural property of the run design |
| Rich qualification is a property of instructed specialists | 5 detectable qualifications across 27 uninstructed analyses; de-scaffolded seats ~half of scaffolded | direction robust to recall |
| Aggregation wins preference at 20B scale — **now TWO judge families** | Cell 43: 0.818 [0.718,0.919] (gpt-oss); Cell 43-R: 0.788 [0.645,0.917] (qwen3-vl, judge selected blind to direction); survives length-matching; arm lengths within 1.4% | replicated across vendor/architecture/generation; self-preference symmetric; NOT explained by length or framework density — composition unidentified |
| Dictated qualification phrases COST preference | Cell 43: 0.261 [0.140,0.388] and 0.317 [0.152,0.480] (gpt-oss, both forms below 0.5); Cell 43-R: form-Y replicates at 0.217 [0.125,0.333]; form-X points the same way (0.276) but spans at n=29 decisive | causal and counterbalanced; three of four judge-x-form cells exclude 0.5, the fourth agrees in point estimate, none contradicts. Preference pressure is in measured tension with epistemic marking |
| **The lead uses a routed clarification it asked for** — the first supported positive intervention in the program | Cell 44: informed 7/7 = 1.000 vs control 0.333 (CI [+0.200,+1.000]) and vs ritual filler 0.200 (CI [+0.545,+0.947]); informed arm unanimous across both judges; adversarial resolution of every judge disagreement still leaves gaps of +0.40/+0.53; literal secondary agrees | orchestrator-routed re-consultation (design c), lead-side with controlled clarifications; conditioned n=7, agreement 0.703 on the analysis population (0.583 overall, recorded), one writer — scope stated; seat-side realism is design (b), not yet run |
| **Re-consultation is recognition-limited, not capability-limited** | Cell 44: lead uses a routed clarification 7/7 but names the tension 0.34; Cell 45: seat routes correctly 10/11 = 0.909 [0.623,0.984] but recognizes the out-of-domain need only 0.306, gap CI [-0.056,+0.528] spanning zero (P45.1 falsified, P45.2 supported) | both halves of the loop show a working mechanism behind a scarce trigger; design (c), which takes its trigger from the mandated tension list rather than model self-assessment, is the recommended architecture — design (b) does not proceed per its registered consequence |
| **Engineered redundancy is causal** — the planner's overlap assignment, isolated as one factor, halves corruption adoption | Cell 47: corrupted-value adoption 0.900 bare vs 0.450 planned (CI [+0.200,+0.725]); clean-value adoption 0.000 vs 0.500 (CI [+0.175,+0.825]) — the co-source is USED, not merely diluting; exact-match instrument, decisive 0.94 | first prospective test of the harness architecture (§3); bare arm doubles as the sharpest no-verification number on record (0.900 corruption repeat when sole-sourced). Protection is BIMODAL across items — three fully protected, two not at all — so the mean halving must not be quoted as uniform; which quantities the selector protects is OPEN |
| **Out-of-band freight carries AND is used** — the harness's §6 channel tested on both halves | Cell 48: appendix carriage 1.000 vs 0.174 surviving prose transport (third convergent transport measurement); preference cost NOT EVALUABLE at power (0.510 [0.267,0.754], 65/116 ties — no evidence of penalty, no license to claim absence). Cell 51: appendix-carried caveats FLIP a reader's registered two-token decision at +0.691 [+0.455,+0.891] over a matched irrelevant-appendix control (k=11 items, 440 runs, 0 invalid); channel parity with in-prose placement (+0.091 [-0.036,+0.218] under frozen thresholds); bare floor 0.000, caution-priming delta +0.036 | uptake is causal and content-specific (irrelevant appendix moves nothing, 0.036); direction-balanced items rule out caution-as-uptake; replication reader (qwen2.5:7b) shows same structure at lower reader capability (uptake +0.455, with per-item failures shared by prose — reader-limited, not channel-limited). Verdict population is 11 of 18 authored items after the G1 floor gate (deviation recorded); one artifact corpus, one primary reader family |
| **Sibling visibility does not cause lane bleed** — §2's prohibition loses its causal warrant (informative null) | Cell 52: off-domain framework density, sibling − roster, **−0.009 [−0.048, +0.028]**, 18 case clusters, 322 generations analyzed; CI upper bound BELOW the registered MDD band (+0.05–0.08 computed from archive before the run); in-domain density unchanged (0.143 vs 0.141) | one-factor, byte-fixed archived sibling context, production prompts; tests the sibling-OUTPUT clause only — the historical v2→v3 incident involved cross-domain framing in seat INSTRUCTIONS, untested here. Echo-excluded estimation came back −0.033 [−0.053, −0.013] (LOWER with siblings visible) — unregistered direction, descriptive only, candidate "free-riding keeps seats narrower" mechanism NOT claimed (C50 discipline). Roster-only isolation now stands on cost grounds, not contamination |
| **The re-consultation loop works end-to-end with a live seat** — production, conveyance, and use, no controlled inputs | Cell 54: live-briefed R-adoption 0.905 (19/21) vs archived control 0.333, diff **+0.571 [+0.139, +0.912]**; within −0.095 [−0.227, 0.000] of the scripted ceiling (frozen 0.3 threshold); fact conveyed 21/21 from private working notes (corrected Unicode-folding instrument, replies persisted) | comparators are Cell 44's archived arms under a passed, never-pooled batch check; 6 item clusters; trigger rate is batch-variable (0.208–0.583 across C44/C53/C54) and remains the loop's binding coverage constraint. NEW RISK on record: 4/21 live replies embellished the true fact with fabricated legal authority and were adopted anyway — the content gate screens absence, not invention; fabrication is unbounded pending its own cell |
| **The seating gate predicts pipeline defects** — verdicts frozen at selection, tested at pipeline time | Cell 55: strict rank separation SUPPORTED over ten candidates (min fail-rate 0.333 > max pass-rate 0.056, no inversion); pooled contrast **+0.632 [+0.549, +0.722]**; gate verdicts committed before any pipeline run; screen items disjoint from pipeline cases | fail side has two members (biomistral 17/18 defects; openbiollm 6/18 — a FRESH failure that passed the archive-era screen, so verdicts age and seating must re-gate, not import). Format smoke is a separate axis and does not predict seat defects (saul 0/4 format, 0/18 pipeline) — its target is verdict-emitting roles. Defect = visible text <800 chars; one writer-side outcome family |
| **Live-reply fabrication is bounded: item-triggered, name-stable, never admitted** | Cell 56: reply-level fabrication 0.100 [0.047,0.201] briefed / 0.150 [0.081,0.261] unbriefed (120 replies, archive-validated two-stage instrument, committed classification table); 0/100 on five items vs 15/20 on the one trigger item; the SAME two invented decisions recur in 14 and 13 independent replies; admission of missing specifics 0/20 sampled; backfill contrast +0.050 [+0.000,+0.150] NE at power, direction positive (0.60→0.90 within the trigger item, descriptive) | fourth item-bimodal phenomenon on record; instrument scope is adversarial case citations only, and the sample read shows confident unverified specifics outside that class, so the bound is a FLOOR on confabulation generally; name-stability licenses a blocklist delivery filter (filters, never feeds back — Goodhart-safe); 6 items, one writer, one reply channel |
| **The planner finds ~six in ten load-bearing quantities — and is best at naming what is MISSING** | Cell 57: confirmed recall 0.633 [0.506,0.758] pre-seat / 0.616 [0.469,0.766] post-seat vs mismatched cross-recall 0.019/0.020 (thirty-fold specificity separation); seats add nothing to coverage (−0.017 [−0.100,+0.064]) though list composition churns; unknown-class recall 0.813 vs stated-class 0.531 | PARTIAL band per frozen registration: §3's error immunity is now stated as bounded by planner coverage (~0.6); measured recall is a FLOOR (probe under-recall observed and recorded); ground truth is 41 analyst-authored labels under a frozen decision-relevance rule after the archive labels were rejected as deliberately-peripheral; 493-pair committed confirmation table; sub-question writing untested; third occurrence of the Unicode-hyphen instrument bug recorded and corrected pre-confirmation |
| **The §3 chain works end-to-end live: the clean co-source is USED through planner-authored sub-questions** | Cell 59: clean adoption +0.425 [+0.325,+0.525] (vs Cell 47's planted +0.500), 80 fully-live pipeline runs; assignment 40/40 plans (committed confirmation), conveyance 0.85–0.95; corrupted suppression NE at power (−0.175 [−0.350,+0.025]) with the live bare floor at 0.625 vs planted 0.900 and the protected level replicating at 0.450 | Cell 58's registered halt en route yielded the channel finding: briefed notes convey only into task-relevant assignments (2/8 orthogonal vs 21/21 pointed, C54) — the corrected planner input guarantees relevance by construction. Fourth value-format instrument incident (spaced percent/magnitude) recorded with the cumulative probe-format set; C47 archive rescored under the identical matcher for the like-for-like estimation; 8 item clusters; fifth item-bimodal phenomenon logged |
| Silence scores well on invention metrics | best invention numbers belong to arms with feature-span 0.000–0.002 | definitional |
| Fourteen instrument-validity findings | see §4 | these are *about* measurement, so no instrument confound applies |

## 2. PROVISIONAL — form supported, values pending re-measurement

| claim | current value | what is pending |
|---|---|---|
| ~~The shrinkage form~~ **The transport coefficient** $y = ws + c$ — **now LIVE for TWO writers** (Cell 46) | gpt-oss w = 0.318 [+0.221,+0.431] (n=82); phi4 w = 0.177 [+0.058,+0.275] (n=62), 18 cases, judge agreement 0.877. Within-corpus: gpt-oss 0.172 old / 0.326 new; **phi4 0.170 [+0.067,+0.265] on the new corpus alone** — replication owing nothing to pooling. Linear form holds (T1); observed w is an attenuated LOWER bound, disattenuated band 0.150-0.217 on Cell 30 (T2) | **Pooled figures are cross-regime and must NOT be quoted as a within-corpus rate** — new cases carry mean supply 25.3 vs 5.4, and the pooled slope equals the between-cluster line. phi4's realized n_eff was 42.3 against a registered 47, so point estimates carry Type-M inflation risk. Name retired: transport coefficient, not shrinkage (Cell 37 falsified the estimator story) |
| The parameter cards (both) | see framework paper Table 1 | re-measurement under a validated instrument |
| The w-band meta-analysis | mu_w 0.364 [0.29,0.44], tau 0.158 | pools mostly scaffolded arms; must be relabelled as instruction-compliance pooling even after re-measurement |
| ~~Register-dependent intercept~~ | — | **WITHDRAWN 2026-08-10.** The original result compounded a two-factor baseline with an entangled instrument, so the claim had no support — the withdrawal is a burden-of-proof decision and stands. **Attainability audit 2026-08-11: Cell 31's null is UNINFORMATIVE** — Δc = +0.182 [−0.868, +1.261] *contains the originally claimed gap of +0.637*. Cell 31 may be cited only as failure to re-establish the claim, never as evidence the ledger does nothing. The question is OPEN, not answered-no. |
| Feature-span fraction f | 0.068 median | definitionally regex-bound |
| Aggregation/slope decomposition | modeled share 0.219 | falsified as registered; retained only descriptively |

## 3. WITHDRAWN — must not appear as claims

| claim | withdrawn by | replacement |
|---|---|---|
| "The writer recomputes" / any use of the word recomputation | Cell 37 P37.1 FALSIFIED — **re-checked 2026-08-11 against finding #11 and it holds**, because its falsification condition is a within-arm contrast (A2: 5 corrupted vs 2 correct) that base-rate depression cannot manufacture. P37.2 downgraded to NOT EVALUABLE | the writer is a SOURCE SELECTOR: prefers an uncorrupted source when one exists, propagates the error when none does. Cell 37's *rates* are not behaviour rates and its "neither" cells are not omission |
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
9. **Granularity-dependent judge reliability** — demonstrated on one corpus: 0.833 per sentence vs 0.622 per document, same judges, same 60 documents
10. **Construction blind spots propagate into the design** — regex-driven ablation left 5.4 qualification-bearing sentences in texts labelled zero-supply; the manipulation never created the condition it was built for
11. **An injected premise that contradicts its host question creates a competing source rather than manipulating the intended one** — Cells 37/40 injected primitives conflicting with the case prompt; on item 0 the writer used the case's numbers in 21/21 runs across both cells and the injected numbers 0 times. The "use novel numbers to reduce memorization" rule and coherence with the host question are in direct conflict, and no registration reconciled them. Repair is not idempotent either: this defect was introduced by the fix for a probe collision
12. **Entanglement reached the INSTRUMENT layer, not only the scaffold** — `train/judge_instrument.py::PROMPT` (Cell 7b's pairwise judge) enumerates the same seven phrases dictated to writers by the ADD/addendum prompts (registry R101-R107). A judge told to look for "modeled at" was scoring a writer told to say "modeled at". Found mechanically by the dictation registry on its first run (`docs/DICTATION_REGISTRY.json`)
13. **Registry form essentially never arises without dictation** — 0 of 2907 spans and 0 of 60 de-scaffolded runs (438,797 chars) contain any registry phrase; run-level Wilson upper bound 0.060. The scaffold's phrases are diagnostic OF the scaffold, which is what makes literal-stage partitioning trustworthy, and it corroborates PD-13 from an independent corpus
14. **Local pairwise preference judging is majority reading-order — a task-format property, not a model quirk** — raw first-position preference 0.85-0.88 across four judges from four families (gpt-oss, qwen2.5, phi4, qwen3-vl; Cells 43/43-R); decisive rates under order-debiasing span 0.05-0.40. The bias magnitude is invariant; only the escape rate varies. Both-orderings protocols pay 60-95% of the sample for honesty

## 5. BLOCKED — open questions awaiting an instrument

- ~~Does the supply→emission slope survive de-scaffolding?~~ **ANSWERED 2026-08-10: yes, w = 0.150 [0.058, 0.252] on gpt-oss.**
- ~~Does compensating invention survive?~~ **ANSWERED 2026-08-10 (Cell 38): yes, 0.333 [0.138, 0.609] on confirmed-zero upstream.**
- Can ablation reach true zero supply at all? **NO** — judge-driven ablation also leaves residue (finding #10 generalised); requires upstream authored to contain no qualification
- Is the ledger a distinct mechanism? **OPEN** — Cell 31 completed but its null is uninformative (CI contains the original effect; attainability audit 2026-08-11). A decisive cell needs the n its CI width implies (~4× Cell 31's)
- Do the clause effects survive on non-dictated phrasings for cutoff? (0 events; needs more labels)
- Is qualification *warranted*? (no warrant labels exist; caps every normative claim)
- Do the domain seats buy RECALL accuracy? (Cell 36 measured reasoning, not recall; needs an externally sourced battery)
- Would a harder battery separate the arms? (Cell 36 hit a ceiling at 0.92-0.97; its null is weak)
- **Can a SEAT instruct the lead?** STILL OPEN. Cell 40 ran to completion (81/81) and is **NOT EVALUABLE**: 3, 6 and 2 decisive runs against a required 6 per arm, because the injected premises contradicted the host case and the writer answered the case (finding #11). Neither prediction is falsified. A re-run is blocked on two pre-run conditions: premises drawn from the host case, and an attainability check on the outcome itself
- Is the writer's use of a prior distinguishable from computation? (Cell 37's P37.2 downgraded to NOT EVALUABLE — both arms at floor, no attainability check was registered for it)

## 6. Standing methodological directives

1. **No regex as an instrument** (user directive, 2026-08-09). All prior regex measurements are provisional.
2. **Cutoff family is unmeasurable** with current labels (3 positives). The program covers three families until more labels exist.
3. **Sentence-level counts, not document-level presence** — "any sentence positive" compounds false positives across ~40 sentences.
4. **One factor per comparison**, using the nine-factor arm space; never reuse an arm label across batteries.
5. **Parameters are diagnostics, never optimization targets.**
6. **Report emission alongside any invention metric** — otherwise silence wins.
7. **The 12-item pre-recommendation checklist** runs before any proposed cell.
8. **Outcome attainability** (item 12, from the attainability audit 2026-08-11): before a cell runs, compute from existing runs the fraction in which the outcome variable can fire, and the CI width the planned n buys against the effect the cell must detect — for every registered prediction, not just the primary. Decisive-fraction is a pre-run check, NEVER a design target (finding #8).
9. **Citation strength follows the audit classes** — a DEGENERATE or UNINFORMATIVE null moves its question to OPEN; it is never cited as evidence of absence (`docs/ATTAINABILITY_AUDIT_2026-08-11.md`).

## 7. Artifact status

| artifact | status |
|---|---|
| `docs/paper_moa_audit.tex` | **active draft v0.1 (2026-08-12)** — the MoA-audit paper; thesis: instructions buy the phrase, the phrase costs preference. Every number verified against this ledger at composition; single-judge and 20B-scale scopes stated in-text |
| `docs/paper_framework.tex` | active draft; instruction-gain contribution withdrawn; carries provisional banner |
| `docs/paper_behavior.tex` | active draft; needs the same provisional banner |
| `docs/paper.tex` | superseded by the framework paper; retain for history, do not submit |
| `docs/paper_calibration.tex` | RETRACTED |
| `docs/paper_witnesses.tex` | superseded; fold anything surviving into the behavior paper |
| `site/` | stale — predates audits #1/#2, PD-13, and the regex directive. **Do not deploy** (Netlify paused) until reconciled with this file |
| `gst/` kit | functional; ships regex as default instrument, which now requires a prominent warning |
