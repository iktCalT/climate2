import logging

import openmeteo_requests  # https://open-meteo.com/en/docs/climate-api
import numpy as np
import pandas as pd
import requests_cache
from openmeteo_requests import OpenMeteoRequestsError
from retry_requests import retry

from db import fetch_loc_id, weather_db

logger = logging.getLogger(__name__)

METEO_SHORT_NAMES = {
    "temperature_2m_mean": "temp_mean",
    "temperature_2m_max": "temp_max",
    "temperature_2m_min": "temp_min",
    "precipitation_sum": "precip",
}

SHORT_TO_METEO_NAMES = {value: key for key, value in METEO_SHORT_NAMES.items()}

DEFAULT_MODELS = ("MRI_AGCM3_2_S", "EC_Earth3P_HR")
DEFAULT_METEO_TYPES = (
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
)
OPEN_METEO_HTTP_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60

_openmeteo_client = None


def _coord_key(lat, lon):
    return (round(float(lat), 10), round(float(lon), 10))


def get_openmeteo_client():
    """Reuse one cached Open-Meteo client for a process."""
    global _openmeteo_client
    if _openmeteo_client is None:
        cache_session = requests_cache.CachedSession(
            ".cache", expire_after=OPEN_METEO_HTTP_CACHE_TTL_SECONDS
        )
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        _openmeteo_client = openmeteo_requests.Client(session=retry_session)
    return _openmeteo_client


def get_data(
    con=None,
    location=(0, 0),
    date_start="1950-01-01",
    date_end="1951-12-31",
    models=None,
    meteo_types=None,
    save_as_csv=False,
    insert_into_database=False,
    force_update_database=False,
    return_DataFrame=False,
):
    """Fetch climate data from Open-Meteo; optionally save CSV or upsert into PostgreSQL."""
    lat, lon = location
    models = DEFAULT_MODELS if models is None else tuple(models)
    meteo_types = DEFAULT_METEO_TYPES if meteo_types is None else tuple(meteo_types)
    loc_id = fetch_loc_id(lat, lon, con) if insert_into_database else None

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_start,
        "end_date": date_end,
        "models": models,
        "daily": meteo_types,
    }
    try:
        responses = get_openmeteo_client().weather_api(
            "https://climate-api.open-meteo.com/v1/climate",
            params=params,
        )
    except OpenMeteoRequestsError as error:
        logger.warning(
            "Open-Meteo request failed for latitude=%s longitude=%s: %s",
            lat,
            lon,
            error,
        )
        return False

    if not responses:
        logger.warning(
            "Open-Meteo returned no responses for latitude=%s longitude=%s",
            lat,
            lon,
        )
        return False

    short_names = [METEO_SHORT_NAMES.get(name, name) for name in meteo_types]
    daily_dataframes = []

    try:
        for index, response in enumerate(responses):
            model_name = models[index] if index < len(models) else f"response-{index + 1}"
            logger.info(
                "Received Open-Meteo model=%s requested=(%s, %s) actual=(%s, %s)",
                model_name,
                lat,
                lon,
                response.Latitude(),
                response.Longitude(),
            )

            daily = response.Daily()
            daily_data = {
                "loc_id": loc_id,
                "dates": pd.date_range(
                    start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                    end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=daily.Interval()),
                    inclusive="left",
                ),
            }
            for variable_index, short_name in enumerate(short_names):
                daily_data[short_name] = daily.Variables(
                    variable_index
                ).ValuesAsNumpy()
            daily_dataframes.append(pd.DataFrame(data=daily_data))

        mean_daily_dataframe = pd.concat(daily_dataframes).groupby(["dates"]).mean()
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        logger.warning(
            "Open-Meteo returned an invalid response for latitude=%s longitude=%s",
            lat,
            lon,
            exc_info=True,
        )
        return False

    aggregation_dict = {
        "loc_id": "mean",
        "temp_mean": "mean",
        "temp_max": "max",
        "temp_min": "min",
        "precip": "mean",
    }
    valid_aggregation_dict = {
        col: agg
        for col, agg in aggregation_dict.items()
        if col in mean_daily_dataframe.columns
    }
    mean_monthly_dataframe = mean_daily_dataframe.resample("MS").agg(
        valid_aggregation_dict
    )

    if save_as_csv:
        mean_monthly_dataframe.to_csv(
            "static/weather_data/" + str(lat) + "-" + str(lon) + ".csv"
        )

    if insert_into_database:
        # An insert preserves cached values while an update refreshes exactly
        # the requested month range. Both are safe PostgreSQL upserts.
        write_type = "update" if force_update_database else "insert"
        if not modify_database(mean_monthly_dataframe, type=write_type, con=con):
            return False

    if return_DataFrame:
        return mean_monthly_dataframe
    return True


