"""Tests for the B.5 release builder (real parsed rows; the raw files are never touched)."""

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_release as mr  # noqa: E402


def tidy():
    with open(mr.TIDY, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_release_reconciles_exactly_and_changes_no_row_count():
    rows, counts = mr.build(tidy())
    assert counts["rows"] == len(tidy()) == counts["dated_rows"] + counts["blank_date_rows"]
    assert (counts["dated_rows"], counts["blank_date_rows"]) == (6098, 580)
    assert [r["row_id"] for r in rows] == [r["row_id"] for r in tidy()]  # nothing removed, nothing reordered


def test_prices_and_arrivals_are_exact_decimal_strings_and_missing_stays_missing():
    rows, _ = mr.build(tidy())
    for r in rows:
        for k in ("min_price", "max_price", "modal_price"):
            if r[k]:
                assert Decimal(r[k]) > 0 and r[k].count(".") == 1 and len(r[k].split(".")[1]) == 2
        assert len(r["arrivals_t"].split(".")[1]) == 3
    src = {r["row_id"]: r for r in tidy()}
    assert any(r["max_price"] == "" and src[r["row_id"]]["max_price"] == "" for r in rows)  # a missing max stays empty, not 0


def test_only_floating_point_noise_is_rounded_and_every_such_row_is_flagged():
    rows, counts = mr.build(tidy())
    src = {r["row_id"]: r for r in tidy()}
    changed = [r for r in rows if "ARRIVALS_ROUNDED_3DP" in r["flags"]]
    assert len(changed) == counts["arrivals_rounded_rows"] > 0
    for r in changed:
        assert abs(Decimal(r["arrivals_t"]) - Decimal(src[r["row_id"]]["arrivals_t"])) < Decimal("0.000002")
    for r in rows:
        if "ARRIVALS_ROUNDED_3DP" not in r["flags"]:
            assert Decimal(r["arrivals_t"]) == Decimal(src[r["row_id"]]["arrivals_t"])


def test_release_files_match_their_manifest_and_are_deterministic():
    assert mr.main() == 0
    out = mr.ROOT / "data" / "processed" / "basmati" / "release" / mr.NAME
    m1 = json.loads((out / "manifest.json").read_text())
    first = {n: hashlib.sha256((out / n).read_bytes()).hexdigest() for n in m1["files"]}
    assert first == m1["files"]
    assert mr.main() == 0
    assert json.loads((out / "manifest.json").read_text()) == m1  # same inputs, same release
    assert m1["validation_status"] == "PENDING_HAND_CHECK" and m1["flagged_rows"] == 8
    assert sum(f["data_rows"] for f in m1["raw_files"].values()) == m1["rows"]


def test_every_market_name_becomes_one_mandi_and_unknown_coordinates_stay_empty():
    out = mr.ROOT / "data" / "processed" / "basmati" / "release" / mr.NAME
    mr.main()
    with open(out / "mandis.csv", newline="", encoding="utf-8") as f:
        mandis = list(csv.DictReader(f))
    assert len(mandis) == len({r["market_raw"] for r in tidy()}) == 86
    assert all((m["latitude"] == "") == (m["longitude"] == "") for m in mandis)
    assert 0 < sum(1 for m in mandis if m["latitude"]) < len(mandis)
