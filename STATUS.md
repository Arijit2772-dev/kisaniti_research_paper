# Research status

Updated 24 Oct 2026. Overall checklist: `../kisaniti/docs/PROJECT_TRACKER.md`.

| Phase | Layer | Status | Notes |
|---|---|---|---|
| Baseline | — | DONE (15 Oct) | Paper v2 + forecasting and allocation runs on real paddy data, in `legacy/v2_from_rp_kisan/` |
| R0 | Setup | DONE (22 Oct) | Pinned env; paddy manifests; v2 reproduced: 222 of 222 numbers equal at paper rounding (`results/R0_v2_reproduction`) |
| R1 | Literature | DONE (22 Oct), author check pending | `literature/`: LITERATURE_REVIEW.md (31 search strings, 38 studies, feature matrix, gaps), references.bib (57 entries, all opened), verification_log.md. v2 flags: anoop claim wrong, icrier author name, ds18b20 publisher, shams issue, urra partial. Parameters: farm storage loss 0–0.5% total in first ~3 months (no per-month figure), current holding cost not found, KCC 7% (4% with prompt repayment). Section 2 draft: `paper/sections/02_related_work.md` (authors to rewrite; port into 02_related_work.tex) |
| R2 | L1 Data | DONE for Paper 1 (24 Oct) | Paddy(Basmati) Punjab: 29 months filed (4 full seasons + 2025-26 + start of 2026-27), 6,098 rows, 86 mandis, 6 varieties; June 2025 empty. Coverage: `results/L1_coverage/basmati_coverage.md`. Wheat off-season too sparse (CHAT-32). Still open: sourced MSP table (tracker A.3) |
| R3 | L2 Cleaning | NOT STARTED | — |
| R4 | L3a Forecasting | NOT STARTED | v2 paddy results exist |
| R5 | L3b Storage + hardware | SIMULATION DONE (22 Oct); real node WAITING ON USER (kit) | Rule STORAGE-DEMO-0.1 in shared core; 6 simulated basmati scenarios x 20 seeds vs 3 simpler rules (`layers/L3b_storage_iot/`, `results/L3b_storage/`); Fig. 3 + storage figure + Table; Sections 3.4/4.2 drafted; firmware + Wokwi twin + ingestion in the implementation repo |
| R6 | L3c Hold-or-sell | NOT STARTED | Needs R4 |
| R7 | L3d Allocation + fairness | CORE DONE, EXPERIMENTS UNFINISHED | Exact allocation core, oracle, validator in the product repo (CI green); policy/solver comparison scripts started (`layers/L3d_allocation_fairness/`), runs not completed; v2 allocation results exist |
| R8 | L4 + L5 | NOT STARTED | Needs WhatsApp test number; UI = product Next.js app (CHAT-30) |
| R9 | Integration | NOT STARTED | — |
| R10 | Paper | v3 IN PROGRESS (22 Oct): template + figure drafts | LNCS LaTeX template (llncs v2.25) compiles via `paper/template/build.sh`; Fig. 1 architecture and Fig. 2 methodology drafted as scripts (`paper/figures/src/`, Tabler icons, palette in `style.py`), **awaiting supervisor feedback**; section drafts: Intro + paddy/MSP finding (DRAFT FOR AUTHOR REWRITE), others placeholders; venue (D2) pending |

Known duplicates: an untracked copy of the v2 experiments also exists at `../kisaniti_implementation/experiments/EXP-03_paper_v1/`, and the original at `~/Documents/rp_kisan/`. This folder is the canonical home from now on.