def get_data_in_database(lat, lon, con=None):
    """Return existing weather rows for a location (at most one probe row)."""
    with weather_db(con) as db:
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM data WHERE loc_id =
                (SELECT loc_id FROM locations WHERE lat = %s AND lon = %s)
                LIMIT 1
                """,
                (lat, lon),
            )
            return cur.fetchall()


def load_location_history(location, date_start, date_end, fields, con=None):
    """Load monthly cached values for a location and requested fields."""
    invalid_fields = set(fields) - set(SHORT_TO_METEO_NAMES)
    if invalid_fields:
        raise ValueError(f"Unsupported climate fields: {sorted(invalid_fields)}")

    columns = ", ".join(f"d.{field}" for field in fields)
    with weather_db(con) as db:
        with db.cursor() as cur:
            cur.execute(
                f"""
                SELECT d.dates, {columns}
                FROM data AS d
                JOIN locations AS l ON l.loc_id = d.loc_id
                WHERE l.lat = %s AND l.lon = %s
                  AND d.dates BETWEEN %s AND %s
                ORDER BY d.dates
                """,
                (float(location[0]), float(location[1]), date_start, date_end),
            )
            rows = cur.fetchall()

    history = pd.DataFrame(rows, columns=["dates", *fields])
    if history.empty:
        return pd.DataFrame(columns=fields, index=pd.DatetimeIndex([], name="dates"))
    history["dates"] = pd.to_datetime(history["dates"])
    return history.set_index("dates")


def _expected_months(date_start, date_end):
    start = pd.Timestamp(date_start).to_period("M").to_timestamp()
    end = pd.Timestamp(date_end).to_period("M").to_timestamp()
    return pd.date_range(start=start, end=end, freq="MS")


def _missing_month_ranges(history, expected_months, fields):
    """Return contiguous missing/incomplete monthly ranges as daily API bounds."""
    complete = set()
    if not history.empty:
        for month, row in history.iterrows():
            if not row[list(fields)].isna().any():
                complete.add(pd.Timestamp(month).to_period("M").to_timestamp())

    missing = [month for month in expected_months if month not in complete]
    if not missing:
        return []

    ranges = []
    start = previous = missing[0]
    for month in missing[1:]:
        if month == previous + pd.offsets.MonthBegin(1):
            previous = month
            continue
        ranges.append((start, previous))
        start = previous = month
    ranges.append((start, previous))
    return [
        (start.strftime("%Y-%m-%d"), (end + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d"))
        for start, end in ranges
    ]


def missing_location_ranges(
    location,
    date_start,
    date_end,
    fields=("temp_mean", "temp_max", "temp_min", "precip"),
    con=None,
):
    """Return missing or incomplete monthly ranges for one cached location."""
    fields = tuple(fields)
    history = load_location_history(location, date_start, date_end, fields, con=con)
    return _missing_month_ranges(
        history,
        _expected_months(date_start, date_end),
        fields,
    )


def get_location_history(
    location,
    date_start,
    date_end,
    fields=("temp_mean", "precip"),
    con=None,
):
    """Serve cached history, fetching and storing only missing month ranges.

    Returns ``(history, fetched)`` where ``fetched`` reports whether Open-Meteo
    was contacted. The returned data always comes from PostgreSQL.
    """
    fields = tuple(fields)
    expected_months = _expected_months(date_start, date_end)
    with weather_db(con) as db:
        history = load_location_history(location, date_start, date_end, fields, con=db)
        missing_ranges = _missing_month_ranges(history, expected_months, fields)
        if not missing_ranges:
            return history.reindex(expected_months), False

        meteo_types = [SHORT_TO_METEO_NAMES[field] for field in fields]
        for missing_start, missing_end in missing_ranges:
            ok = get_data(
                con=db,
                location=location,
                date_start=missing_start,
                date_end=missing_end,
                meteo_types=meteo_types,
                insert_into_database=True,
                force_update_database=True,
            )
            if not ok:
                raise RuntimeError("Open-Meteo could not provide the requested history")
        history = load_location_history(location, date_start, date_end, fields, con=db)
    return history.reindex(expected_months), True


def _locations_with_data(con):
    with con.cursor() as cur:
        cur.execute(
            """
            SELECT l.lat, l.lon
            FROM locations l
            WHERE EXISTS (SELECT 1 FROM data d WHERE d.loc_id = l.loc_id)
            """
        )
        rows = cur.fetchall()
    return {_coord_key(lat, lon) for lat, lon in rows}


def get_data_locations(
    lats,
    lons,
    date_start="1950-01-01",
    date_end="1951-12-31",
    force_update_database=False,
):
    """Fetch Open-Meteo data for a lat/lon grid into PostgreSQL."""
    # https://open-meteo.com/en/terms — ~10k/day, 5k/hour, 600/min
    if len(lats) * len(lons) > 5000:
        print(
            """Warning: too many locations at one time.
              \nAPI Hourly limit: 5'000 (around 370 locations)
              \nAPI Daily limit: 10'000
              \nCheck terms at https://open-meteo.com/en/terms"""
        )
        return False

    with weather_db() as con:
        existing = set() if force_update_database else _locations_with_data(con)
        for lat in lats:
            for lon in lons:
                if not force_update_database and _coord_key(lat, lon) in existing:
                    print(
                        f"For location {lat}°N, {lon}°E, data already exists. \n\tSkipping these locations."
                    )
                    continue
                ok = get_data(
                    con=con,
                    location=(lat, lon),
                    date_start=date_start,
                    date_end=date_end,
                    insert_into_database=True,
                    force_update_database=force_update_database,
                )
                if not ok:
                    print("Something went wrong while getting data.")
                    print(f"\tCurrent latitude: {lat}\n\tCurrent longitude: {lon}")
                    return False
    print("\nSuccess!\n")
    return True


