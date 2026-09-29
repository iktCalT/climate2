import html
from html.parser import HTMLParser
import os
import unittest
from unittest.mock import patch

from flask import render_template

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/climate")

import climate.data.cache_availability as cache_availability
import climate.data.db as climate_db
import climate.providers.open_meteo as open_meteo
import climate.services.map_data as map_data
import climate.web.app as web_app
from climate.web.app import app


# External URLs in the pre-refresh References page. Keep these credits visible.
REFERENCE_URLS = set("""
https://carto.com/attributions
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=overview
https://chatgpt.com/
https://colorbrewer2.org/
https://crudata.uea.ac.uk/cru/data/hrg/
https://cs50.harvard.edu/x/
https://developers.openai.com/api/docs/guides/image-generation
https://docs.python.org/3/library/contextlib.html#contextlib.closing
https://docs.python.org/3/library/hashlib.html
https://docs.python.org/3/library/sqlite3.html
https://docs.python.org/3/library/threading.html
https://flask-session.readthedocs.io/en/latest/
https://flask.palletsprojects.com/en/stable/
https://fontawesome.com/
https://fonts.google.com/
https://ftp.cpc.ncep.noaa.gov/CORe/get_core/get_core.txt
https://getbootstrap.com/docs/5.3/
https://github.com/MazeMap/retry-requests
https://github.com/ecmwf/eccodes-python
https://github.com/iktCalT/climate
https://github.com/lennardv2/Leaflet.awesome-markers
https://github.com/maplibre/demotiles
https://github.com/open-meteo/python-requests
https://jquery.com/
https://leafletjs.com/
https://maplibre.org/maplibre-gl-js/docs/
https://maplibre.org/maplibre-gl-js/docs/API/classes/Popup/
https://nodejs.org/
https://numpy.org/doc/stable/
https://open-meteo.com/en/docs/climate-api
https://openai.com/codex/
https://pandas.pydata.org/docs/
https://pcmdi.llnl.gov/CMIP6/TermsOfUse
https://plotly.com/python/
https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
https://psl.noaa.gov/data/coreinfo.html
https://psl.noaa.gov/news/2026/r1datanotice.html
https://python-visualization.github.io/folium/
https://requests-cache.readthedocs.io/en/stable/
https://wpo.noaa.gov/ncep-introduces-operational-reanalysis-for-climate-monitoring-core/
https://www.cpc.ncep.noaa.gov/products/CORe/archive.html
https://www.cpc.ncep.noaa.gov/products/CORe/index.html
https://www.cpc.ncep.noaa.gov/products/CORe/regridding.html
https://www.iconfinder.com/icons/9079087/global_warming_climate_change_hot_heat_temperature_icon
https://www.jsdelivr.com/
https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf
https://www.openstreetmap.org/copyright
https://www.postgresql.org/about/licence/
https://www.postgresql.org/docs/18/
https://www.postgresql.org/docs/18/routine-vacuuming.html
https://www.postgresql.org/docs/18/sql-delete.html
https://www.psycopg.org/psycopg3/docs/
""".split())


class PageStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.ids = set()
        self.links = []
        self.labelled_by = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"h1", "h2", "h3"}:
            self.headings.append(tag)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if "aria-labelledby" in attrs:
            self.labelled_by.extend(attrs["aria-labelledby"].split())
        if tag == "a":
            self.links.append(attrs)


class ContentPageTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def get_page(self, path):
        with (patch("climate.web.app.saved_map_months", side_effect=AssertionError("database read")),
              patch("climate.web.app.get_location_history", side_effect=AssertionError("history read")),
              patch("climate.web.app.viewport_geojson", side_effect=AssertionError("map read"))):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return " ".join(html.unescape(response.get_data(as_text=True)).split())

    def test_home_explains_current_sources_coverage_and_units(self):
        page = self.get_page("/")
        for expected in (
            "NOAA CORe is the active public reanalysis series",
            "Open-Meteo CMIP6 model output remains a separate cached source",
            "Public browsing reads the existing cache",
            "1950 → current month",
            "Selectable map dates; coverage varies by place and variable",
            "from 1951 through the current month",
            "Gaps stay visible",
            "°C and mm/day",
            "not monthly rainfall totals",
            "not direct observations at an exact location",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, page)
        self.assertNotIn("1950–1954 and 2022–2026", page)

    def test_home_actions_and_comparison_guidance(self):
        page = self.get_page("/")
        structure = PageStructure()
        structure.feed(page)
        hrefs = {link.get("href") for link in structure.links}
        self.assertTrue({"/maps", "/locations", "/maps?select=1", "/references"} <= hrefs)
        self.assertEqual(structure.headings.count("h1"), 1)
        self.assertTrue(set(structure.labelled_by) <= structure.ids)
        for expected in (
            "two to four different months",
            "Click a location in any panel",
            "Each panel shows its own monthly value",
            "nearby point, or a labelled display estimate",
            "Missing values stay marked",
            "shared scale presets or enter a custom range",
            "The scale stays fixed until you change it",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, page)

    def test_references_distinguish_provider_dates_coverage_and_history(self):
        page = self.get_page("/references")
        for expected in (
            "Active public source",
            "noaa_core",
            "not direct station observations",
            "mean daily mm/day, not a monthly total",
            "Visitors do not trigger provider downloads",
            "January 1950 through the current month",
            "Location history starts in January 1951",
            "A selectable date does not guarantee saved values",
            "finite active-provider values globally, not regional completeness",
            "open_meteo_cmip6",
            "inactive for public Maps and Locations",
            "not silently mixed",
            "Historical import and validation details (recorded through September 2026)",
            "not current public coverage or a live database count",
            "8,281 canonical rows",
            "248 of 920",
            "284 of 920",
            "Historical CMIP6 cache warning",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, page)

    def test_references_comparison_guidance_anchors_and_citations(self):
        page = self.get_page("/references")
        structure = PageStructure()
        structure.feed(page)
        hrefs = {link.get("href") for link in structure.links}
        self.assertEqual(structure.headings.count("h1"), 1)
        self.assertTrue(set(structure.labelled_by) <= structure.ids)
        self.assertIn("/maps?select=1", hrefs)
        self.assertTrue(REFERENCE_URLS <= hrefs, sorted(REFERENCE_URLS - hrefs))
        for link in structure.links:
            if link.get("href", "").startswith("https://") and link.get("target") == "_blank":
                self.assertTrue({"noopener", "noreferrer"} <= set(link.get("rel", "").split()))
        for expected in (
            "each month's own value and provenance",
            "signed differences in °C or mm/day",
            "Loading, failed and missing data explain why a difference is unavailable",
            "All panels share a manual color scale",
            "Choose a preset or custom range",
            "narrower color bands do not improve data accuracy",
            "Inactive generated-map dependencies",
            "iktCalT/climate",
            "OpenAI Codex (GPT-5)",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, page)

    def test_footer_attribution_follows_the_active_climate_provider(self):
        original_provider = app.config["CLIMATE_PROVIDER"]
        try:
            app.config["CLIMATE_PROVIDER"] = "noaa_core"
            response = self.client.get("/")
        finally:
            app.config["CLIMATE_PROVIDER"] = original_provider

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-climate-provider="noaa_core"', response.data)
        self.assertIn(b"Climate reanalysis data", response.data)
        self.assertIn(b">NOAA CORe</a>", response.data)
        self.assertNotIn(b'aria-label="Open-Meteo Climate API"', response.data)

    def test_noaa_is_the_startup_default_for_public_read_modules(self):
        self.assertEqual(climate_db.ACTIVE_CLIMATE_PROVIDER, "noaa_core")
        for module in (cache_availability, open_meteo, map_data, web_app):
            with self.subTest(module=module.__name__):
                self.assertEqual(module.ACTIVE_CLIMATE_PROVIDER, "noaa_core")
        self.assertEqual(app.config["CLIMATE_PROVIDER"], "noaa_core")

    def test_admin_provider_copy_matches_both_public_modes(self):
        for provider, active_copy, other_copy in (
            ("noaa_core", "Public Maps and Locations currently read saved NOAA CORe data only",
             "Open-Meteo CMIP6 rows remain stored separately"),
            ("open_meteo_cmip6", "Public Maps and Locations currently read saved Open-Meteo CMIP6 data",
             "This page adds NOAA CORe rows to their separate provider cache for comparison"),
        ):
            with self.subTest(provider=provider), app.test_request_context("/admin/data"):
                page = render_template("admin_data.html", csrf_token="test", climate_provider=provider)
            page = " ".join(html.unescape(page).split())
            self.assertIn(active_copy, page)
            self.assertIn(other_copy, page)
            self.assertIn("imports do not", page)


if __name__ == "__main__":
    unittest.main()
