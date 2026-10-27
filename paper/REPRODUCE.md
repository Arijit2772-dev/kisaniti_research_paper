# Reproducing and checking every number in the paper

28 October 2026 • All commands run from `kisaniti_research_paper/`. Python 3.13 environment from `env/` (`env/setup.sh`); the model
comparison needs the packages in `env/requirements_models.lock`.

| Step | Command | What it proves |
|---|---|---|
| Parse the raw monthly files, build the index | `env/run layers/L2_cleaning/parse_basmati.py`, `build_index.py` | every row traced; 6,678 rows reconcile |
| Cleaning screens, blank-date plausibility | `env/run layers/L2_cleaning/compare_screens.py`, `check_blank_date_plausibility.py` | the cleaning choices are measured, not asserted |
| Protocol, freeze, runs (the gate refuses anything out of order) | `env/run layers/L3a_forecasting/run_protocol.py --stage validation\|test\|prospective\|sensitivity` | the test season runs once, after the freeze commits (`git log --oneline` shows `C.0 freeze`, `C.0 configuration freeze`) |
| Independent recomputation of the test statistics | `env/run scripts/independent_check.py` | MAE, Diebold-Mariano, Holm and relative change agree with the runner to 1e-13 (separate code, no shared imports) |
| Allocation experiments | `layers/L3d_allocation_fairness/run_oracle_agreement.py`, `run_policies.py --skip-weighted --tag _no_weighted`, `run_sensitivity.py`, `run_scaling.py` | solver = brute force; 60 plans; sensitivity; scaling |
| System evidence | `env/run scripts/collect_system_evidence.py` (needs a full `scripts/chain.py` run in the product repository) | test counts, contracts, the 14-step run |
| Numbers into the text | `python3 paper/numbers.py --tex` | every number is a macro read from a results file |
| Claims, references, manifest | `env/run scripts/verify_claims.py`; `python3 -I scripts/check_references_crossref.py`; `python3 -I scripts/check_reference_urls.py`; `env/run scripts/make_results_manifest.py verify` | stated numbers match the files; references exist; no result file changed |
| Build | `paper/template/build.sh` (Tectonic) | the PDF |

The test-season runner refuses a second run. To reproduce it from scratch, use a clean clone and delete `results/C0_protocol/test_*`; the
run is deterministic (fixed seeds, one process per job), and `independent_check.py` confirms the statistics from the saved forecasts.
