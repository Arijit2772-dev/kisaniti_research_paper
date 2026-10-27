"""Re-checks every number the paper (and the plan documents) states against the result files and the data, and writes
paper/claims_status.csv. A claim is VERIFIED only if this script recomputes or reads the value from a script-written
file and it matches at the stated rounding; FAILED if it does not; PENDING_RUN if the experiment has not been run.
Nothing here is typed in by hand except the claim's stated value.

    env/run scripts/verify_claims.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R0 = ROOT / "results" / "R0_v2_reproduction"
OUT = ROOT / "paper" / "claims_status.csv"
Result = tuple[str, str]  # (status, what the files say)


def msp_shares() -> Result:
    shares = [float(m) for m in re.findall(r"at MSP % ([0-9.]+)", (R0 / "paper_numbers_reproduced.txt").read_text())]
    return ("VERIFIED" if len(shares) == 6 and min(shares) > 96 else "FAILED", f"six seasons, lowest {min(shares)}%")


def msp_rule_mae() -> Result:
    df = pd.read_csv(R0 / "forecast_table.csv").set_index("Model")
    best = df["MAE mean"].idxmin()
    return ("VERIFIED" if best == "MSP rule" and df.loc["MSP rule", "MAE mean"] == 1.26 else "FAILED", f"lowest mean MAE: {best} {df.loc[best, 'MAE mean']}")


def gain_loose() -> Result:
    df = pd.read_csv(R0 / "allocation_summary_base.csv").set_index("policy")
    g = round(float(df.loc["P3 KisanNiti cooperative (MSP-rule price)", "gain_vs_P1_rs_per_q"]), 2)
    return ("VERIFIED" if g == 0.79 else "FAILED", f"P3 gain over P1 {g}")


def gain_tight() -> Result:
    df = pd.read_csv(R0 / "allocation_sensitivity.csv")
    tight = df[df.cap_q_per_mandi_day == 200].gain_rs_per_q.round(1)
    return ("VERIFIED" if tight.min() == 3.5 and tight.max() == 13.9 else "FAILED", f"tight-limit gains {tight.min()} to {tight.max()}")


def p2_violates_every_run() -> Result:
    df = pd.read_csv(R0 / "allocation_summary_base.csv").set_index("policy")
    v = float(df.loc["P2 Independent best choice", "runs_with_violation"])
    return ("VERIFIED" if v == 1.0 else "FAILED", f"share of runs with a limit violation {v}")


def index_days() -> Result:
    d = pd.read_csv(ROOT / "data/processed/basmati/index_dated_only.csv")
    n = d.groupby("variety").size()
    return ("VERIFIED" if n["1121"] == 433 and n["Basmati 1509"] == 369 else "FAILED", f"dated_only index days: {n.to_dict()}")


def rows_reconcile() -> Result:
    rows = list(csv.DictReader((ROOT / "results/L2_cleaning/reconciliation.csv").open()))
    total, dated, blank = (sum(int(r[k]) for r in rows) for k in ("data_rows", "dated", "blank_date"))
    ok = len(rows) == 29 and total == 6678 and dated == 6098 and blank == 580 and dated + blank == total
    return ("VERIFIED" if ok else "FAILED", f"{len(rows)} manifests: {total} rows = {dated} dated + {blank} blank-date")


def hand_check_rows() -> Result:
    n = sum(1 for _ in csv.DictReader((ROOT / "results/L2_cleaning/hand_check_sheet.csv").open()))
    return ("VERIFIED" if n == 56 else "FAILED", f"{n} rows in the sheet (the check itself is not done)")


def hand_check_counts() -> Result:
    """Recount the 56 observations directly from the per-row file (not from the transfer script's own summary)."""
    rows = list(csv.DictReader((ROOT / "results/L2_cleaning/hand_check_observations.csv").open()))
    modal = sum(1 for r in rows if r["file_modal"] and r["live_modal"] and abs(float(r["file_modal"]) - float(r["live_modal"])) < 0.005)
    arr = sum(1 for r in rows if r["arrivals_agree"] == "0")
    miss = sum(1 for r in rows if r["missing_vs_zero"] == "1")
    full = sum(1 for r in rows if r["numeric_match"] == "1")
    got = (len(rows), modal, arr, miss, full)
    return ("VERIFIED" if got == (56, 56, 20, 4, 33) else "FAILED", f"rows, modal agree, arrivals differ, missing-vs-zero, numeric match = {got}; sign-off still pending")


def power_gain() -> Result:
    t = (ROOT / "results/L1_coverage/power_check.txt").read_text()
    out: dict[str, list[float]] = {}
    for variety, gain in re.findall(r"^(1121|Basmati 1509) h=\d+: .*?smallest detectable gain ≈ ([0-9.]+)%", t, re.M):
        out.setdefault(variety, []).append(float(gain))
    ok = (
        round(min(out["1121"])) == 11 and round(max(out["1121"])) == 13 and round(min(out["Basmati 1509"])) == 12
        and round(max(out["Basmati 1509"])) == 17
    )
    return ("VERIFIED" if ok else "FAILED", f"detectable gains {out} (exploratory run, protocol section 1)")


def basmati_movement() -> Result:
    d = pd.read_csv(ROOT / "data/processed/basmati/index_dated_only.csv").sort_values("date")
    x = d[d.variety == "1121"]
    med = x.groupby("season").index_modal.diff().abs().dropna().median()
    gap = (x.max_modal - x.min_modal)
    return ("FAILED", f"1121 median daily change of the index {med}; same-day gap across mandis median {gap.median()}, mean {gap.mean():.0f}, max {gap.max()}; the plan text says 50 and 1,468")


def protocol_pair_counts() -> Result:
    rows = list(csv.DictReader((ROOT / "results/C0_protocol/eligible_pairs.csv").open()))
    low = [(r["variety"], r["horizon_days"], r["2025-26 eligible"]) for r in rows if r["variant"] == "dated_only" and r["horizon_days"] in ("1", "7", "14") and int(r["2025-26 eligible"]) < 60]
    return ("FAILED" if low else "VERIFIED", f"primary horizons under 60 test pairs after the eligibility rule: {low}")


def independent_check() -> Result:
    import json

    d = json.loads((ROOT / "results/C0_protocol/independent_check.json").read_text())
    return ("VERIFIED" if d["agrees"] and d["comparisons"] == 42 else "FAILED", f"exact quantities agree to {max(d['max_abs_difference'][k] for k in ('mae', 'dm', 'p_raw', 'p_holm', 'rel')):.1e}; bootstrap ends within {d['max_abs_difference']['ci']:.2f} of the interval width")


def forecasts_run() -> Result:
    p = ROOT / "results" / "C0_protocol" / "test_season_inference.csv"
    if not p.exists():
        return ("PENDING_RUN", "the test season has not been run")
    d = pd.read_csv(p)
    better = d[d.verdict == "BETTER"]
    return ("VERIFIED" if len(better) == 0 and len(d) == 42 else "FAILED", f"{len(d)} comparisons with naive at 1, 7, 14 days; {len(better)} judged better by the pre-registered rule")


def only_seasonal_naive_worse() -> Result:
    d = pd.read_csv(ROOT / "results" / "C0_protocol" / "test_season_inference.csv")
    worse = d[(d.p_holm < 0.05) & (d.relative_change > 0)]
    return ("VERIFIED" if len(worse) == 3 and set(worse.model) == {"seasonal_naive"} else "FAILED", f"significantly worse than naive: {sorted(zip(worse.variety, worse.horizon, worse.model, strict=True))}")


def oracle_agreement() -> Result:
    import json

    o = json.loads((ROOT / "results/L3d_allocation/oracle_agreement.json").read_text())
    ok = o["cases"] == o["agree"] and o["cases"] > 0 and all(v["cases"] == v["agree"] for v in o["by_solver"].values())
    return ("VERIFIED" if ok else "FAILED", f"{o['agree']} of {o['cases']} runs equal the brute-force optimum ({o['instances']} instances)")


def validator_agreement() -> Result:
    import json

    v = json.loads((ROOT / "results/L3d_allocation/validator_agreement.json").read_text())
    ok = v["edits"] == v["agree"] and v["expected_valid"] > 0 and v["expected_invalid"] > 0
    return ("VERIFIED" if ok else "FAILED", f"{v['agree']} of {v['edits']} edits get the same verdict ({v['expected_valid']} valid, {v['expected_invalid']} invalid)")


def policy_run() -> Result:
    runs = pd.read_csv(ROOT / "results/L3d_allocation/allocation_policies_runs_no_weighted.csv")
    kis = runs[runs.policy_key == "kisaniti"]
    exact = runs[runs.status.str.contains("/")]
    ok = len(kis) == 60 and bool(kis.valid.all()) and exact.status.str.endswith("PROVEN_OPTIMAL").all()
    return ("VERIFIED" if ok else "FAILED", f"{len(kis)} plans, all valid: {bool(kis.valid.all())}; exact solves proven optimal: {int(exact.status.str.endswith('PROVEN_OPTIMAL').sum())} of {len(exact)}")


def sensitivity_valid() -> Result:
    d = pd.read_csv(ROOT / "results/L3d_allocation/allocation_sensitivity.csv")
    k = d[d.policy_key == "kisaniti"]
    ok = len(k) == 9 and bool((k.all_valid_pct == 100).all())
    return ("VERIFIED" if ok else "FAILED", f"{len(k)} settings, KisanNiti plans valid in all: {bool((k.all_valid_pct == 100).all())}")


def prospective_naive() -> Result:
    m = pd.read_csv(ROOT / "results/C0_protocol/prospective_metrics.csv")
    x = m[(m.variety == "Basmati 1509") & (m.horizon.isin([7, 14]))]
    lowest = x.loc[x.groupby("horizon").mae.idxmin()]
    return ("VERIFIED" if set(lowest.model) == {"naive"} else "FAILED", f"lowest MAE at 7 and 14 days (1509, 2026-27 partial): {dict(zip(lowest.horizon, lowest.model, strict=True))}")


def scaling_valid() -> Result:
    d = pd.read_csv(ROOT / "results/L3d_allocation/allocation_scaling.csv")
    returned = d[d.status != "NOT_APPLICABLE/NONE"]
    ok = bool(returned.valid.all()) and len(returned) > 40
    proven = d[(d.solver.isin(["highs", "scip"])) & (d.farmers <= 100)].status.str.endswith("PROVEN_OPTIMAL").all()
    return ("VERIFIED" if ok and proven else "FAILED", f"{len(returned)} returned plans, all valid: {ok}; HiGHS and SCIP proven optimal up to 100 farmers: {bool(proven)}")


def sensitivity_null() -> Result:
    names = ["with_blank", "dated_only_towns", "with_blank_towns", "dated_only_mm2", "dated_only_mm4"]
    tot = better = other = 0
    for n in names:
        d = pd.read_csv(ROOT / "results" / "C0_protocol" / f"sensitivity_{n}_inference.csv")
        tot += len(d)
        better += int((d.verdict == "BETTER").sum())
        other += int(((d.p_holm < 0.05) & (d.model != "seasonal_naive")).sum())
    return ("VERIFIED" if tot == 210 and better == 0 and other == 0 else "FAILED", f"{tot} comparisons over 5 index variants; better: {better}; significant other than seasonal naive: {other}")


def references_exist() -> Result:
    rows = list(csv.DictReader((ROOT / "literature/crossref_check.csv").open()))
    bad = [r["key"] for r in rows if r["status"].startswith(("DOI_NOT_FOUND", "CANNOT_CHECK"))]
    ok_n = sum(r["status"] == "MATCH" for r in rows)
    return ("VERIFIED" if not bad else "FAILED", f"{ok_n} of {len(rows)} entries match their DOI record; unresolved: {bad}; no DOI (manual): {sum(r['status'] == 'NO_DOI_MANUAL' for r in rows)}")


CLAIMS = [
    ("C01", "Paddy (Common): more than 96% of reports equal the MSP in every season 2020-25", "THE_ONE_PAPER 1; v2 abstract", msp_shares),
    ("C02", "Paddy (Common): the MSP rule has the lowest mean forecast error (Rs 1.26 per quintal); no learned model beats it", "v2 abstract", msp_rule_mae),
    ("C03", "Cooperative plan gains Rs 0.79 per quintal over the nearest-mandi rule with loose limits", "v2 abstract", gain_loose),
    ("C04", "...and Rs 3.5 to 13.9 per quintal with tight limits", "v2 abstract", gain_tight),
    ("C05", "Independent choices exceed a mandi limit in every run", "v2 abstract", p2_violates_every_run),
    ("C06", "Basmati variety index has 433 (1121) and 369 (1509) index days", "protocol 2; THE_ONE_PAPER 3", index_days),
    ("C07", "6,678 basmati rows reconcile with the 29 manifests", "STATUS R3", rows_reconcile),
    ("C08", "The hand-check sheet has 56 rows", "STATUS R3", hand_check_rows),
    ("C23", "Hand check of 56 rows on the live portal: 56 modal prices agree, 33 rows agree fully, 20 differ in arrivals, 4 show a missing bound as zero (agent inspection; owner sign-off pending)", "paper 3.1", hand_check_counts),
    ("C09", "Smallest detectable gain is 11-13% (1121) and 12-17% (1509)", "protocol 8", power_gain),
    ("C10", "Basmati prices move: median daily change Rs 50 per quintal; same-day gap across mandis about Rs 1,468 (1121)", "THE_ONE_PAPER 1", basmati_movement),
    ("C11", "At least 60 test-season pairs per variety at every primary horizon", "protocol 4", protocol_pair_counts),
    ("C12", "No forecasting model beats the naive value on basmati under the pre-registered rule (42 comparisons)", "paper 4.2", forecasts_run),
    ("C18", "The only methods significantly different from naive are worse, and all are seasonal naive", "paper 4.2", only_seasonal_naive_worse),
    ("C13", "The solver reaches the brute-force optimum on every random small instance", "paper 4.3", oracle_agreement),
    ("C14", "The plan validator agrees with a second rule-based checker on every random edit", "paper 4.4", validator_agreement),
    ("C15", "60 plans, all valid, exact solves proven optimal", "paper 4.3", policy_run),
    ("C17", "The KisanNiti plan is valid in every transport-rate and limit setting", "paper 4.3", sensitivity_valid),
    ("C19", "In the partial 2026-27 season the naive value has the lowest MAE for Basmati 1509 at 7 and 14 days", "paper 4.2", prospective_naive),
    ("C20", "Every plan a solver returned in the scaling grid was valid; HiGHS and SCIP proved optimality up to 100 farmers", "paper 4.3", scaling_valid),
    ("C21", "On all five declared index variants no method beats naive; only seasonal naive differs significantly", "paper 4.2", sensitivity_null),
    ("C22", "Independent recomputation of the test statistics agrees with the runner", "paper 4.2", independent_check),
    ("C16", "Every bibliography DOI resolves to a record with the same title", "paper references", references_exist),
]


def main() -> int:
    rows = []
    for cid, text, source, fn in CLAIMS:
        try:
            status, observed = fn()
        except Exception as e:  # a claim that cannot even be checked is not verified
            status, observed = "CANNOT_CHECK", f"{type(e).__name__}: {e}"
        rows.append({"claim": cid, "statement": text, "source": source, "status": status, "observed": observed})
        print(f"{cid} {status:11s} {text[:78]}\n      {observed}")
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    bad = [r["claim"] for r in rows if r["status"] in ("FAILED", "CANNOT_CHECK")]
    print("\nfailed or not checkable:", bad)
    return 0


if __name__ == "__main__":
    sys.exit(main())
