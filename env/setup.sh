#!/usr/bin/env bash
# Create the pinned research environment (.venv) and install the shared core editable.
#   env/setup.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UV="${UV:-uv}"
"$UV" venv "$ROOT/.venv" --python 3.13
"$UV" pip install --python "$ROOT/.venv/bin/python" -r "$ROOT/env/requirements.lock"
"$UV" pip install --python "$ROOT/.venv/bin/python" -e "$ROOT/../kisaniti_implementation/core"
