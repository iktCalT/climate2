import io
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from app import MAX_ADMIN_PREFETCH_POINTS, app
from manage_users import set_admin_status


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

    def test_registration_creates_a_normal_user_even_with_an_old_true_default(self):
        response = self.client.post(
            "/register",
            data={"username": "member", "password": "password", "confirmation": "password"},
        )

        with closing(sqlite3.connect(self.user_database_path)) as con:
            is_admin = con.execute(
                "SELECT is_admin FROM users WHERE username = ?", ("member",)
            ).fetchone()[0]
        self.assertEqual(response.status_code, 200)
        self.assertFalse(is_admin)

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

    def test_normal_user_cannot_see_or_open_manual_prefetch(self):
        self.sign_in_as(self.create_user("member", False))

        home = self.client.get("/")
        update = self.client.get("/update")

        self.assertNotIn(b'href="/update"', home.data)
        self.assertEqual(update.status_code, 403)

    def test_admin_can_prefetch_a_bounded_grid(self):
        self.sign_in_as(self.create_user("climateadmin", True))
        today = datetime.today().strftime("%Y-%m-%d")
        request_data = {
            "lat_start": "10",
            "lat_end": "11",
            "n_lat": "2",
            "lon_start": "20",
            "lon_end": "21",
            "n_lon": "2",
            "date_start": "2020-01-01",
            "date_end": today,
        }
        with patch("app.get_data_locations", return_value=True) as prefetch:
            form = self.client.get("/update")
            response = self.client.post("/update", data=request_data)

        self.assertEqual(form.status_code, 200)
        self.assertIn(str(MAX_ADMIN_PREFETCH_POINTS).encode(), form.data)
        self.assertEqual(response.status_code, 302)
        prefetch.assert_called_once()
        self.assertEqual(prefetch.call_args.kwargs["lats"].size, 2)
        self.assertEqual(prefetch.call_args.kwargs["lons"].size, 2)

    def test_admin_prefetch_rejects_excessive_point_counts(self):
        self.sign_in_as(self.create_user("climateadmin", True))
        today = datetime.today().strftime("%Y-%m-%d")
        with patch("app.get_data_locations") as prefetch:
            response = self.client.post(
                "/update",
                data={
                    "lat_start": "0", "lat_end": "1", "n_lat": str(MAX_ADMIN_PREFETCH_POINTS + 1),
                    "lon_start": "0", "lon_end": "1", "n_lon": "1",
                    "date_start": "2020-01-01", "date_end": today,
                },
            )

        self.assertEqual(response.status_code, 400)
        prefetch.assert_not_called()
