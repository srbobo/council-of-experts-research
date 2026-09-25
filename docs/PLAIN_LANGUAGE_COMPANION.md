# The Council That Mostly Didn't Work

## A plain-language companion to the two papers

This document walks through the same ground as *Instructions Buy the Phrase; the Phrase Costs Preference* (the audit paper) and *Design by Falsification* (the harness paper), in the order those papers use, but without the scientific vocabulary. Where the papers give a statistic, this document gives the number and says what it means. Where the papers cite a ledger entry, this document says what was actually done. Nothing here is a new claim; every finding below has a registered experiment behind it in the two papers.

A reading note on the numbers. Almost every result in the program is a proportion: how often something happened out of how many tries. When the papers write a value like 0.818 with a bracket after it, the bracket is the range the true value could plausibly sit in given how few cases there were. The plain-language version here says things like "about 82%, and plausibly anywhere from 72% to 92%." When the range includes 50% for a head-to-head comparison, or includes zero for a difference, the honest reading is "no detectable effect," and the papers say so.

---

# Part One: The Audit

## 1. The idea being tested

There is a popular recipe for getting better answers out of AI language models. Instead of asking one model a question, ask several, then hand all of their answers to one more model and tell it to combine the best of what it received. The published version of this recipe is called Mixture-of-Agents, and it reports beating GPT-4o on a standard leaderboard.

The recipe comes with a story about why it works. Models are supposed to be "collaborative": shown other models' answers, they produce better ones, even when some of those answers are weak. The combining model is imagined as something like a careful editor who reads every draft, checks the claims, weighs the agreement between drafts, and writes something better than any of them.

Every number supporting that story comes from one kind of measurement: another AI is shown two answers and asked which one it prefers. No published evaluation of the recipe checks whether the combined answer is actually more correct, whether an error in one draft spreads into the final answer, whether the preferring AI is trustworthy on this task, or whether an instruction to the editor changes what it does or only what it says.

This program built the recipe at a small enough scale to check all of that. The models were open ones running on a single machine, between 7 and 20 billion parameters, small enough that every run could be saved, re-read, and re-scored. Three "specialist" models (healthcare, legal, and finance) each answered a business-advisory question, and one editor model combined their answers. Eighteen advisory scenarios were used throughout.

## 2. Calling the shot before running

The program had one rule that shaped everything: before any experiment ran, a written registration stated what was predicted, what result would count as the prediction failing, and, from existing data, how often the thing being measured could even occur. That last item matters more than it sounds. If you predict "the editor will use the specialist's warning," but specialists only issue warnings one time in ten, the experiment cannot tell you much no matter how it comes out. Registrations were committed to version control before the first run, so the order of events is provable.

Results were entered into a running ledger that marks each claim as live, provisional, withdrawn, or blocked. Three separate reviews went back over the ledger and downgraded earlier findings that did not hold up. When this document says a result is "on the record," it means the result is a live ledger entry that survived those reviews.

## 3. Checking the measuring instruments first

Before trusting any finding about the models, the program checked the tools used to measure them. Fourteen problems were found and recorded. Four of them shape everything downstream.

**Counting your own words.** Suppose you tell the editor "when a number is an estimate, say it is *modeled at* rather than stating it flatly." Then you check how often the editor's output contains the words "modeled at." You will find it does, and you will be tempted to conclude the editor has become careful about estimates. But you dictated those words. What you measured is obedience, not carefulness. The program found this confusion in its own earlier work: an instruction moved the dictated wording from 0 out of 30 outputs to 28 out of 30, while other ways of saying the same thing barely moved (1 out of 30 to 4 out of 30). The instruction was buying the phrase.

**A registry of dictated phrases.** To stop this from happening again, the program extracted every phrase that any prompt put into a model's mouth (125 phrases from 35 prompts), froze the list, and refused to run any experiment whose prompts contained a phrase the measuring tool would then count. On its first use, the registry caught that an earlier preference-judging prompt in the program listed the very same seven phrases the writing prompts dictated. The tool for judging outputs had been told to look for the words the outputs had been told to use. The program also checked whether these phrases ever appear on their own, without being dictated: across 2,907 passages and 60 runs with all instructions stripped, they never did. That is what makes the registry trustworthy as a detector of scaffolding rather than of natural writing.

