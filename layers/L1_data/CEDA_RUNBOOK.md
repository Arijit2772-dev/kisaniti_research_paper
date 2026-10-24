# CEDA history runbook: basmati, Punjab, 2000–2021

> **On hold (user decision, 24 Oct 2026):** do not email CEDA or register anywhere for now. Use this only if the CEDA website loads later and offers a download. Check with `curl -I https://agmarknet.ceda.ashoka.edu.in`.

24 October 2026 • How to get about 20 more seasons of basmati prices. **You do the access steps (they need your identity and agreement to CEDA's terms); the script files whatever you obtain with checksums.** The script is tested (`test_ceda_fetch.py`, 7 tests against a fake server) but **has not been run against the real CEDA service**, because it needs a token that only CEDA can issue.

## Status on 24 Oct 2026: the web portal does not load

`agmarknet.ceda.ashoka.edu.in` resolves but never answers, from the user's browser and from our machine (checked with curl: no response), while the CEDA main site and the API documentation do load. So the portal may be down or blocked. **Plan A: email CEDA** (draft: [CEDA_EMAIL_DRAFT.md](CEDA_EMAIL_DRAFT.md), address `ceda@ashoka.edu.in` from their contact page) and try the portal again in a few days. **Plan B:** the data.gov.in "Current Daily Price of Various Commodities from Various Markets (Mandi)" resource lists data from 2013 to 2025 and offers an API on request ([page](https://data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi)); I could not confirm that it holds Punjab variety-wise history for 2013–2020, so this must be tested once the user has a key. **Plan C:** if neither works, Paper 1 keeps its current scope (a small pre-registered forecasting comparison, effect sizes with intervals, exploratory hold-or-sell) and the long-history work moves to Paper 2.

## What CEDA is, and what it is not

- CEDA (Centre for Economic Data and Analysis, Ashoka University) republishes the same AGMARKNET data from **2000 onward**, harmonised, for 300+ commodities and 2,700+ mandis, updated monthly ([CEDA Agri Market Data](https://agmarknet.ceda.ashoka.edu.in)). It adds history, **not an independent source**.
- Its API records have **no variety field**: per market and day only the commodity, min, max and modal price (quantities come from a separate call). So the long history is **commodity-level basmati**, not 1121 vs 1509 separately. That is still what the model comparison needs: a long daily series. The variety split stays available only from 2021 (our AGMARKNET files).
- The overlap years (2021–2026) let us compare CEDA with our own AGMARKNET downloads: a free cross-source check.

## Steps for you

1. In your normal browser open <https://agmarknet.ceda.ashoka.edu.in> (our in-app browser is blocked from this address). Read the **README** page: it states what was cleaned and the terms of use and citation. Note the citation text.
2. Look for a raw-file **download** option for *Paddy (Basmati)* or *Basmati Rice*, state *Punjab*, 2000–2021.
   - **If a download is offered:** save the files, then run `python3 layers/L1_data/ceda_fetch.py ingest-file <files…>`.
   - **If only charts are offered, use the API:** open <https://api.ceda.ashoka.edu.in/documentation/>; it uses a bearer token (JWT). The pages I could reach do not say how to get a token. Use the *Contact Us* page at <https://ceda.ashoka.edu.in> and ask for API access for research on mandi prices (mention Thapar Institute and the paper). I did not find a self-service sign-up, and I will not guess a contact address.
3. When you have a token, put it in your **terminal only**, never in chat or in a file:

```bash
export CEDA_API_TOKEN='paste-token-here'
```

4. Find the ids (writes the reference lists into `data/raw/ceda/_reference/`):

```bash
cd ~/Documents/kisaniti_research_paper && python3 layers/L1_data/ceda_fetch.py discover
```

5. Download prices and quantities, one file per year, with manifests (replace the ids printed above; the date range ends at the start of our own data):

```bash
python3 layers/L1_data/ceda_fetch.py fetch --commodity-id ID --state-id ID --from 2000-01-01 --to 2021-08-31 --quantities
```

6. Market names (needed to read `market_id`):

```bash
python3 layers/L1_data/ceda_fetch.py markets --commodity-id ID --state-id ID
```

7. Tell the next session it is done; it will compare CEDA with the AGMARKNET overlap (2021–2026) and build the long series.

## Safety rules built into the script

- Token only from `CEDA_API_TOKEN`; never printed, logged or stored (a test checks this).
- Responses are saved byte for byte, with a manifest holding request, SHA-256, record count and date range; existing files are never overwritten without `--force`.
- Three attempts per request on rate limits or server errors, honouring `Retry-After`; refusal (401/400) stops the run. No bypassing of limits or access controls.
- `data/raw/` stays out of Git; manifests are committed.

## What to expect and check

- Long gaps in off-season months (the market is seasonal).
- A different count of mandis and possibly different prices from AGMARKNET (harmonisation); we measure the difference on 2021–2026 before using the old years.
- Redistribution terms: CEDA's README governs; publish scripts and manifests, not their data, unless the terms allow it.
