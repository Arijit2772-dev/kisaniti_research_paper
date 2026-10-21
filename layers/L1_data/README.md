# L1 — Data (phase R2, EXP-01)

**Research question:** What real mandi price data exists for our three crop paths in Punjab and Patiala, and how complete is it?

**Crops:**
- Paddy (Common): MSP path; data already available.
- Wheat: MSP window plus held wheat.
- Basmati paddy: by variety, e.g. 1121, 1509, 1718, 1885 (decision CHAT-20).

**Build:** loaders that read raw files into one normalised table (source IDs, mandi, commodity, variety, date, min/modal/max ₹/q, arrivals), plus a coverage report script.

**Sources compared:**

| Source | Status | Use |
|---|---|---|
| AGMARKNET API used in the capstone (`api.agmarknet.gov.in`) | Now needs a CAPTCHA, so scripts cannot download | Existing paddy files only |
| AGMARKNET website reports, downloaded **by the user** in a browser | User-driven; CAPTCHA solved by the user | Wheat and basmati, Punjab, 2016–2026 |
| CEDA Agmarknet (Ashoka University) | Needs access; history from 2000 | Long history, cross-check |
| data.gov.in variety-wise resource | API key and request needed | Recent days |
| Third-party aggregators | Not used as sources | — |

**User download steps** (agmarknet.gov.in → price/arrival reports):
1. State Punjab; commodity Wheat; then Paddy (Basmati) or the listed basmati varieties.
2. Date range year by year, 2016–2026; all markets.
3. Export to Excel/CSV and save unchanged in `data/raw/agmarknet/<crop>/<year>.xlsx`.

Never edit raw files. Record the download date in the manifest.

**Metrics (EXP-01):**
- days with a modal price per mandi and season;
- longest gap;
- variety-name variants;
- duplicates and revisions;
- arrivals availability;
- the share of prices equal to MSP (wheat; repeating the paddy check).

**Outputs:**
- `results/coverage.csv`;
- the Fig. "data coverage heat-map";
- Table "dataset summary";
- the paper Section 3.1 draft;
- manifests in `data/manifests/`.

**Done when:** every series has a manifest, the coverage table is produced by script, and the list of forecastable series is fixed with the rule written down.

Planning reference: [Layer 1 design](../../../kisaniti/docs/handoff/2026-10-14/KisanNiti_Layers_1_to_3_Handoff.md), [Patiala research](../../../kisaniti/docs/research/2026-10-15_Patiala_Storage_Risk_and_Unknowns.md).
