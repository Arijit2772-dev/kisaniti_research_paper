"""Audit: the optimiser against the brute-force oracle on instances that were never used before (seeds 90000 and up),
slightly larger shapes than the main experiment, plus the validator on the optimiser's own plans.

    env/run scripts/audit_optimizer_fresh_seeds.py     writes results/audit/optimizer_fresh_seeds.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from kisaniti_core.allocation import AllocationMode, solve, solve_oracle, validate_plan
from kisaniti_core.allocation.fixtures import random_instance
from kisaniti_core.allocation.oracle import TooLarge

OUT = Path(__file__).resolve().parents[1] / "results" / "audit"


def main() -> int:
    shapes = []
    for s in range(40):
        shapes.append((90000 + s, 3, 4, 2, 3, 0.6, 2, AllocationMode.PARTIAL, True, s % 2 == 0))
        shapes.append((91000 + s, 4, 4, 2, 2, 0.5, 2, AllocationMode.PARTIAL, True, True))
        shapes.append((92000 + s, 3, 3, 2, 3, 0.8, 2, AllocationMode.FULL, True, False))
    cases = agree = skipped = infeasible = 0
    bad = []
    for seed, f, lots, m, d, dens, mi, mode, strict, ties in shapes:
        share = 1.6 if mode is AllocationMode.FULL else 0.6
        inp = random_instance(seed, f, lots, m, d, density=dens, max_increments=mi, mode=mode, strict=strict, ties=ties, capacity_share=share)
        try:
            ref = solve_oracle(inp, max_plans=400_000)
            inf = False
        except TooLarge:
            skipped += 1
            continue
        except ValueError:
            ref, inf = None, True
            infeasible += 1
        for backend in ("highs", "scip", "cpsat"):
            rep = solve(inp, backend=backend, time_limit=60, leximin_method="auto")
            cases += 1
            if inf:
                ok = rep.termination == "PROVEN_INFEASIBLE" and rep.plan is None
            else:
                ok = (rep.termination == "COMPLETED" and rep.optimality == "PROVEN_OPTIMAL" and rep.plan is not None
                      and rep.objective is not None and rep.objective.key() == ref.best.key() and validate_plan(inp, rep.plan).valid)
            agree += ok
            if not ok:
                bad.append({"seed": seed, "backend": backend})
    doc = {"instances_tried": len(shapes), "instances_too_large_for_oracle": skipped, "infeasible": infeasible,
           "solver_runs": cases, "agree": agree, "disagreements": bad}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "optimizer_fresh_seeds.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps(doc, indent=2))
    return 0 if agree == cases and cases > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
