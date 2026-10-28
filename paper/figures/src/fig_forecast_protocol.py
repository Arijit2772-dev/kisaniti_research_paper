"""Fig. 2: the pre-registered basmati forecast comparison (data -> time-ordered seasons -> eight methods -> decision
rule), as four illustrated panels in the style of Fig. 1.

    python3 paper/figures/src/fig_forecast_protocol.py --final

Writes paper/figures/fig_forecast_protocol.{pdf,svg,png}. Everything drawn here was built and run once on the
held-out season (28 Oct 2026, layers/L3a_forecasting/run_protocol.py and results/C0_protocol/); the figure shows the
protocol's fixed design only, so it carries no result numbers (those come from paper/numbers.py into the text).
"""
from __future__ import annotations

import sys
from pathlib import Path

from matplotlib.patches import Rectangle

import figlib as fl
from figlib import style

C = style.PALETTE
W, H = 122.0, 60.0
PY, PH = 0.5, 59.0
TOP = PY + PH - 6.0                       # first line under the title band


def column_item(ax, icon, cx, cy, label, color, r=2.5):
    fl.badge(ax, icon, cx, cy, r, color)
    ax.text(cx, cy - r - 0.7, label, ha="center", va="top", fontsize=7, fontweight="bold", color=style.INK,
            linespacing=1.0, zorder=6)


def seasons(ax, x, y, w):
    """One row of seasons: three to train, one to tune, one held out and run once."""
    rows = [("2021–22", "train"), ("2022–23", "train"), ("2023–24", "train"), ("2024–25", "tune"),
            ("2025–26", "test")]
    fill = {"train": C["cleaning"], "tune": C["outcomes"], "test": C["decision"]}
    hh, gap = 3.0, 0.9
    for i, (lab, kind) in enumerate(rows):
        yy = y - i * (hh + gap)
        ax.text(x, yy + hh / 2, lab, ha="left", va="center", fontsize=7, color=style.INK, zorder=3)
        ax.add_patch(Rectangle((x + 10.6, yy), w - 10.6, hh, facecolor=fill[kind],
                               edgecolor=style.shade(fill[kind], 0.3), lw=0.4, zorder=3))
        ax.text(x + 10.6 + (w - 10.6) / 2, yy + hh / 2, {"train": "train", "tune": "tune",
                                                         "test": "held out"}[kind],
                ha="center", va="center", fontsize=6.6, color=style.on_color(fill[kind]), zorder=4)
    return y - len(rows) * (hh + gap)


def main() -> None:
    fl.set_mode(sys.argv)
    fig, ax = fl.new_figure(W, H)

    # 1 Data and daily index ------------------------------------------------------------------------------------
    xa, wa = 0.5, 28.0
    fl.panel(ax, xa, PY, wa, PH, "Price data", C["data"], 1)
    yy = TOP - 5.0
    for ic, lab, note in [
        ("world-download", "AGMARKNET", "basmati, Punjab,\nmonthly files"),
        ("eraser", "Cleaning", "every row traced,\nflagged, none\nremoved"),
        ("chart-line", "Daily index", "median modal\nprice, ≥3 mandis"),
        ("scale", "Regime test", "MSP crops take\nthe announced\nMSP"),
    ]:
        fl.item(ax, ic, xa + 4.0, yy, lab, note, C["data"], r=2.6, gap=1.2)
        yy -= 13.0 if note.count("\n") > 1 else 11.0

    # 2 Time-ordered seasons --------------------------------------------------------------------------------------
    xb, wb = 31.0, 27.5
    fl.panel(ax, xb, PY, wb, PH, "Seasons", C["cleaning"], 2)
    end = seasons(ax, xb + 1.8, TOP - 5.0, wb - 3.6)
    yy = end - 3.6
    for ic, lab, note in [
        ("lock", "Frozen first", "protocol fixed\nbefore the test"),
        ("calendar-time", "Horizons", "1, 7 and 14 days"),
    ]:
        fl.item(ax, ic, xb + 4.0, yy, lab, note, C["cleaning"], r=2.6, gap=1.2)
        yy -= 10.5

    # 3 Eight methods ---------------------------------------------------------------------------------------------
    xc, wc = 61.0, 30.0
    fl.panel(ax, xc, PY, wc, PH, "Eight methods", C["decision"], 3)
    methods = [
        ("history", "Naive"), ("calendar", "Seasonal\nnaive"),
        ("chart-bar", "5-day\naverage"), ("math-function", "ETS"),
        ("timeline", "ARIMA"), ("git-branch", "LightGBM"),
        ("brain", "GRU"), ("cpu", "Chronos-2"),
    ]
    for k, (ic, lab) in enumerate(methods):
        col, row = k % 2, k // 2
        column_item(ax, ic, xc + wc * (2 * col + 1) / 4, TOP - 4.6 - row * 11.6, lab, C["decision"])
    ax.text(xc + wc / 2, PY + 2.4, "80% and 95% ranges", ha="center", va="center", fontsize=7,
            fontstyle="italic", color=style.MUTED)

    # 4 Decision rule ---------------------------------------------------------------------------------------------
    xd, wd = 93.5, 28.0
    fl.panel(ax, xd, PY, wd, PH, "Decision", C["review"], 4)
    yy = TOP - 5.0
    for ic, lab, note in [
        ("ruler", "Errors", "MAE and MASE,\nRs per quintal"),
        ("checks", "Test vs naive", "Diebold–Mariano,\nHLN correction"),
        ("adjustments", "Many tests", "Holm adjustment,\nbootstrap interval"),
        ("trophy", "Better only if", "p < 0.05, interval\nabove zero, gain\n≥ detectable"),
    ]:
        fl.item(ax, ic, xd + 4.0, yy, lab, note, style.shade(C["review"], 0.25), r=2.6, gap=1.2)
        yy -= 11.0

    # dashed data flow between panels
    mid = PY + PH / 2
    for a, b in [(xa + wa, xb), (xb + wb, xc), (xc + wc, xd)]:
        fl.arrow(ax, [(a + 0.3, mid), (b - 0.3, mid)])

    out = Path(__file__).resolve().parents[1]
    for p in fl.save(fig, out, "fig_forecast_protocol"):
        print(p)


if __name__ == "__main__":
    main()
