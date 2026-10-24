# Cleaning plan (Layer 2) — how the raw AGMARKNET files become a model-ready dataset

24 October 2026 • Concrete steps for phase B. Ground rules: raw files are never edited; every raw row ends up kept, flagged or removed with a reason; missing stays missing; nothing is invented.

## 1. What the raw files look like (verified on the 29 files)

- One CSV per month; market names appear as header lines (`Market Name : …`), followed by dated rows: date, arrivals (tonnes), variety, min, max, modal ₹/quintal.
- **Blank-date rows (580):** a row with empty date and arrivals directly after a dated row in the same market, for the other variety (for example `01/11/2024 … 1121` then `,,Basmati 1509`). The most likely cause is merged table cells on the website (one date and one arrivals figure shared by both varieties), which the CSV export flattens. **This is a hypothesis to confirm on the website** (step 2 below); if true, these are real observations (about 9.5% more data), not junk.
- **"-" in min or max (4 rows):** not reported.
- **Outlier to check:** a modal price of ₹800 in 2021-22 when the season median is ₹3,170.

## 2. Steps

| # | Step | Detail | Output |
|---|---|---|---|
| B.1a | Parse to a tidy table | Columns: `row_id`, `source_file`, `market_raw`, `variety_raw`, `date`, `arrivals_t`, `min`, `max`, `modal`, and flags; keep line numbers for tracing | `data/processed/basmati_tidy.parquet` (git-ignored) |
| B.1b | Blank-date rule | Give a blank-date row the **date and market of the preceding dated row in the same file and market only**; set `date_inferred=true`; `arrivals` is the shared date-level figure, marked `arrivals_shared=true` and never added twice. Never carry a date across a market boundary | counts of inferred rows, checked against the website sample |
| B.1c | Variety map | `1121`→1121; `Basmati 1509`→1509; `Basmati`, `Sugandha`, `SuperFine(Basmati)`, `Other` kept as separate labels and **not used in forecasting** (3% of rows) | mapping table, reviewed by a human |
| B.1d | Market map | 86 raw names → canonical market IDs; review near-duplicates (for example `Amloh APMC` and `Amloh(Gobind Garh Mandi) APMC` may be two markets); coordinates for distance later (20 already geocoded in v2) | `mandi_master.csv` |
| B.1e | Rule checks | min ≤ modal ≤ max when present; positive prices; date inside the file's month; arrivals ≥ 0; duplicate (market, variety, date) with different prices → flag, keep both, never average | flag counts by rule |
| B.1f | Outlier flags | Past-only robust screen per series (MAD, as designed) and the ₹800 case; **flag only**, never delete, because genuine spikes are valuable | flagged list |
| B.2 | Human hand check | About 50 stratified rows (include flagged, blank-date and a few normal rows) compared with the AGMARKNET page by a person; record who and when. Confirms or rejects the blank-date rule | `results/L2_cleaning/hand_check.csv` |
| B.2b | Independent spot check | One month compared with a second source (eNAM, Punjab Mandi Board portal or published price reports); report the agreement | short note in the results |
| B.3 | Compare cleaning options (EXP-02) | A: raw rows only; B: + blank-date rule; C: + outlier flags used as exclusions; D: + MAD vs Hampel vs IQR screens. Measure precision/recall on the hand-checked sample and the effect on forecast error of a simple baseline and one learned model | `results/L2_cleaning/comparison.csv` |
| B.4 | Build the modelling series | Daily **variety-level index**: median modal price across mandis reporting that day (require at least 3 mandis); keep the count of mandis and the interquartile range; mandi-level series only for mandis with at least 60 observations; **no forward-fill presented as observed** | `basmati_index.csv` |
| B.5 | Dataset release | Manifest with checksums, rule versions, counts; reconciliation: raw dated rows + blank-date rows = kept + flagged + removed, with zero unexplained | `data/manifests/basmati_clean_v1.json` |

## 3. Tests (automated, in CI-style pytest)

- Row reconciliation is exact for every month.
- Blank-date rows never receive a date from another market or file.
- A synthetic corrupted copy of the data (labelled synthetic; mechanics only) is detected by the flags.
- Re-running the pipeline on the same raw files gives identical output (hash equal).
- Nothing in `data/raw` changes (checksums equal the manifests).

## 4. Done when

Counts reconcile, the hand check and the spot check are recorded, the blank-date rule is confirmed or replaced, the chosen options are justified by B.3, and the variety index exists with its coverage table.
