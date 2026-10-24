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
| jain2020 | Jain, Marvaniya, Godbole, Munigala (2020). A Framework for Crop Price Forecasting in Emerging Economies by Analyzing the Quality of Time-series Data. arXiv preprint | 10.48550/arXiv.2009.04171 | Abstract read: states that Indian market prices are entered by hand daily, with possible incorrect entries and days without data; uses data-quality features; tomato and maize, 14 markets; does not name AGMARKNET; cleaning steps not seen |

These entries are not yet in `literature/references.bib`; add them (with the full text read) when the paper section is written (tracker H.5).

## 2. What each choice rests on

| Choice | Support | Verdict |
|---|---|---|
| Flag, never delete, candidates for outliers | Principle of the project (missing and odd values stay visible); chandola2009 treats anomalies as possibly meaningful | Design decision |
| Median-and-MAD based screens are a sensible family for prices | leys2013, hampel1974, pearson2016, rousseeuw1993 are about robust location and scale and the Hampel filter. **Their suitability for a daily mandi price series is not shown by any of them** | Engineering lean, to be **tested** on the hand-checked sample and by forecast effect (B.3), not assumed |
| Manual entry errors exist in Indian market prices | jain2020 (abstract) | Weak support; no AGMARKNET-specific evidence found |
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
2. Outlier screens are implemented only in B.3, as candidates, compared against the hand-checked sample and by forecast effect. Whichever is chosen is justified by that comparison, with the references above for the method only.
3. Anything cited from §1 beyond its bibliographic record needs the full text read first.
