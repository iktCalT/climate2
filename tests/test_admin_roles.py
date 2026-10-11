import io
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from html.parser import HTMLParser
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from climate.web.app import app
from climate.cli.manage_users import set_admin_status


class ImportFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_window = False
        self.options = []
        self.limit = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "select" and attrs.get("id") == "import-window":
            self.in_window = True
        elif tag == "option" and self.in_window:
            self.options.append((attrs.get("value"), "selected" in attrs))
        elif tag == "input" and attrs.get("id") == "import-limit":
            self.limit = attrs

    def handle_endtag(self, tag):
        if tag == "select":
            self.in_window = False


class AdminRoleTests(unittest.TestCase):
    def setUp(self):
        handle, self.user_database_path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        with closing(sqlite3.connect(self.user_database_path)) as con:
            con.executescript(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    username TEXT NOT NULL UNIQUE,
                    hash_pwd TEXT NOT NULL,
                    is_admin BOOLEAN NOT NULL DEFAULT TRUE
                );
                CREATE TABLE profiles (
                    user_id INTEGER NOT NULL UNIQUE,
                    bio TEXT DEFAULT 'This is a default bio.',
                    img TEXT DEFAULT NULL
                );
                """
            )
            con.commit()
        self.original_user_database_path = app.config["USER_DATABASE_PATH"]
        app.config.update(TESTING=True, USER_DATABASE_PATH=self.user_database_path)
        self.client = app.test_client()

    def tearDown(self):
        app.config["USER_DATABASE_PATH"] = self.original_user_database_path
        os.unlink(self.user_database_path)

    def create_user(self, username, is_admin, with_profile=True):
        with closing(sqlite3.connect(self.user_database_path)) as con:
            cursor = con.execute(
                "INSERT INTO users (username, hash_pwd, is_admin) VALUES (?, ?, ?)",
                (username, generate_password_hash("password"), is_admin),
            )
            if with_profile:
                con.execute(
                    "INSERT INTO profiles (user_id) VALUES (?)", (cursor.lastrowid,)
                )
            con.commit()
        return cursor.lastrowid

    def sign_in_as(self, user_id):
        with self.client.session_transaction() as flask_session:
            flask_session["user_id"] = user_id

    def test_registration_is_closed_without_creating_account_or_profile(self):
        response = self.client.post(
            "/register",
            data={"username": "member", "password": "password", "confirmation": "password"},
        )

        with closing(sqlite3.connect(self.user_database_path)) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM profiles").fetchone()[0], 0)
        self.assertEqual(response.status_code, 403)
        page = self.client.get("/register")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Registration is temporarily closed", page.data)
        self.assertIn(b"no time to manage new accounts", page.data)
        self.assertNotIn(b'name="password"', page.data)
        self.assertNotIn(b'name="username"', page.data)
        self.assertIn(b'href="/login"', page.data)

    def test_cleanup_requires_current_admin_and_csrf(self):
        with patch("climate.web.app.cleanup_preview") as preview, patch("climate.web.app.cleanup_batch") as delete:
            self.assertEqual(self.client.get("/api/admin/cleanup").status_code, 302)
            self.sign_in_as(self.create_user("member", False))
            self.assertEqual(self.client.get("/api/admin/cleanup").status_code, 403)
            self.assertEqual(self.client.post("/api/admin/cleanup", json={}).status_code, 403)
            self.sign_in_as(self.create_user("admin", True))
            self.assertEqual(self.client.post("/api/admin/cleanup", json={}).status_code, 403)
            preview.assert_not_called()
            delete.assert_not_called()

    def test_cleanup_needs_preview_confirmation_and_cannot_replay(self):
        self.sign_in_as(self.create_user("admin", True))
        self.client.get("/admin/data")
        with self.client.session_transaction() as flask_session:
            csrf = flask_session["import_csrf"]
        headers = {"X-CSRF-Token": csrf}
        with (patch("climate.web.app.cleanup_preview", return_value={"removable": 10}) as preview,
              patch("climate.web.app.cleanup_batch", return_value={"deleted": 10}) as delete):
            self.assertEqual(self.client.post("/api/admin/cleanup", json={"confirm": True}, headers=headers).status_code, 400)
            data = self.client.get("/api/admin/cleanup").get_json()
            delete.assert_not_called()
            payload = {"preview_token": data["preview_token"], "confirm": False}
            self.assertEqual(self.client.post("/api/admin/cleanup", json=payload, headers=headers).status_code, 400)
            payload["confirm"] = True
            self.assertEqual(self.client.post("/api/admin/cleanup", json=payload, headers=headers).get_json()["deleted"], 10)
            self.assertEqual(self.client.post("/api/admin/cleanup", json=payload, headers=headers).status_code, 400)
            delete.assert_called_once()

    def test_cleanup_expired_preview_and_revoked_admin_are_rejected(self):
        user_id = self.create_user("admin", True)
        self.sign_in_as(user_id)
        with self.client.session_transaction() as flask_session:
            flask_session["import_csrf"] = "test-csrf"
            flask_session["cleanup_preview"] = ["test-preview", 0]
        with patch("climate.web.app.cleanup_batch") as delete:
            self.assertEqual(self.client.post("/api/admin/cleanup", json={"confirm": True, "preview_token": "test-preview"}, headers={"X-CSRF-Token": "test-csrf"}).status_code, 400)
            set_admin_status("admin", False, self.user_database_path)
            self.assertEqual(self.client.get("/api/admin/cleanup").status_code, 403)
            delete.assert_not_called()

    def test_cleanup_errors_are_sanitized(self):
        from climate.services.admin_import import ImportBusy
        self.sign_in_as(self.create_user("admin", True))
        self.client.get("/admin/data")
        with self.client.session_transaction() as flask_session:
            csrf = flask_session["import_csrf"]
        with patch("climate.web.app.cleanup_preview", return_value={"removable": 10}):
            for error, status in [(ImportBusy("Busy"), 409), (RuntimeError("private connection details"), 503)]:
                token = self.client.get("/api/admin/cleanup").get_json()["preview_token"]
                with patch("climate.web.app.cleanup_batch", side_effect=error):
                    response = self.client.post("/api/admin/cleanup", json={"confirm": True, "preview_token": token}, headers={"X-CSRF-Token": csrf})
                self.assertEqual(response.status_code, status)
                self.assertNotIn(b"private connection details", response.data)

    def test_role_management_requires_an_existing_user(self):
        user_id = self.create_user("member", False)

        self.assertTrue(set_admin_status("member", True, self.user_database_path))
        self.assertFalse(set_admin_status("missing", True, self.user_database_path))
        with closing(sqlite3.connect(self.user_database_path)) as con:
            is_admin = con.execute(
                "SELECT is_admin FROM users WHERE id = ?", (user_id,)
            ).fetchone()[0]
        self.assertTrue(is_admin)

    def test_login_without_profile_uses_an_empty_image(self):
        self.create_user("member", False, with_profile=False)

        response = self.client.post(
            "/login", data={"username": "member", "password": "password"}
        )

        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as flask_session:
            self.assertIsNone(flask_session["imgname"])

    def test_profile_page_creates_a_missing_profile(self):
        user_id = self.create_user("member", False, with_profile=False)
        self.sign_in_as(user_id)

        response = self.client.get("/profile")

        self.assertEqual(response.status_code, 200)
        with closing(sqlite3.connect(self.user_database_path)) as con:
            profile = con.execute(
                "SELECT bio FROM profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
        self.assertEqual(profile, ("This is a default bio.",))

    def test_profile_bio_update_upserts_a_missing_profile(self):
        user_id = self.create_user("member", False, with_profile=False)
        self.sign_in_as(user_id)

        response = self.client.post("/profile", data={"bio": "Climate student"})

        self.assertEqual(response.status_code, 302)
        with closing(sqlite3.connect(self.user_database_path)) as con:
            bio = con.execute(
                "SELECT bio FROM profiles WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
        self.assertEqual(bio, "Climate student")

    def test_profile_rejects_unsupported_image_types(self):
        user_id = self.create_user("member", False)
        self.sign_in_as(user_id)

        response = self.client.post(
            "/profile",
            data={"img": (io.BytesIO(b"not an image"), "profile.exe")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)

    def test_update_and_admin_data_require_current_admin_for_get_and_post(self):
        with patch("climate.web.app.start_import") as start, patch("climate.web.app.import_status") as status:
            for path, method, expected in (("/update", "get", 302), ("/update", "post", 302),
                                           ("/admin/data", "get", 302), ("/admin/data", "post", 405)):
                with self.subTest(role="anonymous", path=path, method=method):
                    self.assertEqual(getattr(self.client, method)(path).status_code, expected)
            user_id = self.create_user("member", False)
            self.sign_in_as(user_id)
            for path, method, expected in (("/update", "get", 403), ("/update", "post", 403),
                                           ("/admin/data", "get", 403), ("/admin/data", "post", 405)):
                with self.subTest(role="member", path=path, method=method):
                    self.assertEqual(getattr(self.client, method)(path).status_code, expected)
            set_admin_status("member", True, self.user_database_path)
            self.assertEqual(self.client.get("/admin/data").status_code, 200)
            set_admin_status("member", False, self.user_database_path)
            for path, method, expected in (("/update", "get", 403), ("/update", "post", 403),
                                           ("/admin/data", "get", 403), ("/admin/data", "post", 405)):
                with self.subTest(role="revoked", path=path, method=method):
                    self.assertEqual(getattr(self.client, method)(path).status_code, expected)
            start.assert_not_called()
            status.assert_not_called()

    def test_legacy_update_get_is_safe_and_post_never_starts_acquisition(self):
        self.sign_in_as(self.create_user("climateadmin", True))
        legacy_data = {
            "lat_start": "10", "lat_end": "11", "n_lat": "2",
            "lon_start": "20", "lon_end": "21", "n_lon": "2",
            "date_start": "2020-01-01", "date_end": "2020-12-31",
        }
        with (patch("climate.web.app.start_import") as start,
              patch("climate.web.app.import_status") as status,
              patch("climate.providers.open_meteo.get_data_locations") as open_meteo,
              patch("climate.providers.noaa_core.load_core_month") as noaa):
            response = self.client.get("/update")
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.headers["Location"], "/admin/data")
            with self.client.session_transaction() as session:
                self.assertNotIn("import_csrf", session)
            for data in (legacy_data, {"n_lat": "not-a-number"}, {}):
                with self.subTest(data=data):
                    rejected = self.client.post("/update", data=data)
                    self.assertEqual(rejected.status_code, 410)
                    self.assertIn(b"NOAA admin page", rejected.data)
                    self.assertIn(b"/admin/data", rejected.data)
            start.assert_not_called()
            status.assert_not_called()
            open_meteo.assert_not_called()
            noaa.assert_not_called()

    def test_rendered_noaa_defaults_submit_to_csrf_protected_api(self):
        self.sign_in_as(self.create_user("climateadmin", True))
        with patch("climate.web.app.start_import") as start, patch("climate.web.app.import_status") as status:
            page = self.client.get("/admin/data")
            self.assertEqual(page.status_code, 200)
            parser = ImportFormParser()
            parser.feed(page.get_data(as_text=True))
            self.assertEqual(parser.options, [("first", False), ("last", True)])
            self.assertEqual({key: parser.limit[key] for key in ("type", "min", "max", "step", "value")},
                             {"type": "number", "min": "1", "max": "12", "step": "1", "value": "1"})
            self.assertIn("required", parser.limit)
            self.assertEqual(page.data.count(b'href="/admin/data"'), 1)
            self.assertNotIn(b'href="/update"', page.data)
            self.assertNotIn(b"lat_start", page.data)
            with self.client.session_transaction() as session:
                token = session["import_csrf"]
            payload = {"window": next(value for value, selected in parser.options if selected),
                       "limit": int(parser.limit["value"])}
            self.assertEqual(self.client.post("/api/admin/import", json=payload).status_code, 403)
            start.assert_not_called()
            start.return_value = {"started": True, "message": "Started"}
            response = self.client.post("/api/admin/import", json=payload,
                                        headers={"X-CSRF-Token": token})
            self.assertEqual(response.status_code, 202)
            start.assert_called_once_with("last", 1)
            status.assert_not_called()

    def test_noaa_api_requires_current_admin_and_csrf(self):
        with patch("climate.web.app.start_import") as start, patch("climate.web.app.import_status") as status:
            self.assertEqual(self.client.get("/api/admin/import").status_code, 302)
            user_id = self.create_user("member", False)
            self.sign_in_as(user_id)
            self.assertEqual(self.client.get("/api/admin/import").status_code, 403)
            self.assertEqual(self.client.post("/api/admin/import", json={}).status_code, 403)
            start.assert_not_called()
            status.assert_not_called()
            set_admin_status("member", True, self.user_database_path)
            self.assertEqual(self.client.get("/admin/data").status_code, 200)
            self.assertEqual(self.client.post("/api/admin/import", json={}).status_code, 403)
            with self.client.session_transaction() as session:
                token = session["import_csrf"]
            start.return_value = {"started": True, "message": "Started"}
            response = self.client.post("/api/admin/import", json={"window": "first", "limit": 1},
                                        headers={"X-CSRF-Token": token})
            self.assertEqual(response.status_code, 202)
            start.assert_called_once_with("first", 1)
            set_admin_status("member", False, self.user_database_path)
            self.assertEqual(self.client.get("/api/admin/import").status_code, 403)

    def test_noaa_api_reports_conflict_and_sanitizes_failures(self):
        from climate.services.admin_import import ImportBusy
        self.sign_in_as(self.create_user("climateadmin", True))
        self.client.get("/admin/data")
        with self.client.session_transaction() as session:
            token = session["import_csrf"]
        with patch("climate.web.app.start_import", side_effect=ImportBusy("Already running")):
            self.assertEqual(self.client.post("/api/admin/import", json={"window": "first"},
                headers={"X-CSRF-Token": token}).status_code, 409)
        with patch("climate.web.app.import_status", side_effect=RuntimeError("sensitive diagnostic")), self.assertLogs("climate.web.app", "ERROR"):
            response = self.client.get("/api/admin/import")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"sensitive diagnostic", response.data)

    def test_noaa_invalid_window_and_limit_do_not_start_work(self):
        self.sign_in_as(self.create_user("climateadmin", True))
        self.client.get("/admin/data")
        with self.client.session_transaction() as session:
            token = session["import_csrf"]
        with patch("climate.services.admin_import._connect") as connect:
            for payload in ({"window": "all"}, {"window": "first", "limit": 13},
                            {"window": "last", "limit": True}, {"window": []}, []):
                self.assertEqual(self.client.post("/api/admin/import", json=payload,
                    headers={"X-CSRF-Token": token}).status_code, 400)
            connect.assert_not_called()
