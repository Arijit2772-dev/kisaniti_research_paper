"""Fig. 3: storage-node hardware and data path, as four illustrated panels.

    python3 paper/figures/src/fig3_hardware.py           # draft (planned parts marked)
    python3 paper/figures/src/fig3_hardware.py --final   # final: unbuilt parts dashed grey

Writes paper/figures/fig3_hardware[_draft].{pdf,svg,png}.

STATUS is the single place that says what exists (22 Oct 2026): firmware, Wokwi twin with the emulated SHT3x chip,
TLS broker, ingestion and STORAGE-DEMO-0.1 are built and tested; the physical node is not assembled yet (kit not
bought), and the dashboard, WhatsApp delivery and the storage input to the planner are not built.
Update 28 Oct 2026: the planner uses the storage risk (a High-risk lot gets priority; plan "Why this plan" in the product
chain run) and the manager app's Storage sensors page shows readings and placement, so both are now built. The
physical node and storage advice on WhatsApp are still not built.
"""
from __future__ import annotations

import sys
from pathlib import Path

import figlib as fl
from figlib import style
from matplotlib.patches import FancyBboxPatch

C = style.PALETTE
STATUS = {
    "probe": "planned", "esp32": "planned", "twin": "built",
    "hotspot": "planned", "broker": "built", "ack": "built",
    "validate": "built", "store": "built", "rule": "built",
    "planner": "built", "dashboard": "built", "whatsapp": "planned",
}
W, H = 122.0, 66.0
TOP, PH = 9.0, 55.0  # panel bottom and height (final mode has no draft key, so it drops the bottom band)


def sack(ax, x, y, w, h, status):
    """A grain bag with the probe pushed to mid-depth (simple vector drawing)."""
    st = fl.shown_status(status)
    edge = style.FUTURE if st == "future" else style.shade(C["outcomes"], 0.45)
    fill = style.WHITE if st == "future" else style.tint(C["outcomes"], 0.35)
    ls = (0, (2.2, 1.4)) if st == "future" else "solid"
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=3.0", facecolor=fill,
                                edgecolor=edge, lw=0.8, ls=ls, zorder=2))
    ax.plot([x + 1.2, x + w / 2, x + w - 1.2], [y + h - 0.2, y + h + 1.6, y + h - 0.2], color=edge, lw=0.8,
            zorder=2)  # tied top
    for k in range(3):  # grain dots
        for j in range(4):
            ax.plot(x + 2.2 + j * (w - 4.4) / 3, y + 2.0 + k * 2.2, marker="o", ms=1.2, color=edge, zorder=2.5,
                    alpha=0.6)
    tip = (x + w / 2, y + h * 0.45)
    ax.plot([tip[0], tip[0]], [tip[1], y + h + 4.5], color=style.INK, lw=1.2, zorder=3)  # probe shaft
    ax.plot(*tip, marker="o", ms=3.2, color=C["data"], zorder=4)
    ax.text(x + w / 2, y - 1.0, "basmati bag", ha="center", va="top", fontsize=7, color=style.MUTED)
    return tip


