"""Repository resource paths, independent of module location."""

import os
import stat
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIRECTORY = PROJECT_ROOT / "templates"
STATIC_DIRECTORY = PROJECT_ROOT / "static"
SQL_DIRECTORY = PROJECT_ROOT / "sql"


def climate_mode():
    """Return the explicit runtime mode or reject a misspelled setting."""
    mode = os.environ.get("CLIMATE_ENV", "development")
    if mode not in ("development", "production"):
        raise ValueError("CLIMATE_ENV must be development or production")
    return mode


def resolve_user_database_path(database_path=None):
    """Choose the shared account database path, preserving configured locations."""
    if climate_mode() == "production":
        root = production_state_root()
        expected = root / "users.db"
        configured = database_path or os.environ.get("USER_DATABASE_PATH")
        if configured and Path(configured).resolve() != expected:
            raise ValueError("Production account path must be inside CLIMATE_STATE_ROOT")
        if expected.is_symlink() or (expected.exists() and
                                     (not expected.is_file() or expected.stat().st_nlink != 1)):
            raise ValueError("Unsafe production account database path")
        return expected
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


def production_state_root():
    """Resolve an existing private mount shared by web and account CLI."""
    selected = os.environ.get("CLIMATE_STATE_ROOT", "")
    if not selected or not Path(selected).is_absolute():
        raise ValueError("Production requires an absolute CLIMATE_STATE_ROOT")
    selected_path = Path(selected)
    if selected_path == PROJECT_ROOT or selected_path.is_relative_to(PROJECT_ROOT):
        raise ValueError("Production state root must be outside source")
    if selected_path.is_symlink():
        raise ValueError("Production state root cannot be a symlink")
    root = selected_path.resolve()
    if not root.is_dir() or root == PROJECT_ROOT or root.is_relative_to(PROJECT_ROOT):
        raise ValueError("Production state root must be an existing private directory outside source")
    metadata = root.stat()
    if (not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.geteuid()
            or metadata.st_mode & 0o077 or not os.access(root, os.W_OK | os.X_OK)):
        raise ValueError("Production state root must be owned and private to the app user")
    if STATIC_DIRECTORY.resolve().is_relative_to(root) or root.is_relative_to(STATIC_DIRECTORY.resolve()):
        raise ValueError("Production state root overlaps public assets")
    return root
