"""Paper figures for KisanNiti v1 (architecture, mandi network, allocation sensitivity)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
                     "font.size": 9, "savefig.dpi": 400})


def box(ax, x, y, w, h, text, fc="#ffffff", bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02", fc=fc, ec="black", lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5, weight="bold" if bold else "normal")


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", lw=0.8, color="black"))


def fig_architecture():
    fig, ax = plt.subplots(figsize=(6.3, 2.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    rows = [(3.0, "AGMARKNET mandi\nprice history", "Mandi graph +\nA3T-GCN forecast"),
            (1.65, "FPO lot records\n(quantity, location)", "Transport cost and\nfeasible mandi-days"),
            (0.3, "Storage node\n(ESP32 + sensors)", "Storage condition\n(after calibration)")]
    for y, a, b in rows:
        box(ax, 0.1, y, 2.1, 0.75, a, fc="#eef3f8")
        box(ax, 3.0, y, 2.1, 0.75, b, fc="#f3f3f3")
        arrow(ax, 2.2, y + 0.375, 3.0, y + 0.375)
        arrow(ax, 5.1, y + 0.375, 5.9, 2.025 if y != 1.65 else y + 0.375)
    box(ax, 5.9, 1.2, 1.9, 1.65, "Cooperative\nallocation model\n(integer program,\nshared mandi-day\nlimits)", fc="#fff6e5", bold=False)
    box(ax, 8.4, 1.4, 1.5, 1.25, "Selling plan:\nlot → mandi\n→ day → quantity", fc="#eaf5ea")
    arrow(ax, 7.8, 2.025, 8.4, 2.025)
    ax.text(5.0, 3.9, "Inputs  →  analysis  →  decision  →  output", ha="center", fontsize=8, style="italic")
    fig.tight_layout(pad=0.2)
    fig.savefig(FIG / "fig1_architecture.png")


OFFSETS = {"Jal. Cantt": (0.04, -0.07, "left"), "Jalandhar": (-0.03, 0.03, "right"), "Rayya": (-0.03, 0.03, "right"),
           "Dhilwan": (0.03, 0.03, "left"), "Bhawanigarh": (-0.04, -0.04, "right"), "Patiala": (0.0, -0.08, "center"),
           "Amargarh": (-0.03, 0.03, "right"), "Chanarthal": (-0.02, 0.04, "right")}


def fig_network():
    c = pd.read_csv(HERE / "mandi_coordinates.csv")
    lat, lon = c.lat.values, c.lon.values
    R = 6371.0
    la, lo = np.radians(lat), np.radians(lon)
    a = np.sin((la[:, None] - la[None]) / 2) ** 2 + np.cos(la[:, None]) * np.cos(la[None]) * np.sin((lo[:, None] - lo[None]) / 2) ** 2
    dist = 2 * R * np.arcsin(np.sqrt(a))
    k = 5
    fig = plt.figure(figsize=(6.3, 2.9))
    ax = fig.add_axes([0.085, 0.13, 0.40, 0.78])
    for i in range(len(c)):
        for j in np.argsort(dist[i])[1 : k + 1]:
            ax.plot([lon[i], lon[j]], [lat[i], lat[j]], color="#9aa7b4", lw=0.6, zorder=1)
    cand = ["Patiala(New Anaj Mandi) APMC", "Patran APMC", "Bhawanigarh APMC", "Chanarthal APMC", "Amargarh APMC"]
    col = ["#d1495b" if m in cand else "#2e5c8a" for m in c.market_name]
    ax.scatter(lon, lat, s=16, c=col, zorder=2)
    for x, y, m in zip(lon, lat, c.market_name):
        short = m.replace(" APMC", "").replace("(New Anaj Mandi)", "").replace("Jalandhar City(Kartar Pur Dana mandi)", "Kartarpur").replace("Jalandhar Cantt.", "Jal. Cantt").replace("Jalandhar City", "Jalandhar")
        dx, dy, ha = OFFSETS.get(short, (0.03, 0.02, "left"))
        ax.text(x + dx, y + dy, short, fontsize=5.6, zorder=3, ha=ha)
    ax.set_xlim(74.05, 76.55)
    ax.set_aspect(1 / np.cos(np.radians(30.8)))
    ax.set_xlabel("Longitude (°E)", fontsize=7); ax.set_ylabel("Latitude (°N)", fontsize=7)
    ax.tick_params(labelsize=6)
    ax.set_title("(a) 20 Punjab mandis, 5-nearest-neighbour graph", fontsize=7.5)
    ax2 = fig.add_axes([0.53, 0.04, 0.46, 0.88]); ax2.axis("off"); ax2.set_xlim(0, 4); ax2.set_ylim(0, 6)
    steps = ["Last 7 prices of every mandi\n(relative to latest price)", "Graph convolution\n(mix with neighbour mandis)",
             "GRU cell\n(learn change over time)", "Attention over the 7 steps\n(weight useful past dates)",
             "Price for next 1–7 trading dates\nfor each mandi"]
    for i, s in enumerate(steps):
        y = 5.0 - i * 1.18
        box(ax2, 0.3, y, 3.4, 0.8, s, fc="#f3f3f3" if 0 < i < 4 else "#eef3f8")
        if i < 4:
            arrow(ax2, 2.0, y, 2.0, y - 0.38)
    ax2.text(2.0, 6.05, "(b) A3T-GCN forecasting flow", ha="center", fontsize=7.5)
    fig.savefig(FIG / "fig2_mandi_network.png")


def fig_sensitivity():
    s = pd.read_csv(HERE / "results" / "allocation_sensitivity.csv")
    fig, ax = plt.subplots(figsize=(4.2, 2.3))
    for rate, mk in zip([1.0, 2.0, 4.0], ["o", "s", "^"]):
        d = s[s.rate_rs_per_q_km == rate]
        ax.plot(d.cap_q_per_mandi_day, d.gain_rs_per_q, marker=mk, lw=1, ms=4, color="black",
                ls={1.0: ":", 2.0: "--", 4.0: "-"}[rate], label=f"Rs. {rate:g} per quintal-km")
    ax.set_xlabel("Daily limit per mandi for the FPO (quintals)")
    ax.set_ylabel("Gain over P1 (Rs. per quintal)")
    ax.set_xticks([200, 300, 500]); ax.grid(alpha=0.3, lw=0.5)
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout(pad=0.3)
    fig.savefig(FIG / "fig4_allocation_sensitivity.png")


if __name__ == "__main__":
    fig_architecture(); fig_network(); fig_sensitivity()
    print(sorted(p.name for p in FIG.iterdir()))
