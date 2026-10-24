"""Tests for the B.1 parser. Run: python3 -I -m pytest layers/L2_cleaning -q

Tests on in-memory text use SYNTHETIC lines (mechanics only, not real prices).
Tests on the real files read data/raw (never modified) and the committed manifests.
"""

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse_basmati as pb  # noqa: E402

ROOT = pb.ROOT
HEAD = 'Date Wise Prices ...\n\nArrival Date,Arrivals,Variety,Min,Max,Modal\n'

SYNTHETIC = HEAD + """Market Name : Alpha APMC
01/11/2024,100.0,1121,3000.0,3500.0,3200.0
,,Basmati 1509,2500.0,2900.0,2700.0
Market Name : Beta APMC
,,1121,3000.0,3500.0,3200.0
02/11/2024,50.0,1121,3100.0,3600.0,3300.0
,,1121,3100.0,3600.0,3300.0
03/12/2024,10.0,1121,0.0,3600.0,3300.0
04/11/2024,10.0,1121,3900.0,3600.0,3300.0
05/11/2024,10.0,1121,-,3600.0,3300.0
"""


def synthetic_rows():
    rows, unexplained = pb.parse_text("2024-11_punjab.csv", SYNTHETIC)
    assert unexplained == []
    return rows


def test_blank_row_takes_date_of_preceding_row_in_same_market():
    r = synthetic_rows()
    assert r[1]["date"] == "2024-11-01" and r[1]["date_inferred"] == 1 and r[1]["arrivals_shared"] == 1
    assert r[1]["arrivals_t"] == 100.0


def test_blank_row_never_crosses_a_market_boundary():
    r = synthetic_rows()
    assert r[2]["date"] == "" and "BLANK_DATE_NO_ANCHOR" in r[2]["flags"]
    assert r[2]["date_inferred"] == 0


def test_blank_row_never_crosses_a_file_boundary():
    rows, _ = pb.parse_text("2024-12_punjab.csv", HEAD + "Market Name : Alpha APMC\n,,1121,1.0,2.0,1.5\n")
    assert rows[0]["date"] == "" and "BLANK_DATE_NO_ANCHOR" in rows[0]["flags"]


def test_mechanical_flags_detect_corrupted_synthetic_rows():
    r = synthetic_rows()
    flags = {x["row_id"].split(":")[1]: x["flags"] for x in r}
    assert "NONPOSITIVE_PRICE" in flags["11"]
    assert "DATE_OUTSIDE_FILE_MONTH" in flags["11"]
    assert "PRICE_ORDER_VIOLATION" in flags["12"]
    assert "MIN_MISSING" in flags["13"]
    assert "BLANK_SAME_VARIETY_AS_ANCHOR" in flags["10"] and "DUPLICATE_KEY" in flags["10"]


def test_missing_stays_missing_not_zero():
    r = synthetic_rows()
    assert r[-1]["min_price"] == ""


def test_real_files_reconcile_with_manifests():
    all_rows, per_file = pb.parse_all()
    assert len(per_file) == 29
    for name, rows, unexplained, _ in per_file:
        assert unexplained == [], name
        man = json.loads((ROOT / "data" / "manifests" / f"agmarknet_paddy_basmati_{name.replace('.csv', '')}.json").read_text())
        dated = sum(1 for r in rows if not r["date_inferred"] and r["date"])
        blank = sum(1 for r in rows if r["date_inferred"])
        assert (dated, blank) == (man["rows"], man["blank_date_rows"]), name
    assert len({r["row_id"] for r in all_rows}) == len(all_rows)


def test_raw_files_unchanged_checksums_equal_manifests():
    for path in sorted(pb.RAW.glob("*_punjab.csv")):
        man = json.loads((ROOT / "data" / "manifests" / f"agmarknet_paddy_basmati_{path.stem}.json").read_text())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == man["sha256"], path.name


def test_rerun_is_identical():
    def digest():
        rows, _ = pb.parse_all()
        return hashlib.sha256(repr([tuple(r.items()) for r in rows]).encode()).hexdigest()

    assert digest() == digest()


def test_every_blank_row_has_an_anchor_in_same_market_and_file():
    rows, _ = pb.parse_all()
    last = {}
    for r in rows:
        key = (r["source_file"], r["market_raw"])
        if not r["date_inferred"]:
            if r["date"]:
                last[key] = r["date"]
        else:
            assert last.get(key) == r["date"], r["row_id"]
