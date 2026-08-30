"""Viewport-sized climate data for the interactive MapLibre map."""

import math

import numpy as np
import pandas as pd

from db import CLIMATE_TYPES, weather_db
from helpers_data import DEFAULT_METEO_TYPES, get_data

MIN_VIEWPORT_ROWS = 90
MIN_VIEWPORT_COLUMNS = 90
MAX_VIEWPORT_POINTS = 10_000
MAX_FETCH_PER_VIEWPORT = 12
MIN_ZOOM = 0
MAX_ZOOM = 10
NEIGHBOR_REUSE_RADIUS_CELLS = 1.5
NEIGHBOR_REUSE_CHUNK_SIZE = 128
NEAREST_VALUE_CHUNK_SIZE = 128


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
    """Return a dense, bounded rectangular mesh covering the visible map."""
    zoom_lat_step, zoom_lon_step = step_for_zoom(zoom)
    lat_step = min(
        zoom_lat_step,
        (north - south) / MIN_VIEWPORT_ROWS,
    )
    lon_step = min(
        zoom_lon_step,
        (east - west) / MIN_VIEWPORT_COLUMNS,
    )
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
    rows = [
        (lat, lon, value)
        for lat, lon, value in rows
        if value is not None
        and lat_edges[0] <= lat <= lat_edges[-1]
        and lon_edges[0] <= lon <= lon_edges[-1]
    ]
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


def _nearby_cached_values(cells, rows, cell_values, lat_step, lon_step):
    """Reuse a cached point in this or a neighboring zoom-scaled cell."""
    cached_rows = [
        (lat, lon, value) for lat, lon, value in rows if value is not None
    ]
    missing_cells = [cell for cell in cells if cell["index"] not in cell_values]
    if not cached_rows or not missing_cells:
        return {}

    scale = np.array([lat_step, lon_step], dtype=float)
    cached_coordinates = (
        np.asarray([(lat, lon) for lat, lon, _ in cached_rows], dtype=float) / scale
    )
    cached_values = np.asarray([value for _, _, value in cached_rows], dtype=float)
    reused = {}
    maximum_distance_squared = NEIGHBOR_REUSE_RADIUS_CELLS**2

    for start in range(0, len(missing_cells), NEIGHBOR_REUSE_CHUNK_SIZE):
        chunk = missing_cells[start : start + NEIGHBOR_REUSE_CHUNK_SIZE]
        chunk_coordinates = (
            np.asarray(
                [(cell["latitude"], cell["longitude"]) for cell in chunk],
                dtype=float,
            )
            / scale
        )
        deltas = chunk_coordinates[:, np.newaxis, :] - cached_coordinates
        distances_squared = np.sum(np.square(deltas), axis=2)
        nearest_indices = np.argmin(distances_squared, axis=1)
        nearest_distances = distances_squared[
            np.arange(len(chunk)), nearest_indices
        ]
        for cell, nearest_index, distance_squared in zip(
            chunk, nearest_indices, nearest_distances
        ):
            if distance_squared <= maximum_distance_squared:
                reused[cell["index"]] = float(cached_values[nearest_index])
    return reused


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
    estimates = {}
    for start in range(0, len(missing_cells), NEAREST_VALUE_CHUNK_SIZE):
        chunk = missing_cells[start : start + NEAREST_VALUE_CHUNK_SIZE]
        missing_coordinates = np.asarray(
            [(cell["latitude"], cell["longitude"]) for cell in chunk],
            dtype=float,
        )
        coordinate_deltas = (
            missing_coordinates[:, np.newaxis, :] - observed_coordinates
        )
        nearest_indices = np.argmin(
            np.sum(np.square(coordinate_deltas), axis=2), axis=1
        )
        estimates.update(
            {
                cell["index"]: float(observed_values[nearest_index])
                for cell, nearest_index in zip(chunk, nearest_indices)
            }
        )
    return estimates


