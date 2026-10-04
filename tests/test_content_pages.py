import html
from html.parser import HTMLParser
import os
import re
from pathlib import Path
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


# Exact external credits, including approved Plotly and deployment research links.
REFERENCE_URLS = set("""
https://carto.com/attributions
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=overview
https://chatgpt.com/
https://colorbrewer2.org/
https://crudata.uea.ac.uk/cru/data/hrg/
https://cs50.harvard.edu/x/
https://developers.openai.com/api/docs/guides/image-generation
https://developer.mozilla.org/en-US/docs/Web/API/Element/wheel_event
https://developers.cloudflare.com/fundamentals/reference/http-headers/
https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/
https://docs.cloud.google.com/run/docs/container-contract
https://docs.digitalocean.com/products/backups/details/pricing/
https://docs.docker.com/build/concepts/context/
https://docs.docker.com/compose/
https://docs.python.org/3/library/contextlib.html#contextlib.closing
https://docs.python.org/3/library/hashlib.html
https://docs.python.org/3/library/sqlite3.html
https://docs.python.org/3/library/threading.html
https://docs.railway.com/databases
https://docs.railway.com/pricing/plans
https://docs.railway.com/volumes/backups
https://docs.railway.com/volumes/reference
https://flask-session.readthedocs.io/en/latest/
https://flask.palletsprojects.com/en/stable/
https://flask.palletsprojects.com/en/stable/deploying/
https://flask.palletsprojects.com/en/stable/deploying/gunicorn/
https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/
https://fontawesome.com/
https://fonts.google.com/
https://ftp.cpc.ncep.noaa.gov/CORe/get_core/get_core.txt
https://getbootstrap.com/docs/5.3/
https://github.com/MazeMap/retry-requests
https://github.com/benoitc/gunicorn/blob/master/LICENSE
https://github.com/ecmwf/eccodes-python
https://github.com/iktCalT/climate
https://github.com/lennardv2/Leaflet.awesome-markers
https://github.com/maplibre/demotiles
https://github.com/moby/patternmatcher/blob/main/LICENSE
https://github.com/moby/patternmatcher/blob/main/patternmatcher.go
https://github.com/open-meteo/python-requests
https://gunicorn.org/
https://hub.docker.com/_/python
https://jquery.com/
https://leafletjs.com/
https://maplibre.org/maplibre-gl-js/docs/
https://maplibre.org/maplibre-gl-js/docs/API/classes/CanvasSource/
https://maplibre.org/maplibre-gl-js/docs/API/classes/Popup/
https://maplibre.org/maplibre-style-spec/layers/
https://nodejs.org/
https://numpy.org/doc/stable/
https://open-meteo.com/en/docs/climate-api
https://openai.com/codex/
https://pandas.pydata.org/docs/
https://pcmdi.llnl.gov/CMIP6/TermsOfUse
https://plotly.com/python/
https://plotly.com/python/hover-text-and-formatting/
https://plotly.com/python/reference/scatter/#scatter-customdata
https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
https://psl.noaa.gov/data/coreinfo.html
https://psl.noaa.gov/news/2026/r1datanotice.html
https://python-visualization.github.io/folium/
https://raw.githubusercontent.com/maplibre/maplibre-gl-js/v6.6.0/src/style/style.ts
https://raw.githubusercontent.com/maplibre/maplibre-gl-js/v6.6.0/src/ui/map.ts
https://render.com/docs/disks
https://render.com/docs/free
https://render.com/pricing
https://requests-cache.readthedocs.io/en/stable/
https://wpo.noaa.gov/ncep-introduces-operational-reanalysis-for-climate-monitoring-core/
https://www.cpc.ncep.noaa.gov/products/CORe/archive.html
https://www.cpc.ncep.noaa.gov/products/CORe/index.html
https://www.cpc.ncep.noaa.gov/products/CORe/regridding.html
https://www.digitalocean.com/pricing/droplets
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

    def get_page(self, path, provider="noaa_core"):
        with (patch.dict(app.config, {"CLIMATE_PROVIDER": provider}),
              patch("climate.web.app.saved_map_months", side_effect=AssertionError("database read")),
              patch("climate.web.app.get_location_history", side_effect=AssertionError("history read")),
              patch("climate.web.app.viewport_geojson", side_effect=AssertionError("map read"))):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return " ".join(html.unescape(response.get_data(as_text=True)).split())

    def test_home_explains_current_sources_coverage_and_units(self):
        page = self.get_page("/")
        for expected in (
            "NOAA CORe reanalysis",
            "Cache only",
            "Missing values are never downloaded while browsing",
            "1950 → current month",
            "Map dates; coverage varies by place and variable",
            "from 1951 through the current month",
            "Missing coverage stays visible",
            "°C · mm/day",
            "not a monthly total",
            "not direct observations at an exact location",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, page)
        self.assertNotIn("1950–1954 and 2022–2026", page)

    def test_concise_help_and_references_style_isolation(self):
        root = Path(__file__).resolve().parents[1]
        for provider in ("noaa_core", "open_meteo_cmip6"):
            references = self.get_page("/references", provider)
            self.assertNotRegex(references, r'class="[^"]*(?:concise-page|community-)')
            self.assertNotIn('id="community-controls"', references)
        css = (root / "static/styles.css").read_text()
        marker = "/* Concise public pages; References and shared layout keep their existing rules. */"
        self.assertIn(marker, css)
        added = re.sub(r"/\*.*?\*/", "", css.split(marker, 1)[1], flags=re.S)
        for selector in re.findall(r"([^{}]+)\{", added):
            if selector.strip().startswith("@media"):
                continue
            for item in selector.split(","):
                self.assertTrue(item.strip().startswith((".concise-page", ".community-")), item)
        for path, help_class in (("/", "home-guide"), ("/locations", "location-help")):
            self.assertIn(f'<details class="{help_class}">', self.get_page(path))

    def test_home_actions_and_comparison_guidance(self):
        page = self.get_page("/")
        structure = PageStructure()
        structure.feed(page)
        hrefs = {link.get("href") for link in structure.links}
        self.assertTrue({"/maps", "/locations", "/maps?select=1", "/references"} <= hrefs)
        self.assertEqual(structure.headings.count("h1"), 1)
        self.assertTrue(set(structure.labelled_by) <= structure.ids)
        for expected in (
            "two to four months",
            "Click a location",
            "each month's value and source",
            "NOAA map readouts are interpolated estimates from the saved 2° × 4° grid",
            "Missing coverage stays visible",
            "manual color scale",
            "stays fixed until you change it",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, page)

    def test_both_public_modes_explain_purpose_preview_and_comparison_limits(self):
        for provider, source, readout, excluded_readout in (
            (
                "noaa_core",
                "NOAA CORe reanalysis data",
                "NOAA map readouts are interpolated estimates from the saved 2° × 4° grid.",
                "CMIP6 map readouts use the saved containing-cell value",
            ),
            (
                "open_meteo_cmip6",
                "Open-Meteo CMIP6 model data",
                "CMIP6 map readouts use the saved containing-cell value",
                "NOAA map readouts are interpolated estimates",
            ),
        ):
            with self.subTest(provider=provider):
                home = self.get_page("/", provider)
                references = self.get_page("/references", provider)
                self.assertIn(source, home)
                self.assertIn("build awareness of environmental protection", home)
                self.assertIn("Illustrative pattern · not live climate data", home)
                self.assertIn(readout, home)
                self.assertNotIn(excluded_readout, home)
                self.assertIn("Two months do not establish a long-term trend.", home)
                self.assertIn("awareness of broad climate patterns, not high-precision reporting", references)
                self.assertIn("two months cannot establish a long-term climate trend", references)
                self.assertIn("Visitors do not trigger provider downloads", references)
                self.assertIn("A failed viewport request offers a per-panel", references)
                self.assertIn("repeats that saved-cache read after an explicit click", references)
                self.assertIn("Empty coverage and out-of-world views do not offer retry", references)
                self.assertIn("mean daily precipitation in mm/day", references)
                self.assertIn("monthly average daily rate", references)
                self.assertIn("not a monthly total", references)
                reference_links = PageStructure()
                reference_links.feed(references)
                self.assertEqual(
                    {link["href"] for link in reference_links.links
                     if link.get("href", "").startswith("https://")},
                    REFERENCE_URLS,
                )
                if provider == "noaa_core":
                    self.assertIn("Maps smooth the saved 2° × 4° sampling grid by bilinear interpolation; this adds no source resolution or accuracy", references)
                else:
                    self.assertIn("model outputs, not direct station observations", references)

    def test_references_distinguish_provider_dates_coverage_and_history(self):
        page = self.get_page("/references")
        for expected in (
            "Active public source",
            "noaa_core",
            "not direct station observations",
            "mean daily precipitation in mm/day",
            "monthly average daily rate",
            "not a monthly total",
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
        external_urls = {href for href in hrefs if href and href.startswith("https://")}
        self.assertEqual(external_urls, REFERENCE_URLS)
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

    def test_coordinate_selection_guidance_matches_readme_and_references(self):
        readme = " ".join(Path(__file__).resolve().parents[1].joinpath("README.md").read_text().split())
        self.assertIn(
            "On open Maps pages, valid typed coordinates recenter all panels and open linked readouts; clearing the selection does not pan or fetch data.",
            readme,
        )
        for provider in ("noaa_core", "open_meteo_cmip6"):
            references = self.get_page("/references", provider)
            for expected in (
                "enter latitude from −85 to 85 and longitude from −180 to 180 to center ready panels and open linked readouts",
                "negative values mean south and west",
                "Invalid input leaves the maps unchanged",
                "Clear location closes readouts without panning or fetching",
            ):
                with self.subTest(provider=provider, expected=expected):
                    self.assertIn(expected, references)

    def test_seasonal_coverage_guidance_and_plotly_citations(self):
        readme = " ".join(Path(__file__).resolve().parents[1].joinpath("README.md").read_text().split())
        for provider in ("noaa_core", "open_meteo_cmip6"):
            references = self.get_page("/references", provider)
            for page in (readme, references):
                for expected in (
                    "Northern Hemisphere", "March–May", "June–August",
                    "September–November", "December–February",
                    "labelled by January's year",
                    "may not match local seasons everywhere",
                    "coverage, not measurement accuracy",
                    "monthly average daily rate in mm/day",
                    "https://plotly.com/python/hover-text-and-formatting/",
                    "https://plotly.com/python/reference/scatter/#scatter-customdata",
                ):
                    with self.subTest(provider=provider, expected=expected):
                        self.assertIn(expected, page)

    def test_location_edit_guidance_matches_readme_and_both_reference_modes(self):
        readme = " ".join(Path(__file__).resolve().parents[1].joinpath("README.md").read_text().split())
        for expected in (
            "coordinate form stays visible above saved history and empty results",
            "prefilled with your requested coordinates rather than NOAA's sampled grid point",
            "editing fields alone leaves the displayed history unchanged",
            "returns to blank entry fields without reading history",
            "No JavaScript is required",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, readme)
        for provider in ("noaa_core", "open_meteo_cmip6"):
            references = self.get_page("/references", provider)
            for expected in (
                "coordinate form stays visible above saved history and empty results",
                "fields retain your requested coordinates, rather than NOAA's sampled grid point",
                "Submit Update location to read saved history for another location",
                "editing fields alone leaves the displayed result unchanged",
                "Clear returns to blank entry fields without reading history",
                "form works without JavaScript and never triggers provider downloads",
            ):
                with self.subTest(provider=provider, expected=expected):
                    self.assertIn(expected, references)

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
