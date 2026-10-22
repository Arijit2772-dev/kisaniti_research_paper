# L3b — Storage risk and IoT (phase R5, EXP-06/13)

**Research question:** Can a low-cost probe inside the grain give a sensible, explainable storage-risk signal for stored basmati (CHAT-32; held wheat is now a limitation only)?

**Build** (with [hardware](../../hardware/README.md)):
1. Wokwi ESP32 node publishes readings over MQTT.
2. A Python ingestion service checks each reading (de-duplication, timestamps).
3. The storage rule **STORAGE-DEMO-0.1** turns readings into a category:
   - water activity aw = RH/100, using a 24 h median;
   - LOW below 0.65, MEDIUM 0.65–0.70, HIGH 0.70 and above;
   - temperature adjustments and hysteresis.
4. The category feeds the planner.

**Alternatives compared:**
1. STORAGE-DEMO-0.1.
2. Ambient-RH-only threshold.
3. Temperature-only rule.
4. Moisture-% via isotherm equations, only if verified constants are found.

**Scenarios (simulated sensor streams):**
- Patiala dry season (Apr–Jun);
- monsoon (Jul–Sep);
- a freshly harvested wet lot;
- a sensor outage;
- noise of ±2% RH and ±0.3 °C;
- the probe in open air instead of in the grain.

**Metrics:**
- category per scenario;
- category flips per week (stability);
- sensitivity to sensor error;
- the share of time UNKNOWN during outages;
- for real hardware later: calibration offset and data loss.

**Outputs:**
- Fig. "sensor stream → category" for each scenario;
- Table "rule comparison";
- Sections 3.4 and 4.2.

**Done when:** the rule is implemented with tests; the scenarios run from a script; its limits are written plainly (it does not detect actual spoilage).

Spec: [Patiala research Part B](../../../kisaniti/docs/research/2026-10-15_Patiala_Storage_Risk_and_Unknowns.md).

## Results (EXP L3b-1, 22 Oct 2026 — simulated data only)

**Run:** `PYTHONPATH=../kisaniti_implementation/core/src .venv/bin/python layers/L3b_storage_iot/run_experiment.py`, then
`.venv/bin/python layers/L3b_storage_iot/make_figures.py`. About 2 minutes. Outputs in `results/L3b_storage/`
(`runs.csv` per run, `summary.csv`, `traces_seed0.json`, `settings.json`, `environment.txt`); figure
`paper/figures/fig_storage_scenarios.*`; table `paper/tables/table_storage_rules.tex`; numbers via `paper/numbers.py`
(keys `stor_*`).

**Design:** six basmati scenarios on a Patiala farm (`scenarios.py`; S1 stored dry, held Nov–Feb; S2 monsoon hold;
S3 fresh, sun-dried on day 8; S4 monsoon hold with outages; S5 probe in shed air; S6 grain near a_w 0.65). Climate
from IMD *Climatological Tables 1991–2020*, Patiala (42101), p. 300: monthly mean daily max/min temperature and RH at
08:30 and 17:30 IST; shed RH is a daily cycle fitted through both RH observations (shed air assumed equal to outdoor
air). 5-minute samples, hourly assessments; 20 noise seeds; sensor bias 0 and ±2 %RH / ±0.3 °C (SHT30 typical
tolerance in the 20–80 %RH mid range). Rules: STORAGE-DEMO-0.1 from `kisaniti_core.storage` (the product code,
unchanged), an instantaneous ablation (no median/hysteresis), shed-air RH only, temperature only. Each is scored
against the *intended* category (the same FAO-based bands applied to the noise-free in-grain values), which tests
robustness, not biological validity.

**Re-run note (22 Oct, same day):** the first run drove the scenarios with the 17:30 RH only, taken as the daily mean
(read from a secondary table). Using IMD's own table with both observation times makes the shed air 10–20 points more
humid, so stored grain drifts wetter (S1 reaches a_w 0.79 by February). All numbers below and in the paper are from the
re-run.

**What we saw (no bias; values via `paper/numbers.py`, keys `stor_*`):**
- STORAGE-DEMO-0.1 agreed with the intended category on 88–100 % of known hours in S1–S4 and changed category at most
  0.7 times per week. The latest-reading ablation agreed about as often (92–99 %) but changed 1.4–19 times per week,
  most when the grain sat near a limit.
- Shed-air RH was a poor stand-in for the grain: 19–61 % agreement and 14–27 changes per week, following the daily
  humidity cycle. Temperature only marked the whole monsoon hold HIGH and never HIGH in the humid winter (13 %
  agreement in S1).
- With the probe in shed air, STORAGE-DEMO-0.1 returned UNKNOWN for every hour, by design.
- Costs: HIGH reported ~12 h after the intended category (24 h median); the fresh wet lot flagged 23 h late (first
  day UNKNOWN) and kept HIGH ~2 days after drying (9 % false-HIGH hours); outages gave 7 % UNKNOWN (144 samples lost:
  72 to buffer overflow, 72 to the power cut); near a_w 0.65 hysteresis holds MEDIUM (49 % agreement, 0 changes, vs
  92 % and 19 changes/week for the ablation).

**Sensor bias matters as much as the rule:** +2 %RH cut agreement in S1–S4 to 66–96 % (up to 29 % false-HIGH hours),
−2 %RH to 60–85 % (up to 15 % missed-HIGH hours); the ablation was hit the same way, so the median does not protect
against bias. The salt calibration in `../kisaniti_implementation/firmware/BUILD_GUIDE.md` is therefore required
before real readings are interpreted.

**Limits:** every stream is simulated (shed = outdoor air, grain moisture exchange and temperature damping are
assumptions listed in `scenarios.py`); no rule here detects spoilage. Real-node results (calibration offset, settling
time, data loss) belong to Paper 2 or to Sections 3.4/4.2 once measured.

## References checked (22 Oct 2026, for Sections 3.4 / 4.2)

Entries merged into `literature/references.bib` by the literature phase (commit 549b093, re-checked there):

| Key | Opened | Claim it supports |
|---|---|---|
| `greenspan1977` | DOI 10.6028/jres.081A.011 resolves to the NBS PDF; Table 2, NaCl column | 75.47 ± 0.14 / 75.29 ± 0.12 / 75.09 ± 0.11 %RH at 20 / 25 / 30 °C (salt check) |
| `gwinner1996` | fao.org/4/x5065e, ch. 6 "Fungi and mycotoxins"; title page: GTZ Post-Harvest Project, 2nd ed. 1996 | storage fungi need RH ≥ 65 %, grow at about 10–40 °C |
| `delucia1994` | fao.org/4/t0522e; FAO Agricultural Services Bulletin 93, © FAO 1994, ISBN 92-5-103108-8 | below 65–70 % equilibrium RH many degradation processes slow down; safe moisture paddy 14 %, wheat 13 % (hot regions) |
| `sht3x` | Sensirion SHT3x-DIS datasheet, Version 7, December 2022 (PDF read locally) | SHT30 typical ±2 %RH at 20–80 %RH (±3–4 near 0–10 and 90–100 %RH, Fig. 2 table) and ±0.2 °C at 0–65 °C; command 0x2400; CRC-8 0x31/0xFF; conversion formulas |

| `imd2022` (sent to the literature phase to add) | IMD, *Climatological Tables of Observatories in India 1991–2020*, 9th ed. (2022), PDF from imdpune.gov.in; title page, legend p. 216 (I = 0830 IST, II = 1730 IST), Patiala table p. 300 | monthly temperature and RH normals used in `scenarios.py` |
