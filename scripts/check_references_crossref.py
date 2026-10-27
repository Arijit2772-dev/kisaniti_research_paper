"""Checks every bibliography entry that has a DOI against the Crossref record: does the DOI resolve, and do the title,
year and first author agree? Entries without a DOI are listed for a manual check. Writes
literature/crossref_check.csv. This supports, and does not replace, the opened-and-read verification in
literature/verification_log.md (a matching record proves the reference exists, not that it says what the paper claims).

    python3 -I scripts/check_references_crossref.py
"""

import csv
import difflib
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "paper" / "template" / "references.bib"
OUT = ROOT / "literature" / "crossref_check.csv"


def entries(text: str) -> list[dict[str, str]]:
    out = []
    for m in re.finditer(r"@(\w+)\{([^,\s]+),(.*?)\n\}", text, re.S):
        body = m.group(3)
        def field(name: str) -> str:
            f = re.search(rf"^\s*{name}\s*=\s*[{{\"](.*?)[}}\"],?\s*$", body, re.M | re.S | re.I)
            return re.sub(r"[{}]", "", f.group(1)).strip() if f else ""
        out.append({"key": m.group(2), "type": m.group(1), "doi": field("doi"), "title": field("title"), "year": field("year"), "author": field("author")})
    return out


def norm(s: str) -> str:
    s = re.sub(r"\\[\"'`^~=.uvHckrb]\s*\{?(\w)\}?", r"\1", s)  # LaTeX accents: \"O, \'a, \~n
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"<[^>]+>", "", s.lower())).strip()


def main() -> None:
    rows = []
    for e in entries(BIB.read_text(encoding="utf-8")):
        row = {"key": e["key"], "doi": e["doi"], "status": "", "title_similarity": "", "year_bib": e["year"], "year_crossref": "", "first_author_bib": "", "first_author_crossref": "", "note": ""}
        first = e["author"].split(" and ")[0].split(",")[0].strip() if e["author"] else ""
        row["first_author_bib"] = first
        if not e["doi"]:
            row["status"] = "NO_DOI_MANUAL"
            rows.append(row)
            continue
        url = "https://api.crossref.org/works/" + urllib.parse.quote(e["doi"], safe="/")
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "kisaniti-reference-check (mailto:none)"}), timeout=30) as r:
                msg = json.load(r)["message"]
        except urllib.error.HTTPError as ex:
            msg = None
            if ex.code == 404:  # arXiv and some repositories register with DataCite, not Crossref
                try:
                    with urllib.request.urlopen("https://api.datacite.org/dois/" + urllib.parse.quote(e["doi"], safe="/"), timeout=30) as r:
                        a = json.load(r)["data"]["attributes"]
                    msg = {"title": [(a.get("titles") or [{}])[0].get("title", "")], "years": [str(a.get("publicationYear", ""))],
                           "author": [{"family": (a.get("creators") or [{}])[0].get("familyName", "")}]}
                    row["note"] = "DataCite"
                except Exception:
                    msg = None
            if msg is None:
                row["status"] = f"DOI_NOT_FOUND_{ex.code}"
                rows.append(row)
                continue
        except Exception as ex:  # network problem: not a verdict about the reference
            row["status"] = "CANNOT_CHECK"
            row["note"] = type(ex).__name__
            rows.append(row)
            continue
        title = (msg.get("title") or [""])[0]
        years = msg.get("years") or sorted(
            {str(msg[k]["date-parts"][0][0]) for k in ("issued", "published-print", "published-online", "created") if msg.get(k, {}).get("date-parts") and msg[k]["date-parts"][0][0]}
        )
        year = e["year"] if e["year"] in years else (years[0] if years else "")
        fam = ((msg.get("author") or [{}])[0].get("family") or "")
        sim = difflib.SequenceMatcher(None, norm(title), norm(e["title"])).ratio()
        row.update({"title_similarity": f"{sim:.2f}", "year_crossref": year, "first_author_crossref": fam})
        problems = []
        if sim < 0.85:
            problems.append("title differs")
        if year and e["year"] and year != e["year"]:
            problems.append("year differs")
        if fam and first and norm(fam).replace(" ", "")[:5] != norm(first).replace(" ", "")[:5]:
            problems.append("first author differs")
        row["status"] = "MATCH" if not problems else "CHECK: " + ", ".join(problems)
        rows.append(row)
        time.sleep(0.2)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(Counter(r["status"].split(":")[0] for r in rows))
    for r in rows:
        if r["status"] not in ("MATCH", "NO_DOI_MANUAL"):
            print(r["key"], r["status"], r["title_similarity"], r["year_bib"], r["year_crossref"], r["first_author_bib"], r["first_author_crossref"])


if __name__ == "__main__":
    main()
