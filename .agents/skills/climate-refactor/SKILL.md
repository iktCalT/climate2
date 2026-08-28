---
name: climate-refactor
description: >-
  Implement the Climate Flask app refactor (NumPy/batched SQL, SQLite to
  PostgreSQL, Open-Meteo cache-miss). Use when working on this repo's weather
  data pipeline, helpers_data.py, helpers_maps.py, fetch_data, docs/REFACTOR.md,
  phase A/B/C, Postgres, or Open-Meteo fallback.
---

# Climate app refactor

Source of truth: [docs/REFACTOR.md](../../../docs/REFACTOR.md). Do not treat the old Codex plan file as editable or as the living spec.

Owner is Zijian (student). Prefer working in code: create, debug, iterate. Machine: MacBook Air M5; no M-series-specific app code.

## Goals

1. Faster, cleaner Python — NumPy for grids; pandas only for Open-Meteo daily → monthly resample.
2. SQLite → local PostgreSQL (`locations`, `data` with unique `(loc_id, dates)` upserts).
3. Browse history on the site: local DB first; if missing, Open-Meteo Climate API, store, then serve.

## Do not

- Rewrite Folium or Plotly.
- Drop Flask pages or user accounts unless asked.
- Docker, cloud Postgres, or `/update` merge rewrite unless asked.
- Commit `.env` or secrets. Connection string via `DATABASE_URL`.
- Per-cell SQL or a new SQLite connection per grid cell (the old `fetch_data` pattern).
- Naive 8k Open-Meteo calls for a map. Respect ~10k/day, 5k/hour, 600/min.

## Publishing boundary

- The only remote this refactor may fetch from or push to is `refactor`:
  `https://github.com/iktCalT/climate2.git`.
- Never push to, fetch from, rename, remove, or otherwise change `origin` or
  any other repository. `origin` is the original human-authored project.
- Commit and publish refactor work only when Zijian explicitly asks.

## Phases (in order)

Do not skip ahead unless the user names a later phase.

**A — still SQLite:** One (or few) queries → NumPy grid in `fetch_data`. Clean helpers and error handling. Share DB connections. Keep 91×91 grid and climate types `temp_mean` / `temp_max` / `temp_min` / `precip`.

**B — PostgreSQL:** Local Homebrew `postgresql@16` or Postgres.app. `psycopg` v3 or SQLAlchemy; one connection helper. `INSERT ... ON CONFLICT`. Point weather paths off `static/weather.db`. Users can stay on `users.db` until asked.

**C — cache-miss on the site:** `/locations` first: query DB for lat/lon + range; if incomplete, fetch, upsert, serve. Then maps only if missing cells can be fetched without exploding API usage. HTML under `static/weather_data/` and `static/location_data/` is a render cache; the DB is the source of truth for numbers.

## Key files

- `app.py` — routes; `/locations` currently hits the API when chart HTML is missing and does not persist to weather DB; `/maps` only reads local DB.
- `helpers_data.py` — Open-Meteo + pandas monthly agg + SQLite writes.
- `helpers_maps.py` — maps; `fetch_data` is the main bottleneck.
- `helpers.py` — charts, auth helpers.

Date window: maps ~1950-01–2023-12; locations may go through today. Climate API: `https://climate-api.open-meteo.com/v1/climate`.

## When implementing

1. Read `docs/REFACTOR.md` and the files you will change.
2. Stay on the current phase.
3. After UI/route changes, verify in the browser (or say what you could not verify).
4. Do not commit unless Zijian asks.
