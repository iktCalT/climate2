"""Anonymous NOAA CORe bulk retrieval and canonical-grid PostgreSQL import.

The NOAA Open Data Dissemination archive exposes GRIB indexes containing byte
offsets. This module downloads only the required records, validates and
downsamples them to the application's 2-degree by 4-degree grid, and writes one
complete provider-scoped month transactionally.
"""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np

from db import weather_db


logger = logging.getLogger(__name__)

NOAA_CORE_PROVIDER = "noaa_core"
NOAA_CORE_BASE_URL = (
    "https://storage.googleapis.com/noaa-nws-ncep-core/grib"
)
NOAA_CORE_USER_AGENT = "climate2-noaa-core-importer/1.0"
CANONICAL_LATS = np.linspace(-90.0, 90.0, 91)
CANONICAL_LONS = np.linspace(-180.0, 180.0, 91)
CANONICAL_LOCATION_COUNT = len(CANONICAL_LATS) * len(CANONICAL_LONS)
MAX_INDEX_BYTES = 2 * 1024 * 1024

MONTHLY_RECORDS = {
    "temp_mean": (
        ":TMP:2 m above ground:",
        "@3 hour ave(anl)",
        ":ens mean",
    ),
    "precip": (
        ":PRATE:surface:",
        "ave(0-3 hour ave fcst)",
        ":ens mean",
    ),
}

DAILY_RECORDS = {
    "temp_min": (
        ":TMP:2 m above ground:",
        "@3 hour min(0-3 hour min fcst)",
        ":ens mean",
    ),
    "temp_max": (
        ":TMP:2 m above ground:",
        "@3 hour max(0-3 hour max fcst)",
        ":ens mean",
    ),
}


class CoreError(RuntimeError):
    """Base exception for safe, concise importer failures."""


class CoreDownloadError(CoreError):
    """The official NOAA archive could not provide a required record."""


class CoreDecodeError(CoreError):
    """A GRIB record did not match the documented CORe data contract."""


@dataclass(frozen=True)
class GribRecord:
    number: int
    offset: int
    end: int | None
    description: str


@dataclass(frozen=True)
class GridField:
    values: np.ndarray
    latitudes: np.ndarray
    longitudes: np.ndarray
    short_name: str
    units: str
    grid_type: str
    data_date: int | None = None
    step_type: str = ""


@dataclass(frozen=True)
class CoreMonthData:
    month: date
    temp_mean: np.ndarray
    temp_max: np.ndarray
    temp_min: np.ndarray
    precip: np.ndarray

    def rows(self):
        """Yield canonical coordinates and four validated climate metrics."""
        for lat_index, lat in enumerate(CANONICAL_LATS):
            for lon_index, lon in enumerate(CANONICAL_LONS):
                yield (
                    float(lat),
                    float(lon),
                    float(self.temp_mean[lat_index, lon_index]),
                    float(self.temp_max[lat_index, lon_index]),
                    float(self.temp_min[lat_index, lon_index]),
                    float(self.precip[lat_index, lon_index]),
                )


def monthly_file_url(month):
    """Return the official NODD monthly flux-file URL."""
    return (
        f"{NOAA_CORE_BASE_URL}/month/flx/{month.year:04d}/"
        f"flx.{month.year:04d}{month.month:02d}"
    )


def daily_file_url(day):
    """Return the official NODD daily flux-file URL."""
    return (
        f"{NOAA_CORE_BASE_URL}/day/flx/{day.year:04d}/{day.month:02d}/"
        f"flx.{day.year:04d}{day.month:02d}{day.day:02d}"
    )


def parse_grib_index(text):
    """Parse a wgrib-style index and calculate each message's byte range."""
    raw_records = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(":", 2)
        if len(parts) != 3:
            raise CoreDownloadError("NOAA returned a malformed GRIB index line")
        try:
            number = int(parts[0])
            offset = int(parts[1])
        except ValueError as error:
            raise CoreDownloadError("NOAA returned a malformed GRIB index offset") from error
        if number < 1 or offset < 0:
            raise CoreDownloadError("NOAA returned an invalid GRIB index offset")
        raw_records.append((number, offset, line))

    if not raw_records:
        raise CoreDownloadError("NOAA returned an empty GRIB index")
    if any(
        current[1] >= following[1]
        for current, following in zip(raw_records, raw_records[1:])
    ):
        raise CoreDownloadError("NOAA GRIB index offsets are not strictly increasing")

    records = []
    for index, (number, offset, description) in enumerate(raw_records):
        end = raw_records[index + 1][1] - 1 if index + 1 < len(raw_records) else None
        records.append(GribRecord(number, offset, end, description))
    return records


