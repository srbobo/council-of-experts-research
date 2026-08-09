"""Tests for the estimators.

The synthetic tests build run sets with a KNOWN (w, c) and check the kit
recovers it. That matters more than it sounds: an estimator that produces
plausible numbers on real data without ever being checked against a known
answer is how a measurement program convinces itself of things.
"""
from __future__ import annotations

import math

import pytest

from gst import RunRecord, clean_rate, measure_all, partition, shrinkage, span_fraction
from gst.corpus import ablate, build_corpus, decorrelation_report, supply_variants
from gst.instruments import ConsensusInstrument, RegexInstrument
from gst.measure import blindspot
from gst.pairs import diagnose
from gst.select import select, strip_annotation

MARKERS = {
    "cutoff": "This may be stale after my training cutoff.",
    "modeled": "We assume the baseline holds.",
    "jurisd": "Each jurisdiction differs on this point.",
    "hedging": "Downstream results may vary with the inputs.",
}
FILLER = ("The report describes the situation in detail. "
          "It reviews the relevant background and lists the findings. ")


def _text(families, pad=6):
    return " ".join(MARKERS[f] for f in families) + " " + FILLER * pad


def _rec(i, up_fams, out_fams, prompt_id=None, condition="c", writer="w"):
    return RunRecord(run_id=str(i), prompt_id=prompt_id or f"p{i}",
                     upstream=[_text(up_fams, 3)], output=_text(out_fams),
                     condition=condition, writer_id=writer)


class TestInstruments:
    def test_regex_detects_each_family(self):
        ins = RegexInstrument()
        for fam, sent in MARKERS.items():
            assert fam in ins.families(sent), fam

    def test_filler_is_clean(self):
        assert RegexInstrument().families(FILLER * 6) == set()

    def test_consensus_requires_two(self):
        with pytest.raises(ValueError):
            ConsensusInstrument([RegexInstrument()])

    def test_consensus_needs_agreement(self):
        a = RegexInstrument({"x": [r"alpha"]}, name="a")
        b = RegexInstrument({"x": [r"beta"]}, name="b")
        con = ConsensusInstrument([a, b], k=2)
        assert con.families("alpha only") == set()
        assert con.families("alpha and beta") == {"x"}


class TestShrinkage:
    def test_recovers_known_parameters(self):
        """y = 0.5*s + 1 by construction; the fit must find it."""
        fams = ["cutoff", "modeled", "jurisd", "hedging"]
        recs = []
        i = 0
        for s in range(5):
            y = int(round(0.5 * s + 1))
            for _ in range(30):
                recs.append(_rec(i, fams[:s], fams[:y]))
                i += 1
        r = shrinkage(recs)
        assert r.identifiable
        assert abs(r.w - 0.5) < 0.12, r.w
        assert abs(r.c - 1.0) < 0.25, r.c

    def test_faithful_transduction_verdict(self):
        fams = ["cutoff", "modeled", "jurisd", "hedging"]
        recs = [_rec(i * 5 + s, fams[:s], fams[:s])
                for s in range(5) for i in range(20)]
        r = shrinkage(recs)
        assert r.w > 0.85 and r.c < 0.15
        assert "FAITHFUL" in r.verdict

    def test_refuses_when_supply_never_varies(self):
        recs = [_rec(i, ["cutoff"], ["cutoff"]) for i in range(50)]
        r = shrinkage(recs)
        assert not r.identifiable
        assert "supply levels" in r.notes[0]
        assert math.isnan(r.w)

    def test_extrapolated_intercept_is_flagged(self):
        """No runs at zero supply means c is a projection, not a measurement.

        Found by running the kit across 27 arms of the originating
        architecture: 21 reported a prior fill from data whose lowest supply
        level was 1 or 2, and several came back NEGATIVE -- impossible for a
        count, and proof the number was extrapolated.
        """
        fams = ["cutoff", "modeled", "jurisd", "hedging"]
        recs = [_rec(i * 5 + s, fams[:s], fams[:s])
                for s in range(2, 5) for i in range(20)]      # never s=0
        r = shrinkage(recs)
        assert r.identifiable and r.c_extrapolated
        assert "EXTRAPOLATED" in r.verdict
        assert any("EXTRAPOLATED" in n for n in r.notes)

    def test_measured_intercept_is_not_flagged(self):
        fams = ["cutoff", "modeled", "jurisd", "hedging"]
        recs = [_rec(i * 5 + s, fams[:s], fams[:s])
                for s in range(5) for i in range(20)]
        assert not shrinkage(recs).c_extrapolated

    def test_wide_interval_refuses_ranking(self):
        """A wide interval is not a weak result; it is an absent one."""
        fams = ["cutoff", "modeled", "jurisd", "hedging"]
        recs = []
        for i, s in enumerate([0, 1, 2, 3, 4] * 3):
            y = 4 if i % 2 else 0                    # pure noise, no relationship
            recs.append(_rec(i, fams[:s], fams[:y]))
        r = shrinkage(recs)
        assert r.weakly_identified
        assert "WEAKLY IDENTIFIED" in r.verdict

    def test_prior_trust_ratio(self):
        fams = ["cutoff", "modeled", "jurisd", "hedging"]
        recs = [_rec(i * 5 + s, fams[:s], fams[:int(round(0.5 * s + 1))])
                for s in range(5) for i in range(30)]
        r = shrinkage(recs)
        assert r.prior_trust_ratio == pytest.approx((1 - r.w) / r.w)


