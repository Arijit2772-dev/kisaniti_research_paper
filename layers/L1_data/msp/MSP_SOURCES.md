# MSP sources (tracker A.3)

Collected 2026-10-24. Every row in `msp_schedule.csv` was read from the opened PIB press release (Cabinet/CCEA decision); the "Posted On" date on that page is the announcement date. No row is UNVERIFIED.

- Paddy: Kharif Marketing Season (KMS). Wheat: Rabi Marketing Season (RMS), where "RMS 2021-22" is the crop sown in late 2020 and harvested in spring 2021 (announced Sep 2020).
- Wheat has a single MSP (grade `all`). Paddy Grade A is the "^" row in the PIB tables.
- Method: PIB pages returned HTTP 403 to WebFetch, so they were downloaded with curl and the table text parsed. The numbers were read from the page text, not recalled.
- Cross-check: DES "MSP Statement (as on 12.12.2025)", https://desagri.gov.in/wp-content/uploads/2025/12/MSP-Statement_English_As-on-12.12.2025.pdf (TLS certificate error in WebFetch; fetched with curl -k). It gives paddy common/Grade A KMS 2021-22..2025-26 = 1940/1960, 2040/2060, 2183/2203, 2300/2320, 2369/2389 and wheat RMS 2022-23..2026-27 = 2015, 2125, 2275, 2425, 2585. All match the PIB values. Later PIB releases also restate prior-year values (e.g. the 2026-27 Kharif release shows 2369/2389 as 2025-26).
- Not used: CACP site (not needed; PIB covers every season).

## Discrepancies
- None among PIB, DES and the repo's existing numbers. In the repo: `kisaniti/docs/research/2026-10-15_Patiala_Storage_Risk_and_Unknowns.md` and the L3d code use paddy 2369/2389 (KMS 2025-26) and wheat 2585 (RMS 2026-27); both match.
- Note: the repo's research note (15 Oct 2026) treats KMS 2025-26 as the current paddy price. KMS 2026-27 (2441 common / 2461 Grade A) was announced on 13 May 2026, so the repo figure is the previous season's value unless the demo deliberately pins 2025-26.
- No existing MSP_SCHEDULE table or schema exists in the repo (only references to the name), so the CSV follows the column list given in the task.
