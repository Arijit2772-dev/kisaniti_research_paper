"""Fig. 1: KisanNiti system architecture as five illustrated layer panels.

    python3 paper/figures/src/fig1_architecture.py           # draft (planned parts marked)
    python3 paper/figures/src/fig1_architecture.py --final   # final: unbuilt parts dashed grey

Writes paper/figures/fig1_architecture[_draft].{pdf,svg,png}.

STATUS below is the single place that says what exists. Update it as layers are built
(see STATUS.md and the master plan); the final export greys out everything not "built".
Status as of 22 Oct 2026: built = v2 research runs (paddy prices, cleaning, forecasting
comparison, cooperative allocation MILP on a synthetic FPO).
"""
from __future__ import annotations

import sys
from pathlib import Path

import figlib as fl
from figlib import style

C = style.PALETTE
STATUS = {
    "agmarknet": "built", "fpo_records": "built", "mandi_locations": "built",
    "grain_sensor": "planned", "co2_sensor": "future",
    "dedup": "built", "daily_panel": "built", "quality_rules": "planned", "readiness": "planned",
    "forecast": "built", "storage_risk": "planned", "hold_sell": "planned", "allocation": "built",
    "review": "planned", "edit": "planned", "approve": "planned",
    "whatsapp": "planned", "sale_entry": "planned", "stock_update": "planned",
    "feedback": "planned",
}
W, H = 122.0, 94.0


def column_item(ax, icon, cx, cy, label, note, color, status, r=3.0):
    """Badge with the label and note centred below it."""
    fl.badge(ax, icon, cx, cy, r, color, status)
    st = fl.shown_status(status)
    lc = style.FUTURE if st == "future" else style.INK
    nc = style.FUTURE if st == "future" else style.MUTED
    ax.text(cx, cy - r - 0.9, label, ha="center", va="top", fontsize=7, fontweight="bold",
            color=lc, linespacing=1.0, zorder=6)
    if note:
        n_lines = label.count("\n") + 1
        ax.text(cx, cy - r - 0.9 - 2.75 * n_lines, note, ha="center", va="top", fontsize=7,
                color=nc, linespacing=1.0, zorder=6)


