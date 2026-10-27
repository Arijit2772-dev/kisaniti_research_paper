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


CONFORMAL = {"naive", "seasonal_naive", "ma5", "lightgbm", "gru"}  # protocol section 6: split-conformal for models 1-3, 6 and 7
LEVELS = (80, 95)
TUNED = ("lightgbm", "gru")  # families with grid variants


def registry() -> dict[str, ek.Model]:
    """The baseline models, plus models 4 to 8 and their grid variants (models_extra.py)."""
    models = dict(BASELINES)
    import models_extra

    models.update(models_extra.MODELS)
    return models


def runnable(family: str, variety: str, h: int, chosen: dict | None) -> str:
    """The runnable model name of a family: itself, or (test and prospective stages) the grid variant chosen on validation."""
    return family if chosen is None else chosen.get(family, {}).get(variety, {}).get(str(h), family)


def range_rows(variety: str, h: int, family: str, method: str, season: str, ys: list[float], los: dict[int, list[float]], his: dict[int, list[float]]) -> list[dict[str, object]]:
    out = []
    for level in LEVELS:
        if level not in los or not ys:
            continue
        m = ek.interval_metrics(ys, los[level], his[level], level / 100)
        hits = [float(lo <= y <= hi) for y, lo, hi in zip(ys, los[level], his[level], strict=True)]
        lo_ci, hi_ci = ek.block_bootstrap_mean(hits, h)
        out.append({"variety": variety, "horizon": h, "model": family, "range_method": method, "season": season, "level": level, "pairs": len(ys),
                    "coverage": m["coverage"], "coverage_ci_low": lo_ci, "coverage_ci_high": hi_ci, "mean_width": m["mean_width"],
                    "pinball": m["pinball"], "calibrated": bool(lo_ci <= level / 100 <= hi_ci), "claim_allowed": len(ys) >= 40})
    return out


_WORKER: dict[str, object] = {}


def _task(args: tuple) -> tuple:
    """One (variety, horizon, family) job: forecasts for the whole stage season. Runs in a worker process."""
    variety, series, h, fam, name, stage, chosen_unused, models_arg = args
    models = models_arg if models_arg is not None else _WORKER.setdefault("models", registry())  # type: ignore[assignment]
    return (variety, h, fam, name, ek.run_model(series, models[name], h, STAGE_SEASON[stage]))  # type: ignore[index]


def run_stage(
    series_by_variety: dict[str, Sequence[ek.Obs]], stage: str, families: Sequence[str], horizons: Sequence[int],
    models: dict[str, ek.Model] | None, smallest_gain: dict[str, dict[str, float]] | None = None, draws: int = 2000,
    chosen: dict | None = None, calibration: dict[tuple[str, int, str], list[float]] | None = None, workers: int = 1,
) -> dict[str, list[dict[str, object]]]:
    """Forecast rows, metric rows, range rows and (test stage) inference rows for every variety, horizon and model.
    `families` are runnable names in the validation stage and model families in the test and prospective stages, where
    `chosen` maps a tuned family to its validation-chosen variant per variety and horizon. With models=None the workers
    build the registry themselves (needed for more than one process)."""
    season = STAGE_SEASON[stage]
    earlier = [x for x in SEASONS if x < season]
    jobs = [(v, list(series_by_variety[v]), h, fam, runnable(fam, v, h, chosen), stage, None, models) for v in series_by_variety for h in horizons for fam in families]
    if workers > 1:
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(workers, max_tasks_per_child=1) as ex:  # a fresh process per job: LightGBM and PyTorch never share one
            done = list(ex.map(_task, [(*j[:7], None) for j in jobs], chunksize=1))
    else:
        done = [_task(j) for j in jobs]
    by_key = {(v, h, fam): fs for v, h, fam, _, fs in done}
    forecasts: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []
    ranges: list[dict[str, object]] = []
    scales = {(v, h): ek.mase_scale(series_by_variety[v], h, earlier) for v in series_by_variety for h in horizons}
    for variety, h, fam, name, fs in done:
        for f in fs:
            row = {"variety": variety, "horizon": h, "model": fam.split("@")[0], "config": name, "season": season, "origin": f.origin.isoformat(),
                   "target": f.target.isoformat(), "origin_value": f.origin_value, "forecast": f.forecast, "actual": f.actual}
            for lvl in LEVELS:
                row[f"lo{lvl}"], row[f"hi{lvl}"] = (f.ranges[lvl] if f.ranges and lvl in f.ranges else (None, None))
            forecasts.append(row)
        if not fs:
            continue
        metrics.append({"variety": variety, "horizon": h, "model": fam.split("@")[0], "config": name, "season": season, "pairs": len(fs),
                        "mae": ek.mae(fs), "mase": ek.mase(fs, scales[(variety, h)]), "smape": ek.smape(fs), "direction_accuracy": ek.direction_accuracy(fs)})
        if stage == "validation":
            continue
        ys = [f.actual for f in fs]
        if all(f.ranges for f in fs):
            ranges += range_rows(variety, h, fam, "native", season, ys, {lv: [f.ranges[lv][0] for f in fs] for lv in LEVELS},
                                 {lv: [f.ranges[lv][1] for f in fs] for lv in LEVELS})
        res = (calibration or {}).get((variety, h, fam))
        if fam in CONFORMAL and res:
            los, his = {}, {}
            for lvl in LEVELS:
                w = ek.conformal_halfwidth(res, lvl / 100)
                if w is not None:
                    los[lvl], his[lvl] = [f.forecast - w for f in fs], [f.forecast + w for f in fs]
            ranges += range_rows(variety, h, fam, "conformal", season, ys, los, his)
    inference: list[dict[str, object]] = []
    if stage == "test":
        raw = []
        for variety in series_by_variety:
            for h in (x for x in horizons if x in (1, 7, 14)):  # the primary family (section 8)
                for fam in (f for f in families if f != "naive"):
                    raw.append((variety, h, fam, ek.compare_forecasts(by_key[(variety, h, fam)], by_key[(variety, h, "naive")], h, draws)))
        adj = ek.holm_adjust([r["p_raw"] for *_, r in raw])  # type: ignore[misc]
        for (variety, h, fam, r), p_adj in zip(raw, adj, strict=True):
            gain = (smallest_gain or {}).get(variety, {}).get(str(h))
            verdict = "NO_THRESHOLD" if gain is None else ("BETTER" if ek.beats_naive(p_adj, r["ci"], r["relative_change"], gain) else "NO_DETECTABLE_DIFFERENCE")  # type: ignore[arg-type]
            inference.append({"variety": variety, "horizon": h, "model": fam, "pairs": r["pairs"], "relative_change": r["relative_change"],
                              "dm_statistic": r["dm_statistic"], "p_raw": r["p_raw"], "p_holm": p_adj, "ci_low": r["ci"][0], "ci_high": r["ci"][1],  # type: ignore[index]
                              "smallest_gain": gain, "verdict": verdict})
    return {"forecasts": forecasts, "metrics": metrics, "ranges": ranges, "inference": inference}


