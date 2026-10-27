"""Writes results/RESULTS_MANIFEST.json: the SHA-256 of every result file that the paper reads, with the research commit
and the checksums of the frozen index files. `verify` mode (used by verify_claims.py) recomputes them and reports any file that
changed, appeared or disappeared since the manifest, so a number in the paper cannot silently come from a modified file.

    env/run scripts/make_results_manifest.py          # write
    env/run scripts/make_results_manifest.py verify   # check
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "RESULTS_MANIFEST.json"
DIRS = ["C0_protocol", "L1_coverage", "L2_cleaning", "L3b_storage", "L3d_allocation", "R0_v2_reproduction", "S1_system"]


def files() -> dict[str, str]:
    out = {}
    for d in DIRS:
        for p in sorted((ROOT / "results" / d).rglob("*")):
            if p.is_file() and not p.name.startswith("."):
                out[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main() -> int:
    now = files()
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        old = json.loads(OUT.read_text())["files"]
        changed = sorted(k for k in old if k in now and old[k] != now[k])
        gone = sorted(set(old) - set(now))
        new = sorted(set(now) - set(old))
        print(f"{len(old)} files in the manifest; changed {changed}; missing {gone}; not in the manifest {new}")
        return 0 if not (changed or gone) else 1
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    frozen = json.loads((ROOT / "layers/L3a_forecasting/config/data_checksums.json").read_text())
    OUT.write_text(json.dumps({"research_commit_before_manifest": commit, "frozen_index_sha256": frozen, "files": now}, indent=2) + "\n")
    print(f"{len(now)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
