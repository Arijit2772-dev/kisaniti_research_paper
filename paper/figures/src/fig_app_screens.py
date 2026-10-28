"""Fig. 5: three screens of the manager app in phone frames (screenshots in ../screens/, see its README).

    python3 paper/figures/src/fig_app_screens.py

Writes paper/figures/fig_app_screens.{pdf,svg,png}. The screenshots are only cropped, never edited.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg
from matplotlib.patches import FancyBboxPatch, Rectangle

import figlib as fl
from figlib import style

HERE = Path(__file__).resolve().parent
SCREENS = HERE.parent / "screens"
# (file, crop top px, crop bottom px, panel title)
SHOTS = [
    ("app_plan_review.jpg", 140, 1470, "(a) Review and approval"),
    ("app_message_punjabi.jpg", 425, 1395, "(b) Farmer message (Punjabi)"),
    ("app_planned_vs_actual.jpg", 0, 845, "(c) Planned against actual"),
]
W, H = 122.0, 78.0
PW, GAP = 36.0, 7.0        # phone width and gap, mm
SW = PW - 3.0              # screen width inside the frame


def main() -> None:
    fig, ax = fl.new_figure(W, H)
    x = (W - 3 * PW - 2 * GAP) / 2
    top = H - 6.5
    imgs = [mpimg.imread(SCREENS / name)[y0:y1] for name, y0, y1, _ in SHOTS]
    full = max(SW * im.shape[0] / im.shape[1] for im in imgs)   # every phone shows a screen this tall
    ph = full + 9.0
    py = top - ph
    for img, (_, _, _, title) in zip(imgs, SHOTS):
        sh = SW * img.shape[0] / img.shape[1]
        ax.add_patch(FancyBboxPatch((x, py), PW, ph, boxstyle="round,pad=0,rounding_size=4.0",
                                    facecolor=style.INK, edgecolor=style.INK, lw=0.6, zorder=1))
        sx, sy = x + 1.5, py + 4.5
        ax.add_patch(Rectangle((sx, sy), SW, full, facecolor=style.WHITE, edgecolor="none", zorder=1.5))
        ax.imshow(img, extent=(sx, sx + SW, sy + full - sh, sy + full), zorder=2, interpolation="lanczos")
        ax.add_patch(FancyBboxPatch((x + PW / 2 - 4.0, py + ph - 2.6), 8.0, 1.0,
                                    boxstyle="round,pad=0,rounding_size=0.5", facecolor="#3A3F47",
                                    edgecolor="none", zorder=3))          # speaker slot
        ax.text(x + PW / 2, top + 1.6, title, ha="center", va="bottom", fontsize=7.5, fontweight="bold",
                color=style.INK)
        x += PW + GAP
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    out = HERE.parent
    fl.MODE = "final"
    for p in fl.save(fig, out, "fig_app_screens"):
        print(p)


if __name__ == "__main__":
    main()
