"""EXP L3b: STORAGE-DEMO-0.1 vs simpler storage rules on simulated Patiala basmati scenarios.

    PYTHONPATH=../kisaniti_implementation/core/src .venv/bin/python layers/L3b_storage_iot/run_experiment.py

Writes results/L3b_storage/ (per-run metrics, summary, hourly traces for seed 0, environment and settings).
All inputs are SYNTHETIC (scenarios.py). The comparison is about rule behaviour; it does not validate any rule
against real spoilage.

Rules
  DEMO        STORAGE-DEMO-0.1 from the shared core (kisaniti_core.storage), unchanged.
  INSTANT     The same bands and temperature adjustments on the latest in-grain reading only
              (no 24 h median, no hysteresis, no settling or coverage checks): an ablation.
  AMBIENT_RH  Latest shed-air RH only, same 65/70 % bands: what a probe hanging in the shed would give.
  TEMP_ONLY   Latest in-grain temperature only: <15 C LOW, 15-25 C MEDIUM, >=25 C HIGH (insect bands, Part B2).

Reference ("intended condition") at each hour: the STORAGE-DEMO-0.1 bands and temperature adjustments applied to the
noise-free in-grain a_w and temperature of the scenario at that instant. Agreement with it measures how far noise,
outages, placement and simplifications move a rule away from the FAO-based definition; it is not ground truth about
grain quality.
"""

from __future__ import annotations

import csv
import json
import platform
import statistics
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from scenarios import SAMPLE, SCENARIO_ASSUMPTIONS, SCENARIOS, Scenario, Stream, simulate  # noqa: E402

from kisaniti_core.provenance import Origin  # noqa: E402
from kisaniti_core.storage import (  # noqa: E402
    POLICY_VERSION,
    Assignment,
    Crop,
    HysteresisState,
    Placement,
    Reading,
    assess,
)
from kisaniti_core.storage.rule import adjust_for_temperature, raw_level  # noqa: E402

OUT = ROOT / "results" / "L3b_storage"
SEEDS = list(range(20))
BIASES = [(0.0, 0.0), (2.0, 0.3), (-2.0, -0.3)]  # (RH points, C): SHT30 typical tolerance (datasheet v7)
RULES = ["DEMO", "INSTANT", "AMBIENT_RH", "TEMP_ONLY"]
RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
FRESH = timedelta(minutes=15)


def intended(aw: float, t: float) -> str:
    level, _ = adjust_for_temperature(raw_level(100 * aw), t, 100 * aw)
    return level.value


def instant_band(rh: float, t: float | None) -> str:
    level = raw_level(rh)
    if t is not None:
        level, _ = adjust_for_temperature(level, t, rh)
    return level.value


def temp_band(t: float) -> str:
    return "HIGH" if t >= 25 else ("MEDIUM" if t >= 15 else "LOW")


def run_rules(sc: Scenario, s: Stream) -> dict[str, list[str]]:
    """Category of each rule at every whole hour after insertion."""
    t0 = s.times[0]
    hours = [t0 + timedelta(hours=h) for h in range(1, sc.days * 24 + 1)]
    received = np.array([r.timestamp() if r else np.inf for r in s.received])
    measured = np.array([t.timestamp() for t in s.times])
    placement = Placement.IN_GRAIN if sc.placement == "IN_GRAIN" else Placement.AMBIENT
    asg = Assignment("kn-sim-001", placement, Crop.PADDY, t0)
    readings = [Reading(t, float(tc), float(rh), origin=Origin.SYNTHETIC)
                for t, tc, rh in zip(s.times, s.probe_t, s.probe_rh, strict=True)]
    out: dict[str, list[str]] = {r: [] for r in RULES}
    state: HysteresisState | None = None
    for at in hours:
        a_ts = at.timestamp()
        lo = int(np.searchsorted(measured, a_ts - 86400, side="right"))
        hi = int(np.searchsorted(measured, a_ts, side="right"))
        idx = [i for i in range(lo, hi) if received[i] <= a_ts]
        res = assess([readings[i] for i in idx], asg, at, state, Origin.SYNTHETIC)
        state = res.state
        out["DEMO"].append(res.category.value)
        fresh = [i for i in idx if a_ts - measured[i] <= FRESH.total_seconds()]
        if not fresh:
            for r in ("INSTANT", "AMBIENT_RH", "TEMP_ONLY"):
                out[r].append("UNKNOWN")
            continue
        j = fresh[-1]
        # INSTANT and TEMP_ONLY read the probe wherever it is; AMBIENT_RH always reads shed air (a second
        # imaginary probe with the same noise draw), so it is defined in every scenario.
        out["INSTANT"].append(instant_band(float(s.probe_rh[j]), float(s.probe_t[j])))
        amb_rh = float(np.clip(s.ambient_rh[j] + (s.probe_rh[j] - _seen_rh(sc, s, j)), 0, 100))
        out["AMBIENT_RH"].append(instant_band(amb_rh, None))
        out["TEMP_ONLY"].append(temp_band(float(s.probe_t[j])))
    return out


def _seen_rh(sc: Scenario, s: Stream, j: int) -> float:
    return float(s.ambient_rh[j]) if sc.placement == "AMBIENT" else float(100 * s.grain_aw[j])


