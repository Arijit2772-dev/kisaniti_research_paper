# Literature review for KisanNiti (phase R1)

22 October 2026 • Drafted by Claude (R1 session) for the authors to check. Every study below was opened through its DOI or URL; how each claim was checked is in [verification_log.md](verification_log.md), and the BibTeX entries are in [references.bib](references.bib).

## 1. Method

### 1.1 Sources actually used

| Source | Used for | Note |
|---|---|---|
| OpenAlex API (`api.openalex.org/works?search=`) | Main search index. It covers Springer, Elsevier (ScienceDirect), IEEE, Wiley, MDPI, PLOS, Nature and Indian society journals | Results ranked by relevance; top 12 screened per query |
| Crossref API | Metadata check for every DOI (authors, title, journal, volume, issue, pages, year) | |
| Europe PMC full text | Full-text checks for open papers (Scientific Reports, PLOS ONE) | Data and code statements |
| Semantic Scholar API, arXiv API, DataCite API | Abstracts missing from Crossref; preprint and AgEcon DOIs | |
| Web search engine (standard and extended mode) | Finding exact titles, abstracts of blocked pages, official documents | Snippets were never used alone for a table entry except where marked PARTIAL in the log |
| Publisher and official sites, opened directly or in a browser | ICRIER, PIB, PMIndia, RBI, DES MSP PDFs, ras.org.in | |

**Deviation from the plan in [README.md](README.md):** Springer Link, ScienceDirect, IEEE Xplore and Google Scholar were not queried through their own search pages. OpenAlex indexes all of them, and ScienceDirect refused automated access (HTTP 403). An author should repeat two or three key searches in Google Scholar before submission and add anything important that is missing.

### 1.2 Search strings (all run on 22 Oct 2026)

OpenAlex free-text search; "filter" is the year filter used; "hits" is the total OpenAlex returned.

| # | Search string | Filter | Hits |
|---|---|---|---|
| Q1 | `AGMARKNET price forecasting` | none | 317 |
| Q2 | `agricultural commodity price forecasting India deep learning` | year > 2019 | 6,900 |
| Q3 | `wheat price forecasting India` | year > 2017 | 13,817 |
| Q4 | `graph neural network agricultural price forecasting` | year > 2019 | 11,197 |
| Q5 | `spatio-temporal graph agricultural market price` | year > 2019 | 2,347 |
| Q6 | `time series foundation model agricultural price` | year > 2022 | 74,345 |
| Q7 | `Chronos TimesFM zero-shot commodity price forecasting` | year > 2023 | 25 |
| Q8 | `minimum support price procurement Punjab paddy wheat farmers` | year > 2014 | 553 |
| Q9 | `minimum support price awareness impact farmers India` | none | 37,940 |
| Q10 | `storage arbitrage farmers sell low buy high` | none | 1,540 |
| Q11 | `farmers storage decision timing of grain sales credit constraints` | year > 2009 | 1,670 |
| Q12 | `post-harvest losses India wheat paddy storage farm level` | year > 2009 | 3,218 |
| Q13 | `storage losses food grains India farm` | none | 34,437 |
| Q14 | `IoT grain storage monitoring temperature humidity sensor` | year > 2018 | 5,231 |
| Q15 | `low-cost wireless sensor grain bin moisture temperature` | year > 2017 | 596 |
| Q16 | `price of fairness` | year = 2011 | 23,748 |
| Q17 | `leximin fair allocation optimization` | none | 301 |
| Q18 | `fair optimization and networks survey Ogryczak` | none | 199 |
| Q19 | `fair allocation agricultural cooperative farmers delivery quota` | year > 2009 | 1,640 |
| Q20 | `farmer producer organisation India marketing performance price realisation` | year > 2014 | 927 |
| Q21 | `farmer producer company collective marketing India` | year > 2014 | 11,620 |
| Q22 | `decision support system farmers market selection mandi` | year > 2014 | 655 |
| Q23 | `SMS agricultural information Indian farmers prices impact` | none | 2,606 |
| Q24 | `optimal market selection farmers transport cost mandi optimization` | year > 2014 | 120 |
| Q25 | `optimal grain marketing storage decision price forecast farmer sell or store model` | year > 2012 | 1,401 |
| Q26 | `WhatsApp agricultural advisory farmers India` | year > 2016 | 1,359 |
| Q27 | `human-in-the-loop decision support agriculture explainable recommendation farmers trust` | year > 2018 | 5,099 |
| Q28 | `price forecasting and optimization framework farmers selling decision integrated` | year > 2018 | 5,826 |
| Q29 | `harvest planning price prediction mixed integer programming farmers revenue` | year > 2018 | 175 |
| Q30 | `Chronos learning the language of time series` | none | 4,811 |
| Q31 | `electronic national agriculture market e-NAM price` | year > 2017 | 4,145 |