**A judge that names no phrases.** To score whether an output actually expresses uncertainty, the program used two AI judges reading sentence by sentence, with definitions that describe the behavior without naming any wording and that explicitly tell the judge not to reward particular phrasing. The two judges agreed 91% of the time across more than 15,000 decisions. An earlier approach that had the judges read whole documents at once agreed only 62% of the time and was thrown out.

**Preference judges mostly pick whichever answer they read first.** When an AI is shown two answers and asked which is better, it picks the first one 85% to 88% of the time. This was true for four different judges from four different model families and sizes, so it is a property of the task, not of any one model. The only fix is to show every pair in both orders and count a result only when the judge picks the same answer both times. Doing that turns 60% to 95% of comparisons into ties. Every preference result in the program uses this fix, which means every preference result rests on the minority of pairs where the judge had a real opinion.

## 4. The phrase-swap experiment

This is the experiment that gives the audit paper its title.

**What was done.** The editor was run three ways on the same eighteen scenarios, seven times each, for 378 runs. One version had a plain prompt. The other two had the same prompt plus one sentence: "When you state a number that is an estimate rather than an established fact, label it using the phrase 'modeled at'." The third version was identical except the phrase was "taken to be." The first phrase had been used in the program's prompts for months. The second was invented the day before and had never appeared anywhere in the program's two million characters of archived output.

**What happened to the phrases.** Each instructed version produced its own phrase in about two thirds of outputs (67% and 70%). The plain version never produced either. No run ever produced the other version's phrase. The months-old house phrase and the day-old invented one performed identically. Whatever the instruction did, it did not draw on any learned habit around the familiar words.

**What happened to the behavior.** The two sentence-level judges then scored how often each output expressed that a number was an estimate *using any wording other than the dictated phrase*. The plain version did this in 34% of runs. The two instructed versions did it in 37% and 32%. Those differences are well inside the noise. Outputs were the same length across all three versions, so the instructed editor was not simply saying less.

**What it means.** The instruction produced the words it asked for and nothing else measurable. The editor did not become more careful about estimates; it learned which two words to insert. The experiment can rule out any hidden behavioral effect larger than about 22 percentage points; it cannot rule out something smaller, and the paper says so.

## 5. The preference experiment

**What was done.** Three head-to-head comparisons on the same scenarios, with every pair judged in both orders and counted only if the judge agreed with itself.

First, the full recipe (three specialists plus editor) against the same editor answering the question directly with no specialists. Second and third, each phrase-instructed version of the editor against the plain version. Because the phrase-swap experiment had already established that those versions differ only in the phrase, any preference difference is caused by the phrase.

**The recipe wins.** Out of 44 pairs where the judge had a real opinion, the full recipe won 82% (plausibly 72% to 92%). The two sides produced answers of nearly the same length (a 1.4% difference), and the recipe still won 82% among the pairs where lengths were closest, so this is not the judge rewarding longer answers. The winner did not consistently use more business frameworks either. What the judge is responding to remains unidentified; the paper says it cannot name the ingredient without a better instrument.

**The phrase loses.** Against the plain version, the "modeled at" editor won only 26% of decided pairs and the "taken to be" editor won 32%. Both are clearly below even. The program had predicted the opposite, that a judge would reward the careful-sounding register. The prediction failed in reverse.

**A second judge from a different family agrees.** All 378 pairs were re-judged by a 30-billion-parameter model from a different vendor, chosen from three candidates by a script that looked only at whether the model could do the task, never at which side it favored. The recipe's win replicated (79%). The "taken to be" penalty replicated (22%). The "modeled at" penalty landed at 28%, the same direction, but with too few decided pairs to be sure, and the paper records that as "not replicated at this power" rather than as a contradiction.

**Putting the two experiments together.** An instruction to be careful about estimates installs only a phrase. A preference judge penalizes that phrase. So any system that is tuned toward what the judge prefers, which is how most AI systems are improved today, will strip out the phrase and leave the underlying carefulness exactly where it was, which is to say unchanged, because the instruction never touched it. The two standard levers pull in opposite directions on the same surface, and neither reaches the thing they are both supposed to be about.

