"""Offline deployment-contract checks with temporary private state only."""

import os
import runpy
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from werkzeug.test import Client
from werkzeug.wrappers import Response

from climate import paths
from climate.cli import manage_users, setup_user_database
from climate.production import configure_production
from climate.web.app import app


ROOT = Path(__file__).resolve().parents[1]


class ProductionConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve() / "private"
        self.root.mkdir(mode=0o700)
        self.env = {
            "CLIMATE_ENV": "production", "CLIMATE_STATE_ROOT": str(self.root),
            "DATABASE_URL": "postgresql://example.invalid/climate",
            "CLIMATE_SECRET_KEY": "s" * 32,
            "CLIMATE_ALLOWED_HOSTS": "climate.example, www.climate.example",
        }

    def configure(self, changes=None):
        values = dict(self.env)
        values.update(changes or {})
        with patch.dict(os.environ, values, clear=True):
            candidate = Flask(__name__)
            configure_production(candidate)
            return candidate

    def test_private_state_and_cli_resolve_same_path(self):
        candidate = self.configure()
        self.assertEqual(candidate.config["USER_DATABASE_PATH"], str(self.root / "users.db"))
        self.assertEqual(candidate.config["COMMUNITY_DATABASE_PATH"], str(self.root / "community.db"))
        self.assertEqual(candidate.config["TRUSTED_HOSTS"], ["climate.example", "www.climate.example"])
        self.assertTrue(candidate.config["SESSION_COOKIE_SECURE"])
        for name in ("SESSION_FILE_DIR", "CLIMATE_CHART_DIRECTORY", "CLIMATE_IMAGE_DIRECTORY"):
            folder = Path(candidate.config[name])
            self.assertEqual(folder.parent, self.root)
            self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
        with patch.dict(os.environ, self.env, clear=True):
            self.assertEqual(paths.resolve_user_database_path(), self.root / "users.db")

    def test_unknown_mode_cannot_write_through_account_clis(self):
        destination = self.root / "nested" / "users.db"
        for mode in ("prod", "PRODUCTION", ""):
            with self.subTest(mode=mode), patch.dict(os.environ, {
                "CLIMATE_ENV": mode, "USER_DATABASE_PATH": str(destination),
            }, clear=True), patch.object(setup_user_database.sqlite3, "connect") as connect:
                with self.assertRaisesRegex(ValueError, "CLIMATE_ENV"):
                    paths.resolve_user_database_path()
                with self.assertRaisesRegex(ValueError, "CLIMATE_ENV"):
                    setup_user_database.initialize_user_database()
                with self.assertRaisesRegex(ValueError, "CLIMATE_ENV"):
                    manage_users.set_admin_status("fake", True)
                connect.assert_not_called()
                self.assertFalse(destination.exists())
                self.assertFalse(destination.parent.exists())
        for environment in ({}, {"CLIMATE_ENV": "development"}):
            with self.subTest(environment=environment), patch.dict(os.environ, {
                **environment, "USER_DATABASE_PATH": str(destination),
            }, clear=True):
                self.assertEqual(paths.climate_mode(), "development")
                self.assertEqual(paths.resolve_user_database_path(), destination)
        with patch.dict(os.environ, self.env, clear=True):
            self.assertEqual(paths.climate_mode(), "production")
            self.assertEqual(paths.resolve_user_database_path(), self.root / "users.db")

    def test_required_settings_and_url_schemes(self):
        for key, value in (
            ("DATABASE_URL", ""), ("DATABASE_URL", "sqlite:///tmp/data.db"),
            ("CLIMATE_SECRET_KEY", "short"), ("CLIMATE_ALLOWED_HOSTS", ""),
            ("CLIMATE_ALLOWED_HOSTS", "*.example.org"),
            ("CLIMATE_ALLOWED_HOSTS", "example.org:443"),
            ("CLIMATE_ALLOWED_HOSTS", "example.org/path"),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.configure({key: value})
        self.configure({"DATABASE_URL": "postgres://example.invalid/climate"})

    def test_rejects_unsafe_state_and_store_aliases(self):
        for value in ("relative/path", str(ROOT), str(ROOT / "instance")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.configure({"CLIMATE_STATE_ROOT": value})
        self.root.chmod(0o755)
        with self.assertRaises(ValueError):
            self.configure()
        self.root.chmod(0o700)
        alias = self.root.parent / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.configure({"CLIMATE_STATE_ROOT": str(alias)})
        for name in ("users.db", "community.db"):
            target = self.root / name
            target.write_bytes(b"fake")
            linked = self.root / (name + ".linked")
            os.link(target, linked)
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.configure()
            linked.unlink()
            target.unlink()
            target.symlink_to(self.root / "missing")
            with self.subTest(name=name + " symlink"), self.assertRaises(ValueError):
                self.configure()
            target.unlink()
        with self.assertRaises(ValueError):
            self.configure({"USER_DATABASE_PATH": str(self.root.parent / "elsewhere.db")})
        with self.assertRaises(ValueError):
            self.configure({"COMMUNITY_DATABASE_PATH": str(self.root.parent / "elsewhere.db")})

    def test_proxy_rewrites_only_allowlisted_peer_and_validated_host(self):
        values = {"CLIMATE_TRUSTED_PROXY_CIDRS": "10.0.0.0/8", "CLIMATE_PROXY_FOR_HOPS": "1",
                  "CLIMATE_PROXY_HOST_HOPS": "1", "CLIMATE_PROXY_PROTO_HOPS": "1"}
        candidate = self.configure(values)
        @candidate.route("/")
        def identity():
            from flask import request
            return f"{request.remote_addr}|{request.scheme}|{request.host}"
        client = Client(candidate, Response)
        headers = {"X-Forwarded-For": "203.0.113.8", "X-Forwarded-Proto": "https",
                   "X-Forwarded-Host": "www.climate.example", "CF-Connecting-IP": "198.51.100.9"}
        with patch.dict(os.environ, self.env | values, clear=True):
            response = client.get("/", base_url="http://climate.example", headers=headers,
                                  environ_overrides={"REMOTE_ADDR": "192.0.2.5"})
            self.assertEqual(response.get_data(as_text=True), "192.0.2.5|http|climate.example")
            response = client.get("/", base_url="http://climate.example", headers=headers,
                                  environ_overrides={"REMOTE_ADDR": "10.1.2.3"})
            self.assertEqual(response.get_data(as_text=True), "203.0.113.8|https|www.climate.example")
            response = client.get("/", base_url="http://climate.example",
                                  headers={**headers, "X-Forwarded-Host": "evil.example"},
                                  environ_overrides={"REMOTE_ADDR": "10.1.2.3"})
            self.assertEqual(response.status_code, 400)
        for cidr in ("0.0.0.0/0", "::/0", "invalid"):
            with self.subTest(cidr=cidr), self.assertRaises(ValueError):
                self.configure(values | {"CLIMATE_TRUSTED_PROXY_CIDRS": cidr})
        with self.assertRaises(ValueError):
            self.configure({"CLIMATE_PROXY_PROTO_HOPS": "1"})

    def test_gunicorn_and_container_contract_are_static(self):
        config = (ROOT / "gunicorn.conf.py").read_text()
        dockerfile = (ROOT / "Dockerfile").read_text()
        ignore = [line.strip() for line in (ROOT / ".dockerignore").read_text().splitlines()
                  if line.strip() and not line.lstrip().startswith("#")]
        self.assertIn('forwarded_allow_ips = ""', config)
        self.assertIn('CLIMATE_ENV', config)
        self.assertIn('PORT', config)
        self.assertEqual(ignore[0], "**")
        self.assertEqual(ignore.count("**"), 1)
        self.assertIn("USER 10001:10001", dockerfile)
        self.assertNotIn("COPY .", dockerfile)
        allowed = set()
        for rule in ignore[1:]:
            self.assertTrue(rule.startswith("!"), rule)
            filename = rule[1:]
            self.assertNotIn(filename, allowed, rule)
            self.assertFalse(any(char in filename for char in "*?[]\\"), rule)
            self.assertFalse(filename.startswith(("/", "../")) or "/../" in filename or filename.endswith("/"), rule)
            relative = Path(filename)
            target = ROOT / relative
            self.assertTrue(stat.S_ISREG(target.lstat().st_mode), rule)
            self.assertEqual(target.stat().st_nlink, 1, rule)
            self.assertFalse(any(parent.is_symlink() for parent in target.parents
                                 if parent != ROOT and parent.is_relative_to(ROOT)), rule)
            allowed.add(filename)
        required = {
            "Dockerfile", "requirements.txt", "requirements-prod.txt", "gunicorn.conf.py", "app.py",
            "climate/__init__.py", "climate/paths.py", "climate/production.py",
            "climate/web/app.py", "climate/web/helpers.py", "climate/data/db.py",
            "climate/providers/open_meteo.py", "climate/providers/noaa_core.py",
            "climate/services/location_fetch.py", "sql/location_fetch.sql",
            "climate/services/community.py", "climate/cli/setup_user_database.py",
            "climate/cli/manage_users.py", "sql/schema.sql", "sql/user_schema.sql",
            "templates/layout.html", "templates/references.html", "templates/maps.html",
            "static/styles.css", "static/number_wheel_guard.js", "static/location_fetch.js",
            "static/user_img/default_icon.png",
        }
        for folder, suffix in (("climate", "*.py"), ("sql", "*.sql"), ("templates", "*.html")):
            required.update(str(path.relative_to(ROOT)) for path in (ROOT / folder).rglob(suffix))
        self.assertTrue(required <= allowed, sorted(required - allowed))
        self.assertTrue(all(name.startswith(("climate/", "sql/", "templates/", "static/"))
                            or name in {"Dockerfile", "requirements.txt", "requirements-prod.txt",
                                        "gunicorn.conf.py", "app.py"} for name in allowed))

        # A negated parent directory would include every descendant in Docker's
        # matcher, even when the private file itself is not named in the rules.
        def effectively_included(filename):
            candidate = Path(filename)
            return any(candidate == Path(exception) or candidate.is_relative_to(exception)
                       for exception in allowed)

        for private in (".env", ".git/config", "instance/users.db", "flask_session/session",
                        "climate/.env", "climate/__pycache__/paths.cpython-314.pyc",
                        "sql/users.db", "templates/.env", "static/users.db",
                        "static/location_data/chart.html", "static/user_img/123.png",
                        "static/user_img/session", "static/img/private.sqlite3"):
            with self.subTest(private=private):
                self.assertFalse(effectively_included(private), private)
        with patch.dict(os.environ, {"CLIMATE_ENV": "production", "PORT": "54321"}, clear=True):
            settings = runpy.run_path(str(ROOT / "gunicorn.conf.py"))
        self.assertEqual(settings["bind"], "0.0.0.0:54321")
        self.assertEqual(settings["forwarded_allow_ips"], "")
        for env in ({"CLIMATE_ENV": "development", "PORT": "8000"},
                    {"CLIMATE_ENV": "production", "PORT": "0"},
                    {"CLIMATE_ENV": "production", "PORT": "65536"}):
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True), self.assertRaises(ValueError):
                runpy.run_path(str(ROOT / "gunicorn.conf.py"))


class DeploymentRouteTests(unittest.TestCase):
    def test_health_has_no_data_or_provider_work(self):
        with patch("climate.web.app.user_db", side_effect=AssertionError("DB")), \
             patch("climate.providers.open_meteo.fetch_data", side_effect=AssertionError("provider"), create=True):
            response = app.test_client().get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "ok\n")

    def test_production_generated_assets_are_narrow_and_private(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            charts, images, static = (root / part for part in ("charts", "images", "static"))
            for folder in (charts, images, static / "user_img"):
                folder.mkdir(parents=True)
            (static / "user_img/default_icon.png").write_bytes(b"icon")
            chart_name = "v7_12.34_-56.78_" + "a" * 64 + ".html"
            (charts / chart_name).write_bytes(b"chart")
            (images / "123.png").write_bytes(b"image")
            (images / "users.db").write_bytes(b"private")
            (images / "session.txt").write_bytes(b"private")
            original = dict(app.config)
            original_static = app.static_folder
            try:
                app.config.update(CLIMATE_PRODUCTION=True, CLIMATE_CHART_DIRECTORY=str(charts),
                                  CLIMATE_IMAGE_DIRECTORY=str(images), USER_DATABASE_PATH=str(root / "users.db"),
                                  COMMUNITY_DATABASE_PATH=str(root / "community.db"))
                app.static_folder = str(static)
                client = app.test_client()
                for url in (f"/static/location_data/{chart_name}", "/static/user_img/123.png",
                            "/static/user_img/default_icon.png"):
                    with self.subTest(url=url):
                        response = client.get(url)
                        self.assertEqual(response.status_code, 200)
                        response.close()
                for url in ("/static/user_img/users.db", "/static/user_img/session.txt",
                            "/static/location_data/../users.db", "/static/user_img/123.png/extra"):
                    with self.subTest(url=url):
                        self.assertEqual(client.get(url).status_code, 404)
                private = root / "private.txt"
                private.write_bytes(b"private")
                (images / "124.png").symlink_to(private)
                os.link(private, images / "125.png")
                for name in ("124.png", "125.png"):
                    self.assertEqual(client.get("/static/user_img/" + name).status_code, 404)
                os.link(private, static / "private-alias.txt")
                response = client.get("/static/private-alias.txt")
                try:
                    self.assertEqual(response.status_code, 404)
                finally:
                    response.close()
            finally:
                app.static_folder = original_static
                app.config.clear()
                app.config.update(original)
