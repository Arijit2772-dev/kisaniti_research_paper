"""Independent re-derivation of the primary price index from the raw AGMARKNET files (second implementation).

It does not import the project's parser or index builder. It reads the 29 raw monthly files with the csv module, counts
every data row, and rebuilds the dated-only daily index from the stated definition (CLEANING_PLAN B.4): per variety and
day, the median modal price over the mandis that reported the variety that day, at least three mandis, a mandi-day with
two or more rows for the variety excluded, rows without a modal price skipped. Then it compares, exactly, with
data/processed/basmati/index_dated_only.csv and the row counts with results/L2_cleaning/reconciliation.csv.

    python3 -I scripts/audit_independent_index.py        (exit code 0 only if everything agrees)
"""

from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "agmarknet" / "paddy_basmati"
VARIETIES = ("1121", "Basmati 1509")


def main() -> int:
    rows = dated = blank = 0
    by_key: dict[tuple[str, str, str], list[float | None]] = defaultdict(list)
    files = sorted(RAW.glob("*.csv"))
    for f in files:
        market = None
        with f.open(newline="", encoding="utf-8") as fh:
            for rec in csv.reader(fh):
                if not rec or not any(c.strip() for c in rec):
                    continue
                first = rec[0].strip()
                if first.startswith("Market Name :"):
                    market = first.split(":", 1)[1].strip()
                    continue
                if len(rec) != 6 or first.startswith(("Arrival Date", "Date Wise", "Commodity")):
                    continue
                rows += 1
                if first == "":
                    blank += 1
                    continue
                dated += 1
                d, m, y = first.split("/")
                iso = date(int(y), int(m), int(d)).isoformat()
                modal = rec[5].strip()
                by_key[(iso, rec[2].strip(), market or "")].append(float(modal) if modal not in ("", "-") else None)
    per_day: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (iso, variety, _market), vals in by_key.items():
        if variety not in VARIETIES or len(vals) != 1 or vals[0] is None:
            continue
        per_day[(iso, variety)].append(vals[0])
    mine = {k: (statistics.median(v), len(v)) for k, v in per_day.items() if len(v) >= 3}

    ok = True
    rec = list(csv.DictReader((ROOT / "results/L2_cleaning/reconciliation.csv").open()))
    want = (sum(int(r["data_rows"]) for r in rec), sum(int(r["dated"]) for r in rec), sum(int(r["blank_date"]) for r in rec))
    print(f"raw files {len(files)}; rows {rows}, dated {dated}, blank-date {blank}; reconciliation says {want}")
    ok &= (rows, dated, blank) == want and len(files) == len(rec)

    theirs = {
        (r["date"], r["variety"]): (float(r["index_modal"]), int(r["n_mandis"]))
        for r in csv.DictReader((ROOT / "data/processed/basmati/index_dated_only.csv").open())
    }
    print(f"index days: independent {len(mine)}, project {len(theirs)}")
    diff = [k for k in set(mine) | set(theirs) if mine.get(k) != theirs.get(k)]
    print(f"index days that differ in presence, value or mandi count: {len(diff)}")
    for k in sorted(diff)[:10]:
        print("  ", k, mine.get(k), theirs.get(k))
    ok &= not diff
    print("INDEPENDENT INDEX AGREES" if ok else "DISAGREEMENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