## 6. Does the editor do what the story says it does?

The recipe's story credits the editor with several abilities. Each was tested.

**Does the editor check facts?** Arithmetic claims were planted in the specialists' drafts, some correct and some deliberately wrong. When one specialist's number was wrong but another specialist had the right one, the wrong number reached the final answer 0 times out of 27. When every specialist had the wrong number, it reached the final answer 5 times out of 27. When the specialists' working was also removed, 12 times out of 27. So the editor does not recompute anything. It picks. When a clean source exists it picks the clean source, and when none exists it has nothing to fall back on. The recipe's claim that the editor gets better even from worse drafts fails at the level of facts: worse drafts made the final answer factually worse.

**Does agreement between specialists count for anything?** Claims that two or more specialists independently made reached the final answer no more often than claims only one made (49% versus 52%). The one signal this architecture uniquely provides, corroboration, goes unused.

**How much of the specialists' caution survives?** The specialists' drafts were scored for how many sentences expressed uncertainty, and the editor's output was scored the same way. Across 144 runs, two editor models, and two sets of scenarios, the editor passed along between 11% and 33% of what it was given. Two thirds to nine tenths of the specialists' caution is lost in the rewrite, and the loss rate looks like a property of the rewriting step itself rather than of any one model. The editor also invents caution of its own about a third of the time when given drafts that contain none.

**Are specialists actually different from each other?** Two medical fine-tunes of the same base model were compared with their base. One used noticeably more medical frameworks than the base, the other did not, and a third lineage moved in the opposite direction. Fine-tuning leaves a fingerprint per model, not per domain. Two "medical" specialists are no more alike than one specialist is with itself across runs. A published follow-up to the original recipe independently found the same thing at leaderboard scale: sampling one good model several times beats mixing different ones.

**Is the combined answer more correct?** On a 60-question test with checkable answers, the recipe and the bare editor scored the same, both between 92% and 97%. Two further tests were built to be harder (36 multi-step calculations and 30 rule-interaction problems with scripted answers), and the bare editor scored 98% on both. There is no room for the recipe to improve on a score that high, so the question was declared untestable at this scale. A committee cannot add accuracy where one member already has the answer.

## 7. The one thing that worked: sending the question back

**The design.** The editor's prompt already required it to list, before writing, the points where the specialists' drafts were in tension. Instead of asking the editor to decide whether it needed help, a separate piece of software read that list and sent a follow-up question to the relevant specialist. Six scenarios were built where the deciding fact was withheld from the specialists' first drafts. Three versions were run: no follow-up; a follow-up reply that sounded responsive but contained no deciding fact; and a reply that contained it.

**The result.** When the editor had named the tension, and the reply contained the fact, the editor resolved the question the way the fact implied 7 times out of 7. With no follow-up it did so 33% of the time. With the empty-sounding reply, 20% of the time. The information did the work. The ritual of consulting did not.

This fits everything else rather than contradicting it. The editor cannot check facts, ignores agreement, and does not become careful when told to. But it does reliably prefer a clean source over a corrupt one. Sending the question back manufactures a clean source at exactly the disputed point, which is the one lever the editor demonstrably responds to.

**The catch.** The loop only runs if the editor names the tension in the first place, and on these planted problems it did so only 34% of the time. A companion experiment gave specialists the option to raise their hand and defer to a colleague. When they raised it, they pointed at the right colleague 10 times out of 11. But they raised it about as often when the question was squarely in their own field as when it was not. Models act correctly when prompted to act. They do not reliably notice that they should.

**Closing the loop with a real specialist.** The results above used scripted replies. Two more experiments used a live specialist model. The first put the deciding fact in the specialist's own first draft, and the editor named the tension only 21% of the time, so that experiment stopped at its pre-declared checkpoint. The second gave the specialist the fact as private notes it had not written down, closer to how a real expert holds knowledge. The live specialist conveyed the fact in all 21 follow-ups, and the editor adopted it 90% of the time versus 33% without the loop, essentially matching the scripted ceiling. One risk appeared: in 4 of the 21 replies, the specialist dressed the correct fact up with invented case law or regulatory rulings, and the editor accepted those too. A follow-up experiment measured this at 10% to 15% of replies, concentrated on one topic, with the same two invented citations recurring, which is what makes a blocklist filter possible.

