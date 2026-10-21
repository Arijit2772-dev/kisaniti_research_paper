# Integration — end-to-end run (phase R9, EXP-10 lite)

**Research question:** Does the whole chain work on real price data, and does KisanNiti beat simple practice over past seasons?

**End-to-end demo** (fixed clock, DEMO label):
1. Wokwi sensor reading.
2. Storage category.
3. Price data for the date.
4. Forecast with ranges.
5. Hold-or-sell advice.
6. Plan for the 300-member persona.
7. Manager approval and reservation.
8. WhatsApp message to the test phone.
9. Recorded sale from a J-form.
10. Stock update.
11. Next plan.

**Whole-system backtest:** replay past seasons day by day, using only data available at each date. Compare KisanNiti with:
- nearest mandi at harvest;
- the MSP-only path;
- the best single-mandi rule.

Report results per season and scenario: normal, spike, glut, monsoon storage stress, data outage, sensor offline.

**Outputs:**
- Fig. "end-to-end flow with real screenshots";
- Table "system vs baselines";
- Section 4.6;
- the limitations list.

**Done when:** one scripted run reproduces the whole chain and the backtest table comes from results files.
