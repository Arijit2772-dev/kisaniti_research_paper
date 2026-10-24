"""B.1 tidy parser for the Paddy(Basmati) Punjab AGMARKNET files, with exact row tracing.

Usage:  python3 -I layers/L2_cleaning/parse_basmati.py

Reads data/raw/agmarknet/paddy_basmati/*.csv (never modified) and writes:
  data/processed/basmati/basmati_tidy.csv           one line per source data row (git-ignored)
  results/L2_cleaning/reconciliation.csv            per file: every source row accounted for
  results/L2_cleaning/flag_counts.csv               rows per mechanical flag
  results/L2_cleaning/parse_summary.md              totals, written by this script

Nothing is deleted or corrected here. Every source data row appears exactly once in the
tidy table with its file and line number; rules only add flags. Statistical outlier
screens are NOT in this file: their choice is open until the literature check and the
hand-checked sample exist (tracker B.2, B.3).

Blank-date rule (hypothesis, to be confirmed on the website by the hand check): a row with
an empty date and empty arrivals takes the date of the closest preceding dated row in the
same market of the same file. It is marked date_inferred=1. If its arrivals cell is also empty,
the anchor's arrivals figure is shown and marked arrivals_shared=1; it is never added twice.
In the files from Dec 2025 on, blank-date rows carry their own arrivals (arrivals_shared=0).
"""

import csv
import hashlib
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "agmarknet" / "paddy_basmati"
OUT_DATA = ROOT / "data" / "processed" / "basmati"
OUT_RES = ROOT / "results" / "L2_cleaning"

COLUMNS = [
    "row_id", "source_file", "line_no", "market_raw", "variety_raw", "date", "date_inferred",
    "arrivals_t", "arrivals_shared", "min_price", "max_price", "modal_price", "flags",
]
# Informational flags describe a pattern worth a human look but are not data errors.
INFO_FLAGS = {"BLANK_DATE_HAS_OWN_ARRIVALS"}
HEADER_PREFIXES = ("Arrival Date", "Date Wise Prices", "Commodity :")


def to_float(text):
    """Return (value, kind): kind is 'ok', 'blank' or 'dash'/'bad' for anything else."""
    t = text.strip()
    if t == "":
        return None, "blank"
    if t == "-":
        return None, "dash"
    try:
        return float(t), "ok"
    except ValueError:
        return None, "bad"


def parse_text(source_file, text):
    """Parse one monthly file. Returns (rows, unexplained) where unexplained lists lines
    that are neither header, market line, blank line nor a six-field data row."""
    month = re.match(r"(\d{4})-(\d{2})", source_file)
    year, mon = int(month.group(1)), int(month.group(2))
    rows, unexplained = [], []
    market = None
    anchor = None  # closest preceding dated row of the current market
    for line_no, line in enumerate(text.splitlines(), start=1):
        raw = line.lstrip("﻿")
        if raw.strip() == "":
            continue
        if raw.startswith("Market Name :"):
            market = raw.split(":", 1)[1].strip().strip(",").strip()
            anchor = None
            continue
        if raw.startswith(HEADER_PREFIXES) or raw.startswith('"'):
            continue
        fields = next(csv.reader([raw]))
        if len(fields) != 6 or market is None:
            unexplained.append((line_no, raw))
            continue
        d_txt, arr_txt, variety, mn, mx, mo = [f.strip() for f in fields]
        flags = []
        date_inferred = 0
        arrivals_shared = 0
        if d_txt:
            try:
                date = datetime.strptime(d_txt, "%d/%m/%Y").date()
            except ValueError:
                date = None
                flags.append("DATE_UNPARSEABLE")
            anchor = {"date": date, "variety": variety, "arrivals": arr_txt} if date else None
        else:
            if anchor is None:
                date = None
                flags.append("BLANK_DATE_NO_ANCHOR")
            else:
                date = anchor["date"]
                date_inferred = 1
                arrivals_shared = 1 if arr_txt == "" else 0
                if variety == anchor["variety"]:
                    flags.append("BLANK_SAME_VARIETY_AS_ANCHOR")
        arrivals, a_kind = to_float(arr_txt)
        if d_txt == "" and arr_txt != "":
            flags.append("BLANK_DATE_HAS_OWN_ARRIVALS")
        if d_txt == "" and a_kind == "blank" and anchor is not None:
            arrivals = to_float(anchor["arrivals"])[0]
        if d_txt and a_kind != "ok":
            flags.append("ARRIVALS_MISSING")
        if a_kind == "bad":
            flags.append("ARRIVALS_UNPARSEABLE")
        prices = {}
        for name, txt in (("min", mn), ("max", mx), ("modal", mo)):
            val, kind = to_float(txt)
            prices[name] = val
            if kind in ("blank", "dash"):
                flags.append(f"{name.upper()}_MISSING")
            elif kind == "bad":
                flags.append(f"{name.upper()}_UNPARSEABLE")
        known = [v for v in prices.values() if v is not None]
        if any(v <= 0 for v in known):
            flags.append("NONPOSITIVE_PRICE")
        if arrivals is not None and arrivals < 0:
            flags.append("NEGATIVE_ARRIVALS")
        lo, md, hi = prices["min"], prices["modal"], prices["max"]
        if (lo is not None and md is not None and lo > md) or (md is not None and hi is not None and md > hi) \
                or (lo is not None and hi is not None and lo > hi):
            flags.append("PRICE_ORDER_VIOLATION")
        if date is not None and (date.year, date.month) != (year, mon):
            flags.append("DATE_OUTSIDE_FILE_MONTH")
        rows.append({
            "row_id": f"{source_file}:{line_no}", "source_file": source_file, "line_no": line_no,
            "market_raw": market, "variety_raw": variety,
            "date": date.isoformat() if date else "", "date_inferred": date_inferred,
            "arrivals_t": "" if arrivals is None else arrivals, "arrivals_shared": arrivals_shared,
            "min_price": "" if lo is None else lo, "max_price": "" if hi is None else hi,
            "modal_price": "" if md is None else md, "flags": ";".join(flags),
        })
    # duplicates: same market, variety and date seen more than once (keep all, never average)
    key_count = Counter((r["market_raw"], r["variety_raw"], r["date"]) for r in rows if r["date"])
    for r in rows:
        if r["date"] and key_count[(r["market_raw"], r["variety_raw"], r["date"])] > 1:
            r["flags"] = (r["flags"] + ";" if r["flags"] else "") + "DUPLICATE_KEY"
    return rows, unexplained


