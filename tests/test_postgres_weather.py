import os
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from db import database_url, fetch_loc_id, weather_db
from helpers_data import get_location_history, modify_database


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "DATABASE_URL is not configured")
class PostgreSQLWeatherTests(unittest.TestCase):
    """Integration tests against a local PostgreSQL database created by setup_database.py."""

    TEST_DATE = "2099-01-01"

    def tearDown(self):
        """Remove only the row created by this test; never clear real climate data."""
        with weather_db() as con:
            with con.cursor() as cur:
                cur.execute("DELETE FROM data WHERE dates >= %s", (self.TEST_DATE,))

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

    def test_location_history_uses_complete_cache_without_api_call(self):
        location = (12.345678, 67.890123)
        with weather_db() as con:
            loc_id = fetch_loc_id(*location, con=con)
            with con.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO data (loc_id, dates, temp_mean, precip)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (loc_id, self.TEST_DATE, 10.0, 2.0),
                )
            with patch("helpers_data.get_data") as fetch:
                history, fetched = get_location_history(
                    location, self.TEST_DATE, self.TEST_DATE, con=con
                )

        self.assertFalse(fetched)
        fetch.assert_not_called()
        self.assertEqual(history.loc[pd.Timestamp(self.TEST_DATE), "temp_mean"], 10.0)

    def test_location_history_fetches_and_upserts_a_missing_month(self):
        location = (-12.345678, -67.890123)
        missing_month = "2099-02-01"

        def fake_get_data(**kwargs):
            loc_id = fetch_loc_id(*kwargs["location"], con=kwargs["con"])
            data = pd.DataFrame(
                {"loc_id": [loc_id], "temp_mean": [15.0], "precip": [3.0]},
                index=pd.to_datetime([missing_month]),
            )
            return modify_database(data, type="update", con=kwargs["con"])

        with weather_db() as con:
            with patch("helpers_data.get_data", side_effect=fake_get_data) as fetch:
                history, fetched = get_location_history(
                    location, missing_month, missing_month, con=con
                )

        self.assertTrue(fetched)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(history.loc[pd.Timestamp(missing_month), "precip"], 3.0)


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
