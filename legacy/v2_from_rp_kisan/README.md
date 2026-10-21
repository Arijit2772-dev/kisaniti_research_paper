# rp_kisan — KisanNiti research paper

Everything for the KisanNiti paper in one place (collected 15 Oct 2026). The files here are copies; the originals stay where they were (Desktop and `Documents/kisaniti_implementation/experiments/EXP-03_paper_v1`).

## Folders

| Folder | What is inside |
|---|---|
| `paper/` | `kisaniti_rp_v2.docx` (complete paper, Sections 1–5, 25 references, 13 pages), `kisaniti_rp_v2.pdf` (same, as PDF), `kisaniti_rp_v1_original.docx` (your first draft, Sections 1–3) |
| `figures/` | Fig. 1 architecture, Fig. 2 mandi network, Fig. 3 circuit (cropped), Fig. 4 allocation sensitivity, and the original Wokwi circuit screenshot |
| `experiments/` | Code and results behind Section 4: forecasting comparison, allocation test, figure script, mandi coordinates, `results/` |
| `experiments/paper_build/` | Script that builds the Word file from `content.js` (the paper text) |
| `reference_papers/` | ICDPN 2025 paper used as the format/style model |

## How to rebuild

- Print every number used in the paper: `python3 experiments/paper_numbers.py`
- Re-run experiments (about 15 minutes): `python3 experiments/forecast_experiment.py`, then `python3 experiments/allocation_experiment.py`, then `python3 experiments/make_figures.py`
- Rebuild the Word file after editing `content.js`: in `experiments/paper_build/` run `npm install docx`, then `node build.js ../../paper/kisaniti_rp_v2.docx`

The experiments read the real data from `~/Documents/sem_6/capstone/agmarknet_paddy_common_punjab_cleaned_records.csv` (AGMARKNET Paddy (Common), Punjab, Sep–Dec 2020–2025).

## Still to confirm before submission

1. Which of GPIO 4 / GPIO 16 goes to the DHT22 (the wires overlap in the circuit image).
2. Author emails `hhitesh_be23` and `ngautam_23`, and the corresponding-author mark.
3. Final hardware: the planning folder says ESP32 + SHT30; the paper uses the DHT22 + DS18B20 circuit.
4. The synthetic allocation settings (Rs. 2 per quintal-km, road factor 1.3, Rs. 2 per quintal per day, 300 quintals per mandi-day) with the guide.
5. The target conference's template, page limit and any required "Disclosure of Interests" section.
