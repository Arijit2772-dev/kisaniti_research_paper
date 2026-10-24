"""B.2 hand-check sheet: 50 stratified rows for a person to compare with the AGMARKNET website.

Usage:  python3 -I layers/L2_cleaning/make_hand_check_sheet.py
Needs:  data/processed/basmati/basmati_tidy.csv (run parse_basmati.py first)
Writes: results/L2_cleaning/hand_check_sheet.csv      (the rows to check; website columns empty)
        results/L2_cleaning/hand_check_instructions.md

The selection is deterministic (fixed seed) and stratified; it is a sample for checking the
parser and the blank-date rule, not a random sample of the whole dataset. Strata:
  A  every row that carries a problem flag (8)
  B  blank-date rows: 3 with their own arrivals (Dec 2025 onwards), 17 spread over the seasons
  C  descriptive extremes: the 3 lowest and 3 highest modal prices relative to their
     season-and-variety median (a description for a human look, NOT an outlier rule)
  D  ordinary dated rows, spread over the seasons (16)
"""

import csv
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TIDY = ROOT / "data" / "processed" / "basmati" / "basmati_tidy.csv"
OUT = ROOT / "results" / "L2_cleaning"
SEED = 20261024
INFO_FLAGS = {"BLANK_DATE_HAS_OWN_ARRIVALS"}
MAIN = ("1121", "Basmati 1509")


def season(date):
    y, m = int(date[:4]), int(date[5:7])
    s = y if m >= 9 else y - 1
    return f"{s}-{str(s + 1)[2:]}"


def load():
    with open(TIDY, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pick(rows, n, rng, taken):
    pool = [r for r in rows if r["row_id"] not in taken]
    rng.shuffle(pool)
    return pool[:n]


def spread(rows, n, rng, taken):
    """n rows spread as evenly as possible over seasons."""
    by = defaultdict(list)
    for r in rows:
        if r["row_id"] not in taken:
            by[season(r["date"])].append(r)
    seasons = sorted(by)
    for s in seasons:
        rng.shuffle(by[s])
    out, i = [], 0
    while len(out) < n and any(by[s] for s in seasons):
        s = seasons[i % len(seasons)]
        if by[s]:
            out.append(by[s].pop())
        i += 1
    return out


def build(rows):
    rng = random.Random(SEED)
    taken, chosen = set(), []

    def add(stratum, items):
        for r in items:
            if r["row_id"] not in taken:
                taken.add(r["row_id"])
                chosen.append((stratum, r))

    problem = [r for r in rows if set(r["flags"].split(";")) - INFO_FLAGS - {""}]
    add("A_problem_flag", problem)

    blanks = [r for r in rows if r["date_inferred"] == "1"]
    own = [r for r in blanks if "BLANK_DATE_HAS_OWN_ARRIVALS" in r["flags"]]
    add("B_blank_own_arrivals", pick(own, 3, rng, taken))
    shared = [r for r in blanks if r["arrivals_shared"] == "1"]
    add("B_blank_shared_arrivals", spread(shared, 17, rng, taken))

    ratios = []
    med = defaultdict(list)
    for r in rows:
        if r["date"] and r["modal_price"] and r["variety_raw"] in MAIN and not r["date_inferred"] == "1":
            med[(season(r["date"]), r["variety_raw"])].append(float(r["modal_price"]))
    med = {k: statistics.median(v) for k, v in med.items()}
    for r in rows:
        if r["date"] and r["modal_price"] and r["variety_raw"] in MAIN:
            ratios.append((float(r["modal_price"]) / med[(season(r["date"]), r["variety_raw"])], r))
    ratios.sort(key=lambda t: t[0])
    add("C_extreme_low", [r for _, r in ratios[:3]])
    add("C_extreme_high", [r for _, r in ratios[-3:]])

    normal = [r for r in rows if r["date_inferred"] != "1" and r["date"] and not r["flags"]
              and r["variety_raw"] in MAIN]
    add("D_ordinary", spread(normal, 16, rng, taken))
    return chosen


def main():
    rows = load()
    chosen = build(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["check_id", "stratum", "row_id", "month_to_select", "market_to_find", "variety_in_file",
            "date_in_file", "date_inferred", "arrivals_in_file", "min_in_file", "max_in_file",
            "modal_in_file", "flags",
            "web_date_shown", "web_arrivals", "web_min", "web_max", "web_modal",
            "web_row_shows_under_previous_date_merged_cell_yes_no", "agrees_yes_no", "checked_by",
            "checked_on", "notes"]
    chosen.sort(key=lambda t: (t[1]["source_file"], t[1]["market_raw"], int(t[1]["line_no"])))
    with open(OUT / "hand_check_sheet.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for i, (stratum, r) in enumerate(chosen, start=1):
            w.writerow([f"HC{i:02d}", stratum, r["row_id"], r["source_file"][:7], r["market_raw"],
                        r["variety_raw"], r["date"], r["date_inferred"], r["arrivals_t"], r["min_price"],
                        r["max_price"], r["modal_price"], r["flags"]] + [""] * 10)
    counts = defaultdict(int)
    for s, _ in chosen:
        counts[s] += 1
    (OUT / "hand_check_instructions.md").write_text(
        "# Hand check of " + str(len(chosen)) + " rows against the AGMARKNET website\n\n"
        "For each line of `hand_check_sheet.csv`: open the AGMARKNET report *Date Wise Prices for Specified "
        "Commodity* for Paddy(Basmati), Punjab, `month_to_select`, find `market_to_find`, and fill the "
        "`web_*` columns with what the page shows for that variety and date.\n\n"
        "**The key question for blank-date rows (`date_inferred = 1`):** on the website, is the variety's row "
        "shown under the date of the row above it (one date cell spanning two rows)? Answer in "
        "`web_row_shows_under_previous_date_merged_cell_yes_no`. If yes for all of them, the blank-date rule "
        "is confirmed. If the page shows a different date, or no such row, write that in `notes`.\n\n"
        "Set `agrees_yes_no` to yes only when date, arrivals and all three prices match the file. "
        "Write your name in `checked_by` and the date in `checked_on`.\n\n"
        "Rows per stratum: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + ".\n\n"
        "Strata C are described only by how far the price is from its season median; they are NOT an "
        "outlier rule. Prices of exactly the same value in min, max and modal are normal for many small "
        "mandis.\n", encoding="utf-8")
    print(f"{len(chosen)} rows;", dict(counts))


if __name__ == "__main__":
    main()
