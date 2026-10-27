"""Models 4 to 8 on synthetic series: sensible output, ordered ranges, and above all no look-ahead: changing the series
after an origin must not change the forecast made at that origin."""

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evalkit as ek  # noqa: E402
import models_extra as me  # noqa: E402


def walk(seed, season, start, n=60):
    rng = np.random.default_rng(seed)
    v = 3000 + np.cumsum(rng.normal(0, 40, n))
    return [ek.Obs(start + timedelta(days=i), season, float(x), 5 + i % 4, 100.0 + (i % 7)) for i, x in enumerate(v)]


def world(seed=0):
    out = []
    for i, season in enumerate(["2021-22", "2022-23", "2023-24", "2024-25"]):
        out += walk(seed + i, season, date(2021 + i, 9, 1))
    return out


FAST = {
    "ets": me.MODELS["ets"],
    "arima": me.MODELS["arima"],
    "lightgbm": me._make_lgbm(7, 50, with_ranges=True),
    "gru": me._make_gru(8, 10),
    "chronos2": me.chronos2,
}


@pytest.mark.parametrize("name", list(FAST))
def test_forecasts_are_finite_plausible_and_ranges_are_ordered(name):
    fs = ek.run_model(world(), FAST[name], 7, "2024-25")
    assert len(fs) > 20, "the model produced (almost) no forecasts"
    for f in fs:
        assert np.isfinite(f.forecast) and 1500 < f.forecast < 4500
        if f.ranges:
            (l80, h80), (l95, h95) = f.ranges[80], f.ranges[95]
            assert l95 <= l80 <= f.forecast <= h80 <= h95


@pytest.mark.parametrize("name", list(FAST))
def test_no_look_ahead_changing_the_future_changes_nothing_before_it(name):
    a = world()
    cut = date(2024, 10, 20)
    b = [o if o.day <= cut else ek.Obs(o.day, o.season, o.value + 500.0, o.n_mandis, o.iqr) for o in a]
    fa = {(f.origin, f.target): f.forecast for f in ek.run_model(a, FAST[name], 7, "2024-25") if f.origin <= cut}
    fb = {(f.origin, f.target): f.forecast for f in ek.run_model(b, FAST[name], 7, "2024-25") if f.origin <= cut}
    assert fa and fa == fb


def test_training_pairs_never_include_a_target_after_the_origin():
    hist = [o for o in world() if o.day <= date(2024, 10, 25)]
    origin = hist[-1].day
    x, y = me._pairs(hist, 7)
    assert len(y) > 50
    # every target value used must be an index value observed on or before the origin
    seen = {o.value for o in hist}
    assert all(v in seen for v in y)
    last_season_targets = [o for o in hist if o.season == hist[-1].season and o.day + timedelta(days=7) <= origin]
    assert len(last_season_targets) > 0


def test_lag_one_is_the_origin_value():
    hist = world()[:70]
    obs = [o for o in hist if o.season == hist[-1].season]
    f = me._features(obs, len(obs) - 1)
    assert f[0] == obs[-1].value and f[1] == obs[-2].value and f[4] == obs[-7].value
