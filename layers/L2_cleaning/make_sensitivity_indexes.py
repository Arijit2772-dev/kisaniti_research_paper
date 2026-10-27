"""C.0 section 13, item 18: the sensitivity indexes with at least 2 and at least 4 mandis per index day (dated-only variant).
The primary index uses at least 3. Writes data/processed/basmati/index_dated_only_mm2.csv and _mm4.csv (git-ignored) and the
checksums of all sensitivity variants to layers/L3a_forecasting/config/sensitivity_checksums.json.

Usage:  env/run layers/L2_cleaning/make_sensitivity_indexes.py
"""

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_index import VARIETIES, build_index  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "processed" / "basmati"


def main() -> None:
    with (DATA / "basmati_tidy.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for mm in (2, 4):
        out = []
        for v in VARIETIES:
            out += build_index(rows, v, "dated_only", min_mandis=mm)[0]
        with (DATA / f"index_dated_only_mm{mm}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(out)
        print(f"mm{mm}: {len(out)} index days")
    names = ["index_with_blank.csv", "index_dated_only_towns.csv", "index_with_blank_towns.csv", "index_dated_only_mm2.csv", "index_dated_only_mm4.csv"]
    sums = {n: hashlib.sha256((DATA / n).read_bytes()).hexdigest() for n in names}
    (ROOT / "layers" / "L3a_forecasting" / "config" / "sensitivity_checksums.json").write_text(json.dumps(sums, indent=2) + "\n")


if __name__ == "__main__":
    main()
