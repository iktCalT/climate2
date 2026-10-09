"""Offline contract tests for one-sample NOAA location acquisition."""

from contextlib import nullcontext
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
import math
import unittest
from unittest.mock import Mock, patch

import numpy as np

from climate.providers.noaa_core import CoreDownloadError, NOAA_CORE_PROVIDER
from climate.services import location_fetch as fetch


SAMPLE = (2.0, 4.0)
MONTH = date(2026, 8, 1)


class Result:
    def __init__(self, row=None, rows=None):
        self.row, self.rows = row, rows

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows or []


class Connection:
    def __init__(self, *, lock=True, rows=(), job=None, limit=None, saved=None, worker_alive=False):
        self.lock, self.rows, self.job, self.limit, self.saved = lock, rows, job, limit, saved
        self.worker_alive = worker_alive
        self.queries = []
        self.closed = False
        self.lock_held = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        self.closed = True

    def transaction(self):
        return nullcontext()

    def execute(self, sql, params=()):
        self.queries.append((sql, params))
        if sql.startswith("SELECT pg_try_advisory_lock"):
            self.lock_held = self.lock
            return Result((self.lock,))
        if sql.startswith("SELECT pg_advisory_unlock"):
            self.lock_held = False
            return Result((True,))
        if sql.startswith("SELECT d.dates"):
            return Result(rows=self.rows)
        if sql.startswith("SELECT state,sample_lat"):
            return Result(self.job)
        if sql.startswith("SELECT EXISTS(SELECT 1 FROM pg_locks"):
            return Result((self.worker_alive,))
        if sql.startswith("SELECT window_start,starts"):
            return Result(self.limit)
        if sql.startswith("SELECT d.temp_mean"):
            return Result(self.saved)
        if sql.startswith("UPDATE climate_location_fetch_limit"):
            self.limit = params
        if sql.startswith("INSERT INTO climate_location_fetch_limit") and self.limit is None:
            self.limit = (params[0], 0)
        return Result()


def month_data(values=(10.0, 15.0, 5.0, 2.0)):
    grids = [np.full((91, 91), value) for value in values]
    return SimpleNamespace(month=MONTH, **dict(zip(fetch.FIELDS, grids)))


