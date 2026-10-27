"""Every number quoted in the paper, read from script-written result files (never typed by hand).

    python3 paper/numbers.py            # print all numbers, grouped by section
    python3 paper/numbers.py --tex      # also write paper/template/numbers.tex (\\kn{key} macros)

Each loader reads one results folder and returns {macro_key: formatted string}. A loader whose
results do not exist yet reports NOT_RUN instead of inventing a value; its keys then print as
??key?? in the PDF. The legacy v2 macros stay in template/numbers_v2.tex (make_numbers_tex.py);
keys here use their own prefixes (r0_, alloc_) so the two files never collide.
"""
from __future__ import annotations

import csv
import json
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TEX_OUT = Path(__file__).resolve().parent / "template" / "numbers.tex"


class NotRun(Exception):
    """The results this loader needs have not been produced yet."""


def _csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise NotRun(str(path.relative_to(ROOT)))
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _json(path: Path) -> dict:
    if not path.exists():
        raise NotRun(str(path.relative_to(ROOT)))
    return json.loads(path.read_text())


def r0_reproduction() -> dict[str, str]:
    """R0: paper v2 re-run with the pinned environment (scripts/reproduce_v2.sh)."""
    rows = _csv(RESULTS / "R0_v2_reproduction" / "comparison.csv")
    same = sum(r["match_at_paper_rounding"] == "True" for r in rows)
    return {"r0_numbers_compared": str(len(rows)), "r0_numbers_equal": str(same),
            "r0_numbers_different": str(len(rows) - same)}


def allocation_oracle() -> dict[str, str]:
    """E.1b: solver against the brute-force oracle on random tiny cases (results/L3d_allocation/oracle_agreement.json)."""
    o = _json(RESULTS / "L3d_allocation" / "oracle_agreement.json")
    out = {"alloc_oracle_cases": f"{o['cases']:,}", "alloc_oracle_agree": f"{o['agree']:,}", "alloc_oracle_instances": str(o["instances"])}
    for solver, r in o["by_solver"].items():
        out[f"alloc_oracle_agree_{solver}"] = f"{r['agree']:,}"
        out[f"alloc_oracle_cases_{solver}"] = f"{r['cases']:,}"
    return out


def allocation_sensitivity() -> dict[str, str]:
    """E.3: the policy comparison under 3 x 3 transport rates and mandi-day limits."""
    out = {f"alloc_sens_{r['key']}": r["value"] for r in _csv(RESULTS / "L3d_allocation" / "allocation_sensitivity_summary.csv")}
    rows = _csv(RESULTS / "L3d_allocation" / "allocation_sensitivity.csv")
    pof = {(r["rate_rs_per_q_km"], r["cap_q_per_mandi_day"], r["policy_key"]): float(r["price_of_fairness_rs_per_q"]) for r in rows}
    settings = {(a, b) for a, b, _ in pof}
    out["alloc_sens_greedy_costlier"] = str(sum(pof[(a, b, "greedy")] > pof[(a, b, "kisaniti")] for a, b in settings))
    return out


def allocation_scaling() -> dict[str, str]:
    """E.2: solve time against FPO size, three back ends and the greedy heuristic."""
    return {f"alloc_scaling_{r['key']}": r["value"] for r in _csv(RESULTS / "L3d_allocation" / "allocation_scaling_summary.csv")}