def select_index_records(records, specifications):
    """Select exactly one indexed record for each required field."""
    selected = {}
    for name, tokens in specifications.items():
        matches = [
            record
            for record in records
            if all(token in record.description for token in tokens)
        ]
        if len(matches) != 1:
            raise CoreDownloadError(
                f"Expected one NOAA CORe {name} record; found {len(matches)}"
            )
        if matches[0].end is None:
            raise CoreDownloadError(
                f"NOAA CORe {name} is the final record and has no indexed end offset"
            )
        selected[name] = matches[0]
    return selected


def _coalesced_record_groups(selected):
    """Group adjacent selected messages into the fewest byte-range requests."""
    ordered = sorted(selected.items(), key=lambda item: item[1].offset)
    groups = []
    for name, record in ordered:
        if not groups or record.offset > groups[-1][1] + 1:
            groups.append([record.offset, record.end, [(name, record)]])
        else:
            groups[-1][1] = max(groups[-1][1], record.end)
            groups[-1][2].append((name, record))
    return groups


class CoreArchiveClient:
    """Read public NOAA indexes and selected byte ranges with bounded retries."""

    def __init__(self, timeout_seconds=60.0, retries=3, sleep=time.sleep):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if retries < 1:
            raise ValueError("retries must be at least 1")
        self.timeout_seconds = float(timeout_seconds)
        self.retries = int(retries)
        self.sleep = sleep
        self._index_cache = {}

    def _download(self, url, byte_range=None, maximum_bytes=None):
        headers = {"User-Agent": NOAA_CORE_USER_AGENT}
        if byte_range is not None:
            start, end = byte_range
            headers["Range"] = f"bytes={start}-{end}"
            maximum_bytes = end - start + 1
        request = Request(url, headers=headers)
        last_error = None

        for attempt in range(self.retries):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    status = getattr(response, "status", response.getcode())
                    if byte_range is not None and status != 206:
                        raise CoreDownloadError(
                            "NOAA archive ignored a byte-range request; "
                            "refusing a full-file download"
                        )
                    data = response.read(maximum_bytes + 1 if maximum_bytes else -1)
                    if maximum_bytes is not None and len(data) > maximum_bytes:
                        raise CoreDownloadError("NOAA response exceeded its expected size")
                    if byte_range is not None and len(data) != maximum_bytes:
                        raise CoreDownloadError("NOAA returned an incomplete byte range")
                    return data
            except HTTPError as error:
                last_error = error
                if 400 <= error.code < 500 and error.code not in (408, 429):
                    break
            except (URLError, TimeoutError, OSError, CoreDownloadError) as error:
                last_error = error
            if attempt + 1 < self.retries:
                self.sleep(2**attempt)

        detail = getattr(last_error, "code", None) or str(last_error)
        raise CoreDownloadError(f"NOAA download failed ({detail})") from last_error

    def index_records(self, file_url):
        if file_url not in self._index_cache:
            payload = self._download(
                f"{file_url}.idx",
                maximum_bytes=MAX_INDEX_BYTES,
            )
            try:
                text = payload.decode("ascii")
            except UnicodeDecodeError as error:
                raise CoreDownloadError("NOAA returned a non-text GRIB index") from error
            self._index_cache[file_url] = parse_grib_index(text)
        return self._index_cache[file_url]

    def records(self, file_url, specifications):
        """Download selected messages, coalescing adjacent byte ranges."""
        selected = select_index_records(self.index_records(file_url), specifications)
        payloads = {}
        for start, end, group in _coalesced_record_groups(selected):
            block = self._download(f"{file_url}.grb", byte_range=(start, end))
            for name, record in group:
                relative_start = record.offset - start
                relative_end = record.end - start + 1
                payload = block[relative_start:relative_end]
                if not payload.startswith(b"GRIB") or not payload.endswith(b"7777"):
                    raise CoreDownloadError(
                        f"NOAA CORe {name} byte range is not one complete GRIB message"
                    )
                payloads[name] = payload
        return payloads


