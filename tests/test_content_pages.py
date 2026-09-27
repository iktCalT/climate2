import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/climate")

from climate.web.app import app


class ContentPageTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_home_explains_both_climate_workflows(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Explore climate history", response.data)
        self.assertIn(b'href="/maps"', response.data)
        self.assertIn(b'href="/locations"', response.data)
        self.assertIn(b"Climate-model output", response.data)
        self.assertIn(b"NOAA CORe", response.data)
        self.assertIn(b"administrator-managed", response.data)
        self.assertIn(b"1950\xe2\x80\x931954", response.data)
        self.assertIn(b"2022\xe2\x80\x932026", response.data)
        self.assertIn(b"2 \xc2\xb0C color stops", response.data)
        self.assertIn(b"remain uncorrected", response.data)
        self.assertIn(b"never silently mixes reanalysis", response.data)

    def test_references_cover_data_stack_and_project_origin(self):
        response = self.client.get("/references")

        self.assertEqual(response.status_code, 200)
        for expected in (
            b"Open-Meteo Climate API",
            b"CMIP6 Terms of Use",
            b"ECMWF ecCodes Python",
            b"PostgreSQL 18",
            b"MapLibre GL JS",
            b"Flask-Session",
            b"Bootstrap 5",
            b"NASA POWER monthly API",
            b"NOAA Conventional Observation Reanalysis (CORe)",
            b"NOAA CORe NODD archive",
            b"NOAA NCEI open-data policy",
            b"NOAA CORe regridding guidance",
            b"NCEP/NCAR Reanalysis 1 update notice",
            b"Inactive generated-map dependencies",
            b"iktCalT/climate",
            b"OpenAI Codex (GPT-5)",
            b"must be credited both here and in the repository README",
            b"must never be committed or pushed",
            b"open_meteo_cmip6",
            b"noaa_core",
            b"all eight exact 0\xe2\x80\x933 hour extrema pairs",
            b"all 92 requested months",
            b"newest-first 2016\xe2\x80\x932026 backfill",
            b"read-only PostgreSQL report",
            b"all 8,281 canonical rows for January 1950",
            b"February 1952",
            b"July 2023",
            b"August 2026",
            b"does not silently",
            b"OpenAI image generation",
            b"sends no visitor error message to an external image service",
        ):
            self.assertIn(expected, b" ".join(response.data.split()))

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


if __name__ == "__main__":
    unittest.main()
