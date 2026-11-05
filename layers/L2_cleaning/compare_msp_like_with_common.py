"""O26: how MSP-valued basmati rows compare with other basmati rows and with Paddy (Common) records.

Usage: python3 -I layers/L2_cleaning/compare_msp_like_with_common.py

POST-HOC AND EXPLORATORY: not part of the frozen protocol. These patterns can suggest, but cannot prove, that a row is
an MSP or common-paddy report under a basmati label. Uses the same rule as check_msp_like_rows.py: a dated row whose
modal price is within Rs 1 of its season's paddy Grade-A or common MSP. Nothing is removed from any file.

Writes results/L2_cleaning/msp_like_rows/common_paddy_comparison.json
"""
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TIDY = ROOT / "data" / "processed" / "basmati" / "basmati_tidy.csv"
RAW = ROOT / "data" / "raw" / "agmarknet" / "paddy_basmati"
COMMON = ROOT / "data" / "raw" / "agmarknet" / "paddy_common" / "agmarknet_paddy_common_punjab.csv"
MSP = ROOT / "layers" / "L1_data" / "msp" / "msp_schedule.csv"
OUT = ROOT / "results" / "L2_cleaning" / "msp_like_rows" / "common_paddy_comparison.json"
VARIETIES = ("1121", "Basmati 1509")
TOLERANCE_RS = 1.0
ARRIVALS_EPS = 0.01


def season(d):
    y, m = int(d[:4]), int(d[5:7])
    s = y if m >= 9 else y - 1
    return f"{s}-{str(s + 1)[2:]}"


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def flat(r):
    return r["min_price"] == r["max_price"] == r["modal_price"]


def common_match(rows, by_key, last_date):
    """Share with a common-paddy row on the same mandi and date, and how many of those agree on price and arrivals."""
    rows = [r for r in rows if r["date"] <= last_date]
    with_row = same_price = same_arrivals = 0
    for r in rows:
        q = by_key.get((r["market_raw"], r["date"]))
        if not q:
            continue
        with_row += 1
        m = float(r["modal_price"])
        same_price += any(abs(float(x["modal_price_rs_per_quintal"] or -1e9) - m) <= TOLERANCE_RS for x in q)
        if r["arrivals_t"]:
            a = float(r["arrivals_t"])
            same_arrivals += any(abs(float(x["arrivals_metric_tonnes"] or -1e9) - a) < ARRIVALS_EPS for x in q)
    return {"rows": len(rows), "with_common_row": with_row, "same_price": same_price, "same_arrivals": same_arrivals}


def main():
    msp = defaultdict(list)
    for r in read(MSP):
        if r["crop"] == "paddy":
            msp[r["marketing_season"].split()[1]].append(float(r["msp_rs_per_quintal"]))
    scope = [r for r in read(TIDY) if r["variety_raw"] in VARIETIES and r["date"] and r["modal_price"] != "" and r["date_inferred"] != "1"]
    for r in scope:
        r["like"] = any(abs(float(r["modal_price"]) - v) <= TOLERANCE_RS for v in msp.get(season(r["date"]), []))
    like = [r for r in scope if r["like"]]
    like_1121 = [r for r in like if r["variety_raw"] == "1121"]
    other_1121 = [r for r in scope if r["variety_raw"] == "1121" and not r["like"]]

    traced = 0
    lines = {}
    for r in like:
        f = r["source_file"]
        lines.setdefault(f, (RAW / f).read_text(encoding="utf-8", errors="replace").split("\n"))
        line = lines[f][int(r["line_no"]) - 1]
        traced += str(float(r["modal_price"])) in line and r["variety_raw"] in line

    by_day = defaultdict(list)
    for r in other_1121:
        by_day[r["date"]].append(float(r["modal_price"]))
    gaps = [statistics.median(by_day[r["date"]]) - float(r["modal_price"]) for r in like_1121 if by_day[r["date"]]]

    like_by_mandi = Counter(r["market_raw"] for r in like_1121)
    all_by_mandi = Counter(r["market_raw"] for r in scope if r["variety_raw"] == "1121")
    only = sorted(m for m, n in like_by_mandi.items() if n == all_by_mandi[m])

    common = read(COMMON)
    last = max(r["arrival_date"] for r in common)
    by_key = defaultdict(list)
    for r in common:
        by_key[(r["market_name"], r["arrival_date"])].append(r)

    arrivals = lambda rows: statistics.median(float(r["arrivals_t"]) for r in rows if r["arrivals_t"])
    out = {
        "status": "POST-HOC EXPLORATORY: suggests, does not prove; never replaces the primary result",
        "rows": {"msp_like": len(like), "msp_like_1121": len(like_1121), "other_1121": len(other_1121)},
        "traced_to_raw_line": traced,
        "months": dict(sorted(Counter(r["date"][5:7] for r in like).items())),
        "median_arrivals_t": {"msp_like_1121": arrivals(like_1121), "other_1121": arrivals(other_1121)},
        "min_eq_max_eq_modal_pct": {"msp_like_1121": 100 * statistics.mean(map(flat, like_1121)), "other_1121": 100 * statistics.mean(map(flat, other_1121))},
        "same_day_gap_to_other_1121_median": {"rows_compared": len(gaps), "median_rs": statistics.median(gaps), "pct_over_500": 100 * statistics.mean(g > 500 for g in gaps)},
        "mandis_with_1121_only_at_msp": {"count": len(only), "rows": sum(like_by_mandi[m] for m in only), "mandis": only},
        "common_paddy_last_date": last,
        "common_match": {"msp_like_1121": common_match(like_1121, by_key, last), "other_1121": common_match(other_1121, by_key, last)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
