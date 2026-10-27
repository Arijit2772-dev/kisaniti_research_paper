"""B.3a (EXP-02, descriptive part): what do different outlier screens flag, and how much would excluding the flagged rows
move the variety index? No forecast is run and no ground truth is used: the hand check (B.2) is what decides which
screen is right, so precision and recall are NOT computed here. The screens only flag; nothing is ever deleted
(CLEANING_PLAN.md B.1f).

Rules (parameters are listed, not tuned): MAD past-only (>= 10 earlier prices in the series; k = 3 and 5), Hampel
(centred window of 7 prices, k = 3), IQR (per series and season, 1.5 x IQR). A series is one market and one variety.

Usage:  env/run layers/L2_cleaning/compare_screens.py
Needs:  data/processed/basmati/basmati_tidy.csv       Writes: results/L2_cleaning/screen_comparison.csv
"""

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_index import build_index  # noqa: E402

ROOT = HERE.parents[1]
TIDY = ROOT / "data" / "processed" / "basmati" / "basmati_tidy.csv"
OUT = ROOT / "results" / "L2_cleaning" / "screen_comparison.csv"
VARIETIES = ("1121", "Basmati 1509")


def mad_scale(vals):
    med = statistics.median(vals)
    return med, 1.4826 * statistics.median(abs(v - med) for v in vals)


def flags(rows):
    """{rule: set(row_id)} for dated rows with a modal price."""
    series = defaultdict(list)
    for r in rows:
        if r["date"] and r["modal_price"] != "" and r["variety_raw"] in VARIETIES:
            series[(r["market_raw"], r["variety_raw"])].append(r)
    out = defaultdict(set)
    for s in series.values():
        s.sort(key=lambda r: (r["date"], r["row_id"]))
        x = [float(r["modal_price"]) for r in s]
        for i, r in enumerate(s):
            if i >= 10:
                med, sc = mad_scale(x[:i])
                for k in (3, 5):
                    if sc > 0 and abs(x[i] - med) > k * sc:
                        out[f"mad_k{k}"].add(r["row_id"])
            win = x[max(0, i - 3): i + 4]
            if len(win) >= 5:
                med, sc = mad_scale(win)
                if sc > 0 and abs(x[i] - med) > 3 * sc:
                    out["hampel_w7_k3"].add(r["row_id"])
        by_season = defaultdict(list)
        for i, r in enumerate(s):
            by_season[r["date"][:4] + ("a" if r["date"][5:7] in ("09", "10", "11", "12") else "b")].append(i)
        for idx in by_season.values():
            vals = sorted(x[i] for i in idx)
            if len(vals) >= 8:
                q = statistics.quantiles(vals, n=4)
                lo, hi = q[0] - 1.5 * (q[2] - q[0]), q[2] + 1.5 * (q[2] - q[0])
                for i in idx:
                    if x[i] < lo or x[i] > hi:
                        out["iqr_1.5"].add(s[i]["row_id"])
    return out


def main():
    with TIDY.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    considered = [r for r in rows if r["date"] and r["modal_price"] != "" and r["variety_raw"] in VARIETIES and r["date_inferred"] != "1"]
    flagged = flags(considered)
    base = {v: {r["date"]: r["index_modal"] for r in build_index(rows, v, "dated_only")[0]} for v in VARIETIES}
    out = []
    for rule in sorted(flagged):
        bad = flagged[rule]
        kept = [r for r in rows if r["row_id"] not in bad]
        row = {"rule": rule, "rows_considered": len(considered), "rows_flagged": len(bad), "share_flagged_pct": round(100 * len(bad) / len(considered), 2)}
        for v in VARIETIES:
            new = {r["date"]: r["index_modal"] for r in build_index(kept, v, "dated_only")[0]}
            changed = [abs(new[d] - base[v][d]) for d in base[v] if d in new and new[d] != base[v][d]]
            tag = v.replace("Basmati ", "")
            row[f"{tag}_index_days"] = len(base[v])
            row[f"{tag}_days_lost"] = sum(1 for d in base[v] if d not in new)
            row[f"{tag}_days_changed"] = len(changed)
            row[f"{tag}_max_change_rs"] = max(changed) if changed else 0
            row[f"{tag}_median_change_rs"] = statistics.median(changed) if changed else 0
        out.append(row)
    rules = sorted(flagged)
    for i, a in enumerate(rules):
        out[i]["jaccard_with_others"] = "; ".join(f"{b}:{len(flagged[a] & flagged[b]) / max(1, len(flagged[a] | flagged[b])):.2f}" for b in rules if b != a)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    for r in out:
        print({k: r[k] for k in ("rule", "rows_flagged", "share_flagged_pct", "1121_days_lost", "1121_days_changed", "1121_max_change_rs", "1509_days_changed", "1509_max_change_rs")})


if __name__ == "__main__":
    main()
