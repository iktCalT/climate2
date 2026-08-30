# Climate

> [!IMPORTANT]
> This repository is an AI-assisted refactor produced with **OpenAI Codex (GPT-5)**. It is derived from [iktCalT/climate](https://github.com/iktCalT/climate), which its human author implemented as a CS50 final project with substantial guidance from ChatGPT. Keep this work in the `climate2` fork; do not push these commits to the original repository.

Climate is a Flask website for exploring modelled historical climate data. It reads weather values from a local PostgreSQL cache and asks the [Open-Meteo Climate API](https://open-meteo.com/en/docs/climate-api) for missing data before saving and displaying it.

## Current features

- **Maps:** a flat, fullscreen-capable MapLibre map for mean, maximum, or minimum temperature and precipitation from January 1950 through the current month. Opening Maps shows mean temperature for the newest stable month by default, falling back to the previous month during the first six UTC hours of a new month. Tiles form a continuous grid and become finer as the map is enlarged. Tiles reuse direct or sufficiently nearby PostgreSQL observations without requiring the sample to match the tile or zoom center; the permitted neighbor distance shrinks with the tile step as the map is enlarged. A settled viewport requests at most one batch of 12 locations that have no suitable cached neighbor and persists all four metrics for each location. Temporary estimates remain visibly distinguished from cached values.
- **Locations:** displays four seasonal history lines at a time for one latitude/longitude from January 1951 through the current month. Mean temperature is selected by default, with minimum temperature, maximum temperature, and precipitation available from the chart menu. PostgreSQL is checked first, and only missing monthly ranges are fetched.
- **Accounts:** visitors and normal registered users can browse climate data. Administrators can pre-fetch a validated grid of at most 100 locations through `/update`.
- **Local-first storage:** weather data uses PostgreSQL 18. Account and profile data remains in a separate, ignored SQLite file so new personal information is not committed.

The displayed values are climate-model output, not direct station observations. See the in-app References page for data and software attribution.

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

## Attribution

The original project was implemented by its human author as a CS50 final project with substantial guidance from ChatGPT. Parts of its authentication and error-page helpers originated from CS50 course material. Climate data is supplied by Open-Meteo and its listed climate-model providers; the application uses Flask, NumPy, pandas, Plotly, PostgreSQL, psycopg, and MapLibre GL JS.

## License

See [LICENSE](LICENSE).
