"""Offline regressions for acquisition identity under a NOAA public selector."""

from contextlib import contextmanager, redirect_stdout
from datetime import date
from io import StringIO
import sqlite3
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

import climate.data.cache_availability as availability
import climate.cli.compare_climate_providers as comparison
import climate.cli.migrate_weather_sqlite as migration
import climate.cli.prefetch_climate as prefetch
import climate.providers.open_meteo as meteo
import climate.services.map_data as maps
from climate.data.db import OPEN_METEO_PROVIDER
from climate.providers.noaa_core import NOAA_CORE_PROVIDER


class RecordingCursor:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def executemany(self, query, rows):
        self.calls.append((query, list(rows)))

    def fetchall(self):
        return self.rows


class RecordingConnection:
    def __init__(self, rows=()):
        self.recording = RecordingCursor(rows)
        self.calls = []

    def cursor(self):
        return self.recording

    def execute(self, query):
        self.calls.append(query)


class SplitSourceCursor(RecordingCursor):
    """A NOAA row exists; the corresponding CMIP6 month is still absent."""

    def fetchall(self):
        if self.calls[-1][1][-1] == NOAA_CORE_PROVIDER:
            return [(date(2020, 1, 1), 12.0, 14.0, 10.0, 1.0)]
        return []


@contextmanager
def connection_context(con):
    yield con


