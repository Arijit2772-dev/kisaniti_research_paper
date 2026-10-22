# Reference verification log (R1)

Checked 22 Oct 2026 by Claude (R1 session). An author must re-check before submission.
Methods: Crossref API (metadata), OpenAlex/Semantic Scholar (abstracts), Europe PMC (open full text), publisher or official page opened directly (curl, WebFetch or the in-app browser), arXiv/DataCite API for preprints.

Verdicts: **OK** = DOI/URL opened, metadata match, claim found in the source. **FIX** = source is real but the v2 entry or claim needs a change. **PARTIAL** = claim checked only against an abstract shown by a search index (publisher page blocked).

## 1. The 25 v2 references

| Key | DOI / URL opened | Claim in v2 | Checked against | Verdict |
|---|---|---|---|---|
| sfac | sfacindia.com/fpofaq.aspx (200) | FPO = PO whose members are farmers; can pool, market, sell | FAQ text | OK |
| icrier | icrier.org/pdf/Policy_Brief_20.pdf (PDF, Apr 2024) | Rs 1.53 trillion loss/yr; NABCONS 2020–22; storage discussed | PDF text | **FIX**: second author is **Raya** Das (the `paper/references/v2_placeholder.bib` says "Ritika"); cite as Policy Brief 20, April 2024, PDF URL |
| manogna | 10.1038/s41598-025-05103-z | AGMARKNET daily 2010–2024, 23 commodities, 165 markets; LSTM/GRU best | Europe PMC full text | OK (data on request; no code) |
| msp1 | desagri PDF "as on 22.01.2025" | MSP by crop year | PDF | OK (Paddy Common 2300, Grade A 2320 for 2024-25) |
| msp2 | desagri PDF "as on 28.05.2025" | MSP by marketing season | PDF | OK |
| nayak | 10.1038/s41598-024-68040-3 | TOP crops, major markets, weather variables help DL | Europe PMC full text | OK (data/code on request) |
| ozden | 10.1590/0103-8478cr20220677 | StemGNN, 1,791 days, vs CNN/LSTM/RF | abstract | OK |
| min | 10.1038/s41598-025-97724-7 | GNNs beat stacked LSTM; smoothing helps multivariate more | Europe PMC full text | OK (4 crops: potato, onion, lettuce, cucumber; KAMIS data public; no code stated) |
| islam | 10.1016/j.atech.2024.100468 | 125 days, 16.7–29.2 °C inside, no insects/mould | abstract | OK |
| anuk | 10.1016/j.jspr.2025.102588 | AI/IoT review incl. smart sensors, anomaly detection | abstract | OK |
| zhao | 10.1109/TITS.2019.2935152 | GCN + GRU, traffic | abstract | OK (code on GitHub) |
| bai | 10.3390/ijgi10070485 | adds attention, traffic | abstract | OK |
| urra | 10.1016/j.cie.2024.110185 (Crossref OK; ScienceDirect 403) | MILP for harvest, processing, transport, small olive growers, Chile | indexed abstract (Coquimbo, mobile mills) | PARTIAL |
| gamez | 10.1016/j.iswa.2024.200426 | MILP first-mile transport, cooperative in Greece | abstract | OK |
| anoop | 10.1016/j.asoc.2025.112729 (Crossref OK; ScienceDirect 403) | "three-objective … inventory- and warehouse-related penalty factors" | indexed abstract: tri-objective rail freight, penalties on rakes, capacity utilisation, weekly limits; MOSA vs NSGA-II | **FIX/UNVERIFIED**: wording seems to come from the authors' 2022 paper (10.1016/j.rtbm.2021.100628, "…considering inventory and warehouse parameters"). Reword or cite that paper |
| shams | 10.1007/s00521-023-09391-2 | explainable crop recommendation | abstract | **FIX** (minor): add issue 11 |
| agmarknet | agmarknet.gov.in (200, "Agmarknet 2.0") | data portal | site | OK |
| osm | nominatim.openstreetmap.org (demo page) | geocoding | site | OK |
| cgc | canada.ca news release 13 Sep 2017 | check probes regularly; hot spots may mean insects | page ("every two weeks") | OK |
| esp32 | Espressif datasheet v5.3 | 2.4 GHz, 802.11 b/g/n | PDF | OK |
| dht22 | SparkFun-hosted Aosong datasheet | ±2% RH (max ±5%), <±0.5 °C | PDF | OK, but hardware retired (CHAT-29) |
| ds18b20 | SparkFun-hosted PDF | ±0.5 °C −10…+85 °C; 4.7 kΩ pull-up | PDF | **FIX**: PDF is a *Dallas Semiconductor preliminary* datasheet, not Maxim Integrated; hardware retired (CHAT-29) |
| wokwi | wokwi.com (200) | ESP32 simulator | site | OK |
| highs | 10.1007/s12532-017-0130-5 | HiGHS solver citation | Crossref (online 2017, vol 10(1) 2018) | OK |
| scipy | 10.1038/s41592-019-0686-2 | SciPy 1.0 | Crossref | OK |

No v2 reference is fake. Flagged: **anoop** (claim does not match), **icrier** (author first name in placeholder bib), **ds18b20** (wrong publisher), **shams** (missing issue), **urra** (only partially checkable). dht22/ds18b20 are not needed in v3.

Data note for authors: the AGMARKNET commodity is "Paddy (Common)" but the plan says prices equal the **Grade-A** MSP; say which MSP explicitly in v3.

## 2. New references (all in `references.bib`)

All DOIs below resolved at Crossref (or arXiv/DataCite) and metadata were copied from the registry record; claims checked against the abstract (A) or full text (F).

