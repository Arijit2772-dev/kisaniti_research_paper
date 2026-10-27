"""Collects the facts about the built system that the paper states, from the product repository and a recorded chain run.
Writes results/S1_system/system_evidence.json. Nothing is typed by hand: counts come from collecting the tests, listing
the contract and migration files, and reading the chain report (a full run of scripts/chain.py, copied beside it).

    env/run scripts/collect_system_evidence.py [--product ../kisaniti_implementation]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "S1_system"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def collected(cmd: list[str], cwd: Path, env: dict[str, str]) -> int:
    out = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True).stdout
    return sum(int(m.group(1)) for m in re.finditer(r"^[^\s:]+\.py: (\d+)$", out, re.M))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", default=str(ROOT.parent / "kisaniti_implementation"))
    prod = Path(ap.parse_args().product)
    base_env = {"PATH": "/usr/bin:/bin"}
    be, core, ing = prod / "backend", prod / "core", prod / "backend" / "ingestion"
    tests = {
        "backend": collected(
            [str(be / ".venv/bin/python"), "-m", "pytest", "--collect-only", "-q"], be,
            {**base_env, "PYTHONPATH": "src:ingestion/src:../core/src", "DATABASE_URL": "postgresql+psycopg://x:y@localhost:1/z"},
        ),
        "core": collected([str(core / ".venv/bin/python"), "-m", "pytest", "--collect-only", "-q"], core, base_env),
        "ingestion": collected(
            [str(ing / ".venv/bin/python"), "-m", "pytest", "--collect-only", "-q"], ing,
            {**base_env, "PYTHONPATH": "src:../../core/src"},
        ),
        "contracts": sum(  # parametrised: one "path::id" line per case
            1 for ln in subprocess.run([str(core / ".venv/bin/python"), "-m", "pytest", "contracts/tests", "--collect-only", "-q"], cwd=prod, env=base_env, capture_output=True, text=True).stdout.splitlines() if "::" in ln
        ),
    }
    slices = sorted(p.parent.parent.parent.name for p in (prod / "contracts").glob("*/v1/examples/index.json"))
    examples = {k: len(list((prod / "contracts").glob(f"*/v1/examples/{k}/*.json"))) for k in ("valid", "invalid")}
    chain = json.loads((OUT / "chain_report.json").read_text())
    evidence = {
        "commits": {"product": git(prod, "rev-parse", "--short", "HEAD"), "research": git(ROOT, "rev-parse", "--short", "HEAD")},
        "tests_collected": tests,
        "contract_slices": slices,
        "contract_examples": examples,
        "migrations": len(list((prod / "backend" / "migrations" / "versions").glob("0*.py"))),
        "chain": {
            "ok": chain["ok"],
            "full_run": "stopped_after" not in chain,
            "steps": [s["step"] for s in chain["steps"]],
            "steps_passed": sum(1 for s in chain["steps"] if s["ok"]),
            "product_commit": chain["commit"],
            "seconds": round(sum(s["seconds"] for s in chain["steps"]), 1),
        },
    }
    (OUT / "system_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
