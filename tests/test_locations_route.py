import os
import unittest
from unittest.mock import patch

import pandas as pd

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/climate")

from app import app


class LocationsRouteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_history_is_drawn_after_a_cache_miss(self):
        history = pd.DataFrame(
            {"temp_mean": [10.0], "precip": [2.0]},
            index=pd.to_datetime(["1950-01-01"]),
        )
        with patch("app.get_location_history", return_value=(history, True)) as load:
            with patch("app.draw_chart") as draw:
                response = self.client.get("/locations?latitude=1&longitude=2")

        self.assertEqual(response.status_code, 200)
        load.assert_called_once()
        draw.assert_called_once()

    def test_unavailable_history_returns_a_service_error(self):
        with patch(
            "app.get_location_history",
            side_effect=RuntimeError("Open-Meteo unavailable"),
        ):
            response = self.client.get("/locations?latitude=1&longitude=2")

        self.assertEqual(response.status_code, 503)