def main() -> None:
    fl.set_mode(sys.argv)
    fig, ax = fl.new_figure(W, H)
    top_y, top_h = 48.0, 45.5
    bot_y, bot_h = 9.0, 30.0

    # 1 Data sources --------------------------------------------------------
    x1, w1 = 0.5, 36.0
    fl.panel(ax, x1, top_y, w1, top_h, "Data sources", C["data"], 1)
    rows = [
        ("world-download", "AGMARKNET", "mandi prices", "agmarknet"),
        ("users", "FPO lots", "synthetic in tests", "fpo_records"),
        ("map-pin", "Mandi locations", "road distances", "mandi_locations"),
        ("temperature", "Grain sensor", "ESP32 + SHT30", "grain_sensor"),
        ("gauge", "CO$_2$ sensor", "spoilage sign", "co2_sensor"),
    ]
    for k, (ic, lab, note, key) in enumerate(rows):
        fl.item(ax, ic, x1 + 4.6, top_y + top_h - 10.3 - k * 7.6, lab, note, C["data"],
                STATUS[key], r=2.9)

    # 2 Cleaning and checks -------------------------------------------------
    x2, w2 = 42.5, 28.0
    fl.panel(ax, x2, top_y, w2, top_h, "Cleaning", C["cleaning"], 2)
    rows = [
        ("eraser", "De-duplicate", "repair zero\nprices", "dedup"),
        ("calendar-time", "Daily panel", "price per\nmandi-day", "daily_panel"),
        ("filter", "Quality rules", "units, outliers", "quality_rules"),
        ("list-check", "Readiness", "report per crop", "readiness"),
    ]
    for k, (ic, lab, note, key) in enumerate(rows):
        fl.item(ax, ic, x2 + 4.6, top_y + top_h - 10.6 - k * 9.4, lab, note, C["cleaning"],
                STATUS[key], r=2.9, gap=1.4)

    # 3 Decision models (2 x 2 cards) ----------------------------------------
    x3, w3 = 76.5, 45.0
    fl.panel(ax, x3, top_y, w3, top_h, "Decision models", C["decision"], 3)
    cw, ch, gx, gy = 19.4, 17.0, 3.4, 3.8
    cx0 = x3 + (w3 - 2 * cw - gx) / 2
    cy_top = top_y + top_h - 6.0 - 1.6 - ch
    cy_bot = cy_top - gy - ch
    cards = {
        "forecast": (cx0, cy_top, "chart-line", "Price forecast", "baselines vs GNN"),
        "storage_risk": (cx0 + cw + gx, cy_top, "alert-triangle", "Storage risk", "grain T and RH"),
        "hold_sell": (cx0, cy_bot, "scale", "Hold or sell", "per stored lot"),
        "allocation": (cx0 + cw + gx, cy_bot, "truck", "Lot allocation", "MILP, shared\nmandi limits"),
    }
    for key, (x, y, ic, lab, note) in cards.items():
        fl.card(ax, x, y, cw, ch, C["decision"], STATUS[key])
        column_item(ax, ic, x + cw / 2, y + ch - 4.2, lab, note, C["decision"], STATUS[key], r=2.9)
    # solid arrows inside the step
    fx, fy = cards["forecast"][0], cards["forecast"][1]
    sx, sy = cards["storage_risk"][0], cards["storage_risk"][1]
    hx, hy = cards["hold_sell"][0], cards["hold_sell"][1]
    ax_, ay_ = cards["allocation"][0], cards["allocation"][1]
    fl.arrow(ax, [(fx + cw / 2, fy - 0.2), (hx + cw / 2, hy + ch + 0.3)], style.INK,
             dashed=False, lw=0.7, head=1.4, status=STATUS["hold_sell"])
    fl.arrow(ax, [(sx + 2.0, sy - 0.2), (hx + cw - 2.0, hy + ch + 0.3)], style.INK,
             dashed=False, lw=0.7, head=1.4, status=STATUS["hold_sell"])
    fl.arrow(ax, [(hx + cw + 0.2, hy + ch / 2), (ax_ - 0.3, ay_ + ch / 2)], style.INK,
             dashed=False, lw=0.7, head=1.4, status=STATUS["hold_sell"])

    # 4 Manager review (vertical, top to bottom) ------------------------------
    x4, w4 = 79.5, 42.0
    fl.panel(ax, x4, bot_y, w4, bot_h, "Manager review", C["review"], 4)
    rows = [
        ("clipboard-check", "Review plan", "lots, mandis, days", "review"),
        ("adjustments", "Edit", "quantities, dates", "edit"),
        ("user-check", "Approve, release", "reserves mandi slots", "approve"),
    ]
    ys = [bot_y + bot_h - 11.0 - k * 7.6 for k in range(3)]
    for (ic, lab, note, key), y in zip(rows, ys):
        fl.item(ax, ic, x4 + 5.0, y, lab, note, C["review"], STATUS[key], r=2.9)

    # 5 Farmers and sale records (right to left) ------------------------------
    x5, w5 = 0.5, 73.0
    fl.panel(ax, x5, bot_y, w5, bot_h, "Farmers and sale records", C["outcomes"], 5)
    cols = [
        ("message-circle", "WhatsApp advice", "Punjabi, Hindi,\nEnglish", "whatsapp"),
        ("receipt", "Sale entry", "J-form price\nand quantity", "sale_entry"),
        ("packages", "Stock update", "sold and\nheld lots", "stock_update"),
    ]
    xs = [x5 + w5 * f for f in (5 / 6, 3 / 6, 1 / 6)]
    by = bot_y + bot_h - 6.0 - 6.2
    for (ic, lab, note, key), x in zip(cols, xs):
        column_item(ax, ic, x, by, lab, note, C["outcomes"], STATUS[key], r=3.2)
    for a, b, key in [(0, 1, "sale_entry"), (1, 2, "stock_update")]:
        fl.arrow(ax, [(xs[a] - 4.4, by), (xs[b] + 4.4, by)], style.INK, dashed=False, lw=0.7,
                 head=1.3, status=STATUS[key])

    # dashed data-flow arrows between layers ----------------------------------
    mid = top_y + top_h / 2 - 3
    fl.arrow(ax, [(x1 + w1 + 0.4, mid), (x2 - 0.4, mid)])
    fl.arrow(ax, [(x2 + w2 + 0.4, mid), (x3 - 0.4, mid)])
    fl.arrow(ax, [(x4 + w4 / 2 + 6, top_y - 0.4), (x4 + w4 / 2 + 6, bot_y + bot_h + 0.4)],
             status=STATUS["review"])
    ax.text(x4 + w4 / 2 + 7.5, (top_y + bot_y + bot_h) / 2, "selling plan", va="center",
            fontsize=7, color=style.MUTED)
    fl.arrow(ax, [(x4 - 0.4, ys[2]), (x5 + w5 + 0.4, ys[2])], status=STATUS["whatsapp"])
    # feedback loop: sale records back to the data layer
    fb = fl.shown_status(STATUS["feedback"])
    fx0 = x1 + 9.0
    fl.arrow(ax, [(fx0, bot_y + bot_h + 0.4), (fx0, top_y - 0.4)], status=STATUS["feedback"])
    fl.badge(ax, "refresh", fx0 + 4.4, (top_y + bot_y + bot_h) / 2, 2.2, C["outcomes"], STATUS["feedback"])
    ax.text(fx0 + 7.6, (top_y + bot_y + bot_h) / 2, "sale prices and stock feed the next plan",
            va="center", fontsize=7, color=style.FUTURE if fb == "future" else style.MUTED)

    fl.legend_draft(ax, 1.0, 3.6)
    out = Path(__file__).resolve().parents[1]
    for p in fl.save(fig, out, "fig1_architecture"):
        print(p)


if __name__ == "__main__":
    main()
