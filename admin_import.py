"""Small administrator-started NOAA batches; PostgreSQL is the checkpoint.

The dedicated connection owns a session advisory lock until the background
thread exits. A server restart releases the lock; completed months survive.
No automatic scheduler or provider activation is involved.
"""

import logging
from datetime import date
from threading import Thread

import psycopg

from db import database_url
from import_noaa_core import last_complete_month, months_between
from noaa_core import (
    CoreArchiveClient, EccodesDecoder, completed_core_months,
    load_core_month, upsert_core_month,
)

logger = logging.getLogger(__name__)
LOCK_ID = 19502026
MAX_BATCH_MONTHS = 12
WINDOWS = {
    "first": ("First five years · 1950–1954", date(1950, 1, 1), date(1954, 12, 1)),
    "last": ("Last five years · 2022–2026", date(2022, 1, 1), date(2026, 12, 1)),
}


class ImportBusy(Exception):
    pass


def window_months(window, today=None):
    if window not in WINDOWS:
        raise ValueError("Choose one of the two five-year windows.")
    _, start, end = WINDOWS[window]
    months = months_between(start, min(end, last_complete_month(today)))
    return list(reversed(months)) if window == "last" else months


def _connect():
    return psycopg.connect(database_url(), autocommit=True)


def import_status():
    """No provider requests. Coverage comes from validated monthly DB rows."""
    with _connect() as con:
        row = con.execute(
            "SELECT window_name, state, processed, total, current_month "
            "FROM climate_import_job WHERE id = 1"
        ).fetchone()
        available = con.execute("SELECT pg_try_advisory_lock(%s)", (LOCK_ID,)).fetchone()[0]
        if available:
            con.execute("SELECT pg_advisory_unlock(%s)", (LOCK_ID,))
        windows = []
        for key, (label, _, _) in WINDOWS.items():
            months = window_months(key)
            complete = completed_core_months(con, months)
            pending = [month for month in months if month not in complete]
            windows.append({
                "id": key, "label": label, "complete": len(complete),
                "total": len(months), "next": pending[0].strftime("%Y-%m") if pending else None,
            })
    job = None
    if row:
        window, state, processed, total, month = row
        if state == "running" and available:
            state = "interrupted"
        job = {"window": window, "state": state, "processed": processed,
               "total": total, "month": month.strftime("%Y-%m") if month else None}
    return {"running": not available, "windows": windows, "job": job}


def _progress(con, state, processed, month=None):
    con.execute(
        "UPDATE climate_import_job SET state=%s, processed=%s, current_month=%s, "
        "updated_at=CURRENT_TIMESTAMP WHERE id=1", (state, processed, month),
    )


def fetch_month_batch(con, months):
    """Fetch only the already-selected bounded batch, fail closed, release lock."""
    processed = 0
    try:
        archive, decoder = CoreArchiveClient(), EccodesDecoder()
        for month in months:
            # Detect a lost lock connection before downloading or committing.
            _progress(con, "running", processed, month)
            data = load_core_month(month, archive=archive, decoder=decoder)
            _progress(con, "running", processed, month)
            # Use the lock connection for the atomic write as well.
            with con.transaction():
                upsert_core_month(data, con=con)
            processed += 1
            _progress(con, "running", processed, month)
        _progress(con, "complete", processed)
    except Exception:
        logger.exception("Administrator NOAA batch failed; committed months remain resumable")
        try:
            _progress(con, "failed", processed)
        except Exception:
            logger.warning("Could not persist job status; next status check will report interruption")
    finally:
        con.close()  # Releases the session lock, including on failure.


def start_import(window, limit=1):
    """Start one bounded background batch; never accept arbitrary dates or URLs."""
    months = window_months(window)
    if type(limit) is not int or not 1 <= limit <= MAX_BATCH_MONTHS:
        raise ValueError("Choose between 1 and 12 months per batch.")
    con = _connect()
    handed_off = False
    try:
        if not con.execute("SELECT pg_try_advisory_lock(%s)", (LOCK_ID,)).fetchone()[0]:
            raise ImportBusy("A NOAA batch is already running. Wait for it to finish.")
        completed = completed_core_months(con, months)
        pending = [month for month in months if month not in completed][:limit]
        if not pending:
            return {"started": False, "message": "This window is already complete."}
        con.execute(
            "INSERT INTO climate_import_job (id,window_name,state,processed,total,current_month) "
            "VALUES (1,%s,'running',0,%s,%s) ON CONFLICT (id) DO UPDATE SET "
            "window_name=EXCLUDED.window_name,state='running',processed=0,"
            "total=EXCLUDED.total,current_month=EXCLUDED.current_month,updated_at=CURRENT_TIMESTAMP",
            (window, len(pending), pending[0]),
        )
        Thread(target=fetch_month_batch, args=(con, pending), daemon=True).start()
        handed_off = True
        return {"started": True, "message": f"Started a {len(pending)}-month batch."}
    finally:
        if not handed_off:
            con.close()
