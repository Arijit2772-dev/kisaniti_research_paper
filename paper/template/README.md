# LaTeX template (Springer LNCS / LNNS proceedings)

Decision CHAT-31: the manuscript is written in LaTeX with Springer's proceedings class.

## Where the class files come from

| File | Origin |
|---|---|
| `llncs.cls` (v2.25, 2026/09/03), `splncs04.bst`, `llncsdoc.pdf`, `readme.txt`, `history.txt` | Springer's **LaTeX2e Proceedings Template (ZIP)**, linked from the LNCS "Information for authors and editors" page, <https://link.springer.com/series/558/information-for-authors-and-editors>. Download URL: <https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27851904/data/LaTeX2e%20Proceedings%20Template%20ZIP>, fetched 22 Oct 2026, zip SHA-256 `42afb32ed4fadc9e209134ec65dab1bd2a7ead42f9a3f8abb184f250c4a197b9`. Files copied unchanged. |

The same class serves LNCS, LNNS-style proceedings and the other Springer CS proceedings series. When the venue is chosen (decision D2), check its call for papers for a different template, page limit or required sections, and update this folder.

## Files

| File | Role |
|---|---|
| `main.tex` | Title, authors, packages, draft markers; `\input`s `../sections/*.tex` |
| `make_numbers_tex.py` | Writes `numbers_v2.tex` (macros like `\kn{msp_share_2024}`) and `../tables/table_msp_share.tex` from the v2 result files. Replace its loaders with the v3 results / `paper/numbers.py` when R0/R4 are done |
| `build.sh` | Regenerates the final-mode figures and the numbers, then compiles with Tectonic into `build/main.pdf` |
| `references.bib` | Symlink to `../../literature/references.bib` (owned by the literature phase). Until that file exists, `build.sh` uses `../references/v2_placeholder.bib` (unverified v2 entries) |

## Build

```bash
brew install tectonic
paper/template/build.sh
```

Tectonic downloads the LaTeX packages it needs on the first run. Overleaf also works: upload this folder plus `../sections`, `../tables` and `../figures`.

## Draft markers

`\draftfor{...}` boxes mark text drafted by Claude that an author must rewrite; `\authornote{...}` marks a to-do. Set `\draftmodefalse` in `main.tex` to hide them; before submission there must be none left (`grep -rn 'draftfor\|authornote' paper/sections`).