| Key | Read | Key facts used |
|---|---|---|
| manogna2021 | A | NCDEX spot prices, 5 oilseed/guar commodities; LSTM best vs ARIMA/TDNN |
| paul2022 | F | brinjal, 17 Odisha markets, AGMARKNET data public; GRNN best vs ARIMA |
| bhoi2023 | A | basmati, 74 Punjab APMC markets, monthly 2000–2023; TBATS, probability ranges |
| balantrapu2026 | A | AGMARKNET wheat/maize monthly 2008–2025; ridge best, but naive persistence about as good for MSP-anchored wheat |
| ozden2026 | A | GNN+CNN+RF, wheat producer price index, 109 countries, random 80/20 split |
| ansari2024chronos | A (arXiv API) | pretrained probabilistic forecaster, zero-shot; code public |
| wang2026tsfm | A (arXiv API) | USDA monthly prices; zero-shot TSFMs beat classical/DL; preprint |
| sun2023review | A | review of price forecasting methods |
| aditya2017 | A | NSSO 70th round: 23.7% (kharif) / 20.0% (rabi) of farmers aware of MSP |
| das2020 | A | access to MSP for paddy/wheat by farm size and state, 2012–13 survey |
| gupta2021 | A | MSP affects 13% of paddy and 16% of wheat sellers |
| burke2019 | A | Kenya: timely credit lets farmers store and sell later; 29% ROI |
| kadjo2018 | A | Benin: expected storage loss reduces storage for later sale |
| cardell2023 | A | lean-season price fails to exceed harvest price 15–25% of years |
| tripathi2023 | A | sell-or-store ADSS with storage, rental and physical-loss cost; TOP crops, north India; single producer |
| levi2020 | A | Karnataka UMP raised paddy modal prices 5.1% |
| basavaraja2007 | A | Karnataka farm-level loss 3.28 kg/q wheat, 3.82 kg/q rice; storage stage highest |
| kumar2017 | A | storage losses up to 50–60% traditional, 1–2% scientific |
| gulati2024report | F | ICRIER-ADMI 2022 field survey tables (see §3) |
| pib2025nabcons | F (browser) | NABCONS farm-operation loss: paddy 4.16%, wheat 3.61% |
| lydia2022 | A | PIC + GSM warehouse monitoring, SMS alerts, thresholds |
| kodali2020 | A | microcontroller + T/RH/quality sensors for warehouses |
| hema2020 | A | in-container sensors, fans switched on thresholds |
| bertsimas2011 | A | price of fairness (proportional, max-min) |
| ogryczak2014 | A | survey of lexicographic max-min (fair) optimisation |
| kurokawa2018 | A | leximin mechanism deployed for classroom allocation |
| chen2023fairness | A (Semantic Scholar) | how to write maximin/leximax etc. in MILP |
| neti2019 | F (ras.org.in) | 7,374 producer companies 2003–2019; median paid-up capital Rs 106,000 |
| fafchamps2012 | A | RML SMS in 100 Maharashtra villages: no significant price effect |
| cole2021 | A | voice advisory in Gujarat changed input use, no clear yield/profit gain |
| pmindia2025miss, rbi2022miss | F | see §3 |

Dropped because the abstract could not be read: Avinash et al. 2024 (10.1016/j.asoc.2024.111557), Kantanantha et al. 2010 (10.1007/s13253-010-0025-7). Gibson et al. 2020 and WRI 2021 were opened but not used.

## 3. Hold-or-sell parameters (sourced values)

| Parameter | Sourced value | Source | Status |
|---|---|---|---|
| On-farm storage loss | Wheat, Madhya Pradesh farms: **0.39%** (farmer inquiry, n=200) and **0.50%** (measured, n=40) of production lost in farm storage. Punjab paddy farms: **0.00%** (farmers sell soon after harvest); market-level storage 0.15–0.21%. Re-visits about 1 and 3 months later found no significant rise; the authors say losses "kick in after the third month" | gulati2024report, Tables 4.1, 4.2, 4.6 and p. 50 (ICRIER-ADMI survey 2022) | Found (total, not per month) |
| | Older commercial storage: ~1% over 4 months, 3–5% over 8 months (Krishnamurthy 1975, cited in gulati2024report p. 21) → roughly 0.25–0.6% per month | secondary | Found, secondary and old |
| | Punjab wheat: storage-stage losses negligible (Grover 2013, cited in gulati2024report) | secondary | Found, secondary |
| | **Per-month on-farm loss rate for North India wheat/paddy** | — | **NOT FOUND** as a direct figure. DEMO ℓ(LOW)=0.5%/30 days is at or above every observed value for the first 3 months |
| Holding cost | On-farm structures, Bihar 2013–14: Rs 21/q/year (gunny bags), Rs 11/q/year (metal bin) (Kumar et al. 2020, cited in gulati2024report p. 22) | secondary | Found, old and secondary |
| | Current warehouse tariff (CWC/PSWC, Rs/q/month) | CWC tariff page loaded empty; CAG Report 20/2023 link returns 404 | **NOT FOUND**. Ask the FPO / PSWC |
| Crop-loan rate | **7%** p.a. on KCC short-term loans up to Rs 3 lakh; lenders get 1.5% subvention; prompt repayment incentive up to 3% → **4%** effective. FY 2025-26 | pmindia2025miss (28 May 2025) | Found |
| | Small and marginal farmers can get the same rate for up to **6 months after harvest** against negotiable warehouse receipts in WDRA-accredited warehouses | rbi2022miss (RBI/2022-23/35, FY 2021-22) | Found (2021-22 circular; later years seen only in search snippets) |
| | FY 2026-27 continuation; Budget 2025-26 limit rise to Rs 5 lakh | news only, not opened | **NOT VERIFIED** |
