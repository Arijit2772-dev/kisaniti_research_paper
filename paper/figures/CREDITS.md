# Figure credits and licences

## Icons: Tabler Icons (MIT)

- Source: [Tabler Icons](https://tabler.io/icons), npm package `@tabler/icons` **3.46.0** (published 28 Jul 2026), outline style.
- Licence: MIT, copyright (c) 2020-2026 Paweł Kuna. The full text is in [`src/icons/tabler/LICENSE`](src/icons/tabler/LICENSE) and must stay next to the icons.
- Only the icons we use are copied into [`src/icons/tabler/`](src/icons/tabler/), unchanged. The scripts read their SVG path data and draw it as vector strokes.
- No brand logos are used. WhatsApp is shown with the generic `message-circle` icon and a text label, so no trademark artwork appears in the paper.
- To add an icon: run `npm pack @tabler/icons@3.46.0`, copy `package/icons/outline/<name>.svg` into `src/icons/tabler/`, and list it below.

Icons in use: adjustments, copy, device-desktop, lock, router, alert-triangle, arrows-split, brain, calendar, calendar-time, chart-bar, chart-dots, chart-histogram, chart-line, checks, clipboard-check, cloud-upload, coin-rupee, cpu, database, device-mobile, droplet, eraser, file-check, file-spreadsheet, filter, gauge, git-branch, history, hourglass, list-check, map-pin, math-function, message-circle, packages, receipt, refresh, route, ruler, scale, server, table, target, temperature, timeline, topology-star-3, trophy, truck, user-check, users, wheat, wifi, world-download (not all are drawn yet).

## Palette

Defined once in [`style.py`](style.py), one colour per system layer:

| Layer | Colour | CIELAB L* |
|---|---|---|
| L1 data sources | indigo `#373C7A` | 28 |
| L2 cleaning | teal `#167170` | 43 |
| L3 decision models | terracotta `#CA7644` | 58 |
| L4 manager review | green `#7EC085` | 72 |
| L5 WhatsApp and sale records | sand `#ECD781` | 86 |
| Future / not built | grey `#9AA0A6`, dashed | — |

Checks (`python3 paper/figures/style.py`):
- greyscale: lightness steps of at least 13.9 L*, so the five layers keep their order when printed in black and white;
- colour vision: the smallest pairwise CIELAB distance is 38.8 (normal), 21.4 (protan), 24.9 (deutan) and 23.1 (tritan), using the Machado, Oliveira and Fernandes (2009) simulation matrices at full severity.

The palette was chosen by searching hues at fixed lightness levels for the largest smallest distance under all three simulations; it is our own, not taken from another source.

## Fonts

Arial (falls back to Helvetica, Liberation Sans or DejaVu Sans), embedded as TrueType in the PDFs. Smallest text is 7 pt at the printed size (122 mm wide, the LNCS text width).

## Data

Fig. 2's split grid is read from `FOLDS` in `legacy/v2_from_rp_kisan/experiments/forecast_experiment.py`. No measured values appear in Fig. 1 or Fig. 2.

## Fig. 3 (hardware) and the storage-scenario figure

- `src/fig3_hardware.py` (added by the M5 hardware session, 22 Oct 2026) reuses `figlib`; icons `copy`, `device-desktop`, `lock` and `router` were added from `@tabler/icons@3.46.0` (outline), unchanged.
- `fig_storage_scenarios.*` is a data plot from `layers/L3b_storage_iot/make_figures.py` (simulated data, results/L3b_storage/).
