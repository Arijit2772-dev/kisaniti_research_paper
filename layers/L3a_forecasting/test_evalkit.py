"""Tests for evalkit.py on synthetic series with known answers. No price data is used except in the pair-count
check, which reads dates only."""

import csv
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evalkit as ek  # noqa: E402

D = date(2022, 9, 1)


def series(values, season="2022-23", start=D, step=1):
    return [ek.Obs(start + timedelta(days=i * step), season, float(v)) for i, v in enumerate(values)]


# ---- pairs ----
def test_eligibility_needs_ten_days_including_the_origin():
    s = series(range(30))
    raw = ek.raw_pairs(s, 7, "2022-23")
    elig = ek.eligible_pairs(s, 7, "2022-23")
    assert len(raw) == 23  # origins 0..22
    assert [o.day for o, _ in elig][0] == D + timedelta(days=9)  # the 10th index day is the first eligible origin
    assert len(elig) == 23 - 9


def test_pairs_use_exact_calendar_days_and_stay_in_one_season():
    a = series([1, 2, 3, 4, 5], season="2022-23")
    b = series([9, 9], season="2023-24", start=date(2023, 9, 1))
    assert ek.raw_pairs(a + b, 2, "2022-23") == [(a[0], a[2]), (a[1], a[3]), (a[2], a[4])]
    gap = [a[0], a[2]]  # day 1 missing: h=1 finds nothing, h=2 finds one pair; nothing is filled or matched nearby
    assert ek.raw_pairs(gap, 1, "2022-23") == [] and len(ek.raw_pairs(gap, 2, "2022-23")) == 1


# ---- models ----
def test_baselines_by_hand():
    s = series([10, 20, 30, 40, 50, 60, 70])
    assert ek.naive(s, D) == 70
    assert ek.moving_average5(s, D) == (30 + 40 + 50 + 60 + 70) / 5
    assert ek.moving_average5(s[:2], D) == 15  # fewer than five: all there are


def test_moving_average_ignores_the_previous_season():
    old = series([1000] * 5, season="2021-22", start=date(2021, 9, 1))
    new = series([10, 20], season="2022-23")
    assert ek.moving_average5(old + new, D) == 15


def test_seasonal_naive_median_in_a_three_day_window():
    prev = [ek.Obs(date(2021, 10, d), "2021-22", v) for d, v in [(8, 100.0), (9, 200.0), (10, 300.0), (11, 1000.0), (14, 5.0)]]
    cur = [ek.Obs(date(2022, 9, 20), "2022-23", 1.0)]
    # target 2022-10-10 -> centre 2021-10-10, window 7..13 -> 100, 200, 300, 1000 -> median 250 (14 Oct is out)
    assert ek.seasonal_naive(prev + cur, date(2022, 10, 10)) == 250.0
    assert ek.seasonal_naive(prev + cur, date(2022, 12, 25)) is None  # empty window
    assert ek.seasonal_naive(prev, date(2021, 10, 10)) is None  # first season has no previous one


def test_run_model_never_passes_the_future():
    s = series(range(30))
    seen = []

    def spy(history, target):
        seen.append((history[-1].day, max(o.day for o in history), target))
        return history[-1].value

    ek.run_model(s, spy, 3, "2022-23")
    # the series is daily and h = 3: the history must end exactly on the origin, three days before the target
    assert seen and all(last == mx and (target - last).days == 3 for last, mx, target in seen)


# ---- metrics ----
def test_metrics_by_hand():
    fs = [ek.Forecast(D, D, 100.0, 110.0, 120.0), ek.Forecast(D, D, 100.0, 90.0, 80.0), ek.Forecast(D, D, 100.0, 100.0, 100.0)]
    assert ek.mae(fs) == pytest.approx((10 + 10 + 0) / 3)
    assert ek.smape(fs) == pytest.approx((2 * 10 / 230 + 2 * 10 / 170 + 0) / 3)
    assert ek.direction_accuracy(fs) == pytest.approx(1.0)  # up/up, down/down, flat/flat
    assert ek.mase(fs, 5.0) == pytest.approx(ek.mae(fs) / 5.0)
    wrong = [ek.Forecast(D, D, 100.0, 110.0, 90.0)]
    assert ek.direction_accuracy(wrong) == 0.0


