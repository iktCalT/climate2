"""Render a read-only NOAA CORe versus Open-Meteo PostgreSQL report."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from math import isfinite
from statistics import fmean

from db import ACTIVE_CLIMATE_PROVIDER, CLIMATE_TYPES, weather_db
from import_noaa_core import last_complete_month, parse_month
from noaa_core import (
    CANONICAL_LATS,
    CANONICAL_LOCATION_COUNT,
    CANONICAL_LONS,
    NOAA_CORE_PROVIDER,
)


MAX_COMPARISON_MONTHS = 12
METRIC_UNITS = {
    "temp_mean": "°C",
    "temp_max": "°C",
    "temp_min": "°C",
    "precip": "mm/day",
}
REPRESENTATIVE_POINTS = (
    ("land — New York area", 40.0, -72.0),
    ("ocean — central Pacific", 0.0, -140.0),
    ("polar — North Pole", 90.0, 0.0),
    ("polar — South Pole", -90.0, 0.0),
    ("dateline — west edge", 0.0, -180.0),
    ("dateline — east edge", 0.0, 180.0),
)
CANONICAL_COORDINATES = frozenset(
    (_coordinate_lat, _coordinate_lon)
    for _coordinate_lat in (round(float(value), 10) for value in CANONICAL_LATS)
    for _coordinate_lon in (round(float(value), 10) for value in CANONICAL_LONS)
)


@dataclass(frozen=True)
class ClimateRow:
    month: date
    latitude: float
    longitude: float
    temp_mean: float | None
    temp_max: float | None
    temp_min: float | None
    precip: float | None

    def value(self, metric):
        value = getattr(self, metric)
        if value is None or not isfinite(float(value)):
            return None
        return float(value)

    @property
    def complete(self):
        return all(self.value(metric) is not None for metric in CLIMATE_TYPES)

    @property
    def key(self):
        return (self.month, _coordinate(self.latitude), _coordinate(self.longitude))


def _coordinate(value):
    return round(float(value), 10)


def _format_value(value):
    return "missing" if value is None else f"{float(value):.3f}"


def _format_difference(value):
    return "missing" if value is None else f"{float(value):+.3f}"


def choose_months(requested, available, today=None):
    """Validate explicit months or select the latest bounded CORe months."""
    latest = last_complete_month(today)
    if requested:
        months = sorted(set(requested))
        if len(months) > MAX_COMPARISON_MONTHS:
            raise ValueError(
                f"compare at most {MAX_COMPARISON_MONTHS} distinct months per run"
            )
        future = [month for month in months if month > latest]
        if future:
            raise ValueError(
                f"comparisons use complete months through {latest:%Y-%m}"
            )
        return months

    months = sorted(set(available))[-MAX_COMPARISON_MONTHS:]
    if not months:
        raise ValueError("PostgreSQL has no NOAA CORe months to compare")
    return months


def available_core_months(con):
    with con.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT dates
            FROM data
            WHERE provider = %s
            ORDER BY dates
            """,
            (NOAA_CORE_PROVIDER,),
        )
        return [row[0] for row in cur.fetchall()]


def load_rows(con, provider, months):
    """Load selected rows without modifying or fetching climate data."""
    with con.cursor() as cur:
        cur.execute(
            """
            SELECT d.dates, l.lat, l.lon,
                   d.temp_mean, d.temp_max, d.temp_min, d.precip
            FROM data AS d
            JOIN locations AS l ON l.loc_id = d.loc_id
            WHERE d.provider = %s
              AND d.dates = ANY(%s::date[])
            ORDER BY d.dates, l.lat, l.lon
            """,
            (provider, list(months)),
        )
        records = [ClimateRow(*row) for row in cur.fetchall()]
    return index_canonical_rows(records)


def index_canonical_rows(records):
    """Index only the canonical map grid; ignore user-entered locations."""
    return {
        row.key: row
        for row in records
        if (row.key[1], row.key[2]) in CANONICAL_COORDINATES
    }


def metric_summary(core_rows, active_rows, month, metric):
    deltas = []
    for key in sorted(set(core_rows) & set(active_rows)):
        if key[0] != month:
            continue
        core_value = core_rows[key].value(metric)
        active_value = active_rows[key].value(metric)
        if core_value is not None and active_value is not None:
            deltas.append(float(core_value) - float(active_value))
    if not deltas:
        return None
    return {
        "count": len(deltas),
        "signed_mean": fmean(deltas),
        "mean_absolute": fmean(abs(delta) for delta in deltas),
        "minimum": min(deltas),
        "maximum": max(deltas),
    }