def _validate_viewport(climate_type, south, west, north, east, zoom):
    """Reject unsafe or nonsensical viewport requests before querying data."""
    if climate_type not in CLIMATE_TYPES:
        raise ValueError("Unsupported climate type")
    if not all(math.isfinite(value) for value in (south, west, north, east, zoom)):
        raise ValueError("Viewport values must be finite")
    if zoom < MIN_ZOOM:
        raise ValueError("Zoom must be non-negative")
    if zoom > MAX_ZOOM:
        raise ValueError(f"Zoom must not exceed {MAX_ZOOM}")
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
        raise ValueError("Invalid viewport bounds")


def _query_weather_rows(
    con,
    date,
    climate_type,
    lat_edges,
    lon_edges,
    latitude_padding=0,
    longitude_padding=0,
):
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
                max(-90, lat_edges[0] - latitude_padding),
                min(90, lat_edges[-1] + latitude_padding),
                max(-180, lon_edges[0] - longitude_padding),
                min(180, lon_edges[-1] + longitude_padding),
            ),
        )
        return cur.fetchall()


def _fetch_missing_cells(con, cells, month):
    """Fetch one bounded batch and cache every metric for each coordinate."""
    period = pd.Period(month, freq="M")
    fetched = 0
    fetch_count = min(len(cells), MAX_FETCH_PER_VIEWPORT)
    if fetch_count == len(cells):
        selected_cells = cells
    else:
        selected_indices = np.linspace(
            0,
            len(cells) - 1,
            num=fetch_count,
            dtype=int,
        )
        selected_cells = [cells[index] for index in selected_indices]

    for cell in selected_cells:
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
    latitude_padding = lat_step * NEIGHBOR_REUSE_RADIUS_CELLS
    longitude_padding = lon_step * NEIGHBOR_REUSE_RADIUS_CELLS

    with weather_db() as con:
        rows = _query_weather_rows(
            con,
            date,
            climate_type,
            lat_edges,
            lon_edges,
            latitude_padding,
            longitude_padding,
        )
        cell_values = _bucket_rows(rows, lat_edges, lon_edges)
        reused_values = _nearby_cached_values(
            cells, rows, cell_values, lat_step, lon_step
        )
        satisfied = set(cell_values) | set(reused_values)
        missing = [cell for cell in cells if cell["index"] not in satisfied]
        cached_count = len(satisfied)
        fetched = 0
        if fetch_missing and missing:
            fetched = _fetch_missing_cells(con, missing, month)
            if fetched:
                rows = _query_weather_rows(
                    con,
                    date,
                    climate_type,
                    lat_edges,
                    lon_edges,
                    latitude_padding,
                    longitude_padding,
                )
                cell_values = _bucket_rows(rows, lat_edges, lon_edges)
                reused_values = _nearby_cached_values(
                    cells, rows, cell_values, lat_step, lon_step
                )

    displayed_values = dict(cell_values)
    displayed_values.update(
        {index: [value] for index, value in reused_values.items()}
    )
    estimates = _estimated_values(cells, displayed_values)
    features = []
    for cell in cells:
        values = cell_values.get(cell["index"])
        reused_value = reused_values.get(cell["index"])
        if values:
            value = sum(values) / len(values)
            source = "direct_cache"
            source_count = len(values)
        elif reused_value is not None:
            value = reused_value
            source = "nearby_cache"
            source_count = 1
        else:
            value = estimates.get(cell["index"])
            source = "display_estimate"
            source_count = 0
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
                    "source_count": source_count,
                    "source": source,
                    "estimated": source != "direct_cache",
                },
            }
        )
    satisfied = set(cell_values) | set(reused_values)
    missing_count = len(cells) - len(satisfied)
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "latitude_step": lat_step,
            "longitude_step": lon_step,
            "cached": cached_count,
            "fetched": fetched,
            "missing": missing_count,
            "observed": len(satisfied),
            "direct": len(cell_values),
            "reused_nearby": len(reused_values),
            "rows": len(lat_edges) - 1,
            "columns": len(lon_edges) - 1,
            "tiles": len(cells),
        },
    }
