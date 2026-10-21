# KisanNiti — research paper workspace

Research-first workspace (created 21 Oct 2026). It holds research prototypes of every layer, real-data experiments, results, figures and the paper text. Start with the [research plan](RESEARCH_PLAN.md); progress is tracked in [STATUS.md](STATUS.md). Agents start with [CLAUDE.md](CLAUDE.md).

| Folder | What is inside |
|---|---|
| `layers/` | One folder per layer, each with a research card (question, build, alternatives, metrics, outputs): L1 data, L2 cleaning, L3a forecasting, L3b storage/IoT, L3c hold-or-sell, L3d allocation/fairness, L4 manager review, L5 WhatsApp/outcomes |
| `hardware/` | Architecture, Wokwi simulation, firmware |
| `integration/` | End-to-end run and whole-system backtest |
| `literature/` | Verified literature review and references |
| `paper/` | Section drafts, figures, tables, references, template, `numbers.py` |
| `data/` | Raw and processed data (**not committed**); `data/manifests/` is committed |
| `env/` | Pinned Python environment |
| `legacy/v2_from_rp_kisan/` | Copy of the earlier paper v2 workspace (`~/Documents/rp_kisan`) with its experiments and results |
| `reference_papers/` | The group's ICDPN 2025 Springer paper used as the style model (local only, not committed) |

Related repositories: planning [`../kisaniti`](../kisaniti/README.md) (GitHub `kisaniti_plan`), product [`../kisaniti_implementation`](../kisaniti_implementation/README.md).

## Clone layout

Keep all three side by side:

```bash
git clone https://github.com/Arijit2772-dev/kisaniti_plan.git kisaniti
```

```bash
git clone https://github.com/Arijit2772-dev/kisaniti_implementation.git kisaniti_implementation
```

```bash
git clone https://github.com/Arijit2772-dev/kisaniti_research_paper.git kisaniti_research_paper
```
