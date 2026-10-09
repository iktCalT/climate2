"""Bounded, anonymous NOAA history acquisition for one canonical sample/month."""

from datetime import date, datetime, timedelta, timezone
import logging
import math
import os
import re
import time
from threading import Thread

import psycopg

from climate.data.db import database_url
from climate.data.location_sampling import sample_noaa_location
from climate.data.months import last_complete_month, months_between
from climate.providers.noaa_core import (
    CoreArchiveClient, CoreDownloadError, NOAA_CORE_PROVIDER, load_core_month,
)
from climate.services.admin_import import LOCK_ID

logger = logging.getLogger(__name__)
FIRST_MONTH = date(1951, 1, 1)
FIELDS = ("temp_mean", "temp_max", "temp_min", "precip")


class FetchUnavailable(Exception):
    """A validated setting or runtime precondition prevents acquisition."""


def settings(config):
    enabled = config.get("LOCATION_FETCH_ENABLED", "1")
    if enabled not in ("0", "1"):
        raise FetchUnavailable("Invalid Location fetch setting")

    def number(name, default, low, high):
        raw = str(config.get(name, default))
        if not re.fullmatch(r"[0-9]+", raw) or not low <= int(raw) <= high:
            raise FetchUnavailable("Invalid Location fetch setting")
        return int(raw)

    return {
        "enabled": enabled == "1",
        "hourly_limit": number("LOCATION_FETCH_HOURLY_LIMIT", 12, 1, 60),
        "max_requests": number("LOCATION_FETCH_MAX_REQUESTS", 192, 32, 512),
        "max_bytes": number("LOCATION_FETCH_MAX_MIB", 512, 32, 1024) * 1024 * 1024,
        "max_seconds": number("LOCATION_FETCH_MAX_SECONDS", 900, 60, 1800),
    }


class BoundedArchiveClient(CoreArchiveClient):
    """Cap all selected-record downloads in one month, including indexes."""

    def __init__(self, options):
        super().__init__(timeout_seconds=30, retries=1)
        self.deadline = time.monotonic() + options["max_seconds"]
        self.requests_left = options["max_requests"]
        self.bytes_left = options["max_bytes"]

    def _download(self, url, byte_range=None, maximum_bytes=None):
        remaining = self.deadline - time.monotonic()
        expected = (byte_range[1] - byte_range[0] + 1) if byte_range else maximum_bytes
        if remaining <= 0 or self.requests_left <= 0 or (expected and expected > self.bytes_left):
            raise CoreDownloadError("Location download budget exhausted")
        self.requests_left -= 1
        self.timeout_seconds = min(30.0, remaining)
        budget_before = self.bytes_left
        payload = super()._download(url, byte_range=byte_range, maximum_bytes=maximum_bytes)
        if self.bytes_left == budget_before:
            # The normal response hook charges chunks as read. Also account for
            # clients that override the parent's downloader (offline fakes).
            if len(payload) > self.bytes_left:
                raise CoreDownloadError("Location download byte budget exhausted")
            self.bytes_left -= len(payload)
        return payload

    def _read_response(self, response, maximum_bytes):
        """Check wall clock between single-recv chunks and tighten socket timeout."""
        if maximum_bytes is None or not callable(getattr(response, "read1", None)):
            raise CoreDownloadError("Location response cannot be bounded")
        payload = bytearray()
        while True:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise CoreDownloadError("Location download time budget exhausted")
            socket = getattr(getattr(getattr(response, "fp", None), "raw", None), "_sock", None)
            if socket is None or not callable(getattr(socket, "settimeout", None)):
                if callable(getattr(response, "isclosed", None)) and response.isclosed():
                    return bytes(payload)
                raise CoreDownloadError("Location response socket cannot be bounded")
            socket.settimeout(min(30.0, remaining))
            size = min(64 * 1024, maximum_bytes + 1 - len(payload), self.bytes_left + 1)
            if size <= 0:
                raise CoreDownloadError("Location download byte budget exhausted")
            chunk = response.read1(size)
            if time.monotonic() > self.deadline:
                raise CoreDownloadError("Location download time budget exhausted")
            if not chunk:
                return bytes(payload)
            if len(chunk) > self.bytes_left:
                raise CoreDownloadError("Location download byte budget exhausted")
            self.bytes_left -= len(chunk)
            payload.extend(chunk)
            if len(payload) > maximum_bytes:
                raise CoreDownloadError("Location response exceeded its expected size")


def _connect():
    return psycopg.connect(database_url(), autocommit=True)