class ProviderIdentityTests(unittest.TestCase):
    def test_default_provider_reaches_history_map_and_saved_month_sql(self):
        from climate.data.db import ACTIVE_CLIMATE_PROVIDER

        self.assertEqual(ACTIVE_CLIMATE_PROVIDER, NOAA_CORE_PROVIDER)
        history_con = RecordingConnection()
        meteo.load_location_history(
            (1, 2), "2020-01-01", "2020-01-31", ("temp_mean",), con=history_con
        )
        self.assertEqual(history_con.recording.calls[0][1],
                         (1.0, 2.0, "2020-01-01", "2020-01-31", NOAA_CORE_PROVIDER))

        map_con = RecordingConnection()
        maps._query_weather_rows(map_con, "2020-01-01", "temp_mean", [0, 2], [0, 4])
        self.assertEqual(map_con.recording.calls[0][1][1], NOAA_CORE_PROVIDER)

        months_con = RecordingConnection()
        with patch.object(availability, "weather_db", return_value=connection_context(months_con)):
            self.assertEqual(availability.saved_map_months("2020-01", "2020-02"), [])
        saved_dates_query, saved_dates_params = months_con.recording.calls[-1]
        self.assertIn("WHERE provider = %s AND dates BETWEEN %s AND %s", saved_dates_query)
        self.assertEqual(saved_dates_params,
                         (NOAA_CORE_PROVIDER, "2020-01-01", "2020-02-01"))

    def test_normal_and_force_write_rows_keep_cmip6_identity(self):
        frame = pd.DataFrame(
            {"loc_id": [7], "temp_mean": [12.5]},
            index=pd.to_datetime(["2020-01-01"]),
        )
        con = RecordingConnection()
        with patch.object(meteo, "ACTIVE_CLIMATE_PROVIDER", NOAA_CORE_PROVIDER):
            self.assertTrue(meteo.modify_database(frame, type="insert", con=con))
            self.assertTrue(meteo.modify_database(frame, type="update", con=con))

        self.assertEqual(len(con.recording.calls), 2)
        for query, rows in con.recording.calls:
            self.assertIn("ON CONFLICT (loc_id, dates, provider)", query)
            self.assertEqual(rows[0][-1], OPEN_METEO_PROVIDER)
        self.assertIn("DO NOTHING", con.recording.calls[0][0])
        self.assertIn("DO UPDATE", con.recording.calls[1][0])

    def test_legacy_migration_writes_cmip6_rows(self):
        con = RecordingConnection()
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "legacy.db"
            source = sqlite3.connect(source_path)
            try:
                source.execute("CREATE TABLE locations (loc_id INTEGER, lat REAL, lon REAL)")
                source.execute("CREATE TABLE data (loc_id INTEGER, dates TEXT, temp_mean REAL, temp_max REAL, temp_min REAL, precip REAL)")
                source.execute("INSERT INTO locations VALUES (7, 1, 2)")
                source.execute("INSERT INTO data VALUES (7, '2020-01-01', 12, 14, 10, 1)")
                source.commit()
            finally:
                source.close()
            with patch.object(migration, "weather_db", return_value=connection_context(con)), patch(
                "climate.data.db.ACTIVE_CLIMATE_PROVIDER", NOAA_CORE_PROVIDER
            ):
                migration.migrate(source_path)

        writes = [(query, rows) for query, rows in con.recording.calls if "INSERT INTO data" in query]
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0][1][0][-1], OPEN_METEO_PROVIDER)

    def test_prefetch_checkpoints_and_gap_probe_use_cmip6(self):
        con = RecordingConnection()
        con.recording = SplitSourceCursor()
        with patch.object(prefetch, "weather_db", return_value=connection_context(con)), patch.object(
            meteo, "ACTIVE_CLIMATE_PROVIDER", NOAA_CORE_PROVIDER
        ):
            self.assertEqual(prefetch.load_period_completion(con), {})
            ranges = meteo.missing_location_ranges(
                (1, 2), "2020-01-01", "2020-01-31",
                fields=("temp_mean", "temp_max", "temp_min", "precip"), con=con
            )

        checkpoint_query, checkpoint_params = con.recording.calls[0]
        history_query, history_params = con.recording.calls[1]
        self.assertIn("d.provider = %s", checkpoint_query)
        self.assertEqual(checkpoint_params[-3], OPEN_METEO_PROVIDER)
        self.assertIn("d.provider = %s", history_query)
        self.assertEqual(history_params[-1], OPEN_METEO_PROVIDER)
        self.assertEqual(ranges, [("2020-01-01", "2020-01-31")])

    def test_source_specific_location_probes_ignore_noaa_rows(self):
        con = RecordingConnection()
        with patch.object(meteo, "ACTIVE_CLIMATE_PROVIDER", NOAA_CORE_PROVIDER):
            self.assertEqual(meteo.get_data_in_database(1, 2, con=con), [])
            self.assertEqual(meteo._locations_with_data(con), set())

        self.assertEqual(con.recording.calls[0][1][-1], OPEN_METEO_PROVIDER)
        self.assertEqual(con.recording.calls[1][1], (OPEN_METEO_PROVIDER,))

    def test_noaa_public_history_retains_gaps_without_open_meteo(self):
        con = RecordingConnection()
        with patch.object(meteo, "ACTIVE_CLIMATE_PROVIDER", NOAA_CORE_PROVIDER), patch.object(
            meteo, "get_data", side_effect=AssertionError("Open-Meteo contacted")
        ) as fetch:
            history, fetched = meteo.get_location_history(
                (1, 2), "2020-01-01", "2020-01-31", con=con, fetch_missing=True
            )

        self.assertFalse(fetched)
        self.assertTrue(pd.isna(history.loc["2020-01-01", "temp_mean"]))
        self.assertEqual(con.recording.calls[0][1][-1], NOAA_CORE_PROVIDER)
        fetch.assert_not_called()

    def test_map_public_query_selects_noaa_and_opt_in_fallback_stays_off(self):
        con = RecordingConnection()
        with patch.object(maps, "ACTIVE_CLIMATE_PROVIDER", NOAA_CORE_PROVIDER), patch.object(
            maps, "get_data", side_effect=AssertionError("Open-Meteo contacted")
        ) as fetch:
            maps._query_weather_rows(con, "2020-01-01", "temp_mean", [0, 2], [0, 4])
            self.assertEqual(maps._fetch_missing_cells(con, [{"latitude": 1, "longitude": 2}], "2020-01"), 0)

        self.assertEqual(con.recording.calls[0][1][1], NOAA_CORE_PROVIDER)
        fetch.assert_not_called()

    def test_comparison_reads_distinct_fixed_sources_under_noaa_selection(self):
        con = RecordingConnection()
        with patch.object(comparison, "weather_db", return_value=connection_context(con)), patch.object(
            comparison, "available_core_months", return_value=[date(2020, 1, 1)]
        ), patch.object(comparison, "load_rows", side_effect=[{}, {}]) as load, patch.object(
            comparison, "render_report", return_value="report\n"
        ), patch("climate.data.db.ACTIVE_CLIMATE_PROVIDER", NOAA_CORE_PROVIDER), redirect_stdout(StringIO()):
            self.assertEqual(comparison.run([date(2020, 1, 1)]), 0)

        self.assertEqual(con.calls, ["SET TRANSACTION READ ONLY"])
        self.assertEqual([call.args[1] for call in load.call_args_list], [NOAA_CORE_PROVIDER, OPEN_METEO_PROVIDER])


if __name__ == "__main__":
    unittest.main()