class TestSpans:
    def test_high_dilution_flagged(self):
        recs = [_rec(i, ["cutoff"], ["cutoff"]) for i in range(20)]
        r = span_fraction(recs)
        assert 0 < r.f_median < 0.5
        assert "DILUTION" in r.verdict
        assert r.dilution_factor > 2

    def test_property_free_output_is_zero(self):
        recs = [RunRecord(run_id=str(i), prompt_id=f"p{i}",
                          upstream=[_text(["cutoff"])], output=FILLER * 8)
                for i in range(10)]
        assert span_fraction(recs).f_median == 0.0


class TestCleanRate:
    def test_invention_lowers_p0(self):
        recs = ([_rec(i, [], ["cutoff"]) for i in range(10)]            # invented
                + [_rec(100 + i, ["cutoff"], ["cutoff"]) for i in range(10)])
        r = clean_rate(recs)
        assert r.p0_by_supply[0][0] == 0.0
        assert r.p0_by_supply[1][0] == 1.0

    def test_empirical_curve_needs_repeats(self):
        recs = [_rec(i, [], ["cutoff"]) for i in range(12)]   # all unique prompt_ids
        r = clean_rate(recs)
        assert r.bon_empirical == {}
        assert any("independence curve" in n for n in r.notes)

    def test_correlated_redraws_are_detected(self):
        """One task is always unclean, another always clean. Independence says
        best-of-2 fixes half of it; the empirical curve must say it does not."""
        recs = []
        for k in range(6):
            recs.append(_rec(k, [], ["cutoff"], prompt_id="bad"))
        for k in range(6):
            recs.append(_rec(100 + k, [], [], prompt_id="good"))
        r = clean_rate(recs)
        assert r.bon_empirical[2] == pytest.approx(0.5, abs=0.01)
        assert r.bon_independent[2] > r.bon_empirical[2]
        assert any("positively correlated" in n for n in r.notes)

    def test_cell_keys_separate_conditions(self):
        """Runs of one task under two different arms are not redraws.

        Arm A is always unclean, arm B always clean. Pooling them under the
        task id would let a draw from A be 'rescued' by a draw from B, giving
        1 - C(4,2)/C(8,2) = 0.786 for best-of-2 -- selection credited for a
        configuration change. Separated, each arm is measured on its own and
        the honest pooled figure is (0 + 1)/2 = 0.5.
        """
        recs = ([_rec(i, [], ["cutoff"], prompt_id="t", condition="A") for i in range(4)]
                + [_rec(50 + i, [], [], prompt_id="t", condition="B") for i in range(4)])
        r = clean_rate(recs)
        assert r.bon_empirical[2] == pytest.approx(0.5, abs=0.01)
        assert r.bon_empirical[2] < 0.7           # not the 0.786 of pooled arms


class TestBlindspot:
    def test_miss_rates_and_joint(self):
        loose = RegexInstrument({"x": [r"alpha"]}, name="loose")
        tight = RegexInstrument({"x": [r"alpha beta gamma"]}, name="tight")
        probes = [("alpha beta gamma", {"x"}), ("alpha only", {"x"})]
        r = blindspot(probes, [loose, tight])
        assert r.per_instrument["loose"] == 0.0
        assert r.per_instrument["tight"] == 0.5
        assert r.joint_independent == 0.0

    def test_near_duplicate_instruments_warned(self):
        a = RegexInstrument({"x": [r"alpha"]}, name="a")
        b = RegexInstrument({"x": [r"alpha"]}, name="b")
        r = blindspot([("alpha", {"x"}), ("beta", {"x"})], [a, b])
        assert any("near-duplicate" in n for n in r.notes)