class EccodesDecoder:
    """Decode and validate CORe GRIB2 messages with ECMWF ecCodes."""

    def __init__(self, eccodes_module=None):
        if eccodes_module is None:
            try:
                import eccodes as eccodes_module  # type: ignore
            except (ImportError, RuntimeError) as error:
                raise CoreDecodeError(
                    "ecCodes is unavailable; install requirements.txt and run "
                    "`python -m eccodes selfcheck`"
                ) from error
        self.eccodes = eccodes_module

    def decode(self, payload, field_name, expected_date=None):
        handle = None
        try:
            handle = self.eccodes.codes_new_from_message(payload)
            short_name = str(self.eccodes.codes_get(handle, "shortName"))
            units = str(self.eccodes.codes_get(handle, "units"))
            grid_type = str(self.eccodes.codes_get(handle, "gridType"))
            level_type = str(self.eccodes.codes_get(handle, "typeOfLevel"))
            level = float(self.eccodes.codes_get(handle, "level"))
            data_date = int(self.eccodes.codes_get(handle, "dataDate"))
            step_type = str(self.eccodes.codes_get(handle, "stepType"))
            statistical_process = int(
                self.eccodes.codes_get(handle, "typeOfStatisticalProcessing")
            )
            values = np.asarray(
                self.eccodes.codes_get_values(handle), dtype=np.float64
            )
            latitudes = np.asarray(
                self.eccodes.codes_get_array(handle, "latitudes"), dtype=np.float64
            )
            longitudes = np.asarray(
                self.eccodes.codes_get_array(handle, "longitudes"), dtype=np.float64
            )
            bitmap_present = int(self.eccodes.codes_get(handle, "bitmapPresent"))
            if bitmap_present:
                missing_value = float(self.eccodes.codes_get(handle, "missingValue"))
                values[np.isclose(values, missing_value)] = np.nan
        except Exception as error:
            raise CoreDecodeError(f"Could not decode NOAA CORe {field_name}") from error
        finally:
            if handle is not None:
                self.eccodes.codes_release(handle)

        if grid_type != "regular_gg":
            raise CoreDecodeError(f"Unexpected NOAA CORe grid type: {grid_type}")
        if values.size != 512 * 256:
            raise CoreDecodeError(
                f"Unexpected NOAA CORe grid size: {values.size}; expected 131072"
            )
        if not (values.size == latitudes.size == longitudes.size):
            raise CoreDecodeError("NOAA CORe coordinates and values have different sizes")
        if np.unique(np.round(latitudes, 10)).size != 256 or np.unique(
            np.round(np.mod(longitudes, 360.0), 10)
        ).size != 512:
            raise CoreDecodeError("NOAA CORe does not use the documented 512 by 256 grid")
        if expected_date is not None and data_date != int(expected_date.strftime("%Y%m%d")):
            raise CoreDecodeError(
                f"Unexpected NOAA CORe data date: {data_date}; expected {expected_date:%Y%m%d}"
            )

        if field_name == "precip":
            normalized_units = units.lower().replace(" ", "").replace("**", "^")
            if (
                short_name.lower() not in {"prate", "avg_prate"}
                or normalized_units != "kgm^-2s^-1"
                or level_type != "surface"
                or step_type != "avg"
                or statistical_process != 0
            ):
                raise CoreDecodeError(
                    "Unexpected NOAA CORe precipitation metadata: "
                    f"{short_name} {units} {level_type} {step_type}"
                )
        else:
            expected_temperature_names = {
                "temp_mean": {"2t", "tmp", "avg_2t"},
                "temp_min": {"2t", "tmp", "min_2t"},
                "temp_max": {"2t", "tmp", "max_2t"},
            }
            if short_name.lower() not in expected_temperature_names[field_name]:
                raise CoreDecodeError(
                    f"Unexpected NOAA CORe temperature field: {short_name}"
                )
            if units.lower() not in {"k", "kelvin"}:
                raise CoreDecodeError(
                    f"Unexpected NOAA CORe temperature units: {units}"
                )
            if level_type != "heightAboveGround" or level != 2:
                raise CoreDecodeError(
                    f"Unexpected NOAA CORe temperature level: {level_type} {level:g}"
                )
            expected_steps = {
                "temp_mean": ("avg", 0),
                "temp_min": ("min", 3),
                "temp_max": ("max", 2),
            }
            if (step_type, statistical_process) != expected_steps[field_name]:
                raise CoreDecodeError(
                    f"Unexpected NOAA CORe {field_name} statistic: {step_type}"
                )

        return GridField(
            values=values,
            latitudes=latitudes,
            longitudes=longitudes,
            short_name=short_name,
            units=units,
            grid_type=grid_type,
            data_date=data_date,
            step_type=step_type,
        )


