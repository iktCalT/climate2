# Climate

> [!IMPORTANT]
> This repository is an AI-assisted refactor produced with [OpenAI Codex](https://openai.com/codex/) (GPT-5). It is derived from [iktCalT/climate](https://github.com/iktCalT/climate), which its human author implemented as a CS50 final project with substantial guidance from [ChatGPT](https://chatgpt.com/). Keep this work in the `climate2` fork; do not push these commits to the original repository.

Climate is a Flask website for exploring modelled historical climate data. Public browsing reads saved values from a local PostgreSQL cache without contacting climate providers. Administrators manage acquisition separately; the active dataset is still [Open-Meteo Climate API](https://open-meteo.com/en/docs/climate-api) CMIP6 output.

## Current features

- **Maps:** a flat, fullscreen-capable MapLibre map for mean, maximum, or minimum temperature and precipitation from January 1950 through the current month. Opening Maps shows the newest saved active-provider mean-temperature month, no later than the stable-date limit (previous month during the first six UTC hours of a new month, current month otherwise), and starts over the contiguous United States. Explicitly selected dates are never replaced. If no suitable saved month exists, the date selector opens instead. Users can compare two through four distinct months side by side; moving any panel synchronizes every viewport, and all panels share one visible, manually selected preset or custom scale and legend. The scale stays fixed through panning, zooming, loading, date changes, and page reloads until changed manually. The global overview fits within a 91-by-91 grid using 2-degree latitude by 4-degree longitude cells. As the viewport shrinks, cell size decreases more slowly so fewer cells are displayed, stopping at 0.5-degree latitude by 1-degree longitude cells and city-scale zoom level 10. Tiles reuse direct or sufficiently nearby PostgreSQL observations without requiring the sample to match the tile or zoom center. Public viewport requests never fetch missing climate cells. Missing coverage and display-only spatial estimates remain visibly distinguished from cached values in every comparison panel; nothing is queued for download.
- **Locations:** displays four seasonal history lines at a time for one latitude/longitude from January 1951 through the current month. Mean temperature is selected by default, with minimum temperature, maximum temperature, and precipitation available from the chart menu. Only saved active-provider monthly values are read; gaps stay missing, with coverage counts and a clear empty state. Seasonal means use available months and may represent incomplete seasons. Rendered chart URLs are keyed to current data content so imports and cleanup are reflected on the next page request.
- **Accounts:** visitors and normal registered users can browse climate data. Administrators can start/resume bounded NOAA edge-window batches and view live coverage through `/admin/data`. The older Open-Meteo point-grid tool remains at `/update` for advanced use.
- **Local-first storage:** weather data uses PostgreSQL 18. Every climate row is scoped to an explicit provider/product identifier, and all current reads select the active `open_meteo_cmip6` series so future NOAA CORe reanalysis cannot be silently mixed into existing comparisons. Account and profile data remains in a separate, ignored SQLite file so new personal information is not committed.
- **Resumable NOAA bulk import:** `import_noaa_core.py` anonymously retrieves only the indexed NOAA CORe GRIB2 records needed for a complete month, derives monthly extremes from daily records, nearest-samples the native Gaussian grid to the canonical 2°×4° points, validates metadata and physical bounds, and commits the month atomically under `noaa_core`. If a daily file omits both extrema, the importer may recover them only from all eight exact 0–3 hour extrema pairs in NOAA's official 3-hourly archive; any incomplete fallback rejects the month. PostgreSQL is the checkpoint, the default batch is one month, and full 1950–present selection is explicit rather than automatic.
- **Read-only provider review:** `compare_climate_providers.py` compares up to 12 imported months against the active Open-Meteo rows already in PostgreSQL. It reports canonical-grid coverage, per-metric deltas, and stable land, ocean, polar, and dateline samples as Markdown without contacting either provider, writing the database, or switching the website.

On **Maps → Change selection**, **Find a saved month** lists saved dates and
finite-value point counts for the chosen variable. Use a date as the first
month or add it to a comparison; manual date entry remains available. Counts
are global, not a claim of complete US/viewport coverage or verified accuracy.
Changing the variable refreshes the saved-date list but never changes dates
already entered. Availability uses one read-only, active-provider PostgreSQL
aggregation with a three-second statement timeout and a short lock timeout;
if it fails, the selector explains the problem and keeps manual entry usable.
The listing refreshes on a new page request, so imports and cleanup affect the
next visit without a persistent availability cache. No packages were added.

The displayed values are climate-model output, not direct station observations. See the in-app References page for data and software attribution.

The shared footer follows the active climate provider. It currently credits Open-Meteo and CMIP6; the existing NOAA CORe citation replaces that credit automatically only when a separate activation change switches live reads to `noaa_core`.

## Provider status

- **Current data scope:** administrator-started NOAA fetching is limited to 1950–1954 and 2022–2026, through the latest complete month. Manual full-history and 2016–2026 backfill work is no longer a priority; saved rows remain intact unless an administrator explicitly uses the optional cleanup tool. Open-Meteo CMIP6 is still active pending a separate validated provider switch. Some inherited ocean temperatures disagree with fresh source checks and have not been repaired. See the [provider evaluation](docs/CLIMATE_PROVIDER_EVALUATION.md).

On 2026-09-26, the administrator coverage check found both windows complete:
60/60 months for 1950–1954 and 56/56 for 2022–August 2026. No additional
downloads were needed for this interface change. The admin page reads current
coverage directly from PostgreSQL rather than relying on this dated snapshot.

## Architecture

```text
Browser -> Flask -> provider-scoped PostgreSQL weather cache

Administrator tools -> Open-Meteo or NOAA importer -> PostgreSQL

NOAA CORe -> indexed GRIB2 importer -> PostgreSQL (`noaa_core`, inactive)

Accounts -> ignored local SQLite database
```

Code is grouped by responsibility:

- `app.py` / `run.sh` — small Flask entry points.
- `climate/web/` — routes, authentication, validation, and chart presentation.
- `climate/services/` — map tiles and administrator import/cleanup workflows.
- `climate/providers/` — Open-Meteo and NOAA acquisition and validation.
- `climate/data/` — PostgreSQL access, saved-month queries, and calendar helpers.
- `climate/cli/` — explicit administrative commands, run with `python -m`.
- `sql/` — weather, account, and import-job schemas.
- `templates/`, `static/`, `tests/` — page templates, browser assets, and tests.
- `docs/` — project decisions and operating guides; `docs/agents/` holds shared
  instructions, owned logs, and context lookup.

Start with the [architecture guide](docs/ARCHITECTURE.md) or
[documentation index](docs/README.md). Agents should enter through
[AGENTS.md](AGENTS.md) and their [assigned task](docs/AGENT_TASKS.md).

## Local setup on macOS

This project targets PostgreSQL **18** and works on Apple Silicon without machine-specific application code. Run commands from the repository root; `./run.sh` also works when invoked from another directory.

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
   .venv/bin/python -m climate.cli.setup_database
   .venv/bin/python -m climate.cli.setup_user_database
   ```

4. Start the website:

   ```sh
   .venv/bin/flask --app app run
   ```

The default weather connection is `postgresql://localhost/climate`. To use another local database, set `DATABASE_URL` in the shell that launches Flask. To place the account database elsewhere, set `USER_DATABASE_PATH`. Never commit credentials or a populated user database; `.env`, database files, profile uploads, generated charts, keys, and local caches are ignored. Legacy database and upload files that were tracked by the original project are removed from this refactor's current tree, while local copies remain available to their owner.

If you still have the legacy weather database, its non-personal climate rows can be imported once:

```sh
.venv/bin/python -m climate.cli.migrate_weather_sqlite static/weather.db
```

The migration is optional and safe to rerun. Public browsing never fills PostgreSQL automatically: administrators use the existing Open-Meteo point-grid tool or NOAA importer for deliberate acquisition. NOAA rows remain separate and inactive. PostgreSQL climate rows do not expire automatically; administrators can deliberately update or clean them. Identical Open-Meteo responses used by acquisition tools are cached locally for seven days. Cache-only browsing removes climate-provider network waits, but database, chart rendering, and basemap/asset loading still take time. Sparse or empty views are expected where active-provider data has not been imported.

To resumably fill the canonical global grid for 1950–1953 and 2023–2026,
run a bounded batch repeatedly:

```sh
.venv/bin/python -m climate.cli.prefetch_climate --dry-run
.venv/bin/python -m climate.cli.prefetch_climate
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
.venv/bin/python -m climate.cli.import_noaa_core --dry-run
.venv/bin/python -m climate.cli.import_noaa_core --period 1950-1953
.venv/bin/python -m climate.cli.import_noaa_core --period 2023-2026
.venv/bin/python -m climate.cli.import_noaa_core --period 1950-present --dry-run
.venv/bin/python -m climate.cli.import_noaa_core --period 1950-present --limit 12
.venv/bin/python -m climate.cli.import_noaa_core --period 2016-2026 --newest-first --dry-run
.venv/bin/python -m climate.cli.import_noaa_core --period 2016-2026 --newest-first --limit 12
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

Those CLI periods remain available for compatibility, but routine acquisition
now uses **Admin → Data** at `/admin/data`: select 1950–1954 or 2022–2026,
choose 1–12 months (default 1), and click **Start / resume batch**. The last
window runs newest-first. Both windows stop at complete months and skip saved
months. Status refreshes while a job runs; opening the page never downloads.

Run `python -m climate.cli.setup_database` once after upgrading to install the additive
`sql/admin_import.sql` job-status table. Keep the app server running while a batch
works. The background thread is not a durable queue: a server restart interrupts
unfinished work, but committed months survive and the page offers manual resume.
PostgreSQL serializes administrator batches across web workers. Do not run the
standalone CLI importer concurrently with the admin tool. Admin rights are
checked on every request, starts require a session-bound CSRF token, and public
errors contain no raw connection details. No credentials are entered in the UI.

### Optional administrator cleanup

On **Admin → Data**, choose **Preview cleanup (no deletion)** to see retained
and removable row counts for each provider. Cleanup keeps every climate row in
**1950–1954 and 2022–2026**, and removes only rows outside those windows, from
all providers including active Open-Meteo. Back up PostgreSQL first if you need
exact recovery: there is no in-app undo and re-fetching can return revised data.
After reviewing the counts, check the explicit confirmation and click
**Delete up to 50,000 rows**. Each click commits one bounded batch. Preview and
confirm again to continue; nothing deletes automatically. Preview tokens expire
after 10 minutes. The reusable functions are `cleanup_preview()` and
`cleanup_batch()` in `climate/services/admin_cleanup.py`; the latter is destructive and must only
be called deliberately. The website enforces current admin rights and CSRF.

Cleanup shares the admin import lock, uses 2-second lock and 30-second statement
timeouts, and rolls back SQL failures. Pause CLI imports before cleanup.
Accounts, profiles, location definitions, downloaded files, and rendered caches
are untouched. This is manual pruning, **not an enforced retention policy**:
public browsing no longer refills removed rows, but explicit import tools can.
New location page requests use a chart URL based on current cached data; an
already-open chart or a directly accessed old generated file can still show old
values. Pruning alone is not a guarantee of faster indexed queries.

The bounded SQL follows PostgreSQL's documented
[batch DELETE pattern](https://www.postgresql.org/docs/18/sql-delete.html).
[Routine vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html)
reclaims deleted space for reuse and refreshes planner statistics; deleting rows
does not immediately shrink the database file. This page never runs disruptive
`VACUUM FULL`. PostgreSQL and its documentation use the
[PostgreSQL License](https://www.postgresql.org/about/licence/).

For finer comparison colors, manually choose **Cold detail** (−10 to 10 °C),
**Mild detail** (0 to 20 °C), or **Warm detail** (20 to 40 °C). Their color stops
are 2 °C apart, with continuous interpolation. All panels share that scale;
saved presets/custom scales are preserved. Values outside the selected range
use the endpoint colors. More contrast is not greater data accuracy.

Compare only rows already stored in PostgreSQL after importing review months:

```sh
.venv/bin/python -m climate.cli.compare_climate_providers --month 1950-01
.venv/bin/python -m climate.cli.compare_climate_providers --month 1952-02 --month 2023-07
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
.venv/bin/python -m climate.cli.manage_users grant-admin USERNAME
.venv/bin/python -m climate.cli.manage_users revoke-admin USERNAME
```

See [docs/USER_ROLES.md](docs/USER_ROLES.md) for administrator ingest limits and [docs/POSTGRESQL.md](docs/POSTGRESQL.md) for database details.

## Testing

Run the offline regression suite from the repository root:

```sh
DATABASE_URL= PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests
node --test tests/test_map_scales.mjs
```

The route tests use temporary account databases and do not modify personal account data.
The empty `DATABASE_URL` skips live PostgreSQL tests. Only enable database
integration checks against an explicitly isolated test database.
Optional real-SQL cleanup tests create only connection-local temporary tables:
`CLIMATE_CLEANUP_PG_TEST=1 .venv/bin/python -m unittest discover -s tests -p 'test_admin_cleanup.py'`.
They verify date boundaries, all-provider retention, batch limits, rollback, and
import-lock conflicts without deleting application climate rows.

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

- [Python threading](https://docs.python.org/3/library/threading.html) (Python Software Foundation licence) runs bounded background admin batches; no task-queue dependency was added.
- [Python hashlib](https://docs.python.org/3/library/hashlib.html) (Python Software Foundation licence) creates SHA-256 data-content keys for location chart reuse without stale results after imports or cleanup.
- [Node.js](https://nodejs.org/) runs the dependency-free map-scale tests (`node tests/test_map_scales.mjs`); Node is MIT-licensed with bundled third-party notices in its [licence](https://github.com/nodejs/node/blob/main/LICENSE).

- [ECMWF ecCodes Python](https://github.com/ecmwf/eccodes-python) decodes the selected NOAA GRIB2 records and is distributed under Apache License 2.0. Its PyPI installation includes the binary ecCodes library on macOS and Linux.
- [Flask](https://flask.palletsprojects.com/en/stable/) and [Flask-Session](https://flask-session.readthedocs.io/en/latest/) provide the web application and server-side sessions.
- [PostgreSQL](https://www.postgresql.org/docs/18/) and [Psycopg](https://www.psycopg.org/psycopg3/docs/) provide climate storage, read-only saved-month aggregation, bounded query execution, and Python database access.
- [NumPy](https://numpy.org/doc/stable/), [pandas](https://pandas.pydata.org/docs/), and [Plotly Python](https://plotly.com/python/) provide numerical work, monthly aggregation, and charts.
- [Open-Meteo's Python client](https://github.com/open-meteo/python-requests), [requests-cache](https://requests-cache.readthedocs.io/en/stable/), and [retry-requests](https://github.com/MazeMap/retry-requests) provide API transport, local response caching, and bounded retries.
- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) renders maps using the [MapLibre demo style and tiles](https://github.com/maplibre/demotiles).
- [ColorBrewer 2.0](https://colorbrewer2.org/) provides the cartographic diverging and sequential palette guidance adapted for the temperature and precipitation scale presets.
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/) is delivered through [jsDelivr](https://www.jsdelivr.com/), and the interface loads Audiowide, Space Mono, and Muli through [Google Fonts](https://fonts.google.com/).

Project, learning, and visual sources:

- The original [iktCalT/climate](https://github.com/iktCalT/climate) project was implemented by its human author as a [CS50x](https://cs50.harvard.edu/x/) final project with substantial [ChatGPT](https://chatgpt.com/) guidance. Authentication and error-page helper patterns were adapted from CS50 course material.
- The climate favicon is sourced from [Iconfinder](https://www.iconfinder.com/icons/9079087/global_warming_climate_change_hot_heat_temperature_icon).
- The local climate error-page illustration was generated specifically for this project with [OpenAI image generation](https://developers.openai.com/api/docs/guides/image-generation). It is not adapted from a third-party character or source image; error messages and status codes remain accessible HTML rather than image text.
- Inactive legacy generated map HTML files under `static/weather_data/` embed [Folium](https://python-visualization.github.io/folium/), [Leaflet](https://leafletjs.com/), [jQuery](https://jquery.com/), [Leaflet.awesome-markers](https://github.com/lennardv2/Leaflet.awesome-markers), [Font Awesome](https://fontawesome.com/), [OpenStreetMap](https://www.openstreetmap.org/copyright), and [CARTO basemaps](https://carto.com/attributions). They are retained only as historical artifacts and are not used by the current MapLibre pages.
- This refactor is produced with [OpenAI Codex](https://openai.com/codex/) under the human owner's direction and review.

## License

See [LICENSE](LICENSE).
