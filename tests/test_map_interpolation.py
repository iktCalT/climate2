"""NOAA lattice contract with isolated fake SQL and no acquisition/writes."""
import json
import math
import sys
import unittest
from unittest.mock import MagicMock, patch

from climate.services import map_data


class MapInterpolationTests(unittest.TestCase):
    def payload(self, bounds, rows, provider="noaa_core", zoom=5):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = rows
        with patch.object(map_data, "ACTIVE_CLIMATE_PROVIDER", provider), patch.object(
            map_data, "weather_db"
        ) as database, patch.object(map_data, "get_data", side_effect=AssertionError("fetch")):
            database.return_value.__enter__.return_value = connection
            result = map_data.viewport_geojson("2000-01", "temp_mean", *bounds, zoom, fetch_missing=False)
        cursor.execute.assert_called_once()
        query, parameters = cursor.execute.call_args.args
        self.assertIn("d.provider = %s", query)
        self.assertEqual(parameters[:2], ("2000-01-01", provider))
        self.assertTrue(query.lstrip().startswith("SELECT"))
        connection.commit.assert_not_called()
        return result, parameters

    def test_regular_halo_single_read_nulls_and_legacy_response(self):
        result, parameters = self.payload((0.1, 0.1, 1.9, 3.9), [
            (0, 0, 0), (0, 4, 4), (2, 0, 8), (2, 4, 12),
            (-2, -4, None), (-2, 0, float("nan")), (-2, 4, float("inf")),
            (1, 2, 99),
        ])
        grid = result["interpolation"]
        self.assertEqual(grid["latitudes"], [-2, 0, 2, 4])
        self.assertEqual(grid["longitudes"], [-4, 0, 4, 8])
        self.assertEqual(parameters[2:], (-2, 4, -4, 8))
        self.assertEqual(grid["values"][1:3], [[None, 0, 4, None], [None, 8, 12, None]])
        self.assertEqual(grid["values"][0], [None] * 4)
        self.assertEqual(result["type"], "FeatureCollection")
        self.assertIn("features", result)
        self.assertTrue(result["metadata"]["cache_only"])
        self.assertEqual(result["metadata"]["fetched"], 0)

    def test_world_and_dateline_halo_bounded_8281(self):
        world, parameters = self.payload((-90, -180, 90, 180), [], zoom=0)
        grid = world["interpolation"]
        self.assertEqual(parameters[2:], (-90, 90, -180, 180))
        self.assertEqual(len(grid["latitudes"]) * len(grid["longitudes"]), 8281)
        self.assertEqual(grid["latitudes"], list(range(-90, 91, 2)))
        self.assertEqual(grid["longitudes"], list(range(-180, 181, 4)))
        for west, east, expected in [(-180, -179, [-180, -176, -172]), (179, 180, [172, 176, 180])]:
            result, _ = self.payload((-1, west, 1, east), [])
            self.assertEqual(result["interpolation"]["longitudes"], expected)

    def test_noaa_nonfinite_nodes_remain_holes_and_legacy_json_stays_finite(self):
        for missing in (None, math.nan, math.inf, -math.inf):
            with self.subTest(missing=missing):
                result, _ = self.payload((0, 0, 2, 4), [
                    (0, 0, missing), (0, 4, 4), (2, 0, 8), (2, 4, 12),
                ])
                json.dumps(result, allow_nan=False)
                grid = result["interpolation"]
                row = grid["latitudes"].index(0)
                column = grid["longitudes"].index(0)
                self.assertIsNone(grid["values"][row][column])
                self.assertEqual(grid["values"][row][column + 1], 4)
                self.assertEqual(grid["values"][row + 1][column:column + 2], [8, 12])
                self.assertTrue(result["features"], "finite source nodes still provide legacy features")
                self.assertTrue(all(math.isfinite(feature["properties"]["value"])
                                    for feature in result["features"]))

    def test_noaa_finite_aggregation_overflow_cannot_emit_invalid_json(self):
        maximum = sys.float_info.max
        result, _ = self.payload((0, 0, 2, 4), [
            (0, 0, maximum), (0, 4, maximum), (2, 0, maximum), (2, 4, maximum),
        ], zoom=0)
        json.dumps(result, allow_nan=False)
        self.assertEqual(result["features"], [], "overflowing aggregate is omitted")
        grid = result["interpolation"]
        row = grid["latitudes"].index(0)
        column = grid["longitudes"].index(0)
        self.assertEqual(grid["values"][row][column:column + 2], [maximum, maximum])
        self.assertEqual(grid["values"][row + 1][column:column + 2], [maximum, maximum])

    def test_noaa_default_fetch_flag_cannot_acquire_or_write(self):
        with patch.object(map_data, "ACTIVE_CLIMATE_PROVIDER", "noaa_core"), patch.object(
            map_data, "weather_db"
        ), patch.object(map_data, "_query_weather_rows", return_value=[]) as read, patch.object(
            map_data, "_fetch_missing_cells", side_effect=AssertionError("acquisition")
        ):
            result = map_data.viewport_geojson("2000-01", "precip", 0, 0, 2, 4, 5)
        read.assert_called_once()
        self.assertTrue(result["metadata"]["cache_only"])

    def test_cmip6_retains_polygon_provenance_without_interpolation(self):
        result, _ = self.payload((0, 0, 0.5, 3), [(0.25, 0.5, 17.5)], "open_meteo_cmip6")
        self.assertNotIn("interpolation", result)
        self.assertEqual([feature["properties"]["source"] for feature in result["features"]],
                         ["direct_cache", "nearby_cache", "display_estimate"])
