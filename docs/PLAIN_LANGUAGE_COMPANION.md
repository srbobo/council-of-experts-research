# The Council That Mostly Didn't Work

## A plain-language companion to the two papers

This document walks through the same ground as the project's paper (now one combined draft, *Hardening Mixture-of-Agents*, which merged an audit paper and a harness paper), in the order the paper uses, but without the scientific vocabulary. Where the paper gives a statistic, this document gives the number and says what it means. Nothing here is a new claim.

> **Corrected on 1 October 2026.** A review of the whole project found that several numbers in the paper and in this companion were wrong or overstated. One came from a scoring bug. Others were ranges that were too narrow for so few scenarios, or shares that counted only part of the data. One claim was withdrawn. The passages below now give the corrected versions, each marked "Corrected". Three limits apply throughout and were understated before: in most experiments the three specialists were the editor model itself, given three one-sentence roles. Every judge and reader was a small AI model. And no person labeled a sentence, judged an answer or read a report. Six new experiments are running to test the parts that could not be fixed by recomputing (Cells 62 to 67). The review is in `docs/BOARD_REVIEW_2026-10-01.md`.

A reading note on the numbers. Almost every result in the program is a proportion: how often something happened out of how many tries. When the papers write a value like 0.818 with a bracket after it, the bracket is the range the true value could plausibly sit in given how few cases there were. The plain-language version here says things like "about 82%, and plausibly anywhere from 72% to 92%." When the range includes 50% for a head-to-head comparison, or includes zero for a difference, the reading is "too close to call." Since October 2026 the ranges are computed over scenarios or questions, not individual runs, which makes them wider than the ones first published.

---

# Part One: The Audit

## 1. The idea being tested

There is a popular recipe for getting better answers out of AI language models. Instead of asking one model a question, ask several, then hand all of their answers to one more model and tell it to combine the best of what it received. The published version of this recipe is called Mixture-of-Agents, and it reports beating GPT-4o on a standard leaderboard.

The recipe comes with a story about why it works. Models are supposed to be "collaborative": shown other models' answers, they produce better ones, even when some of those answers are weak. The combining model is imagined as something like a careful editor who reads every draft, checks the claims, weighs the agreement between drafts, and writes something better than any of them.

The recipe's headline numbers come from one kind of measurement: another AI is shown two answers and asked which one it prefers. (Corrected: we first wrote that every published number is of this kind and that nobody had checked accuracy or the spread of errors. That was wrong. The original paper reports accuracy on a math test in an appendix, a follow-up paper reports accuracy on three tests, and another group measured the damage one deceptive model does to the recipe.) What we set out to check was narrower: at small scale, whether an error in one draft spreads into the final answer, whether the preferring AI can be trusted on this task, and whether an instruction to the editor changes what it does or only what it says.

This program built the recipe at a small enough scale to check all of that. The models were open ones running on a single machine, between 7 and 20 billion parameters, small enough that every run could be saved, re-read, and re-scored. Three "specialists" (healthcare, legal, and finance) each answered a business-advisory question, and one editor model combined their answers. In the early experiments the specialists were separately fine-tuned models. In most of the later ones, including every test of the rebuilt system, they were the editor model itself given three one-sentence roles. That makes our pipeline a much smaller thing than the published recipe, which uses six different large models. Eighteen advisory scenarios were used throughout.

## 2. Calling the shot before running

The program had one rule that shaped everything: before any experiment ran, a written registration stated what was predicted, what result would count as the prediction failing, and, from existing data, how often the thing being measured could even occur. That last item matters more than it sounds. If you predict "the editor will use the specialist's warning," but specialists only issue warnings one time in ten, the experiment cannot tell you much no matter how it comes out. Each plan was written before its result, and the project history shows that. (Corrected: we first said the order of plan and runs was provable. The saved run files were added to the history weeks later and carry no timestamps, so it is not. Runs since October 2026 record their own time and settings.)

Results were entered into a running ledger that marks each claim as live, provisional, withdrawn, or blocked. Three separate reviews went back over the ledger and downgraded earlier findings that did not hold up. A fourth and broader review in October 2026 corrected several of the numbers below.

