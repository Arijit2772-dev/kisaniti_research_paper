# Is one data source enough? Data adequacy for the paper

24 October 2026 • Assessment written after the basmati download, using the filed data and exploratory statistics (script-checked; the numbers below come from the 29 raw files, 6,098 dated rows). This is a planning judgement, not a result to publish.

## 1. What we have

| Item | Value |
|---|---|
| Source | AGMARKNET (official Government of India price portal), Punjab, Paddy(Basmati) |
| Period | Five full seasons 2021-22 … 2025-26 plus Sep–Oct 2026 |
| Size | 6,098 dated rows + **580 blank-date rows that are probably real second-variety prices** (see §3), 86 mandis, 726 trading days |
| Varieties | 1121 (3,234 rows) and Basmati 1509 (2,700) make up 97%; four others are tiny |
| Season shape | Dense in Sep–Dec, thin in Jan–Feb, **nothing in June** |

## 2. What the data says (exploratory, to be redone properly in EXP-01/03)

- **Prices really move** (unlike MSP paddy). For variety 1121, consecutive reports in the same mandi within 7 days change by a median of ₹50/q and a 90th percentile of ₹300/q; only 32% are unchanged (1509: 20%).
- **Mandis really differ.** On days with at least 8 mandis reporting, the median gap between the highest and lowest 1121 price is ₹1,468/q (middle-half spread ₹595). Part of this is quality and grade, which the data cannot separate, so it is an upper bound on the gain from choosing mandis.
- **Prices rise within the season.** Median 1121 modal price from Sep–Oct to Dec–Feb: ₹1,965→3,500, 3,275→3,900, 3,200→4,200, 2,690→3,515, 3,000→3,575 (2021-22 … 2025-26). Early-season arrivals are often lower grade and the Dec–Feb sample has fewer mandis, so this does **not yet** prove that holding pays; it is the question the hold-or-sell backtest has to answer.
- **Series are short.** 71 mandi series for 1121 but only **21 have at least 60 observations** (1509: 14 of 56); the median series has about 25. Per-mandi models would be starved of data.

## 3. Is it enough?

| Purpose | Verdict | Why |
|---|---|---|
| Paper 1 (conference): forecasting at variety level with ranges | **Enough for a small, pre-registered comparison; not enough to rank many close models** (see 3b) | About 700 trading days of daily data in five seasons; a variety-level daily index can be built; train 2021-22 to 2023-24, validate 2024-25, test 2025-26, with Sep–Oct 2026 as a genuinely unseen check |
| Paper 1: allocation and fairness | **Enough** | Needs real price differences between mandis (present) plus a synthetic FPO, which is labelled as such |
| Paper 1: hold-or-sell backtest | **Weak but usable as exploratory** | Only **five seasons**, so any average gain rests on five data points. Report per-season results and bootstrap intervals; do not claim statistical significance or "proven benefit" |
| Paper 1: per-mandi forecasting | **Not enough** | Few long series. Forecast the variety-level index and add mandi offsets |
| Paper 2 (journal) | **Not enough on its own** | Needs many more seasons, a second source or region, and validation against real FPO or farmer sales |

## 3b. Power check: can this data show real differences between models? (measured 24 Oct)

Script: `power_check.py`; output: `results/L1_coverage/power_check.txt`. Exploratory, rolling-origin, expanding window, naive vs a ridge-on-lags learner, variety-level daily index (at least 3 mandis per day).

| Item | 1121 | 1509 |
|---|---|---|
| Index days available | 433 (65–90 per season) | 369 (36–86 per season) |
| Forecast origins (1-step / 5-step) | 383 / 356 | 317 / 295 |
| Smallest model gain over naive that a test can detect (80% power, 5% level) | **about 11–13% of naive error** | **about 12–17%** |
| What the simple learner achieved | −0.2% (1-step), +5.6% (5-step): not detectable | −7.4%, −0.9%: not detectable |
| Average correlation between mandis' day-to-day changes | 0.37, so pooling mandis adds far fewer independent samples than rows suggest | |

**What this means**

- **Detectable:** large effects, roughly 12% or more over the baseline. A good model, or an MSP-style rule that wins clearly, will show.
- **Not detectable:** differences of a few percent between similar models. With about 8 models, the ranking in the middle of the table would be noise. Any claim like "model A beats model B" below ~10% would not hold up.
- **Deep models** (GRU, T-GCN, A3T-GCN) have only ~430 daily points per variety to learn from. Published studies where they win used 10–15 years across 100+ markets. Expect them to be unstable here, and say so.
- **Hold-or-sell:** one outcome per season, so five numbers. Five out of five seasons in the same direction would give a sign-test p of about 0.03 (one-sided); anything else is inconclusive.
- **Allocation and fairness:** not affected; they use same-day price differences between mandis, which exist in volume.

**Ways to get enough power, in order of value**

1. **CEDA history (2000 onward, about 20 more seasons). Note: at commodity level only (no variety field in the API); runbook and tested filing script: [CEDA_RUNBOOK.md](CEDA_RUNBOOK.md).** Roughly 4–5 times more origins would cut the smallest detectable gain to about 5–7%. This is the single most important addition for a paper that trains and ranks many models. The portal advertises downloadable raw files, over 300 commodities and 2,700 mandis, updated monthly; whether it needs registration is not stated on the pages we could reach, so the owner must check ([CEDA Agri Market Data](https://agmarknet.ceda.ashoka.edu.in)).
2. **A second region** (Haryana basmati) as an independent test series, and more varieties.
3. **Fewer candidates, fixed in advance:** at most 6–8 models, the protocol written before looking at the test seasons, and a multiple-comparison correction (Holm, or a Model Confidence Set).
4. **Report effect sizes with confidence intervals**, not just "best model".

## 4. The "one website" question

- AGMARKNET is the official public source. In the literature review of 38 studies, price-forecasting work on Indian mandis commonly relies on it (for example daily data for 165 markets 2010–2024, Punjab basmati across 74 markets 2000–2023). So using it is normal. The weakness is not the source but having **only one source with no independent check**.
- **Cheap fixes that make one source credible:**
  1. **Hand check:** compare about 50 rows against the website (already planned, step B.2); also confirms the blank-date rule.
  2. **Independent spot check:** compare one month with a second source (eNAM trade data, the Punjab Mandi Board portal, or published press price reports) and report the agreement.
  3. **Internal consistency tests:** min ≤ modal ≤ max, prices against MSP, price against arrivals.
  4. **State the limitation** in the paper: modal price is a mandi-level summary, not the price a farmer received.
- **Extensions that matter for Paper 2** (optional now):
  - CEDA's harmonised AGMARKNET archive (2000 onward): about 20 more seasons for the hold-or-sell backtest. It is the same underlying data, so it adds history, not independence.
  - Haryana basmati mandis: a second region for robustness.
  - Weather (IMD or NASA POWER) and export prices (APEDA) as covariates.
  - Real farmer sale records from an FPO (J-forms), once a partner exists.

## 5. Decisions this implies (recorded in the tracker)

1. Model the **variety-level daily index** (1121 and 1509), with mandi offsets; do not train per-mandi models.
2. Treat hold-or-sell results as **exploratory** in Paper 1, with per-season reporting and uncertainty; seek CEDA history for Paper 2.
3. Add the **independent spot check** to the cleaning phase.
4. Never describe the AGMARKNET modal price as the farmer's price.