def test_mase_scale_uses_only_the_given_training_seasons():
    s = series([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], season="2021-22", start=date(2021, 9, 1)) + series(
        [0, 100, 0, 100, 0, 100, 0, 100, 0, 100, 0, 100, 0], season="2022-23"
    )
    assert ek.mase_scale(s, 1, ["2021-22"]) == pytest.approx(1.0)
    assert ek.mase_scale(s, 1, ["2022-23"]) == pytest.approx(100.0)
    with pytest.raises(ValueError):
        ek.mase_scale(s, 1, ["2020-21"])


# ---- ranges ----
def test_conformal_rank_and_refusal():
    r = list(range(1, 20))  # n = 19
    assert ek.conformal_halfwidth(r, 0.80) == 16  # ceil(20 * 0.8) = 16th smallest
    assert ek.conformal_halfwidth(r, 0.95) == 19  # ceil(20 * 0.95) = 19
    assert ek.conformal_halfwidth(list(range(1, 10)), 0.95) is None  # k = 10 > 9: no honest interval


def test_conformal_coverage_on_exchangeable_data():
    rng = np.random.default_rng(1)
    hit = []
    for _ in range(300):
        cal = np.abs(rng.normal(size=99))
        w = ek.conformal_halfwidth(cal, 0.80)
        hit.extend(np.abs(rng.normal(size=20)) <= w)
    assert 0.78 <= np.mean(hit) <= 0.83  # theory: 80% (to 100/(n+1)); loose bounds for the simulation


def test_interval_stats_and_pinball_by_hand():
    fs = [ek.Forecast(D, D, 0.0, 10.0, 12.0), ek.Forecast(D, D, 0.0, 10.0, 25.0)]
    st = ek.interval_stats(fs, 5.0, 0.80)  # intervals [5, 15]: first covered, second not
    assert st["coverage"] == 0.5 and st["mean_width"] == 10.0
    # tau = 0.1: lower bound 5: y=12 -> d=7 -> 0.7 ; y=25 -> d=20 -> 2.0 ; upper bound 15 at 0.9: d=-3 -> 0.3 ; d=10 -> 9.0
    assert st["pinball"] == pytest.approx(((0.7 + 2.0) / 2 + (0.3 + 9.0) / 2) / 2)


# ---- inference ----
def test_dm_h1_equals_the_formula_written_out():
    rng = np.random.default_rng(3)
    e1, e2 = rng.normal(size=40), rng.normal(size=40) * 1.5
    d = np.abs(e1) - np.abs(e2)
    n = len(d)
    stat = d.mean() / math.sqrt(np.mean((d - d.mean()) ** 2) / n) * math.sqrt((n - 1) / n)
    got_stat, got_p = ek.dm_test(e1, e2, 1)
    assert got_stat == pytest.approx(stat)
    assert got_p == pytest.approx(2 * stats.t.sf(abs(stat), n - 1))


def test_dm_longer_lag_uses_bartlett_weights():
    rng = np.random.default_rng(4)
    e1, e2 = rng.normal(size=60), rng.normal(size=60)
    d = np.abs(e1) - np.abs(e2)
    n, h = len(d), 3
    dc = d - d.mean()
    g = [np.sum(dc[k:] * dc[: n - k]) / n for k in range(h)]
    lrv = g[0] + 2 * (1 - 1 / 3) * g[1] + 2 * (1 - 2 / 3) * g[2]
    stat = d.mean() / math.sqrt(lrv / n) * math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    assert ek.dm_test(e1, e2, h)[0] == pytest.approx(stat)


def test_dm_sign_symmetry_identical_models_and_size():
    rng = np.random.default_rng(5)
    good, bad = rng.normal(size=80) * 1.0, rng.normal(size=80) * 3.0
    s_gb, p_gb = ek.dm_test(good, bad, 2)
    s_bg, p_bg = ek.dm_test(bad, good, 2)
    assert s_gb < 0 < s_bg and p_gb == pytest.approx(p_bg) and p_gb < 0.001
    assert ek.dm_test(good, good, 2) == (0.0, 1.0)
    with pytest.raises(ValueError):
        ek.dm_test([1, 2, 3, 4], [1, 2, 3, 5], 2)


def test_dm_rejects_about_five_percent_under_the_null():
    rng = np.random.default_rng(6)
    rej = sum(ek.dm_test(rng.normal(size=60), rng.normal(size=60), 1)[1] < 0.05 for _ in range(1000))
    assert 25 <= rej <= 80  # 5% of 1000 = 50; loose bounds