def reference(sc: Scenario, s: Stream) -> list[str]:
    t0 = s.times[0]
    per_hour = int(timedelta(hours=1) / SAMPLE)
    return [intended(float(s.grain_aw[h * per_hour]), float(s.grain_t[h * per_hour]))
            for h in range(1, sc.days * 24 + 1)] if t0 else []


def flips(cats: Sequence[str]) -> int:
    known = [c for c in cats if c != "UNKNOWN"]
    return sum(a != b for a, b in zip(known, known[1:], strict=False))


def first_at_least(cats: Sequence[str], level: str) -> int | None:
    return next((i for i, c in enumerate(cats) if c != "UNKNOWN" and RANK[c] >= RANK[level]), None)


def metrics(cats: Sequence[str], ref: Sequence[str], days: int) -> dict[str, float | None]:
    known = [(c, r) for c, r in zip(cats, ref, strict=True) if c != "UNKNOWN"]
    n = len(cats)
    m: dict[str, float | None] = {
        "share_unknown": 1 - len(known) / n,
        "share_low": sum(c == "LOW" for c in cats) / n,
        "share_medium": sum(c == "MEDIUM" for c in cats) / n,
        "share_high": sum(c == "HIGH" for c in cats) / n,
        "flips_per_week": flips(cats) / (days / 7),
        "agreement_known": (sum(c == r for c, r in known) / len(known)) if known else None,
        "false_high_share": (sum(c == "HIGH" and r != "HIGH" for c, r in known) / len(known)) if known else None,
        "missed_high_share": (sum(c != "HIGH" and r == "HIGH" for c, r in known) / len(known)) if known else None,
    }
    ref_high, rule_high = first_at_least(ref, "HIGH"), first_at_least(cats, "HIGH")
    m["high_delay_h"] = (rule_high - ref_high) if ref_high is not None and rule_high is not None else None
    return m


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    traces: dict[str, dict[str, object]] = {}
    for sc in SCENARIOS:
        for rh_bias, t_bias in BIASES:
            for seed in SEEDS:
                s = simulate(sc, seed, rh_bias=rh_bias, t_bias=t_bias)
                ref = reference(sc, s)
                cats = run_rules(sc, s)
                for rule in RULES:
                    rows.append({"scenario": sc.key, "rule": rule, "rh_bias": rh_bias, "t_bias": t_bias, "seed": seed,
                                 **metrics(cats[rule], ref, sc.days)})
                if seed == 0 and rh_bias == 0:
                    per_hour = int(timedelta(hours=1) / SAMPLE)
                    traces[sc.key] = {
                        "start": s.times[0].isoformat(), "hours": len(ref), "reference": ref, **cats,
                        "grain_aw": [round(float(x), 4) for x in s.grain_aw[per_hour::per_hour]],
                        "grain_t": [round(float(x), 2) for x in s.grain_t[per_hour::per_hour]],
                        "probe_rh": [round(float(x), 2) for x in s.probe_rh[per_hour::per_hour]],
                        "ambient_rh": [round(float(x), 2) for x in s.ambient_rh[per_hour::per_hour]],
                        "ambient_t": [round(float(x), 2) for x in s.ambient_t[per_hour::per_hour]],
                        "lost_samples": sum(r is None for r in s.received),
                    }
            print(f"{sc.key} bias {rh_bias:+.0f}%RH/{t_bias:+.1f}C done", flush=True)

    with (OUT / "runs.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    summary = []
    keys = [k for k in rows[0] if k not in ("scenario", "rule", "rh_bias", "t_bias", "seed")]
    for sc in SCENARIOS:
        for rh_bias, t_bias in BIASES:
            for rule in RULES:
                sel = [r for r in rows if r["scenario"] == sc.key and r["rule"] == rule and r["rh_bias"] == rh_bias]
                rec: dict[str, object] = {"scenario": sc.key, "rule": rule, "rh_bias": rh_bias, "t_bias": t_bias,
                                          "seeds": len(sel)}
                for k in keys:
                    vals = [float(r[k]) for r in sel if r[k] is not None]  # type: ignore[arg-type]
                    rec[f"{k}_mean"] = round(statistics.fmean(vals), 4) if vals else ""
                    rec[f"{k}_sd"] = round(statistics.stdev(vals), 4) if len(vals) > 1 else ""
                    rec[f"{k}_n"] = len(vals)
                summary.append(rec)
    with (OUT / "summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    (OUT / "traces_seed0.json").write_text(json.dumps(traces))
    (OUT / "settings.json").write_text(json.dumps({
        "policy_version": POLICY_VERSION, "seeds": SEEDS, "biases_rh_t": BIASES, "rules": RULES,
        "assessment_step": "1 h", "sample_interval": "5 min", "noise_sd": {"rh_points": 0.3, "t_c": 0.05},
        "scenarios": [{k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in asdict(sc).items()}
                      for sc in SCENARIOS],
        "assumptions": SCENARIO_ASSUMPTIONS, "origin": "SYNTHETIC",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }, indent=2))
    (OUT / "environment.txt").write_text(
        f"python {platform.python_version()}\nnumpy {np.__version__}\nplatform {platform.platform()}\n"
        f"kisaniti_core.storage {POLICY_VERSION} from {Path(sys.modules['kisaniti_core'].__file__ or '').parent}\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