Web search (extended mode): `decision support system that combines crop price forecasting with optimal market and selling time recommendation for farmers, journal article` (found Tripathi et al. 2023). Exact-title searches were used to reach abstracts of two Elsevier papers whose pages were blocked. Parameter searches (storage loss, warehouse tariff, KCC interest) are listed in the log, §3.

The 25 references of paper v2 were also carried in and re-checked (log, §1).

### 1.3 Inclusion and exclusion

**Included** if all of these hold:

1. Peer-reviewed journal or conference paper, or a report from a government body or a major research institute. Two arXiv preprints on pretrained forecasting models are included and labelled as preprints, because this line of work is new.
2. On one of the eight R1 topics (price forecasting with Indian mandi data; graph or pretrained models for crop prices; MSP and procurement; hold-or-sell and storage timing; storage losses in India; grain-storage IoT; fair allocation; FPO and advisory systems).
3. The DOI or URL resolves and the metadata match the registry record.
4. The abstract or full text could be read, so that each table entry rests on what the paper says.

**Excluded:**

- abstract not readable anywhere (Avinash et al. 2024, Kantanantha et al. 2010);
- duplicates of the same work (SSRN, Figshare, Zenodo copies);
- system descriptions with no evaluation, mostly 2025–26 student "price advisory app" papers in journals without clear peer review;
- out-of-scope venues (for example an MSP awareness survey in a medical journal);
- non-agricultural papers, except method sources (T-GCN, A3T-GCN, HiGHS, SciPy) and the fairness papers, which have no agricultural counterpart.

**Flow (approximate):** about 370 titles screened (top 12 of 31 queries) → about 50 records opened → 38 studies in Table 1. Method and official sources (MSP lists, datasheets, scheme notices) are in the bib file but not in the table.

## 2. Table of studies

Legend: **Y** = reported; **–** = not reported in what we read; **n.r.** = the abstract does not say. "Read" says what we read: **A** = abstract, **F** = full text. "Code" records the paper's data/code statement where the full text was read.

