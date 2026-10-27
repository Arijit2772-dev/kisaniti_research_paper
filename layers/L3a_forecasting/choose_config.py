"""Picks the hyperparameters used in the test season (protocol section 13, item 13): per tuned family, variety and
horizon the variant with the lowest validation-season MAE, ties to the first in grid order. Reads
results/C0_protocol/validation_metrics.csv and writes config/chosen.json. Run once, after the validation run and before the
configuration freeze; it refuses if a variant is missing for any variety and horizon.

    env/run layers/L3a_forecasting/choose_config.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "results" / "C0_protocol"


def choose(rows: list[dict[str, str]], grids: dict) -> dict[str, dict[str, dict[str, str]]]:
    chosen: dict[str, dict[str, dict[str, str]]] = {}
    for fam, key in (("lightgbm", lambda g: f"lightgbm@nl{g['num_leaves']}_n{g['n_estimators']}"), ("gru", lambda g: f"gru@h{g['hidden']}_e{g['epochs']}")):
        order = [key(g) for g in grids[fam]]
        for variety in sorted({r["variety"] for r in rows}):
            for h in sorted({int(r["horizon"]) for r in rows}):
                got = {r["config"]: float(r["mae"]) for r in rows if r["variety"] == variety and int(r["horizon"]) == h and r["model"] == fam}
                missing = [v for v in order if v not in got]
                if len(missing) == len(order):
                    continue  # no variant could forecast here (too few training pairs): the family is not forecast for this cell
                if missing:
                    raise SystemExit(f"validation results missing for {fam} {variety} h={h}: {missing}")
                best = min(order, key=lambda v: (got[v], order.index(v)))
                chosen.setdefault(fam, {}).setdefault(variety, {})[str(h)] = best
    return chosen


def main() -> None:
    rows = list(csv.DictReader((OUT / "validation_metrics.csv").open()))
    chosen = choose(rows, json.loads((HERE / "config" / "grids.json").read_text()))
    (HERE / "config" / "chosen.json").write_text(json.dumps(chosen, indent=2) + "\n")
    print(json.dumps(chosen, indent=2))


if __name__ == "__main__":
    main()
