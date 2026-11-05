"""O26: basmati rows whose modal price equals the paddy MSP, and what they do to the index and the forecast comparison.

Usage:  env/run layers/L2_cleaning/check_msp_like_rows.py          # counts and index effect only
        env/run layers/L2_cleaning/check_msp_like_rows.py --models # also re-runs the eight methods (slow)

POST-HOC AND EXPLORATORY. This check was not in the frozen protocol and was written after the primary result was known.
It never replaces the primary result, and it writes nothing into results/C0_protocol. It calls the pure run_stage()
with the configuration already chosen on the primary validation season, as the declared sensitivity runs do. Conformal
ranges are not computed, again as in those runs.

Rule: a dated row of 1121 or Basmati 1509 is "MSP-like" if its modal price is within Rs 1 of the paddy Grade-A or
common MSP of its season (layers/L1_data/msp/msp_schedule.csv). The rule flags a value. It does not prove that the
value is wrong. Two filters are tested: the O26 rows only (2025-26) and all seasons.
"""
import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "layers" / "L2_cleaning"))
sys.path.insert(0, str(ROOT / "layers" / "L3a_forecasting"))
import build_index as bi  # noqa: E402

TIDY = ROOT / "data" / "processed" / "basmati" / "basmati_tidy.csv"
BASE = ROOT / "data" / "processed" / "basmati" / "index_dated_only.csv"
OUT_DATA = ROOT / "data" / "processed" / "basmati"
OUT = ROOT / "results" / "L2_cleaning" / "msp_like_rows"
MSP = ROOT / "layers" / "L1_data" / "msp" / "msp_schedule.csv"
CONFIG = ROOT / "layers" / "L3a_forecasting" / "config"
TOLERANCE_RS = 1.0


def msp_by_season():
    out = {}
    with open(MSP, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["crop"] == "paddy":
                out.setdefault(r["marketing_season"].split()[1], []).append(float(r["msp_rs_per_quintal"]))
    return out


def is_msp_like(row, msp):
    if not row["date"] or row["modal_price"] == "":
        return False
    return any(abs(float(row["modal_price"]) - v) <= TOLERANCE_RS for v in msp.get(bi.season(row["date"]), []))


def read_index(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["variety"], r["date"]): r for r in csv.DictReader(f)}


def build(rows):
    out = []
    for variety in bi.VARIETIES:
        out += bi.build_index(rows, variety, "dated_only")[0]
    return out


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def effect(base, new):
    report = {}
    for variety in bi.VARIETIES:
        for season in sorted({k_s["season"] for k, k_s in base.items() if k[0] == variety}):
            keys = [k for k, r in base.items() if k[0] == variety and r["season"] == season]
            kept = [k for k in keys if k in new]
            diffs = [float(new[k]["index_modal"]) - float(base[k]["index_modal"]) for k in kept]
            changed = [d for d in diffs if d != 0]
            report[f"{variety}|{season}"] = {
                "index_days": len(keys), "days_lost": len(keys) - len(kept), "days_changed": len(changed),
                "median_abs_change_of_changed": statistics.median(abs(d) for d in changed) if changed else 0,
                "max_abs_change": max((abs(d) for d in changed), default=0),
                "mean_change_all_kept_days": statistics.mean(diffs) if diffs else 0,
                "index_days_at_msp_before": sum(1 for k in keys if is_like_value(base[k])),
            }
    return report


MSPS = msp_by_season()


def is_like_value(r):
    return any(abs(float(r["index_modal"]) - v) <= TOLERANCE_RS for v in MSPS.get(r["season"], []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    with open(TIDY, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    base = read_index(BASE)
    rebuilt = {(r["variety"], r["date"]): r for r in build(rows)}
    control = {k: float(v["index_modal"]) for k, v in rebuilt.items()} == {k: float(v["index_modal"]) for k, v in base.items()}
    if not control:
        raise SystemExit("REFUSED: the rebuilt index differs from index_dated_only.csv")
    in_scope = [r for r in rows if r["variety_raw"] in bi.VARIETIES and r["date"] and r["modal_price"] != "" and r["date_inferred"] != "1"]
    like = [r for r in in_scope if is_msp_like(r, MSPS)]
    counts = Counter((bi.season(r["date"]), r["variety_raw"]) for r in like)
    totals = Counter((bi.season(r["date"]), r["variety_raw"]) for r in in_scope)
    like_ids = {r["row_id"] for r in like}
    filters = {"excl_msp_2025_26": lambda r: r["row_id"] in like_ids and bi.season(r["date"]) == "2025-26",
               "excl_msp_all": lambda r: r["row_id"] in like_ids}
    summary = {"status": "POST-HOC EXPLORATORY: not part of the frozen protocol; never replaces the primary result",
               "rule": f"modal within Rs {TOLERANCE_RS:g} of the season's paddy Grade-A or common MSP",
               "control_rebuilt_index_equals_primary": control, "dated_rows_in_scope": len(in_scope), "msp_like_rows": len(like),
               "rows_by_season_variety": {f"{s}|{v}": {"msp_like": n, "dated_rows": totals[(s, v)]} for (s, v), n in sorted(counts.items())},
               "markets_top": Counter(r["market_raw"] for r in like).most_common(10),
               "min_eq_max_eq_modal": sum(r["min_price"] == r["max_price"] == r["modal_price"] for r in like), "filters": {}}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, drop in filters.items():
        kept = [r for r in rows if not (r["row_id"] in like_ids and drop(r))]
        idx = build(kept)
        write(OUT_DATA / f"index_{name}.csv", idx)
        summary["filters"][name] = {"rows_removed": len(rows) - len(kept),
                                    "effect": effect(base, {(r["variety"], r["date"]): r for r in idx})}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    if not a.models:
        return
    import run_protocol as rp
    grids = json.loads((CONFIG / "grids.json").read_text())
    chosen = json.loads((CONFIG / "chosen.json").read_text())
    horizons = grids["horizons"]["primary"] + grids["horizons"]["secondary"]
    for name in filters:
        res = rp.run_stage(rp.load_index(OUT_DATA / f"index_{name}.csv"), "sensitivity", grids["families"], horizons, None,
                           grids.get("smallest_detectable_gain"), chosen=chosen, calibration=None, workers=a.workers)
        rp.write_csv(OUT / f"{name}_metrics.csv", res["metrics"])
        rp.write_csv(OUT / f"{name}_inference.csv", res["inference"])
        rp.write_csv(OUT / f"{name}_forecasts.csv", res["forecasts"])
        print(name, Counter(r["verdict"] for r in res["inference"]), flush=True)


if __name__ == "__main__":
    main()
