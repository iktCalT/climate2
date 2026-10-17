"""Safety and lifecycle checks for the disposable Python test runner."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests" / "run_offline.py"


class OfflineRunnerTests(unittest.TestCase):
    def run_python(self, *arguments, cwd=ROOT):
        return subprocess.run(
            [sys.executable, *map(str, arguments)], cwd=cwd, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
        )

    def test_invalid_filename_pattern_is_rejected(self):
        result = self.run_python(RUNNER, "--pattern", "../test*.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("filename pattern", result.stderr)

    def test_imported_app_is_refused_before_discovery(self):
        result = self.run_python(
            "-c",
            "import runpy, sys, types; sys.modules['app'] = types.ModuleType('app'); "
            f"sys.argv = [{str(RUNNER)!r}, '--pattern', 'nothing*.py']; "
            f"runpy.run_path({str(RUNNER)!r}, run_name='__main__')",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("app was imported before offline isolation", result.stderr)
        self.assertNotIn("No tests discovered", result.stderr)

    def test_empty_discovery_exits_two(self):
        result = self.run_python(RUNNER, "--pattern", "no_such_offline_test_*.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("No tests discovered", result.stderr)

    def test_isolation_cleanup_and_suite_exit_statuses(self):
        suffix = uuid.uuid4().hex
        suite_name = f"test_offline_probe_{suffix}.py"
        with tempfile.TemporaryDirectory(prefix="offline-runner-check-") as scratch:
            fake_root = Path(scratch) / "project"
            fake_tests = fake_root / "tests"
            fake_tests.mkdir(parents=True)
            suite_path = fake_tests / suite_name
            marker = Path(scratch) / "state-path.txt"
            suite_path.write_text(
                "import os, sys, unittest\n"
                "from pathlib import Path\n"
                "import psycopg, requests, urllib.request\n"
                "from flask_session.defaults import Defaults\n"
                "from flask_session.filesystem import FileSystemSessionInterface\n"
                "from climate.web.app import app\n"
                "from climate.web import helpers\n"
                "import climate.providers.noaa_core as noaa_core\n"
                "class Probe(unittest.TestCase):\n"
                " def test_isolation(self):\n"
                "  self.assertEqual(os.environ['CLIMATE_ENV'], 'development')\n"
                "  self.assertEqual(os.environ['LOCATION_FETCH_ENABLED'], '0')\n"
                "  self.assertEqual(os.environ['DATABASE_URL'], '')\n"
                "  self.assertEqual(os.environ['CLIMATE_CLEANUP_PG_TEST'], '0')\n"
                "  self.assertEqual(os.environ['CLIMATE_AVAILABILITY_PG_TEST'], '0')\n"
                "  self.assertEqual(os.environ['PYTHONDONTWRITEBYTECODE'], '1')\n"
                "  self.assertTrue(os.environ['USER_DATABASE_PATH'].startswith(os.path.dirname(os.environ['SESSION_FILE_DIR'])))\n"
                "  self.assertTrue(os.environ['COMMUNITY_DATABASE_PATH'].startswith(os.path.dirname(os.environ['SESSION_FILE_DIR'])))\n"
                "  self.assertEqual(os.environ['COMMUNITY_ENABLED'], '0')\n"
                "  self.assertEqual(os.environ['COMMUNITY_SECRET'], '')\n"
                "  self.assertTrue(Path(os.environ['SESSION_FILE_DIR']).is_dir())\n"
                "  self.assertEqual(app.config['CLIMATE_IMAGE_DIRECTORY'], str(Path(os.environ['SESSION_FILE_DIR']).parent / 'images'))\n"
                "  self.assertEqual(helpers.LOCATION_CHART_DIRECTORY, Path(os.environ['SESSION_FILE_DIR']).parent / 'charts')\n"
                "  self.assertEqual(Path.cwd(), Path(__file__).resolve().parents[1])\n"
                "  self.assertTrue(any(Path(entry or '.').resolve() == Path.cwd() for entry in sys.path))\n"
                "  self.assertFalse(sys.dont_write_bytecode is False)\n"
                "  self.assertIn(str(Path(os.environ['SESSION_FILE_DIR'])), FileSystemSessionInterface.__init__.__defaults__)\n"
                "  for call in (lambda: psycopg.connect('unused'), lambda: requests.Session().request('GET', 'https://example.invalid'), lambda: urllib.request.urlopen('https://example.invalid'), lambda: noaa_core.urlopen('https://example.invalid')):\n"
                "   with self.assertRaises(RuntimeError): call()\n"
                "  Path(os.environ['OFFLINE_PROBE_MARKER']).write_text(str(Path(os.environ['SESSION_FILE_DIR']).parent))\n"
                "  if os.environ.get('OFFLINE_PROBE_FAIL') == '1': self.fail('intentional offline runner failure')\n"
                "if __name__ == '__main__': unittest.main()\n"
            )
            harness = (
                "import os, sys, runpy\n"
                f"sys.path.insert(0, {str(ROOT / 'tests')!r})\n"
                f"sys.path.insert(0, {str(ROOT)!r})\n"
                "import run_offline\n"
                f"run_offline.ROOT = __import__('pathlib').Path({str(fake_root)!r})\n"
                "from flask_session.defaults import Defaults\n"
                "original_session_default = Defaults.SESSION_FILE_DIR\n"
                "import urllib.request\n"
                "original_urlopen = urllib.request.urlopen\n"
                "before_cwd = __import__('pathlib').Path.cwd()\n"
                "before_path = list(sys.path)\n"
                "before_bytecode = sys.dont_write_bytecode\n"
                "before = {key: os.environ.get(key) for key in run_offline.ENVIRONMENT}\n"
                "import urllib.request\n"
                "code = run_offline.main(['--pattern', " + repr(suite_name) + "])\n"
                "assert __import__('pathlib').Path.cwd() == before_cwd\n"
                "assert sys.path == before_path\n"
                "assert sys.dont_write_bytecode == before_bytecode\n"
                "assert {key: os.environ.get(key) for key in run_offline.ENVIRONMENT} == before\n"
                "app = sys.modules['climate.web.app'].app\n"
                "helpers = sys.modules['climate.web.helpers']\n"
                "assert app.config.get('CLIMATE_IMAGE_DIRECTORY') == before_image\n"
                "assert helpers.LOCATION_CHART_DIRECTORY == before_chart\n"
                "assert sys.modules['climate.providers.noaa_core'].urlopen is original_urlopen\n"
                "temp_state = __import__('pathlib').Path(open(os.environ['OFFLINE_PROBE_MARKER']).read())\n"
                "session_defaults = sys.modules['flask_session.filesystem'].FileSystemSessionInterface.__init__.__defaults__\n"
                "assert original_session_default in session_defaults\n"
                "assert str(temp_state / 'sessions') not in session_defaults\n"
                f"print('OFFLINE_RUNNER_RESTORED_{suffix}')\n"
                "raise SystemExit(code)\n"
            )
            # Inspect app configuration only after main() has restored it.
            harness = harness.replace(
                "app = sys.modules['climate.web.app'].app\n",
                "app = sys.modules['climate.web.app'].app\n"
                "before_image = None\n"
                "before_chart = __import__('pathlib').Path('static/location_data')\n",
            )
            env = os.environ.copy()
            env["OFFLINE_PROBE_MARKER"] = str(marker)
            env["OFFLINE_PROBE_FAIL"] = "0"
            success = subprocess.run(
                [sys.executable, "-c", harness], cwd=ROOT, env=env, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
            )
            self.assertEqual(success.returncode, 0, success.stdout + success.stderr)
            self.assertIn(f"OFFLINE_RUNNER_RESTORED_{suffix}", success.stdout)
            temp_state = Path(marker.read_text())
            self.assertFalse(temp_state.exists(), "runner temporary state was not removed")

            env["OFFLINE_PROBE_FAIL"] = "1"
            failure = subprocess.run(
                [sys.executable, "-c", harness], cwd=ROOT, env=env, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
            )
            self.assertEqual(failure.returncode, 1, failure.stdout + failure.stderr)
            self.assertIn(f"OFFLINE_RUNNER_RESTORED_{suffix}", failure.stdout)
            self.assertIn("intentional offline runner failure", failure.stderr)
            failed_state = Path(marker.read_text())
            self.assertFalse(failed_state.exists(), "runner temporary state survived test failure")


if __name__ == "__main__":
    unittest.main()