def _sample(latitude, longitude):
    if any(isinstance(value, str) and len(value) > 32 for value in (latitude, longitude)):
        raise ValueError("Invalid latitude/longitude")
    sample = sample_noaa_location(latitude, longitude)
    return sample.latitude, sample.longitude


def _coverage(con, sample, today=None):
    final = last_complete_month(today)
    months = months_between(FIRST_MONTH, final) if final >= FIRST_MONTH else []
    rows = con.execute(
        "SELECT d.dates,d.temp_mean,d.temp_max,d.temp_min,d.precip FROM data d "
        "JOIN locations l ON l.loc_id=d.loc_id WHERE l.lat=%s AND l.lon=%s "
        "AND d.provider=%s AND d.dates BETWEEN %s AND %s",
        (*sample, NOAA_CORE_PROVIDER, FIRST_MONTH, final),
    ).fetchall()
    expected = set(months)
    complete = {row[0] for row in rows if row[0] in expected and all(
        value is not None and math.isfinite(value) for value in row[1:]
    )}
    missing = [month for month in months if month not in complete]
    return len(complete), len(months), missing


def _lock_available(con):
    available = con.execute("SELECT pg_try_advisory_lock(%s)", (LOCK_ID,)).fetchone()[0]
    if available:
        con.execute("SELECT pg_advisory_unlock(%s)", (LOCK_ID,))
    return available


def status(latitude, longitude, config):
    sample = _sample(latitude, longitude)
    options = settings(config)
    if not options["enabled"]:
        return {"state": "disabled", "complete": 0, "total": 0,
                "remaining": 0, "month": None, "retry_seconds": 0,
                "sample": {"latitude": sample[0], "longitude": sample[1]}}
    with _connect() as con:
        complete, total, missing = _coverage(con, sample)
        row = con.execute(
            "SELECT state,sample_lat,sample_lon,current_month,backend_pid "
            "FROM climate_location_fetch_job WHERE id=1"
        ).fetchone()
        available = _lock_available(con)
        worker_alive = bool(row and row[4] and con.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s "
            "AND locktype='advisory' AND granted)", (row[4],)
        ).fetchone()[0])
        limit = con.execute(
            "SELECT window_start,starts FROM climate_location_fetch_limit WHERE id=1"
        ).fetchone()
    active_here = bool(row and row[0] == "running" and worker_alive
                       and not available and (row[1], row[2]) == sample)
    active_elsewhere = not available and not active_here
    state = "done" if not missing else "ready"
    if not missing:
        state = "done"
    elif active_here:
        state = "running"
    elif row and (row[1], row[2]) == sample and row[0] == "complete":
        state = "complete"
    elif active_elsewhere:
        state = "busy"
    elif row and (row[1], row[2]) == sample:
        state = "interrupted" if row[0] == "running" else row[0]
    now = datetime.now(timezone.utc)
    used = limit[1] if limit and now - limit[0] < timedelta(hours=1) else 0
    retry_seconds = max(0, int(3600 - (now - limit[0]).total_seconds()) + 1) if used >= options["hourly_limit"] else 0
    if state == "ready" and retry_seconds:
        state = "throttled"
    return {
        "state": state, "sample": {"latitude": sample[0], "longitude": sample[1]},
        "complete": complete, "total": total, "remaining": len(missing),
        "month": row[3].strftime("%Y-%m") if active_here else None,
        "retry_seconds": retry_seconds,
    }


def _valid_final(values):
    mean, maximum, minimum, precip = values
    if not all(math.isfinite(value) for value in values):
        return False
    return (all(-150 <= value <= 100 for value in (mean, maximum, minimum))
            and 0 <= precip <= 5000 and minimum <= maximum and minimum <= mean + 0.1
            and maximum >= mean - 0.1)