def modify_database(data, type="donothing", con=None):
    """Insert or update weather rows from a DataFrame with PostgreSQL upserts."""
    if type not in ("insert", "update"):
        logger.warning(
            "Unsupported database write mode %r; expected 'insert' or 'update'", type
        )
        return False

    with weather_db(con) as db:
        rows = [
            (
                int(row.loc_id),
                row.Index.date() if hasattr(row.Index, "date") else row.Index,
                _nullable_float(getattr(row, "temp_mean", None)),
                _nullable_float(getattr(row, "temp_max", None)),
                _nullable_float(getattr(row, "temp_min", None)),
                _nullable_float(getattr(row, "precip", None)),
            )
            for row in data.itertuples()
        ]
        if not rows:
            return True
        with db.cursor() as cur:
            if type == "insert":
                cur.executemany(
                    """
                    INSERT INTO data (loc_id, dates, temp_mean, temp_max, temp_min, precip)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (loc_id, dates) DO NOTHING
                    """,
                    rows,
                )
            else:
                cur.executemany(
                    """
                    INSERT INTO data (loc_id, dates, temp_mean, temp_max, temp_min, precip)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (loc_id, dates) DO UPDATE SET
                        temp_mean = COALESCE(EXCLUDED.temp_mean, data.temp_mean),
                        temp_max = COALESCE(EXCLUDED.temp_max, data.temp_max),
                        temp_min = COALESCE(EXCLUDED.temp_min, data.temp_min),
                        precip = COALESCE(EXCLUDED.precip, data.precip)
                    """,
                    rows,
                )
    return True


def _nullable_float(value):
    return None if value is None or pd.isna(value) else float(value)


if __name__ == "__main__":
    lats = [90]
    lons = np.linspace(-180, 180, 91)
    get_data_locations(
        lats=lats,
        lons=lons,
        date_start="1950-01-01",
        date_end="2023-12-31",
        force_update_database=False,
    )
