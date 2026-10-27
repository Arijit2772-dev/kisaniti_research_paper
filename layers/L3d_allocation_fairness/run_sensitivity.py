"""EXP-09b (L3d): how much do the findings depend on the two invented inputs, the transport rate and the mandi-day limit?

Repeats the policy comparison (without the weighted-sum policies) for a grid of transport rates and limits on the same
60 synthetic plans (10 seeds x 6 weeks). Writes results/L3d_allocation/allocation_sensitivity.csv and
allocation_sensitivity_summary.csv (key,value rows read by paper/numbers.py).

    env/run layers/L3d_allocation_fairness/run_sensitivity.py [--seeds 10] [--workers 6]
"""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal

import pandas as pd
from l3d_common import BASE, HARVEST_WEEKS, RESULTS
from run_policies import one, summarise

RATES = [Decimal("1"), Decimal("2"), Decimal("4")]  # Rs per quintal-km (DEMO range)
CAPS = [200, 300, 500]  # quintals per mandi-day (DEMO range)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    out = []
    with ProcessPoolExecutor(a.workers) as ex:
        for rate in RATES:
            for cap in CAPS:
                params = {**BASE, "rate": rate, "cap_q": cap}
                jobs = [(s, w, params, False) for s in range(a.seeds) for w in range(HARVEST_WEEKS)]
                df = pd.DataFrame([r for part in ex.map(one, jobs) for r in part])
                s = summarise(df).set_index("policy_key")
                p1 = s.loc["p1_nearest"]
                for key in ("p1_nearest", "p2_independent", "utilitarian", "maxmin", "greedy", "kisaniti"):
                    r = s.loc[key]
                    out.append({"rate_rs_per_q_km": float(rate), "cap_q_per_mandi_day": cap, "policy_key": key, "plans": int(r.runs),
                                "all_valid_pct": r.all_valid_pct, "net_rs_per_q": r.net_rs_per_q, "min_fulfilment_pct": r.min_fulfilment_pct,
                                "gini_fulfilment": r.gini_fulfilment, "price_of_fairness_rs_per_q": r.price_of_fairness_rs_per_q,
                                "gain_vs_p1_rs_per_q": r.gain_vs_p1_actual_rs_per_q, "allocated_pct": r.allocated_pct,
                                "p1_min_fulfilment_pct": p1.min_fulfilment_pct})
                print("done", rate, cap, flush=True)
    df = pd.DataFrame(out).round(4)
    df.to_csv(RESULTS / "allocation_sensitivity.csv", index=False)
    k = df[df.policy_key == "kisaniti"]
    g = k.set_index(["rate_rs_per_q_km", "cap_q_per_mandi_day"])
    rows = {
        "settings": len(g),
        "kis_min_fulfilment_min": g.min_fulfilment_pct.min(), "kis_min_fulfilment_max": g.min_fulfilment_pct.max(),
        "kis_gain_vs_p1_min": g.gain_vs_p1_rs_per_q.min(), "kis_gain_vs_p1_max": g.gain_vs_p1_rs_per_q.max(),
        "kis_pof_min": g.price_of_fairness_rs_per_q.min(), "kis_pof_max": g.price_of_fairness_rs_per_q.max(),
        "p1_min_fulfilment_max": g.p1_min_fulfilment_pct.max(),
        "kis_always_valid": int((g.all_valid_pct == 100).all()),
    }
    with (RESULTS / "allocation_sensitivity_summary.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["key", "value"])
        for key, v in rows.items():
            w.writerow([key, f"{v:.2f}" if isinstance(v, float) else v])
    print(df.to_string())


if __name__ == "__main__":
    main()
