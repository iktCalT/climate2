from datetime import date
from unittest import TestCase
from unittest.mock import MagicMock, patch

import admin_import as service


class AdminImportServiceTests(TestCase):
    def test_five_year_windows_and_current_month_cap(self):
        first = service.window_months("first", date(2026, 9, 26))
        last = service.window_months("last", date(2026, 9, 26))
        self.assertEqual((first[0], first[-1], len(first)),
                         (date(1950, 1, 1), date(1954, 12, 1), 60))
        self.assertEqual((last[0], last[-1], len(last)),
                         (date(2026, 8, 1), date(2022, 1, 1), 56))
        self.assertEqual(service.window_months("last", date(2028, 1, 1))[0], date(2026, 12, 1))

    def test_invalid_input_never_opens_database(self):
        with patch.object(service, "_connect") as connect:
            for window, limit in [("all", 1), ("first", 0), ("last", 13), ("first", True), ("last", 1.5)]:
                with self.assertRaises(ValueError):
                    service.start_import(window, limit)
            connect.assert_not_called()

    def test_busy_lock_rejects_duplicate_start_and_closes_connection(self):
        con = MagicMock()
        con.execute.return_value.fetchone.return_value = (False,)
        with patch.object(service, "_connect", return_value=con), patch.object(service, "Thread") as thread:
            with self.assertRaises(service.ImportBusy):
                service.start_import("first")
            thread.assert_not_called()
        con.close.assert_called_once()

    def test_start_skips_complete_months_then_limits_and_hands_off_connection(self):
        con = MagicMock()
        con.execute.return_value.fetchone.return_value = (True,)
        months = [date(1950, month, 1) for month in (1, 2, 3)]
        with (patch.object(service, "_connect", return_value=con),
              patch.object(service, "window_months", return_value=months),
              patch.object(service, "completed_core_months", return_value={months[0]}),
              patch.object(service, "Thread") as thread):
            self.assertTrue(service.start_import("first", 1)["started"])
            self.assertEqual(thread.call_args.kwargs["args"], (con, [months[1]]))
            thread.return_value.start.assert_called_once()
        con.close.assert_not_called()

    def test_complete_window_does_not_launch_thread(self):
        con = MagicMock()
        con.execute.return_value.fetchone.return_value = (True,)
        months = [date(1950, 1, 1)]
        with (patch.object(service, "_connect", return_value=con),
              patch.object(service, "window_months", return_value=months),
              patch.object(service, "completed_core_months", return_value=set(months)),
              patch.object(service, "Thread") as thread):
            self.assertFalse(service.start_import("first")["started"])
            thread.assert_not_called()
        con.close.assert_called_once()

    def test_thread_launch_failure_releases_lock(self):
        con = MagicMock()
        con.execute.return_value.fetchone.return_value = (True,)
        with (patch.object(service, "_connect", return_value=con),
              patch.object(service, "completed_core_months", return_value=set()),
              patch.object(service, "Thread") as thread):
            thread.return_value.start.side_effect = RuntimeError("cannot start")
            with self.assertRaises(RuntimeError):
                service.start_import("first")
        con.close.assert_called_once()

    def test_worker_failure_preserves_first_month_and_stops(self):
        con = MagicMock()
        months = [date(1950, month, 1) for month in (1, 2, 3)]
        data = object()
        with (patch.object(service, "CoreArchiveClient"), patch.object(service, "EccodesDecoder"),
              patch.object(service, "load_core_month", side_effect=[data, RuntimeError("failed")]) as load,
              patch.object(service, "upsert_core_month") as save,
              patch.object(service, "_progress") as progress,
              self.assertLogs(service.logger, level="ERROR")):
            service.fetch_month_batch(con, months)
        save.assert_called_once_with(data, con=con)
        self.assertEqual(load.call_count, 2)
        self.assertEqual(con.transaction.call_count, 1)
        progress.assert_any_call(con, "failed", 1)
        con.close.assert_called_once()

    def test_worker_completes_and_uses_same_lock_connection(self):
        con = MagicMock()
        with (patch.object(service, "CoreArchiveClient"), patch.object(service, "EccodesDecoder"),
              patch.object(service, "load_core_month", return_value="validated") as load,
              patch.object(service, "upsert_core_month") as save,
              patch.object(service, "_progress") as progress):
            service.fetch_month_batch(con, [date(1950, 1, 1)])
        save.assert_called_once_with("validated", con=con)
        progress.assert_any_call(con, "complete", 1)
        con.close.assert_called_once()

    def test_status_detects_interruption_without_downloading(self):
        con = MagicMock()
        con.__enter__.return_value = con
        con.execute.return_value.fetchone.side_effect = [
            ("first", "running", 1, 2, date(1950, 2, 1)), (True,),
        ]
        with (patch.object(service, "_connect", return_value=con),
              patch.object(service, "completed_core_months", return_value=set()),
              patch.object(service, "CoreArchiveClient") as archive):
            status = service.import_status()
        self.assertFalse(status["running"])
        self.assertEqual(status["job"]["state"], "interrupted")
        archive.assert_not_called()
