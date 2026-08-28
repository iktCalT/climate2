import sqlite3
import unittest

import numpy as np

from db import fetch_loc_id
from helpers_maps import fetch_data


def _memory_weather_db():
    con = sqlite3.connect(":memory:")
    con.execute(
        "CREATE TABLE locations (loc_id INTEGER PRIMARY KEY, lat REAL, lon REAL)"
    )
    con.execute(
        """
        CREATE TABLE data (
            loc_id INTEGER,
            dates TEXT,
            temp_mean REAL,
            temp_max REAL,
            temp_min REAL,
            precip REAL
        )
        """
    )
    return con


class FetchDataTests(unittest.TestCase):
    def test_one_query_scatters_onto_grid(self):
        con = _memory_weather_db()
        lats = np.linspace(-90, 90, 91)
        lons = np.linspace(-180, 180, 91)
        loc_id = fetch_loc_id(lats[10], lons[20], con=con)
        con.execute(
            "INSERT INTO data (loc_id, dates, temp_mean) VALUES (?, ?, ?)",
            (loc_id, "1950-01-01 00:00:00", 12.5),
        )
        con.commit()

        out_lats, out_lons, grid = fetch_data(
            shape=(91, 91),
            date="1950-01-01",
            climate_type="temp_mean",
            con=con,
        )
        self.assertEqual(len(out_lats), 91)
        self.assertEqual(len(out_lons), 91)
        self.assertEqual(grid[10, 20], 12.5)
        self.assertTrue(np.isnan(grid[0, 0]))

    def test_rejects_unknown_climate_type(self):
        con = _memory_weather_db()
        with self.assertRaises(ValueError):
            fetch_data(climate_type="humidity", con=con)

    def test_fetch_loc_id_inserts_once(self):
        con = _memory_weather_db()
        a = fetch_loc_id(1.0, 2.0, con=con)
        b = fetch_loc_id(1.0, 2.0, con=con)
        self.assertEqual(a, b)
        count = con.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
