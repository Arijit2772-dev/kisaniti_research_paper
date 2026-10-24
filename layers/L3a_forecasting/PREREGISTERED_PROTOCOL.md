# Pre-registered forecasting protocol (C.0) — Paddy(Basmati), Punjab

24 October 2026 • **Status: DRAFT for the owner's approval. It becomes FROZEN by a commit whose message starts with "C.0 freeze".** No forecasting model has been run on this data for the purpose of this protocol. After the freeze, every change is an amendment (§12) with date and reason, and results before and after are both reported.

## 1. What has been looked at already (disclosure)

- `layers/L1_data/power_check.py` (exploratory, 24 Oct) ran a naive baseline and one ridge learner over **all five seasons** to estimate what difference could be detected. Its output is `results/L1_coverage/power_check.txt`. It was used to set the reporting threshold in §8 and **not** to choose or tune any model. It did show the naive and ridge errors on all seasons, including the test season; this is stated here so a reader can judge it.
- `layers/L3a_forecasting/count_horizon_pairs.py` only counts index days (no prices compared).
- The earlier paddy(common) experiments (v2) are a different commodity and are not used for choices here.

## 2. Series

- Variety-level daily index from `layers/L2_cleaning/build_index.py` for **1121** and **Basmati 1509**: median modal ₹/quintal over mandis that reported that variety that day, at least 3 mandis, no filling. Other variety labels (about 3% of rows) are not forecast.
- **Which variant is primary is decided by the hand check (B.2) with a rule fixed now:** `with_blank` is primary if at least 19 of the 20 blank-date rows in the hand-check sheet are confirmed on the website (same date, same prices, shown under the preceding date); otherwise `dated_only` is primary and the blank-date rule is reported as rejected. The other variant is run as a sensitivity analysis.
- The index is a mandi-level summary price, **not the price a farmer received**.

## 3. Splits

| Role | Seasons | Use |
|---|---|---|
| Initial training | 2021-22 to 2023-24 | fit; expanding window thereafter |
| Validation | 2024-25 | tune hyperparameters, interval calibration, choose between listed variants |
| **Test (held out)** | 2025-26 | evaluated **once**, after the configuration is frozen |
| Prospective check | 2026-27 (Sep–Oct 2026 so far) | reported separately at the end, labelled partial |

- Rolling origin: each forecast uses only data up to its origin day. A season begins with no earlier days in-season; an origin is eligible only after **10 index days of the current season** exist. Features use same-season values only (no lag across the February–August gap).
- A **target** is the index value on exactly origin + h calendar days in the same season. No nearest-day matching, no filling.

## 4. Horizons (deviation from the earlier plan, see §11)

Pairs available per horizon come from `results/C0_protocol/horizon_pairs.csv` (index days exist only September–January).

| Horizon (calendar days) | Treatment | Why |
|---|---|---|
| 1, 7, 14 | **Primary** | At least 60 test-season pairs per variety at every primary horizon (1121: 76, 73, 66; 1509: 71, 66, 60 under `dated_only`) |
| 28 | Secondary | 59 (1121) and 47 (1509) test-season pairs, strongly overlapping |
| 60 | Descriptive only | 29 and 24 test-season pairs, heavily overlapping; no tests, no claims |
| 90, 120 | **Not evaluated** | 25 and 6 pairs in all seasons together for 90 days; 4 and 1 for 120 days |

The product still needs advice beyond these horizons (CHAT-22 asks for ranges beyond 7 days). The paper will say the forecast evidence covers up to 28 days and that longer-horizon advice rests on assumptions, not on a tested forecast.

## 5. Models (eight, fixed)

| # | Model | Notes |
|---|---|---|
| 1 | Naive (last index value) | reference for every comparison |
| 2 | Seasonal naive | median of the previous season's index within ±3 days of the same calendar day; not available for 2021-22 |
| 3 | Moving average | mean of the last 5 index days |
| 4 | ETS | statsforecast `AutoETS` |
| 5 | ARIMA | statsforecast `AutoARIMA` |
| 6 | LightGBM | features: lags 1,2,3,5,7 of the index, day-of-season, number of mandis (lagged), lagged IQR. 5 seeds |
| 7 | GRU | one small network, fixed grid on validation only. 5 seeds |
| 8 | Chronos-2 zero-shot | pretrained; its training data may include public price series, so its result is flagged. Checked 24 Oct: runs on this Mac on CPU (`amazon/chronos-2`, Apache-2.0, 120M parameters; chronos-forecasting 2.3.2, torch 2.14.1). Input: the index of the current season only, reindexed to daily with missing days left as NaN (not filled); quantile forecasts from the model. Dropped and reported if it fails later |

