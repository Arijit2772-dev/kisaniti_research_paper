"""Evaluation kit for the pre-registered forecasting protocol (C.0, layers/L3a_forecasting/PREREGISTERED_PROTOCOL.md).

This file holds only the machinery: rolling-origin pairs, the three baseline models, the metrics, split-conformal
ranges, the Diebold-Mariano test with the Harvey-Leybourne-Newbold correction and a Newey-West variance, Holm's
correction, a moving-block bootstrap and the three-part rule for "better than naive" (section 8). It is tested on
synthetic series with known answers (test_evalkit.py). **No model has been run on the price index with it**: the
protocol is a draft until the owner approves it and the hand check has fixed the primary index variant.

Where the protocol text leaves a choice open, the choice made here is listed in EVALKIT_ASSUMPTIONS.md and must be
confirmed by the owner before the protocol is frozen.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
from scipy import stats

MIN_SEASON_DAYS = 10  # section 3: an origin is eligible after 10 index days of the current season exist


@dataclass(frozen=True)
class Obs:
    day: date
    season: str
    value: float


Model = Callable[[Sequence[Obs], date], "float | None"]  # (history up to the origin, target day) -> forecast


# ---- pairs --------------------------------------------------------------------------------------------------------
def raw_pairs(series: Sequence[Obs], h: int, season: str) -> list[tuple[Obs, Obs]]:
    """(origin, target) pairs of one season: an index value on the origin day and on exactly origin + h days.
    This is what count_horizon_pairs.py counts (no eligibility rule)."""
    days = {o.day: o for o in series if o.season == season}
    return [(o, days[o.day + timedelta(days=h)]) for o in sorted(days.values(), key=lambda x: x.day) if o.day + timedelta(days=h) in days]


def eligible_pairs(series: Sequence[Obs], h: int, season: str) -> list[tuple[Obs, Obs]]:
    """raw_pairs restricted to origins with at least MIN_SEASON_DAYS index days of the season up to and including
    the origin."""
    in_season = sorted(o.day for o in series if o.season == season)
    return [(o, t) for o, t in raw_pairs(series, h, season) if sum(1 for d in in_season if d <= o.day) >= MIN_SEASON_DAYS]


# ---- the three baseline models (the others live elsewhere) -------------------------------------------------------
def _same_season(history: Sequence[Obs]) -> list[Obs]:
    return [o for o in history if o.season == history[-1].season]


def naive(history: Sequence[Obs], target: date) -> float:
    return history[-1].value


def moving_average5(history: Sequence[Obs], target: date) -> float:
    last = _same_season(history)[-5:]
    return sum(o.value for o in last) / len(last)


def _one_year_earlier(d: date) -> date:
    try:
        return d.replace(year=d.year - 1)
    except ValueError:  # 29 February
        return d.replace(year=d.year - 1, day=28)


def seasonal_naive(history: Sequence[Obs], target: date) -> float | None:
    """Median of the previous season's index values within +-3 days of the target's calendar day one year earlier;
    None when the previous season or the window is empty (2021-22 has no previous season)."""
    seasons = sorted({o.season for o in history})
    i = seasons.index(history[-1].season)
    if i == 0:
        return None
    centre = _one_year_earlier(target)
    vals = [o.value for o in history if o.season == seasons[i - 1] and abs((o.day - centre).days) <= 3]
    return float(np.median(vals)) if vals else None


# ---- forecasts over pairs ----------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Forecast:
    origin: date
    target: date
    origin_value: float
    forecast: float
    actual: float

    @property
    def error(self) -> float:
        return self.forecast - self.actual


def run_model(series: Sequence[Obs], model: Model, h: int, season: str) -> list[Forecast]:
    ordered = sorted(series, key=lambda o: o.day)
    out: list[Forecast] = []
    for origin, target in eligible_pairs(ordered, h, season):
        history = [o for o in ordered if o.day <= origin.day]  # nothing after the origin is ever passed in
        f = model(history, target.day)
        if f is not None:
            out.append(Forecast(origin.day, target.day, origin.value, float(f), target.value))
    return out


# ---- metrics -----------------------------------------------------------------------------------------------------
def mae(fs: Sequence[Forecast]) -> float:
    return float(np.mean([abs(f.error) for f in fs]))


def smape(fs: Sequence[Forecast]) -> float:
    return float(np.mean([2 * abs(f.error) / (abs(f.forecast) + abs(f.actual)) for f in fs]))


def direction_accuracy(fs: Sequence[Forecast]) -> float:
    """Share of pairs where forecast and actual move the same way (up, down, flat) relative to the origin value."""
    return float(np.mean([np.sign(f.forecast - f.origin_value) == np.sign(f.actual - f.origin_value) for f in fs]))


def mase_scale(series: Sequence[Obs], h: int, training_seasons: Sequence[str]) -> float:
    """In-sample h-step naive MAE over the eligible pairs of the training seasons."""
    errs = [abs(t.value - o.value) for s in training_seasons for o, t in eligible_pairs(series, h, s)]
    if not errs:
        raise ValueError("no training pairs for the MASE scale")
    return float(np.mean(errs))


def mase(fs: Sequence[Forecast], scale: float) -> float:
    return mae(fs) / scale


# ---- ranges -----------------------------------------------------------------------------------------------------
def conformal_halfwidth(abs_residuals: Sequence[float], coverage: float) -> float | None:
    """Split conformal: the ceil((n + 1) * coverage)-th smallest absolute residual; None if n is too small."""
    n = len(abs_residuals)
    k = math.ceil((n + 1) * coverage)
    return None if k > n else float(sorted(abs_residuals)[k - 1])


def interval_stats(fs: Sequence[Forecast], halfwidth: float, coverage: float) -> dict[str, float]:
    lo = np.array([f.forecast - halfwidth for f in fs])
    hi = np.array([f.forecast + halfwidth for f in fs])
    y = np.array([f.actual for f in fs])
    tau = (1 - coverage) / 2
    return {
        "coverage": float(np.mean((y >= lo) & (y <= hi))),
        "mean_width": 2 * halfwidth,
        "pinball": float((pinball(y, lo, tau) + pinball(y, hi, 1 - tau)) / 2),
    }


def pinball(y: np.ndarray, q: np.ndarray, tau: float) -> float:
    d = y - q
    return float(np.mean(np.maximum(tau * d, (tau - 1) * d)))


# ---- inference --------------------------------------------------------------------------------------------------
def dm_test(err_model: Sequence[float], err_naive: Sequence[float], h: int) -> tuple[float, float]:
    """Diebold-Mariano on absolute-error loss with the Harvey-Leybourne-Newbold correction, a Newey-West (Bartlett)
    variance with lag h - 1 and the t(n - 1) distribution; two-sided. d = |e_model| - |e_naive|, so a negative
    statistic means the model is better. Returns (statistic, p)."""
    d = np.abs(np.asarray(err_model, float)) - np.abs(np.asarray(err_naive, float))
    n = len(d)
    if n <= 2 * h:
        raise ValueError("too few pairs for the HLN correction")
    dc = d - d.mean()
    lrv = float(np.dot(dc, dc) / n)
    for k in range(1, h):
        lrv += 2 * (1 - k / h) * float(np.dot(dc[k:], dc[:-k]) / n)
    if lrv <= 0:
        return (0.0, 1.0) if d.mean() == 0 else (math.copysign(math.inf, d.mean()), 0.0)
    dm = d.mean() / math.sqrt(lrv / n)
    stat = dm * math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    return float(stat), float(2 * stats.t.sf(abs(stat), n - 1))


def holm_adjust(pvalues: Sequence[float]) -> list[float]:
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adj[i] = running
    return adj


def block_bootstrap_relative_change(
    err_model: Sequence[float], err_naive: Sequence[float], block: int, draws: int = 2000, seed: int = 20261026
) -> tuple[float, float]:
    """95% interval of (MAE_model - MAE_naive) / MAE_naive with moving blocks of `block` consecutive pairs."""
    a, b = np.abs(np.asarray(err_model, float)), np.abs(np.asarray(err_naive, float))
    n = len(a)
    block = max(1, min(block, n))
    rng = np.random.default_rng(seed)
    starts_n = n - block + 1
    per = math.ceil(n / block)
    vals = np.empty(draws)
    for i in range(draws):
        idx = np.concatenate([np.arange(s, s + block) for s in rng.integers(0, starts_n, per)])[:n]
        vals[i] = (a[idx].mean() - b[idx].mean()) / b[idx].mean()
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def beats_naive(holm_p: float, ci: tuple[float, float], relative_change: float, smallest_gain: float) -> bool:
    """Section 8: all three must hold. relative_change is negative for an improvement; smallest_gain is positive."""
    return holm_p < 0.05 and ci[1] < 0 and -relative_change >= smallest_gain


def compare_to_naive(
    series: Sequence[Obs], model: Model, h: int, test_season: str, draws: int = 2000
) -> dict[str, float | int | tuple[float, float]]:
    """One model against naive on the test season, on the pairs where both produce a forecast. Returns the raw
    p (not yet Holm-adjusted, which needs the whole family), the interval and the relative change in MAE."""
    base = {(f.origin, f.target): f for f in run_model(series, naive, h, test_season)}
    mine = [f for f in run_model(series, model, h, test_season) if (f.origin, f.target) in base]
    ref = [base[(f.origin, f.target)] for f in mine]
    e_m, e_n = [f.error for f in mine], [f.error for f in ref]
    stat, p = dm_test(e_m, e_n, h)
    return {
        "pairs": len(mine),
        "mae_model": mae(mine),
        "mae_naive": mae(ref),
        "relative_change": mae(mine) / mae(ref) - 1,
        "dm_statistic": stat,
        "p_raw": p,
        "ci": block_bootstrap_relative_change(e_m, e_n, h, draws),
    }