## 3. Checking the measuring instruments first

Before trusting any finding about the models, the program checked the tools used to measure them. Fourteen problems were found and recorded, and the October 2026 review added six more. Four of them shape everything downstream.

**Counting your own words.** Suppose you tell the editor "when a number is an estimate, say it is *modeled at* rather than stating it flatly." Then you check how often the editor's output contains the words "modeled at." You will find it does, and you will be tempted to conclude the editor has become careful about estimates. But you dictated those words. What you measured is obedience, not carefulness. The program found this confusion in its own earlier work: an instruction moved the dictated wording from 0 out of 30 outputs to 28 out of 30, while other ways of saying the same thing barely moved (1 out of 30 to 4 out of 30). The instruction was buying the phrase.

**A registry of dictated phrases.** To stop this from happening again, the program extracted every phrase that any prompt put into a model's mouth (125 phrases from 35 prompts), froze the list, and refused to run any experiment whose prompts contained a phrase the measuring tool would then count. On its first use, the registry caught that an earlier preference-judging prompt in the program listed the very same seven phrases the writing prompts dictated. The tool for judging outputs had been told to look for the words the outputs had been told to use. The program also checked whether these phrases ever appear on their own, without being dictated: across 2,907 passages and 60 runs with all instructions stripped, they never did. That is what makes the registry trustworthy as a detector of scaffolding rather than of natural writing.

