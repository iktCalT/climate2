from contextlib import redirect_stderr
from datetime import date
from io import StringIO
import unittest
from unittest.mock import Mock, call, patch

import prefetch_climate


class ResumablePrefetchTests(unittest.TestCase):
    def test_canonical_grid_is_stable_and_has_8281_locations(self):
        locations = prefetch_climate.canonical_grid()

        self.assertEqual(len(locations), 91 * 91)
        self.assertEqual(locations[0], (-90.0, -180.0))
        self.assertEqual(locations[-1], (90.0, 180.0))
        self.assertEqual(len(set(locations)), len(locations))

    def test_periods_cover_the_requested_years(self):
        self.assertEqual(
            prefetch_climate.PREFETCH_PERIODS,
            (
                ("1950-1953", date(1950, 1, 1), date(1953, 12, 31)),
                ("2023-2026", date(2023, 1, 1), date(2026, 12, 31)),
            ),
        )

    def test_candidate_selection_skips_only_fully_complete_locations(self):
        locations = [(0.0, 0.0), (0.0, 4.0), (0.0, 8.0)]
        completion = {
            (0.0, 0.0): {0, 1},
            (0.0, 4.0): {0},
        }

        candidates = prefetch_climate.select_candidates(
            locations, completion, limit=2
        )

        self.assertEqual(
            candidates,
            [((0.0, 4.0), (1,)), ((0.0, 8.0), (0, 1))],
        )

    def test_request_pacer_spaces_request_starts(self):
        pacer = prefetch_climate.RequestPacer(30)
        with patch("prefetch_climate.time.monotonic", side_effect=[10, 12]), patch(
            "prefetch_climate.time.sleep"
        ) as sleep:
            pacer.wait()
            pacer.wait()

        sleep.assert_called_once_with(28)

    def test_prefetch_period_commits_each_missing_range_independently(self):
        ranges = [("1953-01-01", "1953-12-31"), ("1952-02-01", "1952-02-28")]
        pacer = Mock()
        with patch(
            "prefetch_climate.missing_location_ranges", return_value=ranges
        ), patch("prefetch_climate.get_data", side_effect=[True, True]) as fetch:
            result = prefetch_climate.prefetch_period(
                (2.0, 4.0),
                prefetch_climate.PREFETCH_PERIODS[0],
                pacer=pacer,
            )

        self.assertEqual(result, (2, 2))
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(pacer.wait.call_args_list, [call(), call()])
        for fetch_call in fetch.call_args_list:
            self.assertNotIn("con", fetch_call.kwargs)
            self.assertTrue(fetch_call.kwargs["insert_into_database"])
            self.assertTrue(fetch_call.kwargs["force_update_database"])

    def test_prefetch_period_stops_after_first_failure(self):
        ranges = [("1953-01-01", "1953-12-31"), ("2023-01-01", "2026-12-31")]
        with patch(
            "prefetch_climate.missing_location_ranges", return_value=ranges
        ), patch("prefetch_climate.get_data", return_value=False) as fetch:
            result = prefetch_climate.prefetch_period(
                (2.0, 4.0), prefetch_climate.PREFETCH_PERIODS[0]
            )

        self.assertEqual(result, (0, 1))
        fetch.assert_called_once()

    def test_limit_is_bounded_to_provider_safe_batch(self):
        args = prefetch_climate.parse_args([])
        self.assertEqual(args.limit, 100)
        self.assertEqual(args.delay_seconds, 30)
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            prefetch_climate.parse_args(["--limit", "101"])
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            prefetch_climate.parse_args(["--delay-seconds", "-1"])


if __name__ == "__main__":
    unittest.main()