def l3b_storage() -> dict[str, str]:
    """R5 / L3b: storage rules on simulated basmati scenarios (layers/L3b_storage_iot/, results/L3b_storage/)."""
    base = RESULTS / "L3b_storage"
    rows = _csv(base / "summary.csv")
    settings = _json(base / "settings.json")
    traces = _json(base / "traces_seed0.json")
    sc_code = {f"S{i}": f"s{i}" for i in range(1, 7)}
    rule_code = {"DEMO": "demo", "INSTANT": "instant", "AMBIENT_RH": "shed", "TEMP_ONLY": "temp"}
    bias_code = {0.0: "", 2.0: "_biasplus", -2.0: "_biasminus"}

    def pct(v: str) -> str:
        return "--" if v == "" else f"{100 * float(v):.0f}"

    out: dict[str, str] = {"stor_seeds": str(len(settings["seeds"])), "stor_scenarios": str(len(settings["scenarios"]))}
    for r in rows:
        key = f"stor_{sc_code[r['scenario'][:2]]}_{rule_code[r['rule']]}"
        b = bias_code[float(r["rh_bias"])]
        out[f"{key}_agree{b}"] = pct(r["agreement_known_mean"])
        out[f"{key}_unknown{b}"] = pct(r["share_unknown_mean"])
        out[f"{key}_high{b}"] = pct(r["share_high_mean"])
        out[f"{key}_falsehigh{b}"] = pct(r["false_high_share_mean"])
        out[f"{key}_missedhigh{b}"] = pct(r["missed_high_share_mean"])
        out[f"{key}_flips{b}"] = "--" if r["flips_per_week_mean"] == "" else f"{float(r['flips_per_week_mean']):.1f}"
        d = r["high_delay_h_mean"]
        out[f"{key}_highdelay{b}"] = "--" if d == "" else f"{float(d):.0f}"
    base_rows = [r for r in rows if float(r["rh_bias"]) == 0.0 and r["scenario"] != "S5_open_air"]
    for rule, code in rule_code.items():
        f = [float(r["flips_per_week_mean"]) for r in base_rows if r["rule"] == rule]
        out[f"stor_{code}_flips_min"], out[f"stor_{code}_flips_max"] = f"{min(f):.1f}", f"{max(f):.1f}"
        a = [float(r["agreement_known_mean"]) for r in base_rows if r["rule"] == rule]
        out[f"stor_{code}_agree_min"], out[f"stor_{code}_agree_max"] = pct(str(min(a))), pct(str(max(a)))
    # sensor bias, scenarios S1-S4 (in grain, moving conditions)
    for bias, tag in ((2.0, "biasplus"), (-2.0, "biasminus")):
        sel = [r for r in rows if r["rule"] == "DEMO" and float(r["rh_bias"]) == bias and r["scenario"][:2] in ("S1", "S2", "S3", "S4")]
        a = [float(r["agreement_known_mean"]) for r in sel]
        m = [float(r["missed_high_share_mean"]) for r in sel]
        fh = [float(r["false_high_share_mean"]) for r in sel]
        out[f"stor_demo_agree_{tag}_min"], out[f"stor_demo_agree_{tag}_max"] = pct(str(min(a))), pct(str(max(a)))
        out[f"stor_demo_missedhigh_{tag}_max"] = pct(str(max(m)))
        out[f"stor_demo_falsehigh_{tag}_max"] = pct(str(max(fh)))
    out["stor_s4_lost_samples"] = str(traces["S4_outages"]["lost_samples"])
    out["stor_s1_grain_aw_max"] = f"{max(traces['S1_winter_dry']['grain_aw']):.3f}"
    return out


def allocation_policies() -> dict[str, str]:
    """E.1: the 60-plan policy comparison without the weighted-sum policies (results/L3d_allocation/)."""
    base = RESULTS / "L3d_allocation"
    out: dict[str, str] = {}
    for r in _csv(base / "allocation_policies_summary_no_weighted.csv"):
        k = r["policy_key"]
        out[f"allpol_{k}_runs"] = r["runs"]
        for col, fmt in [("net_rs_per_q", "{:,.2f}"), ("min_fulfilment_pct", "{:.1f}"), ("gini_fulfilment", "{:.4f}"),
                         ("allocated_pct", "{:.1f}"), ("price_of_fairness_rs_per_q", "{:.2f}"),
                         ("runs_with_violation_pct", "{:.0f}"), ("all_valid_pct", "{:.0f}"), ("seconds_mean", "{:.2f}"),
                         ("seconds_max", "{:.1f}"), ("gain_vs_p1_actual_rs_per_q", "{:.2f}")]:
            if r.get(col, "") != "":
                out[f"allpol_{k}_{col}"] = fmt.format(float(r[col]))
    runs = _csv(base / "allocation_policies_runs_no_weighted.csv")
    out["allpol_plans"] = str(len({(r["seed"], r["week"]) for r in runs}))
    out["allpol_exact_proven"] = str(sum(1 for r in runs if r["status"].endswith("PROVEN_OPTIMAL")))
    out["allpol_exact_solves"] = str(sum(1 for r in runs if "/" in r["status"]))
    return out


