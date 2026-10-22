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


def l3d_allocation() -> dict[str, str]:
    """R7 / L3d: allocation and fairness (layers/L3d_allocation_fairness/, results/L3d_allocation/)."""
    out: dict[str, str] = {}
    base = RESULTS / "L3d_allocation"
    oracle = _json(base / "oracle_agreement.json")
    out["alloc_oracle_cases"] = f"{oracle['cases']:,}"
    out["alloc_oracle_agree"] = f"{oracle['agree']:,}"
    for solver, r in oracle.get("by_solver", {}).items():
        out[f"alloc_oracle_agree_{solver}"] = f"{r['agree']:,}"
        out[f"alloc_oracle_cases_{solver}"] = f"{r['cases']:,}"
    for r in _csv(base / "allocation_policies_summary.csv"):
        key = r["policy_key"]
        for col, fmt in [("net_rs_per_q", "{:,.2f}"), ("min_fulfilment_pct", "{:.1f}"), ("gini_fulfilment", "{:.3f}"),
                         ("allocated_pct", "{:.1f}"), ("price_of_fairness_rs_per_q", "{:.2f}"),
                         ("runs_with_violation_pct", "{:.0f}")]:
            if r.get(col, "") != "":
                out[f"alloc_{key}_{col}"] = fmt.format(float(r[col]))
    for k, v in _json(base / "allocation_settings.json").get("paper_numbers", {}).items():
        out[f"alloc_{k}"] = str(v)
    for r in _csv(base / "allocation_scaling_summary.csv"):
        out[f"alloc_scaling_{r['key']}"] = r["value"]
    for r in _csv(base / "allocation_sensitivity_summary.csv"):
        out[f"alloc_sens_{r['key']}"] = r["value"]
    return out


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


LOADERS: list[tuple[str, Callable[[], dict[str, str]]]] = [
    ("R0 reproduction of v2", r0_reproduction),
    ("3.6 / 4.4 allocation and fairness", l3d_allocation),
    ("3.4 / 4.2 storage rules (simulated)", l3b_storage),
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
             r"\providecommand\kn[1]{\ifcsname kn@#1\endcsname\csname kn@#1\endcsname\else\textbf{??#1??}\fi}"]
    for k in sorted(numbers):
        v = numbers[k].replace("%", r"\%")
        lines.append(rf"\expandafter\def\csname kn@{k}\endcsname{{{v}}}")
    TEX_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    numbers, status = collect()
    for name, fn in LOADERS:
        print(f"== {name}: {status[name]}")
        prefix = {"R0 reproduction of v2": "r0_", "3.4 / 4.2 storage rules (simulated)": "stor_"}.get(name, "alloc_")
        for k in sorted(k for k in numbers if k.startswith(prefix)):
            print(f"   {k:48s} {numbers[k]}")
    if "--tex" in sys.argv:
        write_tex(numbers)
        print(f"wrote {TEX_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
