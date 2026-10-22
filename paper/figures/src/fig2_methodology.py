"""Fig. 2: forecasting methodology pipeline (data -> time-ordered split -> models compared
-> metrics -> selection), in three illustrated panels.

    python3 paper/figures/src/fig2_methodology.py           # draft (planned parts marked)
    python3 paper/figures/src/fig2_methodology.py --final   # final: unbuilt parts dashed grey

Writes paper/figures/fig2_methodology[_draft].{pdf,svg,png}.

The split grid is read from FOLDS in the forecasting script, so the figure cannot drift
from the experiment. Status as of 22 Oct 2026: built = the v2 paddy comparison
(legacy/v2_from_rp_kisan/experiments/forecast_experiment.py); planned = the Paper 1
additions in the master plan (basmati paddy by variety per CHAT-32, price ranges,
significance tests, coverage, per-variety model selection). Held wheat is not forecast
(CHAT-32: too few off-season Punjab mandi rows) and is not drawn.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

from matplotlib.patches import FancyBboxPatch, Rectangle

import figlib as fl
from figlib import style

C = style.PALETTE
ROOT = Path(__file__).resolve().parents[3]
FORECAST_SCRIPT = ROOT / "legacy" / "v2_from_rp_kisan" / "experiments" / "forecast_experiment.py"
STATUS = {
    "agmarknet": "built", "basmati": "planned", "cleaning": "built", "graph": "built",
    "split": "built",
    "naive": "built", "moving_avg": "built", "msp_rule": "built",
    "ridge": "built", "gru": "built", "tgcn": "built", "a3tgcn": "built",
    "tuning": "built", "ranges": "planned",
    "errors": "built", "paired": "built", "dm_test": "planned", "coverage": "planned",
    "selection": "planned",
}
W, H = 122.0, 79.0


def read_folds() -> list[tuple[list[int], int, int]]:
    tree = ast.parse(FORECAST_SCRIPT.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "FOLDS" for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("FOLDS not found in " + str(FORECAST_SCRIPT))


def column_item(ax, icon, cx, cy, label, note, color, status, r=2.7):
    fl.badge(ax, icon, cx, cy, r, color, status)
    st = fl.shown_status(status)
    lc = style.FUTURE if st == "future" else style.INK
    nc = style.FUTURE if st == "future" else style.MUTED
    ax.text(cx, cy - r - 0.8, label, ha="center", va="top", fontsize=7, fontweight="bold",
            color=lc, zorder=6)
    if note:
        ax.text(cx, cy - r - 3.5, note, ha="center", va="top", fontsize=7, color=nc,
                linespacing=1.0, zorder=6)


def card_title(ax, x, y, text, extra=None):
    ax.text(x, y, text, ha="left", va="center", fontsize=7, fontweight="bold",
            fontstyle="italic", color=style.INK)
    if extra:
        ax.text(x + 0.0, y - 2.9, extra, ha="left", va="center", fontsize=7, color=style.MUTED)


def split_grid(ax, x, y, w, folds, color_train, color_val, color_test):
    """Rows = folds, columns = seasons; train / validation / test cells."""
    seasons = sorted({s for tr, va, te in folds for s in tr + [va, te]})
    label_w = 4.6
    cw = (w - label_w) / len(seasons)
    chh, gap = 2.6, 0.9
    for j, s in enumerate(seasons):
        ax.text(x + label_w + (j + 0.5) * cw, y + 1.6, f"’{s % 100:02d}", ha="center",
                va="center", fontsize=7, color=style.MUTED, zorder=3)
    for i, (tr, va, te) in enumerate(folds):
        yy = y - (i + 1) * (chh + gap)
        ax.text(x, yy + chh / 2, f"F{i + 1}", ha="left", va="center", fontsize=7,
                fontweight="bold", color=style.INK, zorder=3)
        for j, s in enumerate(seasons):
            fc = color_train if s in tr else color_val if s == va else color_test if s == te else style.WHITE
            ec = style.shade(fc, 0.3) if fc != style.WHITE else style.FUTURE
            ax.add_patch(Rectangle((x + label_w + j * cw + 0.3, yy), cw - 0.6, chh, facecolor=fc,
                                   edgecolor=ec, lw=0.4, zorder=3))
    ly = y - len(folds) * (chh + gap) - 2.6
    lx = x
    for name, fc in [("train", color_train), ("val.", color_val), ("test", color_test)]:
        ax.add_patch(Rectangle((lx, ly - 1.0), 2.4, 2.0, facecolor=fc, edgecolor=style.shade(fc, 0.3),
                               lw=0.4, zorder=3))
        ax.text(lx + 3.0, ly, name, va="center", fontsize=7, color=style.MUTED, zorder=3)
        lx += 3.4 + {"train": 6.6, "val.": 5.2, "test": 5}[name]


def main() -> None:
    fl.set_mode(sys.argv)
    fig, ax = fl.new_figure(W, H)
    py, ph = 8.0, 70.0
    top = py + ph - 6.0                  # first line under the title band

    # 1 Data and time-ordered split ------------------------------------------
    xa, wa = 0.5, 35.0
    fl.panel(ax, xa, py, wa, ph, "Data and split", C["data"], 1)
    rows = [
        ("world-download", "AGMARKNET", "Paddy (Common),\nPunjab, Sep–Dec", "agmarknet"),
        ("wheat", "Basmati paddy", "by variety", "basmati"),
        ("eraser", "Cleaning", "one price per\nmandi-day", "cleaning"),
        ("topology-star-3", "Mandi graph", "k nearest mandis", "graph"),
    ]
    yy = top - 4.8
    for ic, lab, note, key in rows:
        fl.item(ax, ic, xa + 4.4, yy, lab, note, C["data"], STATUS[key], r=2.8, gap=1.4)
        yy -= 8.6 if "\n" in note else 7.2
    cx, cy, cw, ch = xa + 1.6, py + 1.6, wa - 3.2, yy - py - 1.4
    fl.card(ax, cx, cy, cw, ch, C["data"], STATUS["split"])
    fl.draw_icon(ax, "timeline", cx + 2.6, cy + ch - 2.6, 3.4, C["data"])
    card_title(ax, cx + 5.0, cy + ch - 2.6, "Time-ordered split")
    split_grid(ax, cx + 1.2, cy + ch - 7.0, cw - 2.4, read_folds(),
               C["cleaning"], C["outcomes"], C["decision"])

    # 2 Models compared --------------------------------------------------------
    xb, wb = 39.5, 43.0
    fl.panel(ax, xb, py, wb, ph, "Models compared", C["cleaning"], 2)
    # simple rules card
    sx, sw = xb + 1.6, wb - 3.2
    sh = 17.8
    sy = top - 1.4 - sh
    fl.card(ax, sx, sy, sw, sh, C["cleaning"])
    card_title(ax, sx + 1.6, sy + sh - 2.3, "Simple rules")
    for k, (ic, lab, note, key) in enumerate([
        ("history", "Naive", "last price", "naive"),
        ("chart-bar", "Moving avg.", "last 7 dates", "moving_avg"),
        ("coin-rupee", "MSP rule", "announced", "msp_rule"),
    ]):
        column_item(ax, ic, sx + sw * (2 * k + 1) / 6, sy + sh - 7.3, lab, note,
                    C["cleaning"], STATUS[key])
    # learned models card
    lh = 28.4
    ly = sy - 1.6 - lh
    fl.card(ax, sx, ly, sw, lh, C["cleaning"])
    card_title(ax, sx + 1.6, ly + lh - 2.3, "Learned models")
    ax.text(sx + sw - 1.6, ly + lh - 2.3, "neural: 5 seeds", ha="right", va="center", fontsize=7,
            color=style.MUTED)
    learned = [
        ("math-function", "Ridge", "linear", "ridge"),
        ("brain", "GRU", "no graph", "gru"),
        ("topology-star-3", "T-GCN", "graph + GRU", "tgcn"),
        ("target", "A3T-GCN", "+ attention", "a3tgcn"),
    ]
    for k, (ic, lab, note, key) in enumerate(learned):
        col, row = k % 2, k // 2
        column_item(ax, ic, sx + sw * (2 * col + 1) / 4, ly + lh - 7.3 - row * 11.6, lab, note,
                    C["cleaning"], STATUS[key])
    yy = ly - 4.2
    for ic, lab, note, key in [
        ("adjustments", "Tuned on validation", "k, ridge penalty, stopping", "tuning"),
        ("chart-histogram", "Price ranges", "quantile forecasts", "ranges"),
    ]:
        fl.item(ax, ic, xb + 4.4, yy, lab, note, C["cleaning"], STATUS[key], r=2.8, gap=1.4)
        yy -= 7.0

    # 3 Evaluation and selection ----------------------------------------------
    xc, wc = 87.0, 34.5
    fl.panel(ax, xc, py, wc, ph, "Evaluation", C["decision"], 3)
    rows = [
        ("ruler", "Errors", "MAE, RMSE, MAPE\nhorizon 1–7 dates", "errors"),
        ("checks", "Paired check", "date by date\nvs naive", "paired"),
        ("chart-dots", "Significance", "Diebold–Mariano", "dm_test"),
        ("gauge", "Coverage", "of price ranges", "coverage"),
        ("trophy", "Selection", "best on validation,\nper variety, horizon", "selection"),
    ]
    yy = top - 4.8
    for ic, lab, note, key in rows:
        fl.item(ax, ic, xc + 4.4, yy, lab, note, C["decision"], STATUS[key], r=2.8, gap=1.4)
        yy -= 11.0 if "\n" in note else 8.4

    # dashed flow between panels
    mid = py + ph / 2
    fl.arrow(ax, [(xa + wa + 0.4, mid), (xb - 0.4, mid)])
    fl.arrow(ax, [(xb + wb + 0.4, mid), (xc - 0.4, mid)])

    fl.legend_draft(ax, 1.0, 3.6)
    out = Path(__file__).resolve().parents[1]
    for p in fl.save(fig, out, "fig2_methodology"):
        print(p)


if __name__ == "__main__":
    main()
