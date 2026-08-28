import openmeteo_requests  # https://open-meteo.com/en/docs/climate-api
import numpy as np
import pandas as pd
import requests_cache
from retry_requests import retry
import sqlite3

from db import WEATHER_DB, fetch_loc_id, weather_db

METEO_SHORT_NAMES = {
    "temperature_2m_mean": "temp_mean",
    "temperature_2m_max": "temp_max",
    "temperature_2m_min": "temp_min",
    "precipitation_sum": "precip",
}

_openmeteo_client = None


def _coord_key(lat, lon):
    return (round(float(lat), 10), round(float(lon), 10))


def get_openmeteo_client():
    """Reuse one cached Open-Meteo client for a process."""
    global _openmeteo_client
    if _openmeteo_client is None:
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        _openmeteo_client = openmeteo_requests.Client(session=retry_session)
    return _openmeteo_client


def get_data(
    con=None,
    location=(0, 0),
    date_start="1950-01-01",
    date_end="1951-12-31",
    models=["MRI_AGCM3_2_S", "EC_Earth3P_HR"],
    meteo_types=[
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
    ],
    save_as_csv=False,
    insert_into_database=False,
    force_update_database=False,
    return_DataFrame=False,
):
    """Fetch climate data from Open-Meteo; optionally save CSV or insert into SQLite."""
    lat, lon = location
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
    except Exception as e:
        print(f"Open-Meteo request failed: {e}")
        return False

    short_names = [METEO_SHORT_NAMES.get(name, name) for name in meteo_types]
    daily_dataframes = []

    for i, response in enumerate(responses):
        if i == 0:
            print(f"Got data from location: {lat}°N, {lon}°E")
            print(
                f"\tActual coordinate: {response.Latitude()}°N, {response.Longitude()}°E"
            )
        print(f"\tModel {i + 1}: {models[i]}")

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
        for j, short_name in enumerate(short_names):
            daily_data[short_name] = daily.Variables(j).ValuesAsNumpy()
        daily_dataframes.append(pd.DataFrame(data=daily_data))

    mean_daily_dataframe = pd.concat(daily_dataframes).groupby(["dates"]).mean()

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
        data_tmp = get_data_in_database(lat, lon, con=con)
        if data_tmp:
            if force_update_database:
                print(
                    f"For location {lat}°N, {lon}°E, data already exists. \n\tUpdating data in the database."
                )
                modify_database(mean_monthly_dataframe, type="update", con=con)
            else:
                print(
                    f"For location {lat}°N, {lon}°E, data already exists. \n\tSkipping these locations."
                )
        else:
            modify_database(mean_monthly_dataframe, type="insert", con=con)

    if return_DataFrame:
        return mean_monthly_dataframe
    return True


def get_data_in_database(lat, lon, con=None):
    """Return existing weather rows for a location (at most one probe row)."""
    try:
        with weather_db(con) as db:
            return db.execute(
                """
                SELECT * FROM data WHERE loc_id =
                (SELECT loc_id FROM locations WHERE lat = ? AND lon = ?)
                LIMIT 1
                """,
                (lat, lon),
            ).fetchall()
    except sqlite3.Error as e:
        print(f"get_data_in_database failed: {e}")
        return False


def _locations_with_data(con):
    rows = con.execute(
        """
        SELECT l.lat, l.lon
        FROM locations l
        WHERE EXISTS (SELECT 1 FROM data d WHERE d.loc_id = l.loc_id)
        """
    ).fetchall()
    return {_coord_key(lat, lon) for lat, lon in rows}


def get_data_locations(
    lats,
    lons,
    date_start="1950-01-01",
    date_end="1951-12-31",
    dbpath=WEATHER_DB,
    force_update_database=False,
):
    """Fetch Open-Meteo data for a lat/lon grid into SQLite."""
    # https://open-meteo.com/en/terms — ~10k/day, 5k/hour, 600/min
    if len(lats) * len(lons) > 5000:
        print(
            """Warning: too many locations at one time.
              \nAPI Hourly limit: 5'000 (around 370 locations)
              \nAPI Daily limit: 10'000
              \nCheck terms at https://open-meteo.com/en/terms"""
        )
        return False

    with weather_db(path=dbpath) as con:
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
    """INSERT OR IGNORE or REPLACE weather rows from a DataFrame."""
    if type not in ("insert", "update"):
        print("\nWarning: wrong type specified, only 'insert' or 'update' are acceptable\n")
        return False

    try:
        with weather_db(con) as db:
            data.to_sql("temporary_table", db, if_exists="replace")
            if type == "insert":
                db.execute(
                    """
                    INSERT OR IGNORE INTO data (loc_id, dates, temp_mean, temp_max, temp_min, precip)
                    SELECT loc_id, dates, temp_mean, temp_max, temp_min, precip
                    FROM temporary_table
                    """
                )
            else:
                db.execute(
                    """
                    REPLACE INTO data (loc_id, dates, temp_mean, temp_max, temp_min, precip)
                    SELECT loc_id, dates, temp_mean, temp_max, temp_min, precip
                    FROM temporary_table
                    """
                )
        return True
    except sqlite3.Error as e:
        print(f"modify_database failed: {e}")
        return False


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