class TestSelect:
    def test_rejects_feedback_shaped_generator(self):
        with pytest.raises(TypeError, match="no required arguments"):
            select(lambda draft: draft, ["up"], n=2)

    def test_picks_the_clean_candidate(self):
        cands = iter([_text(["cutoff", "modeled"]), _text(["cutoff"])])
        res = select(lambda: next(cands), [_text(["cutoff"])], n=2)
        assert res.chosen_index == 1
        assert res.clean and not res.annotated

    def test_annotates_when_nothing_is_clean(self):
        res = select(lambda: _text(["cutoff"]), [FILLER * 6], n=2)
        assert res.annotated and not res.clean
        assert "not traceable" in res.chosen

    def test_annotation_round_trips(self):
        body = _text(["cutoff"])
        res = select(lambda: body, [FILLER * 6], n=1)
        assert strip_annotation(res.chosen) == body


class TestCorpus:
    def test_ablate_removes_only_targeted_family(self):
        t = _text(["cutoff", "modeled"])
        out = ablate(t, remove={"cutoff"})
        ins = RegexInstrument()
        assert "cutoff" not in ins.families(out)
        assert "modeled" in ins.families(out)

    def test_variants_span_the_supply_range(self):
        got = supply_variants([_text(["cutoff", "modeled", "jurisd"])])
        assert sorted(s for s, _, _ in got) == [0, 1, 2, 3]

    def test_decorrelation_detects_balance(self):
        recs = [_rec(i, ["cutoff", "modeled", "jurisd"], ["cutoff"],
                     prompt_id=f"task{i}") for i in range(12)]
        rep = decorrelation_report(build_corpus(recs))
        assert rep.balanced, rep.notes
        assert rep.normalized_mi < 0.15
        assert any("below the >=1000 scale" in n for n in rep.notes)


class TestPairs:
    def _item(self, families):
        from gst.corpus import CounterfactualItem
        return CounterfactualItem(prompt_id="p", supply=len(families),
                                  upstream=[_text(families)],
                                  target_families=set(families))

    def test_drop_pair_removes_one_sourced_family(self):
        from gst.pairs import make_drop_pair
        ref = _text(["cutoff", "modeled"])
        pairs = make_drop_pair(ref, self._item(["cutoff", "modeled"]))
        assert {p.family for p in pairs} == {"cutoff", "modeled"}
        for p in pairs:
            assert p.family not in RegexInstrument().families(p.rejected)
            assert p.chosen == ref
        assert diagnose([(p.chosen, p.rejected) for p in pairs]).minimal

    def test_invention_pair_adds_an_unsourced_family(self):
        from gst.pairs import make_invention_pair
        ref = _text(["cutoff"])
        pairs = make_invention_pair(ref, self._item(["cutoff"]),
                                    {"hedging": MARKERS["hedging"]})
        assert len(pairs) == 1 and pairs[0].family == "hedging"
        assert "hedging" in RegexInstrument().families(pairs[0].rejected)
        assert "hedging" not in RegexInstrument().families(pairs[0].chosen)

    def test_invention_pair_skips_sourced_families(self):
        """A family the upstream raised is preservation, not invention."""
        from gst.pairs import make_invention_pair
        pairs = make_invention_pair(_text(["cutoff"]), self._item(["cutoff"]),
                                    {"cutoff": MARKERS["cutoff"]})
        assert pairs == []

    def test_diagnosis_matches_the_loss_mask_definition(self):
        """Deleting one whole property-bearing sentence must read as minimal.

        If `diagnose_pair` measured bare marker spans while `char_mask` masked
        whole sentences, this pair would report ~90% off-feature and send the
        user to fix pair construction that was already correct.
        """
        from gst.pairs import char_mask, make_drop_pair
        ref = _text(["cutoff", "modeled"])
        p = make_drop_pair(ref, self._item(["cutoff", "modeled"]))[0]
        d, off, _ = __import__("gst.pairs", fromlist=["x"]).diagnose_pair(
            p.chosen, p.rejected)
        assert off == 0.0, off
        assert char_mask(ref) and len(char_mask(ref)[0]) == 2

    def test_minimal_pair_is_recognized(self):
        chosen = _text(["cutoff"])
        rejected = chosen.replace(MARKERS["cutoff"], "").strip()
        d = diagnose([(chosen, rejected)])
        assert d.minimal, d.off_feature_frac

    def test_diluted_pair_is_flagged(self):
        chosen = _text(["cutoff"])
        rejected = MARKERS["cutoff"] + " Wholly different prose follows here. " + \
            "It shares no wording with the other completion whatsoever. " * 8
        d = diagnose([(chosen, rejected)])
        assert not d.minimal
        assert d.off_feature_frac > 0.5


