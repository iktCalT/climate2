"""Deliberately create, grant, or revoke local administrator access.

This script manages only the ignored local SQLite user database. It never
contacts PostgreSQL or a remote service.
"""
import argparse
import getpass
import re
import sqlite3
import stat
import sys
import unicodedata
import warnings
from contextlib import closing

from werkzeug.security import generate_password_hash

from climate.paths import STATIC_DIRECTORY, resolve_user_database_path


class AdminCreationError(ValueError):
    """A safe, user-facing reason administrator creation could not finish."""


def _validate_username(username):
    if not isinstance(username, str) or re.fullmatch(r"[A-Za-z0-9_-]{3,16}", username) is None:
        raise AdminCreationError("Username must be 3–16 ASCII letters, digits, underscores, or hyphens.")


def _validate_password(password):
    if (not isinstance(password, str) or not 15 <= len(password) <= 128
            or password.isspace()
            or any(unicodedata.category(char) in ("Cc", "Cs") for char in password)):
        raise AdminCreationError("Password must contain 15–128 characters without control characters.")


def _existing_private_database(database_path):
    try:
        selected = resolve_user_database_path(database_path).absolute()
        static = STATIC_DIRECTORY.resolve(strict=True)
        static_identity = static.stat()

        def reject_static_alias(candidate):
            if candidate.is_relative_to(static):
                raise ValueError
            # Ancestor identity catches symlink and case aliases without scanning files.
            for ancestor in candidate.parents:
                parent_identity = ancestor.stat()
                if (parent_identity.st_dev, parent_identity.st_ino) == (
                        static_identity.st_dev, static_identity.st_ino):
                    raise ValueError

        # Check the selected location before following a final symlink out of static.
        reject_static_alias(selected)
        path = selected.resolve(strict=True)
        reject_static_alias(path)
        identity = path.stat()
        if not stat.S_ISREG(identity.st_mode) or identity.st_nlink != 1:
            raise ValueError
    except (OSError, RuntimeError, TypeError, ValueError):
        raise AdminCreationError("An initialized private user database is required.") from None
    return path


def create_admin(username, password, database_path=None):
    """Atomically add an administrator and default profile to an existing store."""
    _validate_username(username)
    _validate_password(password)
    path = _existing_private_database(database_path)
    try:
        # mode=rw cannot create a missing file, even if it vanishes after validation.
        with closing(sqlite3.connect(f"{path.as_uri()}?mode=rw", uri=True)) as con:
            with con:
                try:
                    user = con.execute(
                        "INSERT INTO users (username, hash_pwd, is_admin) VALUES (?, ?, 1)",
                        (username, generate_password_hash(password)),
                    )
                except sqlite3.IntegrityError as error:
                    if error.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                        raise AdminCreationError("Username is already in use.") from None
                    raise
                con.execute("INSERT INTO profiles (user_id) VALUES (?)", (user.lastrowid,))
    except sqlite3.Error:
        raise AdminCreationError("Administrator creation failed; check the initialized user database.") from None


def _read_password():
    if not (sys.stdin.isatty() and sys.stderr.isatty()):
        raise AdminCreationError("An interactive terminal is required.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("Password: ")
            confirmation = getpass.getpass("Confirm password: ")
    except (getpass.GetPassWarning, EOFError, KeyboardInterrupt, OSError):
        raise AdminCreationError("Password entry was cancelled or unavailable.") from None
    if password != confirmation:
        raise AdminCreationError("Passwords do not match.")
    _validate_password(password)
    return password


def set_admin_status(username, is_admin, database_path=None):
    """Set one existing user's administrator flag and return whether it exists."""
    path = resolve_user_database_path(database_path)
    with closing(sqlite3.connect(path)) as con:
        result = con.execute(
            "UPDATE users SET is_admin = ? WHERE username = ?", (bool(is_admin), username)
        )
        con.commit()
    return result.rowcount == 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Manage local Climate administrator roles.")
    parser.add_argument("action", choices=("grant-admin", "revoke-admin", "create-admin"))
    parser.add_argument("username")
    argv = sys.argv[1:] if argv is None else list(argv)

    if argv and argv[0] == "create-admin":
        # argparse includes unknown argument values in errors; never echo a
        # password accidentally supplied as an extra CLI argument.
        if len(argv) != 2:
            parser.error("create-admin requires exactly one username.")
        try:
            _validate_username(argv[1])
            create_admin(argv[1], _read_password())
        except AdminCreationError as error:
            parser.error(str(error))
        print("Administrator account created.")
        return

    if len(argv) > 1 and argv[:2] == ["--", "create-admin"]:
        parser.error("Use create-admin USERNAME without a leading separator.")

    args = parser.parse_args(argv)
    if args.action == "create-admin":
        parser.error("Use create-admin USERNAME.")

    if not set_admin_status(args.username, args.action == "grant-admin"):
        parser.error(f"No user named {args.username!r} exists in the local user database.")

    print(f"Updated administrator status for {args.username!r}.")


if __name__ == "__main__":
    main()
