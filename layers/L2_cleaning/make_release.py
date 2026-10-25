"""B.5 dataset release: the cleaned basmati rows in the form the product imports, with an exact manifest.

Usage:  python3 -I layers/L2_cleaning/make_release.py

Reads  data/processed/basmati/basmati_tidy.csv   (parse_basmati.py; raw files are never edited)
       results/L2_cleaning/reconciliation.csv     (per raw file: sha256 and row counts)
       legacy/v2_from_rp_kisan/experiments/mandi_coordinates.csv (OpenStreetMap lookups of 20 mandis; used where the
                                                                  market name matches exactly)
Writes data/processed/basmati/release/<name>/{observations.csv, mandis.csv, manifest.json}   (git-ignored data)
       results/L2_cleaning/release/<name>.manifest.json                                       (committed provenance)

Nothing is removed or corrected: every parsed row is in the release with its flags. The two changes of form are
stated in the manifest: prices and arrivals are written as exact decimal strings, and arrivals with more than three
decimals (floating-point noise in the source, under 0.000002 tonne = 2 grams) are rounded half-to-even to three and the row
gets the flag ARRIVALS_ROUNDED_3DP. The release is PENDING_HAND_CHECK: the blank-date rule is a hypothesis until the
owner's hand check (tracker B.2). The output is deterministic (same inputs, same bytes).
"""

import csv
import hashlib
import json
import re
import subprocess
import sys
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_basmati import INFO_FLAGS  # noqa: E402

TIDY = ROOT / "data" / "processed" / "basmati" / "basmati_tidy.csv"
RECON = ROOT / "results" / "L2_cleaning" / "reconciliation.csv"
COORDS = ROOT / "legacy" / "v2_from_rp_kisan" / "experiments" / "mandi_coordinates.csv"
NAME = "basmati_punjab_release1"
OBS_COLUMNS = ["row_id", "source_file", "line_no", "market_raw", "variety_raw", "date", "date_inferred", "arrivals_t",
               "arrivals_shared", "min_price", "max_price", "modal_price", "flags"]
CENT, MILLI = Decimal("0.01"), Decimal("0.001")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def town_of(market: str) -> str:
    """Town name without a bracketed sub-yard and without APMC, for grouping only (mandis are never merged)."""
    t = re.sub(r"\(.*?\)", "", market)
    t = re.sub(r"\bAPMC\b", "", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()


def exact(value: str, quantum: Decimal) -> tuple[str, bool]:
    """Exact decimal string with the quantum's scale; the flag says whether rounding changed the value."""
    d = Decimal(value)
    q = d.quantize(quantum, rounding=ROUND_HALF_EVEN)
    return str(q), q != d


def build(tidy_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    out, rounded = [], 0
    for r in tidy_rows:
        flags = [f for f in r["flags"].split(";") if f]
        arr, changed = exact(r["arrivals_t"], MILLI) if r["arrivals_t"] else ("", False)
        if changed:
            flags.append("ARRIVALS_ROUNDED_3DP")
            rounded += 1
        row = {k: r[k] for k in ("row_id", "source_file", "line_no", "market_raw", "variety_raw", "date", "date_inferred", "arrivals_shared")}
        row.update({"arrivals_t": arr, "flags": ";".join(flags)})
        for k in ("min_price", "max_price", "modal_price"):
            row[k] = exact(r[k], CENT)[0] if r[k] else ""
        out.append({c: row[c] for c in OBS_COLUMNS})
    dated = sum(1 for r in out if r["date_inferred"] == "0")
    blank = sum(1 for r in out if r["date_inferred"] == "1")
    flagged = sum(1 for r in out if set(r["flags"].split(";")) - INFO_FLAGS - {"ARRIVALS_ROUNDED_3DP", ""})
    counts = {"rows": len(out), "dated_rows": dated, "blank_date_rows": blank, "flagged_rows": flagged, "arrivals_rounded_rows": rounded}
    if counts["rows"] != dated + blank:
        raise SystemExit(f"reconciliation failed: {counts}")
    return out, counts


def write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    with open(TIDY, newline="", encoding="utf-8") as f:
        tidy = list(csv.DictReader(f))
    obs, counts = build(tidy)
    with open(RECON, newline="", encoding="utf-8") as f:
        recon = list(csv.DictReader(f))
    if sum(int(r["data_rows"]) for r in recon) != counts["rows"] or any(int(r["unexplained_lines"]) for r in recon):
        raise SystemExit("the parse and the reconciliation disagree; run parse_basmati.py again")
    coords = {r["market_name"]: r for r in csv.DictReader(open(COORDS, newline="", encoding="utf-8"))}
    names = sorted({r["market_raw"] for r in obs})
    mandis = []
    for n in names:
        c = coords.get(n)
        mandis.append({"name": n, "town": town_of(n), "state": "Punjab", "latitude": c["lat"] if c else "", "longitude": c["lon"] if c else "",
                       "coordinate_source": f"OpenStreetMap Nominatim, query: {c['query']}" if c else ""})
    out = ROOT / "data" / "processed" / "basmati" / "release" / NAME
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "observations.csv", OBS_COLUMNS, obs)
    write_csv(out / "mandis.csv", ["name", "town", "state", "latitude", "longitude", "coordinate_source"], mandis)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
    manifest = {
        "release_name": NAME, "commodity": "Paddy(Basmati)", "crop": "PADDY", "msp_applies": False, "state": "Punjab", "source": "AGMARKNET, Date Wise Prices for Specified Commodity (manual CSV export, filed 22-24 Oct 2026)",
        **counts, "files": {"observations.csv": sha256_file(out / "observations.csv"), "mandis.csv": sha256_file(out / "mandis.csv")},
        "mandis": len(mandis), "mandis_with_coordinates": sum(1 for m in mandis if m["latitude"]),
        "raw_files": {r["source_file"]: {"sha256": r["sha256"], "data_rows": int(r["data_rows"])} for r in recon},
        "validation_status": "PENDING_HAND_CHECK",
        "validation_note": "The blank-date rule (rows with an empty date take the date of the preceding row of the same market) is a hypothesis until the 56-row hand check on the website is done.",
        "rules": {
            "parser": "layers/L2_cleaning/parse_basmati.py", "research_repo_commit_at_release": commit,
            "blank_date_rule": "a row with empty date and arrivals takes the date of the closest preceding dated row of the same market in the same file; date_inferred = 1",
            "flags": "mechanical checks only; no value is removed or corrected; informational flag BLANK_DATE_HAS_OWN_ARRIVALS",
            "decimals": "prices exact to 0.01 rupee; arrivals exact to 0.001 tonne; ARRIVALS_ROUNDED_3DP marks rows rounded from source noise (under 0.000002 t = 2 grams)",
            "mandi_names": "one mandi per source market name; town groups sub-yards for analysis only",
        },
    }
    mpath = out / "manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    keep = ROOT / "results" / "L2_cleaning" / "release"
    keep.mkdir(parents=True, exist_ok=True)
    (keep / f"{NAME}.manifest.json").write_text(mpath.read_text(), encoding="utf-8")
    print(json.dumps({"release": str(out), **counts, "mandis": len(mandis), "with_coordinates": manifest["mandis_with_coordinates"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
