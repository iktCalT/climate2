"""One-time migration of weather rows from the legacy SQLite database.

Usage: python migrate_weather_sqlite.py [path/to/weather.db]
The PostgreSQL schema must already exist and DATABASE_URL must be set.
"""

import sqlite3
import sys

from db import weather_db


BATCH_SIZE = 10_000


def migrate(sqlite_path="static/weather.db"):
    source = sqlite3.connect(sqlite_path)
    source.row_factory = sqlite3.Row
    try:
        with weather_db() as target:
            with target.cursor() as cur:
                locations = source.execute("SELECT loc_id, lat, lon FROM locations")
                for row in locations:
                    cur.execute(
                        """
                        INSERT INTO locations (loc_id, lat, lon)
                        OVERRIDING SYSTEM VALUE VALUES (%s, %s, %s)
                        ON CONFLICT (loc_id) DO UPDATE
                        SET lat = EXCLUDED.lat, lon = EXCLUDED.lon
                        """,
                        (row["loc_id"], row["lat"], row["lon"]),
                    )

                rows = source.execute(
                    "SELECT loc_id, dates, temp_mean, temp_max, temp_min, precip FROM data"
                )
                while batch := rows.fetchmany(BATCH_SIZE):
                    cur.executemany(
                        """
                        INSERT INTO data (loc_id, dates, temp_mean, temp_max, temp_min, precip)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (loc_id, dates) DO UPDATE SET
                            temp_mean = EXCLUDED.temp_mean,
                            temp_max = EXCLUDED.temp_max,
                            temp_min = EXCLUDED.temp_min,
                            precip = EXCLUDED.precip
                        """,
                        [tuple(row) for row in batch],
                    )
                cur.execute(
                    "SELECT setval(pg_get_serial_sequence('locations', 'loc_id'), "
                    "COALESCE((SELECT MAX(loc_id) FROM locations), 1), true)"
                )
    finally:
        source.close()


if __name__ == "__main__":
    migrate(sys.argv[1] if len(sys.argv) > 1 else "static/weather.db")
    print("SQLite weather data migrated to PostgreSQL.")
