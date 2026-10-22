# AGMARKNET download runbook (for any AI agent or person)

22 October 2026 • Exact steps to keep downloading Punjab mandi price data, the way it has been done so far. Any agent with a browser and a shell can continue from here. **A human must type every CAPTCHA.** Never solve, bypass or automate a CAPTCHA, and never use a CAPTCHA-solving service.

## 0. Before you start

- Workspace: `~/Documents/kisaniti_research_paper` (GitHub `Arijit2772-dev/kisaniti_research_paper`).
- Read: [DOWNLOAD_CHECKLIST.md](DOWNLOAD_CHECKLIST.md) (findings) and [download_log.csv](download_log.csv) (what is already filed). Skip any month already in the log.
- Decision CHAT-32: **Paddy(Basmati)** is the main crop to download. Wheat downloads are paused, because off-season Punjab wheat has only 2–5 rows a month.

## 1. One month, step by step

1. Open `https://agmarknet.gov.in/datewisespeccommdodityinput` (Reports → Price & Arrival Reports → "Date Wise Prices for Specified Commodity").
2. Fill the four dropdowns. Each is a custom button: click it, then click the option text.
   - **Year:** e.g. `2025` (the site offers only 2021–2026).
   - **Month:** e.g. `November`.
   - **State/UT:** `Punjab` (not "Punjabi", which is the language switch).
   - **Commodity:** `Paddy(Basmati)` (not "Basmati Rice").

   Check that the page text shows all four values.
3. **Ask the human** to type the CAPTCHA shown on the page and press **Submit**. In the Claude desktop app the in-app browser must be visible (Cmd+Shift+B) or the human cannot see it.
4. The result page title reads "Date Wise Prices for Specified Commodity on <Month>, <Year> for Commodity : <Commodity>, State/UT : Punjab". Confirm it matches what you asked for.
5. Click **Export** → **Export as CSV**. The file lands in `~/Downloads` as `Date_wise_Prices_for_Specified_Commodity_<date>_<time>.csv`. Wait about 5 seconds.
6. File it:

```bash
cd ~/Documents/kisaniti_research_paper && python3 -I layers/L1_data/ingest_download.py
```

   The script reads month, commodity and state from the file's own title line. It moves the file unchanged to `data/raw/agmarknet/<commodity>/<YYYY-MM>_punjab.csv` (git-ignored), writes `data/manifests/agmarknet_<commodity>_<YYYY-MM>_punjab.json` (SHA-256, rows, markets, date range) and appends to `download_log.csv`. It refuses duplicates.
7. Check the printed summary. **0 rows** or a wrong month means something went wrong: delete the filed file and its manifest line, then redo the month. "Blank-date rows" are normal; they are kept raw for the cleaning layer.
8. Every few months, commit and push:

```bash
cd ~/Documents/kisaniti_research_paper && git add layers/L1_data data/manifests && git commit -m "L1: basmati <months> filed" && git pull --rebase --autostash && git push
```

   Never `git add -A`: other sessions have uncommitted work in this repo. Never commit `data/raw/`.
9. Go back to step 1 for the next month. The "Back" button does **not** keep the selections, so refill all four.

## 2. Months to download (Paddy(Basmati), Punjab), in this order

Tick by checking `download_log.csv`.

| # | Months | Why |
|---|---|---|
| 1 | 2025-09, 2025-11, 2025-12, 2026-01, 2026-02 | Latest season (2025-10 is done) |
| 2 | 2026-09, 2026-10 | Current season (site data frozen up to about 20 Oct 2026) |
| 3 | 2024-09 → 2025-02 | Season 2024–25 |
| 4 | 2023-09 → 2024-02 | Season 2023–24 |
| 5 | 2022-09 → 2023-02 | Season 2022–23 |
| 6 | 2021-09 → 2022-02 | Season 2021–22 |
| 7 | One off-season test: 2025-06 | Check whether basmati trades outside Sep–Feb. If it has fewer than ~30 rows, skip the other off-season months |
| 8 | Optional: 2026-03 → 2026-08, other years' Mar–Aug | Only if the test in row 7 shows real data |

That is about 37 CAPTCHAs for rows 1–7.

## 3. Rules

- Raw files are never edited, renamed by hand or "fixed". Cleaning happens in Layer 2.
- Don't download from third-party sites as a substitute; only agmarknet.gov.in, data.gov.in or CEDA.
- Record anything unusual, such as an empty month, a changed column header, or a different site layout, in DOWNLOAD_CHECKLIST.md under "Findings".
- If the site changes its form or export, update `ingest_download.py` and keep its header check strict.
