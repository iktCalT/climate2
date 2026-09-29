"""Offline public-provider and NOAA coordinate regressions."""

import html
import math
import re
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import pandas as pd

from climate.data.location_sampling import sample_noaa_location
from climate.web.app import app
from climate.web.helpers import draw_chart


@contextmanager
def public_provider(provider):
    """Simulate the deploy-time selector in all public-read consumers."""
    old = app.config["CLIMATE_PROVIDER"]
    app.config["CLIMATE_PROVIDER"] = provider
    try:
        with patch("climate.web.app.ACTIVE_CLIMATE_PROVIDER", provider), patch(
            "climate.providers.open_meteo.ACTIVE_CLIMATE_PROVIDER", provider
        ):
            yield
    finally:
        app.config["CLIMATE_PROVIDER"] = old


def history(value=10.0):
    return pd.DataFrame(
        {"temp_mean": [value], "temp_max": [15.0], "temp_min": [5.0], "precip": [2.0]},
        index=pd.to_datetime(["1951-01-01"]),
    )


class NoaaSamplingTests(unittest.TestCase):
    def test_rejects_invalid_nonfinite_and_out_of_range_coordinates(self):
        for coordinates in ((None, 0), ("bad", 0), (math.nan, 0),
                            (0, math.inf), (-math.inf, 0), (90.01, 0), (0, 180.01)):
            with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                sample_noaa_location(*coordinates)

    def test_midpoint_ties_choose_smaller_coordinate(self):
        for coordinates, expected in (((1, 2), (0, 0)), ((-1, -2), (-2, -4)),
                                      ((89, 2), (88, 0)), ((0, -178), (0, -180))):
            with self.subTest(coordinates=coordinates):
                sample = sample_noaa_location(*coordinates)
                self.assertEqual((sample.latitude, sample.longitude), expected)

    def test_dateline_equivalence_pole_and_distances(self):
        self.assertEqual(sample_noaa_location(0, 180), sample_noaa_location(0, -180))
        self.assertEqual(sample_noaa_location(0, 178).longitude, -180)
        self.assertEqual((sample_noaa_location(90, 135).latitude,
                          sample_noaa_location(90, 135).longitude), (90, 0))
        self.assertAlmostEqual(sample_noaa_location(90, 135).distance_km, 0, places=7)
        self.assertAlmostEqual(sample_noaa_location(0, 0).distance_km, 0, places=7)
        self.assertAlmostEqual(sample_noaa_location(1, 0).distance_km, 111.195, places=2)
        self.assertAlmostEqual(sample_noaa_location(0, 180).distance_km, 0, places=7)


class PublicLocationTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def request_history(self, provider, latitude, longitude, data):
        with public_provider(provider), patch(
            "climate.web.app.get_location_history", return_value=(data, False)
        ) as load, patch("climate.web.app.os.path.isfile", return_value=False), patch(
            "climate.web.app.draw_chart"
        ) as chart:
            response = self.client.get(
                f"/locations?latitude={latitude}&longitude={longitude}&fetch_missing=true"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(load.call_count, 1)
        self.assertIs(load.call_args.kwargs["fetch_missing"], False)
        self.assertEqual(load.call_args.kwargs["date_start"], "1951-01-01")
        return response, load.call_args.kwargs, chart

    def test_noaa_uses_one_fixed_sample_and_displays_request_distance(self):
        response, kwargs, chart = self.request_history("noaa_core", 1, 2, history())
        self.assertEqual(kwargs["location"], (0.0, 0.0))
        self.assertEqual(chart.call_count, 1)
        self.assertEqual(chart.call_args.kwargs["sampled_location"], (0.0, 0.0))
        self.assertEqual(chart.call_args.kwargs["source_label"], "NOAA CORe reanalysis")
        page = html.unescape(response.get_data(as_text=True))
        for phrase in ("requested 1.0°N, 2.0°E", "sampled 2° × 4° grid point 0.0°N, 0.0°E",
                       "approximately", "coarse grid sample", "1 of 1 months"):
            self.assertIn(phrase, page)

    def test_cmip6_uses_exact_coordinates(self):
        response, kwargs, chart = self.request_history("open_meteo_cmip6", 1, 2, history())
        self.assertEqual(kwargs["location"], (1.0, 2.0))
        self.assertEqual(chart.call_args.kwargs["sampled_location"], (1.0, 2.0))
        self.assertIn("Open-Meteo CMIP6 model output at the requested coordinates", response.get_data(as_text=True))
        self.assertNotIn("coarse grid sample", response.get_data(as_text=True))

    def test_noaa_missing_sample_does_not_search_or_fetch(self):
        empty = history(float("nan"))
        empty.loc[:, :] = float("nan")
        with public_provider("noaa_core"), patch(
            "climate.web.app.get_location_history", return_value=(empty, False)
        ) as load, patch("climate.web.app.draw_chart") as chart:
            response = self.client.get("/locations?latitude=1&longitude=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(load.call_count, 1)
        self.assertEqual(load.call_args.kwargs["location"], (0.0, 0.0))
        self.assertIs(load.call_args.kwargs["fetch_missing"], False)
        chart.assert_not_called()
        self.assertIn(b"No saved climate data for this NOAA grid sample", response.data)
        self.assertNotIn(b"<iframe", response.data)

    def test_chart_identity_tracks_request_sample_provider_and_values(self):
        requests = (("noaa_core", 1, 2, history()),
                    ("noaa_core", 0.5, 2, history()),
                    ("noaa_core", 1, 4.5, history()),
                    ("open_meteo_cmip6", 1, 2, history()),
                    ("noaa_core", 1, 2, history(11.0)))
        names = [self.request_history(*case)[2].call_args.kwargs["filename"] for case in requests]
        self.assertEqual(len(names), len(set(names)))

    def test_invalid_http_coordinates_never_load_history(self):
        with public_provider("noaa_core"), patch("climate.web.app.get_location_history") as load:
            for query in ("latitude=nan&longitude=0", "latitude=0&longitude=inf",
                          "latitude=91&longitude=0"):
                with self.subTest(query=query):
                    self.assertEqual(self.client.get("/locations?" + query).status_code, 400)
        load.assert_not_called()

    def test_generated_chart_titles_follow_source_for_all_metrics(self):
        for provider, label in (("noaa_core", "NOAA CORe reanalysis"),
                                ("open_meteo_cmip6", "Open-Meteo CMIP6 model output")):
            with self.subTest(provider=provider):
                figure = draw_chart(1, 2, history(), source_label=label,
                                    sampled_location=(0, 0) if provider == "noaa_core" else (1, 2))
                self.assertIn(label, figure.layout.title.text)
                self.assertIn("requested 1, 2", figure.layout.title.text)
                for button in figure.layout.updatemenus[0].buttons:
                    self.assertIn(label, button.args[1]["title.text"])
                    self.assertIn("requested 1, 2", button.args[1]["title.text"])


class ProviderCopyTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_public_pages_follow_source_without_losing_navigation_or_credits(self):
        references_by_provider = {}
        with patch("climate.web.app.saved_map_months", return_value=[]):
            for provider, active, inactive in (("noaa_core", "NOAA CORe", "Open-Meteo CMIP6"),
                                               ("open_meteo_cmip6", "Open-Meteo CMIP6", "NOAA CORe")):
                with public_provider(provider):
                    pages = {path: self.client.get(path).get_data(as_text=True)
                             for path in ("/", "/maps?select=1", "/locations", "/references")}
                for path, page in pages.items():
                    with self.subTest(provider=provider, path=path):
                        if path == "/references" and provider == "open_meteo_cmip6":
                            self.assertIn("Open-Meteo's downscaled CMIP6", page)
                        else:
                            self.assertIn(active, page)
                        self.assertIn(f'data-climate-provider="{provider}"', page)
                        if path != "/references":
                            self.assertIn('href="/references"', page)
                references_by_provider[provider] = set(re.findall(r'href="(https://[^\"]+)"', pages["/references"]))
                self.assertIn("inactive for public Maps and Locations", pages["/references"])
                self.assertIn("mean daily mm/day, not a monthly total", pages["/references"])
                self.assertIn("Historical import and validation details", pages["/references"])
                self.assertIn("not silently mixed", pages["/references"])
                self.assertIn(inactive, pages["/references"])
                if provider == "noaa_core":
                    self.assertIn("rounds latitude and longitude separately to one fixed 2° × 4° grid point", pages["/"])
                    self.assertIn("rounds latitude and longitude separately to one fixed 2° × 4° NOAA grid point", pages["/locations"])
                    self.assertIn("reanalysis", pages["/maps?select=1"])
                    self.assertIn("NOAA CORe</a>", pages["/"])
                    self.assertNotIn('aria-label="Open-Meteo Climate API"', pages["/"])
                else:
                    self.assertIn("inherited ocean temperatures remain suspect", pages["/"])
                    self.assertIn('aria-label="Open-Meteo Climate API"', pages["/"])
        self.assertEqual(references_by_provider["noaa_core"],
                         references_by_provider["open_meteo_cmip6"])


if __name__ == "__main__":
    unittest.main()