def _store_sample(con, sample, month_data):
    lat, lon = sample
    lat_index = round((lat + 90) / 2)
    lon_index = round((lon + 180) / 4)
    incoming = tuple(float(getattr(month_data, name)[lat_index, lon_index]) for name in FIELDS)
    with con.transaction():
        con.execute(
            "INSERT INTO locations(lat,lon) VALUES (%s,%s) ON CONFLICT(lat,lon) DO NOTHING",
            sample,
        )
        row = con.execute(
            "SELECT d.temp_mean,d.temp_max,d.temp_min,d.precip FROM data d "
            "JOIN locations l ON l.loc_id=d.loc_id WHERE l.lat=%s AND l.lon=%s "
            "AND d.dates=%s AND d.provider=%s FOR UPDATE OF d",
            (*sample, month_data.month, NOAA_CORE_PROVIDER),
        ).fetchone()
        values = tuple(old if old is not None and math.isfinite(old) else new
                       for old, new in zip(row or (None,) * 4, incoming))
        if not _valid_final(values):
            raise ValueError("Combined saved and source values fail NOAA validation")
        con.execute(
            "INSERT INTO data(loc_id,dates,provider,temp_mean,temp_max,temp_min,precip) "
            "SELECT loc_id,%s,%s,%s,%s,%s,%s FROM locations WHERE lat=%s AND lon=%s "
            "ON CONFLICT(loc_id,dates,provider) DO UPDATE SET "
            "temp_mean=EXCLUDED.temp_mean,temp_max=EXCLUDED.temp_max,"
            "temp_min=EXCLUDED.temp_min,precip=EXCLUDED.precip",
            (month_data.month, NOAA_CORE_PROVIDER, *values, *sample),
        )


def _worker(con, sample, month, options):
    try:
        archive = BoundedArchiveClient(options)
        data = load_core_month(month, archive=archive)
        if time.monotonic() > archive.deadline:
            raise CoreDownloadError("Location download time budget exhausted")
        _store_sample(con, sample, data)
        con.execute(
            "UPDATE climate_location_fetch_job SET state='complete',updated_at=CURRENT_TIMESTAMP WHERE id=1"
        )
    except Exception:
        logger.warning("Location NOAA month failed; sample cache remains resumable", exc_info=False)
        try:
            con.execute(
                "UPDATE climate_location_fetch_job SET state='failed',updated_at=CURRENT_TIMESTAMP WHERE id=1"
            )
        except Exception:
            logger.warning("Location job status could not be recorded")
    finally:
        con.close()


def start(latitude, longitude, config):
    sample = _sample(latitude, longitude)
    options = settings(config)
    if not options["enabled"]:
        return {"state": "disabled", "complete": 0, "total": 0,
                "remaining": 0, "month": None, "retry_seconds": 0,
                "sample": {"latitude": sample[0], "longitude": sample[1]}}
    con = _connect()
    handed_off = False
    try:
        if not con.execute("SELECT pg_try_advisory_lock(%s)", (LOCK_ID,)).fetchone()[0]:
            return status(latitude, longitude, config)
        complete, total, missing = _coverage(con, sample)
        if not missing:
            return {"state": "done", "complete": complete, "total": total,
                    "remaining": 0, "month": None, "retry_seconds": 0,
                    "sample": {"latitude": sample[0], "longitude": sample[1]}}
        now = datetime.now(timezone.utc)
        with con.transaction():
            con.execute(
                "INSERT INTO climate_location_fetch_limit(id,window_start,starts) "
                "VALUES(1,%s,0) ON CONFLICT(id) DO NOTHING", (now,)
            )
            window, used = con.execute(
                "SELECT window_start,starts FROM climate_location_fetch_limit WHERE id=1 FOR UPDATE"
            ).fetchone()
            if now - window >= timedelta(hours=1):
                window, used = now, 0
            if used >= options["hourly_limit"]:
                return {"state": "throttled", "remaining": len(missing),
                        "complete": complete, "total": total,
                        "retry_seconds": max(1, int(3600 - (now - window).total_seconds()) + 1),
                        "month": None,
                        "sample": {"latitude": sample[0], "longitude": sample[1]}}
            con.execute(
                "UPDATE climate_location_fetch_limit SET window_start=%s,starts=%s WHERE id=1",
                (window, used + 1),
            )
            month = missing[-1]  # Recent history becomes visible first.
            con.execute(
                "INSERT INTO climate_location_fetch_job"
                "(id,state,sample_lat,sample_lon,current_month,backend_pid) "
                "VALUES(1,'running',%s,%s,%s,pg_backend_pid()) ON CONFLICT(id) DO UPDATE SET "
                "state='running',sample_lat=EXCLUDED.sample_lat,sample_lon=EXCLUDED.sample_lon,"
                "current_month=EXCLUDED.current_month,backend_pid=EXCLUDED.backend_pid,"
                "started_at=CURRENT_TIMESTAMP,"
                "updated_at=CURRENT_TIMESTAMP",
                (*sample, month),
            )
        Thread(target=_worker, args=(con, sample, month, options), daemon=True).start()
        handed_off = True
        result = status(latitude, longitude, config)
        result["state"] = "running"
        result["month"] = month.strftime("%Y-%m")
        return result
    finally:
        if not handed_off:
            con.close()
