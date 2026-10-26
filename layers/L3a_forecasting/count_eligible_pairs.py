"""C.0 helper: pair counts after the section 3 eligibility rule (an origin needs 10 index days of its season).

Usage:  env/run layers/L3a_forecasting/count_eligible_pairs.py
Needs:  data/processed/basmati/index_<variant>.csv
Writes: results/C0_protocol/eligible_pairs.csv

Reads only the date, season and variety columns. No price value is read and no model is run, so this does not look
at forecast performance. count_horizon_pairs.py counts pairs without the eligibility rule; this file shows how many
of them remain.
"""

import csv
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evalkit as ek  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "basmati"
OUT = ROOT / "results" / "C0_protocol" / "eligible_pairs.csv"
HORIZONS = (1, 7, 14, 28, 60)
SEASONS = ("2021-22", "2022-23", "2023-24", "2024-25", "2025-26", "2026-27")


def main() -> None:
    out = []
    for variant in ("dated_only", "with_blank"):
        with open(DATA / f"index_{variant}.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for variety in ("1121", "Basmati 1509"):
            s = [ek.Obs(date.fromisoformat(r["date"]), r["season"], 0.0) for r in rows if r["variety"] == variety]
            for h in HORIZONS:
                row = {"variant": variant, "variety": variety, "horizon_days": h}
                for season in SEASONS:
                    row[season + " raw"] = len(ek.raw_pairs(s, h, season))
                    row[season + " eligible"] = len(ek.eligible_pairs(s, h, season))
                out.append(row)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    for r in out:
        if r["variant"] == "dated_only":
            print(r["variety"], r["horizon_days"], "test season 2025-26: raw", r["2025-26 raw"], "eligible", r["2025-26 eligible"])


if __name__ == "__main__":
    main()
