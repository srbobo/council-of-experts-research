# Pre-registration — GST measurement and intervention on {{SYSTEM}}

Commit this file BEFORE running anything. The git timestamp is the record.
Everything below is filled in ahead of the run except the Results section,
which stays empty until the analysis is complete.

---

## 1. System under study

- **Architecture:** (lead-council / MoA / RAG-synthesis / other; how many
  upstream components, arranged how)
- **Writing model:** name, size, and access level (API / open weights /
  residual-stream access)
- **Upstream components:** what produces the text the writer reads
- **Task distribution:** where the prompts come from. State plainly whether
  they are authored, sampled from production traffic, or drawn from a public
  benchmark — authored cases cannot support claims about a task distribution.

## 2. Property class and instruments

- **Property class:** what is being preserved, discarded, or invented
  (epistemic qualification / source attribution / numeric provenance / other)
- **Families:** the countable sub-behaviors, with their definitions
- **Instrument 1:** name, how validated, known blind spots
- **Instrument 2:** name, how validated, known blind spots
- **Independence argument:** why these two instruments do not share a failure
  mode. If they do, say so — the joint blind-spot figure is then an overstatement.

**Rules in force (do not edit):**
- No verdict rests on a single instrument.
- The instrument that generates any corrective feedback never grades
  compliance with that feedback.
- Empty or unparseable instrument replies are excluded and counted, never
  defaulted to a substantive label.
- Rates are reported beside raw counts and zero-rates.

## 3. Execution-path assertion

- **Required routes per run:** (minimum number of upstream components that
  must actually have contributed)
- **Required marker in the writer prompt:** (a string that proves the
  intended condition executed)
- **Quarantine policy:** violating runs are stored, counted, and excluded
  from every estimate. They are never silently dropped.

## 4. Design

- **Supply variation:** how runs will span supply levels. Natural variation
  is usually insufficient; state whether ablation (`gst.corpus`) is used.
- **Repeated sampling:** number of runs per (task, condition, writer) cell.
  At least 2 is required for an empirical best-of-n curve; more is better.
- **Sample size and stopping rule:** fixed in advance. No optional stopping.
- **Blinding:** who or what sees which condition, and when.

## 5. Predictions

Register each as a numbered proposition with the falsification condition
stated. Vague predictions cannot fail, and a prediction that cannot fail is
not one.

- **P1 (A1, shrinkage):** w will fall in [___, ___] and c in [___, ___].
  *Falsified if* w > 0.85 with c < 0.15 (faithful transduction), or the
  quadratic term's CI excludes zero for reasons other than a ceiling against
  a bounded family count.
- **P2 (A2, dilution):** f will be below ___, implying sequence-level
  preference training moves ranking metrics without moving behavior.
  *Falsified if* whole-sequence training at this f does move emitted behavior.
- **P3 (A3, selection vs feedback):** verifier-blind selection will improve
  the measured property under BOTH instruments; a feedback loop over the same
  verifier will improve it under the feedback instrument only.
  *Falsified if* selection shows instrument-relative improvement (the second
  instrument disagrees), which would break the framework's central asymmetry.
- **P4 (intervention):** ___
  *Falsified if* ___

## 6. Consequences

State now what each outcome obliges you to do, so the obligation is not
negotiable later.

- If P1 holds: ___
- If P1 is falsified: ___
- If the intervention shows no effect: ___ (a null is a result; say where it
  will be reported)

## 7. Analysis plan

- Estimators: `gst.measure` at version ___, seed ___
- Exclusions: floor guard at ___ characters; quarantined runs; empty replies
- Multiplicity: how many predictions are being tested, and what correction
  (if any) applies
- The parameter card will be published in full, including guards that fired

---

## Results

*(Leave empty until the analysis is complete. Fill in once, and do not edit
the sections above afterward — amend by appending a dated amendment instead.)*

## Amendments

*(Any change after the first run goes here, dated, with the reason and
whether it was made before or after unblinding.)*