def row_status(row):
    """kept = no problem flag; flagged = at least one non-informational flag. Nothing is removed."""
    problems = set(row["flags"].split(";")) - INFO_FLAGS - {""}
    return "flagged" if problems else "kept"


def parse_all(raw_dir=RAW):
    all_rows, per_file = [], []
    for path in sorted(raw_dir.glob("*_punjab.csv")):
        text = path.read_text(encoding="utf-8-sig")
        rows, unexplained = parse_text(path.name, text)
        per_file.append((path.name, rows, unexplained, hashlib.sha256(path.read_bytes()).hexdigest()))
        all_rows.extend(rows)
    return all_rows, per_file


def write_outputs(all_rows, per_file):
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_RES.mkdir(parents=True, exist_ok=True)
    with open(OUT_DATA / "basmati_tidy.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(all_rows)
    with open(OUT_RES / "reconciliation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["source_file", "sha256", "data_rows", "dated", "blank_date", "kept", "flagged",
                    "removed", "unexplained_lines"])
        for name, rows, unexplained, sha in per_file:
            dated = sum(1 for r in rows if not r["date_inferred"] and r["date"])
            blank = sum(1 for r in rows if r["date_inferred"] or "BLANK_DATE_NO_ANCHOR" in r["flags"])
            kept = sum(1 for r in rows if row_status(r) == "kept")
            w.writerow([name, sha, len(rows), dated, blank, kept, len(rows) - kept, 0, len(unexplained)])
    flag_counts = Counter(fl for r in all_rows for fl in r["flags"].split(";") if fl)
    with open(OUT_RES / "flag_counts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["flag", "rows"])
        for flag, n in sorted(flag_counts.items()):
            w.writerow([flag, n])
    dated = sum(1 for r in all_rows if not r["date_inferred"] and r["date"])
    blank = sum(1 for r in all_rows if r["date_inferred"])
    flagged = sum(1 for r in all_rows if row_status(r) == "flagged")
    unexplained = sum(len(u) for _, _, u, _ in per_file)
    lines = [
        "# B.1 parse summary (written by parse_basmati.py)", "",
        f"- Source files: {len(per_file)}", f"- Data rows: {len(all_rows)}",
        f"- Dated rows: {dated}", f"- Blank-date rows (date inferred, hypothesis): {blank}",
        f"- Rows flagged (problem flags; informational ones excluded): {flagged}", "- Rows removed: 0",
        f"- Unexplained source lines: {unexplained}", "", "| Flag | Rows |", "|---|---|",
    ]
    lines += [f"| {k} | {v} |" for k, v in sorted(flag_counts.items())]
    (OUT_RES / "parse_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    all_rows, per_file = parse_all()
    write_outputs(all_rows, per_file)
    print(f"{len(all_rows)} data rows from {len(per_file)} files; see {OUT_RES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
