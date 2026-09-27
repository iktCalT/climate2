"""Flask entry point: .venv/bin/python -m flask --app app run."""

from climate.web.app import app

__all__ = ["app"]
