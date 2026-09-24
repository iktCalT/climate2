import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/climate")

from app import app


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
        self.assertIn(b"anonymous NOAA CORe bulk importer", response.data)
        self.assertIn(b"cross-provider comparisons", response.data)

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
        ):
            self.assertIn(expected, response.data)


if __name__ == "__main__":
    unittest.main()
