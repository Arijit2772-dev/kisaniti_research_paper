"""Drawing helpers for the illustrated diagrams (Fig. 1, Fig. 2, ...).

Diagrams are drawn with matplotlib in millimetre coordinates at final printed size, so
font sizes in points are the real printed sizes. Icons are Tabler Icons (MIT, see
icons/tabler/LICENSE): the SVG path data is parsed here and drawn as vector strokes, so
the PDF and SVG exports stay fully vector.

Each drawn element has a build status:
    "built"   exists and has been run (solid, in colour);
    "planned" in the master plan for Paper 1 but not built yet;
    "future"  beyond Paper 1 (always dashed and grey).
In draft mode, planned parts are drawn in colour with a dashed ring so reviewers can judge
the final look. In final mode, planned parts are drawn like future parts, so the paper
never shows an unbuilt component as built.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch, Polygon, Rectangle
from matplotlib.path import Path as MPath

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import style  # noqa: E402

ICON_DIR = HERE / "icons" / "tabler"
MM = 1 / 25.4
PT_PER_MM = 72 / 25.4

MODE = "draft"          # set by each script from the command line: "draft" or "final"


def set_mode(argv: list[str]) -> None:
    global MODE
    MODE = "final" if "--final" in argv else "draft"


def shown_status(status: str) -> str:
    """Status as drawn: in final mode anything not built is drawn as future."""
    if MODE == "final" and status != "built":
        return "future"
    return status


# ---------------------------------------------------------------- SVG path parsing
_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


def _arc_to_cubics(x1, y1, rx, ry, phi, large, sweep, x2, y2):
    """SVG elliptical arc to cubic Bezier segments (SVG 1.1 implementation notes F.6)."""
    if rx == 0 or ry == 0:
        return [((x1, y1), (x2, y2), (x2, y2))]
    rx, ry = abs(rx), abs(ry)
    cp, sp = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    coef = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        coef = -coef
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    n = max(1, math.ceil(abs(dt) / (math.pi / 2)))
    step = dt / n
    k = 4 / 3 * math.tan(step / 4)
    out = []

    def pt(t):
        x, y = rx * math.cos(t), ry * math.sin(t)
        return cp * x - sp * y + cx, sp * x + cp * y + cy

    def der(t):
        x, y = -rx * math.sin(t), ry * math.cos(t)
        return cp * x - sp * y, sp * x + cp * y

    t = t1
    for _ in range(n):
        p0, p3 = pt(t), pt(t + step)
        d0, d3 = der(t), der(t + step)
        out.append(((p0[0] + k * d0[0], p0[1] + k * d0[1]),
                    (p3[0] - k * d3[0], p3[1] - k * d3[1]), p3))
        t += step
    return out


def parse_path(d: str) -> MPath:
    toks = _TOKEN.findall(d)
    verts, codes = [], []
    i, cmd = 0, None
    x = y = sx = sy = 0.0
    last_c = None      # last cubic control point (for S)
    last_q = None      # last quadratic control point (for T)

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]; i += 1
        rel = cmd.islower()
        c = cmd.upper()
        ox, oy = (x, y) if rel else (0.0, 0.0)
        if c == "Z":
            codes.append(MPath.CLOSEPOLY); verts.append((sx, sy))
            x, y = sx, sy
            last_c = last_q = None
            continue
        if c == "M":
            x, y = num() + ox, num() + oy
            sx, sy = x, y
            verts.append((x, y)); codes.append(MPath.MOVETO)
            cmd = "l" if rel else "L"
            last_c = last_q = None
        elif c == "L":
            x, y = num() + ox, num() + oy
            verts.append((x, y)); codes.append(MPath.LINETO)
            last_c = last_q = None
        elif c == "H":
            x = num() + ox
            verts.append((x, y)); codes.append(MPath.LINETO)
            last_c = last_q = None
        elif c == "V":
            y = num() + oy
            verts.append((x, y)); codes.append(MPath.LINETO)
            last_c = last_q = None
        elif c in "CS":
            if c == "C":
                c1 = (num() + ox, num() + oy)
            else:
                c1 = (2 * x - last_c[0], 2 * y - last_c[1]) if last_c else (x, y)
            c2 = (num() + ox, num() + oy)
            x, y = num() + ox, num() + oy
            verts += [c1, c2, (x, y)]; codes += [MPath.CURVE4] * 3
            last_c, last_q = c2, None
        elif c in "QT":
            if c == "Q":
                q = (num() + ox, num() + oy)
            else:
                q = (2 * x - last_q[0], 2 * y - last_q[1]) if last_q else (x, y)
            x, y = num() + ox, num() + oy
            verts += [q, (x, y)]; codes += [MPath.CURVE3] * 2
            last_q, last_c = q, None
        elif c == "A":
            rx, ry, phi = num(), num(), num()
            large, sweep = int(num()), int(num())
            nx, ny = num() + ox, num() + oy
            for c1, c2, p in _arc_to_cubics(x, y, rx, ry, phi, large, sweep, nx, ny):
                verts += [c1, c2, p]; codes += [MPath.CURVE4] * 3
            x, y = nx, ny
            last_c = last_q = None
    return MPath(verts, codes)


_ICON_CACHE: dict[str, list[MPath]] = {}


def icon_paths(name: str) -> list[MPath]:
    if name not in _ICON_CACHE:
        svg = (ICON_DIR / f"{name}.svg").read_text()
        paths = []
        for m in re.finditer(r"<path([^>]*)/>", svg):
            attrs = m.group(1)
            if 'stroke="none"' in attrs:      # Tabler's invisible 24x24 bounding box
                continue
            paths.append(parse_path(re.search(r'\bd="([^"]+)"', attrs).group(1)))
        _ICON_CACHE[name] = paths
    return _ICON_CACHE[name]


# ---------------------------------------------------------------- figure and shapes
def new_figure(width_mm: float, height_mm: float):
    style.apply()
    fig = plt.figure(figsize=(width_mm * MM, height_mm * MM))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, width_mm)
    ax.set_ylim(0, height_mm)
    ax.set_axis_off()
    return fig, ax


def draw_icon(ax, name, cx, cy, size, color, z=5):
    """Draw a Tabler icon centred at (cx, cy) with a box `size` mm wide."""
    s = size / 24.0
    lw = 2.0 * s * PT_PER_MM          # Tabler stroke width is 2 units of 24
    for p in icon_paths(name):
        v = [(cx + (px - 12) * s, cy - (py - 12) * s) for px, py in p.vertices]
        ax.add_patch(PathPatch(MPath(v, p.codes), fill=False, edgecolor=color, lw=lw,
                               capstyle="round", joinstyle="round", zorder=z))


def badge(ax, name, cx, cy, r, color, status="built", z=4):
    """Icon in a filled circle. Future parts: white circle, dashed grey edge, grey icon."""
    st = shown_status(status)
    if st == "future":
        ax.add_patch(Circle((cx, cy), r, facecolor=style.WHITE, edgecolor=style.FUTURE,
                            lw=0.8, ls=(0, (2.2, 1.4)), zorder=z))
        draw_icon(ax, name, cx, cy, r * 1.25, style.FUTURE, z + 1)
        return
    ax.add_patch(Circle((cx, cy), r, facecolor=color, edgecolor=style.shade(color, 0.35),
                        lw=0.6, zorder=z))
    draw_icon(ax, name, cx, cy, r * 1.25, style.on_color(color), z + 1)
    if st == "planned":
        ax.add_patch(Circle((cx, cy), r + 0.75, fill=False, edgecolor=style.INK, lw=0.6,
                            ls=(0, (1.2, 1.0)), zorder=z))


def panel(ax, x, y, w, h, title, color, number=None, header_h=6.0):
    """Rounded panel with a coloured title band (number badge + bold italic title)."""
    body = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=2.4",
                          facecolor=style.tint(color, 0.9), edgecolor=style.shade(color, 0.2),
                          lw=0.9, zorder=1)
    ax.add_patch(body)
    band = Rectangle((x, y + h - header_h), w, header_h, facecolor=color, edgecolor="none",
                     zorder=1.5)
    band.set_clip_path(body)
    ax.add_patch(band)
    fg = style.on_color(color)
    tx = x + 2.2
    if number is not None:
        ax.add_patch(Circle((x + 4.0, y + h - header_h / 2), 2.0, facecolor=fg,
                            edgecolor="none", zorder=2))
        ax.text(x + 4.0, y + h - header_h / 2 - 0.05, str(number), ha="center", va="center",
                fontsize=7, fontweight="bold", color=color, zorder=3)
        tx = x + 7.2
    ax.text(tx, y + h - header_h / 2, title, ha="left", va="center", fontsize=8,
            fontweight="bold", fontstyle="italic", color=fg, zorder=3)
    return body


def card(ax, x, y, w, h, color, status="built", z=2):
    """White rounded card inside a panel (a sub-step)."""
    st = shown_status(status)
    if st == "future":
        ec, ls, fc = style.FUTURE, (0, (2.2, 1.4)), style.WHITE
    else:
        ec, ls, fc = style.shade(color, 0.15), "solid", style.WHITE
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.4",
                                facecolor=fc, edgecolor=ec, lw=0.6, ls=ls, zorder=z))


def item(ax, icon, x, y, label, note, color, status="built", r=3.0, gap=1.6):
    """Badge on the left, bold label and grey note on the right. (x, y) = badge centre."""
    badge(ax, icon, x, y, r, color, status)
    st = shown_status(status)
    lc = style.FUTURE if st == "future" else style.INK
    nc = style.FUTURE if st == "future" else style.MUTED
    tx = x + r + gap
    if note:
        ax.text(tx, y + 0.35, label, ha="left", va="bottom", fontsize=7, fontweight="bold",
                color=lc, linespacing=1.0, zorder=6)
        ax.text(tx, y + 0.05, note, ha="left", va="top", fontsize=7, color=nc,
                linespacing=1.0, zorder=6)
    else:
        ax.text(tx, y, label, ha="left", va="center", fontsize=7, fontweight="bold", color=lc,
                linespacing=1.0, zorder=6)


def arrow(ax, pts, color=style.INK, dashed=True, lw=0.9, head=1.6, z=3, status="built"):
    """Polyline arrow through pts with a solid filled head at the last point.
    Dashed = data flow between steps; solid = within a step."""
    if shown_status(status) == "future":
        color = style.FUTURE
        dashed = True
    xs, ys = zip(*pts)
    ls = (0, (2.6, 1.6)) if dashed else "solid"
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    # stop the line where the head starts so dashes do not poke through the tip
    end = (x1 - ux * head * 0.9, y1 - uy * head * 0.9)
    ax.plot(list(xs[:-1]) + [end[0]], list(ys[:-1]) + [end[1]], color=color, lw=lw, ls=ls,
            solid_capstyle="butt", dash_capstyle="butt", zorder=z)
    w = head * 0.45
    tip = (x1, y1)
    base = (x1 - ux * head, y1 - uy * head)
    ax.add_patch(Polygon([tip, (base[0] - uy * w, base[1] + ux * w),
                          (base[0] + uy * w, base[1] - ux * w)], closed=True,
                         facecolor=color, edgecolor=color, lw=0.3, zorder=z))


def legend_draft(ax, x, y):
    """Small key explaining the status marks (draft only)."""
    if MODE == "final":
        return
    ax.add_patch(Circle((x + 1.6, y), 1.3, facecolor=style.tint(style.INK, 0.8), edgecolor="none"))
    ax.add_patch(Circle((x + 1.6, y), 2.0, fill=False, edgecolor=style.INK, lw=0.6,
                        ls=(0, (1.2, 1.0))))
    ax.text(x + 4.4, y, "planned for Paper 1, not built yet", va="center", fontsize=7,
            color=style.MUTED)
    x2 = x + 50
    ax.add_patch(Circle((x2 + 1.6, y), 1.6, facecolor=style.WHITE, edgecolor=style.FUTURE, lw=0.8,
                        ls=(0, (2.2, 1.4))))
    ax.text(x2 + 4.4, y, "future work", va="center", fontsize=7, color=style.MUTED)
    ax.text(x2 + 22, y, "DRAFT", va="center", fontsize=7, fontweight="bold", color="#B3261E")


def save(fig, out_dir: Path, stem: str) -> list[Path]:
    """Write vector PDF and SVG plus a 600 dpi PNG preview."""
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if MODE == "final" else "_draft"
    paths = []
    for ext in ("pdf", "svg", "png"):
        p = out_dir / f"{stem}{suffix}.{ext}"
        kw = {"dpi": 600} if ext == "png" else {}
        if ext == "pdf":
            kw["metadata"] = {"CreationDate": None, "Creator": "paper/figures/src"}
        if ext == "svg":
            kw["metadata"] = {"Date": None}
        fig.savefig(p, **kw)
        paths.append(p)
    plt.close(fig)
    return paths
