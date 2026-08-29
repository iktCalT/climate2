import sqlite3
import tempfile
import unittest
from pathlib import Path

from setup_user_database import initialize_user_database


class UserDatabaseSetupTests(unittest.TestCase):
    def test_new_database_has_private_safe_normal_user_default(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "accounts" / "users.db"

            initialize_user_database(database_path)
            with sqlite3.connect(database_path) as connection:
                cursor = connection.execute(
                    "INSERT INTO users (username, hash_pwd) VALUES (?, ?)",
                    ("member", "test-hash"),
                )
                connection.execute(
                    "INSERT INTO profiles (user_id) VALUES (?)", (cursor.lastrowid,)
                )
                user = connection.execute(
                    "SELECT username, is_admin FROM users"
                ).fetchone()
                profile = connection.execute(
                    "SELECT bio, img FROM profiles"
                ).fetchone()

            self.assertEqual(user, ("member", 0))
            self.assertEqual(profile, ("This is a default bio.", None))


if __name__ == "__main__":
    unittest.main()
