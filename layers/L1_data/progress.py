"""Show which Paddy(Basmati) months are filed and which is next.

Usage:  python3 layers/L1_data/progress.py

Reads download_log.csv (the source of truth) and compares it with the target list
in DOWNLOAD_RUNBOOK.md: Sep-Jan of the 2021-22, 2022-23 and 2023-24 seasons,
the already planned later months, and 2025-06 as the off-season test.
"""

import csv
from pathlib import Path

LOG = Path(__file__).with_name("download_log.csv")

TARGET = (
    ["2023-09", "2023-10", "2023-11", "2023-12", "2024-01"]
    + ["2022-09", "2022-10", "2022-11", "2022-12", "2023-01"]
    + ["2021-09", "2021-10", "2021-11", "2021-12", "2022-01"]
    + ["2025-06"]
)
# Months the site reported as empty; they count as done (see data/manifests/*_NO_DATA.json)
CHECKED_EMPTY = {"2025-06"}


def main() -> None:
    filed = {}
    with LOG.open() as handle:
        for row in csv.DictReader(handle):
            if row["commodity"] == "Paddy(Basmati)":
                filed[row["month"]] = (int(row["rows"]), int(row["markets"]))

    print(f"Paddy(Basmati) months filed: {len(filed)}")
    for month in sorted(filed):
        rows, markets = filed[month]
        print(f"  {month}: {rows} rows, {markets} markets")

    missing = [m for m in TARGET if m not in filed and m not in CHECKED_EMPTY]
    if CHECKED_EMPTY:
        print(f"Checked, site reports no data: {', '.join(sorted(CHECKED_EMPTY))}")
    print(f"\nStill to download ({len(missing)}): {', '.join(missing) if missing else 'none'}")
    if missing:
        print(f"NEXT: {missing[0]}  (Paddy(Basmati), Punjab)")


if __name__ == "__main__":
    main()
