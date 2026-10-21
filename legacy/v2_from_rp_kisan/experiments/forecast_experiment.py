"""EXP-03 (paper v1): small mandi-network forecasting comparison on real AGMARKNET data.

Data   : AGMARKNET Paddy(Common), Punjab, Sep-Dec of 2020-2025 (cleaned records from sem_6/capstone).
Nodes  : 20 mandis that report in all six seasons and have the most trading dates.
Split  : train = 2020-2023 seasons, validation = 2024 season, test = 2025 season (never used for tuning).
Task   : forecast the modal price of every mandi for the next 1..7 trading dates from the last 7 trading dates.
Models : naive (persistence), 7-date moving average, MSP rule, ridge regression, GRU (no graph),
         T-GCN (graph + GRU), A3T-GCN (graph + GRU + temporal attention).
Errors are computed only where the target price was actually reported (no filled values are scored).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

HERE = Path(__file__).resolve().parent
RAW = Path("/Users/arijitsingh/Documents/sem_6/capstone/agmarknet_paddy_common_punjab_cleaned_records.csv")
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

L, H = 7, 7                       # input window and forecast horizon (trading dates)
SEEDS = [0, 1, 2, 3, 4]
TRAIN_SEASONS, VAL_SEASON, TEST_SEASON = [2020, 2021, 2022, 2023], 2024, 2025
# Official MSP, Paddy Grade 'A' (Rs/quintal), DES, Ministry of Agriculture & Farmers Welfare
MSP_GRADE_A = {2020: 1888, 2021: 1960, 2022: 2060, 2023: 2203, 2024: 2320, 2025: 2389}

torch.set_num_threads(4)


# ----------------------------------------------------------------------------- data
def build_panel():
    coords = pd.read_csv(HERE / "mandi_coordinates.csv")
    mandis = list(coords.market_name)
    d = pd.read_csv(RAW, parse_dates=["arrival_date"])
    d = d[d.market_name.isin(mandis)].copy()
    d["w"] = d.arrivals_metric_tonnes.where(d.arrivals_metric_tonnes > 0, 0.0)
    d["wp"] = d.w * d.modal_price_rs_per_quintal

    def agg(g):
        if g.w.sum() > 0:
            return g.wp.sum() / g.w.sum()
        return g.modal_price_rs_per_quintal.mean()

    daily = d.groupby(["arrival_date", "market_name"]).apply(agg, include_groups=False).rename("price").reset_index()
    wide = daily.pivot(index="arrival_date", columns="market_name", values="price")[mandis].sort_index()
    wide["season"] = wide.index.year
    return wide, mandis, coords, d


def knn_adjacency(coords, k):
    lat = np.radians(coords.lat.values.astype(float))
    lon = np.radians(coords.lon.values.astype(float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2) ** 2
    dist = 2 * 6371.0 * np.arcsin(np.sqrt(a))
    n = len(coords)
    A = np.zeros((n, n))
    for i in range(n):
        nn_idx = np.argsort(dist[i])[1 : k + 1]
        A[i, nn_idx] = 1.0
    A = np.maximum(A, A.T)                      # undirected
    A_hat = A + np.eye(n)
    dinv = np.diag(1.0 / np.sqrt(A_hat.sum(1)))
    return dinv @ A_hat @ dinv, dist


def make_windows(wide, mandis, seasons):
    """Return X (S,N,L) prices, Y (S,N,H) prices, M (S,N,H) observed mask, season id per sample."""
    Xs, Ys, Ms, Ss, Ds = [], [], [], [], []
    for s in seasons:
        block = wide[wide.season == s][mandis]
        obs = block.notna().values
        # no look-ahead: carry each mandi's last price forward; before a mandi's first report in the season,
        # use the mean price reported by the other mandis on that same date
        filled = block.ffill()
        filled = filled.T.fillna(block.mean(axis=1)).T.values
        T = len(block)
        for t in range(L - 1, T - H):
            Xs.append(filled[t - L + 1 : t + 1].T)
            Ys.append(filled[t + 1 : t + 1 + H].T)
            Ms.append(obs[t + 1 : t + 1 + H].T)
            Ss.append(s)
            Ds.append(block.index[t])
    return (np.array(Xs, dtype=np.float64), np.array(Ys, dtype=np.float64),
            np.array(Ms, dtype=bool), np.array(Ss), np.array(Ds))


# ----------------------------------------------------------------------------- metrics
def metrics(pred, Y, M):
    out = {}
    for name, sl in [("h1", slice(0, 1)), ("h7", slice(6, 7)), ("h1_7", slice(0, 7))]:
        p, y, m = pred[:, :, sl][M[:, :, sl]], Y[:, :, sl][M[:, :, sl]], None
        err = p - y
        out[name] = {
            "MAE": float(np.mean(np.abs(err))),
            "RMSE": float(np.sqrt(np.mean(err ** 2))),
            "MAPE": float(np.mean(np.abs(err) / y) * 100),
            "n": int(len(y)),
        }
    return out


# ----------------------------------------------------------------------------- baselines
def naive(X):
    return np.repeat(X[:, :, -1:], H, axis=2)


def moving_avg(X):
    return np.repeat(X.mean(axis=2, keepdims=True), H, axis=2)


def msp_rule(X, seasons):
    v = np.array([MSP_GRADE_A[s] for s in seasons], dtype=float)
    return np.broadcast_to(v[:, None, None], (len(seasons), X.shape[1], H)).copy()


def rel_features(X):
    last = X[:, :, -1:]
    return X / last - 1.0, last


def ridge_fit_predict(Xtr, Ytr, Mtr, Xev, alphas, Xval, Yval, Mval):
    def design(X):
        f, last = rel_features(X)
        return f.reshape(-1, L), last.reshape(-1, 1)

    Ftr, ltr = design(Xtr)
    Rtr = (Ytr.reshape(-1, H) / ltr) - 1.0
    best = None
    for a in alphas:
        W = []
        for h in range(H):
            m = Mtr.reshape(-1, H)[:, h]
            A = np.c_[np.ones(m.sum()), Ftr[m]]
            reg = a * np.eye(A.shape[1]); reg[0, 0] = 0
            W.append(np.linalg.solve(A.T @ A + reg, A.T @ Rtr[m, h]))
        W = np.array(W)

        def pred(X):
            F, l = design(X)
            return ((np.c_[np.ones(len(F)), F] @ W.T + 1.0) * l).reshape(X.shape[0], X.shape[1], H)

        mae = metrics(pred(Xval), Yval, Mval)["h1_7"]["MAE"]
        if best is None or mae < best[0]:
            best = (mae, a, pred)
    return best[2](Xev), best[1]


# ----------------------------------------------------------------------------- neural models
class GraphGRUCell(nn.Module):
    """T-GCN cell: GRU whose input/hidden transforms are graph convolutions (A_hat = I gives a plain GRU)."""

    def __init__(self, A_hat, in_dim, hid):
        super().__init__()
        self.register_buffer("A", torch.tensor(A_hat, dtype=torch.float32))
        self.hid = hid
        self.gates = nn.Linear(in_dim + hid, 2 * hid)
        self.cand = nn.Linear(in_dim + hid, hid)

    def gc(self, lin, z):                      # z: (B,N,F)
        return lin(torch.einsum("ij,bjf->bif", self.A, z))

    def forward(self, x, h):
        zr = torch.sigmoid(self.gc(self.gates, torch.cat([x, h], -1)))
        r, u = zr.chunk(2, -1)
        c = torch.tanh(self.gc(self.cand, torch.cat([x, r * h], -1)))
        return u * h + (1 - u) * c


class SeqModel(nn.Module):
    def __init__(self, A_hat, hid=32, attention=False):
        super().__init__()
        self.cell = GraphGRUCell(A_hat, 1, hid)
        self.attention = attention
        if attention:                           # A3T-GCN temporal attention over hidden states
            self.att = nn.Sequential(nn.Linear(hid, hid), nn.Tanh(), nn.Linear(hid, 1))
        self.head = nn.Linear(hid, H)

    def forward(self, x):                       # x: (B,N,L) relative changes
        B, N, T = x.shape
        h = x.new_zeros(B, N, self.cell.hid)
        hs = []
        for t in range(T):
            h = self.cell(x[:, :, t : t + 1], h)
            hs.append(h)
        if self.attention:
            Hs = torch.stack(hs, 2)                          # (B,N,T,hid)
            a = torch.softmax(self.att(Hs).squeeze(-1), -1)  # (B,N,T)
            ctx = (a.unsqueeze(-1) * Hs).sum(2)
        else:
            ctx = h
        return self.head(ctx)                               # (B,N,H) relative change vs last price


def train_neural(A_hat, attention, seed, data, max_epochs=400, patience=40, lr=1e-3, hid=32):
    torch.manual_seed(seed); np.random.seed(seed)
    (Xtr, Ytr, Mtr), (Xva, Yva, Mva) = data
    model = SeqModel(A_hat, hid, attention)
    opt = torch.optim.Adam(model.parameters(), lr=lr)

    def tens(X, Y, M):
        f, last = rel_features(X)
        return (torch.tensor(f, dtype=torch.float32), torch.tensor(Y / last - 1.0, dtype=torch.float32),
                torch.tensor(M, dtype=torch.float32), last)

    ftr, rtr, mtr, _ = tens(Xtr, Ytr, Mtr)
    fva, _, _, lva = tens(Xva, Yva, Mva)
    best, best_state, wait = math.inf, None, 0
    for ep in range(max_epochs):
        model.train()
        perm = torch.randperm(len(ftr))
        for i in range(0, len(ftr), 32):
            idx = perm[i : i + 32]
            loss = ((model(ftr[idx]) - rtr[idx]).abs() * mtr[idx]).sum() / mtr[idx].sum().clamp(min=1)
            opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            pva = (model(fva).numpy() + 1.0) * lva
        mae = metrics(pva, Yva, Mva)["h1_7"]["MAE"]
        if mae < best - 1e-6:
            best, wait = mae, 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= patience:
                break
    model.load_state_dict(best_state)
    model.eval()

    def predict(X):
        f, last = rel_features(X)
        with torch.no_grad():
            return (model(torch.tensor(f, dtype=torch.float32)).numpy() + 1.0) * last

    return predict, best, sum(p.numel() for p in model.parameters())


# ----------------------------------------------------------------------------- main
FOLDS = [  # forward-chaining: train on earlier seasons, tune on the next, test on the one after
    ([2020, 2021], 2022, 2023),
    ([2020, 2021, 2022], 2023, 2024),
    ([2020, 2021, 2022, 2023], 2024, 2025),
]


def run_fold(wide, mandis, coords, train_s, val_s, test_s, save=False):
    Xtr, Ytr, Mtr, Str, _ = make_windows(wide, mandis, train_s)
    Xva, Yva, Mva, Sva, _ = make_windows(wide, mandis, [val_s])
    Xte, Yte, Mte, Ste, Dte = make_windows(wide, mandis, [test_s])
    results, extra = {}, {"windows": {"train": len(Xtr), "val": len(Xva), "test": len(Xte)},
                          "scored_targets_h1": int(Mte[:, :, 0].sum())}
    results["Naive (last price)"] = metrics(naive(Xte), Yte, Mte)
    results["Moving average (7 dates)"] = metrics(moving_avg(Xte), Yte, Mte)
    results["MSP rule"] = metrics(msp_rule(Xte, Ste), Yte, Mte)
    p_ridge, a = ridge_fit_predict(Xtr, Ytr, Mtr, Xte, [0.01, 0.1, 1, 10, 100], Xva, Yva, Mva)
    results["Ridge regression"] = metrics(p_ridge, Yte, Mte); extra["ridge_alpha"] = a
    kval = {}
    for k in [2, 3, 5]:
        A_hat, _ = knn_adjacency(coords, k)
        _, vbest, _ = train_neural(A_hat, True, 0, ((Xtr, Ytr, Mtr), (Xva, Yva, Mva)))
        kval[k] = vbest
    k_best = min(kval, key=kval.get)
    extra["k_validation_MAE"] = kval; extra["k_selected"] = k_best
    A_k, _ = knn_adjacency(coords, k_best)
    I = np.eye(len(mandis))
    neural_preds = {}
    for name, A_hat, att in [("GRU (no graph)", I, False), ("T-GCN (graph, no attention)", A_k, False),
                             ("A3T-GCN", A_k, True)]:
        runs, preds = [], []
        for s in SEEDS:
            pred_fn, _, params = train_neural(A_hat, att, s, ((Xtr, Ytr, Mtr), (Xva, Yva, Mva)))
            pt = pred_fn(Xte); preds.append(pt); runs.append(metrics(pt, Yte, Mte))
        agg = {}
        for hz in runs[0]:
            agg[hz] = {m: float(np.mean([r[hz][m] for r in runs])) for m in ["MAE", "RMSE", "MAPE"]}
            agg[hz].update({m + "_sd": float(np.std([r[hz][m] for r in runs])) for m in ["MAE", "RMSE", "MAPE"]})
            agg[hz]["n"] = runs[0][hz]["n"]
        results[name] = agg; extra[name + " params"] = params
        neural_preds[name] = np.mean(preds, 0)

    def per_date_mae(pred):
        e = np.abs(pred - Yte)[:, :, 0]; m = Mte[:, :, 0]
        return np.array([e[i][m[i]].mean() if m[i].any() else np.nan for i in range(len(e))])

    from scipy.stats import binomtest
    base = per_date_mae(naive(Xte)); paired = {}
    for name, pr in [("A3T-GCN", neural_preds["A3T-GCN"]), ("MSP rule", msp_rule(Xte, Ste)), ("Ridge regression", p_ridge)]:
        e = per_date_mae(pr); ok = ~np.isnan(e) & ~np.isnan(base)
        better, worse = int((e[ok] < base[ok] - 1e-9).sum()), int((e[ok] > base[ok] + 1e-9).sum())
        pval = binomtest(better, better + worse, 0.5).pvalue if better + worse > 0 else float("nan")
        paired[name] = {"dates_better_than_naive": better, "dates_worse": worse,
                        "ties": int(ok.sum() - better - worse), "sign_test_p": float(pval)}
    extra["paired_vs_naive_h1"] = paired
    if save:
        np.savez(OUT / "test_forecasts.npz", dates=Dte.astype("datetime64[D]").astype(str), mandis=np.array(mandis),
                 X=Xte, Y=Yte, M=Mte, a3tgcn=neural_preds["A3T-GCN"], naive=naive(Xte))
    return results, extra


def main():
    wide, mandis, coords, rec = build_panel()
    obs = wide[mandis].notna()
    all_vals = wide[mandis].stack()
    seasons_ser = wide.season.reindex(all_vals.index.get_level_values(0)).values
    msp_ser = np.array([MSP_GRADE_A[s] for s in seasons_ser])
    desc = {
        "records_in_selected_mandis": int(len(rec)),
        "trading_dates": int(len(wide)),
        "dates_per_season": {int(k): int(v) for k, v in wide.groupby("season").size().items()},
        "observed_share": float(obs.values.mean()),
        "observed_mandi_days": int(obs.values.sum()),
        "share_exactly_at_msp_by_season": {int(s): float(np.mean(np.round(all_vals.values[seasons_ser == s]) == MSP_GRADE_A[s])) for s in MSP_GRADE_A},
        "share_within_1pct_of_msp_all_seasons": float(np.mean(np.abs(all_vals.values - msp_ser) / msp_ser <= 0.01)),
        "price_std_by_season": {int(s): float(np.std(all_vals.values[seasons_ser == s], ddof=1)) for s in MSP_GRADE_A},
        "cross_mandi_daily_std_mean_by_season": {int(k): float(v) for k, v in wide.groupby("season")[mandis].apply(lambda b: b.std(axis=1).mean()).items()},
    }
    print(json.dumps(desc, indent=1))
    all_res = {}
    for i, (tr, va, te) in enumerate(FOLDS):
        res, extra = run_fold(wide, mandis, coords, tr, va, te, save=(te == 2025))
        all_res[te] = {"train": tr, "val": va, "results": res, "extra": extra}
        print(f"fold test={te}: k={extra['k_selected']} windows={extra['windows']} paired={extra['paired_vs_naive_h1']}")
        for name, r in res.items():
            print(f"   {name:30s} h1 MAE {r['h1']['MAE']:7.2f}  h7 MAE {r['h7']['MAE']:7.2f}  h1-7 MAE {r['h1_7']['MAE']:7.2f} RMSE {r['h1_7']['RMSE']:7.2f}")
    models = list(all_res[2025]["results"])
    rows = []
    for name in models:
        row = [name]
        for te in [2023, 2024, 2025]:
            row.append(round(all_res[te]["results"][name]["h1_7"]["MAE"], 2))
        row.append(round(float(np.mean(row[1:4])), 2))
        row.append(round(float(np.mean([all_res[te]["results"][name]["h1"]["MAE"] for te in [2023, 2024, 2025]])), 2))
        row.append(round(float(np.mean([all_res[te]["results"][name]["h7"]["MAE"] for te in [2023, 2024, 2025]])), 2))
        row.append(round(float(np.mean([all_res[te]["results"][name]["h1_7"]["RMSE"] for te in [2023, 2024, 2025]])), 2))
        row.append(round(float(np.mean([all_res[te]["results"][name]["h1_7"]["MAPE"] for te in [2023, 2024, 2025]])), 3))
        rows.append(row)
    tab = pd.DataFrame(rows, columns=["Model", "MAE 2023", "MAE 2024", "MAE 2025", "MAE mean", "MAE h=1 mean",
                                      "MAE h=7 mean", "RMSE mean", "MAPE % mean"])
    tab.to_csv(OUT / "forecast_table.csv", index=False)
    json.dump({"description": desc, "folds": all_res}, open(OUT / "forecast_results.json", "w"), indent=1, default=str)
    print(tab.to_string(index=False))


if __name__ == "__main__":
    main()
