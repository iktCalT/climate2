"""Offline, temporary-store checks for terminal-only administrator creation."""

import getpass
import io
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import check_password_hash, generate_password_hash

from climate.cli import manage_users
from climate.paths import SQL_DIRECTORY
from climate.web.app import app


PASSWORD = "  Example password 123  "


class Terminal(io.StringIO):
    def isatty(self):
        return True


class AdminBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "users.db"
        self.database.touch()
        with closing(sqlite3.connect(self.database)) as con:
            con.executescript((SQL_DIRECTORY / "user_schema.sql").read_text())

    def rows(self):
        with closing(sqlite3.connect(self.database)) as con:
            return con.execute("SELECT username, hash_pwd, is_admin FROM users ORDER BY id").fetchall(), con.execute(
                "SELECT user_id, bio, img FROM profiles ORDER BY user_id"
            ).fetchall()

    def test_create_hash_profile_and_login(self):
        manage_users.create_admin("Admin_01", PASSWORD, self.database)
        users, profiles = self.rows()
        self.assertEqual((users[0][0], users[0][2]), ("Admin_01", 1))
        self.assertNotEqual(users[0][1], PASSWORD)
        self.assertTrue(check_password_hash(users[0][1], PASSWORD))
        self.assertFalse(check_password_hash(users[0][1], PASSWORD.strip()))
        self.assertEqual(profiles[0][1:], ("This is a default bio.", None))

        original = dict(app.config)
        try:
            app.config.update(TESTING=True, USER_DATABASE_PATH=str(self.database))
            client = app.test_client()
            self.assertEqual(client.post("/login", data={"username": "Admin_01", "password": PASSWORD}).status_code, 302)
            with client.session_transaction() as session:
                self.assertEqual(session["user_id"], profiles[0][0])
            self.assertEqual(client.get("/admin/data").status_code, 200)
        finally:
            app.config.clear()
            app.config.update(original)

    def test_duplicate_member_and_admin_preserve_rows(self):
        with closing(sqlite3.connect(self.database)) as con:
            for name, admin in (("member", 0), ("admin", 1)):
                cursor = con.execute(
                    "INSERT INTO users (username, hash_pwd, is_admin) VALUES (?, ?, ?)",
                    (name, generate_password_hash("previous-password"), admin),
                )
                con.execute("INSERT INTO profiles (user_id, bio) VALUES (?, ?)", (cursor.lastrowid, "previous bio"))
            con.commit()
        before = self.rows()
        for name in ("member", "admin"):
            with self.subTest(name=name), self.assertRaisesRegex(manage_users.AdminCreationError, "already in use"):
                manage_users.create_admin(name, PASSWORD, self.database)
            self.assertEqual(self.rows(), before)

    def test_profile_failure_rolls_back_user(self):
        with closing(sqlite3.connect(self.database)) as con:
            con.execute("DROP TABLE profiles")
            con.commit()
        with self.assertRaisesRegex(manage_users.AdminCreationError, "creation failed"):
            manage_users.create_admin("new_admin", PASSWORD, self.database)
        with closing(sqlite3.connect(self.database)) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)

    def test_missing_and_uninitialized_store_never_create_user(self):
        missing = Path(self.temp.name) / "missing.db"
        with self.assertRaises(manage_users.AdminCreationError):
            manage_users.create_admin("new_admin", PASSWORD, missing)
        self.assertFalse(missing.exists())
        empty = Path(self.temp.name) / "empty.db"
        empty.touch()
        with self.assertRaises(manage_users.AdminCreationError):
            manage_users.create_admin("new_admin", PASSWORD, empty)
        self.assertEqual(empty.stat().st_size, 0)

    def test_unsafe_store_paths_rejected_without_static_tree_scan(self):
        static = Path(self.temp.name) / "static"
        static.mkdir()
        public = static / "users.db"
        public.write_bytes(self.database.read_bytes())
        alias = Path(self.temp.name) / "alias.db"
        alias.symlink_to(public)
        hardlink = Path(self.temp.name) / "hardlink.db"
        os.link(self.database, hardlink)
        directory = Path(self.temp.name) / "directory.db"
        directory.mkdir()
        fifo = Path(self.temp.name) / "fifo.db"
        os.mkfifo(fifo)
        with patch.object(manage_users, "STATIC_DIRECTORY", static), patch.object(Path, "rglob", side_effect=AssertionError("recursive scan")):
            for path in (public, alias, self.database, hardlink, directory, fifo):
                with self.subTest(path=path.name), self.assertRaises(manage_users.AdminCreationError):
                    manage_users.create_admin("new_admin", PASSWORD, path)
        self.assertEqual(self.rows()[0], [])

    def test_static_symlink_to_private_store_is_rejected_without_writes(self):
        manage_users.create_admin("existing_admin", PASSWORD, self.database)
        before = self.rows()
        static = Path(self.temp.name) / "static"
        static.mkdir()
        alias = static / "admin-alias.db"
        alias.symlink_to(self.database)
        parent_alias = Path(self.temp.name) / "static-alias"
        parent_alias.symlink_to(static, target_is_directory=True)
        with patch.object(manage_users, "STATIC_DIRECTORY", static), patch.object(
            Path, "rglob", side_effect=AssertionError("recursive scan")
        ):
            for path in (alias, parent_alias / alias.name):
                with self.subTest(path=path), self.assertRaises(manage_users.AdminCreationError):
                    manage_users.create_admin("new_admin", PASSWORD, path)
                self.assertEqual(self.rows(), before)

    def test_username_and_password_boundaries_before_writes(self):
        valid_users = ("abc", "A_9-" + "x" * 12)
        for name in valid_users:
            manage_users.create_admin(name, PASSWORD, self.database)
        self.assertEqual(len(self.rows()[0]), 2)
        for name in ("ab", "x" * 17, "abc\n", "éaa", "a b", "a/b"):
            with self.subTest(username=name), self.assertRaises(manage_users.AdminCreationError):
                manage_users.create_admin(name, PASSWORD, self.database)
        valid_passwords = ("x" * 15, "x" * 128, PASSWORD)
        for index, password in enumerate(valid_passwords):
            manage_users.create_admin(f"valid{index}", password, self.database)
        for password in ("x" * 14, "x" * 129, " " * 15, "x" * 14 + "\n", "x" * 14 + "\x00", "x" * 14 + "\ud800"):
            with self.subTest(length=len(password)), self.assertRaises(manage_users.AdminCreationError):
                manage_users.create_admin("rejected", password, self.database)
        self.assertEqual(len(self.rows()[0]), 5)

    def test_cli_hidden_prompt_success_twice_and_no_password_environment(self):
        with patch.dict(os.environ, {"USER_DATABASE_PATH": str(self.database), "PASSWORD": "unused fake value"}), patch.object(
            manage_users.sys, "stdin", Terminal()
        ), patch.object(manage_users.sys, "stderr", Terminal()), patch.object(
            manage_users.getpass, "getpass", side_effect=[PASSWORD] * 4
        ) as prompt, patch("builtins.print") as printed:
            manage_users.main(["create-admin", "first_admin"])
            manage_users.main(["create-admin", "second_admin"])
        self.assertEqual(prompt.call_count, 4)
        self.assertEqual(len(self.rows()[0]), 2)
        self.assertTrue(all(PASSWORD not in str(call) for call in printed.call_args_list))

    def test_cli_rejects_unavailable_input_without_writes(self):
        cases = (
            (False, False, [PASSWORD, PASSWORD]),
            (True, False, [PASSWORD, PASSWORD]),
            (True, True, [PASSWORD, "different-password"]),
            (True, True, EOFError()),
            (True, True, KeyboardInterrupt()),
            (True, True, getpass.GetPassWarning()),
        )
        for stdin_tty, stderr_tty, prompt_result in cases:
            with self.subTest(prompt_result=type(prompt_result).__name__):
                stdin = Terminal() if stdin_tty else io.StringIO()
                stderr = Terminal() if stderr_tty else io.StringIO()
                with patch.dict(os.environ, {"USER_DATABASE_PATH": str(self.database)}), patch.object(
                    manage_users.sys, "stdin", stdin
                ), patch.object(manage_users.sys, "stderr", stderr), patch.object(
                    manage_users.getpass, "getpass", side_effect=prompt_result
                ) as prompt, self.assertRaises(SystemExit):
                    manage_users.main(["create-admin", "new_admin"])
                if not (stdin_tty and stderr_tty):
                    prompt.assert_not_called()
                self.assertEqual(self.rows()[0], [])

    def test_cli_extra_password_arguments_are_sanitized(self):
        for args in (("--password", "fakevalue"), ("fakevalue",)):
            stderr = Terminal()
            with self.subTest(args=args), patch.object(manage_users.sys, "stderr", stderr), patch.object(
                manage_users.getpass, "getpass"
            ) as prompt, self.assertRaises(SystemExit):
                manage_users.main(["create-admin", "new_admin", *args])
            prompt.assert_not_called()
            self.assertNotIn("fakevalue", stderr.getvalue())
            self.assertEqual(self.rows()[0], [])

    def test_cli_separator_cannot_revoke_existing_admin(self):
        manage_users.create_admin("existing_admin", PASSWORD, self.database)
        before = self.rows()
        stderr = Terminal()
        with patch.dict(os.environ, {"USER_DATABASE_PATH": str(self.database)}), patch.object(
            manage_users.sys, "stderr", stderr
        ), patch.object(manage_users.getpass, "getpass") as prompt, self.assertRaises(SystemExit):
            manage_users.main(["--", "create-admin", "existing_admin"])
        prompt.assert_not_called()
        self.assertEqual(self.rows(), before)


if __name__ == "__main__":
    unittest.main()