class TestRecordHygiene:
    def test_short_output_is_dropped_not_scored(self):
        recs = [RunRecord(run_id="1", prompt_id="p", upstream=["x " * 200],
                          output="too short")]
        keep, dropped = partition(recs)
        assert keep == [] and sum(dropped.values()) == 1

    def test_card_reports_missing_blindspot(self):
        fams = ["cutoff", "modeled", "jurisd", "hedging"]
        recs = [_rec(i * 5 + s, fams[:s], fams[:s]) for s in range(5) for i in range(6)]
        card = measure_all(recs, system="synthetic")
        assert any("two-instrument" in n for n in card.notes)
        assert "synthetic" in card.render()


class TestCompare:
    def test_ranking_requires_an_interval(self):
        """4 events against 7 at n=45 is not a difference."""
        from gst.compare import compare_arm
        a = [_rec(i, [], ["cutoff"] if i < 4 else []) for i in range(45)]
        b = [_rec(100 + i, [], ["cutoff"] if i < 7 else []) for i in range(45)]
        d = compare_arm(a, b)
        assert d.lam < d.lam_baseline          # point estimate "wins"
        assert not d.distinguishable           # interval says otherwise
        assert "not distinguishable" in d.verdict

    def test_real_difference_is_detected(self):
        from gst.compare import compare_arm
        a = [_rec(i, [], []) for i in range(45)]
        b = [_rec(100 + i, [], ["cutoff"]) for i in range(45)]
        d = compare_arm(a, b)
        assert d.distinguishable and d.diff_ci[1] < 0

    def test_instrument_relative_improvement_is_named(self):
        """An arm that improves only under the instrument it was tuned against
        has changed wording, not behavior."""
        from gst.compare import compare_two_instrument
        sees = RegexInstrument({"cutoff": [r"training cutoff"]}, name="tuned")
        blind = RegexInstrument({"cutoff": [r"NEVER_MATCHES_ANYTHING"]}, name="indep")
        a = [_rec(i, [], []) for i in range(45)]
        b = [_rec(100 + i, [], ["cutoff"]) for i in range(45)]
        r = compare_two_instrument(a, b, sees, blind)
        assert "INSTRUMENT-RELATIVE" in r.verdict

    def test_mismatched_case_batteries_are_caught(self):
        from gst.compare import check_comparable, restrict_to_shared
        arms = {"x": [_rec(i, [], [], prompt_id=f"c{i}") for i in range(5)],
                "y": [_rec(50 + i, [], [], prompt_id=f"c{i}") for i in range(3)]}
        rep = check_comparable(arms)
        assert not rep.comparable
        assert any("no other arm ran" in n for n in rep.notes)
        assert all(len(v) == 3 for v in restrict_to_shared(arms).values())


class TestScaffoldEntanglement:
    def test_detects_patterns_that_appear_in_prompts(self):
        """The check that would have caught finding #8 a month earlier."""
        from gst.instruments import audit_scaffold_overlap
        ins = RegexInstrument({"x": [r"modeled at", r"hypothetical"]})
        prompt = "Your synthesis MUST label it as an assumption (use 'modeled at')."
        r = audit_scaffold_overlap(ins, prompt)
        assert r["x"]["dictated"] == [r"modeled at"]
        assert r["x"]["clean"] == [r"hypothetical"]

    def test_clean_lexicon_reports_no_overlap(self):
        from gst.instruments import audit_scaffold_overlap
        ins = RegexInstrument({"x": [r"hypothetical"]})
        r = audit_scaffold_overlap(ins, "Analyze the financial aspects.")
        assert r["x"]["dictated"] == []