**A judge that names no phrases.** To score whether an output actually expresses uncertainty, the program used two AI judges reading sentence by sentence, with definitions that describe the behavior without naming any wording and that explicitly tell the judge not to reward particular phrasing. The two judges agreed 91% of the time across more than 15,000 decisions. (Corrected: that figure flatters the tool. Most sentences carry no caveat, so two judges answering independently would agree 88% of the time by luck. Beyond luck, their agreement is weak. They also found only two thirds of the sentences containing "modeled at" and one third of those containing "taken to be". No label has ever been compared with a person's. Cell 62 makes that comparison, and until it reports, every count of caveats below is provisional.) An earlier approach that had the judges read whole documents at once agreed only 62% of the time and was thrown out.

**Preference judges mostly pick whichever answer they read first.** When an AI is shown two answers and asked which is better, it picks the first one 85% to 88% of the time. This was true for the four small local judges we tried. Published work finds the size of this bias varies from judge to judge, so we no longer call it a property of the task. The only fix is to show every pair in both orders and count a result only when the judge picks the same answer both times. Doing that turns 60% to 95% of comparisons into ties. Our first analysis counted only those pairs, which made preferences look larger than they are. (Corrected: we now count every pair, with a pair the judge splits by position as half a win for each side.)

## 4. The phrase-swap experiment

This is the experiment that gives the audit paper its title.

**What was done.** The editor was run three ways on the same eighteen scenarios, seven times each, for 378 runs. One version had a plain prompt. The other two had the same prompt plus one sentence: "When you state a number that is an estimate rather than an established fact, label it using the phrase 'modeled at'." The third version was identical except the phrase was "taken to be." The first phrase had been used in the program's prompts for months. The second was invented the day before and had never appeared anywhere in the program's two million characters of archived output.

**What happened to the phrases.** Each instructed version produced its own phrase in about two thirds of outputs (67% and 70%). The plain version never produced either. No run ever produced the other version's phrase. The months-old house phrase and the day-old invented one performed identically. Whatever the instruction did, it did not draw on any learned habit around the familiar words.

**What happened to the behavior.** The two sentence-level judges then scored how often each output expressed that a number was an estimate *using any wording other than the dictated phrase*. The plain version did this in 34% of runs. The two instructed versions did it in 37% and 32%. Those differences are well inside the noise. Outputs were the same length across all three versions, so the instructed editor was not simply saying less.

**What it means.** The instruction produced the words it asked for and nothing else measurable. The editor did not become more careful about estimates; it learned which two words to insert. The experiment can rule out any hidden behavioral effect larger than about 22 percentage points; it cannot rule out something smaller. (Corrected: the two judges that did this scoring miss many such sentences, so a change expressed in new wording could also have gone unseen.)

## 5. The preference experiment

**What was done.** Three head-to-head comparisons on the same scenarios, with every pair judged in both orders and counted only if the judge agreed with itself.

First, the full recipe (three specialists plus editor) against the same editor answering the question directly with no specialists. Second and third, each phrase-instructed version of the editor against the plain version. Because the phrase-swap experiment had already established that those versions differ only in the phrase, any preference difference is caused by the phrase.

**The recipe wins.** Out of 44 pairs where the judge picked the same winner in both orders, the full recipe won 82%. (Corrected: counting all 126 pairs, with split pairs as half, the recipe scored 61%, still a clear preference.) The two sides produced answers of nearly the same length (a 1.4% difference), so this is not the judge rewarding longer answers. The winner did not consistently use more business frameworks either. What the judge is responding to remains unidentified. One limit we did not state before: the recipe costs four model calls against one, and we did not test the obvious alternative of asking the single model four times and combining its answers.

**The phrase loses.** Against the plain version, the "modeled at" editor won only 26% of the pairs the judge decided consistently and the "taken to be" editor 32%. (Corrected: counting all pairs, the scores were 41% and 44%. The first is a clear difference from an even split. The second falls just short of one.) The program had predicted the opposite, that a judge would reward the careful-sounding wording.

**A second judge from a different family agrees.** All 378 pairs were re-judged by a 30-billion-parameter model from a different vendor, chosen from three candidates by a script that looked only at whether the model could do the task, never at which side it favored. (Corrected: counting all pairs, this judge scored the recipe 58%, a clear preference. It scored both phrase versions 45%, a clear difference for "taken to be" and too close to call for "modeled at".) Published studies have found the same thing with much larger judges: AI judges mark down text that expresses uncertainty.

**Putting the two experiments together.** An instruction to be careful about estimates installs only a phrase. A preference judge penalizes that phrase. So any system that is tuned toward what the judge prefers, which is how most AI systems are improved today, will strip out the phrase and leave the underlying carefulness exactly where it was, which is to say unchanged, because the instruction never touched it. The two standard tools pull in opposite directions on the same wording, and neither reaches the thing they are both supposed to be about. This holds for two small local judges, and no person judged any pair.

## 6. Does the editor do what the story says it does?

The recipe's story credits the editor with several abilities. Each was tested.

**Does the editor check facts?** Arithmetic claims were planted in the specialists' drafts, some correct and some deliberately wrong. When every specialist had the wrong number, it reached the final answer 5 times out of 27, and 12 times out of 27 when the specialists' working was also removed. (Corrected: we first also reported that with one wrong and one right source the wrong number got through 0 times out of 27, and read that as protection. In those runs 23 of 27 answers stated neither number, and some planted numbers contradicted the scenario's own text, which the editor used instead. That count shows nothing either way.) What the later experiments show is that the editor picks between sources. They do not yet show whether it catches an error it could check, because the planted numbers could not be checked. Cell 63 tests that.

**Does agreement between specialists count for anything?** (Withdrawn in October 2026.) We first reported that claims made by two or more specialists reached the final answer no more often than claims made by one (49% against 52%), and concluded the editor ignores agreement. That rested on one of four kinds of caveat, counted with a keyword counter, in runs whose prompts told the editor which phrase to use. The other three kinds showed large gains when specialists agreed. The question is open.

**How much of the specialists' caution survives?** The specialists' drafts were scored for how many sentences expressed uncertainty, and the editor's output was scored the same way. We first reported that the editor passed along between 11% and 33% of what it was given, and that two thirds to nine tenths of the caution was lost. (Corrected: the editor's answer is only 18% to 30% as long as the drafts it read, and caveat sentences make up about the same share of the answer as of the drafts, 19% against 18% in one set of scenarios and 10% against 13% in the other. So the figure mostly says that a summary is shorter than its sources. For the second editor model the result was too close to call. Whether caveats are dropped more than other content is being tested in Cell 66.) The editor also adds caution of its own about a third of the time when given drafts that contain none, a count that depends on the judges now under check.

**Are specialists actually different from each other?** Two medical fine-tunes of the same base model were compared with their base. One used noticeably more medical frameworks than the base. For the other the result was too close to call. (Corrected: we first said the two disagree and that fine-tuning leaves a fingerprint per model. Their plausible ranges overlap almost entirely, so the data cannot show that they differ.) The practical point stands on other evidence: a published study found that medical fine-tunes beat their base model in only about one comparison in eight, so a label is no guarantee.

**Is the combined answer more correct?** On a 60-question test with checkable answers, the recipe and the bare editor scored the same, both between 92% and 97%. Two further tests were built to be harder (36 multi-step calculations and 30 rule-interaction problems with scripted answers), and the bare editor scored 98% on both. There is no room for the recipe to improve on a score that high, so the question was declared untestable at this scale. A committee cannot add accuracy where one member already has the answer.

## 7. The one thing that worked: sending the question back

**The design.** The editor's prompt already required it to list, before writing, the points where the specialists' drafts were in tension. Instead of asking the editor to decide whether it needed help, a separate piece of software read that list and sent a follow-up question to the relevant specialist. Six scenarios were built where the deciding fact was withheld from the specialists' first drafts. Three versions were run: no follow-up; a follow-up reply that sounded responsive but contained no deciding fact; and a reply that contained it.

**The result.** When the editor had named the disagreement and the reply contained the fact, the editor resolved the question the way the fact implied 7 times out of 7. With no follow-up it did so in 5 of 15 such runs, and with the empty-sounding reply in 3 of 15. (Corrected: those counts cover only runs where the editor named the disagreement, which happened in 7, 15 and 15 of 36 runs. Over all 36 runs per version the counts were 15, 10 and 8. No question went the other way, but with six questions the difference is too close to call.)

This fits the rest. The editor picks between sources, and a follow-up reply puts a new source at exactly the disputed point.

**The catch.** The loop only runs if the editor names the tension in the first place, and on these planted problems it did so only 34% of the time. A companion experiment gave specialists the option to raise their hand and defer to a colleague. When they raised it, they pointed at the right colleague 10 times out of 11. They raised it in 31% of runs when the question lay outside their field and 8% when it lay inside. (Corrected: we first said "about as often". The difference points the expected way but was too close to call on six questions, and the rate is too low to rely on.)

**Closing the loop with a real specialist.** The results above used scripted replies. Two more experiments used a live specialist model. The first put the deciding fact in the specialist's own first draft, and the editor named the tension only 21% of the time, so that experiment stopped at its pre-declared checkpoint. The second gave the specialist the fact as private notes it had not written down, closer to how a real expert holds knowledge. The live specialist conveyed the fact in all 21 follow-ups, and the editor took the intended side in 19 of those 21 runs. (Corrected: we first compared this with the 33% from the earlier no-follow-up runs. Those were made six days before and the two batches differ, so we no longer state the size of the gain. The specialist was also handed the fact, so this shows the route works, not that a specialist finds the fact.) One risk appeared: in 4 of the 21 replies, the specialist dressed the correct fact up with invented case law or regulatory rulings, and the editor accepted those too. A follow-up experiment measured this at 10% to 15% of replies, concentrated on one topic, with the same two invented citations recurring, which is what makes a blocklist filter possible.

**On real problems, the catch is smaller.** When the assembled system was later run on 54 natural inquiries rather than planted ones, the follow-up fired on 85% of them. Real specialists disagree often. The scarce-trigger problem is the floor, not the forecast.

## 8. What the audit means

The recipe's headline is not overturned. Combining several drafts produced something two small AI judges prefer, at this scale, against a single answer of equal length. What we cannot say is why, or whether it would beat the same model asked four times. Instructions for caution produce phrases, and the judges mark the phrases down. With two sources the editor picks one.

Two practical implications follow. First, any system improved by preference training will quietly lose whatever visible caution its instructions installed, so caution that must survive has to live somewhere the judge never sees, in a structured field or a separate section rather than in the prose. Second, at this scale roughly five sixths of a raw "which is better" verdict is reading order, so with judges like these, an evaluation that shows pairs in one order only is mostly measuring position.

---

# Part Two: The Harness

## 9. The plan, and what happened to it

The system that was going to be built was ordinary for its moment: three domain specialists, one lead writer, and a set of assumptions that seemed too obvious to test. Specialists know things generalists do not. Telling the writer to preserve uncertainty makes it careful. A model that is out of its depth can say so. When specialists agree, that agreement means something.

Nine such assumptions were written down and tested one at a time. Here is the scorecard in plain words.

| The council needed this to be true | What was done | What happened |
|---|---|---|
| Specialists trained on the same field share a way of thinking | Compared two medical fine-tunes of one base model | **Not shown either way.** One differed from its base. The other was too close to call, and their ranges overlap. |
| An instruction to be careful changes the writer's behavior | Swapped the instructed phrase for a synonym | **False.** The named phrase appears; nothing else changes. |
| Careful marking is at worst neutral to a judge | Judged instructed versions against plain, both orders | **Backwards.** The phrase loses, and a second judge family agrees. |
| A specialist can tell when a question is outside its field | Gave specialists a way to defer | **Too close to call.** They deferred in 31% of runs outside their field and 8% inside, on six questions. When they deferred, they named the right colleague. |
| Agreement between specialists strengthens a claim | Re-scored saved runs with a keyword counter | **Withdrawn.** One kind of caveat showed no effect and three showed large gains. No checked way to measure it yet. |
| The writer checks the specialists' facts | Planted numbers that could not be checked | **Not yet tested fairly.** With two sources the writer picks one. A test where checking is possible is running (Cell 63). |
| The council gives more correct answers | Three tests with checkable answers | **Cannot be tested.** The single writer already scores 92% to 98%; there is no room to improve. |
| The writer's prose carries the specialists' caution | Counted caution sentences in and out | **Shortened in proportion.** The answer is about 30% as long as the drafts and carries about the same share of caveat sentences. Whether caveats are lost more than other content is being tested (Cell 66). |
| What a model says about its own confidence predicts what it does | Asked models to rate their own plausibility and ownership | **Too close to call, twice.** Both tests were too small to settle it. |

Three of these failures turned out to be the foundation for what came next.

**Obedience is not behavior.** The instruction reliably bought its own phrase and nothing else. Every "be careful" line in a system prompt is, on this evidence, buying words.

**The writer is a chooser.** Given two sources for a figure, it states one of them, about evenly, and does not tell the reader that two existed. Whether it would catch an error it could check is still being tested. Either way, you can control which sources exist.

**The bottleneck is noticing, not acting.** In every consultation design, the mechanism worked when it fired and fired rarely. The writer used a follow-up 7 times out of 7 but asked for one only a third of the time. Specialists pointed correctly when they deferred but deferred rarely. Our tests of whether a model knows when it needs help were each too small to settle the question.

## 10. What survived

Three measured results outlived the audit, and they are the only three the harness rests on. Each is given as corrected in October 2026.

1. Two small AI judges prefer the combined answer: 61% and 58% counting every pair. It costs four model calls against one.
2. A second source changes which figure the editor repeats: the planted figure appeared in 45% of answers against 90% with one source. The editor picks one and does not show both.
3. A follow-up reply that holds the deciding fact is used: 7 of 7 runs where the editor had named the disagreement, and 15 of 36 runs overall against 10 of 36 with no follow-up.

## 11. The harness

Each component below exists because a specific experiment licensed it, and does only what that experiment showed. The full system diagram in the harness paper labels every connection with the number that justifies it.

**Seats are earned, not assigned by label.** Because fingerprints are per-model, no specialist is seated for being "the legal model." Every candidate passes a measured gate: it must produce real output rather than degenerate repetition (one archived fine-tune failed this 12 times out of 12), must differ measurably from its own base model, and must handle production-length prompts. A general model given a role prompt is a legitimate specialist if it passes, and most of the program ran on exactly that.

**Specialists work alone, for cost reasons only.** Each specialist gets its task and a one-line list of who else is on the panel, never the others' drafts. The original reason for this was fear of cross-contamination. That fear was tested and found groundless (see the next section). The rule stays because showing drafts costs about 10,000 characters of input and 14% longer output per specialist while changing nothing measurable.

**Redundancy is built in on purpose.** The planning layer identifies the quantities the answer depends on and assigns each to at least two specialists. This gives the editor a second source for each figure. It does not make the system immune to errors, since the editor picks between sources about evenly. What it does create is a disagreement that the next two steps can pick up.

**Follow-ups are triggered by a required list, never by a model's self-assessment.** The writer works in two passes: first a mandatory list of tensions between the drafts (produced in 391 of 396 archived runs), then the synthesis. Software reads the list and dispatches follow-ups. A reply that adds nothing is flagged rather than silently delivered.

**Caution travels around the writer, not through it.** Specialists emit their caveats, assumptions, and confidence as structured fields. The harness carries those fields mechanically into an appendix of the final document. (As built so far, the specialists write ordinary prose and AI judges pull out about five caveats per report. The structured version is the design, not yet the system.) The writer never sees them and receives no instructions about being careful, because such instructions buy nothing and cost preference.

**Some numbers may never be optimized.** Trigger rates, hedge counts, phrase compliance, caution-survival rates, and preference scores on epistemic content are diagnostics only. Each one is on a written list, with the experiment that showed what optimizing it would manufacture.

## 12. Attacking the harness

Rules distilled from findings can still be wrong. Each load-bearing rule got its own experiment, with the failure condition written first.

**The screening test flags models that answer too briefly. Kept, with a narrower reading.** Ten candidate models were screened, with results saved before any of them ran in the pipeline. The two that failed were the two with the most broken answers in the pipeline (33% and 94% of their contributions). All eight that passed ran clean (0% to 6%). Picking those two by luck would happen about 1 time in 45. (Corrected: the screening test and the outcome both measure the same thing, very short answers, on different prompts. And in tests of the rebuilt system one model plays every specialist.) Screening results also go stale: one model that passed an old screen failed a fresh one and then misbehaved.

**The planner works, link by link. Kept, with bounds.** The planning layer had never been exercised; every earlier redundancy result used assignments a human had planted. Three experiments closed the gap. The planner finds the load-bearing quantities 63% of the time, and it is best at exactly the right kind, the *missing* quantities nobody has measured (81%). Given a quantity, it assigns it to two specialists in 40 of 40 plans. Live specialists convey what they were briefed 85% to 95% of the time, and the writer then uses the second specialist's figure in about half of runs (whether the planted figure appears less often was too close to call in the live test). A halted first attempt produced a useful side finding: a specialist only conveys a privately briefed fact if the fact is relevant to what it was asked (2 of 8 when it was not, 21 of 21 when it was). So a second source can only be arranged for the 63% of figures the planner finds, and it is not a guarantee for those.

**The "drop empty replies" gate failed. Recorded as not deployable.** Two attempts, two failures on opposite halves of the problem. A judge-based gate let vacuous filler through (dropped 3 of 6). A stricter extract-and-verify gate caught the filler (6 of 6) but rejected 52% of real replies. Per the rule written in advance, there is no third attempt without purpose-built training data. Empty replies are flagged, never silently dropped. By contrast, the blocklist for invented citations caught all 21 known cases with no false alarms across 141 saved replies. (Corrected: its three names came from those same replies, so this shows the filter runs as written, not how it does on new replies.)

**A second source changes the answer about half the time. Kept, with a different reading.** One change, giving the figure to a second specialist with a different value, cut how often the planted value appeared from 90% to 45% of answers, and the second value appeared in 50%. (Corrected: we first called this halving the spread of errors and said the 90% showed a writer that does not verify. The planted value could not be checked against the scenario, and the question asked for it, so repeating it was following the request. The drop is a clear difference over 8 questions. The rise in the second value falls just short of one.) The result was all-or-nothing per item, and two guesses about what decides it were tested and both were too close to call.

**The appendix holds the caveats, and a reader model uses it. Kept, with limits.** The appendix holds 100% of the specialists' caveats because it is built from them. (Corrected: we first said 17% survived in the editor's prose. That number came from a scoring bug. The editor repeats 3% of caveat sentences word for word, and that says nothing about caveats it restates in its own words.) No preference penalty for the appendix was detected. When a deciding caveat sat in the appendix, a reader model changed its decision 73% of the time, against 4% for an irrelevant caveat. The items were balanced between caveats that should block a decision and caveats that should allow one. Limits: the reader was an AI model that had been told to use anything attached, and the appendix held a single sentence. Cell 64 tests other readers and longer appendices.

