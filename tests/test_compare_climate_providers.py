from contextlib import redirect_stderr
from datetime import date
from io import StringIO
import unittest

from compare_climate_providers import (
    ClimateRow,
    MAX_COMPARISON_MONTHS,
    choose_months,
    evidence_complete,
    index_canonical_rows,
    metric_summary,
    parse_args,
    render_report,
)
from noaa_core import CANONICAL_LOCATION_COUNT


def row(month, latitude, longitude, values=(10.0, 15.0, 5.0, 2.0)):
    return ClimateRow(month, latitude, longitude, *values)


class ProviderComparisonTests(unittest.TestCase):
    def test_default_months_are_latest_bounded_available_core_months(self):
        available = [date(2000 + year, 1, 1) for year in range(15)]

        selected = choose_months(None, available, today=date(2026, 9, 24))

        self.assertEqual(len(selected), MAX_COMPARISON_MONTHS)
        self.assertEqual(selected[0], date(2003, 1, 1))
        self.assertEqual(selected[-1], date(2014, 1, 1))

    def test_explicit_months_are_unique_sorted_and_complete(self):
        selected = choose_months(
            [date(1952, 2, 1), date(1950, 1, 1), date(1952, 2, 1)],
            [],
            today=date(2026, 9, 24),
        )

        self.assertEqual(selected, [date(1950, 1, 1), date(1952, 2, 1)])

    def test_more_than_twelve_explicit_months_are_rejected(self):
        requested = [date(2000 + year, 1, 1) for year in range(13)]

        with self.assertRaisesRegex(ValueError, "at most 12"):
            choose_months(requested, [], today=date(2026, 9, 24))

    def test_current_or_future_month_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "complete months through 2026-08"):
            choose_months(
                [date(2026, 9, 1)], [], today=date(2026, 9, 24)
            )

    def test_metric_summary_uses_only_paired_non_null_values(self):
        month = date(1950, 1, 1)
        core = {
            item.key: item
            for item in (
                row(month, 0, 0, (10, 20, 0, 2)),
                row(month, 0, 4, (None, 30, 1, 4)),
            )
        }
        active = {
            item.key: item
            for item in (
                row(month, 0, 0, (7, 21, -1, 1)),
                row(month, 0, 4, (8, 25, 2, 2)),
            )
        }

        summary = metric_summary(core, active, month, "temp_mean")

        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["signed_mean"], 3)
        self.assertEqual(summary["mean_absolute"], 3)

    def test_nonfinite_database_values_are_reported_as_missing(self):
        month = date(1950, 1, 1)
        invalid = row(month, 0, 0, (float("nan"), 20, 0, 2))

        self.assertIsNone(invalid.value("temp_mean"))
        self.assertFalse(invalid.complete)

    def test_noncanonical_user_locations_are_excluded(self):
        month = date(1950, 1, 1)
        canonical = row(month, 40, -72)
        user_location = row(month, 40.123, -72.456)

        indexed = index_canonical_rows([canonical, user_location])

        self.assertEqual(indexed, {canonical.key: canonical})

    def test_report_exposes_missing_evidence_and_product_warning(self):
        month = date(1950, 1, 1)
        core_row = row(month, 40, -72)
        core = {core_row.key: core_row}

        report = render_report(core, {}, [month])

        self.assertIn("Evidence status: INCOMPLETE", report)
        self.assertIn("reanalysis", report)
        self.assertIn("CMIP6 average", report)
        self.assertIn("| 1950-01 | 1 | 1 | 0 | 0 | 0 |", report)
        self.assertIn("land — New York area", report)
        self.assertIn("missing", report)

    def test_report_delta_direction_is_core_minus_open_meteo(self):
        month = date(1950, 1, 1)
        core_row = row(month, 40, -72, (12, 18, 3, 4))
        active_row = row(month, 40, -72, (10, 20, 2, 1))

        report = render_report(
            {core_row.key: core_row}, {active_row.key: active_row}, [month]
        )

        self.assertIn("Deltas are `CORe - Open-Meteo`", report)
        self.assertIn("| `temp_mean` | °C | 1 | +2.000 | 2.000", report)
        self.assertIn("| `precip` | mm/day | 1 | +3.000 | 3.000", report)

    def test_incomplete_rows_cannot_mark_evidence_complete(self):
        month = date(1950, 1, 1)
        core = {}
        active = {}
        for index in range(CANONICAL_LOCATION_COUNT):
            latitude = float(index)
            core_row = row(month, latitude, 0)
            active_row = row(month, latitude, 0)
            core[core_row.key] = core_row
            active[active_row.key] = active_row

        self.assertFalse(evidence_complete(core, active, [month]))

    def test_month_argument_parses_and_invalid_format_exits(self):
        self.assertEqual(parse_args(["--month", "1952-02"]).month, [date(1952, 2, 1)])
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            parse_args(["--month", "1952/02"])


if __name__ == "__main__":
    unittest.main()
