#!/usr/bin/env bash
# R0: re-run the paper v2 experiments unchanged and compare their outputs with the v2 results.
# The legacy scripts are copied to a scratch folder (results/R0_v2_reproduction/artifacts/, git-ignored);
# only the data path is changed, to point at the copied data in data/processed/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
LEG="$ROOT/legacy/v2_from_rp_kisan/experiments"
OUT="$ROOT/results/R0_v2_reproduction"
WORK="$OUT/artifacts/work"
rm -rf "$WORK"; mkdir -p "$WORK/results"
cp "$LEG"/forecast_experiment.py "$LEG"/allocation_experiment.py "$LEG"/paper_numbers.py "$LEG"/mandi_coordinates.csv "$WORK/"
DATA="$ROOT/data/processed/agmarknet/paddy_common/agmarknet_paddy_common_punjab_cleaned_records.csv"
sed -i '' "s#^RAW = Path(.*)#RAW = Path(\"$DATA\")#" "$WORK/forecast_experiment.py"
grep -q "$DATA" "$WORK/forecast_experiment.py"
cd "$WORK"
{ echo "python: $($PY --version)"; $PY -c "import numpy,pandas,scipy,torch;print('numpy',numpy.__version__,'pandas',pandas.__version__,'scipy',scipy.__version__,'torch',torch.__version__)"; uname -a; date -u +%Y-%m-%dT%H:%M:%SZ; } > "$OUT/environment.txt"
/usr/bin/time -p "$PY" forecast_experiment.py > "$OUT/artifacts/forecast_stdout.txt" 2>&1
/usr/bin/time -p "$PY" allocation_experiment.py > "$OUT/artifacts/allocation_stdout.txt" 2>&1
"$PY" paper_numbers.py > "$OUT/paper_numbers_reproduced.txt"
(cd "$LEG" && "$PY" paper_numbers.py) > "$OUT/paper_numbers_v2.txt"
for f in forecast_table.csv allocation_summary_base.csv allocation_sensitivity.csv allocation_settings.json; do cp "results/$f" "$OUT/$f"; done
"$PY" "$ROOT/scripts/compare_v2.py"