| # | Study | Year | Region; crops | Data | Methods | Optimisation / fairness | IoT | Communication | Human approval | Evaluation | Code | Read |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Manogna et al. [manogna] | 2025 | India, 165 markets; 23 commodities | AGMARKNET daily, 2010–2024 | ARIMA, SVR, XGBoost, MLP, RNN, LSTM, GRU, ESN | – | – | – | – | RMSE, MAPE; LSTM/GRU best | data on request | F |
| 2 | Manogna & Mishra [manogna2021] | 2021 | India; 5 oilseed/guar commodities | NCDEX daily spot prices | ARIMA, TDNN, LSTM | – | – | – | – | out-of-sample error, direction; LSTM best | n.r. | A |
| 3 | Paul et al. [paul2022] | 2022 | Odisha, 17 markets; brinjal | AGMARKNET wholesale prices | GRNN, SVR, RF, GBM vs ARIMA | – | – | – | – | error metrics; GRNN best in most markets | data public; code not stated | F |
| 4 | Nayak et al. [nayak] | 2024 | India, major markets; tomato, onion, potato | prices + rainfall and temperature | NBEATSX, TransformerX vs ARIMAX, MLR, ANN, SVR, RF, XGBoost | – | – | – | – | RMSE, MAE, sMAPE, MASE, QL; DL with weather best | on request | F |
| 5 | Bhoi et al. [bhoi2023] | 2023 | Punjab, 74 APMC markets; basmati | monthly, 2000–2023 | TSLM, ARIMA, theta, NNETAR, STLF, TBATS | – | – | – | – | probability bands checked against AGMARKNET prices | n.r. | A |
| 6 | Balantrapu et al. [balantrapu2026] | 2026 | All-India; wheat, maize | AGMARKNET daily → 204 months, 2008–2025 | ridge, SVR, RF, ExtraTrees, GB, XGBoost, ARIMA, SARIMA, naive | – | – | – | – | 27-month hold-out; ridge best but naive close for MSP-anchored wheat | n.r. | A |
| 7 | Özden & Bulut [ozden] | 2024 | Turkey; vegetables | 1,791 days of prices and trade volume | StemGNN vs CNN, LSTM, RF | – | – | – | – | MAE, RMSE | n.r. | A |
| 8 | Min et al. [min] | 2025 | South Korea; potato, onion, lettuce, cucumber | daily Seoul wholesale prices + 6 weather variables | stacked LSTM, StemGNN, T-GCN; smoothing windows | – | – | – | – | GNN beat LSTM in multivariate setting | data public (KAMIS); code not stated | F |
| 9 | Özden [ozden2026] | 2026 | 109 countries; wheat PPI | FAO, weather, governance index, 2000–2023 | GNN + CNN + RF | – | – | – | – | random 80/20 split; R² 0.962 | n.r. | A |
| 10 | Ansari et al. [ansari2024chronos] (preprint) | 2024 | general | 42 benchmark datasets | pretrained T5-based probabilistic forecaster | – | – | – | – | zero-shot vs local and deep models | Y (GitHub) | A |
| 11 | Wang & Zhang [wang2026tsfm] (preprint) | 2026 | USA; major field crops | USDA ERS monthly, 1997–2025 | 17 methods incl. Chronos, TimesFM, Moirai, Time-MoE | – | – | – | – | vs USDA futures-based forecasts; TSFMs best | n.r. | A |
| 12 | Sun et al. [sun2023review] | 2023 | review | – | classical, ML, hybrid forecasting | – | – | – | – | review | – | A |
| 13 | Aditya et al. [aditya2017] | 2017 | India; MSP crops | NSSO 70th round | probit, Heckman | – | – | – | – | 23.7%/20.0% of farmers aware of MSP | – | A |
| 14 | Das [das2020] | 2020 | India; paddy, wheat | farm survey 2012–13 | access shares, odds by farm size and state | – | – | – | – | small farmers less likely to sell to agencies | – | A |
| 15 | Gupta et al. [gupta2021] | 2021 | India; paddy, wheat | multiple national sources | descriptive | – | – | – | – | MSP reaches 13% of paddy and 16% of wheat sellers | – | A |
| 16 | Burke et al. [burke2019] | 2019 | Kenya; maize | field experiment | timely harvest loans | – | – | – | – | RCT; 29% return; local price effects | n.r. | A |
| 17 | Kadjo et al. [kadjo2018] | 2018 | Benin; maize | panel, 309 households | econometric storage model | – | – | – | – | expected storage loss lowers storage for sale | n.r. | A |
| 18 | Cardell & Michelson [cardell2023] | 2023 | 30 African countries; maize | 20 years, 1,038 markets | seasonal returns, risk-aversion model | – | – | – | – | lean-season price not higher in 15–25% of years | n.r. | A |
| 19 | Tripathi et al. [tripathi2023] | 2023 | north India; tomato, onion, potato | market prices (source n.r.) | time-series + ML forecasts; sell-or-store rule with storage, rent, loss costs | sell/store decision (single producer) | – | n.r. | – | simulation on TOP markets | n.r. | A |
| 20 | Levi et al. [levi2020] | 2020 | Karnataka; paddy, groundnut, maize, others | UMP market data | difference-in-differences | – | – | – | – | paddy modal price +5.1% | n.r. | A |
| 21 | Basavaraja et al. [basavaraja2007] | 2007 | Karnataka; rice, wheat | survey 2003–04 (100 farmers per crop) | loss accounting, regression | – | – | – | – | farm loss 3.82 kg/q rice, 3.28 kg/q wheat; storage stage highest | – | A |
| 22 | Kumar & Kalita [kumar2017] | 2017 | developing countries; cereals | review | hermetic storage options | – | – | – | – | storage loss up to 50–60% traditional, 1–2% scientific | – | A |
| 23 | Gulati et al. [gulati2024report] | 2024 | MP, Punjab, Bihar; wheat, paddy, maize, soybean | ICRIER-ADMI field survey 2022 | inquiry + measurement of losses by stage | – | – | – | – | farm storage loss 0–0.96% by state and crop | – | F |
| 24 | Islam et al. [islam] | 2024 | Bangladesh; paddy | 125-day storage trial | hygrometer, Wi-Fi camera, remote controller | – | Y | remote viewing | – | T/RH logged; no insects or mould | n.r. | A |
| 25 | Anukiruthika & Jayas [anuk] | 2025 | review; grain storage | – | AI, ML, IoT, digital twins | – | Y (review) | – | – | review | – | A |
| 26 | Lydia et al. [lydia2022] | 2022 | India; warehouse grain | sensor prototype | PIC + GSM; T, RH, level, gas, smoke | threshold control | Y | SMS alerts, app | – | prototype | n.r. | A |
| 27 | Kodali et al. [kodali2020] | 2020 | India; warehouse food | sensor prototype | microcontroller, T, RH, quality sensors | – | Y | client app | – | prototype | n.r. | A |
| 28 | Hema et al. [hema2020] | 2020 | grain containers | sensor prototype | sensors, fan switching | threshold control | Y | n.r. | – | prototype | n.r. | A |
| 29 | Bertsimas et al. [bertsimas2011] | 2011 | general | – | proportional and max-min fairness | Y (price of fairness bounds) | – | – | – | theory | – | A |
| 30 | Ogryczak et al. [ogryczak2014] | 2014 | networks, location | – | lexicographic max-min methods | Y (survey) | – | – | – | survey | – | A |
| 31 | Kurokawa et al. [kurokawa2018] | 2018 | California; school classrooms | real district data | randomized leximin mechanism | Y (leximin) | – | – | – | proofs + real-data runs | n.r. | A |
| 32 | Chen & Hooker [chen2023fairness] | 2023 | general | – | MILP formulations of maximin, leximax, alpha-fairness | Y (guide) | – | – | – | survey | – | A |
| 33 | Urra-Calfuñir et al. [urra] | 2024 | Chile (Coquimbo); olive oil | past harvest seasons | MILP: harvest, plant assignment, transport, mobile mills | Y (profit) | – | – | – | case study | n.r. | A* |
| 34 | Gámez-Albán et al. [gamez] | 2024 | Greece; cooperative produce | case study | MILP vehicle routing (first mile) | Y (cost) | – | – | – | up to 40% lower logistics cost | n.r. | A |
| 35 | Anoop et al. [anoop] | 2025 | India; food grain by rail | historical data of the organisation | tri-objective model, MOSA vs NSGA-II | Y (with capacity/weekly-limit penalties) | – | – | – | 7 metrics | n.r. | A* |
| 36 | Neti et al. [neti2019] | 2019 | India; producer companies | MCA registry, 7,374 companies | descriptive | – | – | – | – | median paid-up capital ₹1.06 lakh | – | F |
| 37 | Fafchamps & Minten [fafchamps2012] | 2012 | Maharashtra, 100 villages | RCT | SMS price and weather service (RML) | – | – | Y (SMS) | – | no significant price effect | n.r. | A |
| 38 | Cole & Fernando [cole2021] | 2021 | Gujarat; cotton | two-year RCT | voice advisory service | – | – | Y (voice calls) | – | changed input use; no clear yield/profit gain | n.r. | A |

