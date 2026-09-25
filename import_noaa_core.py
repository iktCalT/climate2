"""Import selected NOAA CORe months resumably into provider-scoped PostgreSQL."""

from __future__ import annotations

import argparse
from datetime import date, timedelta

from db import weather_db
from noaa_core import (
    CoreArchiveClient,
    CoreError,
    EccodesDecoder,
    NOAA_CORE_PROVIDER,
    completed_core_months,
    load_core_month,
    upsert_core_month,
)


CORE_PERIODS = {
    "1950-1953": (date(1950, 1, 1), date(1953, 12, 1)),
    "2023-2026": (date(2023, 1, 1), date(2026, 12, 1)),
    "1950-present": (date(1950, 1, 1), None),
}
DEFAULT_CORE_PERIODS = ("1950-1953", "2023-2026")
DEFAULT_MONTH_LIMIT = 1
MAX_MONTH_LIMIT = 12


def parse_month(value):
    try:
        parsed = date.fromisoformat(f"{value}-01")
    except ValueError as error:
        raise argparse.ArgumentTypeError("month must use YYYY-MM") from error
    return parsed


def next_month(month):
    if month.month == 12:
        return date(month.year + 1, 1, 1)
    return date(month.year, month.month + 1, 1)


def last_complete_month(today=None):
    today = date.today() if today is None else today
    first_of_current_month = date(today.year, today.month, 1)
    previous_day = first_of_current_month - timedelta(days=1)
    return date(previous_day.year, previous_day.month, 1)


def months_between(start, end):
    months = []
    current = start
    while current <= end:
        months.append(current)
        current = next_month(current)
    return months


def selected_months(periods=None, explicit_months=None, through=None, today=None):
    """Return stable, unique, complete calendar months for one run."""
    latest = last_complete_month(today)
    if through is not None:
        latest = min(latest, through)

    if explicit_months:
        requested = list(explicit_months)
    else:
        names = list(DEFAULT_CORE_PERIODS) if not periods else list(periods)
        requested = []
        for name in names:
            start, end = CORE_PERIODS[name]
            period_end = latest if end is None else min(end, latest)
            requested.extend(months_between(start, period_end))

    unique = sorted(set(requested))
    invalid = [month for month in unique if month > latest]
    if invalid:
        raise ValueError(
            f"NOAA CORe imports only complete months through {latest:%Y-%m}"
        )
    return unique


def run(
    periods=None,
    explicit_months=None,
    through=None,
    limit=DEFAULT_MONTH_LIMIT,
    dry_run=False,
    validate_only=False,
    timeout_seconds=60.0,
    retries=3,
):
    months = selected_months(
        periods=periods,
        explicit_months=explicit_months,
        through=through,
    )
    with weather_db() as con:
        completed = completed_core_months(con, months)

    if validate_only and explicit_months:
        pending = months
    else:
        pending = [month for month in months if month not in completed]
    selected = pending[:limit]

    print(
        f"NOAA CORe checkpoint: {len(completed)}/{len(months)} requested months "
        f"complete for provider {NOAA_CORE_PROVIDER}."
    )
    if not selected:
        print("Nothing to import.")
        return 0
    print(
        "Next months: " + ", ".join(month.strftime("%Y-%m") for month in selected)
    )
    if dry_run:
        print("Dry run: NOAA was not contacted and PostgreSQL was not changed.")
        return 0

    archive = CoreArchiveClient(
        timeout_seconds=timeout_seconds,
        retries=retries,
    )
    try:
        decoder = EccodesDecoder()
    except CoreError as error:
        print(f"Importer stopped: {error}")
        return 1

    for number, month in enumerate(selected, start=1):
        print(f"[{number}/{len(selected)}] Downloading and validating {month:%Y-%m}")
        try:
            data = load_core_month(month, archive=archive, decoder=decoder)
            if validate_only:
                print(
                    f"Validated {month:%Y-%m}: "
                    f"temperature {data.temp_min.min():.1f}..{data.temp_max.max():.1f} °C; "
                    f"precipitation {data.precip.min():.2f}..{data.precip.max():.2f} mm/day"
                )
            else:
                upsert_core_month(data)
                print(f"Committed {month:%Y-%m} to PostgreSQL.")
        except CoreError as error:
            print(
                f"Importer stopped at {month:%Y-%m}: {error}. "
                "Earlier committed months remain resumable."
            )
            return 1

    if validate_only:
        print("Validation finished; PostgreSQL was not changed.")
    else:
        print("Batch finished. Re-run the same command to continue from PostgreSQL.")
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Import NOAA CORe resumably for the canonical global grid. "
            "No account, API key, or licence-acceptance step is required."
        )
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--period",
        action="append",
        choices=tuple(CORE_PERIODS),
        help=(
            "period to import; repeat as needed "
            "(default: the two recorded edge periods)"
        ),
    )
    selection.add_argument(
        "--month",
        action="append",
        type=parse_month,
        help="specific complete YYYY-MM month; repeat as needed",
    )
    parser.add_argument(
        "--through",
        type=parse_month,
        help="do not select period months after YYYY-MM",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_MONTH_LIMIT,
        help=f"months to process this run (1-{MAX_MONTH_LIMIT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show PostgreSQL progress without contacting NOAA",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="download and validate without writing PostgreSQL",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=60.0,
        help="HTTPS timeout for one NOAA index or byte range (default: 60)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="bounded attempts per NOAA request (default: 3)",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= MAX_MONTH_LIMIT:
        parser.error(f"--limit must be between 1 and {MAX_MONTH_LIMIT}")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    if not 1 <= args.retries <= 5:
        parser.error("--retries must be between 1 and 5")
    if args.dry_run and args.validate_only:
        parser.error("--dry-run and --validate-only cannot be combined")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        return run(
            periods=args.period,
            explicit_months=args.month,
            through=args.through,
            limit=args.limit,
            dry_run=args.dry_run,
            validate_only=args.validate_only,
            timeout_seconds=args.timeout_seconds,
            retries=args.retries,
        )
    except ValueError as error:
        print(f"Importer stopped: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
