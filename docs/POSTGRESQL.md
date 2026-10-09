# Local PostgreSQL 18

The weather database now uses PostgreSQL 18. `static/weather.db` remains only
as the legacy migration source; the Flask weather features no longer read it.
User accounts use separate ignored SQLite storage: private `instance/users.db`
for new installations, or explicit `USER_DATABASE_PATH`. An existing legacy
`static/users.db` remains a warned fallback until deliberately relocated;
see [private account storage](USER_ROLES.md#private-account-storage).

PostgreSQL 18.6 is installed locally through Homebrew and runs as a background
service. Flask uses `postgresql://localhost/climate` automatically. Set
`DATABASE_URL` only when you want to use a different database:

```sh
.venv/bin/flask --app app run
```

The database has the following tables:

- `locations`: a unique latitude/longitude and its `loc_id`.
- `data`: one row per location/month/provider with a primary key on
  `(loc_id, dates, provider)`. Open-Meteo rows use `open_meteo_cmip6`; current
  public reads explicitly select the `noaa_core` series. Each provider remains
  separately addressable.

Both ingestion and updates use provider-scoped PostgreSQL `ON CONFLICT`
upserts. Running `python -m climate.cli.setup_database` also upgrades an existing two-column
weather key idempotently: legacy rows are labelled `open_meteo_cmip6` before
the provider-aware primary key is installed. To make a fresh local database
after intentionally deleting it, run:

```sh
/opt/homebrew/opt/postgresql@18/bin/createdb climate
export DATABASE_URL='postgresql://localhost/climate'
.venv/bin/python -m climate.cli.setup_database
.venv/bin/python -m climate.cli.migrate_weather_sqlite static/weather.db
```

## Location history gap fetching

Run `.venv/bin/python -m climate.cli.setup_database` explicitly after updating
the application. It additively creates `climate_location_fetch_job` and
`climate_location_fetch_limit`; ordinary web startup never alters schema. Local
development enables NOAA Location gap fetching by default. Production requires
`LOCATION_FETCH_ENABLED=1`; `0` disables it. Restart workers after changing
settings. `LOCATION_FETCH_HOURLY_LIMIT` defaults to 12 attempted months per
fixed one-hour window (allowed 1–60), including failed attempts. Per-month limits default
to 192 archive requests, 512 MiB downloaded, and 900 seconds elapsed;
`LOCATION_FETCH_MAX_REQUESTS` (32–512), `LOCATION_FETCH_MAX_MIB` (32–1024),
and `LOCATION_FETCH_MAX_SECONDS` (60–1800) may be set within those bounds.
Elapsed checks run during streamed response reads and before saving; socket
timeouts shrink to the remaining budget. This is not a process-level deadline
for operating-system DNS or connection setup. Leaving the page stops browser
continuation, not the already-started bounded month job.

Only one global NOAA job runs at a time, sharing the import/cleanup advisory
lock. PostgreSQL retains the hourly counter, latest job state, and successfully
committed sample rows across process restarts. One start retrieves at most one
missing completed month for one canonical sample, newest first. The browser
continues after successful months while the page stays open; failures,
interruption and throttling require explicit retry. The archive exposes global
fields rather than a point endpoint, so downloading daily extrema can take
minutes or exhaust the per-month budget. Saved finite fields are preserved;
inconsistent combined values reject the month. Maps remain cache-only.

The browser reads `GET /api/location-fetch/status` and sends a same-origin,
bounded JSON `POST /api/location-fetch/start` with only requested latitude and
longitude. Both return one common snapshot (`state`, sampled coordinates,
complete/total/remaining months, current month, and throttle retry seconds).
Normal states, including busy/throttled/disabled, use HTTP 200. Invalid input
uses 400, cross-origin POST uses 403, wrong media type uses 415, oversized body
uses 413, and unavailable storage or configuration uses 503. Status never
downloads; one accepted start charges the global allowance before the worker
begins, including a failed attempt.

The migration is safe to re-run: it upserts locations and weather rows. Do not
commit a real connection string or credentials; `.env` remains ignored if you
choose to keep one for personal reference.

## Resumable edge-period prefetch

The canonical 91-by-91 global grid can be filled for 1950–1953 and 2023–2026
in bounded, resumable batches:

```sh
.venv/bin/python -m climate.cli.prefetch_climate --dry-run
.venv/bin/python -m climate.cli.prefetch_climate --limit 100
```

The database is the only checkpoint. The command counts a period as complete
only when every month has all four climate metrics, fetches missing contiguous
ranges, and commits each successful range separately. An interrupted or
partially failed batch can therefore be resumed with the same command. Live
requests start at least 30 seconds apart by default, and the command stops on
the first provider failure rather than consuming the rest of a batch while a
rate limit is active.

## Resumable NOAA CORe bulk import

The optional NOAA importer fills one complete global month at a time under the
separate `noaa_core` provider family. It does not require an account, API key,
token, or `.env` entry. The website currently reads saved `noaa_core` rows;
imports add to that provider without changing or relabelling other rows.

```sh
.venv/bin/python -m eccodes selfcheck
.venv/bin/python -m climate.cli.import_noaa_core --dry-run
.venv/bin/python -m climate.cli.import_noaa_core --period 1950-1953
.venv/bin/python -m climate.cli.import_noaa_core --period 2023-2026
```

The default batch is one month and the maximum is 12 months. Only completed
calendar months are selected. NOAA `.idx` files identify the exact GRIB2 byte
ranges, so unrelated fields and full archive files are not downloaded. The
importer validates dates, variables, aggregation types, units, levels, the
512-by-256 Gaussian grid, missing values, physical bounds, and temperature
ordering before writing anything.

One database transaction creates or reuses the 8,281 canonical locations and
upserts all four values for the month. A month is complete only when every
canonical location has every metric. Interrupted or incomplete months are
retried; complete months are skipped. For a no-write live check, use:

```sh
.venv/bin/python -m climate.cli.import_noaa_core --month 1950-01 --validate-only
```

## Read-only provider comparison

After the same month exists under both provider identities, generate a
deterministic Markdown review from PostgreSQL only:

```sh
.venv/bin/python -m climate.cli.compare_climate_providers --month 1950-01
.venv/bin/python -m climate.cli.compare_climate_providers --month 1952-02 --month 2023-07
```

The command begins a read-only transaction and never calls NOAA or Open-Meteo.
It filters to the 8,281 canonical map coordinates, reports missing and complete
coverage explicitly, calculates `noaa_core - open_meteo_cmip6` differences for
all four metrics, and prints land, ocean, polar, and both dateline-edge samples.
It accepts at most 12 complete months. A complete report means the selected
database evidence is present; it does not establish scientific accuracy or
coverage outside the requested months.
