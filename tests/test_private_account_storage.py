import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from climate import paths
from climate.cli import manage_users, setup_user_database
from climate.web.app import app


class UserDatabasePathTests(unittest.TestCase):
    def test_explicit_argument_precedes_environment_and_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            configured = root / "environment.db"
            explicit = root / "explicit.db"
            with patch.dict(os.environ, {"USER_DATABASE_PATH": str(configured)}), \
                    patch.object(paths, "PROJECT_ROOT", root), \
                    patch.object(paths, "STATIC_DIRECTORY", root / "static"):
                (root / "static").mkdir()
                (root / "static" / "users.db").touch()
                (root / "instance").mkdir()
                (root / "instance" / "users.db").touch()
                self.assertEqual(paths.resolve_user_database_path(explicit), explicit)
                self.assertEqual(paths.resolve_user_database_path(), configured)

    def test_warned_legacy_path_precedes_private_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static = root / "static"
            static.mkdir()
            legacy = static / "users.db"
            legacy.touch()
            (root / "instance").mkdir()
            (root / "instance" / "users.db").touch()
            with patch.dict(os.environ, {}, clear=True), \
                    patch.object(paths, "PROJECT_ROOT", root), \
                    patch.object(paths, "STATIC_DIRECTORY", static), \
                    self.assertWarnsRegex(RuntimeWarning, "legacy static/users.db"):
                self.assertEqual(paths.resolve_user_database_path(), legacy)

    def test_private_default_and_environment_consumers_agree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static = root / "static"
            static.mkdir()
            expected_default = root / "instance" / "users.db"
            configured = root / "private-store" / "accounts.custom"
            with patch.dict(os.environ, {}, clear=True), \
                    patch.object(paths, "PROJECT_ROOT", root), \
                    patch.object(paths, "STATIC_DIRECTORY", static):
                self.assertEqual(paths.resolve_user_database_path(), expected_default)

            with patch.dict(os.environ, {"USER_DATABASE_PATH": str(configured)}), \
                    patch.object(paths, "PROJECT_ROOT", root), \
                    patch.object(paths, "STATIC_DIRECTORY", static):
                self.assertEqual(paths.resolve_user_database_path(), configured)
                self.assertEqual(setup_user_database.initialize_user_database(), configured)
                with closing(sqlite3.connect(configured)) as connection:
                    connection.execute(
                        "INSERT INTO users (username, hash_pwd) VALUES (?, ?)",
                        ("qa_fake", "not-a-real-password-hash"),
                    )
                    connection.commit()
                self.assertTrue(manage_users.set_admin_status("qa_fake", True))
                with closing(sqlite3.connect(configured)) as connection:
                    self.assertEqual(
                        connection.execute(
                            "SELECT is_admin FROM users WHERE username = ?", ("qa_fake",)
                        ).fetchone(),
                        (1,),
                    )


class _TrackingConnection:
    def __init__(self, fail=False):
        self.closed = False
        self.fail = fail

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def executescript(self, _schema):
        if self.fail:
            raise sqlite3.OperationalError("fake schema failure")

    def close(self):
        self.closed = True


class UserDatabaseConnectionLifetimeTests(unittest.TestCase):
    def test_setup_closes_connection_after_success_and_schema_error(self):
        for fail in (False, True):
            connection = _TrackingConnection(fail=fail)
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as directory:
                with patch.object(setup_user_database.sqlite3, "connect", return_value=connection):
                    if fail:
                        with self.assertRaisesRegex(sqlite3.OperationalError, "fake schema"):
                            setup_user_database.initialize_user_database(
                                Path(directory) / "accounts.db"
                            )
                    else:
                        setup_user_database.initialize_user_database(
                            Path(directory) / "accounts.db"
                        )
                self.assertTrue(connection.closed)


class PrivateStaticServingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.static = self.root / "public"
        self.static.mkdir()
        self.outside = self.root / "outside"
        self.outside.mkdir()
        self.original_static = app.static_folder
        self.original_database = app.config["USER_DATABASE_PATH"]
        app.static_folder = str(self.static)
        self.client = app.test_client()

    def tearDown(self):
        app.static_folder = self.original_static
        app.config["USER_DATABASE_PATH"] = self.original_database
        self.directory.cleanup()

    def put(self, relative, data=b"fake"):
        target = self.static / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def assert_denied(self, path):
        for method in ("get", "head"):
            response = getattr(self.client, method)("/static/" + path)
            self.assertEqual(response.status_code, 404, (method, path))

    def test_anonymous_get_and_head_deny_databases_sidecars_hidden_and_private_target(self):
        configured = self.put("accounts.custom", b"fake account database")
        app.config["USER_DATABASE_PATH"] = str(configured)
        for name in (
            "users.db", "app.sqlite", "cache.sqlite3", "user.db-wal",
            "user.db-journal", "user.db-shm", ".secret", "nested/.hidden/file.txt",
        ):
            self.put(name)
            self.assert_denied(name)
        self.assert_denied("accounts.custom")
        self.put(".private-target", b"hidden fake content")
        (self.static / "visible-alias.txt").symlink_to(self.static / ".private-target")
        self.assert_denied("visible-alias.txt")

    def test_anonymous_get_and_head_deny_database_backup_name_variants(self):
        backup_names = (
            "users.db.bak",
            "archive.sqlite.backup.tar",
            "cache.sqlite3-old",
            "users.db-wal.bak",
            "cache.sqlite-shm.gz",
            "USERS.DB.BAK",
            "accounts.sqlite3~",
            "users.db-backup",
            "users.db_backup",
            "users.db backup",
            "users.db(backup)",
            "users.db!backup",
            "wal.sqlite3_wal backup",
        )
        for name in backup_names:
            with self.subTest(name=name):
                self.put(name)
                self.assert_denied(name)

    def test_hardlink_and_symlink_aliases_of_configured_account_file_are_denied(self):
        configured = self.root / "private" / "account.data"
        configured.parent.mkdir()
        configured.write_bytes(b"fake account database")
        app.config["USER_DATABASE_PATH"] = str(configured)
        hardlink = self.static / "aliases" / "hard-link.bin"
        hardlink.parent.mkdir(parents=True)
        os.link(configured, hardlink)
        self.assert_denied("aliases/hard-link.bin")
        symlink = self.static / "aliases" / "soft-link.bin"
        try:
            symlink.symlink_to(configured)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable")
        self.assert_denied("aliases/soft-link.bin")

    def test_case_alias_of_configured_file_is_denied_when_filesystem_supports_it(self):
        configured = self.put("aliases/PrivateAccount.custom", b"fake account database")
        app.config["USER_DATABASE_PATH"] = str(configured)
        alias = self.static / "aliases" / "privateaccount.custom"
        try:
            same_file = os.path.samefile(configured, alias)
        except OSError:
            same_file = False
        if not same_file:
            self.skipTest("filesystem does not resolve case aliases")
        self.assert_denied("aliases/privateaccount.custom")

    def test_out_of_root_symlink_traversal_and_symlink_loop_are_denied(self):
        (self.outside / "outside.txt").write_text("outside")
        (self.static / "escape.txt").symlink_to(self.outside / "outside.txt")
        (self.static / "loop-a").symlink_to(self.static / "loop-b")
        (self.static / "loop-b").symlink_to(self.static / "loop-a")
        self.assert_denied("escape.txt")
        self.assert_denied("loop-a")
        self.assert_denied("../outside/outside.txt")

    def test_normal_assets_and_generated_chart_files_remain_available(self):
        assets = {
            "css/site.css": b"body { color: black; }",
            "js/site.js": b"void 0;",
            "images/icon.png": b"fake image bytes",
            "location_data/chart.html": b"<html>fake chart</html>",
            "js/dbpedia.js": b"window.dbpedia = true;",
            "js/thing.dbpedia.js": b"window.thing = true;",
        }
        for name, content in assets.items():
            self.put(name, content)
            for method in ("get", "head"):
                response = getattr(self.client, method)("/static/" + name)
                self.assertEqual(response.status_code, 200, (method, name))
                response.close()
            response = self.client.get("/static/" + name)
            try:
                self.assertEqual(response.data, content)
            finally:
                response.close()


if __name__ == "__main__":
    unittest.main()
