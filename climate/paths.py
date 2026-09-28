"""Repository resource paths, independent of module location."""

import os
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIRECTORY = PROJECT_ROOT / "templates"
STATIC_DIRECTORY = PROJECT_ROOT / "static"
SQL_DIRECTORY = PROJECT_ROOT / "sql"


def resolve_user_database_path(database_path=None):
    """Choose the shared account database path, preserving configured locations."""
    configured = database_path or os.environ.get("USER_DATABASE_PATH")
    if configured:
        return Path(configured)

    legacy_path = STATIC_DIRECTORY / "users.db"
    if legacy_path.exists():
        warnings.warn(
            "Using legacy static/users.db for accounts. Set USER_DATABASE_PATH "
            "to relocate it outside the static directory.",
            RuntimeWarning,
            stacklevel=2,
        )
        return legacy_path
    return PROJECT_ROOT / "instance" / "users.db"
