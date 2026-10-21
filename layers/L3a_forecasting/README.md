# L3a — Price forecasting (phase R4, EXP-03/04)

**Research questions:**
1. Which model forecasts Punjab wheat and basmati mandi prices best at 1–120 days?
2. Are its 80% and 95% ranges trustworthy (CHAT-22)?
3. For MSP crops, can anything beat the MSP rule? (v2 says no for paddy.)

**Models compared, and why each is included:**

| Model | Why included |
|---|---|
| Naive (last price), seasonal naive, moving average | Required baselines; prices are sticky |
| MSP rule (paddy, wheat in the procurement window) | v2 showed it wins for MSP crops |
| ETS / ARIMA (statsmodels/statsforecast) | Classic, interpretable ranges |
| Ridge, XGBoost / LightGBM with lags, calendar, arrivals | Strong tabular learners |
| GRU, T-GCN, A3T-GCN (existing v2 code) | Deep sequence and graph models; tests whether linking mandis helps |
| Chronos-2 (zero-shot) | Pretrained time-series foundation model; check its training-data overlap |

**Protocol:**
- Rolling origin; train only on the past; the final season held out.
- Horizons 1, 7, 14, 30, 60, 90 and 120 days.
- 5 seeds for neural models.
- Ranges: quantile models, conformal intervals and Chronos-2 quantiles compared.

**Metrics:**
- MAE (₹/q), MASE, sMAPE;
- direction accuracy;
- interval coverage and pinball loss;
- Diebold–Mariano significance tests;
- training and inference time.

**Outputs:**
- `results/forecast_<crop>.csv` and `results/intervals_<crop>.csv`;
- Fig. "MAE by horizon" and Fig. "interval coverage";
- Sections 3.3 and 4.1.

**Done when:** each crop and horizon has a best model chosen by the promotion rule in the [research plan](../../../kisaniti/docs/research/RESEARCH_AND_EXPERIMENT_PLAN.md), with negative results reported.
