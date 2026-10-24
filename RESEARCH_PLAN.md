# KisanNiti research plan — research paper first

21 October 2026 • Research-track plan. **The overall plan (paper + software + hardware) is the [master plan](../kisaniti/docs/MASTER_PLAN.md)**; this file details the research side. The user's main goal now is a **Springer research paper** backed by real data, real model runs, fair comparisons and a working prototype of every layer. The full product comes later.

| Folder | Role |
|---|---|
| `kisaniti_research_paper` (this) | Research prototypes per layer, experiments, results, paper text |
| [`../kisaniti`](../kisaniti/README.md) | Design and decisions (source of truth for *how things should be*) |
| [`../kisaniti_implementation`](../kisaniti_implementation/README.md) | The future product; its coding gate stays closed |

## 1. Where we start from (already done)

Imported into [`legacy/v2_from_rp_kisan/`](legacy/v2_from_rp_kisan/README.md) (copy of `~/Documents/rp_kisan`, 15 Oct):

- **Paper v2:** "KisanNiti: An AI- and IoT-Based Framework for Cooperative Post-Harvest Selling in Farmer Producer Organizations". It has Sections 1–5, 25 references and 13 pages in Springer layout. Authors: Harkiran Kaur (supervisor), Arijit Singh, Tushar Garg, Hitesh Mehandiratta, Namya Gautam (Thapar Institute).
- **Real data:** AGMARKNET Paddy (Common), Punjab, Sep–Dec 2020–2025, 16,201 cleaned records, 176 mandis. File: `~/Documents/sem_6/capstone/`.
- **Forecasting run:** naive, moving average, MSP rule, ridge, GRU, T-GCN and A3T-GCN, tested on 2023/2024/2025 seasons with 5 seeds.
  - More than 96% of mandi prices equal the Grade-A MSP.
  - The **MSP rule wins** (mean MAE ₹1.26/q vs naive ₹1.77, A3T-GCN ₹2.36).
- **Allocation run:** a synthetic 40-lot FPO sending to 5 Patiala-area mandis at real 2025 prices.
  - The cooperative integer program gains ₹0.79/q over nearest-mandi at a 300 q mandi-day limit, and ₹3.5–13.9/q at a 200 q limit.
  - Independent choices broke the limits in 100% of runs.
- **Figures:** architecture, mandi network, Wokwi circuit (ESP32 + DHT22 + 2×DS18B20), allocation sensitivity.
- **Earlier capstone** (`~/Documents/sem_6/capstone`): download, audit and cleaning scripts, plus ARIMA, XGBoost and sklearn baselines.

These results already support decision CHAT-20 in the planning folder: MSP crops need no forecasting, while held wheat and basmati do.

## 2. Paper strategy

| Paper | Venue (confirm with guide) | Content | When |
|---|---|---|---|
| **Paper 1** | Springer LNNS/LNCS conference proceedings, same style as the group's ICDPN 2025 paper ([reference](reference_papers/)) | v2 upgraded to v3. Keep the paddy MSP finding. Add wheat and basmati forecasting with price ranges, an exact fair cooperative allocation (leximin MILP vs alternatives), the IoT pipeline with a Wokwi simulation and the storage-risk rule, and screenshots of the manager dashboard and WhatsApp prototype. | First |
| **Paper 2** | Springer journal (SN Computer Science or Agricultural Research) | The full study: hold-or-sell backtest over many seasons, whole-system simulation, solver scaling, real hardware bench test, usability/comprehension tests (with ethics approval) | After Paper 1 |

Each paper reports distinct results; no duplicate publication.

## 3. How the work is split: phases mapped to layers

Every phase delivers four things, written as it goes:

1. working research code in its layer folder;
2. a results file produced by a script;
3. figures and tables;
4. **its own paper section draft** in `paper/sections/`.

Paper numbers are never typed by hand: `paper/numbers.py` reads them from the results.

| Phase | Layer | Research card | Can start now? | Needs from user | Feeds paper section |
|---|---|---|---|---|---|
| R0 | Setup | §4 below | Yes | — | Reproducibility statement |
| R1 | Literature | [literature/README](literature/README.md) | Yes | — | 2 Related Work |
| R2 | L1 Data | [L1_data](layers/L1_data/README.md) | Paddy yes; wheat and basmati need downloads | AGMARKNET downloads (CAPTCHA) or CEDA access | 3.1 Data |
| R3 | L2 Cleaning | [L2_cleaning](layers/L2_cleaning/README.md) | After R2 | — | 3.2 |
| R4 | L3a Forecasting | [L3a_forecasting](layers/L3a_forecasting/README.md) | Paddy re-run now; others after R3 | — | 3.3, 4.1 |
| R5 | L3b Storage + hardware | [L3b_storage_iot](layers/L3b_storage_iot/README.md), [hardware](hardware/README.md) | Yes (Wokwi) | Real kit later (optional for Paper 1) | 3.4, 4.2 |
| R6 | L3c Hold or sell | [L3c_hold_sell](layers/L3c_hold_sell/README.md) | After R4 | — | 3.5, 4.3 |
| R7 | L3d Allocation + fairness | [L3d_allocation_fairness](layers/L3d_allocation_fairness/README.md) | Yes (uses existing paddy prices) | — | 3.6, 4.4 |
| R8 | L4 Review + L5 WhatsApp | [L4](layers/L4_manager_review/README.md), [L5](layers/L5_whatsapp_outcomes/README.md) | After R7 | WhatsApp test number (Meta developer app) | 3.7, 4.5 |
| R9 | Integration | [integration](integration/README.md) | After R4–R8 | — | 4.6 |
| R10 | Paper assembly | [paper/README](paper/README.md) | Continuous; final pass at the end | Venue, template, author details | Whole paper |

