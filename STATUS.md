# Research status

Updated 22 Oct 2026.

| Phase | Layer | Status | Notes |
|---|---|---|---|
| Baseline | — | DONE (15 Oct) | Paper v2 + forecasting and allocation runs on real paddy data, in `legacy/v2_from_rp_kisan/` |
| R0 | Setup | NOT STARTED | Pin env, data manifests, reproduce v2 numbers |
| R1 | Literature | NOT STARTED | — |
| R2 | L1 Data | IN PROGRESS | Ingest script + manifests working; wheat Apr–May 2025 dense, off-season Punjab wheat nearly empty (2–5 rows/month); basmati Oct 2025 dense (429 rows, 39 mandis, ₹2,389–3,765) → basmati is the main market-priced crop |
| R3 | L2 Cleaning | NOT STARTED | — |
| R4 | L3a Forecasting | NOT STARTED | v2 paddy results exist |
| R5 | L3b Storage + hardware | NOT STARTED | Hardware decided: ESP32 + SHT30 + Wokwi twin (CHAT-29) |
| R6 | L3c Hold-or-sell | NOT STARTED | Needs R4 |
| R7 | L3d Allocation + fairness | NOT STARTED | v2 allocation results exist |
| R8 | L4 + L5 | NOT STARTED | Needs WhatsApp test number; UI = product Next.js app (CHAT-30) |
| R9 | Integration | NOT STARTED | — |
| R10 | Paper | v3 IN PROGRESS (22 Oct): template + figure drafts | LNCS LaTeX template (llncs v2.25) compiles via `paper/template/build.sh`; Fig. 1 architecture and Fig. 2 methodology drafted as scripts (`paper/figures/src/`, Tabler icons, palette in `style.py`), **awaiting supervisor feedback**; section drafts: Intro + paddy/MSP finding (DRAFT FOR AUTHOR REWRITE), others placeholders; venue (D2) pending |

Known duplicates: an untracked copy of the v2 experiments also exists at `../kisaniti_implementation/experiments/EXP-03_paper_v1/`, and the original at `~/Documents/rp_kisan/`. This folder is the canonical home from now on.
