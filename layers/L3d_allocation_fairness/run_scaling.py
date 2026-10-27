"""EXP-08b (L3d): how large an FPO can each solver handle? Random instances of growing size (farmers = lots,
5 to 25 mandis, 3 to 14 dates) solved by the three back ends and the greedy heuristic with a 60 s limit; three seeds
per size. Writes results/L3d_allocation/allocation_scaling.csv and allocation_scaling_summary.csv (key,value).
Run on an otherwise idle machine: the timings are the result.

    env/run layers/L3d_allocation_fairness/run_scaling.py
"""

from __future__ import annotations

import csv
import statistics
import time
from pathlib import Path

from kisaniti_core.allocation import solve, solve_greedy, validate_plan
from kisaniti_core.allocation.fixtures import random_instance

RESULTS = Path(__file__).resolve().parents[2] / "results" / "L3d_allocation"
SIZES = [(10, 3, 3), (30, 5, 5), (100, 8, 7), (300, 12, 10), (1000, 25, 14)]  # (farmers = lots, mandis, dates)
BACKENDS = ["highs", "scip", "cpsat"]
LIMIT = 60.0


def main() -> None:
    rows = []
    for farmers, mandis, dates in SIZES:
        for seed in range(3):
            t = time.perf_counter()
            inp = random_instance(seed, farmers, farmers, mandis, dates, density=0.5, max_increments=6, capacity_share=0.6)
            build = time.perf_counter() - t
            t = time.perf_counter()
            g = solve_greedy(inp)
            rows.append({"farmers": farmers, "mandis": mandis, "dates": dates, "seed": seed, "solver": "greedy", "build_s": round(build, 3),
                         "solve_s": round(time.perf_counter() - t, 3), "status": "HEURISTIC", "valid": validate_plan(inp, g).valid})
            for b in BACKENDS:
                t = time.perf_counter()
                rep = solve(inp, backend=b, time_limit=LIMIT)
                sec = time.perf_counter() - t
                rows.append({"farmers": farmers, "mandis": mandis, "dates": dates, "seed": seed, "solver": b, "build_s": round(build, 3),
                             "solve_s": round(sec, 3), "status": f"{rep.termination}/{rep.optimality}",
                             "valid": bool(rep.plan is not None and validate_plan(inp, rep.plan).valid)})
                print(farmers, seed, b, rows[-1]["solve_s"], rows[-1]["status"], flush=True)
    with (RESULTS / "allocation_scaling.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    summary: dict[str, str] = {"time_limit_s": f"{LIMIT:.0f}"}
    for solver in ["greedy", *BACKENDS]:
        for farmers, _, _ in SIZES:
            sel = [r for r in rows if r["solver"] == solver and r["farmers"] == farmers]
            summary[f"{solver}_{farmers}_median_s"] = f"{statistics.median(r['solve_s'] for r in sel):.2f}"
            summary[f"{solver}_{farmers}_proven"] = str(sum(r["status"].endswith("PROVEN_OPTIMAL") for r in sel)) + f"/{len(sel)}"
    summary["all_valid"] = str(all(r["valid"] for r in rows))
    with (RESULTS / "allocation_scaling_summary.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["key", "value"])
        w.writerows(sorted(summary.items()))


if __name__ == "__main__":
    main()
