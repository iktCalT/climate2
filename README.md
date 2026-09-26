# Climate

> [!IMPORTANT]
> This repository is an AI-assisted refactor produced with [OpenAI Codex](https://openai.com/codex/) (GPT-5). It is derived from [iktCalT/climate](https://github.com/iktCalT/climate), which its human author implemented as a CS50 final project with substantial guidance from [ChatGPT](https://chatgpt.com/). Keep this work in the `climate2` fork; do not push these commits to the original repository.

Climate is a Flask website for exploring modelled historical climate data. It reads weather values from a local PostgreSQL cache and asks the [Open-Meteo Climate API](https://open-meteo.com/en/docs/climate-api) for missing data before saving and displaying it.

## Current features

- **Maps:** a flat, fullscreen-capable MapLibre map for mean, maximum, or minimum temperature and precipitation from January 1950 through the current month. Opening Maps shows mean temperature for the newest stable month by default, falling back to the previous month during the first six UTC hours of a new month, and starts over the contiguous United States. Users can compare two through four distinct months side by side; moving any panel synchronizes every viewport, and all panels share one visible, manually selected preset or custom scale and legend. The scale stays fixed through panning, zooming, loading, date changes, and page reloads until changed manually. The global overview fits within a 91-by-91 grid using 2-degree latitude by 4-degree longitude cells. As the viewport shrinks, cell size decreases more slowly so fewer cells are displayed, stopping at 0.5-degree latitude by 1-degree longitude cells and city-scale zoom level 10. Tiles reuse direct or sufficiently nearby PostgreSQL observations without requiring the sample to match the tile or zoom center. A settled viewport requests at most one distributed batch of four locations that have no suitable cached neighbor and persists all four metrics for each location. Temporary estimates remain visibly distinguished from cached values in every comparison panel.
- **Locations:** displays four seasonal history lines at a time for one latitude/longitude from January 1951 through the current month. Mean temperature is selected by default, with minimum temperature, maximum temperature, and precipitation available from the chart menu. PostgreSQL is checked first, and only missing monthly ranges are fetched.
- **Accounts:** visitors and normal registered users can browse climate data. Administrators can pre-fetch a validated grid of at most 100 locations through `/update`.
- **Local-first storage:** weather data uses PostgreSQL 18. Every climate row is scoped to an explicit provider/product identifier, and all current reads select the active `open_meteo_cmip6` series so future NOAA CORe reanalysis cannot be silently mixed into existing comparisons. Account and profile data remains in a separate, ignored SQLite file so new personal information is not committed.
- **Resumable NOAA bulk import:** `import_noaa_core.py` anonymously retrieves only the indexed NOAA CORe GRIB2 records needed for a complete month, derives monthly extremes from daily records, nearest-samples the native Gaussian grid to the canonical 2°×4° points, validates metadata and physical bounds, and commits the month atomically under `noaa_core`. If a daily file omits both extrema, the importer may recover them only from all eight exact 0–3 hour extrema pairs in NOAA's official 3-hourly archive; any incomplete fallback rejects the month. PostgreSQL is the checkpoint, the default batch is one month, and full 1950–present selection is explicit rather than automatic.
- **Read-only provider review:** `compare_climate_providers.py` compares up to 12 imported months against the active Open-Meteo rows already in PostgreSQL. It reports canonical-grid coverage, per-metric deltas, and stable land, ocean, polar, and dateline samples as Markdown without contacting either provider, writing the database, or switching the website.

The displayed values are climate-model output, not direct station observations. See the in-app References page for data and software attribution.

The shared footer follows the active climate provider. It currently credits Open-Meteo and CMIP6; the existing NOAA CORe citation replaces that credit automatically only when a separate activation change switches live reads to `noaa_core`.

## Provider status

- **NOAA CORe backfill:** the local PostgreSQL checkpoint contains all 92 requested edge-period months across 1950–1953 and 2023–2026, with 8,281 canonical rows and all four metrics per month. May 2026 live validation exercised the exact 3-hourly extrema fallback for NOAA's missing May 19 daily extrema. An opt-in `1950-present` period makes the missing middle decades resumable in the same bounded batches; live batches have added all months of 1954–1961 and brought the checkpoint to 188/920 complete months, with 1962 next. Open-Meteo remains the active website provider until that backfill and a separate activation decision are complete because CORe reanalysis and the two-model CMIP6 average are materially different products. See the [provider evaluation](docs/CLIMATE_PROVIDER_EVALUATION.md).

## Architecture

```text
Browser -> Flask -> provider-scoped PostgreSQL weather cache
                    |
                    +-- missing months/cells -> Open-Meteo -> PostgreSQL

NOAA CORe -> indexed GRIB2 importer -> PostgreSQL (`noaa_core`, inactive)

Accounts -> ignored local SQLite database
```

The main modules are:

- `app.py` — Flask routes, validation, account access, and administrator ingest.
- `db.py` — PostgreSQL connection and location lookup helpers.
- `helpers_data.py` — Open-Meteo requests, monthly aggregation, cache lookup, and PostgreSQL upserts.
- `noaa_core.py` — anonymous indexed NOAA retrieval, GRIB2 validation, canonical-grid sampling, and provider-scoped monthly upserts.
- `import_noaa_core.py` — bounded command-line batch, validation-only mode, and PostgreSQL resume checkpoint.
- `compare_climate_providers.py` — read-only canonical coverage, metric-delta, and representative-point Markdown report.
- `map_data.py` — bounded, zoom-aware MapLibre GeoJSON viewport tiles.
- `helpers.py` — charts, validators, and authentication helpers.
- `schema.sql` — PostgreSQL weather schema.
- `user_schema.sql` — schema for a new local account database; it contains no user data.

## Local setup on macOS

This project targets PostgreSQL **18** and works on Apple Silicon without machine-specific application code.

1. Install and start PostgreSQL 18:

   ```sh
   brew install postgresql@18
   brew services start postgresql@18
   /opt/homebrew/opt/postgresql@18/bin/createdb climate
   ```

2. Create a Python environment and install the dependencies:

   ```sh
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

3. Create the weather and account schemas:

   ```sh
   .venv/bin/python setup_database.py
   .venv/bin/python setup_user_database.py
   ```

4. Start the website:

   ```sh
   .venv/bin/flask --app app run
   ```

The default weather connection is `postgresql://localhost/climate`. To use another local database, set `DATABASE_URL` in the shell that launches Flask. To place the account database elsewhere, set `USER_DATABASE_PATH`. Never commit credentials or a populated user database; `.env`, database files, profile uploads, generated charts, keys, and local caches are ignored. Legacy database and upload files that were tracked by the original project are removed from this refactor's current tree, while local copies remain available to their owner.

If you still have the legacy weather database, its non-personal climate rows can be imported once:

```sh
.venv/bin/python migrate_weather_sqlite.py static/weather.db
```

The migration is optional and safe to rerun. Otherwise, the application gradually fills PostgreSQL from Open-Meteo as data is requested. PostgreSQL climate rows do not expire automatically, so a value cached yesterday is reused today; administrators can deliberately force an update. As a secondary safeguard, identical Open-Meteo HTTP responses are cached locally for seven days.

To resumably fill the canonical global grid for 1950–1953 and 2023–2026,
run a bounded batch repeatedly:

```sh
.venv/bin/python prefetch_climate.py --dry-run
.venv/bin/python prefetch_climate.py
```

PostgreSQL is the checkpoint. Complete locations are skipped, missing
contiguous month ranges are fetched, and every successful range is committed
independently. Each run checks at most 100 incomplete locations; use a smaller
batch with `--limit NUMBER` when needed. Provider requests start at least 30
seconds apart by default because Climate API usage is weighted by time span,
variables, and models. The batch stops on its first provider failure and can be
resumed later. Use `--delay-seconds NUMBER` only when a different pacing policy
is appropriate for the available Open-Meteo plan.

The higher-capacity NOAA path works month-by-month across the whole canonical
grid. It needs no account or secret:

```sh
.venv/bin/python -m eccodes selfcheck
.venv/bin/python import_noaa_core.py --dry-run
.venv/bin/python import_noaa_core.py --period 1950-1953
.venv/bin/python import_noaa_core.py --period 2023-2026
.venv/bin/python import_noaa_core.py --period 1950-present --dry-run
.venv/bin/python import_noaa_core.py --period 1950-present --limit 12
```

Only complete calendar months are eligible. One month is imported per run by
default; `--limit NUMBER` may raise the batch to at most 12. Use
`--month YYYY-MM --validate-only` to download and validate a sample without a
database write. Each successful month contains all 8,281 canonical locations
and all four metrics in the separate `noaa_core` family. An interrupted month
is retried in full, while a completed month is skipped. If both extrema are
absent from a daily aggregate index, the importer uses all eight exact 0–3
hour extrema pairs from that day's official 3-hourly files; it rejects partial
daily or 3-hourly evidence rather than interpolating or skipping a day. The
local checkpoint completed all 92 edge-period months on 2026-09-25. These rows
do not change website output because all current reads still select
`open_meteo_cmip6`. The `1950-present` period is opt-in and dynamically stops
at the latest complete month; use `--through YYYY-MM` to set an earlier bound.
Default selection remains the two recorded edge periods, so a normal rerun
does not unexpectedly begin the much larger full-history job.

Compare only rows already stored in PostgreSQL after importing review months:

```sh
.venv/bin/python compare_climate_providers.py --month 1950-01
.venv/bin/python compare_climate_providers.py --month 1952-02 --month 2023-07
```

At most 12 distinct complete months may be requested. With no `--month`, the
command selects the latest 12 available CORe months. It opens a read-only
transaction, ignores non-canonical user-entered coordinates, and prints a
Markdown report to standard output. `COMPLETE` means both providers contain
all required comparison values for the selected canonical grid; it is not an
activation decision. CORe and the active two-model CMIP6 average are different
products, so a human review across the recorded historical, leap-year, recent,
polar, ocean, and dateline cases is still required.

## Administrator setup

Registration always creates a normal user. Promote or demote an existing local account with:

```sh
.venv/bin/python manage_users.py grant-admin USERNAME
.venv/bin/python manage_users.py revoke-admin USERNAME
```

See [docs/USER_ROLES.md](docs/USER_ROLES.md) for administrator ingest limits and [docs/POSTGRESQL.md](docs/POSTGRESQL.md) for database details.

## Testing

With the virtual environment and local PostgreSQL available:

```sh
.venv/bin/python -m unittest discover -s tests
```

The route tests use temporary account databases and do not modify personal account data.

## Repository privacy

Never commit or push `.env` files, database passwords, API tokens, private
keys, populated databases, session data, personal account data, or
machine-specific configuration. Keep sensitive values in ignored local files
or environment variables; documented examples may contain only clearly fake,
non-functional placeholders.

The repository ignores common secret, credential, key, and database filename
patterns as a backstop. Before every commit and push, inspect the staged file
list and scan staged content for likely secrets because `.gitignore` cannot
protect a file that is already tracked or staged. If a real credential is ever
exposed, remove it from the change without repeating its value and rotate or
revoke it before publishing.

## Refactor documentation

- [Refactor plan](docs/REFACTOR.md) — the agreed, unchanged source plan.
- [PostgreSQL 18 setup](docs/POSTGRESQL.md)
- [User roles](docs/USER_ROLES.md)
- [Project direction and publication boundaries](docs/PROJECT_DIRECTION.md)
- [Recorded follow-up requirements](docs/NEXT_REQUIREMENTS.md)
- [Climate provider evaluation](docs/CLIMATE_PROVIDER_EVALUATION.md)

## External sources and attribution

Every external package, service, dataset, webpage, image, font, code source, or
other third-party resource used by this project must be credited here and on
the in-app References page in the same change that introduces it. Prefer a
canonical provider link and record the purpose and licence requirements when
available.

Current data and evaluated providers:

- [Open-Meteo Climate API](https://open-meteo.com/en/docs/climate-api) supplies the active downscaled climate-model data; its underlying models follow the [CMIP6 terms](https://pcmdi.llnl.gov/CMIP6/TermsOfUse).
- [NOAA Conventional Observation Reanalysis (CORe)](https://www.cpc.ncep.noaa.gov/products/CORe/index.html), its [public NODD archive](https://www.cpc.ncep.noaa.gov/products/CORe/archive.html), and [field/retrieval documentation](https://ftp.cpc.ncep.noaa.gov/CORe/get_core/get_core.txt) define the selected anonymous bulk source. The retrieval guide documents the monthly, daily, and 3-hourly file layout used by the exact daily-extrema fallback. NOAA documents the analyses and downloader as public domain; the [NOAA NCEI open-data policy](https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf) explains NOAA's public-domain and CC0 policy. CORe is imported but not yet the active website provider.
- NOAA's [CORe regridding guidance](https://www.cpc.ncep.noaa.gov/products/CORe/regridding.html) documents its 512-by-256 Gaussian grid, the [Physical Sciences Laboratory overview](https://psl.noaa.gov/data/coreinfo.html) describes its reanalysis role, and the [Weather Program Office announcement](https://wpo.noaa.gov/ncep-introduces-operational-reanalysis-for-climate-monitoring-core/) records the operational transition. The [NCEP/NCAR Reanalysis 1 update notice](https://psl.noaa.gov/news/2026/r1datanotice.html) explains why that retired predecessor was not selected.
- [Copernicus CDS ERA5 monthly data](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=overview) remains an evaluated alternative under CC BY, but was not selected because programmatic retrieval requires an account, dataset-licence acceptance, and a private token.
- [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) and [CRU gridded datasets](https://crudata.uea.ac.uk/cru/data/hrg/) were evaluated as documented alternatives but are not active providers.

Current application software and delivery services:

- [ECMWF ecCodes Python](https://github.com/ecmwf/eccodes-python) decodes the selected NOAA GRIB2 records and is distributed under Apache License 2.0. Its PyPI installation includes the binary ecCodes library on macOS and Linux.
- [Flask](https://flask.palletsprojects.com/en/stable/) and [Flask-Session](https://flask-session.readthedocs.io/en/latest/) provide the web application and server-side sessions.
- [PostgreSQL](https://www.postgresql.org/docs/18/) and [Psycopg](https://www.psycopg.org/psycopg3/docs/) provide climate storage and Python database access.
- [NumPy](https://numpy.org/doc/stable/), [pandas](https://pandas.pydata.org/docs/), and [Plotly Python](https://plotly.com/python/) provide numerical work, monthly aggregation, and charts.
- [Open-Meteo's Python client](https://github.com/open-meteo/python-requests), [requests-cache](https://requests-cache.readthedocs.io/en/stable/), and [retry-requests](https://github.com/MazeMap/retry-requests) provide API transport, local response caching, and bounded retries.
- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) renders maps using the [MapLibre demo style and tiles](https://github.com/maplibre/demotiles).
- [ColorBrewer 2.0](https://colorbrewer2.org/) provides the cartographic diverging and sequential palette guidance adapted for the temperature and precipitation scale presets.
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/) is delivered through [jsDelivr](https://www.jsdelivr.com/), and the interface loads Audiowide, Space Mono, and Muli through [Google Fonts](https://fonts.google.com/).

Project, learning, and visual sources:

- The original [iktCalT/climate](https://github.com/iktCalT/climate) project was implemented by its human author as a [CS50x](https://cs50.harvard.edu/x/) final project with substantial [ChatGPT](https://chatgpt.com/) guidance. Authentication and error-page helper patterns were adapted from CS50 course material.
- The climate favicon is sourced from [Iconfinder](https://www.iconfinder.com/icons/9079087/global_warming_climate_change_hot_heat_temperature_icon).
- Error images use [Memegen](https://github.com/jacebrowning/memegen) with an inherited Grumpy Cat background; the cultural reference is documented by [Know Your Meme](https://knowyourmeme.com/memes/grumpy-cat). The inherited background's original image licence is not established and should be replaced before broader publication.
- Inactive legacy generated map HTML files under `static/weather_data/` embed [Folium](https://python-visualization.github.io/folium/), [Leaflet](https://leafletjs.com/), [jQuery](https://jquery.com/), [Leaflet.awesome-markers](https://github.com/lennardv2/Leaflet.awesome-markers), [Font Awesome](https://fontawesome.com/), [OpenStreetMap](https://www.openstreetmap.org/copyright), and [CARTO basemaps](https://carto.com/attributions). They are retained only as historical artifacts and are not used by the current MapLibre pages.
- This refactor is produced with [OpenAI Codex](https://openai.com/codex/) under the human owner's direction and review.

## License

See [LICENSE](LICENSE).
