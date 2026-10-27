"""Tests for protocol_gate.py: every refusal, and the one path that is allowed at each stage."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protocol_gate as pg  # noqa: E402

OK = dict(
    commit_subjects=("C.0 configuration freeze: grids and chosen models", "validation results", "C.0 freeze: protocol approved", "older"),
    dirty_paths=(), data_sha256="a" * 64, frozen_data_sha256="a" * 64, grids_present=True, test_results_exist=False,
)


def facts(**kw):
    return pg.Facts(**{**OK, **kw})


@pytest.mark.parametrize("stage", ["validation", "test", "prospective"])
def test_a_frozen_clean_run_is_allowed(stage):
    pg.check(stage, facts())


def test_unknown_stage_is_refused():
    with pytest.raises(pg.GateRefused, match="unknown stage"):
        pg.check("whenever", facts())


def test_no_freeze_commit_refuses_every_stage():
    for stage in ("validation", "test", "prospective"):
        with pytest.raises(pg.GateRefused, match="not frozen"):
            pg.check(stage, facts(commit_subjects=("C.0 draft: more text", "B.5: release")))


def test_a_configuration_freeze_does_not_count_as_the_protocol_freeze():
    with pytest.raises(pg.GateRefused, match="not frozen"):
        pg.check("validation", facts(commit_subjects=("C.0 configuration freeze: x",)))


def test_changed_code_or_protocol_refuses():
    with pytest.raises(pg.GateRefused, match="changed since"):
        pg.check("validation", facts(dirty_paths=("layers/L3a_forecasting/evalkit.py",)))


def test_data_checksum_must_be_recorded_and_equal():
    with pytest.raises(pg.GateRefused, match="missing"):
        pg.check("validation", facts(frozen_data_sha256=None))
    with pytest.raises(pg.GateRefused, match="differs"):
        pg.check("validation", facts(data_sha256="b" * 64))


def test_grids_must_exist_before_any_run():
    with pytest.raises(pg.GateRefused, match="grids"):
        pg.check("validation", facts(grids_present=False))


def test_test_and_prospective_need_the_configuration_freeze_but_validation_does_not():
    only_protocol = facts(commit_subjects=("C.0 freeze: protocol approved",))
    pg.check("validation", only_protocol)
    for stage in ("test", "prospective"):
        with pytest.raises(pg.GateRefused, match="configuration is not frozen"):
            pg.check(stage, only_protocol)


def test_the_test_season_runs_once():
    with pytest.raises(pg.GateRefused, match="exactly once"):
        pg.check("test", facts(test_results_exist=True))
    pg.check("prospective", facts(test_results_exist=True))  # a separate, later check is allowed
    pg.check("validation", facts(test_results_exist=True))
