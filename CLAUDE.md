# Claude — start here for the KisanNiti research paper

## 1. What this folder is

This is the **research-first** workspace. Its goal is a Springer research paper (Paper 1: a conference in LNNS/LNCS style, like the group's ICDPN 2025 paper; Paper 2: a journal) backed by:

- real data;
- real model runs;
- fair comparisons;
- a working research prototype of every layer.

You need no earlier chat context.

## 2. Read first

1. [RESEARCH_PLAN.md](RESEARCH_PLAN.md) and [STATUS.md](STATUS.md).
2. The research card for your phase in `layers/`, `hardware/`, `integration/`, `literature/` or `paper/`.
3. Design source of truth: [`../kisaniti/CLAUDE.md`](../kisaniti/CLAUDE.md). The most relevant parts:
   - decisions CHAT-20 to 26 in [`../kisaniti/docs/blueprint/09_CHAT_DECISION_STATUS.md`](../kisaniti/docs/blueprint/09_CHAT_DECISION_STATUS.md);
   - the [research and experiment plan](../kisaniti/docs/research/RESEARCH_AND_EXPERIMENT_PLAN.md);
   - [design alternatives](../kisaniti/docs/research/DESIGN_ALTERNATIVES.md);
   - [hold-or-sell spec](../kisaniti/docs/design/HOLD_SELL_ADVISORY.md);
   - [Patiala research](../kisaniti/docs/research/2026-10-15_Patiala_Storage_Risk_and_Unknowns.md);
   - [FPO persona](../kisaniti/docs/research/PATIALA_FPO_PROFILE_APPROX.md);
   - [Springer plan](../kisaniti/docs/paper/SPRINGER_PUBLICATION_PLAN.md).
4. The earlier work in `legacy/v2_from_rp_kisan/`: read its README before changing anything it covers.

## 3. Rules

**Research prototypes**
- Research code is allowed here (decision CHAT-27).
- The product gate for `../kisaniti_implementation` is unchanged. Do not copy research code there without review.

**Data and results**
- Real data only for accuracy and benefit claims. Synthetic people and lots must be labelled synthetic. Never invent data.
- Results files are written only by scripts. Paper numbers come from `paper/numbers.py`, never typed by hand.
- Fair comparisons: same targets, time-ordered splits, no future data, baselines always included, significance tests, negative results reported.

**Writing**
- Every reference verified: open the DOI and check the claim; never invent a citation; log what was checked.
- Plain, human first-person prose ("we"); short sentences; no AI-sounding phrases; use the humanizer skill before finalising.

**Engineering**
- Tests for core math: exact quantities, a brute-force reference for the optimizer, stock arithmetic.
- Seeds and package versions logged.
- Secrets in `.env` (never committed). No personal data: synthetic farmers only; WhatsApp tests go only to the user's own phone.

**Design changes**
- Design or decision changes go to the planning repo registers, not just into code.
- If results contradict a design decision, record a conflict there.

## 4. How to work

- One phase or layer at a time.
- Commit with clear messages and push to `origin main`.
- Update [STATUS.md](STATUS.md) and the layer README's "Results" section, then write the matching paper section draft.
- Ask the user only for what they alone can do:
  - data downloads behind CAPTCHA;
  - the WhatsApp test number;
  - decisions D1–D4 in the plan;
  - author details.
