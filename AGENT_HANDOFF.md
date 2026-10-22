# Agent handoff — continue KisanNiti from here

22 October 2026 • For any AI agent (Claude, ChatGPT, Codex, Gemini, …) or person taking over. Read this file and you can continue without any earlier chat.

## 1. The project in five lines

1. **KisanNiti** helps a Farmer Producer Organisation (FPO) in Patiala, Punjab decide where, when and how much members should sell after harvest.
2. **Goals:** a Springer research paper first (LNNS/LNCS conference, like the group's ICDPN 2025 paper), then a journal paper, plus working software and hardware built side by side.
3. **Team:** Thapar Institute. Supervisor Harkiran Kaur; students Arijit Singh, Tushar Garg, Hitesh Mehandiratta, Namya Gautam.
4. **Crops:**
   - MSP paddy and wheat use the fixed government price.
   - **Basmati paddy** is the market-priced crop for forecasting, mandi choice and hold-or-sell (CHAT-32).
   - Held wheat is a limitation only.
5. **Hardware:** ESP32 + SHT30 probe inside the grain, real build plus a Wokwi twin (CHAT-29).

## 2. Three repositories (clone side by side)

| Folder | GitHub (private, Arijit2772-dev) | Role | Start file |
|---|---|---|---|
| `~/Documents/kisaniti` | `kisaniti_plan` | Design and decisions (CHAT-01…32) — the source of truth | `CLAUDE.md`, `docs/MASTER_PLAN.md` |
| `~/Documents/kisaniti_implementation` | `kisaniti_implementation` | Product: shared `core/` algorithms, FastAPI, PostgreSQL, Next.js, firmware | `CLAUDE.md`, `STATUS.md` |
| `~/Documents/kisaniti_research_paper` | `kisaniti_research_paper` | Experiments, data, results, figures, paper | `CLAUDE.md`, `RESEARCH_PLAN.md`, `STATUS.md` |

## 3. Where things stand (22 Oct 2026)

| Work | State | Who |
|---|---|---|
| Planning (architecture, 5 layers, decisions, master plan, quality/figure/writing guides) | Done | — |
| Paper v2 (13 pages) on real Paddy(Common) data | Done; being upgraded to v3 | `legacy/v2_from_rp_kisan/` |
| Literature review R1 | Running in a separate session | "kn-literature" |
| M0 foundation + M7 fair allocation | Running | "kn-foundation" |
| M5 hardware (firmware, Wokwi, storage rule) | Running | "kn-hardware" |
| Illustrated figures + LaTeX base | Running | "kn-figures" |
| **Data download (L1)** | In progress: 1 basmati month and 4 wheat months filed | **Needs a human for CAPTCHAs** — follow [layers/L1_data/DOWNLOAD_RUNBOOK.md](layers/L1_data/DOWNLOAD_RUNBOOK.md) |

Check each repo's `STATUS.md` and `git log` for newer progress; parallel sessions may have pushed since this file was written.

## 4. What to do next, in order

1. **Finish basmati downloads:** the runbook lists the months (about 37 CAPTCHAs). The November 2025 form may already be filled in the browser.
2. **L2 cleaning** on basmati and paddy: rules compared against a hand-checked sample ([card](layers/L2_cleaning/README.md)).
3. **L3a forecasting** on basmati by variety: baselines vs ETS/ARIMA vs XGBoost/LightGBM vs GRU/A3T-GCN vs Chronos-2, with 80%/95% ranges and Diebold–Mariano tests ([card](layers/L3a_forecasting/README.md)).
4. **L3c hold-or-sell backtest** on basmati seasons ([card](layers/L3c_hold_sell/README.md)).
5. **Integrate the results** of the running sessions: allocation, storage, figures and literature.
6. **L4/L5 product screens and WhatsApp** test message (needs the user's Meta test number).
7. **End-to-end run, then paper v3 assembly** following the writing and figure guides; authors rewrite in their own words; declare AI assistance (Springer policy).

The full milestone list is M0–M12 in [`../kisaniti/docs/MASTER_PLAN.md`](../kisaniti/docs/MASTER_PLAN.md).

## 5. Non-negotiable rules

- **Real data only for accuracy and benefit claims.** Synthetic farmers and lots are labelled. Never invent data, numbers, results or references.
- **Paper numbers come from result files via a script.** Every reference has an opened, checked DOI.
- **Writing and figures follow the guides:**
  - [paper/WRITING_GUIDE.md](paper/WRITING_GUIDE.md): the college checker flagged v2 as 13% AI-like.
  - [paper/FIGURE_GUIDE.md](paper/FIGURE_GUIDE.md): the supervisor wants illustrated icon-style diagrams.
- **Algorithms live once** in `kisaniti_implementation/core/` and are imported by experiments. Exact kg/₹ arithmetic, per-farmer leximin fairness, a pure optimizer and an independent validator.
- **Design changes go into the planning repo's decision register** before code changes behaviour.
- **Git:**
  - commit only your own files (no `git add -A`);
  - `git pull --rebase --autostash` before pushing;
  - one session per folder.
- **Humans only:** CAPTCHAs, account creation, hardware purchase, WhatsApp account, FPO contact, ethics approval.

## 6. What the user still needs to do

See [`../kisaniti/docs/USER_ACTIONS.md`](../kisaniti/docs/USER_ACTIONS.md):

- solve the CAPTCHAs for the downloads;
- buy the hardware kit;
- set up a Meta WhatsApp test number;
- confirm the venue and author details with the supervisor;
- ask about ethics approval;
- later: hosting, and when to make the repos public.
