# Data (not committed)

Layout:

- `raw/agmarknet/<crop>/` — exactly as downloaded
- `processed/` — cleaned data

Every file needs a manifest in `manifests/` recording:

- source and terms;
- who downloaded it and when;
- request scope (state, commodity, variety, dates);
- row count and date range;
- SHA-256 checksum.

The existing Paddy (Common) files are in `~/Documents/sem_6/capstone/`. Phase R0 copies them in and writes their manifests.
