# L4 — Manager review and approval (phase R8, EXP-11 lite)

**Research question:** Can a manager review, edit and approve a plan safely, with stock reserved exactly once even under concurrent requests?

**Build:**
- The **product Next.js manager app** with its FastAPI + PostgreSQL backend (CHAT-30), developed in `../kisaniti_implementation`; this card covers the research checks and screenshots. Screens:
  - proposal list;
  - proposal detail with fairness and costs explained;
  - edit;
  - approve with reservation;
  - release;
  - hold-or-sell view;
  - storage view.
- It follows the [UI/UX plan](../../../kisaniti/docs/design/UI_UX_PLAN.md) principles: plan ≠ approval ≠ sale; unknown is never 0.

**Tests:**
- duplicate and concurrent approval (no double reservation);
- exact stock arithmetic (1,000 kg lot: approve 600 → 400 free).

**Metrics:** correctness tests pass/fail; optionally a small usability check if ethics allows.

**Outputs:**
- dashboard screenshots for the paper (the reference paper showed Blynk screenshots);
- the test report;
- Sections 3.7 and 4.5 (part).

**Done when:** the end-to-end approve and release flow works on fixture data and is screenshotted with the DEMO label visible.
