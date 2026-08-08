# End-to-end adversarial audit — the auditor auditing itself

**Date:** 2026-08-07. **Trigger:** user-directed, with four specific charges:
where the assistant's probabilistic generation led the program astray; whether
the experimental materials were biased toward conclusions; whether
assistant-invented terminology drove inappropriate mathematics; and what
novelty survives. Empirical checks were run where the question was checkable;
findings below are graded by severity.

---

## A. Circularity in the experimental materials (checked empirically today)

### A1. SEVERE — the instrument–instruction loop

`council/prompts.py` was inspected against the lexicon. The seat prompts
instruct the specialists to produce the measured families BY NAME, and in two
places dictate the LITERAL STRINGS the lexicon detects:

- The finance seat prompt suggests the phrasings `"assuming," "under the
  assumption that..."` — matching the lexicon's `\bassuming (?:that|the...)`
  patterns.
- The PRESERVE synthesis instruction commands: *"your synthesis MUST also
  label it as an assumption (use "modeled at," "assumed")"* — dictating the
  exact string the `modell?ed at` regex measures.

Consequences, honestly graded:

1. **The instruction-gain results are partially tautological.** "The C2
   numeric clause lifts the modeled family 0.003 → 0.499" (Cell 13) is
   measured compliance with an instruction that names the measured string.
   The valid residue is: (a) the instruction's effect is CONDITIONAL
   (gate/trigger differences within the same scaffold are real contrasts),
   and (b) even literal phrase-dictation achieves only partial compliance —
   but "instructions move epistemic disposition 3–4×" overstates what was
   shown. It should read "instructions naming target phrases move those
   phrases 3–4×, conditionally."
2. **Cross-architecture w comparisons are scaffold-confounded.** The
   council's w = 0.35 was measured with a phrase-dictating scaffold present;
   MoA's w = 0.16 without it, and with proposers whose dialect the lexicon
   was never tuned to. The paper's "the instruction moves w more than the
   architecture" leans partly on this confounded contrast. The clean
   within-scaffold instruction contrast (flat 0.255 vs council 0.346) has
   OVERLAPPING intervals. **Paper amendment required.**
3. **Supply is manufactured.** The seats raise 2.5–4 families because they
   are prompted and fine-tuned to; uninstructed general models raise ~0
   (Cell 25's side observation now reads as confirmation). Ecological
   claims about "what specialists naturally raise" are unsupported. The
   defensible reframe is a-fortiori and actually SHARPENS the negative
   result: **under conditions rigged maximally toward transport —
   instructed seats, an echo phrase dictated to the writer — only a third
   of supplied qualification arrives.** The pessimistic law survives; its
   parameter values are scaffold-specific.
4. **What survives untouched:** the zero-supply invention results (the
   writer emits lexicon-class phrases with no seat raising them, and in the
   MoA arms with no instruction naming them — if anything the scaffold
   finding makes uninstructed invention MORE striking); and the ledger
   arms' c ≈ 0 (the ledger protocol contains no family names and no
   dictated phrases — checked — so the register contrast is scaffold-free
   on the treatment side).

This is recorded as **instrument-validity finding #8: instrument–scaffold
entanglement.** The kit's documentation must warn that a lexicon shared
between the system's instructions and its measurement measures compliance,
not disposition.

### A2. CLEARED — the authored cases are lexicon-clean

All case texts measured: zero lexicon families fire in any case prompt,
including the trigger-heavy ones. The trigger mechanism is topical (drug
pricing → recency disclosure), not string-planting. The trigger-heavy/light
design is legitimate, and the "authored zero-warrant anchor" for invention
is not string-circular. Its remaining weakness is different: the warrant
judgment ("this case deserves no hedging") is the author's, never
externally validated. Judge validation of warrant labels remains open work.

### A3. Injection selection bias (moderate, disclosed but under-weighted)

Cell 25/27 injections were selected to fire exactly one family — so
high-supply strata carry perfectly-detectable supply while natural low-supply
strata may hide undetected qualification. Measurement error is correlated
with stratum. Direction of bias on w unquantified; flagged for any future
sweep.

---

## B. Registration strength was heterogeneous, and the weakest were presented like the strongest

- **Genuinely prospective** (data generated after freeze): Cells 13–21, 23,
  25, 27, 28. These carry real evidential force.
- **Retrospective on partially-seen data** (recomputation cells 24, 26, 29):
  the author had prior aggregate exposure to the corpus. Cells 24 and 26
  retain force because their outcomes SURPRISED the registrant (24 reversed
  the registered direction; 26 falsified the offered hypothesis). Cell 29 is
  the weak case: P29.4 (register intercept) was registered AFTER the ledger
  arms' c ≈ 0 was known — it is a descriptive pooling wearing a
  registration, and should be cited as measurement, not as a passed test.
  P29.1's bars were likewise set with heavy knowledge of the arm fits.
