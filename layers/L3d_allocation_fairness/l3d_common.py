"""Shared pieces of the L3d experiments: the SYNTHETIC 300-member Patiala persona, the REAL 2025 paddy price
panel, instance building, research baselines (nearest mandi, independent choice) and scoring.

Origins of every input (shown in every results file):
  REAL       AGMARKNET Paddy(Common) 2025 modal prices (data/processed, manifest in data/manifests);
             mandi coordinates from OpenStreetMap (legacy/v2_from_rp_kisan/experiments/mandi_coordinates.csv)
  POLICY     MSP 2025-26 for paddy Grade A, Rs 2,389 per quintal (planning price, CHAT-20)
  SYNTHETIC  farmers, villages, land, lot sizes, harvest weeks, storage categories, transport and waiting
             rates, road factor, mandi-day limits (DEMO assumptions, PATIALA_FPO_PROFILE_APPROX / CHAT-25)
The optimizer, oracle, validator and objective all come from kisaniti_core (one shared core, CHAT-28).
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

import numpy as np
import pandas as pd
from kisaniti_core.allocation import (
    AllocationInput,
    AllocationMode,
    Choice,
    Lot,
    MarketLoad,
    Plan,
    StorageCategory,
    evaluate,
    gini,
)
from kisaniti_core.allocation.model import Assignment
from kisaniti_core.ids import fixture_id
from kisaniti_core.provenance import Mode, Origin
from kisaniti_core.quantity import Quantity, RatePerKg

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "L3d_allocation"
PRICES_CSV = ROOT / "data" / "processed" / "agmarknet" / "paddy_common" / "agmarknet_paddy_common_punjab_cleaned_records.csv"
COORDS_CSV = ROOT / "legacy" / "v2_from_rp_kisan" / "experiments" / "mandi_coordinates.csv"
NS = "kisaniti-l3d-patiala-persona"

# ---- settings (DEMO assumptions unless marked) ------------------------------------------------------------
CANDIDATES = ["Patiala(New Anaj Mandi) APMC", "Patran APMC", "Bhawanigarh APMC", "Chanarthal APMC", "Amargarh APMC"]
MSP_2025_INR_PER_Q = Decimal("2389.00")  # POLICY: paddy Grade A MSP, KMS 2025-26 (same value as paper v2)
SEASON = 2025
MEMBERS = 300  # CHAT-25 persona (scheme minimum in the plains)
VILLAGES = 20
HARVEST_WEEKS = 6  # members' paddy becomes ready over six weeks (DEMO)
FIRST_WEEK = date(2025, 10, 6)  # Monday; Punjab procurement runs from 1 October (DEMO choice of start)
HORIZON_DATES = 5  # plan the next five trading dates (as in paper v2)
INCREMENT_Q = 1  # plan in whole quintals (DEMO)
YIELD_Q_PER_HA = 65  # ESTIMATE, not verified for the paper
LAND_HA = (1.0, 10.0)  # ESTIMATE range from the persona; median about 3 ha
CENTRE = (30.25, 76.20)  # synthetic FPO area between Patiala and Bhawanigarh, about 30 km x 30 km (paper v2)
ROAD_FACTOR = Decimal("1.3")  # road / straight-line distance (paper v2 assumption)
BASE = {"rate": Decimal("2"), "wait": Decimal("2"), "cap_q": 300}  # Rs/q-km, Rs/q per day of waiting, q per mandi-day
STORAGE_MIX = [(StorageCategory.HIGH, 0.2), (StorageCategory.MEDIUM, 0.3), (StorageCategory.LOW, 0.3),
               (StorageCategory.UNKNOWN, 0.2)]  # SYNTHETIC assessment fixture (handoff §5 allows this for tests)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


# ---- persona -------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Member:
    farmer_id: str
    lot_id: str
    village: int
    lat: float
    lon: float
    land_ha: float
    paddy_q: int
    harvest_week: int
    storage: StorageCategory


def make_persona(seed: int, members: int = MEMBERS) -> list[Member]:
    """SYNTHETIC: 300 members in 20 villages; one MSP-paddy lot per member (fixed-price path)."""
    rng = random.Random(seed)
    villages = [(CENTRE[0] + rng.uniform(-0.135, 0.135), CENTRE[1] + rng.uniform(-0.155, 0.155)) for _ in range(VILLAGES)]
    out = []
    cats, weights = zip(*STORAGE_MIX, strict=True)
    for i in range(members):
        v = rng.randrange(VILLAGES)
        lat = villages[v][0] + rng.uniform(-0.009, 0.009)  # about +/- 1 km around the village
        lon = villages[v][1] + rng.uniform(-0.010, 0.010)
        land = min(LAND_HA[1], max(LAND_HA[0], rng.lognormvariate(math.log(3.0), 0.55)))
        out.append(Member(fixture_id(NS, "mbr", f"{seed}-{i}"), fixture_id(NS, "lot", f"{seed}-{i}"), v, lat, lon,
                          round(land, 2), max(1, round(land * YIELD_Q_PER_HA)), rng.randrange(HARVEST_WEEKS),
                          rng.choices(cats, weights)[0]))
    return out


# ---- real prices ---------------------------------------------------------------------------------------------
def price_panel(season: int = SEASON) -> tuple[list[date], dict[tuple[str, date], Decimal]]:
    """REAL: arrival-weighted modal price per mandi and trading date (Rs/q, rounded to paise), season `season`.
    Trading dates are dates on which at least one candidate mandi reported. A mandi without a report on a
    date takes its last earlier report in the season (no look-ahead); before its first report, the MSP."""
    d = pd.read_csv(PRICES_CSV, parse_dates=["arrival_date"])
    d = d[(d.year == season) & d.market_name.isin(CANDIDATES)].copy()
    d["w"] = d.arrivals_metric_tonnes.where(d.arrivals_metric_tonnes > 0, 0.0)
    rows = {}
    for (day, m), g in d.groupby(["arrival_date", "market_name"]):
        p = (g.w * g.modal_price_rs_per_quintal).sum() / g.w.sum() if g.w.sum() > 0 else g.modal_price_rs_per_quintal.mean()
        rows[(m, day.date())] = Decimal(str(p)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    dates = sorted({k[1] for k in rows})
    filled: dict[tuple[str, date], Decimal] = {}
    for m in CANDIDATES:
        last = MSP_2025_INR_PER_Q
        for day in dates:
            last = rows.get((m, day), last)
            filled[(m, day)] = last
    return dates, filled


def mandi_coords() -> dict[str, tuple[float, float]]:
    c = pd.read_csv(COORDS_CSV).set_index("market_name")
    return {m: (float(c.loc[m, "lat"]), float(c.loc[m, "lon"])) for m in CANDIDATES}


# ---- instances -----------------------------------------------------------------------------------------------
@dataclass
class Instance:
    inp: AllocationInput
    actual_net: dict[tuple[str, str, date], int]  # net 1/10,000 Rs per kg at ACTUAL prices
    km: dict[tuple[str, str], float]  # (lot, mandi) road km
    mandi_name: dict[str, str]
    members: list[Member]
    week: int
    origin: date


def per_kg(rs_per_q: Decimal) -> RatePerKg:
    return RatePerKg.from_decimal((rs_per_q / 100).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN))


def build_instance(persona: list[Member], week: int, trading_dates: list[date],
                   prices: dict[tuple[str, date], Decimal], coords: dict[str, tuple[float, float]],
                   rate: Decimal = BASE["rate"], wait: Decimal = BASE["wait"], cap_q: int = BASE["cap_q"],
                   seed: int = 0, mandis: list[str] | None = None, planning: str = "msp") -> Instance:
    """Weekly plan: members whose paddy is ready in `week`, the next HORIZON_DATES trading dates from the
    week's Monday, every candidate mandi admissible, planning price = MSP (or the actual price when
    planning="actual": the perfect-foresight bound), scored later at actual prices."""
    mandis = mandis or CANDIDATES
    start = FIRST_WEEK.toordinal() + 7 * week
    horizon = [d for d in trading_dates if d.toordinal() >= start][:HORIZON_DATES]
    members = [m for m in persona if m.harvest_week == week]
    mid = {name: fixture_id(NS, "mnd", name) for name in mandis}
    lots, choices, actual, kms = [], [], {}, {}
    inc = Quantity.from_quintals(INCREMENT_Q)
    msp = per_kg(MSP_2025_INR_PER_Q)
    for mem in members:
        lots.append(Lot(mem.lot_id, mem.farmer_id, Quantity.from_quintals(mem.paddy_q), inc, mem.storage))
        for name in mandis:
            road = (ROAD_FACTOR * Decimal(str(haversine_km((mem.lat, mem.lon), coords[name])))).quantize(Decimal("0.01"))
            kms[(mem.lot_id, mid[name])] = float(road)
            for di, day in enumerate(horizon):
                cost = per_kg(rate * road + wait * di)
                price = msp if planning == "msp" else per_kg(prices[(name, day)])
                c = Choice(mem.lot_id, mid[name], day, price, cost)
                choices.append(c)
                actual[c.key] = per_kg(prices[(name, day)]).units - cost.units
    caps = {(mid[n], d): Quantity.from_quintals(cap_q) for n in mandis for d in horizon}
    inp = AllocationInput(fixture_id(NS, "fpo", seed), fixture_id(NS, "cmd", "paddy-common"), Mode.RESEARCH,
                          Origin.SYNTHETIC, AllocationMode.PARTIAL, MarketLoad.STRICT, tuple(horizon), tuple(mid.values()),
                          tuple(m.farmer_id for m in members), tuple(lots), tuple(choices), caps)
    return Instance(inp, actual, kms, {v: k for k, v in mid.items()}, members, week, horizon[0])


# ---- research baselines (not product algorithms) ----------------------------------------------------------------
def nearest_fcfs(inst: Instance, seed: int) -> Plan:
    """P1: lots arrive in random order; each goes to its nearest mandi on the first date with room, then the
    next nearest, filling what fits (partial loads allowed); the rest stays unsold this week."""
    inp = inst.inp
    rng = random.Random(seed)
    load: dict[tuple[str, date], int] = defaultdict(int)
    n: dict[tuple[str, str, date], int] = defaultdict(int)
    order = list(inp.lots)
    rng.shuffle(order)
    for lot in order:
        left = lot.max_increments
        inc = lot.increment.units
        for mnd in sorted(inp.mandis, key=lambda m: (inst.km[(lot.id, m)], m)):
            for d in inp.dates:
                room = (inp.capacities[(mnd, d)].units - load[(mnd, d)]) // inc
                take = min(left, room)
                if take > 0:
                    n[(lot.id, mnd, d)] += take
                    load[(mnd, d)] += take * inc
                    left -= take
                if left == 0:
                    break
            if left == 0:
                break
    return Plan.from_increments(inp, n)


def independent_best(inst: Instance) -> Plan:
    """P2: every lot sends everything to its own best (mandi, date) at planning prices, ignoring others."""
    inp = inst.inp
    best: dict[str, Choice] = {}
    for c in inp.choices_canonical:
        if c.lot_id not in best or c.net_units > best[c.lot_id].net_units:
            best[c.lot_id] = c
    return Plan(tuple(Assignment(c.lot_id, c.mandi_id, c.date, inp.lot(c.lot_id).increment * inp.lot(c.lot_id).max_increments)
                      for c in best.values()))


# ---- scoring -------------------------------------------------------------------------------------------------
def score(inst: Instance, plan: Plan) -> dict[str, float]:
    """Exact objective at planning and at actual prices, plus fairness and storage metrics (floats for tables)."""
    inp = inst.inp
    plan_obj = evaluate(inp, plan)
    act = evaluate(inp, plan, net_override=inst.actual_net)
    supply_q = sum(lot.quantity.units for lot in inp.lots) / 100_000
    alloc_q = plan_obj.allocated_g / 100_000
    fr = plan_obj.fulfilment_sorted
    high = [lot.id for lot in inp.lots if lot.storage is StorageCategory.HIGH]
    high_q = sum(inp.lot(i).quantity.units for i in high) / 100_000
    high_first = sum(a.quantity.units for a in plan.assignments if a.lot_id in high and a.date == inp.dates[0]) / 100_000
    load: dict[tuple[str, date], int] = defaultdict(int)
    for a in plan.assignments:
        load[(a.mandi_id, a.date)] += a.quantity.units
    over = [q - inp.capacities[k].units for k, q in load.items() if q > inp.capacities[k].units]
    km = sum(a.quantity.units * inst.km[(a.lot_id, a.mandi_id)] for a in plan.assignments) / max(1, plan_obj.allocated_g)
    return {
        "farmers": len(inp.farmers), "supply_q": supply_q, "allocated_q": alloc_q, "allocated_pct": 100 * alloc_q / supply_q,
        "expected_net_rs": float(plan_obj.net_return_inr), "actual_net_rs": float(act.net_return_inr),
        "expected_net_rs_per_q": float(plan_obj.net_return_inr) / alloc_q if alloc_q else float("nan"),
        "actual_net_rs_per_q": float(act.net_return_inr) / alloc_q if alloc_q else float("nan"),
        "min_fulfilment_pct": 100 * float(fr[0]) if fr else float("nan"),
        "p10_fulfilment_pct": 100 * float(np.percentile([float(x) for x in fr], 10)) if fr else float("nan"),
        "zero_fulfilment_farmers": sum(1 for x in fr if x == 0),
        "gini_fulfilment": gini(fr),
        "high_storage_first_date_pct": 100 * high_first / high_q if high_q else float("nan"),
        "avg_km": km, "limit_violations": len(over), "excess_q": sum(over) / 100_000,
    }
