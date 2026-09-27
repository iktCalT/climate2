"""Create the ignored local SQLite account database without personal data."""

import os
from pathlib import Path
import sqlite3

from climate.paths import SQL_DIRECTORY


DEFAULT_USER_DATABASE_PATH = "static/users.db"


def initialize_user_database(database_path=None):
    """Create missing account tables and return the database path."""
    path = Path(
        database_path
        or os.environ.get("USER_DATABASE_PATH", DEFAULT_USER_DATABASE_PATH)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = (SQL_DIRECTORY / "user_schema.sql").read_text()
    with sqlite3.connect(path) as connection:
        connection.executescript(schema)
    return path


def main():
    path = initialize_user_database()
    print(f"Local account schema is ready at {path}.")


if __name__ == "__main__":
    main()
