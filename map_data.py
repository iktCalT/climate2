"""Viewport-sized climate data for the interactive MapLibre map."""
import math
import numpy as np
import pandas as pd
from db import CLIMATE_TYPES, weather_db
from helpers_data import SHORT_TO_METEO_NAMES, get_data

MAX_VIEWPORT_POINTS = 600
MAX_FETCH_PER_VIEWPORT = 12


def step_for_zoom(zoom):
    """Return the latitude/longitude tile size for a zoom level.

    The imported climate grid is 2 degrees apart north-to-south and 4 degrees
    apart east-to-west.  Keeping that aspect ratio at low zoom prevents the
    empty vertical bands that appeared when 4-degree source samples were drawn
    in 2-degree-wide tiles.  Finer levels ask Open-Meteo for real values at the
    centre of the smaller cells, subject to the per-request fetch limit.
    """
    if zoom < 3:
        return 2.0, 4.0
    if zoom < 5:
        return 1.0, 2.0
    if zoom < 7:
        return 0.5, 1.0
    if zoom < 9:
        return 0.25, 0.5
    if zoom < 11:
        return 0.1, 0.2
    return 0.05, 0.1



def _grid_edges(low, high, step, lower_limit, upper_limit):
    """Create stable, clipped grid edges that every adjacent tile shares."""
    start = max(lower_limit, math.floor(low / step) * step)
    end = min(upper_limit, math.ceil(high / step) * step)
    count = max(1, math.ceil((end - start) / step))
    edges = [round(min(end, start + index * step), 8) for index in range(count + 1)]
    edges[-1] = round(end, 8)
    return edges


def _viewport_cells(south, west, north, east, zoom):
    """Return a bounded rectangular mesh covering the visible map area."""
    lat_step, lon_step = step_for_zoom(zoom)
    while True:
        lat_edges = _grid_edges(south, north, lat_step, -90, 90)
        lon_edges = _grid_edges(west, east, lon_step, -180, 180)
        count = (len(lat_edges) - 1) * (len(lon_edges) - 1)
        if count <= MAX_VIEWPORT_POINTS:
            break
        scale = math.sqrt(count / MAX_VIEWPORT_POINTS)
        lat_step *= scale
        lon_step *= scale

    cells = []
    for lat_index, (cell_south, cell_north) in enumerate(zip(lat_edges, lat_edges[1:])):
        for lon_index, (cell_west, cell_east) in enumerate(zip(lon_edges, lon_edges[1:])):
            cells.append({
                "index": (lat_index, lon_index),
                "south": cell_south,
                "west": cell_west,
                "north": cell_north,
                "east": cell_east,
                "latitude": round((cell_south + cell_north) / 2, 6),
                "longitude": round((cell_west + cell_east) / 2, 6),
            })
    return cells, lat_edges, lon_edges, lat_step, lon_step


def _sample_coordinates(south, west, north, east, zoom):
    """Compatibility helper for tests and callers that only need cell centres."""
    cells, _, _, lat_step, lon_step = _viewport_cells(south, west, north, east, zoom)
    return [(cell["latitude"], cell["longitude"]) for cell in cells], max(lat_step, lon_step)


def _bucket_rows(rows, lat_edges, lon_edges):
    """Aggregate cached source points into their containing rectangular tile."""
    values = {}
    for lat, lon, value in rows:
        if value is None:
            continue
        lat_index = min(len(lat_edges) - 2, max(0, np.searchsorted(lat_edges, float(lat), side="right") - 1))
        lon_index = min(len(lon_edges) - 2, max(0, np.searchsorted(lon_edges, float(lon), side="right") - 1))
        values.setdefault((lat_index, lon_index), []).append(float(value))
    return values


def _estimated_values(cells, cell_values):
    """Provide a continuous display while finer cells await Open-Meteo data.

    Estimates never replace database values. The response labels them so the
    browser can distinguish a temporary nearest-cached value from an observed
    one while bounded cache-miss requests fill the finer grid.
    """
    observed = [cell for cell in cells if cell["index"] in cell_values]
    if not observed:
        return {}

    observed_coordinates = np.array(
        [(cell["latitude"], cell["longitude"]) for cell in observed], dtype=float
    )
    observed_values = np.array(
        [np.mean(cell_values[cell["index"]]) for cell in observed], dtype=float
    )
    estimates = {}
    for cell in cells:
        if cell["index"] in cell_values:
            continue
        distances = np.square(observed_coordinates[:, 0] - cell["latitude"]) + np.square(
            observed_coordinates[:, 1] - cell["longitude"]
        )
        estimates[cell["index"]] = float(observed_values[np.argmin(distances)])
    return estimates


def viewport_geojson(month, climate_type, south, west, north, east, zoom, fetch_missing=True):
    if climate_type not in CLIMATE_TYPES: raise ValueError("Unsupported climate type")
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180): raise ValueError("Invalid viewport bounds")
    cells, lat_edges, lon_edges, lat_step, lon_step = _viewport_cells(south, west, north, east, zoom)
    date = f"{month}-01"
    query = f"SELECT l.lat, l.lon, d.{climate_type} FROM data d JOIN locations l ON l.loc_id=d.loc_id WHERE d.dates=%s AND l.lat BETWEEN %s AND %s AND l.lon BETWEEN %s AND %s ORDER BY l.lat, l.lon"
    with weather_db() as con:
        with con.cursor() as cur:
            cur.execute(query, (date, lat_edges[0], lat_edges[-1], lon_edges[0], lon_edges[-1]))
            rows = cur.fetchall()
        cell_values = _bucket_rows(rows, lat_edges, lon_edges)
        missing = [cell for cell in cells if cell["index"] not in cell_values]
        fetched = 0
        if fetch_missing:
            period = pd.Period(month, freq="M")
            for cell in missing[:MAX_FETCH_PER_VIEWPORT]:
                if get_data(con=con, location=(cell["latitude"], cell["longitude"]), date_start=period.start_time.strftime("%Y-%m-%d"), date_end=period.end_time.strftime("%Y-%m-%d"), meteo_types=[SHORT_TO_METEO_NAMES[climate_type]], insert_into_database=True, force_update_database=True):
                    fetched += 1
            if fetched:
                with con.cursor() as cur:
                    cur.execute(query, (date, lat_edges[0], lat_edges[-1], lon_edges[0], lon_edges[-1]))
                    rows = cur.fetchall()
                cell_values = _bucket_rows(rows, lat_edges, lon_edges)

    estimates = _estimated_values(cells, cell_values)
    features = []
    for cell in cells:
        values = cell_values.get(cell["index"])
        estimated = not values
        value = estimates.get(cell["index"]) if estimated else sum(values) / len(values)
        if value is None:
            continue
        features.append({
            "type": "Feature",
            "id": f"{cell['latitude']:.6f}:{cell['longitude']:.6f}",
            "geometry": {"type": "Polygon", "coordinates": [[
                [cell["west"], cell["south"]], [cell["east"], cell["south"]],
                [cell["east"], cell["north"]], [cell["west"], cell["north"]],
                [cell["west"], cell["south"]],
            ]]},
            "properties": {
                "value": value,
                "latitude": cell["latitude"],
                "longitude": cell["longitude"],
                "source_count": len(values or []),
                "estimated": estimated,
            },
        })
    missing_count = sum(1 for cell in cells if cell["index"] not in cell_values)
    return {"type":"FeatureCollection", "features":features, "metadata":{"latitude_step":lat_step,"longitude_step":lon_step,"fetched":fetched,"missing":missing_count}}
