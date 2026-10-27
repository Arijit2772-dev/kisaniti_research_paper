import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import transfer_hand_check as t  # noqa: E402

LEDGER = """| Check | Source row | Date context | Date layout | Export arrivals | Live arrivals | Live min / max / modal | Numeric result |
|---|---|---|---|---:|---:|---|---|
| HC01 | 2021-10_punjab.csv:149 | 2021-10-31 | explicit | 1.0 | 1.0 | 700.0 / 900.0 / 800.0 | numeric match |
| HC02 | 2021-10_punjab.csv:193 | 2021-10-30 | explicit | 52.0 | 52.0 | 2990.0 / 0 / 3410.0 | missing bounds vs zero |
| HC04 | 2021-10_punjab.csv:252 | 2021-10-25 | blank | 1700.0 | 850 | 2725.0 / 3240.0 / 3025.0 | arrivals differ |
"""


def test_the_ledger_table_is_parsed_with_all_fields():
    got = t.parse_ledger(LEDGER)
    assert list(got) == ["HC01", "HC02", "HC04"]
    assert got["HC02"]["live_max"] == "0" and got["HC04"]["date_layout"] == "blank" and got["HC04"]["live_arrivals"] == "850"


def test_a_duplicate_id_in_the_ledger_is_refused():
    with pytest.raises(SystemExit, match="duplicate"):
        t.parse_ledger(LEDGER + LEDGER.splitlines()[2] + "\n")


def test_a_missing_value_is_not_a_number_and_a_zero_is_not_a_missing_value():
    assert t.num("") is None and t.num("NR") is None and t.num("0") == 0.0 and t.num("2,5".replace(",", ".")) == 2.5


def test_rowspan_ids_come_from_lines_that_say_no_rowspan():
    notes = "## HC26 — November 2023\nneither row has a rowspan attribute.\nHC39/40 show empty date cells, no rowspan; x\nHC51 has an empty date cell with a rowspan mention but a merged cell was seen"
    got = t.rowspan_documented(notes)
    assert {"HC26", "HC39", "HC40"} <= got and "HC51" not in got
