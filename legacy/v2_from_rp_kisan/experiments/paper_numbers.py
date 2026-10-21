"""Print every number quoted in the paper, straight from the result files (used to check the manuscript)."""
import json
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parent / "results"
fr = json.load(open(R / "forecast_results.json"))
d = fr["description"]
print("== data")
print("trading dates", d["trading_dates"], "observed mandi-days", d["observed_mandi_days"],
      "of", d["trading_dates"] * 20, f"({100 * d['observed_share']:.1f}%)")
for s in map(str, range(2020, 2026)):
    print(s, "dates", d["dates_per_season"][s], "at MSP %", round(100 * d["share_exactly_at_msp_by_season"][s], 1),
          "SD", round(d["price_std_by_season"][s], 1), "cross-mandi SD", round(d["cross_mandi_daily_std_mean_by_season"][s], 1))

print("== forecasting")
print(pd.read_csv(R / "forecast_table.csv").to_string(index=False))
tot = {"A3T-GCN": [0, 0, 0], "MSP rule": [0, 0, 0]}
for te, f in fr["folds"].items():
    ex = f["extra"]
    print(te, "k", ex["k_selected"], "windows", ex["windows"], "ridge alpha", ex["ridge_alpha"])
    for m in ["GRU (no graph)", "T-GCN (graph, no attention)", "A3T-GCN"]:
        x = f["results"][m]["h1_7"]
        print(f"   {m:28s} {x['MAE']:.2f} ± {x['MAE_sd']:.2f}")
    for m in tot:
        p = ex["paired_vs_naive_h1"][m]
        tot[m][0] += p["dates_better_than_naive"]; tot[m][1] += p["dates_worse"]; tot[m][2] += p["ties"]
print("paired vs naive at h=1 (better, worse, ties):", tot)

print("== allocation (base)")
a = pd.read_csv(R / "allocation_summary_base.csv")
print(a[["policy", "net_rs_per_q", "transport_rs_per_q", "avg_km", "runs_with_violation", "limit_violations",
         "excess_q", "split_lots", "gain_vs_P1_rs_per_q", "gain_vs_P1_rs_per_q_sd", "quantity_q"]].round(2).to_string(index=False))
a["waiting_rs_per_q"] = a.waiting_rs / a.quantity_q
print(a[["policy", "waiting_rs_per_q"]].round(2).to_string(index=False))
print("== sensitivity")
print(pd.read_csv(R / "allocation_sensitivity.csv").round(2).to_string(index=False))
runs = pd.read_csv(R / "allocation_runs_base.csv")
print("runs per policy", runs.groupby("policy").size().iloc[0], "origins", runs.origin.nunique(), "seeds", runs.seed.nunique())
