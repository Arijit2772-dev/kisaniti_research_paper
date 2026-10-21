"""EXP-08/10 (paper v1): small cooperative-allocation test on a SYNTHETIC FPO using REAL 2025 mandi prices.

Synthetic (labelled) inputs : farmer lot locations and quantities, transport rate, road-circuity factor,
                              per-mandi daily handling limit and per-day waiting cost.
Real inputs                 : mandi coordinates (OpenStreetMap) and AGMARKNET 2025 modal prices / forecasts.

Policies compared on every forecast origin of the 2025 season and every synthetic FPO seed:
  P1 Nearest mandi, first free day (first-come-first-served under the same daily limit)
  P2 Independent best choice (each lot picks its own best mandi-day; ignores the shared daily limit)
  P3 KisanNiti cooperative model (integer program, forecast prices, shared daily limit)
  P4 Same model with the actual prices (perfect-foresight upper bound)
All plans are scored with the actual prices; a separate validator checks every constraint.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"

CANDIDATES = ["Patiala(New Anaj Mandi) APMC", "Patran APMC", "Bhawanigarh APMC", "Chanarthal APMC", "Amargarh APMC"]
D = 5                        # planning horizon: next 5 trading dates
UNIT = 10                    # quantities are planned in 10-quintal units
N_LOTS = 40
FPO_SEEDS = list(range(10))
CIRCUITY = 1.3               # assumed road/straight-line distance ratio
BASE = {"rate": 2.0, "cap": 300, "wait": 2.0}   # Rs per quintal-km, quintals per mandi-day, Rs per quintal per day
CENTRE = (30.25, 76.20)      # synthetic FPO area: about 30 km x 30 km between Patiala and Bhawanigarh


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def make_fpo(seed, coords):
    rng = np.random.default_rng(seed)
    lat = CENTRE[0] + rng.uniform(-0.135, 0.135, N_LOTS)     # ~ +/-15 km
    lon = CENTRE[1] + rng.uniform(-0.155, 0.155, N_LOTS)
    Q = rng.integers(2, 13, N_LOTS) * UNIT                    # 20..120 quintals per lot
    mlat = coords.set_index("market_name").loc[CANDIDATES, "lat"].values.astype(float)
    mlon = coords.set_index("market_name").loc[CANDIDATES, "lon"].values.astype(float)
    km = CIRCUITY * haversine(lat[:, None], lon[:, None], mlat[None, :], mlon[None, :])
    return Q, km


def solve_ip(value, Q, cap):
    """max sum value[f,m,d]*x  s.t. sum_md x = Q_f ; sum_f x <= cap ; x integer units >= 0."""
    F, M, Dd = value.shape
    n = F * M * Dd
    idx = lambda f, m, d: (f * M + m) * Dd + d
    A1 = lil_matrix((F, n)); A2 = lil_matrix((M * Dd, n))
    for f in range(F):
        for m in range(M):
            for d in range(Dd):
                A1[f, idx(f, m, d)] = UNIT
                A2[m * Dd + d, idx(f, m, d)] = UNIT
    c = -(value * UNIT).reshape(-1)
    res = milp(c, constraints=[LinearConstraint(A1.tocsr(), Q, Q), LinearConstraint(A2.tocsr(), -np.inf, cap)],
               integrality=np.ones(n), bounds=Bounds(0, np.inf), options={"time_limit": 60})
    if res.status != 0:
        raise RuntimeError(res.message)
    return np.round(res.x).reshape(F, M, Dd) * UNIT


def nearest_fcfs(Q, km, cap, rng):
    F, M = km.shape
    x = np.zeros((F, M, D)); load = np.zeros((M, D))
    for f in rng.permutation(F):
        left = Q[f]
        for m in np.argsort(km[f]):
            for d in range(D):
                take = min(left, cap - load[m, d])
                if take > 0:
                    x[f, m, d] += take; load[m, d] += take; left -= take
                if left == 0:
                    break
            if left == 0:
                break
        if left > 0:
            raise RuntimeError("capacity too small for FCFS")
    return x


def independent_best(value, Q):
    F = len(Q)
    x = np.zeros_like(value)
    for f in range(F):
        m, d = np.unravel_index(np.argmax(value[f]), value[f].shape)
        x[f, m, d] = Q[f]
    return x


def validate(x, Q, cap):
    """Independent check of the plan; returns number of mandi-day limit violations (quantity must always hold)."""
    assert np.all(x >= -1e-9), "negative quantity"
    assert np.allclose(x.sum(axis=(1, 2)), Q), "lot quantity not conserved"
    load = x.sum(axis=0)
    return int((load > cap + 1e-9).sum()), float(np.clip(load - cap, 0, None).sum())


def score(x, actual, km, rate, wait):
    revenue = float((x * actual[None]).sum())
    transport = float((x * (rate * km)[:, :, None]).sum())
    waiting = float((x * (wait * np.arange(D))[None, None, :]).sum())
    return revenue - transport - waiting, revenue, transport, waiting


def run(params, forecasts, coords, origins, label):
    rate, cap, wait = params["rate"], params["cap"], params["wait"]
    mandis = list(forecasts["mandis"])
    cols = [mandis.index(m) for m in CANDIDATES]
    rows = []
    for seed in FPO_SEEDS:
        Q, km = make_fpo(seed, coords)
        rng = np.random.default_rng(1000 + seed)
        for o in origins:
            actual = forecasts["Y"][o][cols, :D]                 # real prices (last reported value if no report)
            pred = forecasts["a3tgcn"][o][cols, :D]
            msp = np.full_like(actual, 2389.0)
            cost = rate * km[:, :, None] + wait * np.arange(D)[None, None, :]
            plans = {
                "P1 Nearest mandi, first free day": nearest_fcfs(Q, km, cap, rng),
                "P2 Independent best choice": independent_best(msp[None] - cost, Q),
                "P3 KisanNiti cooperative (MSP-rule price)": solve_ip(msp[None] - cost, Q, cap),
                "P3b KisanNiti cooperative (A3T-GCN price)": solve_ip(pred[None] - cost, Q, cap),
                "P4 Perfect-foresight bound": solve_ip(actual[None] - cost, Q, cap),
            }
            for name, x in plans.items():
                nviol, excess = validate(x, Q, cap)
                net, rev, tr, wt = score(x, actual, km, rate, wait)
                split = int(((x > 0).sum(axis=(1, 2)) > 1).sum())
                rows.append({"setting": label, "seed": seed, "origin": str(forecasts["dates"][o]), "policy": name,
                             "quantity_q": float(Q.sum()), "net_rs": net, "revenue_rs": rev, "transport_rs": tr,
                             "waiting_rs": wt, "limit_violations": nviol, "excess_q": excess, "split_lots": split,
                             "avg_km": float((x.sum(2) * km).sum() / Q.sum())})
    return pd.DataFrame(rows)


def main():
    fc = dict(np.load(OUT / "test_forecasts.npz", allow_pickle=True))
    coords = pd.read_csv(HERE / "mandi_coordinates.csv")
    n_orig = len(fc["dates"])
    origins = [o for o in range(n_orig) if o % 3 == 0]             # every third trading date of 2025
    print("origins:", len(origins), "candidate mandis:", CANDIDATES)
    df = run(BASE, fc, coords, origins, "base")
    df.to_csv(OUT / "allocation_runs_base.csv", index=False)
    g = df.groupby("policy").agg(net_rs=("net_rs", "mean"), quantity_q=("quantity_q", "mean"),
                                 transport_rs=("transport_rs", "mean"), waiting_rs=("waiting_rs", "mean"),
                                 avg_km=("avg_km", "mean"), limit_violations=("limit_violations", "mean"),
                                 runs_with_violation=("limit_violations", lambda v: float((v > 0).mean())),
                                 excess_q=("excess_q", "mean"), split_lots=("split_lots", "mean"))
    g["net_rs_per_q"] = g.net_rs / g.quantity_q
    g["transport_rs_per_q"] = g.transport_rs / g.quantity_q
    p1 = df[df.policy.str.startswith("P1")].set_index(["seed", "origin"]).net_rs
    for pol in df.policy.unique():
        diff = df[df.policy == pol].set_index(["seed", "origin"]).net_rs - p1
        qty = df[df.policy == pol].set_index(["seed", "origin"]).quantity_q
        g.loc[pol, "gain_vs_P1_rs_per_q"] = float((diff / qty).mean())
        g.loc[pol, "gain_vs_P1_rs_per_q_sd"] = float((diff / qty).std())
    print(g.round(2).to_string())
    g.round(3).to_csv(OUT / "allocation_summary_base.csv")

    # sensitivity of the cooperative gain to the transport rate and the daily handling limit
    sens = []
    for rate in [1.0, 2.0, 4.0]:
        for cap in [200, 300, 500]:
            p = {"rate": rate, "cap": cap, "wait": BASE["wait"]}
            d = run(p, fc, coords, origins[::2], f"rate={rate},cap={cap}")
            a = d[d.policy.str.startswith("P1")].set_index(["seed", "origin"])
            b = d[d.policy.str.startswith("P3 ")].set_index(["seed", "origin"])
            c = d[d.policy.str.startswith("P2")].set_index(["seed", "origin"])
            sens.append({"rate_rs_per_q_km": rate, "cap_q_per_mandi_day": cap,
                         "P1_net_rs_per_q": float((a.net_rs / a.quantity_q).mean()),
                         "P3_net_rs_per_q": float((b.net_rs / b.quantity_q).mean()),
                         "gain_rs_per_q": float(((b.net_rs - a.net_rs) / a.quantity_q).mean()),
                         "P1_avg_km": float(a.avg_km.mean()), "P3_avg_km": float(b.avg_km.mean()),
                         "P2_runs_with_violation": float((c.limit_violations > 0).mean())})
    s = pd.DataFrame(sens)
    s.round(3).to_csv(OUT / "allocation_sensitivity.csv", index=False)
    print(s.round(2).to_string(index=False))
    json.dump({"candidates": CANDIDATES, "D": D, "unit": UNIT, "n_lots": N_LOTS, "fpo_seeds": FPO_SEEDS,
               "circuity": CIRCUITY, "base": BASE, "centre": CENTRE, "origins": len(origins)},
              open(OUT / "allocation_settings.json", "w"), indent=1)


if __name__ == "__main__":
    main()
