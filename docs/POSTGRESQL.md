# Local PostgreSQL 18

The weather database now uses PostgreSQL 18. `static/weather.db` remains only
as the legacy migration source; the Flask weather features no longer read it.
User accounts continue to use `static/users.db`.

PostgreSQL 18.6 is installed locally through Homebrew and runs as a background
service. Before starting Flask in a new terminal, configure the connection:

```sh
export DATABASE_URL='postgresql://localhost/climate'
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
