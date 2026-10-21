# EXP-03 / EXP-08 — paper v1 run (15 Oct 2026)

Small, real-data experiments behind `~/Desktop/kisaniti_rp_v2.docx` (Sections 4.1–4.3). Status: RUN (not a promoted model; product gate unchanged).

| File | What it does |
|---|---|
| `geocode_mandis.py` → `mandi_coordinates.csv` | OpenStreetMap Nominatim coordinates for the 20 mandis (Sangat = railway-station point, Jaitu = tehsil centroid) |
| `forecast_experiment.py` | Naive, 7-date mean, MSP rule, ridge, GRU, T-GCN, A3T-GCN; forward-chaining test seasons 2023/2024/2025; 5 seeds |
| `allocation_experiment.py` | Synthetic 40-lot FPO (labelled synthetic), 5 Patiala-area mandis, real 2025 prices; P1–P4 policies + sensitivity |
| `make_figures.py` | Fig. 1, 2, 4 (Fig. 3 = cropped Wokwi circuit) |
| `paper_numbers.py` | Prints every number quoted in the paper from `results/` |
| `paper_build/` | docx-js builder (`cd paper_build && npm i docx && node build.js out.docx`) |

Data: `~/Documents/sem_6/capstone/agmarknet_paddy_common_punjab_cleaned_records.csv` (AGMARKNET Paddy(Common), Punjab, Sep–Dec 2020–2025). The AGMARKNET API now needs a captcha, so no new data were downloaded.

Main results: >96% of reported prices equal Grade-A MSP in every season; MSP rule best (mean MAE Rs 1.26/q), naive 1.77, A3T-GCN 2.36 (best learned). Cooperative integer program: +Rs 0.79/q over nearest-mandi at a 300 q/mandi-day limit, +3.5 to +13.9 at 200 q; independent choice breaks limits in 100% of runs.

Assumptions (synthetic): road factor 1.3, Rs 2/q-km, Rs 2/q/day waiting, 300 q per mandi-day. Software: Python 3.13, PyTorch 2.9.1, SciPy 1.15.2 (HiGHS).
