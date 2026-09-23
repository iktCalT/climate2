# Climate

> [!IMPORTANT]
> This repository is an AI-assisted refactor produced with [OpenAI Codex](https://openai.com/codex/) (GPT-5). It is derived from [iktCalT/climate](https://github.com/iktCalT/climate), which its human author implemented as a CS50 final project with substantial guidance from [ChatGPT](https://chatgpt.com/). Keep this work in the `climate2` fork; do not push these commits to the original repository.

Climate is a Flask website for exploring modelled historical climate data. It reads weather values from a local PostgreSQL cache and asks the [Open-Meteo Climate API](https://open-meteo.com/en/docs/climate-api) for missing data before saving and displaying it.

## Current features

- **Maps:** a flat, fullscreen-capable MapLibre map for mean, maximum, or minimum temperature and precipitation from January 1950 through the current month. Opening Maps shows mean temperature for the newest stable month by default, falling back to the previous month during the first six UTC hours of a new month. The global overview fits within a 91-by-91 grid using 2-degree latitude by 4-degree longitude cells. As the viewport shrinks, cell size decreases more slowly so fewer cells are displayed, stopping at 0.5-degree latitude by 1-degree longitude cells and city-scale zoom level 10. Tiles reuse direct or sufficiently nearby PostgreSQL observations without requiring the sample to match the tile or zoom center. A settled viewport requests at most one distributed batch of four locations that have no suitable cached neighbor and persists all four metrics for each location. Temporary estimates remain visibly distinguished from cached values.
- **Locations:** displays four seasonal history lines at a time for one latitude/longitude from January 1951 through the current month. Mean temperature is selected by default, with minimum temperature, maximum temperature, and precipitation available from the chart menu. PostgreSQL is checked first, and only missing monthly ranges are fetched.
- **Accounts:** visitors and normal registered users can browse climate data. Administrators can pre-fetch a validated grid of at most 100 locations through `/update`.
- **Local-first storage:** weather data uses PostgreSQL 18. Account and profile data remains in a separate, ignored SQLite file so new personal information is not committed.

The displayed values are climate-model output, not direct station observations. See the in-app References page for data and software attribution.

## Planned next features

- **ERA5 bulk-provider path:** provider research selected Copernicus CDS ERA5 as the preferred safe, free, global bulk-source candidate. Integration is deliberately deferred until the owner accepts the CDS licence, supplies a token outside Git, and approves the change from averaged CMIP6 projections to reanalysis. Open-Meteo remains active. See the [provider evaluation](docs/CLIMATE_PROVIDER_EVALUATION.md).
- **Manual map scales:** add temperature- and precipitation-specific presets plus validated custom value/color stops. The active scale and legend will stay fixed while panning, zooming, changing dates, or loading data; only the user will change it.
- **Same-scale comparisons:** let users choose two or more months and compare synchronized maps side by side. Every panel will use the same metric, numeric bounds, colors, and legend so visual differences remain meaningful.

## Architecture

```text
Browser -> Flask -> PostgreSQL weather cache
                    |
                    +-- missing months/cells -> Open-Meteo -> PostgreSQL

Accounts -> ignored local SQLite database
```

The main modules are:

- `app.py` — Flask routes, validation, account access, and administrator ingest.
- `db.py` — PostgreSQL connection and location lookup helpers.
- `helpers_data.py` — Open-Meteo requests, monthly aggregation, cache lookup, and PostgreSQL upserts.
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
- [Copernicus CDS ERA5 monthly data](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=overview) and [ERA5 daily statistics](https://cds.climate.copernicus.eu/datasets/derived-era5-single-levels-daily-statistics?tab=overview) are the preferred future bulk-source candidates under CC BY, but are not active providers.
- [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) and [CRU gridded datasets](https://crudata.uea.ac.uk/cru/data/hrg/) were evaluated as documented alternatives but are not active providers.

Current application software and delivery services:

- [Flask](https://flask.palletsprojects.com/en/stable/) and [Flask-Session](https://flask-session.readthedocs.io/en/latest/) provide the web application and server-side sessions.
- [PostgreSQL](https://www.postgresql.org/docs/18/) and [Psycopg](https://www.psycopg.org/psycopg3/docs/) provide climate storage and Python database access.
- [NumPy](https://numpy.org/doc/stable/), [pandas](https://pandas.pydata.org/docs/), and [Plotly Python](https://plotly.com/python/) provide numerical work, monthly aggregation, and charts.
- [Open-Meteo's Python client](https://github.com/open-meteo/python-requests), [requests-cache](https://requests-cache.readthedocs.io/en/stable/), and [retry-requests](https://github.com/MazeMap/retry-requests) provide API transport, local response caching, and bounded retries.
- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) renders maps using the [MapLibre demo style and tiles](https://github.com/maplibre/demotiles).
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/) is delivered through [jsDelivr](https://www.jsdelivr.com/), and the interface loads Audiowide, Space Mono, and Muli through [Google Fonts](https://fonts.google.com/).

Project, learning, and visual sources:

- The original [iktCalT/climate](https://github.com/iktCalT/climate) project was implemented by its human author as a [CS50x](https://cs50.harvard.edu/x/) final project with substantial [ChatGPT](https://chatgpt.com/) guidance. Authentication and error-page helper patterns were adapted from CS50 course material.
- The climate favicon is sourced from [Iconfinder](https://www.iconfinder.com/icons/9079087/global_warming_climate_change_hot_heat_temperature_icon).
- Error images use [Memegen](https://github.com/jacebrowning/memegen) with an inherited Grumpy Cat background; the cultural reference is documented by [Know Your Meme](https://knowyourmeme.com/memes/grumpy-cat). The inherited background's original image licence is not established and should be replaced before broader publication.
- Inactive legacy generated map HTML files under `static/weather_data/` embed [Folium](https://python-visualization.github.io/folium/), [Leaflet](https://leafletjs.com/), [jQuery](https://jquery.com/), [Leaflet.awesome-markers](https://github.com/lennardv2/Leaflet.awesome-markers), [Font Awesome](https://fontawesome.com/), [OpenStreetMap](https://www.openstreetmap.org/copyright), and [CARTO basemaps](https://carto.com/attributions). They are retained only as historical artifacts and are not used by the current MapLibre pages.
- This refactor is produced with [OpenAI Codex](https://openai.com/codex/) under the human owner's direction and review.

## License

See [LICENSE](LICENSE).
