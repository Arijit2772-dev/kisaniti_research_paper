"""Fig. 4: the allocation comparison under the nine transport-rate and mandi-limit settings.

    python3 paper/figures/src/fig_allocation_sensitivity.py

Reads results/L3d_allocation/allocation_sensitivity.csv only (written by
layers/L3d_allocation_fairness/run_sensitivity.py) and writes paper/figures/fig_allocation_sensitivity.{pdf,svg,png}.
(a) the smallest share of a lot sold, by mandi-day limit; it does not depend on the transport rate in these runs.
(b) the price of fairness (net return given up against the utilitarian plan) of the exact KisanNiti plan and the
greedy heuristic, by transport rate, one colour per limit.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

import figlib as fl
from figlib import style

C = style.PALETTE
ROOT = Path(__file__).resolve().parents[3]
CSV = ROOT / "results" / "L3d_allocation" / "allocation_sensitivity.csv"


def main() -> None:
    rows = list(csv.DictReader(CSV.open()))
    rates = sorted({float(r["rate_rs_per_q_km"]) for r in rows})
    caps = sorted({int(r["cap_q_per_mandi_day"]) for r in rows})
    get = {(float(r["rate_rs_per_q_km"]), int(r["cap_q_per_mandi_day"]), r["policy_key"]): r for r in rows}

    style.apply()
    fig, (a, b) = plt.subplots(1, 2, figsize=(122 * fl.MM, 48 * fl.MM), gridspec_kw={"width_ratios": [1, 1.25]})

    # (a) smallest share sold, by limit (identical for every rate, checked here)
    policies = [("p1_nearest", "Nearest mandi", C["data"]), ("greedy", "Greedy", C["outcomes"]),
                ("kisaniti", "KisanNiti", C["decision"])]
    width = 0.26
    for k, (key, lab, col) in enumerate(policies):
        vals = []
        for cap in caps:
            per_rate = {float(get[(rate, cap, key)]["min_fulfilment_pct"]) for rate in rates}
            assert len(per_rate) == 1, (key, cap, per_rate)
            vals.append(per_rate.pop())
        xs = [i + (k - 1) * width for i in range(len(caps))]
        a.bar(xs, vals, width, color=col, edgecolor=style.shade(col, 0.35), lw=0.4, label=lab)
        for x, v in zip(xs, vals):
            a.text(x, v + 1.5, f"{v:.0f}", ha="center", va="bottom", fontsize=6.3, color=style.INK)
    a.set_xticks(range(len(caps)), [str(c) for c in caps])
    a.set_xlabel("Mandi-day limit (quintals)")
    a.set_ylabel("Smallest share sold (%)")
    a.set_ylim(0, 112)
    a.set_title("(a) Least-served farmer", fontsize=7.5, fontweight="bold", loc="left")
    a.legend(frameon=False, fontsize=6.5, loc="upper left", handlelength=1.2)

    # (b) price of fairness, by transport rate
    cap_col = dict(zip(caps, [C["data"], C["cleaning"], C["decision"]]))
    for cap in caps:
        for key, ls, mk in [("kisaniti", "solid", "o"), ("greedy", (0, (3, 1.6)), "s")]:
            ys = [float(get[(rate, cap, key)]["price_of_fairness_rs_per_q"]) for rate in rates]
            b.plot(rates, ys, color=cap_col[cap], ls=ls, marker=mk, ms=3, lw=1.0)
    b.set_xticks(rates, [f"{r:g}" for r in rates])
    b.set_xlabel("Transport rate (Rs per quintal-km)")
    b.set_ylabel("Price of fairness (Rs per quintal)")
    b.set_title("(b) Net return given up", fontsize=7.5, fontweight="bold", loc="left")
    handles = [plt.Line2D([], [], color=cap_col[c], lw=1.2, label=f"limit {c}") for c in caps]
    handles += [plt.Line2D([], [], color=style.INK, lw=1.0, marker="o", ms=3, label="KisanNiti"),
                plt.Line2D([], [], color=style.INK, lw=1.0, ls=(0, (3, 1.6)), marker="s", ms=3, label="Greedy")]
    b.legend(handles=handles, frameon=False, fontsize=6.5, loc="upper left", ncol=2, handlelength=2.0)

    for ax in (a, b):
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=6.8)
        ax.xaxis.label.set_size(7)
        ax.yaxis.label.set_size(7)
    fig.tight_layout(pad=0.4, w_pad=1.6)
    out = Path(__file__).resolve().parents[1]
    fl.MODE = "final"
    for p in fl.save(fig, out, "fig_allocation_sensitivity"):
        print(p)


if __name__ == "__main__":
    main()
