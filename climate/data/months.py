"""Calendar helpers shared by administrator workflows and CLI selection."""

import argparse
from datetime import date, timedelta


def parse_month(value):
    try:
        return date.fromisoformat(f"{value}-01")
    except ValueError as error:
        raise argparse.ArgumentTypeError("month must use YYYY-MM") from error


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
