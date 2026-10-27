"""run_stage on synthetic series with known answers; no real price is used."""

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evalkit as ek  # noqa: E402
import run_protocol as rp  # noqa: E402


def walk(seed, season, start, n=70):
    rng = np.random.default_rng(seed)
    v = 3000 + np.cumsum(rng.normal(0, 40, n))
    return [ek.Obs(start + timedelta(days=i), season, float(x)) for i, x in enumerate(v)]


def world():
    s = []
    for i, season in enumerate(["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]):
        s += walk(10 + i, season, date(2021 + i, 9, 1))
    return {"1121": s}


def test_validation_uses_only_the_validation_season_and_reports_every_model():
    res = rp.run_stage(world(), "validation", ["naive", "ma5", "seasonal_naive"], [1, 7], rp.BASELINES)
    assert {r["season"] for r in res["forecasts"]} == {"2024-25"}
    assert {(r["model"], r["horizon"]) for r in res["metrics"]} == {(m, h) for m in ("naive", "ma5", "seasonal_naive") for h in (1, 7)}
    assert res["inference"] == []  # inference exists only for the test stage


def test_forecasts_never_use_the_future():
    res = rp.run_stage(world(), "validation", ["naive"], [7], rp.BASELINES)
    for r in res["forecasts"]:
        assert date.fromisoformat(r["origin"]) < date.fromisoformat(r["target"]) and r["forecast"] == r["origin_value"]


def test_test_stage_adds_holm_adjusted_inference_against_naive_only():
    oracle_truth = {o.day: o.value for o in world()["1121"]}
    models = {**rp.BASELINES, "oracle": lambda history, target: oracle_truth[target] + 1.0}
    res = rp.run_stage(world(), "test", ["naive", "ma5", "oracle"], [1, 7, 14, 28], models, {"1121": {"1": 0.1, "7": 0.1, "14": 0.1}}, draws=300)
    rows = res["inference"]
    assert {(r["model"], r["horizon"]) for r in rows} == {(m, h) for m in ("ma5", "oracle") for h in (1, 7, 14)}  # primary horizons, no naive
    assert all(r["p_holm"] >= r["p_raw"] for r in rows)
    assert {r["verdict"] for r in rows if r["model"] == "oracle"} == {"BETTER"}
    assert {r["verdict"] for r in rows if r["model"] == "ma5"} == {"NO_DETECTABLE_DIFFERENCE"}


def test_without_a_stated_smallest_gain_no_model_is_called_better():
    models = {**rp.BASELINES, "oracle": lambda history, target: {o.day: o.value for o in world()["1121"]}[target]}
    res = rp.run_stage(world(), "test", ["naive", "oracle"], [1], models, None, draws=200)
    assert {r["verdict"] for r in res["inference"]} == {"NO_THRESHOLD"}


def test_the_real_runner_refuses_today_because_the_protocol_is_not_frozen(capsys):
    import pytest

    if any(x.startswith("C.0 freeze") for x in rp.git("log", "--format=%s").splitlines()):
        pytest.skip("the protocol has been frozen: this check applied only before the freeze")
    sys.argv = ["run_protocol.py", "--stage", "validation"]
    assert rp.main() == 2
    assert "REFUSED" in capsys.readouterr().err


def test_worker_processes_give_the_same_rows_as_one_process():
    one = rp.run_stage(world(), "validation", ["naive", "ma5"], [1, 7], rp.registry(), workers=1)
    two = rp.run_stage(world(), "validation", ["naive", "ma5"], [1, 7], None, workers=2)
    key = lambda r: (r["variety"], r["horizon"], r["model"], r["origin"])  # noqa: E731
    assert sorted(one["forecasts"], key=key) == sorted(two["forecasts"], key=key)


def test_chosen_variants_and_conformal_ranges_in_the_test_stage():
    chosen = {"lightgbm": {"1121": {"1": "ma5"}}}  # any runnable name stands in for a tuned variant
    models = {**rp.BASELINES, "lightgbm": rp.BASELINES["naive"]}
    cal = {("1121", 1, "naive"): [10.0 + i for i in range(40)]}
    res = rp.run_stage(world(), "test", ["naive", "lightgbm"], [1], models, {"1121": {"1": 0.1}}, draws=100, chosen=chosen, calibration=cal)
    assert {m["config"] for m in res["metrics"] if m["model"] == "lightgbm"} == {"ma5"}  # the chosen variant ran under the family name
    conf = [r for r in res["ranges"] if r["range_method"] == "conformal"]
    assert {(r["model"], r["level"]) for r in conf} == {("naive", 80), ("naive", 95)}
    assert all(r["claim_allowed"] for r in conf) and all(0 <= r["coverage"] <= 1 for r in conf)
