# Evidence behind the cleaning choices (B.1 – B.3)

24 October 2026 • Written to separate what is supported from what is only a design choice. The earlier `CLEANING_PLAN.md` named MAD, Hampel and IQR without citations; the literature review (R1) has nothing on cleaning methods. This note adds what was checked.

## 1. References checked (DOI resolved in Crossref on 24 Oct 2026; title, authors, venue and year match)

| Short name | Reference | DOI | Level of checking |
|---|---|---|---|
| leys2013 | Leys, Ley, Klein, Bernard, Licata (2013). Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median. *J. Exp. Soc. Psychol.* | 10.1016/j.jesp.2013.03.013 | Bibliographic record only; full text still to be read before citing a threshold |
| hampel1974 | Hampel (1974). The Influence Curve and its Role in Robust Estimation. *JASA* | 10.1080/01621459.1974.10482962 | Bibliographic record only |
| pearson2016 | Pearson, Neuvo, Astola, Gabbouj (2016). Generalized Hampel Filters. *EURASIP J. Adv. Signal Process.* | 10.1186/s13634-016-0383-6 | Bibliographic record only |
| rousseeuw1993 | Rousseeuw, Croux (1993). Alternatives to the Median Absolute Deviation. *JASA* | 10.1080/01621459.1993.10476408 | Bibliographic record only |
| chandola2009 | Chandola, Banerjee, Kumar (2009). Anomaly detection: a survey. *ACM Comput. Surv.* | 10.1145/1541880.1541882 | Bibliographic record only |
| jain2020 | Jain, Marvaniya, Godbole, Munigala (2020). A Framework for Crop Price Forecasting in Emerging Economies by Analyzing the Quality of Time-series Data. arXiv preprint | 10.48550/arXiv.2009.04171 | **Full text read** (arXiv PDF). Uses AGMARKNET (tomato, maize; Karnataka markets). Weekdays with no entry are treated as missing and filled by a spline; outliers found with the IQR method (threshold 1) and **not modified**; the authors attribute outliers to human entry errors; missing and outlier flags are added as model features. No check against the source website is reported |
| gonzalez2025 | Gonzalez Aguilera, Karbassi Yazdi (2025). Anomaly Detection and Regional Clustering in Chilean Wholesale Fruit and Vegetable Prices with Machine Learning. *Agriculture* 15(22) | 10.3390/agriculture15222362 | Abstract only (publisher blocked automated access): noise reduction with IQR, Z-score and Hampel filters on Chilean wholesale prices 2015–2023. Not AGMARKNET; whether anomalies were removed or flagged is not known to us |
| manogna2025 | Manogna, Dharmaji, Sarang (2025). Enhancing agricultural commodity price forecasting with deep learning. *Sci. Rep.* | 10.1038/s41598-025-05103-z | **Full text read** (open-access PDF). AGMARKNET daily, 2010–2024, 23 commodities. Preprocessing described is normalisation, sliding windows and an 80/20 split; **no outlier or missing-value handling is reported**, although the text calls the data clean |
| bhoi2023 | Bhoi, Vatta, Kumar, Arora, Adhale, Vani (2023). Probability Analysis for Forecasting Basmati Prices in Punjab. *J. Agric. Dev. Policy* | 10.63066/23220457.33.2.005 | Abstract only: monthly series from 74 APMCs, Jan 2000 – May 2023, from AGMARKNET; cleaning not stated |
| ladhar2023 | Ladhar, Sharma, Tangirala, Gupta, Azeem, Jain (2023). AI-based Market Intelligence Systems for Farmer Collectives: A Case Study from India. *ACM J. Comput. Sustain. Soc.* | 10.1145/3609262 | Abstract only (publisher 403): soybean cooperatives, price forecasting and a prospect-theory sell-or-wait recommendation, Android app field-tested. **Not in our literature review** (see §5)

These entries are not yet in `literature/references.bib`; add them (with the full text read) when the paper section is written (tracker H.5).

## 2. What each choice rests on

| Choice | Support | Verdict |
|---|---|---|
| Flag, never delete, candidates for outliers | Principle of the project (missing and odd values stay visible); chandola2009 treats anomalies as possibly meaningful | Design decision |
| Median-and-MAD based screens are a sensible family for prices | leys2013, hampel1974, pearson2016, rousseeuw1993 are about robust location and scale and the Hampel filter. **Their suitability for a daily mandi price series is not shown by any of them** | Engineering lean, to be **tested** on the hand-checked sample and by forecast effect (B.3), not assumed |
| Manual entry errors exist in AGMARKNET prices | jain2020 (full text): authors attribute outliers to human entry errors and report days with no update | Supported as the authors' statement; not independently measured |
| Flag outliers, keep the values, give the flag to the model | jain2020 does exactly this (IQR flag, values unmodified) | Precedent exists; supports our flag-only design |
| IQR, Z-score and Hampel together on wholesale prices | gonzalez2025 (abstract) | Precedent for trying all three; no evidence about which is better on AGMARKNET |
| Papers on AGMARKNET data usually report their cleaning | Of the two AGMARKNET papers read in full, jain2020 describes it, manogna2025 reports none | A reporting gap we can fill: our reconciliation (raw = kept + flagged + removed) is more explicit than either |
| Blank-date rows are real second-variety prices | **No literature.** Raw-file inspection only (see §3). To be confirmed or rejected by the website check (B.2) | Hypothesis |
| MAD vs Hampel vs IQR, thresholds | None specific to this data | UNKNOWN until B.3 gives evidence; do not hard-code |
| At least 3 mandis per day for the index | None; the power check (corr. 0.37 between mandis) shows pooling adds fewer independent samples | Engineering lean |

