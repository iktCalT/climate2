from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from io import StringIO
import unittest
from unittest.mock import patch

import climate.cli.import_noaa_core as import_noaa_core


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

    def test_recent_reverse_period_is_complete_unique_and_bounded(self):
        months = import_noaa_core.selected_months(
            periods=["2016-2026", "2023-2026"],
            newest_first=True,
            today=date(2026, 9, 26),
        )
        self.assertEqual(months, list(reversed(import_noaa_core.months_between(
            date(2016, 1, 1), date(2026, 8, 1)
        ))))
        self.assertEqual(len(months), 128)
        capped = import_noaa_core.selected_months(
            periods=["2016-2026"], newest_first=True,
            through=date(2022, 12, 1), today=date(2026, 9, 26),
        )
        self.assertEqual(capped[0], date(2022, 12, 1))
        self.assertEqual(capped[-1], date(2016, 1, 1))
        after_period = import_noaa_core.selected_months(
            periods=["2016-2026"], newest_first=True, today=date(2027, 6, 1),
        )
        self.assertEqual(after_period[0], date(2026, 12, 1))

    def test_reverse_order_still_rejects_incomplete_explicit_months(self):
        with self.assertRaisesRegex(ValueError, "complete months through 2026-08"):
            import_noaa_core.selected_months(
                explicit_months=[date(2026, 9, 1)], newest_first=True,
                today=date(2026, 9, 26),
            )

    def test_reverse_import_skips_completed_before_limit_and_resumes(self):
        months = [date(2022, month, 1) for month in (10, 12, 11, 12)]
        committed = {date(2022, 12, 1)}
        with (
            patch.object(import_noaa_core, "weather_db"),
            patch.object(import_noaa_core, "completed_core_months",
                         side_effect=lambda con, requested: committed.copy()),
            patch.object(import_noaa_core, "CoreArchiveClient"),
            patch.object(import_noaa_core, "EccodesDecoder"),
            patch.object(import_noaa_core, "load_core_month",
                         side_effect=lambda month, **kwargs: month) as load,
            patch.object(import_noaa_core, "upsert_core_month",
                         side_effect=committed.add) as save,
            redirect_stdout(StringIO()),
        ):
            for expected in (date(2022, 11, 1), date(2022, 10, 1)):
                self.assertEqual(import_noaa_core.run(
                    explicit_months=months, newest_first=True, limit=1,
                ), 0)
                self.assertEqual(load.call_args.args[0], expected)
                self.assertEqual(save.call_args.args[0], expected)
            self.assertEqual(save.call_count, 2)

    def test_reverse_import_stops_on_failure_then_retries_failed_month(self):
        months = [date(2022, month, 1) for month in (10, 11, 12)]
        committed = set()
        with (
            patch.object(import_noaa_core, "weather_db"),
            patch.object(import_noaa_core, "completed_core_months",
                         side_effect=lambda con, requested: committed.copy()),
            patch.object(import_noaa_core, "CoreArchiveClient"),
            patch.object(import_noaa_core, "EccodesDecoder"),
            patch.object(import_noaa_core, "load_core_month", side_effect=[
                date(2022, 12, 1), import_noaa_core.CoreError("archive unavailable"),
                date(2022, 11, 1), date(2022, 10, 1),
            ]) as load,
            patch.object(import_noaa_core, "upsert_core_month", side_effect=committed.add),
            redirect_stdout(StringIO()),
        ):
            self.assertEqual(import_noaa_core.run(
                explicit_months=months, newest_first=True, limit=3,
            ), 1)
            self.assertEqual(committed, {date(2022, 12, 1)})
            self.assertEqual(import_noaa_core.run(
                explicit_months=months, newest_first=True, limit=3,
            ), 0)
        self.assertEqual([call.args[0] for call in load.call_args_list], [
            date(2022, 12, 1), date(2022, 11, 1),
            date(2022, 11, 1), date(2022, 10, 1),
        ])
        self.assertEqual(committed, set(months))

    def test_cli_reverse_dry_run_does_not_contact_archive_or_write(self):
        output = StringIO()
        with (
            patch.object(import_noaa_core, "weather_db"),
            patch.object(import_noaa_core, "completed_core_months", return_value=set()),
            patch.object(import_noaa_core, "CoreArchiveClient") as archive,
            patch.object(import_noaa_core, "upsert_core_month") as save,
            redirect_stdout(output),
        ):
            self.assertEqual(import_noaa_core.main([
                "--period", "2016-2026", "--through", "2022-12",
                "--newest-first", "--limit", "2", "--dry-run",
            ]), 0)
        self.assertIn("Next months: 2022-12, 2022-11", output.getvalue())
        archive.assert_not_called()
        save.assert_not_called()

    def test_batch_and_network_options_are_bounded(self):
        args = import_noaa_core.parse_args([])
        self.assertEqual(args.limit, 1)
        self.assertEqual(args.timeout_seconds, 60)
        self.assertEqual(args.retries, 3)
        self.assertFalse(args.newest_first)
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
