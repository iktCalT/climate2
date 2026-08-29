import os
import unittest
from unittest.mock import patch

import pandas as pd

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/climate")

from app import app
from map_data import MAX_VIEWPORT_POINTS, _sample_coordinates, step_for_zoom


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

    def test_map_api_returns_viewport_geojson(self):
        payload = {"type": "FeatureCollection", "features": [], "metadata": {"step": 4, "fetched": 0, "missing": 0}}
        with patch("app.viewport_geojson", return_value=payload):
            response = self.client.get("/api/map-data?month=1950-01&climate_type=temp_mean&south=-10&west=-10&north=10&east=10&zoom=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["type"], "FeatureCollection")

    def test_map_sampling_gets_finer_and_broad_views_are_capped(self):
        self.assertGreater(step_for_zoom(2), step_for_zoom(10))
        samples, _ = _sample_coordinates(-90, -180, 90, 180, 2)
        self.assertLessEqual(len(samples), MAX_VIEWPORT_POINTS)
