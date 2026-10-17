#!/usr/bin/env python3
"""Run unittest checks with local state isolated and real I/O guarded."""

import argparse
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BLOCKED_MODULES = ("app", "climate.web.app")
ENVIRONMENT = {
    "CLIMATE_ENV": "development",
    "LOCATION_FETCH_ENABLED": "0",
    "DATABASE_URL": "",
    "CLIMATE_CLEANUP_PG_TEST": "0",
    "CLIMATE_AVAILABILITY_PG_TEST": "0",
    "PYTHONDONTWRITEBYTECODE": "1",
    "USER_DATABASE_PATH": "",
    "COMMUNITY_ENABLED": "0",
    "COMMUNITY_SECRET": "",
    "COMMUNITY_DATABASE_PATH": "",
    "SESSION_FILE_DIR": "",
}


def _arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", default="test*.py", help="unittest filename pattern (no directory paths)")
    args = parser.parse_args(argv)
    if (len(args.pattern) > 128 or not re.fullmatch(r"[A-Za-z0-9_*?.-]+", args.pattern)
            or args.pattern in (".", "..")):
        parser.error("--pattern must be a filename pattern of at most 128 safe characters")
    return args


def _blocked(*_args, **_kwargs):
    raise RuntimeError("Offline runner blocked a real database or network request")


def _restore_config(config, original):
    config.clear()
    config.update(original)


def _restore_captured_session_default(interface, temporary, original):
    defaults = interface.__init__.__defaults__
    if defaults:
        interface.__init__.__defaults__ = tuple(
            original if value == temporary else value for value in defaults
        )


def main(argv=None):
    args = _arguments(argv)
    if any(name in sys.modules for name in BLOCKED_MODULES):
        print("Refusing to run: the Flask app was imported before offline isolation.", file=sys.stderr)
        return 2

    previous_cwd = Path.cwd()
    previous_sys_path = list(sys.path)
    previous_environment = {key: os.environ.get(key) for key in ENVIRONMENT}
    previous_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        with tempfile.TemporaryDirectory(prefix="climate-offline-") as temporary:
            state = Path(temporary)
            os.chdir(ROOT)
            sys.path.insert(0, str(ROOT))
            os.environ.update(ENVIRONMENT)
            os.environ["USER_DATABASE_PATH"] = str(state / "users.db")
            os.environ["COMMUNITY_DATABASE_PATH"] = str(state / "community.db")
            os.environ["SESSION_FILE_DIR"] = str(state / "sessions")

            # Flask-Session captures its filesystem default in a function
            # signature, so redirect it before the application is imported.
            import psycopg
            import requests
            import urllib.request
            from flask_session.defaults import Defaults
            original_urlopen = urllib.request.urlopen
            original_session_directory = Defaults.SESSION_FILE_DIR

            with ExitStack() as stack:
                stack.enter_context(patch.object(Defaults, "SESSION_FILE_DIR", str(state / "sessions")))
                stack.enter_context(patch.object(psycopg, "connect", side_effect=_blocked))
                stack.enter_context(patch.object(requests.Session, "request", side_effect=_blocked))
                stack.enter_context(patch.object(urllib.request, "urlopen", side_effect=_blocked))

                # The filesystem interface captures Defaults in its signature
                # when this module imports, so Defaults is patched first.
                from flask_session.filesystem import FileSystemSessionInterface
                if str(state / "sessions") not in FileSystemSessionInterface.__init__.__defaults__:
                    raise RuntimeError("Flask-Session did not adopt the isolated session directory")
                stack.callback(
                    _restore_captured_session_default,
                    FileSystemSessionInterface,
                    str(state / "sessions"),
                    original_session_directory,
                )
                from climate.web.app import app
                from climate.web import helpers
                import climate.providers.noaa_core as noaa_core
                stack.callback(setattr, noaa_core, "urlopen", original_urlopen)

                original_config = dict(app.config)
                original_helper_directory = helpers.LOCATION_CHART_DIRECTORY
                stack.callback(_restore_config, app.config, original_config)
                stack.callback(setattr, helpers, "LOCATION_CHART_DIRECTORY", original_helper_directory)
                app.config.update(
                    USER_DATABASE_PATH=str(state / "users.db"),
                    COMMUNITY_DATABASE_PATH=str(state / "community.db"),
                    CLIMATE_IMAGE_DIRECTORY=str(state / "images"),
                )
                helpers.LOCATION_CHART_DIRECTORY = state / "charts"

                stack.enter_context(patch.object(noaa_core, "urlopen", side_effect=_blocked))
                suite = unittest.defaultTestLoader.discover(
                    str(ROOT / "tests"), pattern=args.pattern
                )
                if suite.countTestCases() == 0:
                    print(f"No tests discovered for filename pattern {args.pattern!r}.", file=sys.stderr)
                    return 2
                result = unittest.TextTestRunner(verbosity=2).run(suite)
                return 0 if result.wasSuccessful() else 1
    finally:
        os.chdir(previous_cwd)
        sys.path[:] = previous_sys_path
        sys.dont_write_bytecode = previous_bytecode
        for key, value in previous_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    raise SystemExit(main())
