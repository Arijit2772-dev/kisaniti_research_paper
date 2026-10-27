"""Prints, for one month of the hand-check sheet, a JavaScript snippet to run in the AGMARKNET result page. The snippet parses
the table text on the page, looks up each sheet row of that month and returns a compact verdict per row (what the page shows,
whether a blank-date row sits under the preceding date's merged cell). The sheet's values are embedded; nothing is sent anywhere.

    python3 scripts/hand_check_js.py 2021-10
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
month = sys.argv[1]
rows = [r for r in csv.DictReader((ROOT / "results/L2_cleaning/hand_check_sheet.csv").open()) if r["month_to_select"] == month]
want = [{"id": r["check_id"], "market": r["market_to_find"], "variety": r["variety_in_file"], "date": r["date_in_file"], "inferred": r["date_inferred"] == "1",
         "arr": r["arrivals_in_file"], "min": r["min_in_file"], "max": r["max_in_file"], "modal": r["modal_in_file"]} for r in rows]
js = """(() => {
const want = %s;
const num = s => { const t = String(s ?? '').replace(/,/g, '').trim(); return t === '' || t === 'NR' ? null : parseFloat(t); };
const lines = document.body.innerText.split('\\n');
let market = null, lastDate = null; const recs = [];
for (const ln of lines) {
  const m = ln.match(/^Market Name : (.*)$/); if (m) { market = m[1].trim(); lastDate = null; continue; }
  const c = ln.split('\\t'); if (c.length < 6 || market === null) continue;
  const hasDate = /^\\d\\d\\/\\d\\d\\/\\d{4}$/.test(c[0].trim());
  if (hasDate) lastDate = c[0].trim().split('/').reverse().join('-');
  else if (c[0].trim() !== '') continue;
  if (!hasDate && lastDate === null) continue;
  recs.push({market, date: lastDate, cont: !hasDate, arr: num(c[1]), variety: c[2].trim(), min: num(c[3]), max: num(c[4]), modal: num(c[5])});
}
const eq = (a, b) => (a === null && (b === '' || b == null)) || (b !== '' && b != null && a !== null && Math.abs(a - parseFloat(b)) < 0.005);
return JSON.stringify({total_records: recs.length, rows: want.map(w => {
  const cand = recs.filter(r => r.market === w.market && r.variety === w.variety && r.date === w.date);
  const hit = cand.find(r => eq(r.arr, w.arr) && eq(r.min, w.min) && eq(r.max, w.max) && eq(r.modal, w.modal));
  const any = hit || cand[0] || null;
  const same = recs.filter(r => r.market === w.market && r.date === w.date);
  const pr = same.filter(r => eq(r.min, w.min) && eq(r.max, w.max) && eq(r.modal, w.modal) && r.variety === w.variety)[0] || any;
  return {id: w.id, inferred: w.inferred, found: !!pr, agrees: !!hit, cont: pr ? pr.cont : null, prices_equal: !!pr && eq(pr.min, w.min) && eq(pr.max, w.max) && eq(pr.modal, w.modal),
          web: pr ? [pr.date, pr.arr, pr.min, pr.max, pr.modal] : null, n: cand.length, rows_that_date: same.length, file_arr: w.arr, market_on_page: recs.some(r => r.market === w.market)};
})});
})()""" % json.dumps(want)
print(js)
