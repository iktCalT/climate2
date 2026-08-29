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

    def test_references_cover_data_stack_and_project_origin(self):
        response = self.client.get("/references")

        self.assertEqual(response.status_code, 200)
        for expected in (
            b"Open-Meteo Climate API",
            b"CMIP6 Terms of Use",
            b"PostgreSQL 18",
            b"MapLibre GL JS",
            b"iktCalT/climate",
            b"OpenAI Codex (GPT-5)",
        ):
            self.assertIn(expected, response.data)


if __name__ == "__main__":
    unittest.main()
