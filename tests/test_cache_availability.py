from contextlib import contextmanager
from datetime import date
import os
import unittest
from unittest.mock import MagicMock, patch

from cache_availability import saved_map_months
from db import ACTIVE_CLIMATE_PROVIDER, CLIMATE_TYPES, database_url


class AvailabilityTests(unittest.TestCase):
    def test_read_only_bounded_provider_scoped_query(self):
        db = MagicMock()
        cursor = db.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(date(2026, 8, 1), 8, 7, 6, 5)]
        with patch("cache_availability.weather_db", return_value=db):
            result = saved_map_months("1950-01", "2026-09")
        self.assertEqual(result, [{"month": "2026-08", "counts": dict(zip(CLIMATE_TYPES, [8, 7, 6, 5]))}])
        cursor.execute.assert_any_call("SET TRANSACTION READ ONLY")
        cursor.execute.assert_any_call("SET LOCAL statement_timeout = '3s'")
        self.assertEqual(cursor.execute.call_args.args[1], (ACTIVE_CLIMATE_PROVIDER, "1950-01-01", "2026-09-01"))


@unittest.skipUnless(os.environ.get("CLIMATE_AVAILABILITY_PG_TEST") == "1", "opt-in temporary PostgreSQL table")
class AvailabilityPostgresTests(unittest.TestCase):
    def test_actual_counts_exclude_inactive_null_nonfinite_and_nonmonthly_rows(self):
        import psycopg
        with psycopg.connect(database_url(), autocommit=True) as con:
            con.execute("CREATE TEMP TABLE data (dates DATE, provider TEXT, temp_mean FLOAT8, temp_max FLOAT8, temp_min FLOAT8, precip FLOAT8)")
            self.assertTrue(con.execute("SELECT relnamespace=pg_my_temp_schema() FROM pg_class WHERE oid='data'::regclass").fetchone()[0])
            rows = [
                ('2026-08-01', ACTIVE_CLIMATE_PROVIDER, 20, 30, 10, 2),
                ('2026-08-01', ACTIVE_CLIMATE_PROVIDER, None, 31, None, 3),
                ('2026-09-01', ACTIVE_CLIMATE_PROVIDER, None, None, None, 4),
                ('1950-01-01', ACTIVE_CLIMATE_PROVIDER, -10, None, None, None),
                ('2026-07-01', ACTIVE_CLIMATE_PROVIDER, float('nan'), float('inf'), float('-inf'), None),
                ('2026-06-01', 'noaa_core', 20, 30, 10, 2),
                ('2026-05-02', ACTIVE_CLIMATE_PROVIDER, 20, 30, 10, 2),
                ('1949-12-01', ACTIVE_CLIMATE_PROVIDER, 20, 30, 10, 2),
                ('2026-10-01', ACTIVE_CLIMATE_PROVIDER, 20, 30, 10, 2),
            ]
            with con.cursor() as cur:
                cur.executemany("INSERT INTO data VALUES (%s,%s,%s,%s,%s,%s)", rows)

            @contextmanager
            def temporary_db():
                with con.transaction():
                    yield con

            with patch("cache_availability.weather_db", temporary_db):
                result = saved_map_months("1950-01", "2026-09")
                self.assertEqual([row['month'] for row in result], ['2026-09', '2026-08', '1950-01'])
                self.assertEqual(result[1]['counts'], dict(temp_mean=1, temp_max=2, temp_min=1, precip=2))
                con.execute("DELETE FROM pg_temp.data")
                self.assertEqual(saved_map_months("1950-01", "2026-09"), [])