def main() -> None:
    global TOP
    fl.set_mode(sys.argv)
    if fl.MODE == "final":
        TOP = 1.0
    fig, ax = fl.new_figure(W, TOP + PH + 2.0)

    # 1 Storage node ----------------------------------------------------------
    x1, w1 = 0.5, 40.0
    fl.panel(ax, x1, TOP, w1, PH, "Storage node", C["data"], 1)
    sack(ax, x1 + 2.2, TOP + 15.0, 11.0, 13.0, STATUS["probe"])
    ax.plot([x1 + 7.7, x1 + 7.7, x1 + 16.6], [TOP + 32.5, TOP + 36.6, TOP + 36.6], color=style.INK, lw=0.7, zorder=3)
    fl.item(ax, "temperature", x1 + 19.2, TOP + PH - 11.0, "SHT30 probe", "in the grain", C["data"],
            STATUS["probe"], r=2.8, gap=1.2)
    fl.item(ax, "cpu", x1 + 19.2, TOP + 36.6, "ESP32", "every 5 min,\n24 h buffer", C["data"], STATUS["esp32"],
            r=2.8, gap=1.2)
    ax.text(x1 + 16.8, TOP + 29.0, "I²C: GPIO 21/22,\n4.7 kΩ pull-ups", fontsize=6.3, color=style.MUTED, va="top",
            linespacing=1.05)
    fl.card(ax, x1 + 2.0, TOP + 2.0, w1 - 4.0, 10.0, C["data"], STATUS["twin"])
    fl.item(ax, "copy", x1 + 6.0, TOP + 7.0, "Wokwi twin", "same firmware,\nemulated SHT3x", C["data"],
            STATUS["twin"], r=2.6, gap=1.2)

    # 2 Network ---------------------------------------------------------------
    x2, w2 = 42.5, 22.0
    fl.panel(ax, x2, TOP, w2, PH, "Network", C["cleaning"], 2)
    fl.item(ax, "router", x2 + 4.2, TOP + PH - 12.0, "Hotspot", "2.4 GHz", C["cleaning"], STATUS["hotspot"],
            r=2.8, gap=1.2)
    fl.item(ax, "lock", x2 + 4.2, TOP + PH - 26.0, "MQTT, TLS", "per-device\nuser + ACL", C["cleaning"],
            STATUS["broker"], r=2.8, gap=1.2)
    fl.item(ax, "refresh", x2 + 4.2, TOP + 10.0, "Ack", "after the\nreading is\nstored", C["cleaning"],
            STATUS["ack"], r=2.8, gap=1.2)

    # 3 Ingestion and storage rule ---------------------------------------------
    x3, w3 = 66.5, 30.0
    fl.panel(ax, x3, TOP, w3, PH, "Ingestion, rule", C["decision"], 3)
    rows = [
        ("filter", "Validate", "schema, device,\nclock", "validate"),
        ("database", "Store once", "de-duplicate by\nboot ID + seq.", "store"),
        ("alert-triangle", "Storage rule", "24 h median,\na$_w$ 0.65 / 0.70", "rule"),
    ]
    for k, (ic, lab, note, key) in enumerate(rows):
        fl.item(ax, ic, x3 + 4.4, TOP + PH - 12.0 - k * 14.0, lab, note, C["decision"], STATUS[key], r=2.8,
                gap=1.2)
    for k in range(2):
        y0 = TOP + PH - 12.0 - k * 14.0
        fl.arrow(ax, [(x3 + 4.4, y0 - 3.2), (x3 + 4.4, y0 - 14.0 + 3.3)], style.INK, dashed=False, lw=0.6,
                 head=1.2)
    ax.text(x3 + 1.8, TOP + 3.4, "LOW / MEDIUM / HIGH /\nUNKNOWN with\nreasons", fontsize=6.3,
            color=style.MUTED, va="bottom", linespacing=1.05)

    # 4 Use -------------------------------------------------------------------
    x4, w4 = 98.5, 23.0
    fl.panel(ax, x4, TOP, w4, PH, "Use", C["review"], 4)
    fl.item(ax, "truck", x4 + 4.2, TOP + PH - 12.0, "Planner", "urgency of\nat-risk lots", C["review"],
            STATUS["planner"], r=2.8, gap=1.2)
    fl.item(ax, "device-desktop", x4 + 4.2, TOP + PH - 26.0, "Dashboard", "readings,\ndevice\nhealth", C["review"],
            STATUS["dashboard"], r=2.8, gap=1.2)
    fl.item(ax, "message-circle", x4 + 4.2, TOP + 12.0, "WhatsApp", "advice to\nfarmers", C["review"],
            STATUS["whatsapp"], r=2.8, gap=1.2)

    # data flow between panels ---------------------------------------------------
    ytx = TOP + 36.6
    fl.arrow(ax, [(x1 + w1 + 0.3, ytx), (x2 - 0.3, ytx)], status=STATUS["esp32"])
    fl.arrow(ax, [(x2 + w2 + 0.3, ytx), (x3 - 0.3, ytx)])
    fl.arrow(ax, [(x3 - 0.3, TOP + 13.0), (x2 + w2 + 0.3, TOP + 13.0)], status=STATUS["ack"])
    fl.arrow(ax, [(x3 + w3 + 0.3, ytx), (x4 - 0.3, ytx)], status=STATUS["planner"])

    fl.legend_draft(ax, 1.0, 4.0)
    out = Path(__file__).resolve().parents[1]
    for p in fl.save(fig, out, "fig3_hardware"):
        print(p)


if __name__ == "__main__":
    main()
