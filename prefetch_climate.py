"""Resumable prefetch for the canonical map grid's edge-year climate data.

PostgreSQL is the checkpoint. Run this command repeatedly; complete locations
are skipped and every successful missing date range is committed separately.
"""

import argparse
from datetime import date

import numpy as np

from db import weather_db
from helpers_data import get_data, missing_location_ranges


PREFETCH_PERIODS = (
    ("1950-1953", date(1950, 1, 1), date(1953, 12, 31)),
    ("2023-2026", date(2023, 1, 1), date(2026, 12, 31)),
)
PREFETCH_FIELDS = ("temp_mean", "temp_max", "temp_min", "precip")
DEFAULT_LOCATION_LIMIT = 100
MAX_LOCATION_LIMIT = 100


def canonical_grid():
    """Return the stable 2-degree by 4-degree global map grid."""
    lats = np.linspace(-90, 90, 91)
    lons = np.linspace(-180, 180, 91)
    return [(float(lat), float(lon)) for lat in lats for lon in lons]


def _month_count(start, end):
    return (end.year - start.year) * 12 + end.month - start.month + 1


def load_period_completion(con, periods=PREFETCH_PERIODS):
    """Return the period indexes complete at each canonical grid location."""
    complete_value = " AND ".join(f"d.{field} IS NOT NULL" for field in PREFETCH_FIELDS)
    count_columns = []
    params = []
    for index, (_, start, end) in enumerate(periods):
        count_columns.append(
            "COUNT(DISTINCT date_trunc('month', d.dates)) "
            f"FILTER (WHERE d.dates BETWEEN %s AND %s AND {complete_value}) "
            f"AS period_{index}"
        )
        params.extend((start, end))

    lats = [float(value) for value in np.linspace(-90, 90, 91)]
    lons = [float(value) for value in np.linspace(-180, 180, 91)]
    date_predicates = []
    for _, start, end in periods:
        date_predicates.append("d.dates BETWEEN %s AND %s")
        params.extend((start, end))
    params.extend((lats, lons))

    query = f"""
        SELECT l.lat, l.lon, {", ".join(count_columns)}
        FROM locations AS l
        JOIN data AS d ON d.loc_id = l.loc_id
        WHERE ({" OR ".join(date_predicates)})
          AND l.lat = ANY(%s)
          AND l.lon = ANY(%s)
        GROUP BY l.lat, l.lon
    """
    with con.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    completion = {}
    for row in rows:
        completed_periods = {
            index
            for index, (_, start, end) in enumerate(periods)
            if row[index + 2] == _month_count(start, end)
        }
        completion[(round(float(row[0]), 10), round(float(row[1]), 10))] = completed_periods
    return completion


def select_candidates(locations, completion, limit, periods=PREFETCH_PERIODS):
    """Choose the next incomplete locations in stable latitude/longitude order."""
    all_periods = set(range(len(periods)))
    candidates = []
    for location in locations:
        key = (round(location[0], 10), round(location[1], 10))
        missing_periods = tuple(sorted(all_periods - completion.get(key, set())))
        if missing_periods:
            candidates.append((location, missing_periods))
            if len(candidates) == limit:
                break
    return candidates


def prefetch_period(location, period):
    """Fetch each missing range independently so successful work is durable."""
    _, start, end = period
    ranges = missing_location_ranges(
        location,
        start,
        end,
        fields=PREFETCH_FIELDS,
    )
    succeeded = 0
    for range_start, range_end in ranges:
        if get_data(
            location=location,
            date_start=range_start,
            date_end=range_end,
            insert_into_database=True,
            force_update_database=True,
        ):
            succeeded += 1
    return succeeded, len(ranges)


def run(limit=DEFAULT_LOCATION_LIMIT, dry_run=False):
    """Run one bounded prefetch batch and return a process exit status."""
    locations = canonical_grid()
    with weather_db() as con:
        completion = load_period_completion(con)

    complete_count = sum(
        completed == set(range(len(PREFETCH_PERIODS)))
        for completed in completion.values()
    )
    candidates = select_candidates(locations, completion, limit)
    remaining = len(locations) - complete_count
    print(
        f"Canonical grid: {complete_count}/{len(locations)} locations complete; "
        f"{remaining} remaining."
    )
    if not candidates:
        print("Nothing to fetch.")
        return 0
    if dry_run:
        print(f"Dry run: the next batch contains {len(candidates)} locations.")
        return 0

    successful_requests = 0
    total_requests = 0
    for number, (location, period_indexes) in enumerate(candidates, start=1):
        lat, lon = location
        labels = ", ".join(PREFETCH_PERIODS[index][0] for index in period_indexes)
        print(f"[{number}/{len(candidates)}] {lat:g}, {lon:g}: checking {labels}")
        for index in period_indexes:
            succeeded, attempted = prefetch_period(location, PREFETCH_PERIODS[index])
            successful_requests += succeeded
            total_requests += attempted

    failures = total_requests - successful_requests
    print(
        f"Batch finished: {successful_requests}/{total_requests} missing ranges fetched. "
        "Run the same command again to verify progress and continue."
    )
    return 1 if failures else 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Fill PostgreSQL resumably for the canonical global grid in "
            "1950-1953 and 2023-2026."
        )
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LOCATION_LIMIT,
        help=f"locations to check this run (1-{MAX_LOCATION_LIMIT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show database progress without contacting Open-Meteo",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= MAX_LOCATION_LIMIT:
        parser.error(f"--limit must be between 1 and {MAX_LOCATION_LIMIT}")
    return args


def main(argv=None):
    args = parse_args(argv)
    return run(limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
