"""B.2c: does the blank-date rule give plausible rows? NOT a substitute for the hand check (B.2), which compares rows
with the portal. This script asks only whether rows whose date was inferred from the row above behave like rows that
carry their own date:

  1. Same-market pairs of 1121 and Basmati 1509 on one day: the modal-price ratio 1121 / 1509 for (a) a control of own-dated rows one day apart and (b) same-day pairs where one row is blank-date (its date inferred). If the rule attached rows to wrong
     days, (b) would be more spread out and would not look like (a). Compared with a two-sample Kolmogorov-Smirnov test.
  2. Duplicates: how often an inferred row lands on a (market, variety, date) that already has a dated row.

Usage:  env/run layers/L2_cleaning/check_blank_date_plausibility.py
Writes: results/L2_cleaning/blank_date_plausibility.json
"""

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
TIDY = ROOT / "data" / "processed" / "basmati" / "basmati_tidy.csv"
OUT = ROOT / "results" / "L2_cleaning" / "blank_date_plausibility.json"


def main() -> None:
    with TIDY.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["date"] and r["modal_price"] != "" and r["variety_raw"] in ("1121", "Basmati 1509")]
    from datetime import date, timedelta

    # In the files a second variety on a market-day always sits in a blank-date row, so there are no pairs where both rows
    # carry their own date on the same day. The control is therefore: own-dated 1121 and 1509 rows of one market on
    # ADJACENT days (the same market, one day apart), whose price ratio shows how much 1121/1509 moves by chance in a day.
    own_by = defaultdict(dict)
    pair_same = defaultdict(dict)
    for r in rows:
        d = date.fromisoformat(r["date"])
        if r["date_inferred"] == "0":
            own_by[(r["market_raw"], r["variety_raw"])][d] = float(r["modal_price"])
        pair_same[(r["market_raw"], d)].setdefault(r["variety_raw"], []).append((float(r["modal_price"]), r["date_inferred"] == "1"))
    own = []  # adjacent-day control
    for (m, var), by in own_by.items():
        if var != "1121":
            continue
        other = own_by.get((m, "Basmati 1509"), {})
        for d, p1 in by.items():
            for dd in (d - timedelta(days=1), d + timedelta(days=1)):
                if dd in other:
                    own.append(p1 / other[dd])
    inferred = []  # same-day pairs in which one row carries an inferred date
    for v in pair_same.values():
        if len(v.get("1121", [])) == 1 and len(v.get("Basmati 1509", [])) == 1:
            (p1, i1), (p2, i2) = v["1121"][0], v["Basmati 1509"][0]
            if i1 or i2:
                inferred.append(p1 / p2)
    keys = defaultdict(list)
    for r in rows:
        keys[(r["market_raw"], r["variety_raw"], r["date"])].append(r["date_inferred"] == "1")
    inf_total = sum(1 for r in rows if r["date_inferred"] == "1")
    inf_dup = sum(1 for v in keys.values() if any(v) and len(v) > 1)
    ks = stats.ks_2samp(own, inferred)
    doc = {
        "pairs_adjacent_day_control": len(own), "pairs_same_day_one_inferred": len(inferred),
        "ratio_median_adjacent_day_control": round(statistics.median(own), 3), "ratio_median_one_inferred": round(statistics.median(inferred), 3),
        "ratio_iqr_adjacent_day_control": round(statistics.quantiles(own, n=4)[2] - statistics.quantiles(own, n=4)[0], 3),
        "ratio_iqr_one_inferred": round(statistics.quantiles(inferred, n=4)[2] - statistics.quantiles(inferred, n=4)[0], 3),
        "ks_statistic": round(float(ks.statistic), 3), "ks_p": round(float(ks.pvalue), 3),
        "inferred_rows": inf_total, "inferred_rows_on_a_key_with_another_row": inf_dup,
        "note": "plausibility only; the hand check against the portal (B.2) is still the test of the rule",
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps(doc, indent=2))


if __name__ == "__main__":
    main()