- **Bar authorship:** the same agent writes bars and analyses. One realized
  dead-zone bar (P28.2) and two underpowered bars (P17.1, P19.1) were found
  by the attainability audit; the structural fix (attainability check at
  registration) is now practice, but bar-choice bias is not fully
  eliminable while one agent plays both roles.

---

## C. The probability-system failure modes, with instances

### C1. Plausible-continuation fill-in (the auditor exhibits the studied phenomenon)

Documented instances: the "still detects" evasion mechanism (wrong), the
fabricated «"we estimate"» quote, the attenuation prediction (reversed), the
"[0.12, 0.45] band" (too tight), two SUPPORTED-printing harness defects
(point-vs-CI; ±0.02 threshold). The pattern is exactly the program's own
c > 0: when evidence is ambiguous, the generator fills from its prior with
fluent, unsourced material. The registration/guard system is, precisely,
this author's evidence ledger — and the error rate under it (2 amended
verdicts, 1 fabrication, caught) versus before it argues the mechanism
works, without arguing it is complete.

### C2. Context-window losses

Bibliography deletion; checkpdf silently checking the wrong paper;
56%-vs-40% population mixing in the framework paper's first draft;
superseded numbers (493-run fit) persisting across compactions until
re-derived. Long-horizon state is a real failure surface; the mitigation
that worked was recomputing from disk rather than trusting recalled numbers.

### C3. Agenda-setting bias

Nearly every cell, instrument, and framing in this program was
assistant-proposed and user-ratified with brief approvals. Alternatives
systematically under-surfaced: **every parameter card is one writer model**
(gpt-oss-20B; the multi-writer arms are the weakly-identified ones), so "the
law" is one model's law until a second-writer card exists; external/human
validation of warrant was never prioritized; a same-architecture
different-writer card would have tested generality better than the chosen
same-writer different-architecture card for some claims. Velocity (five
cells in three days) is itself a generation-loop artifact.

### C4. Terminology → mathematics, detangled term by term

| term | origin | did it drive math? | verdict |
|---|---|---|---|
| "bottleneck" | assistant metaphor | YES — the Markov product law w′=w₁w₂ | WRONG math; refuted by own pre-registered check (PA28.a); replaced by licensing-gate model |
| "dose-response" | pharmacology | YES — causal language on observational fits | council-card w is CORRELATIONAL (case difficulty is a common cause of seat supply and answer hedging); only ablation arms (25/27/28) support causal w. **Paper amendment required: label the council card observational.** |
| "Poisson" | assistant | YES — e^−λ clean-rate math in the v1.0 design | wrong twice (independence + dispersion); retired by the atlas's measured under-dispersion |
| "band" | assistant | soft — invariance rhetoric | corrected by the atlas (τ = 0.158, PI to 0.68) |
| "heat" | assistant | banned by user early | no math attached; clean |
| "shrinkage / prior-trust ratio" | statistics | interpretation, not computation | the regression is valid; the normal-normal COGNITIVE reading ("the writer trusts its prior 1.8×") is a story on top of a slope; the w* derivation is sound decision theory but inherits the cognitive framing |
| "gain control," "transport" | engineering | slogan compression | each slogan mixes results of different validity (density claims valid; w claims scaffold-confounded); slogans should not outrun their weakest component |

---

## D. What survives — novelty and consistency after every downgrade

**Survives at full strength:**
1. **Uninstructed invention at zero supply** — causal (ablation-based),
   cross-architecture, present WITHOUT any scaffold naming the phrases, and
   eliminable by register/licensing constraint (0/22 under the ledger
   arms). The bidirectionality novelty against the uncertainty-loss
   literature stands.
2. **The register-dependent intercept** — same writer, same battery, same
   instrument, scaffold-free treatment arm; the cleanest causal contrast
   the program owns.
3. **The instrument-validity case study, now eight findings** — including
   today's scaffold entanglement, which no external critic found for us.
   This is the program's most transferable contribution and is untouched by
   the biases above because it is ABOUT them.
4. **The kit and its guards** — each guard maps to a realized error,
   several of them the author's own.
5. **Prompt heterogeneity (ICC 0.19)** — internally valid, instrument-relative.
6. **The discipline corpus itself** — 29 registered cells, executed
   consequences, and now three self-audits with corrections on record.

**Survives downgraded:** the shrinkage law as a descriptive regularity of
one writer under maximally transport-favorable scaffolding (which makes its
low w MORE damning, not less); instruction effects as conditional
phrase-compliance.

**Does not survive:** the cross-architecture w comparison as evidence about
instructions; ecological claims about natural specialist caution; the
cognitive reading of w as "trust" stated as fact; Cell 29's P29.4 as a
"passed prediction" rather than a measurement.

**Mandated by this audit:** (1) framework-paper amendments — observational
labeling of the council card, scaffold disclosure, softening of the
instruction-gradient claim to its within-scaffold form; (2) the
de-scaffolded replication as the highest-value future cell: seats prompted
for substance without family names, a paraphrase-robust instrument
(judge-based or the classifier), a second writer model; (3) kit
documentation warning on instrument–scaffold entanglement.
