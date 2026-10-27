"""EXP-09 (L3d): compare selling policies on weekly plans of the SYNTHETIC 300-member Patiala persona, scored
at REAL 2025 AGMARKNET paddy prices. Writes results/L3d_allocation/allocation_policies_{runs,summary}.csv.

    env/run layers/L3d_allocation_fairness/run_policies.py [--seeds 10] [--workers 6]
"""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction

import pandas as pd
from kisaniti_core.allocation import Hierarchy, Weights, solve, solve_greedy, validate_plan

from l3d_common import BASE, HARVEST_WEEKS, RESULTS, build_instance, independent_best, make_persona, mandi_coords, \
    nearest_fcfs, price_panel, score

WEIGHT_SETS = {  # weighted-sum alternative from DESIGN_ALTERNATIVES.md (normalised terms)
    "ws_profit": Weights(Fraction(60, 100), Fraction(25, 100), Fraction(15, 100)),
    "ws_equal": Weights(Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)),
    "ws_fair": Weights(Fraction(15, 100), Fraction(25, 100), Fraction(60, 100)),
}
LABELS = {
    "p1_nearest": "P1 Nearest mandi, first free day",
    "p2_independent": "P2 Independent best choice",
    "utilitarian": "Utilitarian (max net return)",
    "maxmin": "Max-min fulfilment only",
    "ws_profit": "Weighted sum 0.60/0.25/0.15",
    "ws_equal": "Weighted sum 1/3 each",
    "ws_fair": "Weighted sum 0.15/0.25/0.60",
    "greedy": "Greedy water-filling heuristic",
    "kisaniti": "KisanNiti leximin hierarchy",
    "perfect_foresight": "KisanNiti with actual prices (bound)",
}


def one(args: tuple[int, int, dict, bool]) -> list[dict]:
    seed, week, params, with_weighted = args
    dates, prices = price_panel()
    coords = mandi_coords()
    persona = make_persona(seed)
    inst = build_instance(persona, week, dates, prices, coords, rate=params["rate"], wait=params["wait"],
                          cap_q=params["cap_q"], seed=seed)
    rows = []

    def record(key: str, plan, seconds: float, status: str = "COMPLETED") -> None:
        v = validate_plan(inst.inp, plan)
        rows.append({"seed": seed, "week": week, "origin": inst.origin.isoformat(), "policy_key": key,
                     "policy": LABELS[key], "status": status, "valid": v.valid, "seconds": seconds,
                     "rate": float(params["rate"]), "cap_q": params["cap_q"], **score(inst, plan)})

    t = time.perf_counter(); record("p1_nearest", nearest_fcfs(inst, 1000 + 7 * seed + week), time.perf_counter() - t)
    t = time.perf_counter(); record("p2_independent", independent_best(inst), time.perf_counter() - t)
    t = time.perf_counter(); record("greedy", solve_greedy(inst.inp), time.perf_counter() - t)
    for key, h in (("utilitarian", Hierarchy.UTILITARIAN), ("maxmin", Hierarchy.MAXMIN), ("kisaniti", Hierarchy.KISANITI)):
        t = time.perf_counter(); r = solve(inst.inp, hierarchy=h, time_limit=300)
        record(key, r.plan, time.perf_counter() - t, f"{r.termination}/{r.optimality}")
    for key, w in WEIGHT_SETS.items() if with_weighted else []:
        t = time.perf_counter(); r = solve(inst.inp, hierarchy=Hierarchy.WEIGHTED, weights=w, time_limit=300)
        record(key, r.plan, time.perf_counter() - t, f"{r.termination}/{r.optimality}")
    pf = build_instance(persona, week, dates, prices, coords, rate=params["rate"], wait=params["wait"],
                        cap_q=params["cap_q"], seed=seed, planning="actual")
    t = time.perf_counter(); r = solve(pf.inp, hierarchy=Hierarchy.KISANITI, time_limit=300)
    record("perfect_foresight", r.plan, time.perf_counter() - t, f"{r.termination}/{r.optimality}")
    return rows


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df.policy_key == "utilitarian"].set_index(["seed", "week"])
    p1 = df[df.policy_key == "p1_nearest"].set_index(["seed", "week"])
    kis = df[df.policy_key == "kisaniti"].set_index(["seed", "week"])
    out = []
    for key in LABELS:
        if key not in set(df.policy_key):
            continue
        d = df[df.policy_key == key].set_index(["seed", "week"])
        pof = (base.expected_net_rs - d.expected_net_rs) / d.allocated_q
        gain = (d.actual_net_rs - p1.actual_net_rs) / d.allocated_q
        out.append({
            "policy_key": key, "policy": LABELS[key], "runs": len(d), "all_valid_pct": 100 * d.valid.mean(),
            "runs_with_violation_pct": 100 * (d.limit_violations > 0).mean(),
            "allocated_pct": d.allocated_pct.mean(), "net_rs_per_q": d.actual_net_rs_per_q.mean(),
            "expected_net_rs_per_q": d.expected_net_rs_per_q.mean(),
            "min_fulfilment_pct": d.min_fulfilment_pct.mean(), "p10_fulfilment_pct": d.p10_fulfilment_pct.mean(),
            "zero_fulfilment_farmers": d.zero_fulfilment_farmers.mean(), "gini_fulfilment": d.gini_fulfilment.mean(),
            "high_storage_first_date_pct": d.high_storage_first_date_pct.mean(), "avg_km": d.avg_km.mean(),
            "price_of_fairness_rs_per_q": pof.mean(), "price_of_fairness_rs_per_q_max": pof.max(),
            "gain_vs_p1_actual_rs_per_q": gain.mean(), "gain_vs_p1_actual_rs_per_q_sd": gain.std(),
            "min_fulfilment_below_kisaniti_runs_pct": 100 * (d.min_fulfilment_pct < kis.min_fulfilment_pct - 1e-9).mean(),
            "seconds_mean": d.seconds.mean(), "seconds_max": d.seconds.max(),
        })
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--skip-weighted", action="store_true",
                    help="leave out the three weighted-sum policies (each runs to the 300 s limit; open decision E.0)")
    ap.add_argument("--tag", default="", help="suffix of the result file names, e.g. _no_weighted")
    a = ap.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    params = dict(BASE)
    jobs = [(s, w, params, not a.skip_weighted) for s in range(a.seeds) for w in range(HARVEST_WEEKS)]
    with ProcessPoolExecutor(a.workers) as ex:
        rows = [r for part in ex.map(one, jobs) for r in part]
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / f"allocation_policies_runs{a.tag}.csv", index=False)
    s = summarise(df)
    s.round(4).to_csv(RESULTS / f"allocation_policies_summary{a.tag}.csv", index=False)
    print(s[["policy_key", "allocated_pct", "net_rs_per_q", "min_fulfilment_pct", "gini_fulfilment",
             "price_of_fairness_rs_per_q", "runs_with_violation_pct", "seconds_mean"]].round(3).to_string(index=False))
    print(json.dumps({"runs": len(df), "statuses": df.status.value_counts().to_dict()}, indent=1))


if __name__ == "__main__":
    main()