def load_index(path: Path) -> dict[str, list[ek.Obs]]:
    out: dict[str, list[ek.Obs]] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.setdefault(r["variety"], []).append(ek.Obs(date.fromisoformat(r["date"]), r["season"], float(r["index_modal"]), int(r["n_mandis"]), float(r["iqr"])))
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
    ap.add_argument("--workers", type=int, default=1)
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
    horizons = grids["horizons"]["primary"] + grids["horizons"]["secondary"] + grids["horizons"]["descriptive"]
    chosen = calibration = None
    if a.stage == "validation":
        families = [n for fam in grids["families"] for n in ([k for k in models if k.startswith(fam + "@")] if fam in TUNED else [fam])]
    else:
        families = grids["families"]
        chosen = json.loads((CONFIG / "chosen.json").read_text())
        calibration = {}
        with (OUT / "validation_forecasts.csv").open(newline="") as fh:
            for r in csv.DictReader(fh):
                if runnable(r["model"], r["variety"], int(r["horizon"]), chosen) == r["config"]:
                    calibration.setdefault((r["variety"], int(r["horizon"]), r["model"]), []).append(abs(float(r["forecast"]) - float(r["actual"])))
    unknown = [m for m in families if m not in models and runnable(m, "", 0, chosen) not in models]
    if unknown:
        print(f"REFUSED: models without an adapter: {unknown}", file=sys.stderr)
        return 2
    res = run_stage(load_index(index), a.stage, families, horizons, None if a.workers > 1 else models, grids.get("smallest_detectable_gain"), chosen=chosen, calibration=calibration, workers=a.workers)
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / f"{a.stage}_forecasts.csv", res["forecasts"])
    write_csv(OUT / f"{a.stage}_metrics.csv", res["metrics"])
    write_csv(OUT / f"{a.stage}_ranges.csv", res["ranges"])
    if a.stage == "test":
        write_csv(OUT / "test_season_results.csv", res["metrics"])
        write_csv(OUT / "test_season_inference.csv", res["inference"])
    (OUT / f"{a.stage}_run.json").write_text(json.dumps({
        "stage": a.stage, "variant": a.variant, "season": STAGE_SEASON[a.stage], "commit": git("rev-parse", "HEAD").strip(),
        "index_sha256": facts.data_sha256, "models": families, "horizons": horizons, "python": sys.version.split()[0],
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"), "pairs": len(res["forecasts"]),
    }, indent=2) + "\n")
    print(f"{a.stage}: {len(res['forecasts'])} forecast rows, {len(res['metrics'])} metric rows written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