\* abstract read only through a search index; the publisher page was blocked (see log).

## 3. Feature comparison matrix

Representative studies against the features KisanNiti needs. KisanNiti is split into what v2 already built and tested and what v3 plans, so the paper never claims a planned part as done.

| Feature | Manogna 2025 | Bhoi 2023 | Balantrapu 2026 | Min 2025 | Tripathi 2023 | Islam 2024 | Lydia 2022 | Urra 2024 | Anoop 2025 | Kurokawa 2018 | Fafchamps 2012 | **KisanNiti v2 (done)** | **KisanNiti v3 (planned)** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Indian mandi price data | Y | Y | Y | – | n.r. | – | – | – | – | – | – | Y (paddy) | Y (paddy, basmati) |
| MSP baseline or MSP-anchoring check | – | – | Y | – | – | – | – | – | – | – | – | Y | Y |
| Forecast ranges, not only point values | – | Y | – | – | – | – | – | – | – | – | – | – | planned |
| Graph across markets | – | – | – | Y | – | – | – | – | – | – | – | Y | Y |
| Sell-or-hold with storage loss and cost | – | – | – | – | Y | – | – | – | – | – | – | – | planned |
| Storage sensing feeding the decision | – | – | – | – | – | monitoring only | alerts only | – | – | – | – | circuit simulated only | planned (ESP32 + SHT30) |
| Many farmers' lots under shared mandi capacity | – | – | – | – | – | – | – | Y (olive plants) | Y (rail rakes) | – | – | Y | Y |
| Explicit fairness criterion | – | – | – | – | – | – | – | – | – | Y (leximin, schools) | – | – | planned (leximin) |
| Human approval before advice is released | – | – | – | – | – | – | – | – | – | – | – | – | planned (FPO manager) |
| Advice delivered to farmers' phones | – | – | – | – | n.r. | – | SMS alerts | – | – | – | Y (SMS) | – | planned (WhatsApp) |
| Code public | – | n.r. | n.r. | – | n.r. | n.r. | n.r. | n.r. | n.r. | n.r. | n.r. | not yet | planned (archive) |

