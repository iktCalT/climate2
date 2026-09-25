from contextlib import redirect_stderr
from datetime import date
from io import StringIO
import unittest

import import_noaa_core


class NOAAcoreCommandTests(unittest.TestCase):
    def test_default_periods_stop_at_last_complete_month(self):
        months = import_noaa_core.selected_months(today=date(2026, 9, 24))

        self.assertEqual(months[0], date(1950, 1, 1))
        self.assertIn(date(1953, 12, 1), months)
        self.assertIn(date(2026, 8, 1), months)
        self.assertNotIn(date(2026, 9, 1), months)
        self.assertEqual(len(months), 48 + 44)

    def test_specific_future_month_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "complete months through 2026-08"):
            import_noaa_core.selected_months(
                explicit_months=[date(2026, 9, 1)],
                today=date(2026, 9, 24),
            )

    def test_full_history_period_is_explicit_and_stops_at_latest_complete_month(self):
        months = import_noaa_core.selected_months(
            periods=["1950-present"],
            today=date(2026, 9, 24),
        )

        self.assertEqual(months[0], date(1950, 1, 1))
        self.assertEqual(months[-1], date(2026, 8, 1))
        self.assertEqual(len(months), 920)

    def test_full_history_period_respects_an_earlier_through_month(self):
        months = import_noaa_core.selected_months(
            periods=["1950-present"],
            through=date(1954, 2, 1),
            today=date(2026, 9, 24),
        )

        self.assertEqual(months[-1], date(1954, 2, 1))
        self.assertEqual(len(months), 50)

    def test_period_and_month_are_mutually_exclusive(self):
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            import_noaa_core.parse_args(
                ["--period", "1950-1953", "--month", "2023-01"]
            )

    def test_batch_and_network_options_are_bounded(self):
        args = import_noaa_core.parse_args([])
        self.assertEqual(args.limit, 1)
        self.assertEqual(args.timeout_seconds, 60)
        self.assertEqual(args.retries, 3)
        for invalid in (
            ["--limit", "13"],
            ["--timeout-seconds", "0"],
            ["--retries", "6"],
            ["--dry-run", "--validate-only"],
        ):
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                import_noaa_core.parse_args(invalid)


if __name__ == "__main__":
    unittest.main()
