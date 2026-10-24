# Check of Ladhar et al. (2023), ACM JCSS 1(1), Art. 6, DOI 10.1145/3609262

Date of check: 2026-10-24

## Source used
Full text read: the authors' own copy, linked from Aaditeshwar Seth's publications page at IIT Delhi.
- Listing page: https://www.cse.iitd.ac.in/~aseth/publications.html
- PDF: https://www.cse.iitd.ac.in/~aseth/market-intelligence-commodity-prices.pdf
- The PDF is the published ACM version (32 pages, Art. 6, September 2023). Page numbers below are the journal's 6:N.
- OpenAlex marks the ACM PDF as bronze open access. dl.acm.org returned 403 to automated fetches, as expected.
- I did not use collegesidekick.com, which appeared in search results. It is a study-document aggregator, not an author copy.

## (1) Data source, period, markets (Sec. 3, 4.1, 5.3; pp. 6:5-6:7, 6:20)
- Prices and arrivals were scraped daily from Agmarknet (Government of India), 1 Jan 2006 to 31 Dec 2021.
- Six "main" markets in Rajasthan and Madhya Pradesh were kept. Each had at least 50% of days present and no gap of 60 days or more: Kota, Bhawani, Sonkatch, Ratlam, Mahidpur, Ganjbasoda (Table 1).
- Missing days were filled with ARIMA, using past values only.
- The target market is Adilabad (Telangana), where Agmarknet data is sparse. Field officers collected daily Adilabad prices through ODK from November 2021. That gave 90 days, plus 305 older days from Agmarknet.
- Adilabad forecasts come from transfer learning: models trained on the main markets, then fine-tuned on 39 non-overlapping 90-day windows (Sec. 5.3).
- Satellite indices (NDVI, rainfall and others) and news-event series were also tested as inputs (Sec. 4.4, 4.5).

## (2) Forecasting methods and main result (Sec. 5.1, Tables 4, 5, 7, A.3, A.6; pp. 6:10-6:13, 6:21)
- Compared: LSTM and TCN, each univariate and multivariate. Exogenous inputs were a surrogate leading market's price, arrivals, a sine/cosine seasonality feature, satellite data and news data.
- Input is the last 60 days; output is a 30-day horizon. Retraining is every 15 days. Evaluation is rolling, 2014 to 2020, scored by RMSE.
- Main result: the multivariate TCN with a surrogate-market price is best in general.
  - Kota: about 187 INR/quintal RMSE, against 219 for the univariate TCN and 318 for the univariate LSTM (Table 4).
  - The result is not uniform. Bhawani in Table 4 is close between variants, and in the season-only Table 5 an LSTM variant is best for Bhawani and Ratlam-Sonkatch is mixed.
- Satellite and news inputs did not beat surrogate prices at 30 days (Table A.3). They sometimes helped at the 12-week weekly horizon (Sec. 6.3, Table A.6).
- Adilabad: fine-tuned RMSE was 187.41 (Bhawani + Ganjbasoda), against 215.37 without fine-tuning (Table 7).
- The field system uses the Bhawani-Ganjbasoda model (p. 6:22).

## (3) How sell or hold is decided (Sec. 5.2; pp. 6:13-6:18)
- Each day the system recommends the top-3 dates, from today through day 29, on which to sell.
- Method: prospect theory. Each candidate day k is compared with selling today.
  - The forecast ensemble gives p_k, the probability that the price on day k beats today's price.
  - It also gives g_k, the mean gain over today when it is higher, and l_k, the mean loss when it is not.
  - The score is w(p)v(g) + w(1-p)v(l), using Abdellaoui's value and weight functions with a loss-aversion parameter of 2.61.
- Price ranges are used. The ensemble is 5 TCN models: one on the original data and 4 "perturbed" ones. The perturbation shuffles which periods are treated as missing and re-imputes them. This gives 5x(30-k) forecasts per future day.
- It is not an optimisation. The paper's equations include no storage loss, no holding or storage cost, no interest or financing cost, no quality degradation and no quantity decision.
- Storage appears only as context:
  - Soyabean is described as safely storable for 2 to 4 months without cold storage (p. 6:3).
  - Cooperatives pay a 50% advance to farmers and deduct transport and overheads at sale (p. 6:5).