def test_holm_known_example_and_monotonicity():
    assert ek.holm_adjust([0.01, 0.04, 0.03, 0.005]) == pytest.approx([0.03, 0.06, 0.06, 0.02])
    assert ek.holm_adjust([0.9, 0.8]) == pytest.approx([1.0, 1.0])  # 0.8 x 2 = 1.6 capped at 1; 0.9 x 1 < 1.0
    assert ek.holm_adjust([0.6]) == [0.6]
    assert all(a <= 1 for a in ek.holm_adjust([0.5, 0.7, 0.99]))


def test_block_bootstrap_degenerate_and_clear_cases():
    rng = np.random.default_rng(7)
    e = rng.normal(size=50)
    assert ek.block_bootstrap_relative_change(e, e, 3, draws=200) == (0.0, 0.0)
    lo, hi = ek.block_bootstrap_relative_change(e * 0.5, e, 3, draws=500)
    assert lo == pytest.approx(-0.5) and hi == pytest.approx(-0.5)  # exactly half the error everywhere
    b1 = ek.block_bootstrap_relative_change(e * 0.8, e, 4, draws=300, seed=9)
    assert b1 == ek.block_bootstrap_relative_change(e * 0.8, e, 4, draws=300, seed=9)  # the seed fixes the result


def test_beats_naive_needs_all_three_conditions():
    assert ek.beats_naive(0.01, (-0.3, -0.1), -0.2, 0.12)
    assert not ek.beats_naive(0.06, (-0.3, -0.1), -0.2, 0.12)  # Holm p too large
    assert not ek.beats_naive(0.01, (-0.3, 0.02), -0.2, 0.12)  # interval reaches zero
    assert not ek.beats_naive(0.01, (-0.3, -0.1), -0.05, 0.12)  # gain smaller than the detectable gain
    assert not ek.beats_naive(0.01, (0.1, 0.3), 0.2, 0.12)  # worse than naive


# ---- the whole path on synthetic seasons ----
def _walk(seed, n=70, season="2022-23", start=D):
    rng = np.random.default_rng(seed)
    v = 3000 + np.cumsum(rng.normal(0, 40, n))
    return series(v, season=season, start=start)


def test_oracle_beats_naive_and_moving_average_does_not_on_a_random_walk():
    s = _walk(11)
    truth = {o.day: o.value for o in s}

    def oracle(history, target):  # sees the future: only to prove the pipeline can detect a better model
        return truth[target] + 1.0

    better = ek.compare_to_naive(s, oracle, 7, "2022-23", draws=500)
    assert better["p_raw"] < 0.001 and better["ci"][1] < 0 and better["relative_change"] < -0.9
    assert ek.beats_naive(better["p_raw"], better["ci"], better["relative_change"], 0.15)
    ma = ek.compare_to_naive(s, ek.moving_average5, 7, "2022-23", draws=500)
    assert ma["relative_change"] > 0  # averaging old values is worse than the last value on a random walk
    assert not ek.beats_naive(ma["p_raw"], ma["ci"], ma["relative_change"], 0.15)


def test_compare_uses_only_pairs_where_both_models_forecast():
    prev = _walk(12, season="2021-22", start=date(2021, 9, 1))
    cur = _walk(13)
    res = ek.compare_to_naive(prev + cur, ek.seasonal_naive, 7, "2022-23", draws=200)
    assert res["pairs"] == len(ek.eligible_pairs(cur, 7, "2022-23"))
    assert ek.run_model(prev, ek.seasonal_naive, 7, "2021-22") == []  # the first season has no seasonal forecast


# ---- agreement with the pair counts already filed for the protocol (dates only, no prices) ----
INDEX = Path(__file__).resolve().parents[2] / "data" / "processed" / "basmati" / "index_dated_only.csv"
COUNTS = Path(__file__).resolve().parents[2] / "results" / "C0_protocol" / "horizon_pairs.csv"


@pytest.mark.skipif(not (INDEX.exists() and COUNTS.exists()), reason="processed index not present (git-ignored)")
def test_raw_pair_counts_equal_the_filed_counts():
    with open(INDEX, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f)]
    with open(COUNTS, newline="", encoding="utf-8") as f:
        filed = [r for r in csv.DictReader(f) if r["variant"] == "dated_only"]
    checked = 0
    for r in filed:
        s = [ek.Obs(date.fromisoformat(x["date"]), x["season"], 0.0) for x in rows if x["variety"] == r["variety"]]
        for season in ("2021-22", "2022-23", "2023-24", "2024-25", "2025-26", "2026-27"):
            assert len(ek.raw_pairs(s, int(r["horizon_days"]), season)) == int(r[season]), (r["variety"], r["horizon_days"], season)
            checked += 1
    assert checked == len(filed) * 6 and checked > 100