**Parallel tracks:**

- R0 → (R1 ∥ R5 ∥ R7) right away.
- R2 starts as soon as the user downloads data.
- R3 → R4 → R6 follow R2.
- R8 after R7.
- R9 last.
- R10 runs alongside everything.

Different phases may run in separate sessions; two sessions never edit the same layer folder at once.

## 4. R0 — setup (first, short)

1. Python environment pinned in `env/` (versions recorded). The baseline is Python 3.13, PyTorch 2.9.1 and SciPy 1.15.2 from the v2 run.
2. Data manifests in `data/manifests/` for the existing paddy files: source, request, row counts, date range, SHA-256.
3. **Reproduce v2:** re-run the legacy forecasting and allocation scripts and confirm the paper numbers match `legacy/.../results/`. Any difference is reported, not hidden.
4. `paper/numbers.py` skeleton and the section files.

## 5. Ground rules (all phases)

- **Real data only for accuracy and benefit claims.** Synthetic FPO members and lots are labelled synthetic, using the 300-member Patiala persona (CHAT-25).
- **Fair comparisons.** Every new method is compared against simple baselines on the same targets, using time-ordered splits with no future data. Report significance tests and negative results.
- **Every reference verified** (DOI opened, claim checked). Plain, human prose in passive/impersonal academic voice (22 Oct supervisor instruction), students first and supervisor last in the author list. No AI-sounding text: use the humanizer skill before finalising.
- **Hardware honesty:**
  - The current design uses ESP32 + SHT30 (CHAT-06).
  - The v2 paper shows DHT22 + 2×DS18B20. Paper v3 must use **one** consistent hardware story, and the user decides which (see §7).
  - A Wokwi simulation is reported as a simulation.
- **Avoid the reference paper's mistakes:**
  - claims beyond what was built ("AI analysis" with no model);
  - sensor-name mix-ups;
  - unformatted references;
  - no numbers in the results.
- **Code standards:**
  - Every layer has tests for its core math (exact quantities, the optimizer checked against brute force on tiny cases).
  - Seeds and versions are logged.
  - `results/` files are produced only by scripts.
- **Product rules respected:** the privacy contract (synthetic people only), MSP as a fixed price, WhatsApp only, no real messages to fictional farmers (use the user's own test phone).

## 6. Proposed timeline (adjust with the guide)

| Week | Work |
|---|---|
| 1 | R0, R1, R5 (Wokwi), R7 start; user downloads wheat and basmati data |
| 2 | R2, R3, R4 forecasting; R7 finish; paper Sections 2, 3.4, 3.6 drafted |
| 3 | R6 hold/sell; R8 dashboard and WhatsApp; Sections 3.3–3.7, 4.1–4.4 |
| 4 | R9 integration; full paper v3 draft; reference and number checks |
| 5 | Guide review, fixes, template, declarations, submission |

## 7. Decisions (resolved 21 Oct 2026)

| # | Decision | Result |
|---|---|---|
| D1 | Hardware story | **ESP32 + SHT30 in grain, real build + Wokwi twin** (CHAT-29); the DHT22 + DS18B20 circuit is retired |
| D2 | Paper 1 venue | Springer LNNS/LNCS conference, still to be named with the guide |
| D3 | Dashboard | **Product Next.js app** for screenshots (CHAT-30); no Streamlit |
| D4 | Manuscript format | **LaTeX Springer template** unless the venue or guide needs Word (CHAT-31) |

Algorithms used in experiments come from the shared `core/` package in `../kisaniti_implementation` (CHAT-28), so the paper and the product run the same code.

## 8. What only the user can do (research track)

1. Download wheat and basmati price data from AGMARKNET (the CAPTCHA blocks scripts), or get CEDA access. Steps are in the [L1 card](layers/L1_data/README.md).
2. Create a Meta WhatsApp developer test number and add your own phone as the test recipient (for R8 screenshots).
3. Confirm D1–D4, author emails and the corresponding author (open items listed in the [v2 README](legacy/v2_from_rp_kisan/README.md)).
4. Optional: buy the hardware kit for a real bench test (Paper 2 needs it; Paper 1 can use Wokwi).
