"""Viewport-sized climate data for the interactive MapLibre map."""
import math
import numpy as np
import pandas as pd
from db import CLIMATE_TYPES, weather_db
from helpers_data import SHORT_TO_METEO_NAMES, get_data

MAX_VIEWPORT_POINTS = 600
MAX_FETCH_PER_VIEWPORT = 12

def step_for_zoom(zoom):
    if zoom < 3: return 4.0
    if zoom < 5: return 2.0
    if zoom < 7: return 1.0
    if zoom < 9: return 0.5
    if zoom < 11: return 0.25
    return 0.1

def _sample_coordinates(south, west, north, east, zoom):
    step = step_for_zoom(zoom)
    count = (math.floor((north-south)/step)+1) * (math.floor((east-west)/step)+1)
    if count > MAX_VIEWPORT_POINTS: step *= math.sqrt(count / MAX_VIEWPORT_POINTS)
    lats = np.arange(math.ceil(south/step)*step, north+step/2, step)
    lons = np.arange(math.ceil(west/step)*step, east+step/2, step)
    return [(round(float(a), 6), round(float(b), 6)) for a in lats for b in lons], step

def viewport_geojson(month, climate_type, south, west, north, east, zoom, fetch_missing=True):
    if climate_type not in CLIMATE_TYPES: raise ValueError("Unsupported climate type")
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180): raise ValueError("Invalid viewport bounds")
    samples, step = _sample_coordinates(south, west, north, east, zoom)
    date = f"{month}-01"
    query = f"SELECT l.lat, l.lon, d.{climate_type} FROM data d JOIN locations l ON l.loc_id=d.loc_id WHERE d.dates=%s AND l.lat BETWEEN %s AND %s AND l.lon BETWEEN %s AND %s"
    with weather_db() as con:
        with con.cursor() as cur:
            cur.execute(query, (date, south, north, west, east)); rows = cur.fetchall()
        existing = {(round(float(a), 6), round(float(b), 6)) for a, b, _ in rows}
        missing = [point for point in samples if point not in existing]
        fetched = 0
        if fetch_missing:
            period = pd.Period(month, freq="M")
            for point in missing[:MAX_FETCH_PER_VIEWPORT]:
                if get_data(con=con, location=point, date_start=period.start_time.strftime("%Y-%m-%d"), date_end=period.end_time.strftime("%Y-%m-%d"), meteo_types=[SHORT_TO_METEO_NAMES[climate_type]], insert_into_database=True, force_update_database=True): fetched += 1
            if fetched:
                with con.cursor() as cur:
                    cur.execute(query, (date, south, north, west, east)); rows = cur.fetchall()
    return {"type":"FeatureCollection", "features":[{"type":"Feature", "id":f"{a:.6f}:{b:.6f}", "geometry":{"type":"Point","coordinates":[float(b),float(a)]}, "properties":{"value":v,"latitude":a,"longitude":b}} for a,b,v in rows if v is not None], "metadata":{"step":step,"fetched":fetched,"missing":max(0,len(missing)-fetched)}}
