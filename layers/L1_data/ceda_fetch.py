"""Fetch and file CEDA Agmarknet history (Ashoka University) with checksums.

CEDA republishes AGMARKNET data from 2000 onward in a harmonised form, at commodity
level (records carry market, date, min/max/modal price and, separately, quantity;
there is NO variety field). Spec read from https://api.ceda.ashoka.edu.in/documentation/
on 24 Oct 2026; the API needs a bearer token (JWT) obtained from CEDA.

Commands (python3 layers/L1_data/ceda_fetch.py <command> ...):
  discover                       list commodities matching 'basmati'/'paddy' and the Punjab state id
  markets  --commodity-id N --state-id N --indicator price|quantity
                                 save the market-id -> market-name list for every district
  fetch    --commodity-id N --state-id N --from 2000-01-01 --to 2021-12-31 [--quantities]
                                 save prices (and optionally quantities), one file per calendar year
  ingest-file PATH [PATH ...]    file files downloaded by hand from the CEDA web portal

Rules:
  * The token is read from the environment variable CEDA_API_TOKEN, never from the
    command line, never printed, never written to a manifest.
  * Responses are saved byte for byte; a manifest (request, sha256, record count, date range)
    sits beside each file. Existing files are not overwritten without --force.
  * At most 3 attempts per request on 429/5xx, honouring Retry-After. 401/400 stop the run.
    No CAPTCHA, rate-limit or access-control bypass of any kind.
  * Check CEDA's terms of use and cite CEDA when publishing.
Set CEDA_API_BASE to point at a test server.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "ceda"
BASE = os.environ.get("CEDA_API_BASE", "https://api.ceda.ashoka.edu.in/v1").rstrip("/")
SOURCE = "CEDA API v1 (Centre for Economic Data and Analysis, Ashoka University), derived from AGMARKNET"
MAX_ATTEMPTS = 3


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request(method: str, path: str, body: dict | None = None) -> tuple[bytes, int]:
    token = os.environ.get("CEDA_API_TOKEN", "").strip()
    if not token:
        sys.exit("Set CEDA_API_TOKEN in your terminal first (the token is never taken from arguments).")
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read(), resp.status
        except urllib.error.HTTPError as err:
            if err.code in (400, 401, 403, 404):
                sys.exit(f"CEDA API refused the request ({err.code}) for {method} {path}: "
                         f"{'check the token' if err.code in (401, 403) else 'check the parameters'}")
            if err.code == 429 or err.code >= 500:
                if attempt == MAX_ATTEMPTS:
                    sys.exit(f"Giving up on {path} after {MAX_ATTEMPTS} attempts (HTTP {err.code})")
                wait = int(err.headers.get("Retry-After", "0") or 0) or 5 * attempt
                print(f"  HTTP {err.code}; waiting {wait}s (attempt {attempt}/{MAX_ATTEMPTS})")
                time.sleep(wait)
                continue
            raise
        except urllib.error.URLError as err:
            if attempt == MAX_ATTEMPTS:
                sys.exit(f"Network error for {path}: {err.reason}")
            time.sleep(5 * attempt)
    raise RuntimeError("unreachable")


def save(path: Path, payload: bytes, manifest: dict, force: bool) -> bool:
    if path.exists() and not force:
        print(f"  exists, skipped: {path.relative_to(ROOT)}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    manifest = {**manifest, "source": SOURCE, "raw_path": str(path.relative_to(ROOT)),
                "sha256": sha256(payload), "bytes": len(payload), "origin": "REAL",
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    path.with_suffix(path.suffix + ".manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return True


def records(payload: bytes) -> list:
    try:
        data = json.loads(payload).get("data", [])
        return data if isinstance(data, list) else []
    except (ValueError, AttributeError):
        return []


def cmd_discover(args) -> None:
    body, _ = request("GET", "/agmarknet/commodities")
    save(OUT / "_reference" / "commodities.json", body, {"request": "GET /agmarknet/commodities"}, True)
    for item in json.loads(body).get("commodities", []):
        if re.search(r"basmati|paddy|rice", item["name"], re.I):
            print(f"commodity {item['id']:>4}  {item['name']}")
    body, _ = request("GET", "/agmarknet/geographies")
    save(OUT / "_reference" / "geographies.json", body, {"request": "GET /agmarknet/geographies"}, True)
    for state in json.loads(body).get("geographies", []):
        if re.search(r"punjab", state["state_name"], re.I):
            print(f"state     {state['state_id']:>4}  {state['state_name']}  ({len(state.get('districts', []))} districts)")


def cmd_markets(args) -> None:
    geo = json.loads((OUT / "_reference" / "geographies.json").read_text())
    state = next(s for s in geo["geographies"] if s["state_id"] == args.state_id)
    for district in state["districts"]:
        body, _ = request("POST", "/agmarknet/markets", {
            "commodity_id": args.commodity_id, "state_id": args.state_id,
            "district_id": district["district_id"], "indicator": args.indicator})
        req = {"commodity_id": args.commodity_id, "state_id": args.state_id,
               "district_id": district["district_id"], "indicator": args.indicator}
        path = OUT / f"c{args.commodity_id}_s{args.state_id}" / "markets" / f"district_{district['district_id']}.json"
        if save(path, body, {"request": req}, args.force):
            print(f"  district {district['district_name']}: {len(records(body))} markets")


def years(start: date, end: date):
    year = start.year
    while year <= end.year:
        yield max(start, date(year, 1, 1)), min(end, date(year, 12, 31))
        year += 1


def cmd_fetch(args) -> None:
    start, end = date.fromisoformat(args.from_date), date.fromisoformat(args.to_date)
    kinds = ["prices"] + (["quantities"] if args.quantities else [])
    for kind in kinds:
        for first, last in years(start, end):
            req = {"commodity_id": args.commodity_id, "state_id": args.state_id,
                   "from_date": first.isoformat(), "to_date": last.isoformat()}
            path = OUT / f"c{args.commodity_id}_s{args.state_id}" / kind / f"{kind}_{first.year}.json"
            if path.exists() and not args.force:
                print(f"  exists, skipped: {path.relative_to(ROOT)}")
                continue
            body, _ = request("POST", f"/agmarknet/{kind}", req)
            recs = records(body)
            days = sorted(r["date"] for r in recs if "date" in r)
            save(path, body, {"request": req, "records": len(recs),
                              "first_date": days[0] if days else None, "last_date": days[-1] if days else None,
                              "markets": len({r.get("market_id") for r in recs})}, args.force)
            print(f"  {kind} {first.year}: {len(recs)} records, {len({r.get('market_id') for r in recs})} markets")
            time.sleep(args.pause)


def cmd_ingest_file(args) -> None:
    dest = OUT / "portal"
    for name in args.paths:
        src = Path(name).expanduser()
        data = src.read_bytes()
        target = dest / src.name
        if target.exists() and sha256(target.read_bytes()) == sha256(data):
            print(f"Already filed (same bytes): {target.relative_to(ROOT)}")
            continue
        if target.exists():
            sys.exit(f"CONFLICT: {target} exists with different bytes; not overwritten")
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        manifest = {"source": "CEDA Agri Market Data web portal download, by hand",
                    "original_filename": src.name, "raw_path": str(target.relative_to(ROOT)),
                    "sha256": sha256(data), "bytes": len(data), "origin": "REAL",
                    "filed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "lines": data.count(b"\n")}
        target.with_suffix(target.suffix + ".manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
        print(f"Filed {target.relative_to(ROOT)} ({len(data):,} bytes, sha256 {manifest['sha256'][:16]})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("discover").set_defaults(func=cmd_discover)
    m = sub.add_parser("markets")
    m.add_argument("--commodity-id", type=int, required=True)
    m.add_argument("--state-id", type=int, required=True)
    m.add_argument("--indicator", choices=["price", "quantity"], default="price")
    m.add_argument("--force", action="store_true")
    m.set_defaults(func=cmd_markets)
    f = sub.add_parser("fetch")
    f.add_argument("--commodity-id", type=int, required=True)
    f.add_argument("--state-id", type=int, required=True)
    f.add_argument("--from", dest="from_date", required=True)
    f.add_argument("--to", dest="to_date", required=True)
    f.add_argument("--quantities", action="store_true")
    f.add_argument("--pause", type=float, default=1.0, help="seconds between requests")
    f.add_argument("--force", action="store_true")
    f.set_defaults(func=cmd_fetch)
    i = sub.add_parser("ingest-file")
    i.add_argument("paths", nargs="+")
    i.set_defaults(func=cmd_ingest_file)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
