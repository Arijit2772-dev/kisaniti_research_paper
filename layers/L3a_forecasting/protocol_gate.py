"""The technical form of pre-registration: the comparison cannot be run before the protocol is frozen, cannot be
run on changed code or data, and the test season cannot be run twice. Pure decision functions (tested in
test_protocol_gate.py); run_protocol.py supplies the facts from git and the file system.
"""

from __future__ import annotations

from dataclasses import dataclass

FREEZE_PREFIX = "C.0 freeze"
CONFIG_PREFIX = "C.0 configuration freeze"


class GateRefused(Exception):
    """The run is not allowed; the message says what is missing."""


@dataclass(frozen=True)
class Facts:
    commit_subjects: tuple[str, ...]  # subjects of all commits reachable from HEAD, newest first
    dirty_paths: tuple[str, ...]  # tracked or untracked changes under the guarded folders
    data_sha256: str  # checksum of the index file the run would read
    frozen_data_sha256: str | None  # checksum recorded in config/data_checksums.json at the freeze, if any
    grids_present: bool
    test_results_exist: bool


def check(stage: str, f: Facts) -> None:
    """Raise GateRefused unless `stage` ('validation', 'test' or 'prospective') may run."""
    if stage not in ("validation", "test", "prospective"):
        raise GateRefused(f"unknown stage {stage!r}")
    if not any(s.startswith(FREEZE_PREFIX) and not s.startswith(CONFIG_PREFIX) for s in f.commit_subjects):
        raise GateRefused(f"the protocol is not frozen: no commit whose subject starts with {FREEZE_PREFIX!r}")
    if f.dirty_paths:
        raise GateRefused("code, protocol or config changed since the last commit: " + ", ".join(sorted(f.dirty_paths)[:5]))
    if f.frozen_data_sha256 is None:
        raise GateRefused("config/data_checksums.json is missing: the data checksum was not frozen")
    if f.data_sha256 != f.frozen_data_sha256:
        raise GateRefused("the index file differs from the frozen checksum")
    if not f.grids_present:
        raise GateRefused("config/grids.json is missing: the grids must be written before the first validation run")
    if stage in ("test", "prospective"):
        if not any(s.startswith(CONFIG_PREFIX) for s in f.commit_subjects):
            raise GateRefused(f"the configuration is not frozen: no commit whose subject starts with {CONFIG_PREFIX!r}")
    if stage == "test" and f.test_results_exist:
        raise GateRefused("the test season has already been run once; it is evaluated exactly once")
