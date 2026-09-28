"""Create the ignored local SQLite account database without personal data."""

import sqlite3
from contextlib import closing

from climate.paths import SQL_DIRECTORY, resolve_user_database_path


def initialize_user_database(database_path=None):
    """Create missing account tables and return the database path."""
    path = resolve_user_database_path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = (SQL_DIRECTORY / "user_schema.sql").read_text()
    with closing(sqlite3.connect(path)) as connection:
        with connection:
            connection.executescript(schema)
    return path


def main():
    path = initialize_user_database()
    print(f"Local account schema is ready at {path}.")


if __name__ == "__main__":
    main()
