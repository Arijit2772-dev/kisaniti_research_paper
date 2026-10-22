# Paper (phase R10, continuous)

**Guides:** [WRITING_GUIDE](WRITING_GUIDE.md), [FIGURE_GUIDE](FIGURE_GUIDE.md).

**Build:** `paper/template/build.sh` regenerates the figures (final mode) and number macros and compiles `paper/template/build/main.pdf`. Draft figure previews: `python3 paper/figures/src/fig1_architecture.py` (and `fig2_methodology.py`); add `--final` for the paper version, which draws every part not marked built as dashed grey.

**Folders:**
- `sections/`: one draft per section, written as each phase finishes.
- `figures/`, `tables/`: produced only by scripts.
- `references/`: the verified bib file.
- `template/`: the venue's Springer template once chosen (decision D2/D4).
- `numbers.py`: prints every number used in the text from the results files.

**Section map (Paper 1, v3):**

| Section | Content | From phase |
|---|---|---|
| Abstract, Keywords | Written last | All |
| 1 Introduction | Problem: FPO post-harvest selling in Punjab; MSP vs market crops; contributions | R1 + all |
| 2 Related Work | Verified literature plus the comparison matrix | R1 |
| 3 Proposed System | 3.1 Data, 3.2 Cleaning, 3.3 Forecasting, 3.4 Storage + IoT, 3.5 Hold/sell, 3.6 Allocation + fairness (MILP box), 3.7 Review + WhatsApp; architecture figure | R2–R8 |
| 4 Results and Discussion | 4.1 Forecasting, 4.2 Storage, 4.3 Hold/sell, 4.4 Allocation + fairness + solvers, 4.5 Prototype screenshots, 4.6 End-to-end; 4.7 Societal impact | R4–R9 |
| 5 Conclusion and Future Work | Findings, limitations (synthetic FPO, WhatsApp assumption, simulated hardware), Paper 2 plans | All |
| Declarations | Funding, competing interests, ethics, data/code availability, author contributions | User + R10 |
| References | Springer LNCS style, all verified | R1 |

**Baseline text:** `legacy/v2_from_rp_kisan/experiments/paper_build/content.js` (v2). Reuse what still holds, and replace numbers with v3 results.

**Final checks before submission:**
- every number matches `numbers.py`;
- every DOI opens;
- humanizer pass on the prose;
- guide review;
- plagiarism check through the college;
- the venue's page limit and template.
