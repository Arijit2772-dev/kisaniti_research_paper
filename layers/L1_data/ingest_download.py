"""File one AGMARKNET "Date Wise Prices for Specified Commodity" CSV export.

Usage:
    python3 layers/L1_data/ingest_download.py [--copy] [--provenance TEXT] [export.csv ...]

Without a path, the newest Date_wise_Prices_for_Specified_Commodity_*.csv in
~/Downloads is used. Several paths can be given. Re-filing a month whose bytes
already match is a no-op; different bytes are refused. The file is moved (or
copied with --copy) unchanged into
data/raw/agmarknet/<commodity>/<YYYY-MM>_<state>.csv, and a manifest JSON is
written to data/manifests/. The month, commodity and state are read from the
report's own title line, never guessed from the file name.
"""

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "agmarknet"
MANIFESTS = ROOT / "data" / "manifests"
LOG = ROOT / "layers" / "L1_data" / "download_log.csv"
DOWNLOADS = Path.home() / "Downloads"

TITLE = re.compile(
    r"Date Wise Prices for Specified Commodity on (?P<month>[A-Za-z]+), (?P<year>\d{4}) "
    r"for Commodity : (?P<commodity>.+?), State/UT : (?P<state>.+?)\"?\s*$"
)
HEADER = [
    "Arrival Date", "Arrivals (Metric Tonnes)", "Variety",
    "Minimum Price (Rs./Quintal)", "Maximum Price (Rs./Quintal)", "Modal Price (Rs./Quintal)",
]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def summarise(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    match = TITLE.match(lines[0].strip().strip('"') + '"') or TITLE.match(lines[0].strip())
    if not match:
        sys.exit(f"Unexpected title line, not a date-wise report: {lines[0]!r}")
    month = datetime.strptime(f"{match['month']} {match['year']}", "%B %Y")

    header_index = next((i for i, line in enumerate(lines) if line.startswith("Arrival Date,")), None)
    if header_index is None:
        sys.exit("Column header not found")
    header = next(csv.reader([lines[header_index]]))
    if header != HEADER:
        sys.exit(f"Column header changed: {header}")

    markets, rows, dates, problems = set(), 0, [], []
    blank_date_rows = 0
    market = None
    for number, line in enumerate(lines[header_index + 1:], start=header_index + 2):
        if not line.strip() or not line.strip(","):
            continue
        if line.startswith("Market Name :"):
            market = line.split(":", 1)[1].strip().strip(",")
            markets.add(market)
            continue
        fields = next(csv.reader([line]))
        if len(fields) != 6 or market is None:
            problems.append(f"line {number}: {line[:80]}")
            continue
        if not fields[0].strip():
            # Blank date and arrivals: the website prints a second entry for the
            # previous date this way. Kept raw; Layer 2 decides how to treat it.
            blank_date_rows += 1
            continue
        day = datetime.strptime(fields[0], "%d/%m/%Y")
        if (day.year, day.month) != (month.year, month.month):
            problems.append(f"line {number}: date {fields[0]} outside report month")
        dates.append(day)
        rows += 1

    return {
        "commodity": match["commodity"].strip(),
        "state": match["state"].strip().strip('"'),
        "month": month.strftime("%Y-%m"),
        "rows": rows,
        "blank_date_rows": blank_date_rows,
        "markets": len(markets),
        "first_date": min(dates).strftime("%Y-%m-%d") if dates else None,
        "last_date": max(dates).strftime("%Y-%m-%d") if dates else None,
        "problems": problems,
    }


def file_one(source: Path, copy: bool, provenance: str) -> str:
    """File one export. Returns 'filed', 'already-filed' or exits on a conflict."""
    info = summarise(source)
    target_dir = RAW / slug(info["commodity"])
    target = target_dir / f"{info['month']}_{slug(info['state'])}.csv"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() == digest:
            print(f"Already filed (same bytes): {target.relative_to(ROOT)}")
            return "already-filed"
        sys.exit(f"CONFLICT: {target} exists with different bytes; not overwritten")

    target_dir.mkdir(parents=True, exist_ok=True)
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        target.unlink()
        sys.exit(f"Copy of {source.name} did not match its checksum; removed the bad copy")

    manifest = {
        "source": "AGMARKNET (agmarknet.gov.in), report 'Date Wise Prices for Specified Commodity', CSV export",
        "downloaded_by": provenance,
        "filed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "original_filename": source.name,
        "raw_path": str(target.relative_to(ROOT)),
        "sha256": digest,
        "bytes": target.stat().st_size,
        "origin": "REAL",
        **info,
    }
    manifest_path = MANIFESTS / f"agmarknet_{slug(info['commodity'])}_{info['month']}_{slug(info['state'])}.json"
    manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")

    new_log = not LOG.exists()
    with LOG.open("a", newline="") as handle:
        writer = csv.writer(handle)
        if new_log:
            writer.writerow(["month", "commodity", "state", "rows", "blank_date_rows", "markets", "first_date", "last_date",
                             "problems", "sha256", "filed_at_utc"])
        writer.writerow([info["month"], info["commodity"], info["state"], info["rows"], info["blank_date_rows"], info["markets"],
                         info["first_date"], info["last_date"], len(info["problems"]), digest[:16],
                         manifest["filed_at_utc"]])
    if not copy:
        source.unlink()

    print(f"Filed {target.relative_to(ROOT)}: {info['rows']} rows (+{info['blank_date_rows']} blank-date), {info['markets']} markets, "
          f"{info['first_date']} to {info['last_date']}, problems: {len(info['problems'])}")
    for problem in info["problems"][:10]:
        print("  ", problem)
    return "filed"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", help="export CSV file(s); default: newest in ~/Downloads")
    parser.add_argument("--copy", action="store_true", help="keep the original file instead of moving it")
    parser.add_argument("--provenance", default="user (CAPTCHA entered by the user in a browser)",
                        help="who/what downloaded the file, recorded in the manifest")
    args = parser.parse_args()

    if args.paths:
        sources = [Path(p).expanduser() for p in args.paths]
    else:
        candidates = sorted(DOWNLOADS.glob("Date_wise_Prices_for_Specified_Commodity_*.csv"),
                            key=lambda p: p.stat().st_mtime)
        if not candidates:
            sys.exit("No AGMARKNET export found in ~/Downloads")
        sources = [candidates[-1]]
    for source in sources:
        file_one(source, args.copy, args.provenance)


if __name__ == "__main__":
    main()
