"""Known-answer checks for the few-cluster helpers."""
from __future__ import annotations

import math

import pytest

from gst.smallcluster import (cluster_boot, holm, kappa, paired_diffs, prf,
                              sign_flip_p, t_interval)


def test_sign_flip_all_positive_is_two_over_two_to_the_k():
    assert sign_flip_p([1, 1, 1, 1, 1]) == pytest.approx(2 / 32)
    assert sign_flip_p([0.2] * 8) == pytest.approx(2 / 256)


def test_sign_flip_zero_differences_carry_no_evidence():
    # three clusters with no change do not make the result more extreme
    assert sign_flip_p([1, 1, 0.8, 0.2, 1, 0, 0, 0]) == pytest.approx(2 / 32)


def test_sign_flip_balanced_is_one():
    assert sign_flip_p([1, -1, 1, -1]) == pytest.approx(1.0)


def test_t_interval_known_sample():
    m, lo, hi = t_interval([1.0, 2.0, 3.0, 4.0, 5.0])
    assert m == pytest.approx(3.0)
    half = 2.776 * math.sqrt(2.5) / math.sqrt(5)
    assert lo == pytest.approx(3.0 - half) and hi == pytest.approx(3.0 + half)


def test_kappa_perfect_and_independent():
    assert kappa([(True, True)] * 5 + [(False, False)] * 5)["kappa"] == pytest.approx(1.0)
    # 25/25/25/25 table: agreement equals chance
    k = kappa([(True, True)] * 25 + [(True, False)] * 25 + [(False, True)] * 25 + [(False, False)] * 25)
    assert k["raw"] == pytest.approx(0.5) and k["kappa"] == pytest.approx(0.0)
    assert k["overlap"] == pytest.approx(25 / 75)


def test_kappa_high_raw_agreement_can_be_near_chance():
    # the pattern found in the board review: 91% raw agreement, rare positives
    pairs = [(False, False)] * 900 + [(True, False)] * 60 + [(False, True)] * 30 + [(True, True)] * 10
    k = kappa(pairs)
    assert k["raw"] == pytest.approx(0.91)
    assert k["kappa"] < 0.2


def test_prf():
    r = prf([True, True, False, False], [True, False, True, False])
    assert r["precision"] == pytest.approx(0.5) and r["recall"] == pytest.approx(0.5)


def test_holm_is_monotone_and_bounded():
    adj = holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj["a"] == pytest.approx(0.03)
    assert adj["c"] == pytest.approx(0.06)
    assert adj["b"] == pytest.approx(0.06)


def test_cluster_boot_resamples_clusters():
    clusters = {i: [float(i)] for i in range(10)}
    lo, hi = cluster_boot(clusters, lambda s: sum(v for c in s for v in c) / len(s), draws=2000)
    assert lo < 4.5 < hi


def test_paired_diffs_needs_both_arms():
    rows = [{"item": 1, "arm": "x", "v": 1}, {"item": 1, "arm": "y", "v": 0},
            {"item": 2, "arm": "x", "v": 1}]
    ids, d = paired_diffs(rows, "item", "arm", "x", "y", lambda r: r["v"])
    assert ids == [1] and d == [1.0]