Not included, with reasons: **arrivals as a feature** (arrivals are shared or ambiguous for blank-date rows and contain very large values at some markets; unchecked), **T-GCN and A3T-GCN** (they need mandi-level series, which the data-adequacy note rejects as too short), **XGBoost** (one gradient-boosting model is enough for the budget of eight), **an MSP rule** (basmati has no MSP; whether any MSP-anchoring applies to basmati is UNKNOWN and is not assumed).

Hyperparameter grids are written to `layers/L3a_forecasting/config/grids.json` before the first validation run and are not changed afterwards.

## 6. Prediction ranges

- 80% and 95% intervals for every model at every primary horizon: ETS and ARIMA analytic; LightGBM quantile objectives; split-conformal intervals (residuals from the validation season, per horizon) for models 1–3, 6 and 7; Chronos-2 quantiles.
- Reported: empirical coverage with a block-bootstrap 95% interval, mean width, pinball loss. A range is called calibrated only if the nominal level lies inside that interval. Narrow coverage claims are not made from fewer than 40 test pairs.

## 7. Metrics

- Primary: **MAE in ₹/quintal** and **MASE** (scale = in-sample naive h-step MAE of the training seasons).
- Secondary: sMAPE, direction accuracy (up/down versus origin), interval metrics (§6), run time.
- Computed per variety × horizon × season, and pooled over the test season.

## 8. Inference and what may be claimed

- **Family:** each of models 2–8 against the naive model, for each variety and primary horizon (7 × 2 × 3 = 42 tests). Test: Diebold–Mariano with the Harvey–Leybourne–Newbold small-sample correction and a Newey–West variance with lag h − 1, on the test season only. **Holm correction over the whole family.**
- **Effect size:** relative change in MAE versus naive with a moving-block bootstrap 95% interval (block length at least h days).
- **A model is reported as better than naive only if all hold:** Holm-adjusted p < 0.05; the bootstrap interval excludes zero; and the point estimate of the MAE reduction is at least the smallest detectable gain found in the power check (power check: about 11–13% for 1121 and 12–17% for 1509, depending on horizon; to be re-computed from the final pairs and stated per variety and horizon). Otherwise the result is "no detectable difference".
- **Between non-naive models:** no pairwise winner is claimed. The Model Confidence Set (α = 0.10) at each variety × horizon is reported as the set of models not distinguishable from the best; the ordering inside the set is descriptive.
- Sensitivity runs (other index variant, minimum mandis 2 and 4) are labelled as such and never replace the primary result.

## 9. Promotion rule

For each variety and primary horizon the product uses the model that meets §8 against naive; if none does, it uses **naive and says the baseline is enough**. This is a valid, reportable outcome.

## 10. Execution rules

- Order: freeze this file → write grids → run validation → freeze configuration (a commit) → run the test season once → write results files → numbers reach the paper only through `paper/numbers.py`.
- All random seeds are fixed and recorded; one results file per model; the exact commit of code and data manifests is logged with the results.
- Failed or unstable runs (for example the GRU not converging) are reported, not removed.

## 11. Deviations from earlier documents (the owner must approve these)

| Earlier plan | This protocol | Reason |
|---|---|---|
| Horizons 1, 7, 14, 30, 60, 90, 120 (`L3a_forecasting/README.md`) | 1, 7, 14 primary; 28 secondary; 60 descriptive; 90 and 120 not evaluated | Index exists only Sep–Jan; too few pairs (§4) |
| T-GCN, A3T-GCN compared | Dropped | Needs mandi-level series, judged too short |
| "MSP rule per variety" (tracker C.2) | Not used for basmati | Basmati has no MSP; anchoring is UNKNOWN |
| ETS/ARIMA, XGBoost/LightGBM both | One GBM (LightGBM) | Budget of eight models |
| Arrivals as a feature (tracker C.3) | Not used | Arrivals unchecked |

## 12. Amendment log

None yet.