class LocationFetchTests(unittest.TestCase):
    def test_settings_validate_every_bounded_option_and_disabled_state(self):
        defaults = fetch.settings({})
        self.assertEqual((defaults["hourly_limit"], defaults["max_requests"],
                          defaults["max_bytes"], defaults["max_seconds"]),
                         (12, 192, 512 * 1024 * 1024, 900))
        self.assertFalse(fetch.settings({"LOCATION_FETCH_ENABLED": "0"})["enabled"])
        for name, invalid in {
            "ENABLED": ["true", "2"], "HOURLY_LIMIT": ["0", "61", "1.5", "-1"],
            "MAX_REQUESTS": ["31", "513"], "MAX_MIB": ["31", "1025"],
            "MAX_SECONDS": ["59", "1801"],
        }.items():
            for value in invalid:
                with self.subTest(name=name, value=value), self.assertRaises(fetch.FetchUnavailable):
                    fetch.settings({"LOCATION_FETCH_" + name: value})

    def test_coverage_counts_only_four_finite_fields_within_completed_window(self):
        con = Connection(rows=[
            (date(1951, 1, 1), 10., 12., 8., 1.),
            (date(1951, 2, 1), 10., None, 8., 1.),
            (date(1951, 3, 1), 10., math.nan, 8., 1.),
            (date(1951, 4, 1), 10., 12., 8., 1.),
            (date(1950, 12, 1), 10., 12., 8., 1.),
        ])
        complete, total, missing = fetch._coverage(con, SAMPLE, date(1951, 4, 15))
        self.assertEqual((complete, total, missing),
                         (1, 3, [date(1951, 2, 1), date(1951, 3, 1)]))
        self.assertEqual(con.queries[0][1], (*SAMPLE, NOAA_CORE_PROVIDER,
                                              date(1951, 1, 1), date(1951, 3, 1)))

    def test_complete_cache_never_starts_provider_or_consumes_allowance(self):
        con = Connection()
        with patch.object(fetch, "_connect", return_value=con), \
             patch.object(fetch, "_coverage", return_value=(4, 4, [])), \
             patch.object(fetch, "Thread") as thread:
            result = fetch.start(*SAMPLE, {})
        self.assertEqual((result["state"], result["complete"], result["remaining"]), ("done", 4, 0))
        self.assertTrue(con.closed)
        self.assertFalse(any("climate_location_fetch_limit" in sql for sql, _ in con.queries))
        thread.assert_not_called()

    def test_one_recent_missing_month_is_queued_and_limit_is_durable(self):
        con = Connection()
        missing = [date(1951, 1, 1), MONTH]
        with patch.object(fetch, "_connect", return_value=con), \
             patch.object(fetch, "_coverage", return_value=(2, 4, missing)), \
             patch.object(fetch, "status", return_value={"state": "running", "remaining": 2}), \
             patch.object(fetch, "Thread") as thread:
            result = fetch.start(*SAMPLE, {})
        self.assertEqual((result["state"], result["month"]), ("running", "2026-08"))
        self.assertEqual(con.limit[1], 1)
        self.assertFalse(con.closed)  # handed to worker
        self.assertTrue(any(sql.startswith("INSERT INTO climate_location_fetch_job") and params[-1] == MONTH
                            for sql, params in con.queries))
        thread.return_value.start.assert_called_once()

    def test_second_sample_replaces_singleton_only_after_first_worker_releases_lock(self):
        first, second = Connection(), Connection()
        other_sample = (-2.0, 8.0)
        with patch.object(fetch, "_connect", side_effect=[first, second]), \
             patch.object(fetch, "_coverage", side_effect=[(0, 1, [MONTH]), (0, 1, [MONTH])]), \
             patch.object(fetch, "status", return_value={"state": "running"}), \
             patch.object(fetch, "Thread") as thread:
            fetch.start(*SAMPLE, {})
            # A completed worker closes the PG session and releases its advisory lock.
            first.close()
            fetch.start(*other_sample, {})
        jobs = [(sql, params) for con in (first, second) for sql, params in con.queries
                if sql.startswith("INSERT INTO climate_location_fetch_job")]
        self.assertEqual(len(jobs), 2)
        self.assertTrue(all("VALUES(1,'running'" in sql and "ON CONFLICT(id) DO UPDATE" in sql
                            for sql, _ in jobs))
        self.assertEqual([params[:2] for _, params in jobs], [SAMPLE, other_sample])
        locks = [params for con in (first, second) for sql, params in con.queries
                 if sql.startswith("SELECT pg_try_advisory_lock")]
        self.assertEqual(locks, [(fetch.LOCK_ID,), (fetch.LOCK_ID,)])
        self.assertEqual(thread.call_count, 2)
        self.assertFalse(second.closed)

    def test_hourly_limit_returns_counts_without_worker_and_closes_connection(self):
        con = Connection(limit=(datetime.now(timezone.utc), 12))
        with patch.object(fetch, "_connect", return_value=con), \
             patch.object(fetch, "_coverage", return_value=(2, 4, [MONTH])), \
             patch.object(fetch, "Thread") as thread:
            result = fetch.start(*SAMPLE, {})
        self.assertEqual((result["state"], result["complete"], result["total"], result["remaining"]),
                         ("throttled", 2, 4, 1))
        self.assertGreater(result["retry_seconds"], 0)
        self.assertTrue(con.closed)
        thread.assert_not_called()

    def test_shared_admin_lock_prevents_duplicate_start_and_releases_connection(self):
        con = Connection(lock=False)
        with patch.object(fetch, "_connect", return_value=con), \
             patch.object(fetch, "status", return_value={"state": "busy", "remaining": 2}) as status, \
             patch.object(fetch, "_coverage", side_effect=AssertionError("coverage under busy lock")), \
             patch.object(fetch, "Thread") as thread:
            result = fetch.start(*SAMPLE, {})
        self.assertEqual(result["state"], "busy")
        status.assert_called_once()
        thread.assert_not_called()
        self.assertTrue(con.closed)

    def test_status_distinguishes_running_complete_interrupted_and_throttle(self):
        now = datetime.now(timezone.utc)
        cases = [
            (Connection(lock=False, job=("running", *SAMPLE, MONTH, 42), worker_alive=True), "running"),
            (Connection(job=("running", *SAMPLE, MONTH, 42)), "interrupted"),
            (Connection(job=("complete", *SAMPLE, MONTH, 42)), "complete"),
            (Connection(limit=(now, 12)), "throttled"),
        ]
        for con, expected in cases:
            with self.subTest(expected=expected), patch.object(fetch, "_connect", return_value=con), \
                 patch.object(fetch, "_coverage", return_value=(2, 4, [MONTH])):
                result = fetch.status(*SAMPLE, {})
            self.assertEqual(result["state"], expected)
            self.assertEqual((result["complete"], result["total"], result["remaining"]), (2, 4, 1))
            self.assertTrue(con.closed)

    def test_final_month_done_overrides_stale_job_and_disabled_never_connects(self):
        con = Connection(job=("failed", *SAMPLE, MONTH, 42),
                         limit=(datetime.now(timezone.utc), 12))
        with patch.object(fetch, "_connect", return_value=con), \
             patch.object(fetch, "_coverage", return_value=(3, 3, [])):
            result = fetch.status(*SAMPLE, {})
        self.assertEqual((result["state"], result["complete"], result["total"], result["remaining"]),
                         ("done", 3, 3, 0))
        with patch.object(fetch, "_connect", side_effect=AssertionError("database access")):
            self.assertEqual(fetch.status(*SAMPLE, {"LOCATION_FETCH_ENABLED": "0"})["state"], "disabled")
            self.assertEqual(fetch.start(*SAMPLE, {"LOCATION_FETCH_ENABLED": "0"})["state"], "disabled")

    def test_worker_records_success_or_failure_and_always_closes_connection(self):
        for failure in (False, True):
            con = Connection()
            archive = SimpleNamespace(deadline=float("inf"))
            loader = Mock(side_effect=CoreDownloadError("offline") if failure else None,
                          return_value=month_data())
            with self.subTest(failure=failure), patch.object(fetch, "BoundedArchiveClient", return_value=archive), \
                 patch.object(fetch, "load_core_month", loader), \
                 patch.object(fetch, "_store_sample") as store:
                fetch._worker(con, SAMPLE, MONTH, fetch.settings({}))
            self.assertTrue(con.closed)
            marker = "state='failed'" if failure else "state='complete'"
            self.assertTrue(any(marker in sql
                                for sql, _ in con.queries))
            if failure:
                store.assert_not_called()
            else:
                store.assert_called_once()

    def test_saved_finite_values_are_preserved_then_combined_row_validated(self):
        con = Connection(saved=(11., None, 3., 1.))
        fetch._store_sample(con, SAMPLE, month_data())
        upsert = [params for sql, params in con.queries if sql.startswith("INSERT INTO data")][0]
        self.assertEqual(upsert[:6], (MONTH, NOAA_CORE_PROVIDER, 11., 15., 3., 1.))
        self.assertEqual(upsert[-2:], SAMPLE)
        self.assertEqual(sum(sql.startswith("INSERT INTO data") for sql, _ in con.queries), 1)

        invalid = Connection(saved=(90., None, 3., 1.))
        with self.assertRaisesRegex(ValueError, "validation"):
            fetch._store_sample(invalid, SAMPLE, month_data())
        self.assertFalse(any(sql.startswith("INSERT INTO data") for sql, _ in invalid.queries))

    def test_bounded_client_stops_request_and_byte_budgets(self):
        options = fetch.settings({"LOCATION_FETCH_MAX_REQUESTS": "32", "LOCATION_FETCH_MAX_MIB": "32"})
        client = fetch.BoundedArchiveClient(options)
        client.requests_left = 0
        with self.assertRaises(CoreDownloadError):
            client._download("https://example.invalid/data", byte_range=(0, 3))
        client.requests_left = 1
        client.bytes_left = 4
        with patch.object(fetch.CoreArchiveClient, "_download", return_value=b"four") as download:
            self.assertEqual(client._download("https://example.invalid/data", byte_range=(0, 3)), b"four")
        self.assertEqual((client.requests_left, client.bytes_left), (0, 0))
        download.assert_called_once()
        client.requests_left = 1
        client.bytes_left = 3
        with self.assertRaises(CoreDownloadError):
            client._download("https://example.invalid/data", byte_range=(0, 3))

    def test_stream_deadline_tightens_each_read_and_charges_failed_transfer(self):
        clock = [0.0]
        class Socket:
            timeouts = []
            def settimeout(self, value):
                self.timeouts.append(value)
        class Response:
            status = 206
            fp = SimpleNamespace(raw=SimpleNamespace(_sock=Socket()))
            reads = 0
            def getcode(self): return self.status
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read1(self, size):
                self.reads += 1
                self.last_size = size
                clock[0] += 31.0
                return b"x"
        response = Response()
        with patch.object(fetch.time, "monotonic", side_effect=lambda: clock[0]), \
             patch("climate.providers.noaa_core.urlopen", return_value=response):
            client = fetch.BoundedArchiveClient(fetch.settings({"LOCATION_FETCH_MAX_SECONDS": "60"}))
            client.bytes_left = 10
            with self.assertRaisesRegex(CoreDownloadError, "time budget"):
                client._download("https://example.invalid/range", byte_range=(0, 4))
        self.assertEqual(response.reads, 2)
        self.assertEqual(response.fp.raw._sock.timeouts, [30.0, 29.0])
        self.assertEqual(client.requests_left, 191)
        self.assertEqual(client.bytes_left, 9)

    def test_incomplete_range_charges_bytes_and_oversize_stream_is_rejected(self):
        class Socket:
            def settimeout(self, value): pass
        class Response:
            status = 206
            fp = SimpleNamespace(raw=SimpleNamespace(_sock=Socket()))
            def __init__(self, chunks): self.chunks = iter(chunks)
            def getcode(self): return self.status
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read1(self, size): return next(self.chunks)
        client = fetch.BoundedArchiveClient(fetch.settings({}))
        client.bytes_left = 10
        with patch("climate.providers.noaa_core.urlopen", return_value=Response([b"ab", b""])):
            with self.assertRaisesRegex(CoreDownloadError, "incomplete byte range"):
                client._download("https://example.invalid/range", byte_range=(0, 4))
        self.assertEqual((client.bytes_left, client.requests_left), (8, 191))
        client.bytes_left = 5
        with patch("climate.providers.noaa_core.urlopen", return_value=Response([b"abcdef"])):
            with self.assertRaisesRegex(CoreDownloadError, "byte budget"):
                client._download("https://example.invalid/range", byte_range=(0, 4))
        self.assertEqual(client.requests_left, 190)


if __name__ == "__main__":
    unittest.main()