## 3. What the raw files show (script-checked, 24 Oct 2026; `parse_basmati.py`)

- 6,678 data rows = 6,098 dated + 580 blank-date, matching the 29 manifests for every file; 0 unexplained lines.
- Every blank-date row has a preceding dated row in the same market and file. In 578 of 580 the variety differs from the preceding row. The 2 exceptions (Bariwala 18 Nov 2025 1509 and Bareta 11 Sep 2026 1121) have a second row with the same variety, date and market but different prices: kept, flagged as duplicate keys, never averaged.
- In files from Dec 2025 onward, blank-date rows carry their own arrivals (8 rows), so arrivals are per variety there. In the older files they are empty.
- Problem flags (8 rows): 4 rows with the maximum price missing (one also lacks the minimum) and 4 duplicate-key rows (2 pairs). No price-order, non-positive-price, date-range or negative-arrival violation was found.
- Descriptive only: one 1121 modal price of ₹800 (Kot Ise Khan, 31 Oct 2021, 1 tonne; season median ₹3,400) and very large arrivals at Khanna APMC (about 16,000–18,000 t on many days of Nov 2025 – Jan 2026, against a median of 190 t over all rows; the largest single value is 19,000 t at Budalada, 8 Nov 2025). Khanna is a large market, so this is not judged an error, but one Khanna row is in the hand-check sheet to confirm the website shows the same figure. Price outlier screens must not be applied to arrivals without this check.

## 4. Consequence for the next steps

1. The hand check (`results/L2_cleaning/hand_check_sheet.csv`, instructions beside it) decides the blank-date rule.
2. Spline-filling of missing days (jain2020) conflicts with our rule that nothing filled is shown as observed; we compare, not adopt, in B.3.
3. Outlier screens are implemented only in B.3, as candidates, compared against the hand-checked sample and by forecast effect. Whichever is chosen is justified by that comparison, with the references above for the method only.
4. Anything cited from §1 beyond its bibliographic record needs the full text read first.

## 5. A problem this search found in the earlier literature review (not edited here)

`LITERATURE_REVIEW.md` gap 4 says hold-or-sell work is either economics or a single-farmer tool (Tripathi 2023). ladhar2023 describes a forecasting plus sell-or-wait recommendation system built with farmer cooperatives and field-tested, which is closer to KisanNiti than anything in the review's decision-tool group. Only its abstract has been read. Before the novelty statement is used in the paper, someone must read the full text (ACM, may need the college library) and either add it to the review or rewrite the gap. Cleaning practice was also never a column in the review's tables, which is why this note had to be written.

## 6. Amendment 28 Oct 2026: the 56-row inspection against the live portal (B.2), and a correction to this document

**What was done.** An AI agent (Codex) inspected all 56 sampled rows on the live AGMARKNET reports after the owner typed each CAPTCHA; a second agent (Claude) independently re-read the first 26 (HC01 to HC26) in the same way and found identical live values in all 26. The observations are in `results/L2_cleaning/hand_check_observations.csv` (generated by `layers/L2_cleaning/transfer_hand_check.py`, which recomputes every agreement and refuses to run if its counts differ from the ledger's). The owner signed off on 28 Oct 2026 (`results/L2_cleaning/hand_check_signoff.json`); the dataset is VALIDATED in the product database. The sample is purposive and stratified: its agreement rate is not an error rate.

**Results.** 56 of 56 modal prices agree. 33 rows agree on arrivals and all three prices; 20 rows differ in arrivals; 4 rows have a bound that the export holds as missing and the page shows as 0.00 (HC36 is in both groups); 23 rows have at least one of the two. All the other minimum and maximum prices agree.

**Corrections to what this document and the hand-check instructions implied.**
1. *Blank-date rows are visible beneath a dated row of the same market, but a merged date cell was not observed:* the inspected cells carry no `rowspan`. "Merged cell" is therefore not the explanation; the date carry-forward remains a traceable interpretation. The sheet column that says "merged cell" is filled NO where no rowspan was documented and UNKNOWN otherwise, never YES.
2. *Arrivals on the page are not the exported arrivals for rows that follow a dated anchor.* The page often shows the date total divided among the variety rows (for example 1,700 exported, 850 on the page), but not always: Bariwala on 18 Nov 2025 shows 250 and 2,720, which sum to the exported 2,970. No equal-division rule may be applied. Arrivals are not used by the index (it is a median of modal prices), and their exact export semantics are UNKNOWN.
3. *A zero maximum or minimum on the page is a representation of a missing bound*, not a price; missing stays missing.
4. HC55 is dated explicitly on the page but inferred in the export; the date value matches.

**C.0 section 2 rule, for the record.** Of the 22 rows in the sheet whose date was inferred, 21 are shown beneath the preceding date with the same prices (HC55 is the exception). The threshold of 19 is met, but the primary index is `dated_only` by the 27 Oct amendment regardless; `with_blank` remains a labelled sensitivity run.

**Still open.** B.2 is complete (inspection and owner sign-off). B.2b (an independent second source) is open: eNAM historical retrieval timed out and the press report cited offers regional ranges only.
