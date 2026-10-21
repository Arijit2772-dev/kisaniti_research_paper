# L3b — Storage risk and IoT (phase R5, EXP-06/13)

**Research question:** Can a low-cost probe inside the grain give a sensible, explainable storage-risk signal for held wheat and basmati?

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
