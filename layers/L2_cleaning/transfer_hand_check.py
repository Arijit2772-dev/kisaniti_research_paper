"""B.2 transfer (task RESEARCH-B2-TRANSFER-v1): moves the 56 live-portal observations that Codex recorded on 28 Oct 2026 (planning
repository docs/handoff/2026-10-28_AGMARKNET_Reconciliation.md and _Hand_Check.md) into machine-readable research evidence.

  * results/L2_cleaning/hand_check_observations.csv  one row per check ID, with SEPARATE arrival, bound and modal agreement fields,
    the date layout online (blank cell under a dated anchor, or an explicit date) and whether a no-rowspan check is documented
  * results/L2_cleaning/hand_check_sheet.csv         the web_* columns filled; the original columns are untouched
  * results/L2_cleaning/hand_check_summary.json       recomputed counts, hashes before and after, the C.0 blank-date rule evaluation

Every agreement is RECOMPUTED here from the sheet's file values and the live values; the ledger's own labels are only compared.
The checker is an AI agent (Codex, with the human entering each CAPTCHA); the owner's sign-off stays PENDING. A numeric match is not
owner approval, not independent-source verification and not a label of a price as genuine.

    env/run layers/L2_cleaning/transfer_hand_check.py [--planning ../kisaniti]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "L2_cleaning"
SHEET = RES / "hand_check_sheet.csv"
INPUT_SHEET_SHA = "a7e8d80a50bb3ffe78b39add69ac7431a83b15aeadfb5b157305374dc4da5e37"  # recorded by the planning repository before any edit
CHECKER = "Codex (AI agent), live portal, CAPTCHA entered by the owner"
EXPECTED = {"ids": 56, "arrivals_differ": 20, "missing_vs_zero": 4, "union": 23, "numeric_match": 33, "modal_match": 56}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse_ledger(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for ln in text.splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) == 8 and re.fullmatch(r"HC\d\d", c[0]):
            lo = [x.strip() for x in c[6].split("/")]
            if c[0] in out:
                raise SystemExit(f"duplicate ID {c[0]} in the ledger")
            out[c[0]] = {"source_row": c[1], "date_context": c[2], "date_layout": c[3], "export_arrivals": c[4], "live_arrivals": c[5],
                         "live_min": lo[0], "live_max": lo[1], "live_modal": lo[2], "ledger_result": c[7]}
    return out


def rowspan_documented(notes: str) -> set[str]:
    """IDs for which the dated observations say that no rowspan attribute was found."""
    ids: set[str] = set()
    heading = None
    for ln in notes.splitlines():
        m = re.match(r"## (HC\d\d)", ln)
        if m:
            heading = m.group(1)
        if "rowspan" in ln.lower() and ("no rowspan" in ln.lower() or "neither row has a rowspan" in ln.lower() or "without rowspan" in ln.lower()):
            found = set(re.findall(r"HC\d\d", ln))
            for grp in re.findall(r"HC(\d\d)(?:\s*(?:/|and|\+|,)\s*(?:HC)?(\d\d))+", ln):
                found.update(f"HC{g}" for g in grp if g)
            for tail in re.findall(r"HC\d\d\s*/\s*(\d\d)", ln):
                found.add(f"HC{tail}")
            if heading and not found:
                found.add(heading)
            ids |= found
    return ids


def num(s: str) -> float | None:
    s = s.strip()
    return None if s in ("", "-", "NR") else float(s)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--planning", default=str(ROOT.parent / "kisaniti"))
    planning = Path(ap.parse_args().planning) / "docs" / "handoff"
    ledger = parse_ledger((planning / "2026-10-28_AGMARKNET_Reconciliation.md").read_text(encoding="utf-8"))
    notes = (planning / "2026-10-28_AGMARKNET_Hand_Check.md").read_text(encoding="utf-8")
    no_rowspan = rowspan_documented(notes)
    sheet_sha_before = sha(SHEET)
    raw_before = {p.name: sha(p) for p in sorted((ROOT / "data/raw/agmarknet/paddy_basmati").glob("*.csv"))}
    with SHEET.open(newline="", encoding="utf-8") as f:
        sheet = list(csv.DictReader(f))
    first_run = sheet_sha_before == INPUT_SHEET_SHA
    ids = [r["check_id"] for r in sheet]
    if sorted(ids) != sorted(ledger) or len(set(ids)) != EXPECTED["ids"]:
        raise SystemExit(f"IDs differ between the sheet and the ledger: {sorted(set(ids) ^ set(ledger))}")
    obs = []
    for r in sheet:
        L = ledger[r["check_id"]]
        if L["source_row"] != r["row_id"]:
            raise SystemExit(f"{r['check_id']}: source row {L['source_row']} differs from the sheet's {r['row_id']}")
        f_arr, f_min, f_max, f_mod = (num(r[k]) for k in ("arrivals_in_file", "min_in_file", "max_in_file", "modal_in_file"))
        l_arr, l_min, l_max, l_mod = (num(L[k]) for k in ("live_arrivals", "live_min", "live_max", "live_modal"))
        arr_ok = f_arr == l_arr
        modal_ok = f_mod == l_mod
        # a bound that the file holds as missing but the page shows as 0.00 is a representation difference, never a valid zero price
        missing_vs_zero = (f_min is None and l_min == 0) or (f_max is None and l_max == 0)
        min_ok = f_min == l_min
        max_ok = f_max == l_max
        bounds_ok = (min_ok or (f_min is None and l_min == 0)) and (max_ok or (f_max is None and l_max == 0))
        numeric_match = arr_ok and modal_ok and min_ok and max_ok and not missing_vs_zero
        inferred = r["date_inferred"] == "1"
        layout = L["date_layout"]
        under_prev = layout == "blank"
        obs.append({
            "check_id": r["check_id"], "stratum": r["stratum"], "source_row": r["row_id"], "market": r["market_to_find"], "variety": r["variety_in_file"],
            "date_context": L["date_context"], "date_inferred_in_file": int(inferred), "date_layout_online": layout,
            "no_rowspan_documented": "yes" if r["check_id"] in no_rowspan else "unknown",
            "file_arrivals": r["arrivals_in_file"], "live_arrivals": L["live_arrivals"], "arrivals_agree": int(arr_ok),
            "file_min": r["min_in_file"], "live_min": L["live_min"], "file_max": r["max_in_file"], "live_max": L["live_max"],
            "bounds_agree": int(bounds_ok and not missing_vs_zero), "missing_vs_zero": int(missing_vs_zero),
            "file_modal": r["modal_in_file"], "live_modal": L["live_modal"], "modal_agree": int(modal_ok),
            "numeric_match": int(numeric_match), "ledger_result": L["ledger_result"],
            "date_value_matches": 1, "date_layout_differs_from_export": int(inferred != under_prev),
            "checker": CHECKER, "human_signoff": "PENDING",
        })
        # fill the sheet's web_* columns (original columns unchanged)
        r["web_date_shown"] = f"{L['date_context']} ({'blank cell under the dated anchor' if under_prev else 'explicit date'})"
        r["web_arrivals"], r["web_min"], r["web_max"], r["web_modal"] = L["live_arrivals"], L["live_min"], L["live_max"], L["live_modal"]
        r["web_row_shows_under_previous_date_merged_cell_yes_no"] = ("NO (no rowspan documented)" if r["check_id"] in no_rowspan else "UNKNOWN") if under_prev else "n/a (explicit date)"
        r["agrees_yes_no"] = "yes" if numeric_match else "no"
        r["checked_by"], r["checked_on"] = CHECKER, "2026-10-28"
        r["notes"] = L["ledger_result"] + ("; export marks the date inferred, the page shows it explicitly" if inferred != under_prev else "")
    # recomputed counts must equal the ledger's
    counts = {
        "ids": len(obs), "arrivals_differ": sum(not o["arrivals_agree"] for o in obs), "missing_vs_zero": sum(o["missing_vs_zero"] for o in obs),
        "union": sum((not o["arrivals_agree"]) or o["missing_vs_zero"] for o in obs), "numeric_match": sum(o["numeric_match"] for o in obs), "modal_match": sum(o["modal_agree"] for o in obs),
    }
    if counts != EXPECTED:
        raise SystemExit(f"recomputed counts {counts} differ from the ledger's {EXPECTED}")
    # the C.0 section 2 rule (kept for the record; the primary variant is dated_only regardless): of the sheet's rows with an inferred date, how many
    # are confirmed = same date, same prices, shown beneath the preceding date
    inferred_rows = [o for o in obs if o["date_inferred_in_file"]]
    confirmed = [o for o in inferred_rows if o["date_layout_online"] == "blank" and o["modal_agree"] and (o["bounds_agree"] or o["missing_vs_zero"])]
    mine = json.loads((RES / "hand_check_claude_replication_raw.json").read_text())
    same = {k: [v["web"][1], v["web"][2], v["web"][3], v["web"][4]] == [float(next(o for o in obs if o["check_id"] == k)[x]) for x in ("live_arrivals", "live_min", "live_max", "live_modal")] for k, v in mine.items()}
    summary = {
        "recomputed_counts": counts, "ids_unique": len(set(ids)) == 56, "input_sheet_sha256_expected": INPUT_SHEET_SHA, "sheet_sha256_before": sheet_sha_before,
        "first_run_on_unchanged_sheet": first_run, "raw_exports_unchanged": all(sha(ROOT / "data/raw/agmarknet/paddy_basmati" / k) == v for k, v in raw_before.items()), "raw_files": len(raw_before),
        "blank_date_rule_c0": {"rows_with_inferred_date_in_sheet": len(inferred_rows), "confirmed_same_date_same_prices_under_preceding_date": len(confirmed), "threshold": 19,
                               "threshold_met": len(confirmed) >= 19, "not_confirmed": [o["check_id"] for o in inferred_rows if o not in confirmed],
                               "note": "the primary variant is dated_only by the 27 Oct amendment; this evaluation informs the with_blank sensitivity run only. 'Shown beneath the preceding date' is the observed blank cell; merged-cell markup was NOT observed (no rowspan)."},
        "independent_replication": {"rows_replicated_by_claude": len(mine), "live_values_identical_to_codex": sum(same.values()), "differences": [k for k, v in same.items() if not v]},
        "human_signoff": "PENDING", "scope_note": "purposive stratified sample of 56 rows: not an error-rate estimate; a numeric match is not validation of the economic observation",
    }
    out_cols = list(obs[0])
    with (RES / "hand_check_observations.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols, lineterminator="\n")
        w.writeheader()
        w.writerows(obs)
    with SHEET.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sheet[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(sheet)
    summary["sheet_sha256_after"] = sha(SHEET)
    (RES / "hand_check_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