**On real problems, the catch is smaller.** When the assembled system was later run on 54 natural inquiries rather than planted ones, the follow-up fired on 85% of them. Real specialists disagree often. The scarce-trigger problem is the floor, not the forecast.

## 8. What the audit means

The recipe's headline is not overturned. Combining several models' answers really does produce something a judge prefers, at this scale, under fair judging, against an equal-length baseline. What is overturned is the explanation. The preference is not coming from the editor being careful (instructions for that buy phrases, and the judge penalizes phrases), not from length, and not from framework-heavy writing. Underneath it, the editor selects rather than verifies.

Two practical implications follow. First, any system improved by preference training will quietly lose whatever visible caution its instructions installed, so caution that must survive has to live somewhere the judge never sees, in a structured field or a separate section rather than in the prose. Second, at this scale roughly five sixths of a raw "which is better" verdict is reading order, so any evaluation that shows pairs in one order only is measuring position.

---

# Part Two: The Harness

## 9. The plan, and what happened to it

The system that was going to be built was ordinary for its moment: three domain specialists, one lead writer, and a set of assumptions that seemed too obvious to test. Specialists know things generalists do not. Telling the writer to preserve uncertainty makes it careful. A model that is out of its depth can say so. When specialists agree, that agreement means something.

Nine such assumptions were written down and tested one at a time. Here is the scorecard in plain words.

| The council needed this to be true | What was done | What happened |
|---|---|---|
| Specialists trained on the same field share a way of thinking | Compared two medical fine-tunes of one base model | **False.** Each fine-tune has its own fingerprint; the two disagree with each other. |
| An instruction to be careful changes the writer's behavior | Swapped the instructed phrase for a synonym | **False.** The named phrase appears; nothing else changes. |
| Careful marking is at worst neutral to a judge | Judged instructed versions against plain, both orders | **Backwards.** The phrase loses, and a second judge family agrees. |
| A specialist can tell when a question is outside its field | Gave specialists a way to defer | **False.** They defer to the right colleague when they do defer, but defer about as often in their own field as outside it. |
| Agreement between specialists strengthens a claim | Planted agreement across drafts | **No effect.** Corroborated claims survive no better than single ones. |
| The writer checks the specialists' facts | Planted wrong numbers | **False.** The writer picks a source; it never recomputes. |
| The council gives more correct answers | Three tests with checkable answers | **Cannot be tested.** The single writer already scores 92% to 98%; there is no room to improve. |
| The writer's prose carries the specialists' caution | Counted caution sentences in and out | **Mostly lost.** Between 11% and 33% survives. |
| What a model says about its own confidence predicts what it does | Asked models to rate their own plausibility and ownership | **False, twice.** A stable, near-unanimous self-report predicted behavior at exactly coin-flip. |

Three of these failures turned out to be the foundation for what came next.

**Obedience is not behavior.** The instruction reliably bought its own phrase and nothing else. Every "be careful" line in a system prompt is, on this evidence, buying words.

**The writer is a chooser, not a checker.** With a clean source available, errors never propagated. Without one, they did. That sets a ceiling (no prompt will make the writer verify) and opens a door (you can control which sources exist).

**The bottleneck is noticing, not acting.** In every consultation design, the mechanism worked when it fired and fired rarely. The writer used a follow-up 7 times out of 7 but asked for one only a third of the time. Specialists pointed correctly when they deferred but deferred without discrimination. The one faculty the whole industry leans on for escalation, a model knowing it needs help, was the one faculty never found.

## 10. What survived

Three measured gains outlived the audit, and they are the only three the harness claims.

1. Combining answers wins preference: 82% of decided pairs, holding under length matching and a second judge family.
2. Errors cannot spread where two specialists cover the same fact: 0 propagations out of 27 when a clean source exists.
3. Sending a disputed question back to a specialist resolves it: 100% with a scripted reply, 90% with a live one, versus 33% without.

## 11. The harness

Each component below exists because a specific experiment licensed it, and does only what that experiment showed. The full system diagram in the harness paper labels every connection with the number that justifies it.

