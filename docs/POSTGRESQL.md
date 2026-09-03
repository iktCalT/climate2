# Local PostgreSQL 18

The weather database now uses PostgreSQL 18. `static/weather.db` remains only
as the legacy migration source; the Flask weather features no longer read it.
User accounts continue to use `static/users.db`.

PostgreSQL 18.6 is installed locally through Homebrew and runs as a background
service. Flask uses `postgresql://localhost/climate` automatically. Set
`DATABASE_URL` only when you want to use a different database:

```sh
.venv/bin/flask --app app run
```

The database has the following tables:

- `locations`: a unique latitude/longitude and its `loc_id`.
- `data`: one row per location/month with a primary key on `(loc_id, dates)`.

Both ingestion and updates use PostgreSQL `ON CONFLICT` upserts. To make a
fresh local database after intentionally deleting it, run:

```sh
/opt/homebrew/opt/postgresql@18/bin/createdb climate
export DATABASE_URL='postgresql://localhost/climate'
.venv/bin/python setup_database.py
.venv/bin/python migrate_weather_sqlite.py static/weather.db
```

The migration is safe to re-run: it upserts locations and weather rows. Do not
commit a real connection string or credentials; `.env` remains ignored if you
choose to keep one for personal reference.

## Resumable edge-period prefetch

The canonical 91-by-91 global grid can be filled for 1950–1953 and 2023–2026
in bounded, resumable batches:

```sh
.venv/bin/python prefetch_climate.py --dry-run
.venv/bin/python prefetch_climate.py --limit 100
```

The database is the only checkpoint. The command counts a period as complete
only when every month has all four climate metrics, fetches missing contiguous
ranges, and commits each successful range separately. An interrupted or
partially failed batch can therefore be resumed with the same command. Live
requests start at least 30 seconds apart by default, and the command stops on
the first provider failure rather than consuming the rest of a batch while a
rate limit is active.
