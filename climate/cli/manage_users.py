"""Deliberately grant or revoke local administrator access.

This script manages only the ignored local SQLite user database. It never
contacts PostgreSQL or a remote service.
"""
import argparse
import os
import sqlite3
from contextlib import closing


DEFAULT_USER_DATABASE_PATH = "static/users.db"


def set_admin_status(username, is_admin, database_path=None):
    """Set one existing user's administrator flag and return whether it exists."""
    path = database_path or os.environ.get("USER_DATABASE_PATH", DEFAULT_USER_DATABASE_PATH)
    with closing(sqlite3.connect(path)) as con:
        result = con.execute(
            "UPDATE users SET is_admin = ? WHERE username = ?", (bool(is_admin), username)
        )
        con.commit()
    return result.rowcount == 1


def main():
    parser = argparse.ArgumentParser(description="Manage local Climate administrator roles.")
    parser.add_argument("action", choices=("grant-admin", "revoke-admin"))
    parser.add_argument("username")
    args = parser.parse_args()

    if not set_admin_status(args.username, args.action == "grant-admin"):
        parser.error(f"No user named {args.username!r} exists in the local user database.")

    print(f"Updated administrator status for {args.username!r}.")


if __name__ == "__main__":
    main()
