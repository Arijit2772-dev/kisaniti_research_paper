"""Independent recomputation of the test-season statistics. Written separately from layers/L3a_forecasting/evalkit.py: it
imports nothing from it and uses only numpy, scipy and the saved forecast file. It recomputes, for every variety, horizon and
model, the MAE, the paired Diebold-Mariano statistic with the Harvey-Leybourne-Newbold correction and a Bartlett-weighted
variance of lag h - 1, the two-sided p, the Holm adjustment over the 42 primary comparisons, the relative change in MAE, and a
fresh block bootstrap of that change with a different seed, and compares them with results/C0_protocol/test_season_*.csv.
Writes results/C0_protocol/independent_check.json. Exact quantities must agree to 1e-9; the bootstrap interval ends, which depend on the random seed, to within 10% of the interval width.

    env/run scripts/independent_check.py
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results" / "C0_protocol"


def dm_hln(e_model: np.ndarray, e_naive: np.ndarray, h: int) -> tuple[float, float]:
    d = np.abs(e_model) - np.abs(e_naive)
    n = d.size
    dbar = d.mean()
    c = d - dbar
    gam = [float((c[k:] * c[: n - k]).sum() / n) for k in range(h)]  # autocovariances at lags 0..h-1
    var = gam[0] + 2 * sum((1 - k / h) * gam[k] for k in range(1, h))
    dm = dbar / math.sqrt(var / n)
    hln = dm * math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    return hln, 2 * stats.t.sf(abs(hln), n - 1)


def holm(p: list[float]) -> list[float]:
    order = np.argsort(p)
    m = len(p)
    out = np.empty(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * p[i]))
        out[i] = run
    return out.tolist()


def main() -> None:
    f = pd.read_csv(R / "test_forecasts.csv")
    f["err"] = f.forecast - f.actual
    res = pd.read_csv(R / "test_season_results.csv")
    inf = pd.read_csv(R / "test_season_inference.csv")
    worst = {"mae": 0.0, "dm": 0.0, "p_raw": 0.0, "p_holm": 0.0, "rel": 0.0, "ci": 0.0}
    for r in res.itertuples():
        g = f[(f.variety == r.variety) & (f.horizon == r.horizon) & (f.model == r.model)]
        worst["mae"] = max(worst["mae"], abs(g.err.abs().mean() - r.mae))
        assert len(g) == r.pairs
    raw, rows = [], []
    for r in inf.itertuples():
        a = f[(f.variety == r.variety) & (f.horizon == r.horizon) & (f.model == r.model)].set_index(["origin", "target"]).err
        b = f[(f.variety == r.variety) & (f.horizon == r.horizon) & (f.model == "naive")].set_index(["origin", "target"]).err
        both = a.index.intersection(b.index).sort_values()
        ea, eb = a.loc[both].to_numpy(), b.loc[both].to_numpy()
        assert len(both) == r.pairs
        stat, p = dm_hln(ea, eb, int(r.horizon))
        rel = np.abs(ea).mean() / np.abs(eb).mean() - 1
        worst["dm"] = max(worst["dm"], abs(stat - r.dm_statistic))
        worst["p_raw"] = max(worst["p_raw"], abs(p - r.p_raw))
        worst["rel"] = max(worst["rel"], abs(rel - r.relative_change))
        raw.append(p)
        rng = np.random.default_rng(777)
        h = int(r.horizon)
        n = len(both)
        blk = max(1, min(h, n))
        per = math.ceil(n / blk)
        draws = np.empty(4000)
        for i in range(draws.size):
            idx = np.concatenate([np.arange(s, s + blk) for s in rng.integers(0, n - blk + 1, per)])[:n]
            draws[i] = np.abs(ea[idx]).mean() / np.abs(eb[idx]).mean() - 1
        lo, hi = np.percentile(draws, [2.5, 97.5])
        width = r.ci_high - r.ci_low
        worst["ci"] = max(worst["ci"], abs(lo - r.ci_low) / width, abs(hi - r.ci_high) / width)  # Monte Carlo noise, relative to the interval width
        rows.append(r)
    for r, p in zip(rows, holm(raw), strict=True):
        worst["p_holm"] = max(worst["p_holm"], abs(p - r.p_holm))
    better = [r for r, p in zip(rows, holm(raw), strict=True) if p < 0.05 and r.ci_high < 0 and -r.relative_change >= r.smallest_gain]
    ok = all(worst[k] < 1e-9 for k in ("mae", "dm", "p_raw", "p_holm", "rel")) and worst["ci"] < 0.10 and not better
    doc = {"comparisons": len(rows), "metric_rows": int(len(res)), "max_abs_difference": {k: float(v) for k, v in worst.items()}, "better_by_independent_rule": len(better), "agrees": bool(ok)}
    (R / "independent_check.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps(doc, indent=2))


if __name__ == "__main__":
    main()