def sample_canonical(field):
    """Nearest-sample one complete Gaussian field onto the canonical grid."""
    rounded_lats = np.round(field.latitudes, 10)
    rounded_lons = np.round(np.mod(field.longitudes, 360.0), 10)
    source_lats, lat_inverse = np.unique(rounded_lats, return_inverse=True)
    source_lons, lon_inverse = np.unique(rounded_lons, return_inverse=True)

    flat_indexes = lat_inverse * len(source_lons) + lon_inverse
    if len(source_lats) * len(source_lons) != field.values.size:
        raise CoreDecodeError("NOAA CORe field is not a complete rectangular grid")
    if np.unique(flat_indexes).size != field.values.size:
        raise CoreDecodeError("NOAA CORe field contains duplicate grid coordinates")

    matrix = np.empty((len(source_lats), len(source_lons)), dtype=np.float64)
    matrix[lat_inverse, lon_inverse] = field.values
    target_lons = np.mod(CANONICAL_LONS, 360.0)
    lat_indexes = np.abs(
        source_lats[:, np.newaxis] - CANONICAL_LATS[np.newaxis, :]
    ).argmin(axis=0)
    lon_distances = np.abs(
        source_lons[:, np.newaxis] - target_lons[np.newaxis, :]
    )
    lon_indexes = np.minimum(lon_distances, 360.0 - lon_distances).argmin(axis=0)
    sampled = matrix[np.ix_(lat_indexes, lon_indexes)]
    if sampled.shape != (91, 91) or not np.isfinite(sampled).all():
        raise CoreDecodeError("NOAA CORe canonical sample contains missing values")
    return sampled


def _temperature_celsius(field, decoder, field_name, expected_date):
    return (
        sample_canonical(
            decoder.decode(field, field_name, expected_date=expected_date)
        )
        - 273.15
    )


def load_core_month(month, archive=None, decoder=None):
    """Download, aggregate, and validate one complete CORe calendar month."""
    month = date(month.year, month.month, 1)
    archive = CoreArchiveClient() if archive is None else archive
    decoder = EccodesDecoder() if decoder is None else decoder

    monthly_messages = archive.records(monthly_file_url(month), MONTHLY_RECORDS)
    temp_mean = _temperature_celsius(
        monthly_messages["temp_mean"], decoder, "temp_mean", month
    )
    precip_rate = sample_canonical(
        decoder.decode(
            monthly_messages["precip"], "precip", expected_date=month
        )
    )
    precip = np.maximum(precip_rate * 86_400.0, 0.0)

    temp_min = None
    temp_max = None
    days_in_month = monthrange(month.year, month.month)[1]
    for day_number in range(1, days_in_month + 1):
        day = date(month.year, month.month, day_number)
        daily_messages = archive.records(daily_file_url(day), DAILY_RECORDS)
        daily_min = _temperature_celsius(
            daily_messages["temp_min"], decoder, "temp_min", day
        )
        daily_max = _temperature_celsius(
            daily_messages["temp_max"], decoder, "temp_max", day
        )
        temp_min = daily_min if temp_min is None else np.minimum(temp_min, daily_min)
        temp_max = daily_max if temp_max is None else np.maximum(temp_max, daily_max)

    data = CoreMonthData(month, temp_mean, temp_max, temp_min, precip)
    validate_core_month(data)
    return data


