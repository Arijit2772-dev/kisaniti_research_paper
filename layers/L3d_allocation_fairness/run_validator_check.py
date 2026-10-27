"""EXP-08c (L3d, stage 3 of the product): does the independent plan validator accept exactly the plans that satisfy the
hard rules? Random instances are solved, then each solution is edited the way a manager (or a mistake) could edit it:
moves that keep the plan valid and moves that break exactly one rule. A second checker written here from the rules
(plain integers, no import of the validator) gives the expected verdict; the two are compared on every edit.
Writes results/L3d_allocation/validator_agreement.json.

    env/run layers/L3d_allocation_fairness/run_validator_check.py [--instances 300]
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from kisaniti_core.allocation import AllocationMode, MarketLoad, solve, validate_plan
from kisaniti_core.allocation.fixtures import random_instance
from kisaniti_core.allocation.model import Assignment, Plan
from kisaniti_core.quantity import Quantity

RESULTS = Path(__file__).resolve().parents[2] / "results" / "L3d_allocation"


def expected_valid(inp, rows: list[tuple[str, str, object, int]]) -> bool:
    """The hard rules, from the written specification: admissible choice, no duplicate, positive whole increments,
    lot total within the lot (equal to it in FULL mode), mandi-day load within the limit when the limit is strict."""
    admissible = {(c.lot_id, c.mandi_id, c.date) for c in inp.choices}
    lots = {lot.id: lot for lot in inp.lots}
    seen, per_lot, load = set(), defaultdict(int), defaultdict(int)
    for lot_id, mandi, day, grams in rows:
        if lot_id not in lots or (lot_id, mandi, day) not in admissible or (lot_id, mandi, day) in seen:
            return False
        seen.add((lot_id, mandi, day))
        inc = lots[lot_id].increment.units
        if grams <= 0 or grams % inc:
            return False
        per_lot[lot_id] += grams
        load[(mandi, day)] += grams
    for lot_id, total in per_lot.items():
        if total > lots[lot_id].quantity.units:
            return False
    if inp.allocation_mode is AllocationMode.FULL and any(per_lot[lot.id] != lot.quantity.units for lot in inp.lots):
        return False
    if inp.market_load is MarketLoad.STRICT and any(v > inp.capacities[k].units for k, v in load.items() if k in inp.capacities):
        return False
    return True


def edits(inp, base: list[tuple[str, str, object, int]], rng: random.Random):
    """Yield (kind, rows). 'valid-*' edits are meant to keep the plan valid when the instance allows it; the rest break one rule."""
    lots = {lot.id: lot for lot in inp.lots}
    admissible = sorted({(c.lot_id, c.mandi_id, c.date) for c in inp.choices})
    yield "unchanged", list(base)
    if base:
        i = rng.randrange(len(base))
        lot_id, mandi, day, g = base[i]
        inc = lots[lot_id].increment.units
        yield "drop-a-line", base[:i] + base[i + 1:]
        yield "zero-quantity", base[:i] + [(lot_id, mandi, day, 0)] + base[i + 1:]
        yield "half-increment", base[:i] + [(lot_id, mandi, day, g + inc // 2)] + base[i + 1:]
        yield "one-increment-more", base[:i] + [(lot_id, mandi, day, g + inc)] + base[i + 1:]
        yield "duplicate-line", base + [base[i]]
        others = [k for k in admissible if k[0] == lot_id and (k[1], k[2]) != (mandi, day)]
        if others:
            k = rng.choice(others)
            yield "move-whole-line", base[:i] + [(lot_id, k[1], k[2], g)] + base[i + 1:]
    outside = [(lot.id, m, d) for lot in inp.lots for m in {c.mandi_id for c in inp.choices} for d in {c.date for c in inp.choices} if (lot.id, m, d) not in set(admissible)]
    if outside and base:
        k = rng.choice(outside)
        yield "inadmissible-choice", base + [(k[0], k[1], k[2], lots[k[0]].increment.units)]
    lot = rng.choice(inp.lots)
    yield "over-allocate-a-lot", base + [(lot.id, *rng.choice(admissible)[1:], lot.quantity.units + lot.increment.units)] if admissible else base


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", type=int, default=300)
    n_inst = ap.parse_args().instances
    rng = random.Random(8)
    kinds: Counter = Counter()
    agree: Counter = Counter()
    verdict_valid = 0
    total = 0
    for seed in range(n_inst):
        mode = AllocationMode.FULL if seed % 5 == 0 else AllocationMode.PARTIAL
        strict = seed % 4 != 0
        inp = random_instance(seed, rng.randint(2, 6), rng.randint(3, 8), rng.randint(2, 4), rng.randint(2, 4), density=0.6, max_increments=3,
                              mode=mode, strict=strict, capacity_share=1.6 if mode is AllocationMode.FULL else 0.6)
        rep = solve(inp, time_limit=30)
        base_plan = rep.plan if rep.plan is not None else Plan(())
        base = [(a.lot_id, a.mandi_id, a.date, a.quantity.units) for a in base_plan.assignments]
        for kind, rows in edits(inp, base, rng):
            plan = Plan(tuple(Assignment(l, m, d, Quantity(g)) for l, m, d, g in rows)) if all(g >= 0 for *_, g in rows) else None
            if plan is None:
                continue
            want = expected_valid(inp, rows)
            got = validate_plan(inp, plan).valid
            total += 1
            kinds[kind] += 1
            agree[kind] += int(want == got)
            verdict_valid += int(want)
    doc = {"instances": n_inst, "edits": total, "agree": sum(agree.values()), "expected_valid": verdict_valid, "expected_invalid": total - verdict_valid,
           "by_kind": {k: {"edits": kinds[k], "agree": agree[k]} for k in sorted(kinds)}}
    (RESULTS / "validator_agreement.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps(doc, indent=2))


if __name__ == "__main__":
    main()
