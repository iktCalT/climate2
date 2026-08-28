"""SQLite helpers for weather data. Phase B will swap this for PostgreSQL."""

import sqlite3
from contextlib import contextmanager

WEATHER_DB = "static/weather.db"
CLIMATE_TYPES = ("temp_mean", "temp_max", "temp_min", "precip")


@contextmanager
def weather_db(con=None, path=WEATHER_DB):
    """Yield a connection. Close it only if this helper opened it."""
    owns = con is None
    if owns:
        con = sqlite3.connect(path)
    try:
        yield con
        if owns:
            con.commit()
    except Exception:
        if owns:
            con.rollback()
        raise
    finally:
        if owns:
            con.close()


def fetch_loc_id(lat, lon, con=None):
    """Return loc_id for (lat, lon), inserting the location if needed."""
    try:
        with weather_db(con) as db:
            row = db.execute(
                "SELECT loc_id FROM locations WHERE lat = ? AND lon = ?",
                (lat, lon),
            ).fetchone()
            if row:
                return row[0]
            cur = db.execute(
                "INSERT INTO locations (lat, lon) VALUES (?, ?)",
                (lat, lon),
            )
            return cur.lastrowid
    except sqlite3.Error as e:
        print(f"fetch_loc_id failed for {lat}, {lon}: {e}")
        return False
