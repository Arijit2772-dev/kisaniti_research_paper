"""Exploratory data-sufficiency check for the basmati price index (EXP-01 companion).

Question: with this much data, how large must a model's improvement be before a
rolling-origin test can detect it (80% power, 5% level), and how many independent
observations do the planned comparisons really have?

Everything here is exploratory and labelled so; it is not a model result.
Usage: python3 layers/L1_data/power_check.py   (needs numpy)
"""
import csv, glob, statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
rows = []
for f in sorted(glob.glob(str(ROOT / "data/raw/agmarknet/paddy_basmati/*_punjab.csv"))):
    market = None
    for line in open(f, encoding="utf-8-sig").read().splitlines():
        if line.startswith("Market Name :"):
            market = line.split(":", 1)[1].strip().strip(","); continue
        if not line or line.startswith(("Arrival", '"')) or market is None: continue
        p = next(csv.reader([line]))
        if len(p) != 6 or not p[0].strip(): continue
        try:
            rows.append((market, p[2].strip(), datetime.strptime(p[0], "%d/%m/%Y"), float(p[5])))
        except ValueError:
            pass

def season(d): return d.year if d.month >= 9 else d.year - 1

def index(variety, min_mandis=3):
    by = defaultdict(dict)
    for m, v, d, x in rows:
        if v == variety: by[d][m] = x
    days = sorted(d for d, s in by.items() if len(s) >= min_mandis)
    return days, np.array([statistics.median(by[d].values()) for d in days]), [len(by[d]) for d in days]

def hac_var(x, lag):
    x = x - x.mean(); n = len(x)
    v = (x @ x) / n
    for k in range(1, lag + 1):
        v += 2 * (1 - k / (lag + 1)) * (x[k:] @ x[:-k]) / n
    return v / n  # variance of the mean

def ridge_forecast(y, t, h, lags, refit_every=10, min_train=40):
    """Expanding-window ridge on lagged levels differences; predicts y[t+h] - y[t]."""
    preds = {}
    coef = None
    for i in range(min_train, len(y) - h):
        if coef is None or (i - min_train) % refit_every == 0:
            X, Y = [], []
            for j in range(lags, i - h + 1):
                X.append(y[j - lags + 1:j + 1] - y[j - lags:j]); Y.append(y[j + h] - y[j])
            X, Y = np.array(X), np.array(Y)
            coef = np.linalg.solve(X.T @ X + 5.0 * np.eye(lags), X.T @ Y)
        x = y[i - lags + 1:i + 1] - y[i - lags:i]
        preds[i] = y[i] + x @ coef
    return preds

print("== Observations per season (variety-level daily index, >=3 mandis reporting)")
for var in ["1121", "Basmati 1509"]:
    days, y, n = index(var)
    per = defaultdict(int)
    for d in days: per[season(d)] += 1
    print(f"{var}: total index days {len(days)}; per season", {f"{k}-{str(k+1)[2:]}": v for k, v in sorted(per.items())}, f"; median mandis/day {statistics.median(n)}")

print("\n== Rolling-origin comparison: naive vs ridge-on-lags (exploratory), expanding window")
for var in ["1121", "Basmati 1509"]:
    days, y, _ = index(var)
    for h in (1, 5):
        pred = ridge_forecast(y, None, h, lags=5)
        e_n, e_r, keep = [], [], []
        for i, p in pred.items():
            if (days[i + h] - days[i]).days > 3 * h + 4:   # skip jumps across the off-season gap
                continue
            e_n.append(abs(y[i + h] - y[i])); e_r.append(abs(y[i + h] - p)); keep.append(i)
        e_n, e_r = np.array(e_n), np.array(e_r)
        d = e_n - e_r
        n_obs = len(d)
        se = np.sqrt(hac_var(d, lag=max(5, 2 * h)))
        mae_n = e_n.mean()
        # minimum detectable mean loss difference at 80% power, 5% two-sided
        mde = 2.8 * se
        print(f"{var} h={h}: origins {n_obs}; MAE naive ₹{mae_n:.1f}, ridge ₹{e_r.mean():.1f} ({100*(1-e_r.mean()/mae_n):+.1f}%); "
              f"DM-style z={d.mean()/se:+.2f}; smallest detectable gain ≈ {100*mde/mae_n:.1f}% of naive MAE; "
              f"effective n ≈ {int((d.std()**2/ (se**2*n_obs)) * 0 + (d.var()/ (se**2*n_obs)) ** -1 * n_obs) if False else round(d.var()/(se**2))}")

print("\n== How independent are the mandis? (average pairwise correlation of weekly changes, mandis with >=40 obs)")
for var in ["1121"]:
    ser = defaultdict(dict)
    for m, v, d, x in rows:
        if v == var: ser[m][d] = x
    good = [m for m, s in ser.items() if len(s) >= 40]
    dates = sorted({d for m in good for d in ser[m]})
    cors = []
    for i, a in enumerate(good):
        for b in good[i + 1:]:
            common = sorted(set(ser[a]) & set(ser[b]))
            if len(common) >= 30:
                da = np.diff([ser[a][d] for d in common]); db = np.diff([ser[b][d] for d in common])
                if da.std() > 0 and db.std() > 0: cors.append(np.corrcoef(da, db)[0, 1])
    print(f"{var}: {len(good)} mandis with >=40 obs; {len(cors)} pairs; mean correlation of day-to-day changes {np.mean(cors):.2f}")