**Seats are earned, not assigned by label.** Because fingerprints are per-model, no specialist is seated for being "the legal model." Every candidate passes a measured gate: it must produce real output rather than degenerate repetition (one archived fine-tune failed this 12 times out of 12), must differ measurably from its own base model, and must handle production-length prompts. A general model given a role prompt is a legitimate specialist if it passes, and most of the program ran on exactly that.

**Specialists work alone, for cost reasons only.** Each specialist gets its task and a one-line list of who else is on the panel, never the others' drafts. The original reason for this was fear of cross-contamination. That fear was tested and found groundless (see the next section). The rule stays because showing drafts costs about 10,000 characters of input and 14% longer output per specialist while changing nothing measurable.

**Redundancy is built in on purpose.** The planning layer identifies the quantities the answer depends on and assigns each to at least two specialists. This is where the council's error immunity comes from. It does not exist by default.

**Follow-ups are triggered by a required list, never by a model's self-assessment.** The writer works in two passes: first a mandatory list of tensions between the drafts (produced in 391 of 396 archived runs), then the synthesis. Software reads the list and dispatches follow-ups. A reply that adds nothing is flagged rather than silently delivered.

**Caution travels around the writer, not through it.** Specialists emit their caveats, assumptions, and confidence as structured fields. The harness carries those fields mechanically into an appendix of the final document. The writer never sees them and receives no instructions about being careful, because such instructions buy nothing and cost preference.

**Some numbers may never be optimized.** Trigger rates, hedge counts, phrase compliance, caution-survival rates, and preference scores on epistemic content are diagnostics only. Each one is on a written list, with the experiment that showed what optimizing it would manufacture.

## 12. Attacking the harness

Rules distilled from findings can still be wrong. Each load-bearing rule got its own experiment, with the failure condition written first.

**The seating gate predicts real defects. Kept.** Ten candidate models were gated, with verdicts committed before any of them ran in the pipeline. Both models that failed the gate then misbehaved in the pipeline (33% and 94% of their contributions). All eight that passed ran clean (0% to 6%). Two lessons rode along. Gate verdicts go stale: one model that passed an old screen failed a fresh one and then misbehaved, so seating must re-test rather than reuse a stored pass. And formatting failures are a separate matter: the legal fine-tune failed its formatting check outright and then contributed without a single defect.

**The planner works, link by link. Kept, with bounds.** The planning layer had never been exercised; every earlier redundancy result used assignments a human had planted. Three experiments closed the gap. The planner finds the load-bearing quantities 63% of the time, and it is best at exactly the right kind, the *missing* quantities nobody has measured (81%). Given a quantity, it assigns it to two specialists in 40 of 40 plans. Live specialists convey what they were briefed 85% to 95% of the time, and the writer then uses the clean source. A halted first attempt produced a useful side finding: a specialist only conveys a privately briefed fact if the fact is relevant to what it was asked (2 of 8 when it was not, 21 of 21 when it was). The honest end-to-end protection is therefore about 63% coverage multiplied by the selection effect, not a guarantee.

**The "drop empty replies" gate failed. Recorded as not deployable.** Two attempts, two failures on opposite halves of the problem. A judge-based gate let vacuous filler through (dropped 3 of 6). A stricter extract-and-verify gate caught the filler (6 of 6) but rejected 52% of real replies. Per the rule written in advance, there is no third attempt without purpose-built training data. Empty replies are flagged, never silently dropped. By contrast, the blocklist for invented citations works: 21 hits, 0 false alarms, 0 misses across 141 archived replies. The paper reports the failed gate beside the working one because refusing to hide the failure is the method.

