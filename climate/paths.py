"""Repository resource paths, independent of module location."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIRECTORY = PROJECT_ROOT / "templates"
STATIC_DIRECTORY = PROJECT_ROOT / "static"
SQL_DIRECTORY = PROJECT_ROOT / "sql"
