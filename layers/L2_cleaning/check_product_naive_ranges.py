"""Held-out coverage of the ranges the product shows with the naive forecast (RANGE_ABS_ERROR_CONFORMAL_V1).

Usage: env/run layers/L2_cleaning/check_product_naive_ranges.py

POST-HOC AND EXPLORATORY: not part of the frozen protocol. The protocol's split-conformal ranges use one validation
season; the product pools the errors of every earlier forecast up to the origin. This script scores the product's own
code (kisaniti_core.forecast) on the primary index and the 2025-26 season, with the same bootstrap and the same
"calibrated" test as run_protocol.range_rows.
"""
import csv
import json
import sys
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "layers" / "L3a_forecasting"))
import evalkit as ek  # noqa: E402
from kisaniti_core.forecast import COVERAGES, IndexPoint, error_pairs, forecast_naive, half_width  # noqa: E402

INDEX = ROOT / "data" / "processed" / "basmati" / "index_dated_only.csv"
OUT = ROOT / "results" / "L2_cleaning" / "product_naive_ranges.json"
SEASON = "2025-26"
MIN_SEASON_DAYS = 10


def main():
    series = {}
    with open(INDEX, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            series.setdefault(r["variety"], []).append(IndexPoint(date.fromisoformat(r["date"]), round(float(r["index_modal"]) * 1000), int(r["n_mandis"])))
    rows = []
    for variety, pts in series.items():
        pts = sorted(pts, key=lambda p: p.day)
        season_pts = [p for p in pts if p.season == SEASON]
        by_day = {p.day: p for p in season_pts}
        for h in (1, 7, 14):
            ys, los, his, ns = [], {"80": [], "95": []}, {"80": [], "95": []}, []
            for i, o in enumerate(season_pts):
                target = by_day.get(o.day + timedelta(days=h))
                if i + 1 < MIN_SEASON_DAYS or target is None:
                    continue
                errs = error_pairs([p for p in pts if p.day <= o.day], "NAIVE", h, until=o.day)
                widths = {k: half_width(errs, c) for k, c in COVERAGES.items()}
                if any(w is None for w in widths.values()):
                    continue
                point = forecast_naive(season_pts[: i + 1])
                ys.append(target.milli / 1000)
                ns.append(len(errs))
                for k, w in widths.items():
                    los[k].append(float(Fraction(point - w)) / 1000)
                    his[k].append(float(Fraction(point + w)) / 1000)
            for k in COVERAGES:
                level = int(k)
                m = ek.interval_metrics(ys, los[k], his[k], level / 100)
                hits = [float(lo <= y <= hi) for y, lo, hi in zip(ys, los[k], his[k], strict=True)]
                lo_ci, hi_ci = ek.block_bootstrap_mean(hits, h)
                rows.append({"variety": variety, "horizon": h, "level": level, "pairs": len(ys), "coverage": m["coverage"], "ci_low": lo_ci, "ci_high": hi_ci,
                             "mean_width": m["mean_width"], "calibrated": bool(lo_ci <= level / 100 <= hi_ci),
                             "too_wide": lo_ci > level / 100, "too_narrow": hi_ci < level / 100, "error_pairs_min": min(ns), "error_pairs_max": max(ns)})
    summary = {"status": "POST-HOC EXPLORATORY", "season": SEASON, "cases": len(rows), "calibrated": sum(r["calibrated"] for r in rows),
               "too_wide": sum(r["too_wide"] for r in rows), "too_narrow": sum(r["too_narrow"] for r in rows), "rows": rows}
    OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print({k: summary[k] for k in ("cases", "calibrated", "too_wide", "too_narrow")})
    for r in rows:
        print(r["variety"], r["horizon"], r["level"], r["pairs"], round(r["coverage"], 3), round(r["ci_low"], 3), round(r["ci_high"], 3), round(r["mean_width"]), r["calibrated"], r["error_pairs_min"], r["error_pairs_max"])


if __name__ == "__main__":
    main()
