"""Golden test -- reproduce the reference system's published parameters.

An external replication should run this before trusting the kit on its own
data: it checks the install against a real 1,260-run ledger with known
answers, so a failure here means the kit is broken rather than the new
system being interesting.

Skipped automatically when the reference ledger is absent, which it will be
for anyone who installed the package alone.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from gst.adapters.coe import from_ledger
from gst.card import measure_all

LEDGER = Path(__file__).resolve().parents[2] / "bench" / "runs" / "imported"
pytestmark = pytest.mark.skipif(not LEDGER.is_dir(),
                                reason="reference ledger not present")


@pytest.fixture(scope="module")
def card():
    records = from_ledger(LEDGER)
    assert len(records) > 1000, f"expected >1000 usable runs, got {len(records)}"
    return measure_all(records, system="council-of-experts (reference)")


def test_shrinkage_matches_published_range(card):
    sh = card.shrinkage
    assert sh.identifiable
    # Published: w = 0.35, c = 0.54 over the full 1,260-run population.
    assert 0.30 <= sh.w <= 0.40, sh.w
    assert 0.45 <= sh.c <= 0.65, sh.c
    assert sh.prior_trust_ratio > 1.0          # prior outweighs evidence
    assert "SHRINKAGE" in sh.verdict


def test_supply_response_is_monotone(card):
    means = [m for _s, (m, _n) in sorted(card.shrinkage.strata.items())]
    assert means == sorted(means), means
    assert means[0] < 0.6 and means[-1] > 1.5   # compensating floor, compressed top


def test_strata_fit_is_tight_and_run_fit_is_not(card):
    """Both are reported on purpose: the law describes the conditional mean,
    not individual runs, and quoting only the strata R^2 would oversell it."""
    assert card.shrinkage.r2_strata > 0.9
    assert card.shrinkage.r2_runs < 0.5


def test_ceiling_artifact_is_labelled_not_reported_as_falsification(card):
    """The linearity probe fires here because the property class has only four
    families and supply reaches all four. The note must say so."""
    notes = " ".join(card.shrinkage.notes)
    if "quadratic" in notes:
        assert "ceiling" in notes and "bounded count" in notes


def test_high_dilution_detected(card):
    assert card.spans.f_median < 0.2
    assert card.spans.dilution_factor > 5


def test_poisson_check_agrees_with_empirical_clean_rate(card):
    cl = card.clean
    assert abs(cl.poisson_p0 - cl.p0_overall) < 0.05


def test_empirical_best_of_n_is_below_independence(card):
    """The measured curve must not beat the independence formula: redraws from
    one model on one task are positively correlated, so a curve above it would
    mean the estimator is pooling things that are not redraws."""
    cl = card.clean
    assert cl.bon_empirical, "reference ledger has repeated runs; curve expected"
    for n, v in cl.bon_empirical.items():
        if cl.bon_empirical_cells.get(n, 0) >= cl.bon_empirical_cells.get(1, 1) * 0.5:
            assert v <= cl.bon_independent[n] + 0.02, (n, v, cl.bon_independent[n])


def test_recommendations_are_actionable(card):
    recs = card.recommendations(can_train=True)
    assert any("best-of-n" in r for r in recs)
    assert any("minimal-pair" in r for r in recs)
    assert any("steering unavailable" in r for r in recs)   # scope boundary stated
