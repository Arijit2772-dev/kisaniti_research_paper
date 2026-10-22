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

**Design:** six basmati scenarios on a Patiala farm built from IMD 1991–2020 normals (`scenarios.py`; S1 dry Nov–Feb,
S2 monsoon hold, S3 fresh then sun-dried, S4 outages, S5 probe in shed air, S6 grain near a_w 0.65); 5-minute
samples, hourly assessments; 20 noise seeds; sensor bias 0 and ±2 %RH / ±0.3 °C (SHT30 typical tolerance).
Rules: STORAGE-DEMO-0.1 from `kisaniti_core.storage` (the product code, unchanged), an instantaneous ablation (no
median/hysteresis), shed-air RH only, temperature only. Each is scored against the *intended* category (the same
FAO-based bands applied to the noise-free in-grain values), which tests robustness, not biological validity.

**What we saw (no bias):**
- STORAGE-DEMO-0.1 changed category at most 0.2 times per week. The instantaneous version changed up to 19 times per
  week and the shed-air rule 20–28 times per week, mostly from the daily humidity swing.
- Shed-air RH agreed with the in-grain condition on only 11–60% of hours; in the dry winter scenario it called 41% of
  hours HIGH while the grain stayed below a_w 0.66. Temperature only marked the whole monsoon hold HIGH (it reacts to
  insects' temperature range, not to moisture).
- With the probe in shed air, STORAGE-DEMO-0.1 returned UNKNOWN for every hour, by design (placement check).
- Costs: the first ~24 h after insertion are UNKNOWN (6 h settling + 75% coverage), so the wet fresh lot (S3) was
  flagged HIGH 23 h after the intended category; the 24 h median delayed HIGH by about 12 h in S2. After the outages in
  S4 the rule was UNKNOWN 7% of the time (144 samples lost: 72 to buffer overflow, 72 to the power cut).
- Near the 0.65 limit (S6) hysteresis held MEDIUM: 0 changes but only 49% agreement, against 92% agreement with 19
  changes per week for the instantaneous rule. The rule leans to the cautious side.

**Sensor bias matters as much as the rule:** a +2 %RH bias kept STORAGE-DEMO-0.1 at MEDIUM for weeks after the S3
lot was dried (agreement 25%), because the 2-point de-escalation margin equals the sensor tolerance. A −2 %RH bias
missed 21% of the HIGH hours in S2 (the instantaneous rule missed the same share). The salt calibration in
`../kisaniti_implementation/firmware/BUILD_GUIDE.md` is therefore required before real readings are interpreted.

**Limits:** every stream is simulated (grain moisture exchange and temperature damping are assumptions listed in
`scenarios.py`); the IMD figures come from a secondary table; no rule here detects spoilage. Real-node results
(calibration offset, settling time, data loss) belong to Paper 2 or to Sections 3.4/4.2 once measured.