def system_evidence() -> dict[str, str]:
    """The built system: collected test counts, contract files, migrations and a full chain run."""
    e = _json(RESULTS / "S1_system" / "system_evidence.json")
    out = {f"sys_tests_{k}": f"{v:,}" for k, v in e["tests_collected"].items()}
    out["sys_tests_total"] = f"{sum(e['tests_collected'].values()):,}"
    out["sys_slices"] = str(len(e["contract_slices"]))
    out["sys_examples_valid"], out["sys_examples_invalid"] = str(e["contract_examples"]["valid"]), str(e["contract_examples"]["invalid"])
    out["sys_migrations"] = str(e["migrations"])
    c = e["chain"]
    out["sys_chain_steps"], out["sys_chain_passed"] = str(len(c["steps"])), str(c["steps_passed"])
    out["sys_chain_full"] = "yes" if c["full_run"] and c["ok"] else "no"
    out["sys_chain_seconds"] = f"{c['seconds']:.0f}"
    return out


def protocol_pairs() -> dict[str, str]:
    """C.0: (origin, target) pairs per variety and horizon in the test season after the eligibility rule (dates only)."""
    code = {"1121": "1121", "Basmati 1509": "1509"}
    out: dict[str, str] = {}
    for r in _csv(RESULTS / "C0_protocol" / "eligible_pairs.csv"):
        if r["variant"] != "dated_only":
            continue
        out[f"pairs_{code[r['variety']]}_h{r['horizon_days']}"] = r["2025-26 eligible"]
        out[f"pairs_{code[r['variety']]}_h{r['horizon_days']}_raw"] = r["2025-26 raw"]
    return out


def forecast_test_results() -> dict[str, str]:
    """C.0 test-season results of the pre-registered comparison. NOT_RUN until the protocol is frozen and run."""
    code = {"1121": "1121", "Basmati 1509": "1509"}
    base = RESULTS / "C0_protocol"
    out: dict[str, str] = {}
    for r in _csv(base / "test_season_results.csv"):
        k = f"fc_{code[r['variety']]}_{r['horizon']}_{r['model']}"
        out[f"{k}_mae"], out[f"{k}_mase"], out[f"{k}_pairs"] = f"{float(r['mae']):.0f}", f"{float(r['mase']):.2f}", r["pairs"]
    for r in _csv(base / "test_season_inference.csv"):
        k = f"inf_{code[r['variety']]}_{r['horizon']}_{r['model']}"
        out[f"{k}_rel"] = f"{100 * float(r['relative_change']):+.1f}"
        out[f"{k}_p"] = f"{float(r['p_holm']):.3f}"
        out[f"{k}_verdict"] = {"BETTER": "better", "NO_DETECTABLE_DIFFERENCE": "no detectable difference"}.get(r["verdict"], r["verdict"])
    for r in _csv(base / "test_ranges.csv"):
        k = f"rng_{code[r['variety']]}_{r['horizon']}_{r['model']}_{r['range_method']}_{r['level']}"
        out[f"{k}_cov"], out[f"{k}_width"] = f"{100 * float(r['coverage']):.0f}", f"{float(r['mean_width']):.0f}"
    prim = [r for r in _csv(base / "test_ranges.csv") if r["horizon"] in ("1", "7", "14")]
    for method, tag in (("native", "native"), ("conformal", "conf")):
        sel = [r for r in prim if r["range_method"] == method]
        out[f"rng_{tag}_total"] = str(len(sel))
        out[f"rng_{tag}_calibrated"] = str(sum(r["calibrated"] == "True" for r in sel))
        out[f"rng_{tag}_over"] = str(sum(float(r["coverage_ci_low"]) > int(r["level"]) / 100 for r in sel))  # interval wholly above nominal
        out[f"rng_{tag}_under"] = str(sum(float(r["coverage_ci_high"]) < int(r["level"]) / 100 for r in sel))
    inf = _csv(base / "test_season_inference.csv")
    out["inf_total"], out["inf_better"] = str(len(inf)), str(sum(r["verdict"] == "BETTER" for r in inf))
    out["inf_worse_sig"] = str(sum(float(r["p_holm"]) < 0.05 and float(r["relative_change"]) > 0 for r in inf))
    excl = [float(r["ci_low"]) > -float(r["smallest_gain"]) for r in inf]
    out["inf_excl_gain"], out["inf_inconclusive"] = str(sum(excl)), str(len(inf) - sum(excl))
    out["inf_h1_1121_inconclusive"] = str(sum(1 for r, e in zip(inf, excl, strict=True) if not e and r["variety"] == "1121" and r["horizon"] == "1"))
    widths = sorted(float(r["ci_high"]) - float(r["ci_low"]) for r in inf)
    out["inf_width_median"] = f"{100 * (widths[len(widths) // 2 - 1] + widths[len(widths) // 2]) / 2:.0f}"
    return out


