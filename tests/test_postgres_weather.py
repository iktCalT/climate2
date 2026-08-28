import os
import unittest

import numpy as np

from db import database_url, fetch_loc_id, weather_db


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "DATABASE_URL is not configured")
class PostgreSQLWeatherTests(unittest.TestCase):
    """Integration tests against a local PostgreSQL database created by setup_database.py."""

    TEST_DATE = "2099-01-01"

    def tearDown(self):
        """Remove only the row created by this test; never clear real climate data."""
        with weather_db() as con:
            with con.cursor() as cur:
                cur.execute("DELETE FROM data WHERE dates = %s", (self.TEST_DATE,))

    def test_location_upsert_and_numpy_grid_lookup(self):
        from helpers_maps import fetch_data

        lats = np.linspace(-90, 90, 91)
        lons = np.linspace(-180, 180, 91)
        with weather_db() as con:
            loc_id = fetch_loc_id(lats[45], lons[45], con=con)
            self.assertEqual(loc_id, fetch_loc_id(lats[45], lons[45], con=con))
            with con.cursor() as cur:
                cur.execute(
                    "INSERT INTO data (loc_id, dates, temp_mean) VALUES (%s, %s, %s)",
                    (loc_id, self.TEST_DATE, 12.5),
                )

            _, _, grid = fetch_data(
                shape=(91, 91), date=self.TEST_DATE, climate_type="temp_mean", con=con
            )
        self.assertEqual(grid[45, 45], 12.5)
        self.assertTrue(np.isnan(grid[0, 0]))

    def test_invalid_variable_is_rejected(self):
        from helpers_maps import fetch_data

        with self.assertRaises(ValueError):
            fetch_data(climate_type="humidity")


class ConfigurationTests(unittest.TestCase):
    def test_missing_database_url_has_helpful_error(self):
        original = os.environ.pop("DATABASE_URL", None)
        try:
            with self.assertRaises(RuntimeError):
                database_url()
        finally:
            if original is not None:
                os.environ["DATABASE_URL"] = original


if __name__ == "__main__":
    unittest.main()
