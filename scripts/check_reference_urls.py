"""Checks that the URL of every bibliography entry without a DOI (government pages, reports, datasheets) still answers, and
records the HTTP status. A page that answers proves it exists, not that it says what the paper cites; the claim checks are in
literature/verification_log.md. Writes literature/url_check.csv.

    python3 -I scripts/check_reference_urls.py
"""

import csv
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "literature" / "references.bib"
OUT = ROOT / "literature" / "url_check.csv"


def main() -> None:
    text = BIB.read_text(encoding="utf-8")
    rows = []
    for m in re.finditer(r"@(\w+)\{([^,\s]+),(.*?)\n\}", text, re.S):
        body = m.group(3)
        if re.search(r"^\s*doi\s*=", body, re.M):
            continue
        u = re.search(r"^\s*url\s*=\s*\{(.*?)\},?\s*$", body, re.M)
        if not u:
            rows.append({"key": m.group(2), "url": "", "status": "NO_URL"})
            continue
        url = u.group(1).replace("\\%", "%").replace("\\_", "_")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (reference check)"})
            with urllib.request.urlopen(req, timeout=40) as r:
                status = str(r.status)
        except urllib.error.HTTPError as e:
            status = str(e.code)
        except Exception as e:  # Python's TLS stack fails on some government hosts: ask curl before calling it a problem
            out = subprocess.run(["curl", "-sIL", "-m", "40", url], capture_output=True, text=True).stdout.splitlines()
            codes = [ln.split()[1] for ln in out if ln.startswith("HTTP/")]
            status = codes[-1] if codes else type(e).__name__
        rows.append({"key": m.group(2), "url": url, "status": status})
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "url", "status"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r["key"], r["status"])


if __name__ == "__main__":
    main()