def evidence_complete(core_rows, active_rows, months):
    """Return whether both providers contain every required comparison value."""
    for month in months:
        core_month = [row for row in core_rows.values() if row.month == month]
        active_month = [row for row in active_rows.values() if row.month == month]
        if (
            len(core_month) != CANONICAL_LOCATION_COUNT
            or len(active_month) != CANONICAL_LOCATION_COUNT
            or not all(row.complete for row in core_month + active_month)
        ):
            return False
        for _, lat, lon in REPRESENTATIVE_POINTS:
            key = (month, _coordinate(lat), _coordinate(lon))
            if key not in core_rows or key not in active_rows:
                return False
    return True


def render_report(core_rows, active_rows, months):
    """Build deterministic Markdown from two provider-scoped row mappings."""
    lines = [
        "# Climate provider comparison",
        "",
        f"- NOAA provider: `{NOAA_CORE_PROVIDER}`",
        f"- Active provider: `{ACTIVE_CLIMATE_PROVIDER}`",
        "- Months: " + ", ".join(month.strftime("%Y-%m") for month in months),
        "- Operation: PostgreSQL read only; no provider request and no active-provider change",
        "- Evidence status: "
        + ("COMPLETE" if evidence_complete(core_rows, active_rows, months) else "INCOMPLETE"),
        "",
        "CORe is a model-and-observation reanalysis. The active Open-Meteo series is a two-model CMIP6 average. Differences are expected and do not by themselves show that either product is incorrect. This report supplies evidence for a separate human review; it never approves or activates a provider.",
        "",
        "## Coverage",
        "",
        "| Month | CORe rows | CORe complete | Open-Meteo rows | Open-Meteo complete | Paired rows | Expected |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for month in months:
        core_month = {key: row for key, row in core_rows.items() if key[0] == month}
        active_month = {
            key: row for key, row in active_rows.items() if key[0] == month
        }
        lines.append(
            f"| {month:%Y-%m} | {len(core_month)} | "
            f"{sum(row.complete for row in core_month.values())} | "
            f"{len(active_month)} | "
            f"{sum(row.complete for row in active_month.values())} | "
            f"{len(set(core_month) & set(active_month))} | "
            f"{CANONICAL_LOCATION_COUNT} |"
        )

    lines.extend(
        [
            "",
            "## Difference summary",
            "",
            "Deltas are `CORe - Open-Meteo` at identical canonical coordinates.",
            "",
            "| Month | Metric | Unit | Paired values | Signed mean | Mean absolute | Minimum | Maximum |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for month in months:
        for metric in CLIMATE_TYPES:
            summary = metric_summary(core_rows, active_rows, month, metric)
            if summary is None:
                lines.append(
                    f"| {month:%Y-%m} | `{metric}` | {METRIC_UNITS[metric]} | "
                    "0 | missing | missing | missing | missing |"
                )
                continue
            lines.append(
                f"| {month:%Y-%m} | `{metric}` | {METRIC_UNITS[metric]} | "
                f"{summary['count']} | {_format_difference(summary['signed_mean'])} | "
                f"{_format_value(summary['mean_absolute'])} | "
                f"{_format_difference(summary['minimum'])} | "
                f"{_format_difference(summary['maximum'])} |"
            )

    lines.extend(
        [
            "",
            "## Representative points",
            "",
            "The two dateline edges are shown separately to expose cyclic-coordinate handling.",
            "",
            "| Month | Sample | Latitude | Longitude | Metric | Unit | CORe | Open-Meteo | Delta |",
            "| --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for month in months:
        for label, latitude, longitude in REPRESENTATIVE_POINTS:
            key = (month, _coordinate(latitude), _coordinate(longitude))
            core_row = core_rows.get(key)
            active_row = active_rows.get(key)
            for metric in CLIMATE_TYPES:
                core_value = None if core_row is None else core_row.value(metric)
                active_value = None if active_row is None else active_row.value(metric)
                delta = (
                    None
                    if core_value is None or active_value is None
                    else float(core_value) - float(active_value)
                )
                lines.append(
                    f"| {month:%Y-%m} | {label} | {latitude:.1f} | "
                    f"{longitude:.1f} | `{metric}` | {METRIC_UNITS[metric]} | "
                    f"{_format_value(core_value)} | {_format_value(active_value)} | "
                    f"{_format_difference(delta)} |"
                )
    return "\n".join(lines) + "\n"


def run(requested_months=None):
    with weather_db() as con:
        con.execute("SET TRANSACTION READ ONLY")
        months = choose_months(requested_months, available_core_months(con))
        core_rows = load_rows(con, NOAA_CORE_PROVIDER, months)
        active_rows = load_rows(con, ACTIVE_CLIMATE_PROVIDER, months)
    print(render_report(core_rows, active_rows, months), end="")
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Compare provider-scoped PostgreSQL rows without contacting a provider "
            "or changing the active website series."
        )
    )
    parser.add_argument(
        "--month",
        action="append",
        type=parse_month,
        help=(
            "complete YYYY-MM month to compare; repeat up to 12 times "
            "(default: latest available CORe months)"
        ),
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        return run(args.month)
    except ValueError as error:
        print(f"Comparison stopped: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
