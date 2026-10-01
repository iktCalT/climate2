from datetime import datetime, timezone
import os
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from unittest.mock import patch

import pandas as pd

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/climate")

from climate.web.app import app, default_map_month
from climate.data.db import OPEN_METEO_PROVIDER
from climate.services.map_data import (
    MAX_FETCH_PER_VIEWPORT,
    MAX_ZOOM,
    MAX_VIEWPORT_POINTS,
    _estimated_values,
    _fetch_missing_cells,
    _nearby_cached_values,
    _sample_coordinates,
    _viewport_cells,
    step_for_zoom,
    viewport_geojson,
)

MAP_METRIC_LABELS = {
    "temp_mean": "Mean temperature (°C)",
    "temp_max": "Maximum temperature (°C)",
    "temp_min": "Minimum temperature (°C)",
    "precip": "Mean daily precipitation (mm/day)",
}


class CoordinateFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.labels = {}
        self.inputs = {}
        self.forms = []
        self.current_label = None
        self.guidance = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "label":
            self.current_label = attrs.get("for")
            if self.current_label:
                self.labels[self.current_label] = ""
        elif tag == "input" and attrs.get("id"):
            self.inputs[attrs["id"]] = attrs
        elif tag == "form" and attrs.get("action") == "/locations":
            self.forms.append(attrs)
        elif attrs.get("id") == "coordinate-guidance":
            self.in_guidance = True

    def handle_endtag(self, tag):
        if tag == "label":
            self.current_label = None
        elif tag == "p":
            self.in_guidance = False

    def handle_data(self, data):
        if self.current_label:
            self.labels[self.current_label] += data
        if getattr(self, "in_guidance", False):
            self.guidance.append(data)


class MapSelectionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.change_selection_href = None
        self.month_inputs = []
        self.data_type_options = []
        self.data_type_labels = {}
        self.map_headings = []
        self.page_headings = []
        self.map_aria_labels = []
        self._in_data_type = False
        self._in_data_type_option = None
        self._in_map_heading = False
        self._in_page_heading = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("class") == "btn btn-success":
            self.change_selection_href = attrs.get("href")
        elif tag == "input" and attrs.get("name") == "month-picker":
            self.month_inputs.append(attrs)
        elif tag == "select" and attrs.get("id") == "data-type":
            self._in_data_type = True
        elif tag == "option" and self._in_data_type:
            self.data_type_options.append(attrs)
            self._in_data_type_option = attrs.get("value")
            self.data_type_labels[self._in_data_type_option] = ""
        elif tag == "h3" and attrs.get("id", "").startswith("map-heading-"):
            self._in_map_heading = True
        elif tag == "h2" and "fs-4" in attrs.get("class", "").split():
            self._in_page_heading = True
        elif tag == "div" and attrs.get("class") == "climate-map":
            self.map_aria_labels.append(attrs.get("aria-label"))

    def handle_endtag(self, tag):
        if tag == "select":
            self._in_data_type = False
        elif tag == "option":
            self._in_data_type_option = None
        elif tag == "h3":
            self._in_map_heading = False
        elif tag == "h2":
            self._in_page_heading = False

    def handle_data(self, data):
        if self._in_map_heading and data.strip():
            self.map_headings.append(data.strip())
        if self._in_page_heading and data.strip():
            self.page_headings.append(data.strip())
        if self._in_data_type_option and data.strip():
            self.data_type_labels[self._in_data_type_option] += data.strip()


class LocationsRouteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        availability_patch = patch("climate.web.app.saved_map_months", return_value=[
            {"month": "2026-08", "counts": {"temp_mean": 10, "temp_max": 10, "temp_min": 10, "precip": 10}}
        ])
        self.availability = availability_patch.start()
        self.addCleanup(availability_patch.stop)

    def test_saved_history_is_drawn_without_requesting_downloads(self):
        history = pd.DataFrame(
            {
                "temp_mean": [10.0],
                "temp_max": [15.0],
                "temp_min": [5.0],
                "precip": [2.0],
            },
            index=pd.to_datetime(["1951-01-01"]),
        )
        with patch("climate.web.app.get_location_history", return_value=(history, False)) as load:
            with patch("climate.web.app.draw_chart") as draw:
                response = self.client.get("/locations?latitude=1&longitude=2")

        self.assertEqual(response.status_code, 200)
        load.assert_called_once()
        self.assertIs(load.call_args.kwargs["fetch_missing"], False)
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
        with patch("climate.web.app.get_location_history", return_value=(history, False)) as load:
            with patch("climate.web.app.os.path.isfile", return_value=True):
                with patch("climate.web.app.draw_chart") as draw:
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

    def test_coordinate_form_semantics_render_without_database_access(self):
        with patch("climate.web.app.saved_map_months", side_effect=AssertionError("database read")), \
             patch("climate.web.app.get_location_history", side_effect=AssertionError("history read")):
            response = self.client.get("/locations")

        self.assertEqual(response.status_code, 200)
        parser = CoordinateFormParser()
        parser.feed(response.get_data(as_text=True))
        self.assertIn({"action": "/locations", "method": "get", "class": "mx-auto", "style": "width:100%;max-width:640px"}, parser.forms)
        self.assertEqual(parser.labels["latitude"].strip(), "Latitude (°N):")
        self.assertEqual(parser.labels["longitude"].strip(), "Longitude (°E):")
        for identifier, minimum, maximum in (("latitude", "-90", "90"), ("longitude", "-180", "180")):
            field = parser.inputs[identifier]
            self.assertEqual(field["type"], "number")
            self.assertEqual(field["step"], "any")
            self.assertEqual(field["min"], minimum)
            self.assertEqual(field["max"], maximum)
            self.assertEqual(field["aria-describedby"], "coordinate-guidance")
            self.assertIn(identifier, parser.labels)
        guidance = " ".join(parser.guidance)
        self.assertIn("Negative latitude is south", guidance)
        self.assertIn("negative longitude is west", guidance)

    def test_unavailable_history_returns_a_service_error(self):
        with patch(
            "climate.web.app.get_location_history",
            side_effect=RuntimeError("Open-Meteo unavailable"),
        ):
            response = self.client.get("/locations?latitude=1&longitude=2")

        self.assertEqual(response.status_code, 503)

    def test_map_api_returns_viewport_geojson(self):
        payload = {"type": "FeatureCollection", "features": [], "metadata": {"step": 4, "fetched": 0, "missing": 0}}
        with patch("climate.web.app.viewport_geojson", return_value=payload) as viewport:
            for climate_type in MAP_METRIC_LABELS:
                with self.subTest(climate_type=climate_type):
                    response = self.client.get(
                        "/api/map-data?month=1950-01&climate_type="
                        f"{climate_type}&south=-10&west=-10&north=10&east=10&zoom=2&fetch_missing=true"
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json["type"], "FeatureCollection")
                    self.assertEqual(viewport.call_args.args[:2], ("1950-01", climate_type))
                    self.assertIs(viewport.call_args.kwargs["fetch_missing"], False)

    def test_empty_location_shows_no_stale_chart_and_no_download(self):
        history = pd.DataFrame(float("nan"), index=pd.date_range("2022-01-01", periods=3, freq="MS"),
                               columns=["temp_mean", "temp_max", "temp_min", "precip"])
        with (patch("climate.web.app.get_location_history", return_value=(history, False)) as load,
              patch("climate.web.app.os.path.isfile", return_value=True), patch("climate.web.app.draw_chart") as draw):
            response = self.client.get("/locations?latitude=0&longitude=0&fetch_missing=true")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No saved climate data", response.data)
        self.assertIn(b"0 of 3 months", response.data)
        self.assertNotIn(b"<iframe", response.data)
        self.assertIs(load.call_args.kwargs["fetch_missing"], False)
        draw.assert_not_called()

    def test_chart_url_changes_when_values_or_coverage_change(self):
        original = pd.DataFrame({"temp_mean": [10., 11.], "temp_max": [15., 16.],
                                 "temp_min": [5., 6.], "precip": [2., 3.]},
                                index=pd.to_datetime(["2022-01-01", "2022-02-01"]))
        updated = original.copy()
        updated.iloc[0, 0] = 10.5
        pruned = original.copy()
        pruned.iloc[0] = float("nan")
        names = []
        for history in (original, updated, pruned):
            with (patch("climate.web.app.get_location_history", return_value=(history, False)),
                  patch("climate.web.app.os.path.isfile", return_value=False), patch("climate.web.app.draw_chart") as draw):
                response = self.client.get("/locations?latitude=1&longitude=2")
            self.assertEqual(response.status_code, 200)
            names.append(draw.call_args.kwargs["filename"])
        self.assertEqual(len(set(names)), 3)
        self.assertIn(b"1 of 2 months", response.data)

    def test_empty_map_cache_never_invokes_provider(self):
        with (patch("climate.services.map_data.weather_db"),
              patch("climate.services.map_data._query_weather_rows", return_value=[]),
              patch("climate.services.map_data._fetch_missing_cells", side_effect=AssertionError("download forbidden")) as fetch):
            response = self.client.get("/api/map-data?month=1950-01&climate_type=temp_mean&south=0&west=0&north=1&east=1&zoom=5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["features"], [])
        self.assertTrue(response.json["metadata"]["cache_only"])
        self.assertGreater(response.json["metadata"]["missing"], 0)
        fetch.assert_not_called()

    def test_maps_and_api_accept_the_current_month(self):
        with patch("climate.web.app.latest_map_month", return_value="2026-08"):
            form = self.client.get("/maps?select=1")
            with patch("climate.web.app.viewport_geojson", return_value={"type": "FeatureCollection", "features": [], "metadata": {}}):
                page = self.client.get("/maps?month-picker=2026-08&data-type=temp_mean")
                api = self.client.get("/api/map-data?month=2026-08&climate_type=temp_mean&south=-10&west=-10&north=10&east=10&zoom=2")

        self.assertEqual(form.status_code, 200)
        self.assertIn(b'max="2026-08"', form.data)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(api.status_code, 200)

    def test_maps_opens_the_default_month_and_mean_temperature(self):
        with patch("climate.web.app.latest_map_month", return_value="2026-08"):
            with patch("climate.web.app.default_map_month", return_value="2026-08"):
                response = self.client.get("/maps")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mean temperature (\xc2\xb0C) for 2026-08", response.data)
        self.assertIn(b'href="/maps?select=1&amp;month-picker=2026-08&amp;data-type=temp_mean"', response.data)

    def test_rendered_retry_controls_are_month_labelled_native_buttons(self):
        months = ("1960-01", "2001-06", "2026-08")
        with patch("climate.web.app.latest_map_month", return_value="2026-08"):
            response = self.client.get("/maps?" + "&".join(f"month-picker={month}" for month in months)
                                       + "&data-type=temp_mean")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertEqual(page.count('class="btn btn-outline-secondary btn-sm mb-2"'), len(months))
        for index, month in enumerate(months):
            self.assertIn(f'<button id="map-retry-{index}"'.encode(), response.data)
            self.assertIn(f'type="button" aria-label="Retry saved data for {month}"'.encode(), response.data)
            self.assertIn(f'aria-describedby="map-status-{index}" hidden>Retry saved data</button>'.encode(), response.data)

    def test_coordinate_form_renders_native_bounds_status_and_only_on_open_maps(self):
        with patch("climate.web.app.latest_map_month", return_value="2026-08"):
            maps = self.client.get("/maps?month-picker=2026-08&data-type=temp_mean")
            selector = self.client.get("/maps?select=1")

        self.assertEqual(maps.status_code, 200)
        self.assertIn(b'<form id="map-coordinate-form" class="data-note text-start" novalidate>', maps.data)
        self.assertIn('<label for="map-coordinate-latitude">Latitude (\u221285 to 85)</label>'.encode(), maps.data)
        self.assertIn(b'<input class="form-control" id="map-coordinate-latitude" name="latitude" type="number" step="any" min="-85" max="85" required>', maps.data)
        self.assertIn('<label for="map-coordinate-longitude" class="mt-2">Longitude (\u2212180 to 180)</label>'.encode(), maps.data)
        self.assertIn(b'<input class="form-control" id="map-coordinate-longitude" name="longitude" type="number" step="any" min="-180" max="180" required>', maps.data)
        self.assertIn(b'<button id="show-map-coordinate" class="btn btn-climate-primary" type="submit" disabled>Show location on maps</button>', maps.data)
        self.assertIn(b'<button id="clear-map-coordinate" class="btn btn-outline-secondary" type="button">Clear location</button>', maps.data)
        self.assertIn(b'<p id="map-coordinate-status" role="status" aria-live="polite"', maps.data)
        self.assertIn("Negative latitude means south; negative longitude means west. Missing climate data remains missing.".encode(), maps.data)

        self.assertEqual(selector.status_code, 200)
        self.assertNotIn(b'id="map-coordinate-form"', selector.data,
                         "coordinate entry stays off the month selector")

    def test_readable_metric_labels_keep_internal_keys_and_form_values(self):
        months = ("1960-01", "2001-06")
        with patch("climate.web.app.latest_map_month", return_value="2026-08"):
            for metric_key, label in MAP_METRIC_LABELS.items():
                with self.subTest(metric=metric_key):
                    single = self.client.get(
                        f"/maps?month-picker={months[0]}&data-type={metric_key}"
                    )
                    self.assertEqual(single.status_code, 200)
                    single_parser = MapSelectionParser()
                    single_parser.feed(single.get_data(as_text=True))
                    self.assertEqual(single_parser.page_headings, [f"{label} for {months[0]}"])
                    self.assertEqual(single_parser.map_aria_labels,
                                     [f"{label} map for {months[0]}"])
                    self.assertIn(f'const climateType = "{metric_key}";'.encode(), single.data)

                    comparison = self.client.get(
                        f"/maps?month-picker={months[0]}&month-picker={months[1]}&data-type={metric_key}"
                    )
                    self.assertEqual(comparison.status_code, 200)
                    comparison_parser = MapSelectionParser()
                    comparison_parser.feed(comparison.get_data(as_text=True))
                    self.assertEqual(comparison_parser.page_headings,
                                     [f"Comparing {label} across 2 months"])
                    self.assertEqual(comparison_parser.map_aria_labels,
                                     [f"{label} map for {month}" for month in months])

                    selector = self.client.get(
                        f"/maps?select=1&month-picker={months[0]}&data-type={metric_key}"
                    )
                    self.assertEqual(selector.status_code, 200)
                    selector_parser = MapSelectionParser()
                    selector_parser.feed(selector.get_data(as_text=True))
                    self.assertEqual(
                        [option["value"] for option in selector_parser.data_type_options],
                        list(MAP_METRIC_LABELS),
                    )
                    self.assertEqual(selector_parser.data_type_labels, MAP_METRIC_LABELS)
                    self.assertEqual(selector_parser.data_type_labels[metric_key], label)
                    selected = [option["value"] for option in selector_parser.data_type_options
                                if "selected" in option]
                    self.assertEqual(selected, [metric_key])

    def test_precipitation_and_provider_guidance_stays_distinct(self):
        with patch("climate.web.app.latest_map_month", return_value="2026-08"):
            for provider in ("noaa_core", "open_meteo_cmip6"):
                with self.subTest(provider=provider), patch.dict(app.config, CLIMATE_PROVIDER=provider):
                    selector = self.client.get("/maps?select=1")
                    self.assertEqual(selector.status_code, 200)
                    self.assertIn(b"Precipitation is shown as mean daily rate (mm/day)", selector.data)
                    self.assertIn(b"not as a monthly total", selector.data)

                    precip = self.client.get("/maps?month-picker=1960-01&data-type=precip")
                    self.assertEqual(precip.status_code, 200)
                    self.assertIn(b"Precipitation is a monthly average daily rate (mm/day)", precip.data)
                    self.assertIn(b"not a monthly total", precip.data)
                    if provider == "noaa_core":
                        self.assertIn(b"saved NOAA sampling grid is spaced 2\xc2\xb0 latitude \xc3\x97 4\xc2\xb0 longitude", precip.data)
                        self.assertIn(b"adds no source resolution or accuracy", precip.data)
                        self.assertNotIn(b"Open-Meteo CMIP6 model output", precip.data)
                    else:
                        self.assertIn(b"these maps use Open-Meteo CMIP6 model output", precip.data)
                        self.assertNotIn(b"saved NOAA sampling grid", precip.data)

    def test_change_selection_round_trip_preserves_order_variable_and_unavailable_dates(self):
        cases = tuple((["1960-01"], metric) for metric in MAP_METRIC_LABELS)
        cases += tuple((["2026-08", "1960-01", "2001-06", "1951-01"], metric)
                       for metric in MAP_METRIC_LABELS)
        with patch("climate.web.app.latest_map_month", return_value="2026-08"):
            for months, data_type in cases:
                with self.subTest(months=months, data_type=data_type):
                    map_response = self.client.get(
                        "/maps?" + "&".join(f"month-picker={month}" for month in months)
                        + f"&data-type={data_type}"
                    )
                    self.assertEqual(map_response.status_code, 200)
                    calls_before_edit = self.availability.call_count
                    map_parser = MapSelectionParser()
                    map_parser.feed(map_response.get_data(as_text=True))
                    self.assertIsNotNone(map_parser.change_selection_href)
                    query = parse_qs(urlsplit(map_parser.change_selection_href).query)
                    edit_response = self.client.get("/maps?" + urlsplit(map_parser.change_selection_href).query)
                    self.assertEqual(self.availability.call_count, calls_before_edit + 1)

                    self.assertEqual(edit_response.status_code, 200)
                    edit_parser = MapSelectionParser()
                    edit_parser.feed(edit_response.get_data(as_text=True))
                    self.assertEqual([field["value"] for field in edit_parser.month_inputs], months)
                    self.assertTrue(all("required" in field for field in edit_parser.month_inputs))
                    selected = [option["value"] for option in edit_parser.data_type_options if "selected" in option]
                    self.assertEqual(selected, [data_type])
                    self.assertEqual(query.get("month-picker"), months)
                    self.assertEqual(query.get("data-type"), [data_type])
                    form_query = urlencode({
                        "month-picker": [field["value"] for field in edit_parser.month_inputs],
                        "data-type": selected[0],
                    }, doseq=True)
                    submitted_map = self.client.get("/maps?" + form_query)
                    self.assertEqual(submitted_map.status_code, 200)
                    submitted_parser = MapSelectionParser()
                    submitted_parser.feed(submitted_map.get_data(as_text=True))
                    self.assertEqual(submitted_parser.map_headings, months)
                    label = MAP_METRIC_LABELS[data_type]
                    expected_title = (f"{label} for {months[0]}" if len(months) == 1
                                      else f"Comparing {label} across {len(months)} months")
                    self.assertIn(expected_title.encode(), submitted_map.data)
                    self.assertEqual(submitted_map.data.count(b'class="climate-map-panel"'), len(months))
                    self.assertEqual(self.availability.call_count, calls_before_edit + 1,
                                     "submitting explicit map values does not rediscover availability")
        self.assertEqual(self.availability.call_count, len(cases), "only edit-mode discovery reads availability")

    def test_bare_selector_is_empty_and_discovery_failure_keeps_edit_values(self):
        empty = self.client.get("/maps?select=1")
        self.assertEqual(empty.status_code, 200)
        empty_parser = MapSelectionParser()
        empty_parser.feed(empty.get_data(as_text=True))
        self.assertEqual([field["value"] for field in empty_parser.month_inputs], [""])
        self.assertFalse(any("selected" in option for option in empty_parser.data_type_options))

        self.availability.side_effect = RuntimeError("private database diagnostics")
        with self.assertLogs("climate.web.app", "ERROR"):
            response = self.client.get(
                "/maps?select=1&month-picker=1960-01&month-picker=2026-08&data-type=precip"
            )
        self.assertEqual(response.status_code, 200)
        parser = MapSelectionParser()
        parser.feed(response.get_data(as_text=True))
        self.assertEqual([field["value"] for field in parser.month_inputs], ["1960-01", "2026-08"])
        self.assertEqual([option["value"] for option in parser.data_type_options
                          if "selected" in option], ["precip"])
        self.assertIn(b"Saved dates could not be checked", response.data)
        self.assertNotIn(b"private database diagnostics", response.data)

    def test_edit_mode_rejects_invalid_explicit_selection_before_discovery(self):
        latest = "2026-08"
        cases = (
            ("month-picker=1960-13&data-type=temp_mean", b"Invalid month"),
            ("month-picker=1960-01", b"both required"),
            ("month-picker=&data-type=temp_mean", b"both required"),
            ("month-picker=1960-01&month-picker=1960-01&data-type=temp_mean", b"must be distinct"),
            ("&".join(f"month-picker=1960-{month:02d}" for month in range(1, 6))
             + "&data-type=temp_mean", b"at most four"),
            ("month-picker=2026-09&data-type=temp_mean", b"Invalid month"),
            ("month-picker=1960-01&data-type=not-a-variable", b"not supported"),
        )
        self.availability.side_effect = AssertionError("Invalid explicit selection reached discovery")
        with patch("climate.web.app.latest_map_month", return_value=latest):
            for query, message in cases:
                with self.subTest(query=query):
                    response = self.client.get("/maps?select=1&" + query)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn(message, response.data)
        self.availability.assert_not_called()

    def test_maps_compares_distinct_months_with_one_shared_scale(self):
        with patch("climate.web.app.latest_map_month", return_value="2026-08"):
            response = self.client.get(
                "/maps?month-picker=1950-01&month-picker=2026-08&data-type=temp_mean"
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Comparing Mean temperature (\xc2\xb0C) across 2 months", response.data)
        self.assertIn(b'id="climate-map-0"', response.data)
        self.assertIn(b'id="climate-map-1"', response.data)
        self.assertIn(b"syncViewports", response.data)
        self.assertIn(b"Shared by every panel", response.data)
        self.availability.assert_not_called()

    def test_default_map_uses_newest_saved_mean_temperature_not_newer_other_metric(self):
        self.availability.return_value = [
            {"month": "2026-09", "counts": {"temp_mean": 0, "precip": 20}},
            {"month": "2026-08", "counts": {"temp_mean": 4, "precip": 0}},
            {"month": "1951-01", "counts": {"temp_mean": 100, "precip": 0}},
        ]
        with patch("climate.web.app.default_map_month", return_value="2026-09"):
            response = self.client.get("/maps")
        self.assertIn(b"Mean temperature (\xc2\xb0C) for 2026-08", response.data)
        self.assertIn(b"newest saved mean-temperature", response.data)

    def test_default_map_respects_stable_date_bound(self):
        self.availability.return_value = [
            {"month": "2026-09", "counts": {"temp_mean": 10}},
            {"month": "2026-08", "counts": {"temp_mean": 10}},
        ]
        with patch("climate.web.app.default_map_month", return_value="2026-08"):
            response = self.client.get("/maps")
        self.assertIn(b"Mean temperature (\xc2\xb0C) for 2026-08", response.data)

    def test_empty_saved_cache_opens_selector_instead_of_empty_default(self):
        self.availability.return_value = []
        response = self.client.get("/maps")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No saved mean-temperature month", response.data)
        self.assertIn(b'id="map-selection"', response.data)
        self.assertNotIn(b'id="climate-map-0"', response.data)

    def test_availability_failure_keeps_manual_selection_without_leaking_details(self):
        self.availability.side_effect = RuntimeError("private database diagnostics")
        with self.assertLogs("climate.web.app", "ERROR"):
            response = self.client.get("/maps")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Saved dates could not be checked", response.data)
        self.assertNotIn(b"private database diagnostics", response.data)
        self.assertIn(b'id="month-picker-0"', response.data)

    def test_explicit_unavailable_month_is_not_replaced(self):
        self.availability.side_effect = AssertionError("Discovery should not run")
        response = self.client.get("/maps?month-picker=1960-01&data-type=precip")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mean daily precipitation (mm/day) for 1960-01", response.data)
        self.availability.assert_not_called()

    def test_selector_shows_saved_month_controls_and_keeps_manual_dates(self):
        response = self.client.get("/maps?select=1")
        self.assertEqual(response.status_code, 200)
        for value in (b'Find a saved month', b'global saved points', b'id="saved-month"',
                      b'id="use-saved-month"', b'id="compare-saved-month"', b'type="month"'):
            self.assertIn(value, response.data)

    def test_maps_rejects_duplicate_or_excessive_comparison_months(self):
        duplicate = self.client.get(
            "/maps?month-picker=1950-01&month-picker=1950-01&data-type=temp_mean"
        )
        excessive = self.client.get(
            "/maps?month-picker=1950-01&month-picker=1950-02"
            "&month-picker=1950-03&month-picker=1950-04"
            "&month-picker=1950-05&data-type=temp_mean"
        )

        self.assertEqual(duplicate.status_code, 400)
        self.assertIn(b"Comparison months must be distinct", duplicate.data)
        self.assertEqual(excessive.status_code, 400)
        self.assertIn(b"Compare at most four months", excessive.data)
        self.assertIn(b'/static/img/climate-error.png', duplicate.data)
        self.assertNotIn(b"api.memegen.link", duplicate.data)

    def test_default_map_month_uses_previous_month_early_on_day_one(self):
        early_new_year = datetime(2027, 1, 1, 5, 59, tzinfo=timezone.utc)

        self.assertEqual(default_map_month(early_new_year), "2026-12")

    def test_default_map_month_switches_to_current_month_after_six_utc(self):
        ready = datetime(2027, 1, 1, 6, 0, tzinfo=timezone.utc)

        self.assertEqual(default_map_month(ready), "2027-01")

    def test_maps_and_api_reject_a_future_month(self):
        with patch("climate.web.app.latest_map_month", return_value="2026-08"):
            page = self.client.get("/maps?month-picker=2026-09&data-type=temp_mean")
            api = self.client.get("/api/map-data?month=2026-09&climate_type=temp_mean&south=-10&west=-10&north=10&east=10&zoom=2")

        self.assertEqual(page.status_code, 400)
        self.assertEqual(api.status_code, 400)

    def test_map_sampling_uses_bounded_resolution_and_fewer_zoomed_cells(self):
        self.assertEqual(step_for_zoom(2.25), (2.0, 4.0))
        self.assertAlmostEqual(step_for_zoom(3.25)[0], 4 / 3)
        self.assertAlmostEqual(step_for_zoom(3.25)[1], 8 / 3)
        self.assertEqual(step_for_zoom(10), (0.5, 1.0))
        samples, _ = _sample_coordinates(-90, -180, 90, 180, 2)
        self.assertEqual(len(samples), 90 * 90)
        self.assertLessEqual(len(samples), MAX_VIEWPORT_POINTS)
        overview = _viewport_cells(-53, -90, 53, 90, 2.25)
        intermediate = _viewport_cells(-26.5, -45, 26.5, 45, 3.25)
        close = _viewport_cells(40.4, -74.3, 41.0, -73.6, MAX_ZOOM)
        counts = []
        for _, lat_edges, lon_edges, _, _ in (
            overview,
            intermediate,
            close,
        ):
            rows = len(lat_edges) - 1
            columns = len(lon_edges) - 1
            self.assertLessEqual(rows, 91)
            self.assertLessEqual(columns, 91)
            counts.append(rows * columns)
        self.assertGreater(counts[0], counts[1])
        self.assertGreater(counts[1], counts[2])

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
            [
                (
                    cells[0]["latitude"],
                    cells[0]["longitude"] - lon_step,
                    12.0,
                )
            ],
            {},
            lat_step,
            lon_step,
        )

        self.assertEqual(reused[cells[0]["index"]], 12.0)

    def test_map_cache_excludes_direct_and_nearby_cells_from_provider_batch(self):
        cells, _, _, lat_step, lon_step = _viewport_cells(0, 0, 0.5, 3, 5)
        cached_cell = cells[0]
        cached_row = (
            cached_cell["latitude"],
            cached_cell["longitude"],
            17.5,
        )
        with patch("climate.services.map_data.ACTIVE_CLIMATE_PROVIDER", OPEN_METEO_PROVIDER), patch(
            "climate.services.map_data.weather_db"
        ):
            with patch(
                "climate.services.map_data._query_weather_rows", return_value=[cached_row]
            ) as query:
                with patch(
                    "climate.services.map_data._fetch_missing_cells", return_value=0
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
        self.assertEqual(payload["metadata"]["missing"], len(cells) - 2)
        self.assertEqual(
            payload["metadata"]["provider"], OPEN_METEO_PROVIDER
        )
        self.assertAlmostEqual(query.call_args.args[5], lat_step * 1.5)
        self.assertAlmostEqual(query.call_args.args[6], lon_step * 1.5)
        sources = [
            feature["properties"]["source"] for feature in payload["features"]
        ]
        self.assertEqual(
            sources[:3],
            ["direct_cache", "nearby_cache", "display_estimate"],
        )

    def test_one_map_fetch_caches_every_metric_for_a_location(self):
        cells, _, _, _, _ = _viewport_cells(-2, 100, 2, 104, 5)
        with patch("climate.services.map_data.ACTIVE_CLIMATE_PROVIDER", OPEN_METEO_PROVIDER), patch(
            "climate.services.map_data.get_data", return_value=True
        ) as fetch:
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

    def test_map_fetch_batch_is_spread_across_the_missing_viewport(self):
        cells, _, _, _, _ = _viewport_cells(-2, 100, 2, 104, 5)
        with patch("climate.services.map_data.ACTIVE_CLIMATE_PROVIDER", OPEN_METEO_PROVIDER), patch(
            "climate.services.map_data.get_data", return_value=True
        ) as fetch:
            fetched = _fetch_missing_cells(object(), cells, "2026-08")

        locations = [call.kwargs["location"] for call in fetch.call_args_list]
        self.assertEqual(fetched, MAX_FETCH_PER_VIEWPORT)
        self.assertEqual(len(locations), MAX_FETCH_PER_VIEWPORT)
        self.assertEqual(
            locations[0],
            (cells[0]["latitude"], cells[0]["longitude"]),
        )
        self.assertEqual(
            locations[-1],
            (cells[-1]["latitude"], cells[-1]["longitude"]),
        )
        self.assertNotEqual(
            locations,
            [
                (cell["latitude"], cell["longitude"])
                for cell in cells[:MAX_FETCH_PER_VIEWPORT]
            ],
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

    def test_map_data_rejects_zoom_above_city_scale_limit(self):
        with self.assertRaisesRegex(ValueError, "Zoom must not exceed 10"):
            viewport_geojson(
                "2026-08",
                "temp_mean",
                40.4,
                -74.3,
                41.0,
                -73.6,
                MAX_ZOOM + 0.1,
            )

    def test_map_page_cancels_stale_requests_and_clips_world_bounds(self):
        with patch("climate.web.app.latest_map_month", return_value="2026-08"):
            response = self.client.get(
                "/maps?month-picker=2026-08&data-type=temp_mean"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"requestController?.abort()", response.data)
        self.assertIn(b"Math.max(-180, bounds.getWest())", response.data)
        self.assertIn(b"renderWorldCopies: false", response.data)
        self.assertIn(b"center: [-98.5, 39.5]", response.data)
        self.assertIn(b"zoom: 3.25", response.data)
        self.assertIn(b"maxZoom: 10", response.data)
        self.assertIn(b'panel.map.setProjection({type: "mercator"})', response.data)
        self.assertIn(b"FullscreenControl", response.data)
        self.assertIn(b"panel.map.addControl(new FullscreenControl())", response.data)
        self.assertIn(b"no climate downloads", response.data)
        self.assertIn(b"without cached coverage", response.data)
        self.assertNotIn(b"refresh pending", response.data)
        self.assertIn(b"nearby-cache cells", response.data)
        self.assertIn(b"metadata.rows", response.data)
        self.assertIn(b"Open-Meteo CMIP6", response.data)
        selection_script = Path(__file__).parents[1] / "static" / "map_selection.js"
        self.assertIn("Reused nearby PostgreSQL value", selection_script.read_text())
        self.assertIn(b"startViewportLoad", response.data)
        self.assertIn(b'/static/map_scales.js', response.data)
        self.assertIn(b'id="scale-preset"', response.data)
        self.assertIn(b"colorExpression(activeScale)", response.data)
        self.assertIn(b"fixed until you change it", response.data)
        self.assertIn(b"saveScale(family, scale)", response.data)
        self.assertIn(b"panels.forEach((panel)", response.data)
        self.assertEqual(response.data.count(b"fetch(`/api/map-data?${query}`"), 1)
        self.assertNotIn(b"fetching another batch", response.data)
        self.assertNotIn(b'projection: "mercator"', response.data)
