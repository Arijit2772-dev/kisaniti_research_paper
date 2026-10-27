# evalkit.py: choices the protocol text leaves open, and one inconsistency found

**Resolved 27 October 2026:** the owner approved these choices and the correction of the pair counts; they are now §13 and §12 of the frozen protocol.

26 October 2026 • `evalkit.py` is the machinery for the C.0 protocol (pairs, baselines, metrics, conformal ranges, Diebold–Mariano with the HLN correction, Holm, block bootstrap, the three-part rule). It is tested on synthetic series (`test_evalkit.py`, 21 tests; 10 deliberate code changes were each caught by at least one test, after one test was strengthened because a one-day look-ahead survived). **No model has been run on the price index.** The protocol stays a draft until the owner approves it.

## Choices made where the draft is silent (the owner confirms them, or they change before the freeze)

| # | Open point in the draft | Choice in evalkit | Alternative |
|---|---|---|---|
| 1 | Loss for the Diebold–Mariano test (§8 does not name it) | absolute error (MAE is the primary metric, §7) | squared error |
| 2 | "10 index days of the current season exist" (§3): is the origin day counted? | yes, the origin is counted: the 10th index day is the first eligible origin | 11th day |
| 3 | Seasonal naive, "the same calendar day" (§5): the origin's or the target's? | the target's, one year earlier; median of the previous season's values within ±3 days; no forecast when the window is empty | origin's day plus h |
| 4 | Moving average of "the last 5 index days" (§5): across seasons? | same season only (§3 forbids lags across the February–August gap); fewer than five days: the mean of those there are | skip the origin |
| 5 | Newey–West "lag h − 1" (§8): which weights? | Bartlett weights 1 − k/h, so the variance is never negative | rectangular weights (the original DM) |
| 6 | Bootstrap "block length at least h days" (§8): the index days are not daily | blocks of h consecutive pairs (always at least h days) | blocks of h calendar days |
| 7 | MASE scale "in-sample naive h-step MAE of the training seasons" (§7) | eligible pairs of every season before the evaluated one | training seasons only for the test season |
| 8 | Range when too few residuals for the nominal level | no range is made (`None`); the protocol also bars coverage claims from fewer than 40 test pairs | wider fallback |

## Inconsistency found in the draft (not corrected here; it is the owner's to decide)

§4 states "at least 60 test-season pairs per variety at every primary horizon (1121: 76, 73, 66; 1509: 71, 66, 60 under dated_only)". Those numbers come from `count_horizon_pairs.py`, which does not apply the §3 rule that an origin needs 10 index days of its season. With the rule (`count_eligible_pairs.py` → `results/C0_protocol/eligible_pairs.csv`, 2025-26, dated_only):

| Variety | h = 1 | h = 7 | h = 14 | h = 28 (secondary) | h = 60 (descriptive) |
|---|---|---|---|---|---|
| 1121 | 68 | 64 | 60 | 50 | 21 |
| Basmati 1509 | 62 | 57 | **51** | **38** | 18 |

So the sentence "at least 60" holds for 1121 only, not for 1509 at 7 and 14 days, and the secondary horizon of 1509 (38) falls under the 40-pair floor for coverage claims. The `with_blank` variant gives 63, 59, 52 and 40 for 1509. Options: (a) state the true counts in §4 and accept 51 to 57 pairs for 1509 at the primary horizons, (b) count the first 10 days as eligible origins (this changes §3), (c) drop 1509 from the primary family. The power numbers in §8 ("smallest detectable gain") must be recomputed from the final pairs in any case, as §8 already says.
