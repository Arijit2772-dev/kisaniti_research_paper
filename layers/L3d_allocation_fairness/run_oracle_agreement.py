"""EXP-08 (L3d): does the optimizer reach exactly the optimum that a brute-force enumeration finds?

Random tiny instances (the shapes of the product's test T30, with 6x as many seeds) are solved by every backend and
leximin method and compared with the oracle on the complete lexicographic objective tuple. Infeasible FULL-mode
instances must be reported as proven infeasible. Writes results/L3d_allocation/oracle_agreement.json and
oracle_agreement_cases.csv.

    env/run layers/L3d_allocation_fairness/run_oracle_agreement.py [--seeds-per-shape 6]
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

from kisaniti_core.allocation import AllocationMode, solve, solve_oracle, validate_plan
from kisaniti_core.allocation.fixtures import random_instance
from kisaniti_core.allocation.oracle import TooLarge

RESULTS = Path(__file__).resolve().parents[2] / "results" / "L3d_allocation"
BACKENDS = ["highs", "scip", "cpsat"]


def shapes(k: int):
    # (seed, farmers, lots, mandis, dates, density, max_increments, mode, strict, ties)
    for s in range(12 * k):
        yield (s, 2, 3, 2, 2, 0.7, 2, AllocationMode.PARTIAL, True, False)
        yield (1000 + s, 3, 4, 2, 2, 0.5, 2, AllocationMode.PARTIAL, True, s % 2 == 0)
        yield (2000 + s, 2, 2, 3, 3, 0.4, 2, AllocationMode.PARTIAL, True, True)
        yield (3000 + s, 3, 3, 1, 3, 0.8, 3, AllocationMode.FULL, True, False)
    for s in range(6 * k):
        yield (4000 + s, 2, 3, 2, 2, 0.6, 2, AllocationMode.PARTIAL, False, True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds-per-shape", type=int, default=6)
    k = ap.parse_args().seeds_per_shape
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for seed, f, lots, m, d, dens, mi, mode, strict, ties in shapes(k):
        share = 1.6 if mode is AllocationMode.FULL else 0.6
        inp = random_instance(seed, f, lots, m, d, density=dens, max_increments=mi, mode=mode, strict=strict, ties=ties, capacity_share=share)
        try:
            ref = solve_oracle(inp, max_plans=400_000)
            infeasible = False
        except TooLarge:
            continue
        except ValueError:
            ref, infeasible = None, True
        for backend in BACKENDS:
            for method in ("flow", "milp"):
                if method == "flow" and mode is AllocationMode.FULL:
                    continue  # flow leximin applies to PARTIAL mode; FULL uses the automatic choice, run once as "milp"
                use = method if mode is AllocationMode.PARTIAL else "auto"
                t = time.perf_counter()
                rep = solve(inp, backend=backend, time_limit=60, leximin_method=use)
                sec = time.perf_counter() - t
                if infeasible:
                    ok = rep.termination == "PROVEN_INFEASIBLE" and rep.plan is None
                else:
                    ok = (rep.termination == "COMPLETED" and rep.optimality == "PROVEN_OPTIMAL" and rep.plan is not None
                          and rep.objective is not None and rep.objective.key() == ref.best.key() and validate_plan(inp, rep.plan).valid)
                rows.append({"seed": seed, "mode": mode.name, "backend": backend, "method": method, "oracle_infeasible": infeasible,
                             "plans_enumerated": 0 if ref is None else ref.plans_enumerated, "agree": ok, "seconds": round(sec, 4)})
    with (RESULTS / "oracle_agreement_cases.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    by: dict[str, dict[str, float]] = {}
    for b in BACKENDS:
        r = [x for x in rows if x["backend"] == b]
        by[b] = {"cases": len(r), "agree": sum(x["agree"] for x in r), "seconds_mean": round(sum(x["seconds"] for x in r) / len(r), 4)}
    doc = {"cases": len(rows), "agree": sum(x["agree"] for x in rows), "instances": len({x["seed"] for x in rows}),
           "infeasible_instances": len({x["seed"] for x in rows if x["oracle_infeasible"]}), "by_solver": by}
    (RESULTS / "oracle_agreement.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps(doc, indent=2))


if __name__ == "__main__":
    main()
