# B.2b Independent spot check: candidate second sources for AGMARKNET Paddy(Basmati), Punjab

Prepared 2026-10-24. No registration, login, or CAPTCHA was attempted. No prices below come from outside our file; every price quoted is from basmati_tidy.csv.

## 1. Source inventory

| Source | URL | Access date | Works now? | Login/CAPTCHA | Coverage | Independent of AGMARKNET? |
|---|---|---|---|---|---|---|
| eNAM | https://enam.gov.in/web/dashboard/trade-data | 2026-10-24 | curl: HTTP 403 (bot block). Built-in browser: shell loads (Login/Registration links), but no data rendered in the page text. Not confirmed usable. | Probably an interactive form; not tested (would need user to click). No CAPTCHA seen on landing. | eNAM-integrated Punjab mandis only, a subset of APMCs; commodity/variety filters by date. Unverified. | Partly. Trade prices are recorded on eNAM, but eNAM mandis also report to AGMARKNET, so overlap is likely and not a clean independent measurement. Unverified. |
| Punjab Mandi Board (pmb.punjab.gov.in, amis.pmb.punjab.gov.in, mandiboard.nic.in, punjabmandiboard.gov.in) | as listed | 2026-10-24 | No. All hosts: DNS "could not resolve host". Web search did not surface a working official price portal. | n/a | n/a | Would be the best independent source if a live URL exists (the Board's market committees are the origin of AGMARKNET entries, though). Real URL unknown: UNKNOWN. |
| data.gov.in AGMARKNET dataset ("Current daily price of various commodities from various markets (Mandi)") | https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi (API: api.data.gov.in, needs API key) | 2026-10-24 | Page returns HTTP 200; API needs a key (registration, not done). | API key = registration | Same records as AGMARKNET. | NO. Same underlying data. Useful only for checking our parsing/ingestion, not for validating prices. |
| AGMARKNET itself | https://agmarknet.gov.in | 2026-10-24 | HTTP 200 | Not tested | Our own source. | NO (it is the thing being checked). |
| NaPanta (aggregator) | https://www.napanta.com/hi/market-price/punjab/mansa/bareta (also /punjab/amritsar/attari, /punjab/nawanshahr/nawanshahar) | 2026-10-24 | HTTP 200 | None | Per-mandi pages: min/modal/max per variety with "last updated" date. Fetched page showed only one date for 1121 (23 Oct 2026) and said history older than 7 days is in its app. Not usable for a month-old date. | NO in substance. Credits "APMC daily market reports"; same APMC feed as AGMARKNET. Re-publication. |
| Tribune (Amritsar/Punjab desk) | https://www.tribuneindia.com (HTTP 200) | 2026-10-24 | Yes | Possible paywall/none seen | Narrative reports with price ranges, often by district or mandi, rarely a specific day per mandi. Found items were undated in search or from other years. | Yes: reporter or district officer quotes, trade sources. Coarse (range, not modal). |
| Hindu BusinessLine | https://www.thehindubusinessline.com (HTTP 200) | 2026-10-24 | Yes | Metered paywall possible | Basmati market commentary; usually Karnal/Delhi/Haryana, not named Punjab mandis. | Yes (trade quotes), poor market match. |
| commodity-board.com | https://commodity-board.com/heavy-new-crop-paddy-arrivals-weigh-on-basmati-rice-prices | 2026-10-24 | Search hit only; page not fetched | None known | Trade commentary on Punjab/Haryana 1509 paddy, price moves of INR/qtl over days. Source of its numbers unverified. | Unclear. Treat as weak corroboration only. |
| APEDA | https://apeda.gov.in | 2026-10-24 | HTTP 200 (root); /apedawebsite/ 404 | None | Export statistics and FOB basmati rice, not mandi paddy prices. | Independent but a different quantity (export rice). Not suitable for cell-level check. |
| NCDEX spot | https://www.ncdex.com/market-watch/spot-prices | 2026-10-24 | HTTP 200 | None seen | Not verified to carry basmati paddy in Punjab. | UNKNOWN; not confirmed relevant. |
| commodityonline.com | https://commodityonline.com | 2026-10-24 | HTTP 403 | n/a | Aggregates AGMARKNET data. | NO (republication). |

## 2. Assessment

No clean, no-registration, fully independent daily source for named Punjab mandis was found. Honest summary:
- Truly independent but coarse: newspaper reports (Tribune) giving ranges.
- Possibly near-independent at cell level: eNAM trade data, only for eNAM mandis, and only if the portal can be viewed without login (must be tried by the user in a normal browser; it blocked curl and rendered no data in the built-in browser).
- Re-publications (do not count as independent): data.gov.in, NaPanta, commodityonline.
- The Punjab Mandi Board portal could not be located (DNS failures); its URL is UNKNOWN.

## 3. Recommendation

1. eNAM trade-data (user performs manual lookup in an ordinary browser, view-only; stop if it asks for login or CAPTCHA). Cells in section 4 limited to mandis that appear in eNAM.
2. Tribune / trade press range check for October 2025: search tribuneindia.com for "basmati" "1509" "1121" with Amritsar/Fazilka/Muktsar/Malout/Sangrur datelines, 1 to 31 Oct 2025. Pass criterion is that our min-max or modal falls inside the quoted range, and ratio is within a stated tolerance. This gives a plausibility check, not exact agreement.

Report agreement as: exact match count (eNAM), within-tolerance count, outside count, not-findable count. Say plainly in the paper that the check is coarse and that the sources are partly overlapping.

## 4. Protocol

Month: October 2025 (442 rows, 31 days, densest recent month with full coverage; 2025-10-01 to 2025-10-31).

Exclusion rule: rows with modal 2389 to 2391 (Kot ise Khan, Samana(Gajewas), Shahkot, Dinanagar 1121 on 21 Oct, etc.) look like MSP-like constants, not market prices. They are not in the sample, but flag them separately as a data-quality observation to examine in the cleaning layer (not verified as errors).

Cells (market, date, variety; our values min / max / modal, INR per quintal, from basmati_tidy.csv):

| # | Market | Date | Variety | min | max | modal |
|---|---|---|---|---|---|---|
| 1 | Jalalabad APMC | 2025-10-15 | 1121 | 2800 | 3025 | 2900 |
| 2 | Jalalabad APMC | 2025-10-21 | 1121 | 2850 | 3461 | 3175 |
| 3 | Samana APMC | 2025-10-16 | 1121 | 3000 | 3400 | 3280 |
| 4 | Muktsar APMC | 2025-10-16 | 1121 | 3280 | 3425 | 3350 |
| 5 | Muktsar APMC | 2025-10-20 | 1121 | 2850 | 3215 | 3050 |
| 6 | Bareta APMC | 2025-10-21 | 1121 | 2700 | 3370 | 3180 |
| 7 | Dirba APMC | 2025-10-16 | 1121 | 2610 | 3405 | 3110 |
| 8 | Talwandi Bhai APMC | 2025-10-21 | 1121 | 2900 | 3070 | 3000 |
| 9 | Malout APMC | 2025-10-20 | Basmati 1509 | 3150 | 3295 | 3160 |
| 10 | Abohar APMC | 2025-10-16 | Basmati 1509 | 2800 | 3185 | 3051 |
| 11 | Dhuri APMC | 2025-10-16 | Basmati 1509 | 2850 | 3120 | 3080 |
| 12 | Patran APMC | 2025-10-21 | Basmati 1509 | 2850 | 3425 | 3200 |
| 13 | Tarantaran APMC | 2025-10-16 | Basmati 1509 | 2705 | 3390 | 3100 |
| 14 | Mansa APMC | 2025-10-15 | Basmati 1509 | 2200 | 3100 | 2750 |
| 15 | Kotkapura APMC | 2025-10-16 | Basmati 1509 | 2900 | 3345 | 3200 |

Notes:
- Cells 1-8 are 1121, 9-15 are 1509; markets repeat across dates so a mandi-level lookup in eNAM or press covers two cells at once (Jalalabad, Muktsar).
- Cell 14 (Mansa) has an unusually wide min-max; check it with a critical eye.
- Which of these markets are on eNAM Punjab is NOT verified; the user should substitute the nearest eNAM-listed mandi/date with the same variety from the file, taking the substitute row from the CSV, never from the second source.
- Record for each cell: source URL, access date, quoted figure (min/max/modal as the source labels them), variety label as the source gives it, and any unit differences (INR/qtl vs INR/tonne; paddy not rice). If a cell is not findable, record "not findable", do not impute.
- Pre-register the tolerance before looking (suggest: modal within 5% of source modal or inside quoted range).
