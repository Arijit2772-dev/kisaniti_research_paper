# L3d — Cooperative allocation and fairness (phase R7, EXP-08/09)

**Research question:** Does an exact, fair cooperative plan send lots to mandis better than simple rules? What does fairness cost in rupees? Which solver is fast enough?

**Build:**
- An exact lexicographic MILP: allocation → per-farmer leximin → storage priority → net return → tie-break.
- A brute-force reference solver for tiny cases.
- An independent plan validator.
- Instance generator for the **300-member Patiala persona** (CHAT-25), with real 2025 paddy prices now and wheat/basmati later.
- Real mandi coordinates; transport costs labelled as assumptions.
- Extends the v2 `allocation_experiment.py`.

**Alternatives compared:**

| Item | Options |
|---|---|
| Policy | Nearest mandi; independent best choice; weighted-sum objective; max-min only; utilitarian (max ₹); KisanNiti leximin; perfect-foresight bound |
| Solver | HiGHS, SCIP, OR-Tools CP-SAT, greedy heuristic |

**Metrics:**
- net ₹/q;
- minimum farmer fulfilment and Gini;
- **price of fairness** (₹ given up for fairness);
- mandi-day limit violations;
- solve, build and validate time against size (farmers 10–1,000, mandis 3–25, dates 3–14);
- 100% agreement with the brute-force reference on tiny cases.

**Outputs:**
- `results/allocation_*.csv`;
- Fig. "price of fairness" and Fig. "solve time vs size";
- the MILP formulation box (as the reference paper presents its algorithm);
- Sections 3.6 and 4.4.

**Done when:** the reference checks pass, all comparisons come from scripts, and the sensitivity to the transport and limit assumptions is shown.