## 4. Gaps and novelty statement (derived from Tables 1–2)

What the 38 studies show, and what they leave open:

1. **Forecasting and allocation are studied apart.** Rows 1–12 cover price forecasting and three optimise agricultural logistics (rows 33–35). None of them feeds a price forecast into a plan that assigns many farmers' lots to markets and days under shared capacity.
2. **MSP is rarely the baseline.** Only Balantrapu et al. [balantrapu2026] define an MSP-anchored series and compare against naive persistence; they found persistence nearly as good as the best model for wheat. This agrees with our v2 paddy result, where the MSP rule had the lowest error. The other Indian forecasting studies do not report an MSP-based baseline.
3. **Few forecasts give ranges.** Bhoi et al. [bhoi2023] give probability bands for basmati; pretrained models such as Chronos [ansari2024chronos] are probabilistic, but the only agricultural test we found [wang2026tsfm] uses US data and is a preprint. We found no test of pretrained models on AGMARKNET prices.
4. **Hold-or-sell work is either economics or a single-farmer tool.** The economics papers [burke2019, kadjo2018, cardell2023] explain why farmers sell early (credit, expected loss, price risk) but give no tool. Tripathi et al. [tripathi2023] is the only decision tool that weighs storage, rent and physical loss, and it serves one producer, without sensor input.
5. **Storage IoT stops at monitoring.** Rows 24–28 log temperature and humidity or switch fans on thresholds. None connects storage readings to a selling decision.
6. **Fairness is absent from agricultural allocation.** The leximin and price-of-fairness papers (rows 29–32) come from networks, schools and general OR. None of the agricultural optimisation studies we read states a fairness criterion between farmers.
7. **No human approval step is reported**, and the field trials of phone-based advice [fafchamps2012, cole2021] found small or no price and profit effects. Claims about benefits to farmers therefore need direct evidence.
8. **Storage loss in North India is low in the first months.** Farm storage loss was 0.39–0.50% for wheat in Madhya Pradesh and 0% for paddy in Punjab in the 2022 ICRIER-ADMI survey [gulati2024report]; NABCONS reports 3.61% (wheat) and 4.16% (paddy) for all farm operations together [pib2025nabcons].

**Novelty statement (to be confirmed by the authors after their own Scholar check):** Among the 38 studies reviewed, none links mandi price forecasting with an MSP check, a sell-or-hold rule that uses storage condition, and a cooperative allocation that shares mandi capacity between an FPO's members under an explicit fairness criterion, with a manager approval step before farmers are messaged. KisanNiti v2 already combines the MSP check, a market graph and capacity-sharing allocation on real Punjab paddy prices. The remaining parts are v3 work and must be described as such until they are built and tested.

**Limits of this review.** One reviewer (Claude) screened the results; an author should repeat it. Most entries rest on abstracts. Search ranking came from OpenAlex, not from each publisher's own search. Per CHAT-32, basmati is the main market-priced crop for v3 and held wheat is a limitation; only one basmati forecasting study (Punjab, monthly) was found.

## 5. Values for the hold-or-sell advisory

Full sources and status in [verification_log.md](verification_log.md), §3.

| Parameter | Value found | Status |
|---|---|---|
| On-farm storage loss | total 0–0.5% in the first ~3 months (wheat MP 0.39–0.50%; Punjab paddy 0%) [gulati2024report]; older commercial storage ~1% over 4 months, 3–5% over 8 months (secondary) | per-month rate **not found** |
| Holding cost | ₹11–21 per quintal per year for on-farm bins/bags, Bihar 2013–14 (secondary, old) | current warehouse rate **not found**; ask the FPO / PSWC |
| Crop-loan rate | 7% p.a. (4% with prompt repayment), KCC loans up to ₹3 lakh, FY 2025-26 [pmindia2025miss]; same rate for up to 6 months after harvest against warehouse receipts for small and marginal farmers [rbi2022miss] | FY 2026-27 terms **not verified** |
