"""Simulated sensor streams for stored basmati paddy on a Patiala farm (CHAT-32).

Everything here is SYNTHETIC. The streams test how storage rules behave (stability, outages, placement, sensor
error); they are not measurements and do not show that any rule predicts spoilage.

Climate: IMD 1991–2020 normals for Patiala (monthly mean daily max/min temperature and mean relative humidity at
17:30 IST), as tabulated on the Patiala Wikipedia page (secondary source, read 22 Oct 2026). We use the 17:30 RH as
the daily mean RH, which is an approximation recorded in SCENARIO_ASSUMPTIONS.

In-grain model (assumptions, not measured):
* in-grain temperature = ambient temperature passed through a first-order low-pass filter (time constant 2 days),
  which damps the daily swing to under a tenth and delays it, as the centre of a bag would;
* in-grain water activity a_w follows d a_w/dt = (RH_daily_mean/100 - a_w) / tau, i.e. the grain slowly exchanges
  moisture with shed air through the jute bag; tau is set per scenario;
* the probe reads RH = 100 * a_w (inter-granular air at equilibrium, Part B1) plus sensor noise and bias.
No moisture-isotherm constants are used (Part B1: none verified).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import numpy as np

# IMD 1991-2020 normals, Patiala: month -> (mean daily max C, mean daily min C, mean RH % at 17:30 IST)
PATIALA_NORMALS = {
    1: (18.7, 6.7, 70), 2: (22.5, 9.5, 62), 3: (28.0, 14.1, 53), 4: (35.2, 19.3, 33),
    5: (39.3, 24.2, 32), 6: (38.3, 26.5, 46), 7: (34.4, 27.0, 69), 8: (33.4, 26.3, 75),
    9: (33.1, 24.3, 71), 10: (32.6, 18.2, 59), 11: (27.7, 11.9, 59), 12: (21.2, 7.8, 69),
}
CLIMATE_SOURCE = (
    "IMD 1991-2020 normals for Patiala as tabulated on en.wikipedia.org/wiki/Patiala (climate box), read 22 Oct 2026"
)

SAMPLE = timedelta(minutes=5)
IST = timedelta(hours=5, minutes=30)
RH_DIURNAL_AMPLITUDE = 15.0  # +/- points of shed-air RH over a day (assumption)
GRAIN_T_TAU_DAYS = 2.0

SCENARIO_ASSUMPTIONS = {
    "climate": CLIMATE_SOURCE,
    "daily_mean_rh": "IMD 17:30 IST RH used as the daily mean (approximation)",
    "rh_diurnal_amplitude_points": RH_DIURNAL_AMPLITUDE,
    "temperature_diurnal": "sinusoid between monthly mean daily min and max, peak at 15:00 IST",
    "grain_temperature": f"ambient low-pass, time constant {GRAIN_T_TAU_DAYS} days",
    "grain_aw": "first-order exchange with daily-mean shed RH, scenario time constant tau",
    "probe": "RH = 100 * a_w + noise + bias; temperature = grain temperature + noise + bias",
}


def _month_mid(year: int, month: int) -> datetime:
    start = datetime(year, month, 1, tzinfo=UTC)
    nxt = datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=UTC)
    return start + (nxt - start) / 2


def _interp_normals(times: list[datetime]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Daily max, min and RH interpolated linearly between mid-month anchors."""
    years = {t.year for t in times}
    anchors = []
    for y in range(min(years) - 1, max(years) + 2):
        for m in range(1, 13):
            anchors.append((_month_mid(y, m).timestamp(), *PATIALA_NORMALS[m]))
    a = np.array(anchors)
    ts = np.array([t.timestamp() for t in times])
    return tuple(np.interp(ts, a[:, 0], a[:, i]) for i in (1, 2, 3))  # type: ignore[return-value]


def _lowpass(x: np.ndarray, dt_days: float, tau_days: float, x0: float | None = None) -> np.ndarray:
    out = np.empty_like(x)
    k = dt_days / tau_days
    y = x[0] if x0 is None else x0
    for i, v in enumerate(x):
        y += k * (v - y)
        out[i] = y
    return out


@dataclass
class Scenario:
    key: str
    title: str
    start: datetime
    days: int
    aw0: float  # in-grain water activity at insertion
    tau_days: float  # moisture exchange time constant of the bag
    placement: str = "IN_GRAIN"
    drying_day: float | None = None  # S3: lot sun-dried on this day
    aw_after_drying: float | None = None
    hover: bool = False  # S6: a_w forced to wobble around 0.65
    outages: list[tuple[float, float, str]] = field(default_factory=list)  # (start_day, hours, "WIFI"|"POWER")
    note: str = ""