**Redundancy is causal. Kept.** One change, assigning the disputed quantity to a second specialist, cut adoption of the wrong value from 90% to 45% and raised adoption of the right value from 0% to 50%. That 90% figure with no second source is the sharpest measurement on record of a writer that does not verify. Protection was all-or-nothing per item, and two guesses about what decides it were tested and both failed (a model's own plausibility rating; a stable, near-unanimous map of which specialist "owns" each quantity, which predicted at exactly coin-flip). The boundary is listed as open.

**The appendix carries caution, and readers use it. Kept.** The appendix delivered 100% of specialist caveats versus the 17% that survived through prose, with no detectable preference penalty. When a decision-relevant caveat rode in the appendix, a reader model changed its decision 73% of the time, versus 4% when the same appendix carried an irrelevant caveat, and about the same as when the caveat was woven into the prose. The items were balanced between caveats that should block a decision and caveats that should enable one, so generic timidity could not masquerade as reading. The channel the judge cannot see is not decoration. It changes outcomes.

**The live loop closes. Kept, with one halt.** Described in Section 7 above: 21 of 21 conveyed, 90% adopted versus 33%, one halt when the fact was left in the specialist's own draft, and a fabrication rate of 10% to 15% now bounded and filtered.

**Isolation lost its reason. Demoted.** Showing specialists each other's drafts, with everything else fixed, changed their off-field vocabulary by essentially nothing, against a pre-declared threshold of 5 to 8 percentage points. The contamination fear is withdrawn. If anything, specialists who saw their colleagues' coverage used slightly *fewer* off-field terms, which is noted as a possible mechanism and not claimed. The rule survives on cost alone.

**The ownership map died. Rejected.** A stable, near-unanimous self-report of which specialist owns each quantity, exactly the kind of thing a framework would ship as a routing table, predicted real behavior at coin-flip on fresh items. This rejection is reported alongside the successes on purpose. The difference between an evidence-bound system and a stack of prompts is that the system can lose arguments like this one on the record.

**The whole bundle costs nothing detectable. Kept.** With every component individually tested, the assembled harness was judged head-to-head against the original architecture on 108 pairs, both orders, two judge families. No difference could be found in either direction; large effects were ruled out both ways. The harness's preference standing comes from combining answers at all, which both systems do. Its additions (about five caveats per document, a follow-up round, restructured seating) cost nothing the judge can see. The appendix, considered alone, nudged slightly in the harness's favor.

## 13. Costs and open risks

**The trigger bounds coverage, but less than feared.** Everything downstream of the follow-up trigger is measured and works. On planted problems the trigger fired only 21% to 58% of the time, and it is deliberately never optimized, because pushing it up blindly manufactures the empty ritual the control experiment exposed. On real inquiries it fired 85% of the time.

**Open risks, stated.** Which items get protected and which do not is still unexplained after two failed guesses. Invented citations run at 10% to 15% of live replies, on one topic, with the same two fabrications recurring, and the specialist never admits the gap; the filter covers that topic and nothing else, so it is a floor on confabulation, not a ceiling. The preference cost of the appendix is bounded but not proven zero. And the council does not improve accuracy, because a single writer already scores 98% on well-specified problems; the paper calls this the strongest available statement of the rule that a council is not an accuracy device.

**Running the system re-runs the science.** The harness's telemetry, caution-survival rates, trigger rates, slots for phrase-swapping any proposed instruction, and preference-versus-correctness divergence wherever an answer is checkable, is the same battery the program used. A faithful deployment produces the external replication the papers say they need, at almost no extra cost.

## 14. Where the papers stop

Everything above was measured on 7- to 20-billion-parameter models running locally, on English-language business-advisory scenarios, with one primary writer family. Groups of 6 to 18 scenarios cap every result. Some comparisons use archived runs from earlier experiments under a declared freshness check rather than fresh reruns. Trigger rates vary by batch and are only ever quoted as a range. None of the findings should be stretched past those bounds, and the architecture document says, for every component, exactly which experiment licenses it.

## 15. The one-paragraph version

A council of AI experts was built on assumptions that nearly all failed when tested honestly. The failures were not dead ends; each one pointed at a real mechanism. The writer chooses sources rather than checking them, so protection comes from having two sources. Instructions to be careful buy words rather than behavior, and judges penalize the words, so caution has to travel in a channel the writer never touches. Models act well when told to and do not notice when they should, so the trigger has to come from a required artifact rather than from self-assessment. A system built from only those surviving parts was then attacked component by component, kept what held, demoted what did not, and turned out to cost nothing detectable to ship. The method, keeping only what survives a serious attempt to kill it and writing the deaths down next to the survivals, is the actual proposal.