**The live loop closes. Kept, with one halt.** Described in Section 7 above: 21 of 21 conveyed, the fact used in 19 of 21 runs (the comparison with 33% came from another day and is no longer quoted), one halt when the fact was left in the specialist's own draft, and a fabrication rate of 10% to 15% now bounded and filtered.

**Isolation lost its reason. Demoted.** Showing specialists each other's drafts, with everything else fixed, changed their off-field vocabulary by essentially nothing, against a pre-declared threshold of 5 to 8 percentage points. The contamination fear is withdrawn. If anything, specialists who saw their colleagues' coverage used slightly *fewer* off-field terms, which is noted as a possible mechanism and not claimed. The rule survives on cost alone.

**The ownership map died. Rejected.** A stable, near-unanimous self-report of which specialist owns each quantity, exactly the kind of thing a framework would ship as a routing table, predicted real behavior no better than a coin flip on 28 fresh runs, a test too small to settle the question. The idea was dropped for lack of support.

**No preference difference from the original design was found.** With every part tested, the assembled harness was judged head-to-head against the original design on 108 pairs, both orders, two judge families. Counting every pair, it scored 53% and 48%, both too close to call. (Corrected: we first said large differences were ruled out both ways and that the additions cost nothing. The second judge's results cannot rule out a large loss, and we set no margin in advance for calling the two equal. The harness also takes about 14 model calls per question against 4.)

## 13. Costs and open risks

**The trigger bounds coverage, but less than feared.** Everything downstream of the follow-up trigger is measured and works. On planted problems the trigger fired only 21% to 58% of the time, and it is deliberately never optimized, because pushing it up blindly manufactures the empty ritual the control experiment exposed. On real inquiries it fired 85% of the time.

**Open risks, stated.** Which figures a second source changes and which it does not is still unexplained after two failed guesses. Invented citations run at 10% to 15% of live replies, on one topic, with the same two fabrications recurring, and the specialist never admits the gap; the filter covers that topic and nothing else, so it is a floor on confabulation, not a ceiling. The preference cost of the appendix is bounded but not proven zero. And the council does not improve accuracy, because a single writer already scores 98% on well-specified problems; the paper calls this the strongest available statement of the rule that a council is not an accuracy device.

**Running the system re-runs the science.** The harness's telemetry, caution-survival rates, trigger rates, slots for phrase-swapping any proposed instruction, and preference-versus-correctness divergence wherever an answer is checkable, is the same battery the program used. A faithful deployment produces the external replication the papers say they need, at almost no extra cost.

## 14. Where the papers stop

Everything above was measured on 7- to 30-billion-parameter models running locally, on English-language business-advisory scenarios, with one primary writer family. In most experiments the specialists were the writer model in three roles. Every judge and reader was an AI model, and no person labeled, judged or read anything. Groups of 6 to 18 scenarios cap every result. Some comparisons used saved runs from earlier experiments, which we no longer treat as a fair comparison for the size of an effect. None of the findings should be stretched past those bounds.

## 15. The one-paragraph version

A council of AI experts was built on assumptions that mostly failed or could not be confirmed when tested. Three things held up, in narrower form than we first reported. Two small AI judges prefer an answer combined from several drafts, though at four times the cost and without a test against asking one model four times. An instruction to be careful produces the phrase it names, and those judges mark the phrase down. And with two sources for a figure the writer picks one, so a second source changes the answer about half the time without the reader being told. A system rebuilt around those results showed no preference difference from the original and has not yet been tested on anything else. A review in October 2026 corrected the numbers, and six experiments now running test the parts that recomputing could not fix: whether the caveat scoring agrees with a person, whether the writer catches an error it could check, and whether caveats are lost more than other content.
