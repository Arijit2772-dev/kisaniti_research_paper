"""R0: copy the AGMARKNET Paddy (Common) files from the capstone folder into data/ and write manifests.

The source files are copied byte for byte (never edited). Each copy gets a JSON manifest in
data/manifests/ with its SHA-256, row count, date range and request scope. Re-running the script
checks that the copies still match the source; it never overwrites a copy whose checksum differs.

Usage: python scripts/import_capstone_paddy.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path.home() / "Documents" / "sem_6" / "capstone"
API = "https://api.agmarknet.gov.in/v1/prices-and-arrivals/date-wise/specific-commodity"

FILES = [
    {
        "name": "agmarknet_paddy_common_punjab.csv",
        "dest": "raw/agmarknet/paddy_common",
        "stage": "RAW",
        "description": "Flattened AGMARKNET API response, unchanged since download (capstone download_agmarknet_paddy.py).",
        "date_column": "arrival_date",
    },
    {
        "name": "agmarknet_paddy_common_punjab_cleaned_records.csv",
        "dest": "processed/agmarknet/paddy_common",
        "stage": "PROCESSED",
        "description": "Record-level cleaned rows (capstone clean_agmarknet_paddy.py: 81 exact duplicates removed, "
        "19 zero price bounds repaired, 2 market-date-variety duplicate groups aggregated). Input to paper v2.",
        "date_column": "arrival_date",
    },
    {
        "name": "agmarknet_paddy_common_punjab_daily_prices.csv",
        "dest": "processed/agmarknet/paddy_common",
        "stage": "PROCESSED",
        "description": "Punjab-wide arrival-weighted daily modal price on observed trading dates (capstone cleaning output).",
        "date_column": "arrival_date",
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe(path: Path, date_column: str) -> dict:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        dates = []
        markets = set()
        n = 0
        for row in reader:
            n += 1
            dates.append(row[date_column])
            if "market_name" in row:
                markets.add(row["market_name"])
    out = {"rows": n, "columns": columns, "date_min": min(dates), "date_max": max(dates)}
    if markets:
        out["distinct_markets"] = len(markets)
    return out


def main() -> int:
    manifests = ROOT / "data" / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    for spec in FILES:
        src = SRC / spec["name"]
        dest_dir = ROOT / "data" / spec["dest"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / spec["name"]
        src_hash = sha256(src)
        if dest.exists():
            if sha256(dest) != src_hash:
                print(f"ERROR: {dest} exists and differs from {src}; not overwritten", file=sys.stderr)
                return 1
        else:
            shutil.copy2(src, dest)
        assert sha256(dest) == src_hash
        manifest = {
            "manifest_version": 1,
            "file": str(dest.relative_to(ROOT)),
            "stage": spec["stage"],
            "origin": "REAL",
            "description": spec["description"],
            "source": {
                "provider": "AGMARKNET (Directorate of Marketing and Inspection, Government of India)",
                "endpoint": API,
                "request_scope": {
                    "state": "Punjab (stateId=28)",
                    "commodity": "Paddy(Common) (commodityId=2)",
                    "variety": "all varieties returned",
                    "years": "2020-2025",
                    "months": "September-December",
                },
                "downloaded_by": "Arijit Singh (capstone project, download_agmarknet_paddy.py)",
                "downloaded_on": "2026-04-20 (file modification time of the raw CSV; exact request time not logged)",
                "terms": "Public market information published by AGMARKNET; check the portal terms before redistribution. "
                "Data files are not committed to git.",
            },
            "copied_from": str(src),
            "copied_on": date.today().isoformat(),
            "sha256": src_hash,
            "bytes": dest.stat().st_size,
            **describe(dest, spec["date_column"]),
        }
        out = manifests / (spec["name"].removesuffix(".csv") + ".manifest.json")
        out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"{spec['name']}: {manifest['rows']} rows, {manifest['date_min']}..{manifest['date_max']}, sha256 {src_hash[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
