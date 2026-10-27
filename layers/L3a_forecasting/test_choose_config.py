import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import choose_config as cc  # noqa: E402

GRIDS = {"lightgbm": [{"num_leaves": 7, "n_estimators": 100}, {"num_leaves": 15, "n_estimators": 100}],
         "gru": [{"hidden": 16, "epochs": 50}, {"hidden": 32, "epochs": 50}]}


def rows(lgb_mae, gru_mae):
    out = []
    for v in ("1121",):
        for h in (1, 7):
            for cfg, m in zip(("lightgbm@nl7_n100", "lightgbm@nl15_n100"), lgb_mae[h], strict=True):
                out.append({"variety": v, "horizon": str(h), "model": "lightgbm", "config": cfg, "mae": str(m)})
            for cfg, m in zip(("gru@h16_e50", "gru@h32_e50"), gru_mae[h], strict=True):
                out.append({"variety": v, "horizon": str(h), "model": "gru", "config": cfg, "mae": str(m)})
    return out


def test_lowest_validation_mae_wins_per_horizon_and_ties_go_to_the_first():
    got = cc.choose(rows({1: (5.0, 4.0), 7: (3.0, 3.0)}, {1: (2.0, 9.0), 7: (8.0, 1.0)}), GRIDS)
    assert got["lightgbm"]["1121"] == {"1": "lightgbm@nl15_n100", "7": "lightgbm@nl7_n100"}
    assert got["gru"]["1121"] == {"1": "gru@h16_e50", "7": "gru@h32_e50"}


def test_a_missing_variant_refuses():
    r = [x for x in rows({1: (5.0, 4.0), 7: (3.0, 3.0)}, {1: (2.0, 9.0), 7: (8.0, 1.0)}) if x["config"] != "gru@h32_e50"]
    with pytest.raises(SystemExit, match="missing"):
        cc.choose(r, GRIDS)
