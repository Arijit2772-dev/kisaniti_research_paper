# L3c — Hold-or-sell advice (phase R6, EXP-07)

**Research question:** Would range-based hold-or-sell advice have given farmers a better net price than simple practice for held wheat and basmati over past seasons?

**Build:** the pure decision rule from [HOLD_SELL_ADVISORY](../../../kisaniti/docs/design/HOLD_SELL_ADVISORY.md), using the L3a forecasts and the L3b category, plus a backtest engine that only sees the past on each decision date.

**Policies compared:**
1. Sell at harvest.
2. Hold to a fixed month.
3. Forecast-median rule (ignores ranges).
4. KisanNiti range rule.
5. Perfect foresight (upper bound only).

**Costs:** storage loss, holding cost and interest. Values come from the literature (R1); otherwise they are labelled assumptions and tested over a range.

**Metrics:**
- mean and 5th-percentile net ₹/q per season;
- regret against perfect foresight;
- the number of seasons each policy loses to selling at harvest;
- sensitivity tables.

**Outputs:**
- `results/holdsell_backtest.csv`;
- Fig. "net ₹/q by policy and season";
- Sections 3.5 and 4.3.

**Done when:** the backtest is reproducible, the leakage check passes, and the results are reported honestly, even if the advice does not beat selling at harvest.
