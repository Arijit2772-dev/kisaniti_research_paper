"""Runs one stage of the pre-registered comparison (PREREGISTERED_PROTOCOL.md) on the variety index.

    env/run layers/L3a_forecasting/run_protocol.py --stage validation|test|prospective [--variant dated_only]

`main()` first asks protocol_gate.check(): no frozen protocol, changed code or data, missing grids, a second test run
all refuse. `run_stage()` itself is pure (series in, tables out) and is tested on synthetic series (test_run_protocol.py).
Nothing here chooses a model: the models and horizons come from config/grids.json, written before the first run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evalkit as ek  # noqa: E402
import protocol_gate as pg  # noqa: E402

ROOT = HERE.parents[1]
OUT = ROOT / "results" / "C0_protocol"
CONFIG = HERE / "config"
SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26", "2026-27"]
STAGE_SEASON = {"validation": "2024-25", "test": "2025-26", "prospective": "2026-27"}
BASELINES: dict[str, ek.Model] = {"naive": ek.naive, "seasonal_naive": ek.seasonal_naive, "ma5": ek.moving_average5}


def registry() -> dict[str, ek.Model]:
    """The baseline models, plus the others if their adapters exist (models_extra.py, added after the freeze)."""
    models = dict(BASELINES)
    try:
        import models_extra  # type: ignore[import-not-found]

        models.update(models_extra.MODELS)
    except ModuleNotFoundError:
        pass
    return models


def run_stage(
    series_by_variety: dict[str, Sequence[ek.Obs]], stage: str, model_names: Sequence[str], horizons: Sequence[int],
    models: dict[str, ek.Model], smallest_gain: dict[str, dict[str, float]] | None = None, draws: int = 2000,
) -> dict[str, list[dict[str, object]]]:
    """Forecast rows, metric rows and (for the test stage) inference rows for every variety, horizon and model."""
    season = STAGE_SEASON[stage]
    earlier = [s for s in SEASONS if s < season]
    forecasts: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []
    for variety, series in series_by_variety.items():
        for h in horizons:
            scale = ek.mase_scale(series, h, earlier)
            for name in model_names:
                fs = ek.run_model(series, models[name], h, season)
                for f in fs:
                    forecasts.append({"variety": variety, "horizon": h, "model": name, "season": season, "origin": f.origin.isoformat(),
                                      "target": f.target.isoformat(), "origin_value": f.origin_value, "forecast": f.forecast, "actual": f.actual})
                if fs:
                    metrics.append({"variety": variety, "horizon": h, "model": name, "season": season, "pairs": len(fs),
                                    "mae": ek.mae(fs), "mase": ek.mase(fs, scale), "smape": ek.smape(fs), "direction_accuracy": ek.direction_accuracy(fs)})
    inference: list[dict[str, object]] = []
    if stage == "test":
        raw = []
        for variety, series in series_by_variety.items():
            for h in (x for x in horizons if x in (1, 7, 14)):  # the primary family (section 8)
                for name in (n for n in model_names if n != "naive"):
                    r = ek.compare_to_naive(series, models[name], h, season, draws)
                    raw.append((variety, h, name, r))
        adj = ek.holm_adjust([r["p_raw"] for *_, r in raw])  # type: ignore[misc]
        for (variety, h, name, r), p_adj in zip(raw, adj, strict=True):
            gain = (smallest_gain or {}).get(variety, {}).get(str(h))
            verdict = "NO_THRESHOLD" if gain is None else ("BETTER" if ek.beats_naive(p_adj, r["ci"], r["relative_change"], gain) else "NO_DETECTABLE_DIFFERENCE")  # type: ignore[arg-type]
            inference.append({"variety": variety, "horizon": h, "model": name, "pairs": r["pairs"], "relative_change": r["relative_change"],
                              "dm_statistic": r["dm_statistic"], "p_raw": r["p_raw"], "p_holm": p_adj, "ci_low": r["ci"][0], "ci_high": r["ci"][1],  # type: ignore[index]
                              "smallest_gain": gain, "verdict": verdict})
    return {"forecasts": forecasts, "metrics": metrics, "inference": inference}


def load_index(path: Path) -> dict[str, list[ek.Obs]]:
    out: dict[str, list[ek.Obs]] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.setdefault(r["variety"], []).append(ek.Obs(date.fromisoformat(r["date"]), r["season"], float(r["index_modal"])))
    return {k: sorted(v, key=lambda o: o.day) for k, v in out.items()}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=list(STAGE_SEASON))
    ap.add_argument("--variant", default="dated_only", choices=["dated_only", "with_blank"])
    a = ap.parse_args()
    index = ROOT / "data" / "processed" / "basmati" / f"index_{a.variant}.csv"
    sums = CONFIG / "data_checksums.json"
    frozen = json.loads(sums.read_text()).get(index.name) if sums.exists() else None
    facts = pg.Facts(
        commit_subjects=tuple(git("log", "--format=%s").splitlines()),
        dirty_paths=tuple(ln[3:] for ln in git("status", "--porcelain", "--", "layers/L3a_forecasting").splitlines()),
        data_sha256=hashlib.sha256(index.read_bytes()).hexdigest(), frozen_data_sha256=frozen,
        grids_present=(CONFIG / "grids.json").exists(), test_results_exist=(OUT / "test_season_results.csv").exists(),
    )
    try:
        pg.check(a.stage, facts)
    except pg.GateRefused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    grids = json.loads((CONFIG / "grids.json").read_text())
    models = registry()
    unknown = [m for m in grids["models"] if m not in models]
    if unknown:
        print(f"REFUSED: models in grids.json without an adapter: {unknown}", file=sys.stderr)
        return 2
    horizons = grids["horizons"]["primary"] + grids["horizons"]["secondary"] + grids["horizons"]["descriptive"]
    res = run_stage(load_index(index), a.stage, grids["models"], horizons, models, grids.get("smallest_detectable_gain"))
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / f"{a.stage}_forecasts.csv", res["forecasts"])
    write_csv(OUT / f"{a.stage}_metrics.csv", res["metrics"])
    if a.stage == "test":
        write_csv(OUT / "test_season_results.csv", res["metrics"])
        write_csv(OUT / "test_season_inference.csv", res["inference"])
    (OUT / f"{a.stage}_run.json").write_text(json.dumps({
        "stage": a.stage, "variant": a.variant, "season": STAGE_SEASON[a.stage], "commit": git("rev-parse", "HEAD").strip(),
        "index_sha256": facts.data_sha256, "models": grids["models"], "horizons": horizons, "python": sys.version.split()[0],
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"), "pairs": len(res["forecasts"]),
    }, indent=2) + "\n")
    print(f"{a.stage}: {len(res['forecasts'])} forecast rows, {len(res['metrics'])} metric rows written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