SCENARIOS = [
    Scenario("S1_winter_dry", "Dry basmati held Nov-Feb", datetime(2025, 11, 15, tzinfo=UTC), 105, 0.60, 60.0,
             note="Dried basmati, cool months; ambient RH 59-70%"),
    Scenario("S2_monsoon_hold", "Basmati held into the monsoon", datetime(2026, 6, 1, tzinfo=UTC), 122, 0.62, 30.0,
             note="Held through Jun-Sep; jute bag absorbs monsoon humidity"),
    Scenario("S3_fresh_wet", "Freshly harvested, then sun-dried", datetime(2025, 10, 20, tzinfo=UTC), 30, 0.88,
             30.0, drying_day=8.0, aw_after_drying=0.63, note="Harvest moisture, dried on day 8"),
    Scenario("S4_outages", "Monsoon hold with outages", datetime(2026, 7, 1, tzinfo=UTC), 45, 0.64, 30.0,
             outages=[(10.0, 30.0, "WIFI"), (25.0, 6.0, "POWER"), (35.0, 2.0, "WIFI")],
             note="Wi-Fi off 30 h (buffer overflows), power cut 6 h, Wi-Fi off 2 h"),
    Scenario("S5_open_air", "Probe hung in shed air", datetime(2025, 10, 20, tzinfo=UTC), 40, 0.62, 45.0,
             placement="AMBIENT", note="Same lot, probe outside the grain"),
    Scenario("S6_boundary", "Grain near the 0.65 limit", datetime(2026, 2, 1, tzinfo=UTC), 60, 0.65, 45.0,
             hover=True, note="a_w wobbles +/-0.01 around 0.65"),
]


@dataclass
class Stream:
    """One simulated run: true values, what the probe reports, and when each sample reaches the server."""

    times: list[datetime]
    ambient_t: np.ndarray
    ambient_rh: np.ndarray
    grain_t: np.ndarray
    grain_aw: np.ndarray
    probe_t: np.ndarray
    probe_rh: np.ndarray
    received: list[datetime | None]  # None = sample lost


def simulate(sc: Scenario, seed: int, rh_bias: float = 0.0, t_bias: float = 0.0,
             rh_noise: float = 0.3, t_noise: float = 0.05) -> Stream:
    rng = np.random.default_rng(seed)
    warmup = timedelta(days=20)  # let the grain temperature filter settle before insertion
    n_warm = int(warmup / SAMPLE)
    n = int(timedelta(days=sc.days) / SAMPLE) + 1
    all_times = [sc.start - warmup + i * SAMPLE for i in range(n_warm + n)]
    tmax, tmin, rh_mean = _interp_normals(all_times)
    hours_local = np.array([((t + IST).hour + (t + IST).minute / 60) for t in all_times])
    phase = np.sin(2 * np.pi * (hours_local - 9.0) / 24.0)  # +1 at 15:00 IST
    amb_t = (tmax + tmin) / 2 + (tmax - tmin) / 2 * phase
    amb_rh = np.clip(rh_mean - RH_DIURNAL_AMPLITUDE * phase, 5, 100)
    dt_days = SAMPLE / timedelta(days=1)
    grain_t = _lowpass(amb_t, dt_days, GRAIN_T_TAU_DAYS)[n_warm:]
    amb_t, amb_rh, rh_mean = amb_t[n_warm:], amb_rh[n_warm:], rh_mean[n_warm:]
    times = all_times[n_warm:]

    aw = np.empty(n)
    a = sc.aw0
    k = dt_days / sc.tau_days
    for i in range(n):
        day = i * dt_days
        if sc.drying_day is not None and sc.aw_after_drying is not None and sc.drying_day <= day < sc.drying_day + 1:
            a += (sc.aw_after_drying - a) * dt_days * 4  # sun-drying pulls a_w down within about a day
        a += k * (rh_mean[i] / 100 - a)
        aw[i] = a
    if sc.hover:
        days = np.arange(n) * dt_days
        aw = 0.65 + 0.01 * np.sin(2 * np.pi * days / 5.0) + 0.002 * np.sin(2 * np.pi * days / 1.3)

    if sc.placement == "AMBIENT":
        seen_t, seen_rh = amb_t, amb_rh
    else:
        seen_t, seen_rh = grain_t, 100 * aw
    probe_t = seen_t + t_bias + rng.normal(0, t_noise, n)
    probe_rh = np.clip(seen_rh + rh_bias + rng.normal(0, rh_noise, n), 0, 100)
    received = _delivery(times, sc.outages)
    return Stream(times, amb_t, amb_rh, grain_t, aw, probe_t, probe_rh, received)


def _delivery(times: list[datetime], outages: list[tuple[float, float, str]], buffer: int = 288,
              latency: timedelta = timedelta(seconds=2)) -> list[datetime | None]:
    """Receipt time of each sample under the firmware v1 rules: during a Wi-Fi outage samples wait in a 288-sample RAM
    buffer (oldest dropped on overflow) and are sent at reconnect; during a power cut no samples are taken."""
    out: list[datetime | None] = [t + latency for t in times]
    t0 = times[0]
    for start_day, hours, kind in outages:
        s, e = t0 + timedelta(days=start_day), t0 + timedelta(days=start_day, hours=hours)
        idx = [i for i, t in enumerate(times) if s <= t < e]
        if kind == "POWER":
            for i in idx:
                out[i] = None
        else:
            kept = idx[-buffer:]
            for i in idx:
                out[i] = e + latency if i in kept else None
    return out
