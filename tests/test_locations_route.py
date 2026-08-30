from datetime import datetime, timezone
import os
import unittest
from unittest.mock import patch

import pandas as pd

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/climate")

from app import app, default_map_month
from map_data import (
    MAX_VIEWPORT_POINTS,
    _estimated_values,
    _fetch_missing_cells,
    _nearby_cached_values,
    _sample_coordinates,
    _viewport_cells,
    step_for_zoom,
    viewport_geojson,
)


class LocationsRouteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_history_is_drawn_after_a_cache_miss(self):
        history = pd.DataFrame(
            {
                "temp_mean": [10.0],
                "temp_max": [15.0],
                "temp_min": [5.0],
                "precip": [2.0],
            },
            index=pd.to_datetime(["1951-01-01"]),
        )
        with patch("app.get_location_history", return_value=(history, True)) as load:
            with patch("app.draw_chart") as draw:
                response = self.client.get("/locations?latitude=1&longitude=2")

        self.assertEqual(response.status_code, 200)
        load.assert_called_once()
        self.assertEqual(load.call_args.kwargs["date_start"], "1951-01-01")
        self.assertEqual(
            load.call_args.kwargs["fields"],
            ("temp_mean", "temp_max", "temp_min", "precip"),
        )
        self.assertEqual(
            pd.Period(load.call_args.kwargs["date_end"], freq="M"),
            pd.Timestamp.today().to_period("M"),
        )
        draw.assert_called_once()

    def test_cached_history_reuses_the_existing_chart_on_refresh(self):
        history = pd.DataFrame(
            {
                "temp_mean": [10.0],
                "temp_max": [15.0],
                "temp_min": [5.0],
                "precip": [2.0],
            },
            index=pd.to_datetime(["2026-01-01"]),
        )
        with patch("app.get_location_history", return_value=(history, False)) as load:
            with patch("app.os.path.isfile", return_value=True):
                with patch("app.draw_chart") as draw:
                    response = self.client.get(
                        "/locations?latitude=10&longitude=10"
                    )

        self.assertEqual(response.status_code, 200)
        load.assert_called_once()
        draw.assert_not_called()
        self.assertIn(b"Refreshing rechecks PostgreSQL", response.data)

    def test_location_form_describes_the_full_history_range(self):
        response = self.client.get("/locations")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"from 1951 through the current month", response.data)
        self.assertIn(b"maximum, and minimum temperature", response.data)

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

    def test_maps_and_api_accept_the_current_month(self):
        with patch("app.latest_map_month", return_value="2026-08"):
            form = self.client.get("/maps?select=1")
            with patch("app.viewport_geojson", return_value={"type": "FeatureCollection", "features": [], "metadata": {}}):
                page = self.client.get("/maps?month-picker=2026-08&data-type=temp_mean")
                api = self.client.get("/api/map-data?month=2026-08&climate_type=temp_mean&south=-10&west=-10&north=10&east=10&zoom=2")

        self.assertEqual(form.status_code, 200)
        self.assertIn(b'max="2026-08"', form.data)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(api.status_code, 200)

    def test_maps_opens_the_default_month_and_mean_temperature(self):
        with patch("app.latest_map_month", return_value="2026-08"):
            with patch("app.default_map_month", return_value="2026-08"):
                response = self.client.get("/maps")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"temp_mean for 2026-08", response.data)
        self.assertIn(b'href="/maps?select=1"', response.data)

    def test_default_map_month_uses_previous_month_early_on_day_one(self):
        early_new_year = datetime(2027, 1, 1, 5, 59, tzinfo=timezone.utc)

        self.assertEqual(default_map_month(early_new_year), "2026-12")

    def test_default_map_month_switches_to_current_month_after_six_utc(self):
        ready = datetime(2027, 1, 1, 6, 0, tzinfo=timezone.utc)

        self.assertEqual(default_map_month(ready), "2027-01")

    def test_maps_and_api_reject_a_future_month(self):
        with patch("app.latest_map_month", return_value="2026-08"):
            page = self.client.get("/maps?month-picker=2026-09&data-type=temp_mean")
            api = self.client.get("/api/map-data?month=2026-09&climate_type=temp_mean&south=-10&west=-10&north=10&east=10&zoom=2")

        self.assertEqual(page.status_code, 400)
        self.assertEqual(api.status_code, 400)

    def test_map_sampling_gets_finer_and_broad_views_are_capped(self):
        self.assertGreater(step_for_zoom(2)[0], step_for_zoom(10)[0])
        samples, _ = _sample_coordinates(-90, -180, 90, 180, 2)
        self.assertLessEqual(len(samples), MAX_VIEWPORT_POINTS)

    def test_viewport_tiles_share_exact_edges(self):
        cells, _, _, _, _ = _viewport_cells(-4, 100, 4, 108, 4)
        indexed = {cell["index"]: cell for cell in cells}
        first = indexed[(0, 0)]
        east_neighbour = indexed[(0, 1)]
        north_neighbour = indexed[(1, 0)]
        self.assertEqual(first["east"], east_neighbour["west"])
        self.assertEqual(first["north"], north_neighbour["south"])

    def test_missing_tiles_receive_a_temporary_estimate(self):
        cells, _, _, _, _ = _viewport_cells(-2, 100, 2, 104, 5)
        estimates = _estimated_values(cells, {cells[0]["index"]: [17.5]})
        self.assertEqual(len(estimates), len(cells) - 1)
        self.assertTrue(all(value == 17.5 for value in estimates.values()))

    def test_nearby_cache_reuse_is_limited_by_the_current_tile_step(self):
        cells, _, _, lat_step, lon_step = _viewport_cells(0, 0, 0.5, 3, 5)
        cached_cell = cells[0]
        cached_row = (
            cached_cell["latitude"],
            cached_cell["longitude"],
            17.5,
        )

        reused = _nearby_cached_values(
            cells,
            [cached_row],
            {cached_cell["index"]: [17.5]},
            lat_step,
            lon_step,
        )

        self.assertEqual(reused[cells[1]["index"]], 17.5)
        self.assertNotIn(cells[2]["index"], reused)

    def test_cache_just_outside_viewport_can_satisfy_an_edge_tile(self):
        cells, _, _, lat_step, lon_step = _viewport_cells(0, 0, 0.5, 1, 5)
        reused = _nearby_cached_values(
            cells,
            [(cells[0]["latitude"], -0.5, 12.0)],
            {},
            lat_step,
            lon_step,
        )

        self.assertEqual(reused[cells[0]["index"]], 12.0)

    def test_map_cache_excludes_direct_and_nearby_cells_from_provider_batch(self):
        cells, _, _, _, _ = _viewport_cells(0, 0, 0.5, 3, 5)
        cached_cell = cells[0]
        cached_row = (
            cached_cell["latitude"],
            cached_cell["longitude"],
            17.5,
        )
        with patch("map_data.weather_db"):
            with patch(
                "map_data._query_weather_rows", return_value=[cached_row]
            ) as query:
                with patch(
                    "map_data._fetch_missing_cells", return_value=0
                ) as fetch:
                    payload = viewport_geojson(
                        "2026-08", "temp_mean", 0, 0, 0.5, 3, 5
                    )

        fetched_cells = fetch.call_args.args[1]
        fetched_indices = [cell["index"] for cell in fetched_cells]
        self.assertNotIn(cached_cell["index"], fetched_indices)
        self.assertNotIn(cells[1]["index"], fetched_indices)
        self.assertIn(cells[2]["index"], fetched_indices)
        self.assertEqual(payload["metadata"]["cached"], 2)
        self.assertEqual(payload["metadata"]["direct"], 1)
        self.assertEqual(payload["metadata"]["reused_nearby"], 1)
        self.assertEqual(payload["metadata"]["fetched"], 0)
        self.assertEqual(payload["metadata"]["missing"], 1)
        self.assertEqual(query.call_args.args[5], 0.75)
        self.assertEqual(query.call_args.args[6], 1.5)
        sources = [
            feature["properties"]["source"] for feature in payload["features"]
        ]
        self.assertEqual(
            sources,
            ["direct_cache", "nearby_cache", "display_estimate"],
        )

    def test_one_map_fetch_caches_every_metric_for_a_location(self):
        cells, _, _, _, _ = _viewport_cells(-2, 100, 2, 104, 5)
        with patch("map_data.get_data", return_value=True) as fetch:
            fetched = _fetch_missing_cells(object(), cells[:1], "2026-08")

        self.assertEqual(fetched, 1)
        self.assertEqual(
            fetch.call_args.kwargs["meteo_types"],
            (
                "temperature_2m_mean",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
            ),
        )

    def test_estimates_use_the_nearest_observed_cell(self):
        cells, _, _, _, _ = _viewport_cells(0, 0, 2, 6, 4)
        west = cells[0]
        east = cells[-1]
        estimates = _estimated_values(
            cells,
            {
                west["index"]: [5.0],
                east["index"]: [25.0],
            },
        )

        self.assertEqual(estimates[cells[1]["index"]], 5.0)
        self.assertEqual(estimates[cells[-2]["index"]], 25.0)

    def test_map_data_rejects_negative_zoom_before_opening_database(self):
        with self.assertRaisesRegex(ValueError, "Zoom must be non-negative"):
            viewport_geojson("2026-08", "temp_mean", -10, -10, 10, 10, -1)

    def test_map_page_cancels_stale_requests_and_clips_world_bounds(self):
        with patch("app.latest_map_month", return_value="2026-08"):
            response = self.client.get(
                "/maps?month-picker=2026-08&data-type=temp_mean"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"requestController?.abort()", response.data)
        self.assertIn(b"Math.max(-180, bounds.getWest())", response.data)
        self.assertIn(b"renderWorldCopies: false", response.data)
        self.assertIn(b'map.setProjection({type: "mercator"})', response.data)
        self.assertIn(b"FullscreenControl", response.data)
        self.assertIn(b"map.addControl(new FullscreenControl())", response.data)
        self.assertIn(b"loaded from PostgreSQL before this batch", response.data)
        self.assertIn(b"nearby-cache cells", response.data)
        self.assertIn(b"Reused nearby PostgreSQL observation", response.data)
        self.assertIn(b"startViewportLoad", response.data)
        self.assertEqual(response.data.count(b"fetch(`/api/map-data?${query}`"), 1)
        self.assertNotIn(b"fetching another batch", response.data)
        self.assertNotIn(b'projection: "mercator"', response.data)