def data_cleaning() -> dict[str, str]:
    """B.1/B.4: rows, manifests and index days of the basmati data; the hand-check sheet (results/L2_cleaning, data/)."""
    rows = _csv(RESULTS / "L2_cleaning" / "reconciliation.csv")
    out = {"data_manifests": str(len(rows)),
           "data_rows_total": f"{sum(int(r['data_rows']) for r in rows):,}",
           "data_rows_dated": f"{sum(int(r['dated']) for r in rows):,}",
           "data_rows_blank": f"{sum(int(r['blank_date']) for r in rows):,}"}
    out["data_handcheck_rows"] = str(len(_csv(RESULTS / "L2_cleaning" / "hand_check_sheet.csv")))
    idx = _csv(ROOT / "data" / "processed" / "basmati" / "index_dated_only.csv")
    for v, code in (("1121", "1121"), ("Basmati 1509", "1509")):
        out[f"data_index_days_{code}"] = str(sum(1 for r in idx if r["variety"] == v))
    return out


def hand_check() -> dict[str, str]:
    """B.2: the 56-row inspection against the live portal (agent inspection; the owner's sign-off is separate)."""
    d = _json(RESULTS / "L2_cleaning" / "hand_check_summary.json")
    c, b, r = d["recomputed_counts"], d["blank_date_rule_c0"], d["independent_replication"]
    return {"hc_rows": str(c["ids"]), "hc_modal": str(c["modal_match"]), "hc_numeric": str(c["numeric_match"]),
            "hc_arr_differ": str(c["arrivals_differ"]), "hc_missing_zero": str(c["missing_vs_zero"]), "hc_union": str(c["union"]),
            "hc_inferred": str(b["rows_with_inferred_date_in_sheet"]), "hc_inferred_ok": str(b["confirmed_same_date_same_prices_under_preceding_date"]),
            "hc_repl": str(r["rows_replicated_by_claude"]), "hc_repl_same": str(r["live_values_identical_to_codex"])}


def validator_agreement() -> dict[str, str]:
    """Stage 3: the independent plan validator against a second checker written from the rules, on random edits."""
    v = _json(RESULTS / "L3d_allocation" / "validator_agreement.json")
    return {"val_instances": str(v["instances"]), "val_edits": f"{v['edits']:,}", "val_agree": f"{v['agree']:,}",
            "val_valid": f"{v['expected_valid']:,}", "val_invalid": f"{v['expected_invalid']:,}", "val_kinds": str(len(v["by_kind"]))}


def cleaning_screens() -> dict[str, str]:
    """B.3a: what four outlier screens flag and how far excluding the flagged rows would move the index."""
    out: dict[str, str] = {}
    for r in _csv(RESULTS / "L2_cleaning" / "screen_comparison.csv"):
        k = r["rule"].replace(".", "").replace("_", "")
        out[f"scr_{k}_flagged_pct"] = f"{float(r['share_flagged_pct']):.1f}"
        out[f"scr_{k}_flagged"] = f"{int(r['rows_flagged']):,}"
        out[f"scr_{k}_changed_1121"] = r["1121_days_changed"]
        out[f"scr_{k}_changed_1509"] = r["1509_days_changed"]
        out[f"scr_{k}_maxchange_1121"] = f"{float(r['1121_max_change_rs']):.0f}"
        out[f"scr_{k}_lost_1121"] = r["1121_days_lost"]
    return out


def prospective_results() -> dict[str, str]:
    """C.0 prospective check, season 2026-27 (partial): pairs and MAE; no test is run on it."""
    code = {"1121": "1121", "Basmati 1509": "1509"}
    out: dict[str, str] = {}
    for r in _csv(RESULTS / "C0_protocol" / "prospective_metrics.csv"):
        k = f"pro_{code[r['variety']]}_{r['horizon']}"
        out[f"{k}_{r['model']}_mae"] = f"{float(r['mae']):.0f}"
        out[f"{k}_pairs"] = r["pairs"]
    return out


def blank_date_plausibility() -> dict[str, str]:
    """B.2c: do rows with an inferred date behave like own-dated rows? (plausibility only; not the hand check)"""
    d = _json(RESULTS / "L2_cleaning" / "blank_date_plausibility.json")
    return {"bd_pairs": str(d["pairs_same_day_one_inferred"]), "bd_control": str(d["pairs_adjacent_day_control"]),
            "bd_ratio_inf": f"{d['ratio_median_one_inferred']:.2f}", "bd_ratio_ctl": f"{d['ratio_median_adjacent_day_control']:.2f}",
            "bd_iqr_inf": f"{d['ratio_iqr_one_inferred']:.2f}", "bd_iqr_ctl": f"{d['ratio_iqr_adjacent_day_control']:.2f}",
            "bd_rows": str(d["inferred_rows"]), "bd_dups": str(d["inferred_rows_on_a_key_with_another_row"])}


