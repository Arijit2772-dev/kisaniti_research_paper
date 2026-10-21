# L2 — Cleaning and validation (phase R3, EXP-02)

**Research question:** Which cleaning rules remove real errors without deleting genuine price spikes, and does cleaning change forecast accuracy?

**Build:**
- Deterministic rules: units, dates, min ≤ modal ≤ max, duplicates, variety mapping.
- A flag-only outlier screen.
- A cleaning report.
- Reuse and improve the capstone rules (`sem_6/capstone/reports/agmarknet_paddy_cleaning_rules.md`).

**Alternatives compared:**
1. No screening.
2. Rules only.
3. Rules + MAD flag.
4. Rules + Hampel filter.
5. Rules + IQR.

**Ground truth:** about 300–500 rows hand-checked against the AGMARKNET website, labelled error / genuine / unclear, with the checker and date recorded.

**Metrics:**
- precision and recall of the error flags;
- the change in L3a forecast MAE when each cleaned dataset is used.

**Outputs:**
- `results/cleaning_comparison.csv`;
- Table "cleaning rules and effect";
- Section 3.2 draft.

**Done when:** the chosen rule set is justified by the comparison, and the raw → clean counts reconcile exactly.