def validate_core_month(data):
    """Reject incomplete, nonphysical, or internally inconsistent months."""
    expected_shape = (91, 91)
    for name in ("temp_mean", "temp_max", "temp_min", "precip"):
        values = getattr(data, name)
        if values.shape != expected_shape or not np.isfinite(values).all():
            raise CoreDecodeError(f"NOAA CORe {name} is incomplete")
    for name in ("temp_mean", "temp_max", "temp_min"):
        values = getattr(data, name)
        if values.min() < -150 or values.max() > 100:
            raise CoreDecodeError(f"NOAA CORe {name} is outside physical bounds")
    if data.precip.min() < -1e-6 or data.precip.max() > 5000:
        raise CoreDecodeError("NOAA CORe precipitation is outside physical bounds")
    if np.any(data.temp_min > data.temp_mean + 0.1):
        raise CoreDecodeError("NOAA CORe monthly mean is below its daily minimum")
    if np.any(data.temp_max < data.temp_mean - 0.1):
        raise CoreDecodeError("NOAA CORe monthly mean is above its daily maximum")


def completed_core_months(con, months):
    """Return months having all four fields at every canonical location."""
    months = tuple(months)
    if not months:
        return set()
    with con.cursor() as cur:
        cur.execute(
            """
            SELECT d.dates, COUNT(*)
            FROM data AS d
            JOIN locations AS l ON l.loc_id = d.loc_id
            WHERE d.provider = %s
              AND d.dates = ANY(%s)
              AND l.lat = ANY(%s)
              AND l.lon = ANY(%s)
              AND d.temp_mean IS NOT NULL
              AND d.temp_max IS NOT NULL
              AND d.temp_min IS NOT NULL
              AND d.precip IS NOT NULL
            GROUP BY d.dates
            """,
            (
                NOAA_CORE_PROVIDER,
                list(months),
                [float(value) for value in CANONICAL_LATS],
                [float(value) for value in CANONICAL_LONS],
            ),
        )
        rows = cur.fetchall()
    return {
        row[0]
        for row in rows
        if int(row[1]) == CANONICAL_LOCATION_COUNT
    }


def upsert_core_month(data, con=None):
    """Atomically upsert one complete CORe month across the canonical grid."""
    validate_core_month(data)
    location_rows = [
        (float(lat), float(lon))
        for lat in CANONICAL_LATS
        for lon in CANONICAL_LONS
    ]
    with weather_db(con) as db:
        with db.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO locations (lat, lon)
                VALUES (%s, %s)
                ON CONFLICT (lat, lon) DO NOTHING
                """,
                location_rows,
            )
            cur.execute(
                """
                SELECT loc_id, lat, lon
                FROM locations
                WHERE lat = ANY(%s) AND lon = ANY(%s)
                """,
                (
                    [float(value) for value in CANONICAL_LATS],
                    [float(value) for value in CANONICAL_LONS],
                ),
            )
            loc_ids = {
                (round(float(lat), 10), round(float(lon), 10)): int(loc_id)
                for loc_id, lat, lon in cur.fetchall()
            }
            if len(loc_ids) != CANONICAL_LOCATION_COUNT:
                raise CoreError("Could not resolve every canonical PostgreSQL location")

            rows = []
            for lat, lon, temp_mean, temp_max, temp_min, precip in data.rows():
                rows.append(
                    (
                        loc_ids[(round(lat, 10), round(lon, 10))],
                        data.month,
                        NOAA_CORE_PROVIDER,
                        temp_mean,
                        temp_max,
                        temp_min,
                        precip,
                    )
                )
            cur.executemany(
                """
                INSERT INTO data
                    (loc_id, dates, provider, temp_mean, temp_max, temp_min, precip)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (loc_id, dates, provider) DO UPDATE SET
                    temp_mean = EXCLUDED.temp_mean,
                    temp_max = EXCLUDED.temp_max,
                    temp_min = EXCLUDED.temp_min,
                    precip = EXCLUDED.precip
                """,
                rows,
            )
    logger.info(
        "Stored NOAA CORe month=%s rows=%d provider=%s",
        data.month,
        len(rows),
        NOAA_CORE_PROVIDER,
    )