def sensitivity_variants() -> dict[str, str]:
    """C.0 section 13, item 18: the same 42 comparisons on the pre-declared index variants (never replacing the primary)."""
    names = ["with_blank", "dated_only_towns", "with_blank_towns", "dated_only_mm2", "dated_only_mm4"]
    done = [n for n in names if (RESULTS / "C0_protocol" / f"sensitivity_{n}_inference.csv").exists()]
    if not done:
        raise NotRun("results/C0_protocol/sensitivity_*_inference.csv")
    comps = better = worse_other = 0
    for n in done:
        for r in _csv(RESULTS / "C0_protocol" / f"sensitivity_{n}_inference.csv"):
            comps += 1
            better += r["verdict"] == "BETTER"
            worse_other += float(r["p_holm"]) < 0.05 and r["model"] != "seasonal_naive"
    return {"sens_done": str(len(done)), "sens_comparisons": str(comps), "sens_better": str(better), "sens_other_significant": str(worse_other)}


LOADERS: list[tuple[str, Callable[[], dict[str, str]]]] = [
    ("R0 reproduction of v2", r0_reproduction),
    ("3.6 / 4.4 allocation: solver against brute force", allocation_oracle),
    ("3.4 manager edits: validator against a second checker", validator_agreement),
    ("4.3 allocation: sensitivity", allocation_sensitivity),
    ("4.3 allocation: scaling", allocation_scaling),
    ("3.4 / 4.2 storage rules (simulated)", l3b_storage),
    ("4.3 allocation policy comparison (60 plans)", allocation_policies),
    ("3 / 4.5 the built system", system_evidence),
    ("3.1 basmati data and cleaning", data_cleaning),
    ("3.1 outlier screens and the index", cleaning_screens),
    ("3.1 blank-date plausibility", blank_date_plausibility),
    ("3.3 pairs per horizon (C.0, dates only)", protocol_pairs),
    ("4.2 pre-registered forecasting results", forecast_test_results),
    ("4.2 prospective check 2026-27 (partial)", prospective_results),
    ("4.2 sensitivity to the index variant", sensitivity_variants),
    ("2 hand check (B.2)", hand_check),
]


def collect() -> tuple[dict[str, str], dict[str, str]]:
    numbers: dict[str, str] = {}
    status: dict[str, str] = {}
    for name, fn in LOADERS:
        try:
            got = fn()
        except NotRun as e:
            status[name] = f"NOT_RUN (missing {e})"
            continue
        clash = set(got) & set(numbers)
        if clash:
            raise RuntimeError(f"duplicate number keys: {sorted(clash)}")
        numbers.update(got)
        status[name] = f"OK ({len(got)} numbers)"
    return numbers, status


def write_tex(numbers: dict[str, str]) -> None:
    lines = ["% Generated by paper/numbers.py from results/. Do not edit by hand.",
             r"\providecommand\kn[1]{\ifcsname kn@#1\endcsname\csname kn@#1\endcsname\else\textbf{??\detokenize{#1}??}\fi}"]
    for k in sorted(numbers):
        v = numbers[k].replace("%", r"\%")
        lines.append(rf"\expandafter\def\csname kn@{k}\endcsname{{{v}}}")
    TEX_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    numbers, status = collect()
    for name, fn in LOADERS:
        print(f"== {name}: {status[name]}")
        prefix = {"R0 reproduction of v2": "r0_", "3.4 / 4.2 storage rules (simulated)": "stor_",
                  "4.3 allocation policy comparison (60 plans)": "allpol_", "3 / 4.5 the built system": "sys_",
                  "3.3 pairs per horizon (C.0, dates only)": "pairs_", "3.1 basmati data and cleaning": "data_", "4.2 pre-registered forecasting results": "fc_"}.get(name, "alloc_")
        for k in sorted(k for k in numbers if k.startswith(prefix)):
            print(f"   {k:48s} {numbers[k]}")
    if "--tex" in sys.argv:
        write_tex(numbers)
        print(f"wrote {TEX_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
