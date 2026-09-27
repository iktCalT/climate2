"""Exercise entry points and resources that can break when modules move."""

from contextlib import chdir
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app import app as entry_app
from climate.cli import setup_database
from climate.cli.setup_user_database import initialize_user_database
from climate.paths import PROJECT_ROOT
from climate.web.app import app


class ProjectLayoutTests(unittest.TestCase):
    def test_root_entry_exposes_the_same_flask_app(self):
        self.assertIs(entry_app, app)

    def test_templates_static_and_schemas_resolve_outside_project_directory(self):
        connection = MagicMock()
        with tempfile.TemporaryDirectory() as directory, chdir(directory):
            account_path = Path(directory) / "accounts.db"
            self.assertEqual(initialize_user_database(account_path), account_path)
            with patch.object(setup_database, "weather_db", return_value=connection):
                setup_database.main()
            statements = connection.__enter__.return_value.cursor.return_value.__enter__.return_value.execute.call_args_list
            self.assertEqual(len(statements), 2)
            self.assertIn("CREATE TABLE IF NOT EXISTS locations", statements[0].args[0])
            self.assertIn("CREATE TABLE IF NOT EXISTS climate_import_job", statements[1].args[0])
            with app.test_client() as client:
                self.assertEqual(client.get("/").status_code, 200)
                with client.get("/static/styles.css") as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(b".apology-panel", response.data)

    def test_administrative_help_does_not_require_a_database_or_download(self):
        for command in ("prefetch_climate", "import_noaa_core",
                        "compare_climate_providers", "manage_users"):
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, "-m", f"climate.cli.{command}", "--help"],
                    cwd=PROJECT_ROOT,
                    env={**os.environ, "DATABASE_URL": "", "PYTHONDONTWRITEBYTECODE": "1"},
                    capture_output=True, text=True, timeout=20,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)
