# Project structure

The layout groups existing code by responsibility. Routes, provider identifiers,
SQL behavior, and user data paths are preserved; this is not a framework or
database migration. Start the app from the repo root with `./run.sh`.

```text
app.py                  Flask entry point; implementation below
gunicorn.conf.py        explicit production WSGI launch; local run.sh unchanged
Dockerfile              optional non-root production image; no local state bundled
climate/
  production.py         validated production storage/hosts and peer-gated proxy trust
  web/                  app.py routes; helpers.py charts, auth, validation
  services/             map_data.py, admin_import.py, admin_cleanup.py
                        community.py: bounded public pins in private SQLite
  providers/            open_meteo.py, noaa_core.py
  data/                 db.py, cache_availability.py, months.py
  cli/                  explicit setup, ingest, comparison, account commands
  paths.py              source-relative template, static, and SQL resources
sql/                    schema.sql, user_schema.sql, admin_import.sql
templates/              Jinja pages
static/                 browser JS/CSS/images; ignored local data stays in place
tests/                  unittest checks and dependency-free Node map suites
docs/                   requirements, operating guides, shared agent memory
```

## Boundaries

`web` validates HTTP requests and handles permissions/presentation. `services`
coordinates application work; `providers` handles source retrieval and
validation; `data` holds connections, saved-data queries, and shared calendar
helpers. `cli` calls these modules for explicit administration. Shared services
must not import the Flask app or CLI commands. Package initializers have no
startup side effects. The Flask app remains module-level; an app-factory or
Blueprint migration is a separate design task.

`OPEN_METEO_PROVIDER` identifies acquisition and legacy-migration writes;
`ACTIVE_CLIMATE_PROVIDER` selects public cache reads. Never use the public
selector to label source writes. Open-Meteo fallback is disabled when public
reads select another provider; comparisons always use explicit NOAA/CMIP6 IDs.
The public selector is a startup code setting, not a runtime configuration API;
restart all application workers after changing it. NOAA Location requests use
`data/location_sampling.py` to round coordinates to one fixed saved grid point.

Some inherited boundaries are intentionally preserved: Open-Meteo aggregation
and cache access share a module, NOAA retrieval and upserts share a module,
and administrator cleanup shares the import service's lock helper. Do not
silently redesign these contracts during another file move.

## Commands and path compatibility

Run from the repository root using the existing `.venv`:

```sh
./run.sh
.venv/bin/python -m climate.cli.setup_database
.venv/bin/python -m climate.cli.setup_user_database
.venv/bin/python -m climate.cli.manage_users --help
.venv/bin/python -m climate.cli.import_noaa_core --help
.venv/bin/python -m climate.cli.compare_climate_providers --help
.venv/bin/python -m climate.cli.prefetch_climate --help
```

The root `app.py` still supports Flask/WSGI `app:app`. Old root Python commands
now use `python -m climate.cli.<old_stem>`; importing root helpers is replaced
by package imports. Update any personal launch commands accordingly. SQL files
live under `sql/`. Setup resolves schemas relative to source, as Flask resolves
templates/static assets. Runtime data paths, sessions, chart caches, and explicit
relative environment paths retain their previous root-working-directory behavior;
`run.sh` changes to the repository root before starting Flask.

Production is opt-in via `CLIMATE_ENV=production`, with a required private
persistent state root outside the source checkout. Account CLI commands use the
same production account path. Sessions, account/community databases and generated
files are separated beneath that root; only narrowly named charts/profile images
retain their existing public static URLs. Development paths are unchanged.
See [production operation](DEPLOYMENT.md) for startup, proxy trust and host limits.
The optional image has not been built here; Cloud Run's ephemeral filesystem is
not a supported durable deployment for the current local-store design.

Account paths are shared through `climate/paths.py`: new installations use
private `instance/users.db`; explicit configuration and warned legacy fallback
preserve existing accounts. See [storage and relocation](USER_ROLES.md#private-account-storage).
Flask denies private static downloads; separate static servers need their own
restrictions. Account initialization closes its connection deterministically.

Old `helpers_data.py` is `climate/providers/open_meteo.py`; other moved modules
retain their filenames in the directories above. Historical requirement entries
and the fixed `REFACTOR.md` may mention old paths; use this guide for navigation.

## Verification and agents

```sh
DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 \
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests
node --test tests/test_map*.mjs
node --test tests/test_community*.mjs
```

The empty `DATABASE_URL` and zero-valued opt-in flags keep PostgreSQL integration
tests skipped even when other tests set a default. Node runs all map suites,
including interpolation, selection, coordinates, scales and template lifecycle.
Do not enable integration flags against a live
climate database. Database-backed checks require an explicitly isolated test
database; see [PostgreSQL operations](POSTGRESQL.md). No live import, cleanup,
or migration is part of ordinary verification.

Agent entry point: [AGENTS.md](../AGENTS.md). Current ownership and fork prompts
are on the [task board](AGENT_TASKS.md). Find relevant history through the
[context lookup](agents/CONTEXT_INDEX.md), rather than loading all past notes.
