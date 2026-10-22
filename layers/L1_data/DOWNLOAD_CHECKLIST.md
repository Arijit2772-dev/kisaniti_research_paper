# AGMARKNET download checklist (Punjab)

Started 22 October 2026. Source: agmarknet.gov.in → Reports → Price & Arrival Reports → **Date Wise Prices for Specified Commodity**. Each download covers one month, one commodity and one state, needs one CAPTCHA (typed by the user), and is exported as CSV.

**What we learned:**

- The report offers years **2021–2026 only**. For older history we need CEDA (2000 onward), which is optional for Paper 1.
- Each month includes every reporting Punjab mandi, day by day: arrivals (tonnes), variety, min/max/modal ₹ per quintal.
- Some mandis print a second entry for a day with a blank date. These rows are kept raw and counted as `blank_date_rows`; Layer 2 decides how to treat them.

## How each month is filed

1. Claude fills year, month, state and commodity.
2. The user types the CAPTCHA in the in-app browser and presses Submit.
3. Claude clicks Export as CSV, then runs:

```bash
python3 layers/L1_data/ingest_download.py
```

That command moves the file to `data/raw/agmarknet/<commodity>/<YYYY-MM>_punjab.csv` (git-ignored), writes `data/manifests/…json` (committed), and appends to [download_log.csv](download_log.csv).

## Priority order

Most useful months come first, so the forecasting work can start before everything is downloaded.

| Priority | Commodity | Months | Why | Count |
|---|---|---|---|---|
| 1 | Wheat | 2025-05 → 2026-03 | Held-wheat season after the 2025 harvest (prices move off the MSP) | 11 |
| 2 | Paddy(Basmati) | 2025-09 → 2026-03 | Latest basmati season | 7 |
| 3 | Wheat | 2024-04 → 2025-03, then 2023, 2022, 2021 seasons | Earlier held-wheat seasons for training and backtests | 48 |
| 4 | Paddy(Basmati) | 2021-09 → 2025-03 seasons (Sep–Mar) | Earlier basmati seasons | 28 |
| 5 | Wheat and basmati | 2026-04 → 2026-09; basmati Apr–Aug months | Completes the series; off-season basmati may be sparse | ~16 |

Total about 110 CAPTCHAs. Progress is tracked in [download_log.csv](download_log.csv). Done so far: Wheat 2025-04.
