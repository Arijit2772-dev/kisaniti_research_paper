"""Models 4 to 8 of the pre-registered comparison (PREREGISTERED_PROTOCOL.md section 5 and 13): ETS, ARIMA, LightGBM,
GRU and Chronos-2. Every model is a pure function of the history it is given (index values up to the origin, with the
mandi count and IQR of each index day) and the target day; nothing after the origin is ever read. A model returns the
point forecast, or (point, native ranges), or None when it cannot forecast (too little training data).

Hyperparameter variants are named ``family@setting`` and come from config/grids.json; the grid is fixed before the first
validation run and the variant used in the test season is the one with the lowest validation-season MAE per variety
and horizon (choose_config.py).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import evalkit as ek
import numpy as np
import pandas as pd

MIN_TRAIN_PAIRS = 20
LAGS = (1, 2, 3, 5, 7)  # index days back from the origin; lag 1 is the origin day itself, so no feature is later than the origin
SEEDS = (0, 1, 2, 3, 4)
GRIDS = json.loads((Path(__file__).resolve().parent / "config" / "grids.json").read_text()) if (Path(__file__).resolve().parent / "config" / "grids.json").exists() else {}


def _season_obs(history: Sequence[ek.Obs]) -> list[ek.Obs]:
    return [o for o in history if o.season == history[-1].season]


def _daily_frame(obs: Sequence[ek.Obs], origin: date, fill: bool) -> pd.DataFrame:
    """The season's index on a daily grid up to the origin. fill=True carries the last observed value forward (ETS and
    ARIMA input only); fill=False leaves missing days as NaN (Chronos-2)."""
    s = pd.Series({pd.Timestamp(o.day): o.value for o in obs})
    s = s.reindex(pd.date_range(s.index.min(), pd.Timestamp(origin), freq="D"))
    if fill:
        s = s.ffill()
    return pd.DataFrame({"unique_id": "x", "ds": s.index, "y": s.to_numpy()})


# ---- ETS and ARIMA (statsforecast), one fit per origin, forecasts for all horizons up to 60 days cached ------------
_SF_CACHE: dict[tuple[str, date, int], pd.DataFrame] = {}


def _statsforecast(kind: str, history: Sequence[ek.Obs]) -> pd.DataFrame | None:
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA, AutoETS

    obs = _season_obs(history)
    origin = history[-1].day
    key = (kind, origin, len(history))
    if key not in _SF_CACHE:
        model = AutoETS(season_length=1) if kind == "ets" else AutoARIMA(season_length=1)
        sf = StatsForecast(models=[model], freq="D", n_jobs=1)
        _SF_CACHE.clear() if len(_SF_CACHE) > 400 else None
        _SF_CACHE[key] = sf.forecast(df=_daily_frame(obs, origin, fill=True), h=60, level=[80, 95]).set_index("ds")
    return _SF_CACHE[key]


def _make_sf(kind: str, col: str) -> ek.Model:
    def model(history: Sequence[ek.Obs], target: date) -> Any:
        fc = _statsforecast(kind, history)
        row = fc.loc[pd.Timestamp(target)]
        return float(row[col]), {80: (float(row[f"{col}-lo-80"]), float(row[f"{col}-hi-80"])), 95: (float(row[f"{col}-lo-95"]), float(row[f"{col}-hi-95"]))}

    return model


# ---- training pairs shared by LightGBM and the GRU -------------------------------------------------------------------
def _features(obs: Sequence[ek.Obs], i: int) -> list[float]:
    """Features at index position i of a season: the index at lags 1, 2, 3, 5 and 7 (lag 1 is the origin itself), the day of
    the season, and the mandi count and IQR of the origin day."""
    o = obs[i]
    return [obs[i - (k - 1)].value for k in LAGS] + [float((o.day - obs[0].day).days), float(o.n_mandis), o.iqr]


def _pairs(history: Sequence[ek.Obs], h: int) -> tuple[np.ndarray, np.ndarray]:
    """All (features at an eligible origin, index value h days later) pairs whose target day is not after the current origin."""
    origin = history[-1].day
    by_season: dict[str, list[ek.Obs]] = {}
    for o in history:
        by_season.setdefault(o.season, []).append(o)
    xs, ys = [], []
    for obs in by_season.values():
        days = {o.day: o.value for o in obs}
        for i in range(len(obs)):
            if i + 1 < ek.MIN_SEASON_DAYS:
                continue
            t = obs[i].day + timedelta(days=h)
            if t in days and t <= origin:
                xs.append(_features(obs, i))
                ys.append(days[t])
    return np.array(xs, dtype=float), np.array(ys, dtype=float)


def _origin_features(history: Sequence[ek.Obs]) -> np.ndarray | None:
    obs = _season_obs(history)
    return np.array([_features(obs, len(obs) - 1)], dtype=float) if len(obs) >= max(LAGS) else None


# ---- LightGBM ------------------------------------------------------------------------------------------------------
_QUANTILES = {80: (0.1, 0.9), 95: (0.025, 0.975)}


def _make_lgbm(num_leaves: int, n_estimators: int, with_ranges: bool) -> ek.Model:
    import lightgbm as lgb

    cache: dict[tuple[date, int, int], Any] = {}

    def fit(x: np.ndarray, y: np.ndarray, objective: str, alpha: float | None, seed: int) -> Any:
        params: dict[str, Any] = dict(objective=objective, num_leaves=num_leaves, learning_rate=0.05, min_data_in_leaf=5, bagging_fraction=0.8,
                                      bagging_freq=1, feature_fraction=0.8, seed=seed, num_threads=1, verbose=-1, deterministic=True, force_row_wise=True)
        if alpha is not None:
            params["alpha"] = alpha
        return lgb.train(params, lgb.Dataset(x, label=y), num_boost_round=n_estimators)

    def model(history: Sequence[ek.Obs], target: date) -> Any:
        origin = history[-1].day
        h = (target - origin).days
        x, y = _pairs(history, h)
        f0 = _origin_features(history)
        if f0 is None or len(y) < MIN_TRAIN_PAIRS:
            return None
        key = (origin, len(history), h)
        if key not in cache:
            point = float(np.mean([fit(x, y, "regression", None, sd).predict(f0)[0] for sd in SEEDS]))
            ranges = None
            if with_ranges:
                q = {a: float(fit(x, y, "quantile", a, 0).predict(f0)[0]) for pair in _QUANTILES.values() for a in pair}
                lo80, hi80 = min(q[0.1], point), max(q[0.9], point)  # separately fitted quantiles can cross: rearranged to nest
                ranges = {80: (lo80, hi80), 95: (min(q[0.025], lo80), max(q[0.975], hi80))}
            cache.clear() if len(cache) > 2000 else None
            cache[key] = (point, ranges)
        point, ranges = cache[key]
        return point if ranges is None else (point, ranges)

    return model


# ---- GRU -----------------------------------------------------------------------------------------------------------------
def _make_gru(hidden: int, epochs: int) -> ek.Model:
    import torch
    from torch import nn

    torch.set_num_threads(1)
    cache: dict[tuple[date, int, int], float] = {}

    class Net(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.gru = nn.GRU(1, hidden, batch_first=True)
            self.out = nn.Linear(hidden, 1)

        def forward(self, z: Any) -> Any:
            o, _ = self.gru(z)
            return self.out(o[:, -1, :]).squeeze(-1)

    def model(history: Sequence[ek.Obs], target: date) -> Any:
        origin = history[-1].day
        h = (target - origin).days
        key = (origin, len(history), h)
        if key in cache:
            return cache[key]
        obs_now = _season_obs(history)
        if len(obs_now) < 7:
            return None
        # training windows: the last seven index days of the season up to each eligible origin
        by_season: dict[str, list[ek.Obs]] = {}
        for o in history:
            by_season.setdefault(o.season, []).append(o)
        xs, ys = [], []
        for obs in by_season.values():
            days = {o.day: o.value for o in obs}
            for i in range(len(obs)):
                t = obs[i].day + timedelta(days=h)
                if i + 1 >= ek.MIN_SEASON_DAYS and t in days and t <= origin:
                    xs.append([obs[i - 6 + j].value for j in range(7)])
                    ys.append(days[t])
        if len(ys) < MIN_TRAIN_PAIRS:
            return None
        x, y = np.array(xs), np.array(ys)
        mu, sd = x.mean(), x.std() + 1e-9
        xt = torch.tensor((x - mu) / sd, dtype=torch.float32).unsqueeze(-1)
        yt = torch.tensor((y - mu) / sd, dtype=torch.float32)
        now = torch.tensor(((np.array([o.value for o in obs_now[-7:]]) - mu) / sd), dtype=torch.float32).reshape(1, 7, 1)
        preds = []
        for seed in SEEDS:
            torch.manual_seed(seed)
            net = Net()
            opt = torch.optim.Adam(net.parameters(), lr=1e-3)
            for _ in range(epochs):
                opt.zero_grad()
                nn.functional.mse_loss(net(xt), yt).backward()
                opt.step()
            with torch.no_grad():
                preds.append(float(net(now)[0]) * sd + mu)
        cache.clear() if len(cache) > 2000 else None
        cache[key] = float(np.mean(preds))
        return cache[key]

    return model


# ---- Chronos-2 zero-shot -------------------------------------------------------------------------------------------------
_PIPE: list[Any] = []
_CH_CACHE: dict[tuple[date, int], pd.DataFrame] = {}


def _chronos(history: Sequence[ek.Obs]) -> pd.DataFrame:
    origin = history[-1].day
    key = (origin, len(history))
    if key not in _CH_CACHE:
        import chronos

        if not _PIPE:
            _PIPE.append(chronos.Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu"))
        d = _daily_frame(_season_obs(history), origin, fill=False)
        df = pd.DataFrame({"item_id": "x", "timestamp": d["ds"], "target": d["y"]})
        out = _PIPE[0].predict_df(df, prediction_length=60, quantile_levels=[0.025, 0.1, 0.5, 0.9, 0.975])
        _CH_CACHE.clear() if len(_CH_CACHE) > 400 else None
        _CH_CACHE[key] = out.set_index("timestamp")
    return _CH_CACHE[key]


def chronos2(history: Sequence[ek.Obs], target: date) -> Any:
    row = _chronos(history).loc[pd.Timestamp(target)]
    return float(row["0.5"]), {80: (float(row["0.1"]), float(row["0.9"])), 95: (float(row["0.025"]), float(row["0.975"]))}


# ---- registry: families and their grid variants -------------------------------------------------------------------
def variants() -> dict[str, ek.Model]:
    """Every runnable model name: ets, arima, chronos2 and ``lightgbm@..`` / ``gru@..`` for each grid point."""
    out: dict[str, ek.Model] = {"ets": _make_sf("ets", "AutoETS"), "arima": _make_sf("arima", "AutoARIMA"), "chronos2": chronos2}
    for g in GRIDS.get("lightgbm", []):
        out[f"lightgbm@nl{g['num_leaves']}_n{g['n_estimators']}"] = _make_lgbm(g["num_leaves"], g["n_estimators"], with_ranges=True)
    for g in GRIDS.get("gru", []):
        out[f"gru@h{g['hidden']}_e{g['epochs']}"] = _make_gru(g["hidden"], g["epochs"])
    return out


MODELS: dict[str, ek.Model] = variants()
