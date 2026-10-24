"""B.4 variety-level daily price index, built twice so the hand check can choose.

Usage:  python3 -I layers/L2_cleaning/build_index.py
Needs:  data/processed/basmati/basmati_tidy.csv (run parse_basmati.py first)

Definition (from CLEANING_PLAN.md B.4): for one variety and one day, the median of the modal
prices of the mandis that reported that variety on that day; kept only if at least MIN_MANDIS
mandis reported. The count of mandis, the interquartile range and the lowest/highest modal price
are stored with each index value. Nothing is forward-filled or interpolated: days without enough
mandis are absent, not filled.

Variants (the blank-date rule is a hypothesis awaiting the hand check, tracker B.2):
  dated_only     rows with a date in the source file
  with_blank     dated rows + blank-date rows that took the date of the preceding row

Mandi-days with two or more rows for the same variety (DUPLICATE_KEY) are excluded from the
index and counted; the prices are never averaged. Rows with a missing modal price are skipped.
The *_towns variants merge sub-yards of one town (candidate market map) as a sensitivity run.
In those variants a town with several yard rows on one day uses the median of its rows.
Varieties: only 1121 and Basmati 1509 (the other labels are about 3% of rows).

Writes: data/processed/basmati/index_<variant>.csv (git-ignored)
        results/L2_cleaning/index_summary.csv, index_summary.md
"""

import csv
import re
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TIDY = ROOT / "data" / "processed" / "basmati" / "basmati_tidy.csv"
OUT_DATA = ROOT / "data" / "processed" / "basmati"
OUT_RES = ROOT / "results" / "L2_cleaning"
MIN_MANDIS = 3
VARIETIES = ("1121", "Basmati 1509")
VARIANTS = ("dated_only", "with_blank", "dated_only_towns", "with_blank_towns")


def season(date):
    y, m = int(date[:4]), int(date[5:7])
    s = y if m >= 9 else y - 1
    return f"{s}-{str(s + 1)[2:]}"


def town_key(market_raw):
    """Candidate market map for sensitivity only: the town name without bracketed sub-yard,
    the word APMC, spaces or punctuation (so 'Khem karan' and 'Khemkaran (Amarkot)' coincide).
    Whether sub-yards should be merged is an open decision (OPEN_ITEMS O9)."""
    name = re.sub(r"\(.*?\)", "", market_raw)
    name = re.sub(r"\bAPMC\b", "", name, flags=re.I)
    return re.sub(r"[^a-z]", "", name.lower())


def quartiles(values):
    if len(values) < 2:
        return values[0], values[0]
    q = statistics.quantiles(values, n=4, method="inclusive")
    return q[0], q[2]


def build_index(rows, variety, variant, min_mandis=MIN_MANDIS, merge_subyards=False):
    """Return (index_rows, excluded_duplicate_mandi_days)."""
    by_day = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["variety_raw"] != variety or not r["date"] or r["modal_price"] == "":
            continue
        if variant == "dated_only" and r["date_inferred"] == "1":
            continue
        key = town_key(r["market_raw"]) if merge_subyards else r["market_raw"]
        by_day[r["date"]][key].append(float(r["modal_price"]))
    out, dup = [], 0
    for day in sorted(by_day):
        prices = []
        for market, vals in by_day[day].items():
            if len(vals) > 1 and not merge_subyards:
                dup += 1
                continue
            prices.append(vals[0] if len(vals) == 1 else statistics.median(vals))
        if len(prices) < min_mandis:
            continue
        q1, q3 = quartiles(prices)
        out.append({"date": day, "season": season(day), "variety": variety, "index_modal": statistics.median(prices),
                    "n_mandis": len(prices), "q1": q1, "q3": q3, "iqr": q3 - q1,
                    "min_modal": min(prices), "max_modal": max(prices)})
    return out, dup


def main():
    with open(TIDY, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_RES.mkdir(parents=True, exist_ok=True)
    summary = []
    for variant in VARIANTS:
        allrows = []
        for variety in VARIETIES:
            idx, dup = build_index(rows, variety, variant.removesuffix("_towns"), merge_subyards=variant.endswith("_towns"))
            allrows += idx
            by_season = defaultdict(int)
            for r in idx:
                by_season[r["season"]] += 1
            summary.append({"variant": variant, "variety": variety, "index_days": len(idx),
                            "duplicate_mandi_days_excluded": dup,
                            "median_mandis": statistics.median(r["n_mandis"] for r in idx),
                            **{f"days_{s}": n for s, n in sorted(by_season.items())}})
        with open(OUT_DATA / f"index_{variant}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(allrows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(allrows)
    cols = sorted({k for s in summary for k in s}, key=lambda k: (not k.startswith(("variant", "variety", "index", "dup", "median")), k))
    with open(OUT_RES / "index_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n", restval="0")
        w.writeheader()
        w.writerows(summary)
    seasons = sorted({k[5:] for s in summary for k in s if k.startswith("days_")})
    lines = ["# B.4 variety index summary (written by build_index.py)", "",
             f"Rule: median modal price over mandis reporting that day, at least {MIN_MANDIS} mandis; no filling.", "",
             "| Variant | Variety | Index days | Duplicate mandi-days excluded | Median mandis/day | " + " | ".join(seasons) + " |",
             "|---|---|---|---|---|" + "---|" * len(seasons)]
    for s in summary:
        lines.append(f"| {s['variant']} | {s['variety']} | {s['index_days']} | {s['duplicate_mandi_days_excluded']} | "
                     f"{s['median_mandis']} | " + " | ".join(str(s.get(f"days_{x}", 0)) for x in seasons) + " |")
    (OUT_RES / "index_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
