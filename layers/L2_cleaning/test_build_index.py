"""Tests for the B.4 index. Synthetic rows are labelled synthetic (mechanics only)."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_index as bi  # noqa: E402
import parse_basmati as pb  # noqa: E402


def row(market, day, modal, variety="1121", inferred="0"):
    return {"variety_raw": variety, "date": day, "modal_price": str(modal), "market_raw": market,
            "date_inferred": inferred}


SYN = [row("A", "2024-11-01", 3000), row("B", "2024-11-01", 3200), row("C", "2024-11-01", 3100),
       row("D", "2024-11-01", 4000),                      # median of 4 = 3150
       row("A", "2024-11-02", 3000), row("B", "2024-11-02", 3200),   # only 2 mandis -> no index day
       row("A", "2024-11-03", 3000), row("B", "2024-11-03", 3100), row("C", "2024-11-03", 3200),
       row("C", "2024-11-03", 9999),                      # duplicate mandi-day -> C excluded -> 2 mandis
       row("A", "2024-11-04", 3000), row("B", "2024-11-04", 3100), row("C", "2024-11-04", 3300, inferred="1")]


def test_median_and_count():
    idx, _ = bi.build_index(SYN, "1121", "dated_only")
    d = {r["date"]: r for r in idx}
    assert d["2024-11-01"]["index_modal"] == 3150 and d["2024-11-01"]["n_mandis"] == 4


def test_minimum_mandis_and_no_filling():
    idx, _ = bi.build_index(SYN, "1121", "dated_only")
    assert [r["date"] for r in idx] == ["2024-11-01"]


def test_duplicates_excluded_never_averaged():
    idx, dup = bi.build_index(SYN, "1121", "dated_only")
    assert dup == 1 and "2024-11-03" not in {r["date"] for r in idx}


def test_variant_controls_blank_date_rows():
    a, _ = bi.build_index(SYN, "1121", "dated_only")
    b, _ = bi.build_index(SYN, "1121", "with_blank")
    assert "2024-11-04" not in {r["date"] for r in a} and "2024-11-04" in {r["date"] for r in b}


def test_missing_modal_skipped():
    rows = [row("A", "2024-11-01", ""), row("B", "2024-11-01", 3000), row("C", "2024-11-01", 3100)]
    assert bi.build_index(rows, "1121", "dated_only")[0] == []


def test_dated_only_matches_independent_power_check():
    """layers/L1_data/power_check.py (separate code path) reported 433 and 369 index days."""
    text = (pb.ROOT / "results" / "L1_coverage" / "power_check.txt").read_text()
    expected = {m.group(1): int(m.group(2)) for m in re.finditer(r"^(1121|Basmati 1509): total index days (\d+)", text, re.M)}
    import csv
    with open(bi.TIDY, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for variety, n in expected.items():
        assert len(bi.build_index(rows, variety, "dated_only")[0]) == n
