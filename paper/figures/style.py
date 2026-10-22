"""Shared figure style for the KisanNiti paper: one palette, one font, one icon set.

Every diagram (paper/figures/src/) and every data plot imports this file, so colours
and fonts stay the same across figures. Run it directly to re-check the palette:

    python3 paper/figures/style.py

Palette rules (FIGURE_GUIDE.md section 2): five colours, one per system layer, that stay
distinct in greyscale (lightness steps of about 14 CIELAB L*) and for protan, deutan and
tritan colour vision (minimum pairwise CIELAB distance of about 21 after simulation with
the Machado et al. 2009 matrices, severity 1.0).
"""
from __future__ import annotations

import itertools

import matplotlib as mpl

# One colour per layer of the system, ordered dark to light so greyscale keeps the order.
PALETTE = {
    "data": "#373C7A",       # indigo      L* 28  L1 data sources
    "cleaning": "#167170",   # teal        L* 43  L2 cleaning and checks
    "decision": "#CA7644",   # terracotta  L* 58  L3 forecasting, storage risk, hold-or-sell, allocation
    "review": "#7EC085",     # green       L* 72  L4 manager review
    "outcomes": "#ECD781",   # sand        L* 86  L5 WhatsApp and sale records
}
INK = "#1F2328"              # text and dark icons
MUTED = "#5A6270"            # secondary text (notes)
FUTURE = "#9AA0A6"           # future or not-yet-built parts: dashed and grey
WHITE = "#FFFFFF"

# Springer LNCS text block is 122 mm x 193 mm; draw figures at final size.
TEXT_WIDTH_MM = 122.0
MIN_FONT_PT = 7.0            # smallest text allowed at printed size
FONT_FAMILY = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]


def apply() -> None:
    """Set matplotlib defaults used by every figure script."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": FONT_FAMILY,
        "font.size": 7.5,
        "pdf.fonttype": 42,          # embed TrueType so the PDF text stays editable
        "ps.fonttype": 42,
        "svg.fonttype": "none",      # keep SVG text as text for editing
        "axes.prop_cycle": mpl.cycler(color=list(PALETTE.values())),
        "savefig.dpi": 600,
    })


def _mix(hex_color: str, other: tuple[float, float, float], f: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    m = [(1 - f) * c + f * o for c, o in zip((r, g, b), other)]
    return "#" + "".join(f"{round(v * 255):02X}" for v in m)


def tint(hex_color: str, f: float) -> str:
    """Mix a colour with white (f = 0 keeps it, f = 1 gives white)."""
    return _mix(hex_color, (1.0, 1.0, 1.0), f)


def shade(hex_color: str, f: float) -> str:
    """Mix a colour with black (f = 0 keeps it, f = 1 gives black)."""
    return _mix(hex_color, (0.0, 0.0, 0.0), f)


def lightness(hex_color: str) -> float:
    """CIELAB L* of a colour (0 black, 100 white)."""
    return _lab(hex_color)[0]


def on_color(hex_color: str) -> str:
    """Icon or text colour that reads on top of the given fill."""
    return WHITE if lightness(hex_color) < 62 else INK


# ---------------------------------------------------------------- palette check
_CVD = {  # Machado, Oliveira and Fernandes (2009), severity 1.0, linear RGB
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}


def _lab(hex_color: str, cvd: str | None = None) -> tuple[float, float, float]:
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    if cvd:
        lin = [min(1.0, max(0.0, sum(m * v for m, v in zip(row, lin)))) for row in _CVD[cvd]]
    xyz = [sum(m * v for m, v in zip(row, lin)) for row in
           ((0.4124, 0.3576, 0.1805), (0.2126, 0.7152, 0.0722), (0.0193, 0.1192, 0.9505))]
    t = [v / w for v, w in zip(xyz, (0.95047, 1.0, 1.08883))]
    f = [v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116 for v in t]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def palette_report() -> dict[str, float]:
    """Smallest pairwise colour distance (CIELAB) in normal and simulated colour vision,
    plus the smallest greyscale (L*) step."""
    out = {}
    for mode in (None, "protan", "deutan", "tritan"):
        labs = [_lab(c, mode) for c in PALETTE.values()]
        out[mode or "normal"] = min(sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5
                                    for a, b in itertools.combinations(labs, 2))
    ls = sorted(lightness(c) for c in PALETTE.values())
    out["greyscale_min_step"] = min(b - a for a, b in zip(ls, ls[1:]))
    return out


if __name__ == "__main__":
    for name, c in PALETTE.items():
        print(f"{name:9s} {c}  L*={lightness(c):5.1f}")
    for k, v in palette_report().items():
        print(f"{k:20s} {v:5.1f}")
