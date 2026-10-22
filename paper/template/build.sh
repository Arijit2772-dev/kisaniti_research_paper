#!/usr/bin/env bash
# Build the KisanNiti paper PDF: regenerate figures and numbers, then compile with Tectonic.
#   paper/template/build.sh            -> paper/template/build/main.pdf
# Needs: python3 with matplotlib (env/), and Tectonic (brew install tectonic), which fetches
# the LaTeX packages it needs on first run.
set -euo pipefail
cd "$(dirname "$0")"

python3 ../figures/src/fig1_architecture.py --final >/dev/null
python3 ../figures/src/fig2_methodology.py --final >/dev/null
python3 ../figures/src/fig3_hardware.py --final >/dev/null
python3 make_numbers_tex.py
python3 ../numbers.py --tex >/dev/null

# references.bib links to literature/references.bib (owned by the literature phase).
# Until that file exists, fall back to the unverified v2 placeholder.
if [ -e references.bib ]; then
  # l3b_storage.bib: storage-sensing references checked by the M5 session (to be merged into literature/references.bib)
  echo '\bibliography{references,l3b_storage}' > bibfiles.tex
else
  echo "warning: literature/references.bib not found, using paper/references/v2_placeholder.bib" >&2
  cp ../references/v2_placeholder.bib v2_placeholder.bib
  echo '\bibliography{v2_placeholder}' > bibfiles.tex
fi

mkdir -p build
tectonic --keep-logs --outdir build main.tex
echo "built $(pwd)/build/main.pdf"
