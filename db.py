"""PostgreSQL access for the application's weather data.

Set ``DATABASE_URL`` in the shell that runs Flask. All weather code uses this
module instead of opening database connections itself.
"""

from contextlib import contextmanager
import os

try:
    import psycopg
except ImportError:  # Lets non-database commands explain the missing dependency.
    psycopg = None


CLIMATE_TYPES = ("temp_mean", "temp_max", "temp_min", "precip")


def database_url():
    """Return the required PostgreSQL connection string."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Export it before starting the app; see "
            "docs/POSTGRESQL.md."
        )
    return url


@contextmanager
def weather_db(con=None):
    """Yield a PostgreSQL connection and manage its transaction if we opened it."""
    owns_connection = con is None
    if owns_connection:
        if psycopg is None:
            raise RuntimeError(
                "PostgreSQL support is not installed. Run `pip install -r requirements.txt`."
            )
        con = psycopg.connect(database_url())
    try:
        yield con
        if owns_connection:
            con.commit()
    except Exception:
        if owns_connection:
            con.rollback()
        raise
    finally:
        if owns_connection:
            con.close()


def fetch_loc_id(lat, lon, con=None):
    """Return the location id, creating the location atomically when needed."""
    with weather_db(con) as db:
        with db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO locations (lat, lon)
                VALUES (%s, %s)
                ON CONFLICT (lat, lon) DO UPDATE SET lat = EXCLUDED.lat
                RETURNING loc_id
                """,
                (float(lat), float(lon)),
            )
            return cur.fetchone()[0]
