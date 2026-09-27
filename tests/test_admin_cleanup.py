"""Unit checks plus opt-in PostgreSQL tests using only connection-local tables."""

import os
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import climate.services.admin_cleanup as service


class CleanupServiceTests(unittest.TestCase):
    def test_preview_only_counts(self):
        con = MagicMock()
        con.__enter__.return_value = con
        con.execute.return_value.fetchall.return_value = [("example", 10, 20)]
        with patch.object(service, "_connect", return_value=con):
            result = service.cleanup_preview()
        self.assertEqual(result["removable"], 20)
        self.assertEqual(result["providers"][0]["kept"], 10)
        self.assertFalse(any("DELETE" in call.args[0] for call in con.execute.call_args_list))

    def test_busy_import_prevents_deletion(self):
        con = MagicMock()
        con.__enter__.return_value = con
        con.execute.return_value.fetchone.return_value = (False,)
        with patch.object(service, "_connect", return_value=con):
            with self.assertRaises(service.ImportBusy):
                service.cleanup_batch()
        self.assertFalse(any("DELETE" in call.args[0] for call in con.execute.call_args_list))
        self.assertIs(con.transaction.return_value.__exit__.call_args.args[0], service.ImportBusy)

    def test_deletion_is_bounded_and_transactional(self):
        con = MagicMock()
        con.__enter__.return_value = con
        con.execute.return_value.fetchone.return_value = (True,)
        con.execute.return_value.rowcount = 42
        with patch.object(service, "_connect", return_value=con):
            self.assertEqual(service.cleanup_batch()["deleted"], 42)
        query, args = con.execute.call_args.args
        self.assertEqual(args, (50_000,))
        self.assertIn(service.OUTSIDE_WINDOWS, query)
        self.assertIn("FOR UPDATE", query)
        con.transaction.return_value.__exit__.assert_called_once_with(None, None, None)


@unittest.skipUnless(os.environ.get("CLIMATE_CLEANUP_PG_TEST") == "1", "opt-in temporary PostgreSQL tables")
class CleanupPostgresTests(unittest.TestCase):
    def setUp(self):
        self.con = service._connect()
        self.con.execute("CREATE TEMP TABLE data (dates DATE NOT NULL, provider TEXT NOT NULL)")
        # Refuse to test unless unqualified data resolves to this session's temp table.
        self.assertTrue(self.con.execute(
            "SELECT relnamespace = pg_my_temp_schema() FROM pg_class WHERE oid = 'data'::regclass"
        ).fetchone()[0])
        dates = ['1949-12-31', '1950-01-01', '1954-12-31', '1955-01-01',
                 '2021-12-31', '2022-01-01', '2026-12-31', '2027-01-01']
        with self.con.cursor() as cur:
            cur.executemany("INSERT INTO data VALUES (%s,%s)",
                            [(date, provider) for date in dates for provider in ('noaa_core', 'open_meteo_cmip6')])

        @contextmanager
        def temporary_connection():
            yield self.con

        self.connection_patch = patch.object(service, "_connect", temporary_connection)
        self.connection_patch.start()

    def tearDown(self):
        self.connection_patch.stop()
        self.con.close()  # PostgreSQL discards only the session-local test table.

    def test_boundaries_all_providers_and_repeatable_batches(self):
        self.assertEqual(service.cleanup_preview()["removable"], 8)
        with patch.object(service, "MAX_CLEANUP_ROWS", 3):
            self.assertEqual(service.cleanup_batch()["deleted"], 3)
            self.assertEqual(service.cleanup_batch()["deleted"], 3)
            self.assertEqual(service.cleanup_batch()["deleted"], 2)
            self.assertEqual(service.cleanup_batch()["deleted"], 0)
        preview = service.cleanup_preview()
        self.assertEqual(preview["removable"], 0)
        self.assertEqual([row["kept"] for row in preview["providers"]], [4, 4])

    def test_failed_transaction_rolls_back_rows(self):
        with self.assertRaises(RuntimeError):
            with self.con.transaction():
                self.assertEqual(service.cleanup_batch()["deleted"], 8)
                raise RuntimeError("abort temporary fixture transaction")
        self.assertEqual(service.cleanup_preview()["removable"], 8)

    def test_import_session_lock_blocks_cleanup(self):
        from climate.data.db import database_url
        import psycopg
        with psycopg.connect(database_url(), autocommit=True) as other:
            other.execute("SELECT pg_advisory_lock(%s)", (service.LOCK_ID,))
            try:
                with self.assertRaises(service.ImportBusy):
                    service.cleanup_batch()
            finally:
                other.execute("SELECT pg_advisory_unlock(%s)", (service.LOCK_ID,))
        self.assertEqual(service.cleanup_preview()["removable"], 8)