- A "maximum forecast mean" baseline is also compared.

## (4) Multi-farmer allocation, fairness, human approval, sensors, WhatsApp (Secs. 3, 6; pp. 6:3, 6:21-6:24, 6:25-6:26)
- Multi-farmer allocation: no. The unit is one cooperative's stored lot, and the decision is only when to sell. Anamat pooling is described as background.
- Fairness: no. Fairness is mentioned once, in the conclusion, as a general trust factor in AI systems (p. 6:26). It is not implemented.
- Human approval step: not as a workflow. Recommendations are shown in an Android app used by CCD field officers. The authors report that officers treat them as advisory and do not rely on them alone (p. 6:23). There is no formal approve/reject step.
- Sensors: no.
- WhatsApp: only a "share screens via WhatsApp" feature requested by users (p. 6:23). Farmer-facing delivery is a separate IVR voice-call system (about 3,000 farmers, 115 messages, about 100,000 calls, Sec. 6.1). The paper says IVR could relay price and sale recommendations, but it did not do so.

## (5) Evaluation (Sec. 5.2.3, Tables 6, A.4, A.5, Sec. 6, 7; pp. 6:18-6:25)
- Offline backtest on real historical prices, with no simulation of farmers. Seasons run September to January, 2014 to 2020, in Kota, Bhawani and Ratlam.
- Metrics:
  - PAP: share of recommendations that beat selling today.
  - NG: mean INR per quintal gained over selling today.
  - NG-Oracle: the gain from perfect foresight.
- Gain numbers as stated:
  - Prospect theory with perturbation had a PAP of 73.9 to 99.4% for Kota across years (Table 6). The text says "often above 90%".
  - Kota NG by year for prospect theory with perturbation: 26.4, 20.4, -13.4, 92.5, 28.6, 41.0, -0.01 INR/quintal.
  - NG is "typically 20% to 50% of the oracle" (p. 6:18). Oracle values for Kota range from 67 to 269.
  - Gains are modest, sometimes negative, and poor in 2015-16 and 2020-21 (hoarding and crop damage).
- The text says prospect theory with perturbation works best overall. The tables show the simple max-mean baseline beating it on NG in several years (Kota 2015, 2017, 2020).
- Field test: Android app released October 2022. Field officers tracked 16 cooperatives over 5 months.
  - Prices were flat in 2022-23, so the test was uninformative about recommendation quality.
  - By the end of January 2023, 7 of 16 cooperatives had sold small amounts.
  - The authors state they cannot yet say the app is safe to deploy (p. 6:25).
- No realised farmer income gain is reported. The "modest gains" are backtest numbers only.

## (6) Judgement on overlap and gap 4

Overlap with the KisanNiti design is partial, and real in two places.
1. It is a deployed-style hold-or-sell tool for farmer collectives, not just economics, and it uses forecast ranges (an ensemble) rather than point forecasts. Our sentence that hold-or-sell work is "either economics or a single-farmer tool" is therefore wrong as written. This paper is a collective-level, ML-based, field-tested counterexample.
2. It targets cooperatives in India, which is the closest user context to ours.

What it does not do, and what KisanNiti still adds:
- Explicit storage loss, holding cost or interest in the decision.
- Allocation of sales across members, and fairness (leximin).
- An approval workflow, sensors, and WhatsApp delivery.
- Quantity decisions (how much to sell, not only when). Their decision is when to sell the whole lot.
- Their uncertainty is used through prospect theory's behavioural weighting, not through an economic net-benefit calculation.

Must gap 4 change? Yes. The "single-farmer tool" half needs to be softened, and this paper should be cited. Suggested wording: prior systems for farmer collectives (for example Ladhar et al. 2023) recommend only sale timing for a pooled lot from price forecasts. They do not model storage loss or holding cost, allocate across members, apply a fairness criterion, or include a manager approval step.

Caveat: this wording rests on this one paper plus our earlier review. It still needs a check against other collective-level work before we claim the gap is unfilled.
