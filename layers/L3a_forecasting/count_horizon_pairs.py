"""C.0 helper: how many (origin, target) pairs exist per calendar horizon in the variety index?

Usage:  python3 -I layers/L3a_forecasting/count_horizon_pairs.py
Needs:  data/processed/basmati/index_<variant>.csv (run layers/L2_cleaning/build_index.py)
Writes: results/C0_protocol/horizon_pairs.csv

A pair needs an index value on the origin day and on exactly origin + h calendar days, in the
same season. No filling, no nearest-day matching. Counts only; no model is run and no price
error is computed, so this does not look at forecast performance.
"""
import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "basmati"
OUT = ROOT / "results" / "C0_protocol"
HORIZONS = (1, 2, 3, 5, 7, 10, 14, 21, 28, 30, 45, 60, 90, 120)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows_out = []
    for variant in ("dated_only", "with_blank"):
        with open(DATA / f"index_{variant}.csv", newline="", encoding="utf-8") as f:
            idx = list(csv.DictReader(f))
        for variety in ("1121", "Basmati 1509"):
            days = defaultdict(set)
            for r in idx:
                if r["variety"] == variety:
                    days[r["season"]].add(date.fromisoformat(r["date"]))
            for h in HORIZONS:
                row = {"variant": variant, "variety": variety, "horizon_days": h}
                total = 0
                for season in sorted(days):
                    n = sum(1 for d in days[season] if d + timedelta(days=h) in days[season])
                    row[season] = n
                    total += n
                row["total"] = total
                rows_out.append(row)
    cols = ["variant", "variety", "horizon_days", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26", "2026-27", "total"]
    with open(OUT / "horizon_pairs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows_out)
    for r in rows_out:
        if r["variant"] == "dated_only":
            print(r["variety"], r["horizon_days"], [r[c] for c in cols[3:]])


if __name__ == "__main__":
    main()
