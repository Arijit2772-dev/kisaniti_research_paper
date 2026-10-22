"""Figure and table for the L3b storage experiment, read only from results/L3b_storage/.

    .venv/bin/python layers/L3b_storage_iot/make_figures.py

Writes paper/figures/fig_storage_scenarios.{pdf,svg,png} and paper/tables/table_storage_rules.tex.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "paper" / "figures"))
import style  # noqa: E402

RES = ROOT / "results" / "L3b_storage"
FIG = ROOT / "paper" / "figures" / "fig_storage_scenarios"
TABLE = ROOT / "paper" / "tables" / "table_storage_rules.tex"

# Severity is ordered, so it uses one hue light -> dark (the decision-layer colour); UNKNOWN is white + hatch.
CAT_COLOR = {
    "LOW": style.tint(style.PALETTE["decision"], 0.72),
    "MEDIUM": style.PALETTE["decision"],
    "HIGH": style.shade(style.PALETTE["decision"], 0.5),
    "UNKNOWN": style.WHITE,
}
STRIPS = [("reference", "Intended"), ("DEMO", "STORAGE-DEMO-0.1"), ("INSTANT", "Instant (no median)"),
          ("AMBIENT_RH", "Shed-air RH"), ("TEMP_ONLY", "Temperature only")]
PANELS = [("S2_monsoon_hold", "(a) Basmati held into the monsoon"),
          ("S3_fresh_wet", "(b) Freshly harvested, sun-dried on day 8"),
          ("S4_outages", "(c) Monsoon hold with Wi-Fi and power outages"),
          ("S5_open_air", "(d) Probe hung in shed air instead of the grain")]
SCEN_SHORT = {"S1_winter_dry": "S1 dry, Nov--Feb", "S2_monsoon_hold": "S2 monsoon hold",
              "S3_fresh_wet": "S3 fresh, then dried", "S4_outages": "S4 outages",
              "S5_open_air": "S5 probe in air", "S6_boundary": "S6 near 0.65"}
RULE_SHORT = {"DEMO": "DEMO", "INSTANT": "Instant", "AMBIENT_RH": "Shed RH", "TEMP_ONLY": "Temp."}


def _runs(cats: list[str]) -> list[tuple[int, int, str]]:
    out, start = [], 0
    for i in range(1, len(cats) + 1):
        if i == len(cats) or cats[i] != cats[start]:
            out.append((start, i, cats[start]))
            start = i
    return out


def figure() -> None:
    style.apply()
    plt.rcParams["hatch.color"] = style.FUTURE
    plt.rcParams["hatch.linewidth"] = 0.4
    traces = json.loads((RES / "traces_seed0.json").read_text())
    mm = 1 / 25.4
    fig = plt.figure(figsize=(style.TEXT_WIDTH_MM * mm, 175 * mm))
    outer = fig.add_gridspec(len(PANELS), 1, hspace=0.55, left=0.2, right=0.96, top=0.96, bottom=0.08)
    for p, (key, title) in enumerate(PANELS):
        tr = traces[key]
        start = datetime.fromisoformat(tr["start"])
        hours = [start + timedelta(hours=h + 1) for h in range(tr["hours"])]
        x0, x1 = mdates.date2num(hours[0]), mdates.date2num(hours[-1])
        g = outer[p].subgridspec(2, 1, height_ratios=[1.25, 1.35], hspace=0.08)
        ax = fig.add_subplot(g[0])
        ax.plot(hours, tr["ambient_rh"], color=style.FUTURE, lw=0.4, label="Shed-air RH")
        ax.plot(hours, tr["probe_rh"], color=style.PALETTE["data"], lw=1.0,
                label="Probe RH" if key != "S5_open_air" else "Probe RH (in air)")
        if key == "S5_open_air":
            ax.plot(hours, [100 * a for a in tr["grain_aw"]], color=style.PALETTE["data"], lw=1.0, ls=(0, (3, 2)),
                    label="Grain (not measured)")
        for y in (65, 70):
            ax.axhline(y, color=style.MUTED, lw=0.5, ls=(0, (1, 1.5)))
        ax.set_xlim(x0, x1)
        ax.set_ylim(25, 122)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_ylabel("RH (%)", fontsize=7)
        ax.set_title(title, fontsize=7.5, loc="left", fontweight="bold", pad=3)
        ax.tick_params(labelbottom=False, labelsize=6.5, length=2)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.legend(fontsize=6.3, frameon=False, ncol=3, loc="upper left", bbox_to_anchor=(0, 1.04),
                  handlelength=1.6, columnspacing=1.0)

        sx = fig.add_subplot(g[1], sharex=ax)
        for row, (rule, label) in enumerate(STRIPS):
            y = len(STRIPS) - 1 - row
            for a, b, c in _runs(tr[rule]):
                xa = mdates.date2num(hours[a]) - 1 / 48
                xb = mdates.date2num(hours[b - 1]) + 1 / 48
                sx.add_patch(Rectangle((xa, y + 0.12), xb - xa, 0.76, facecolor=CAT_COLOR[c],
                                       edgecolor=style.FUTURE if c == "UNKNOWN" else "none",
                                       hatch="//////" if c == "UNKNOWN" else None, linewidth=0))
            sx.text(-0.01, y + 0.5, label, transform=sx.get_yaxis_transform(), ha="right", va="center", fontsize=6.5,
                    fontweight="bold" if rule == "DEMO" else "normal", color=style.INK)
        sx.set_ylim(0, len(STRIPS))
        sx.set_yticks([])
        sx.set_xlim(x0, x1)
        for s in ("top", "right", "left"):
            sx.spines[s].set_visible(False)
        sx.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=7))
        sx.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        sx.tick_params(labelsize=6.5, length=2)
        if key == "S4_outages":
            for d, h in ((10, 30), (25, 6), (35, 2)):
                t = start + timedelta(days=d)
                ax.axvspan(mdates.date2num(t), mdates.date2num(t + timedelta(hours=h)), color=style.FUTURE,
                           alpha=0.3, lw=0)
                ax.text(mdates.date2num(t + timedelta(hours=h / 2)), 30, "Wi-Fi" if d != 25 else "power",
                        fontsize=6, color=style.MUTED, ha="center", va="bottom")
    handles = [Patch(facecolor=CAT_COLOR[c], edgecolor=style.FUTURE if c == "UNKNOWN" else "none",
                     hatch="////" if c == "UNKNOWN" else None, label=c.capitalize() if c != "UNKNOWN" else "Unknown")
               for c in ("LOW", "MEDIUM", "HIGH", "UNKNOWN")]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=6.8, frameon=False, bbox_to_anchor=(0.58, 0.0),
               title="Category (simulated data, seed 0)", title_fontsize=6.8)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(FIG.with_suffix(f".{ext}"), dpi=600 if ext == "png" else None)
    plt.close(fig)


def _fmt(v: str, pct: bool = True) -> str:
    if v == "":
        return "--"
    x = float(v)
    return f"{100 * x:.0f}" if pct else f"{x:.1f}"


def table() -> None:
    rows = [r for r in csv.DictReader((RES / "summary.csv").open()) if float(r["rh_bias"]) == 0.0]
    rules = list(RULE_SHORT)
    lines = [
        "% Generated by layers/L3b_storage_iot/make_figures.py from results/L3b_storage/summary.csv. Do not edit.",
        "\\begin{table}",
        "\\caption{Storage rules on six simulated basmati scenarios (20 seeds, no sensor bias). Agreement is the share",
        " of known hours on which a rule gives the intended category; changes are category changes per week; Unknown",
        " is the share of hours with no category. Simulated data: rule behaviour only, not spoilage.}",
        "\\label{tab:storage_rules}",
        "\\centering\\scriptsize\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{l" + "rrr" * 0 + "|".join(["cccc"] * 3) + "}",
        "\\hline",
        " & \\multicolumn{4}{c|}{Agreement (\\%)} & \\multicolumn{4}{c|}{Changes per week}"
        " & \\multicolumn{4}{c}{Unknown (\\%)} \\\\",
        "Scenario & " + " & ".join([RULE_SHORT[r] for r in rules] * 3) + " \\\\",
        "\\hline",
    ]
    for sc in SCEN_SHORT:
        by = {r["rule"]: r for r in rows if r["scenario"] == sc}
        cells = [_fmt(by[r]["agreement_known_mean"]) for r in rules]
        cells += [_fmt(by[r]["flips_per_week_mean"], pct=False) for r in rules]
        cells += [_fmt(by[r]["share_unknown_mean"]) for r in rules]
        lines.append(f"{SCEN_SHORT[sc]} & " + " & ".join(cells) + " \\\\")
    lines += ["\\hline", "\\end{tabular}", "\\end{table}", ""]
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    TABLE.write_text("\n".join(lines))


if __name__ == "__main__":
    figure()
    table()
    print("wrote", FIG.with_suffix(".pdf"), "and", TABLE)
