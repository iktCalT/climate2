"""Viewport-sized climate data for the interactive MapLibre map."""

import math

import numpy as np
import pandas as pd

from db import CLIMATE_TYPES, weather_db
from helpers_data import DEFAULT_METEO_TYPES, get_data

MAX_VIEWPORT_POINTS = 600
MAX_FETCH_PER_VIEWPORT = 12
MIN_ZOOM = 0


def step_for_zoom(zoom):
    """Return the latitude/longitude tile size for a zoom level.

    The imported climate grid is 2 degrees apart north-to-south and 4 degrees
    apart east-to-west. Keeping that aspect ratio at low zoom prevents the
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
    for lat_index, (cell_south, cell_north) in enumerate(
        zip(lat_edges, lat_edges[1:])
    ):
        for lon_index, (cell_west, cell_east) in enumerate(
            zip(lon_edges, lon_edges[1:])
        ):
            cells.append(
                {
                    "index": (lat_index, lon_index),
                    "south": cell_south,
                    "west": cell_west,
                    "north": cell_north,
                    "east": cell_east,
                    "latitude": round((cell_south + cell_north) / 2, 6),
                    "longitude": round((cell_west + cell_east) / 2, 6),
                }
            )
    return cells, lat_edges, lon_edges, lat_step, lon_step


def _sample_coordinates(south, west, north, east, zoom):
    """Compatibility helper for tests and callers that only need cell centres."""
    cells, _, _, lat_step, lon_step = _viewport_cells(south, west, north, east, zoom)
    return [(cell["latitude"], cell["longitude"]) for cell in cells], max(lat_step, lon_step)


def _bucket_rows(rows, lat_edges, lon_edges):
    """Aggregate cached source points into their containing rectangular tile."""
    rows = [(lat, lon, value) for lat, lon, value in rows if value is not None]
    if not rows:
        return {}

    coordinates = np.asarray([(lat, lon) for lat, lon, _ in rows], dtype=float)
    lat_indices = np.searchsorted(lat_edges, coordinates[:, 0], side="right") - 1
    lon_indices = np.searchsorted(lon_edges, coordinates[:, 1], side="right") - 1
    lat_indices = np.clip(lat_indices, 0, len(lat_edges) - 2)
    lon_indices = np.clip(lon_indices, 0, len(lon_edges) - 2)

    values = {}
    for lat_index, lon_index, (_, _, value) in zip(
        lat_indices, lon_indices, rows
    ):
        values.setdefault((lat_index, lon_index), []).append(float(value))
    return values


def _estimated_values(cells, cell_values):
    """Provide a continuous display while finer cells await Open-Meteo data.

    Estimates never replace database values. The response labels them so the
    browser can distinguish a temporary nearest-cached value from an observed
    one while bounded cache-miss requests fill the finer grid.
    """
    observed_cells = [cell for cell in cells if cell["index"] in cell_values]
    missing_cells = [cell for cell in cells if cell["index"] not in cell_values]
    if not observed_cells or not missing_cells:
        return {}

    observed_coordinates = np.array(
        [(cell["latitude"], cell["longitude"]) for cell in observed_cells],
        dtype=float,
    )
    observed_values = np.array(
        [np.mean(cell_values[cell["index"]]) for cell in observed_cells], dtype=float
    )
    missing_coordinates = np.array(
        [(cell["latitude"], cell["longitude"]) for cell in missing_cells],
        dtype=float,
    )
    coordinate_deltas = missing_coordinates[:, np.newaxis, :] - observed_coordinates
    nearest_indices = np.argmin(
        np.sum(np.square(coordinate_deltas), axis=2), axis=1
    )
    return {
        cell["index"]: float(observed_values[nearest_index])
        for cell, nearest_index in zip(missing_cells, nearest_indices)
    }


def _validate_viewport(climate_type, south, west, north, east, zoom):
    """Reject unsafe or nonsensical viewport requests before querying data."""
    if climate_type not in CLIMATE_TYPES:
        raise ValueError("Unsupported climate type")
    if not all(math.isfinite(value) for value in (south, west, north, east, zoom)):
        raise ValueError("Viewport values must be finite")
    if zoom < MIN_ZOOM:
        raise ValueError("Zoom must be non-negative")
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
        raise ValueError("Invalid viewport bounds")


def _query_weather_rows(con, date, climate_type, lat_edges, lon_edges):
    query = f"""
        SELECT l.lat, l.lon, d.{climate_type}
        FROM data AS d
        JOIN locations AS l ON l.loc_id = d.loc_id
        WHERE d.dates = %s
          AND l.lat BETWEEN %s AND %s
          AND l.lon BETWEEN %s AND %s
        ORDER BY l.lat, l.lon
    """
    with con.cursor() as cur:
        cur.execute(
            query,
            (
                date,
                lat_edges[0],
                lat_edges[-1],
                lon_edges[0],
                lon_edges[-1],
            ),
        )
        return cur.fetchall()


def _fetch_missing_cells(con, cells, month):
    """Fetch one bounded batch and cache every metric for each coordinate."""
    period = pd.Period(month, freq="M")
    fetched = 0
    for cell in cells[:MAX_FETCH_PER_VIEWPORT]:
        if get_data(
            con=con,
            location=(cell["latitude"], cell["longitude"]),
            date_start=period.start_time.strftime("%Y-%m-%d"),
            date_end=period.end_time.strftime("%Y-%m-%d"),
            meteo_types=DEFAULT_METEO_TYPES,
            insert_into_database=True,
            force_update_database=True,
        ):
            fetched += 1
    return fetched


def viewport_geojson(
    month,
    climate_type,
    south,
    west,
    north,
    east,
    zoom,
    fetch_missing=True,
):
    """Return bounded GeoJSON climate cells for one visible flat-map viewport."""
    _validate_viewport(climate_type, south, west, north, east, zoom)
    cells, lat_edges, lon_edges, lat_step, lon_step = _viewport_cells(
        south, west, north, east, zoom
    )
    date = f"{month}-01"

    with weather_db() as con:
        rows = _query_weather_rows(
            con, date, climate_type, lat_edges, lon_edges
        )
        cell_values = _bucket_rows(rows, lat_edges, lon_edges)
        missing = [cell for cell in cells if cell["index"] not in cell_values]
        cached_count = len(cells) - len(missing)
        fetched = 0
        if fetch_missing and missing:
            fetched = _fetch_missing_cells(con, missing, month)
            if fetched:
                rows = _query_weather_rows(
                    con, date, climate_type, lat_edges, lon_edges
                )
                cell_values = _bucket_rows(rows, lat_edges, lon_edges)

    estimates = _estimated_values(cells, cell_values)
    features = []
    for cell in cells:
        values = cell_values.get(cell["index"])
        estimated = not values
        value = estimates.get(cell["index"]) if estimated else sum(values) / len(values)
        if value is None:
            continue
        features.append(
            {
                "type": "Feature",
                "id": f"{cell['latitude']:.6f}:{cell['longitude']:.6f}",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [cell["west"], cell["south"]],
                            [cell["east"], cell["south"]],
                            [cell["east"], cell["north"]],
                            [cell["west"], cell["north"]],
                            [cell["west"], cell["south"]],
                        ]
                    ],
                },
                "properties": {
                    "value": value,
                    "latitude": cell["latitude"],
                    "longitude": cell["longitude"],
                    "source_count": len(values or []),
                    "estimated": estimated,
                },
            }
        )
    missing_count = sum(1 for cell in cells if cell["index"] not in cell_values)
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "latitude_step": lat_step,
            "longitude_step": lon_step,
            "cached": cached_count,
            "fetched": fetched,
            "missing": missing_count,
            "observed": len(cells) - missing_count,
            "tiles": len(cells),
        },
    }
