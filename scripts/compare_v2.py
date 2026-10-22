"""R0: compare the reproduced v2 results with the original v2 result files.

Writes results/R0_v2_reproduction/comparison.csv (one row per compared number) and report.md.
A number "matches" when it is equal after the rounding the paper used (2 decimals for rupees,
3 for MAPE and shares); every other difference is listed, never hidden.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LEG = ROOT / "legacy" / "v2_from_rp_kisan" / "experiments" / "results"
OUT = ROOT / "results" / "R0_v2_reproduction"
NEW = OUT / "artifacts" / "work" / "results"


def table_rows(name: str, key: str, decimals: int) -> list[dict]:
    a = pd.read_csv(LEG / name).set_index(key)
    b = pd.read_csv(NEW / name).set_index(key)
    rows = []
    for idx in a.index:
        for col in a.columns:
            va, vb = a.loc[idx, col], b.loc[idx, col] if idx in b.index else float("nan")
            try:
                fa, fb = float(va), float(vb)
            except (TypeError, ValueError):
                continue
            rows.append({"file": name, "row": str(idx), "column": col, "v2": fa, "reproduced": fb,
                         "abs_diff": abs(fa - fb), "match_at_paper_rounding": round(fa, decimals) == round(fb, decimals)})
    return rows


def description_rows() -> list[dict]:
    a = json.load(open(LEG / "forecast_results.json"))["description"]
    b = json.load(open(NEW / "forecast_results.json"))["description"]
    rows = []
    for k, va in a.items():
        vb = b.get(k)
        items = va.items() if isinstance(va, dict) else [("", va)]
        for sub, x in items:
            y = vb[sub] if isinstance(vb, dict) else vb
            rows.append({"file": "forecast_results.json:description", "row": k, "column": sub, "v2": float(x),
                         "reproduced": float(y), "abs_diff": abs(float(x) - float(y)),
                         "match_at_paper_rounding": round(float(x), 3) == round(float(y), 3)})
    return rows


def main() -> None:
    rows = description_rows()
    rows += table_rows("forecast_table.csv", "Model", 2)
    rows += table_rows("allocation_summary_base.csv", "policy", 2)
    sa = pd.read_csv(LEG / "allocation_sensitivity.csv")
    sa.insert(0, "setting", sa.rate_rs_per_q_km.astype(str) + "/" + sa.cap_q_per_mandi_day.astype(str))
    sb = pd.read_csv(NEW / "allocation_sensitivity.csv")
    sb.insert(0, "setting", sb.rate_rs_per_q_km.astype(str) + "/" + sb.cap_q_per_mandi_day.astype(str))
    sa.to_csv(OUT / "artifacts" / "_sa.csv", index=False)
    sb.to_csv(OUT / "artifacts" / "_sb.csv", index=False)
    a, b = sa.set_index("setting"), sb.set_index("setting")
    for idx in a.index:
        for col in a.columns:
            fa, fb = float(a.loc[idx, col]), float(b.loc[idx, col])
            rows.append({"file": "allocation_sensitivity.csv", "row": idx, "column": col, "v2": fa, "reproduced": fb,
                         "abs_diff": abs(fa - fb), "match_at_paper_rounding": round(fa, 2) == round(fb, 2)})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "comparison.csv", index=False)
    bad = df[~df.match_at_paper_rounding]
    lines = ["# R0 — reproduction of the paper v2 results", "",
             "Produced by `scripts/reproduce_v2.sh` and `scripts/compare_v2.py`. Environment: `environment.txt`.", "",
             f"- Numbers compared: {len(df)}",
             f"- Equal at the paper's rounding: {int(df.match_at_paper_rounding.sum())}",
             f"- Different: {len(bad)}", ""]
    if len(bad):
        lines += ["## Differences", "", "| File | Row | Column | v2 | Reproduced | Abs. diff |", "|---|---|---|---|---|---|"]
        for r in bad.itertuples():
            lines.append(f"| {r.file} | {r.row} | {r.column} | {r.v2:.4f} | {r.reproduced:.4f} | {r.abs_diff:.4f} |")
    else:
        lines.append("Every compared number matches the v2 result files at the paper's rounding.")
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
