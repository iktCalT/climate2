import folium
from matplotlib import colormaps
from matplotlib.colors import Normalize
import numpy as np
import pandas as pd
import sqlite3

from db import CLIMATE_TYPES, weather_db


REPEAT = 2
SHAPE = (91, 91)
MAX_TEMP = 40
MIN_TEMP = -20
MAX_PRECIP = 10
MIN_PRECIP = 0
OPACITY = 0.5


def add_bounds(map):
    # https://python-visualization.github.io/folium/latest/user_guide/raster_layers/image_overlay.html
    image = np.zeros((361, 361))
    image[0, :] = 1.0
    image[360, :] = 1.0
    image[:, 0] = 1.0
    image[:, 360] = 1.0
    folium.raster_layers.ImageOverlay(
        name="bounds",
        image=image,
        bounds=[[-90, -180], [90, 180]],
        colormap=lambda x: (0, 0, 0, x),
    ).add_to(map)


def add_legend(map, climate_type):
    if climate_type == "precip":
        max_data = str(MAX_PRECIP) + "mm"
        min_data = str(MIN_PRECIP) + "mm"
        title = "Precipitation per day (mm)"
        colormap = "Blues"
    elif climate_type in ["temp_mean", "temp_max", "temp_min"]:
        max_data = str(MAX_TEMP) + "°C"
        min_data = str(MIN_TEMP) + "°C"
        title = f"{climate_type[5:].title()} Temperature (°C)"
        colormap = "coolwarm"
    else:
        return False
    cm = colormaps[colormap]
    r, g, b, a = cm(0.0)
    start = f"rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)}, {OPACITY})"
    r, g, b, a = cm(1.0)
    end = f"rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)}, {OPACITY})"
    legend_html = f"""
    <div style="
        position: fixed; 
        bottom: 30px; left: 30px; width: 120px; height: 230px; 
        background-color: white; z-index:999; font-size:14px; border:2px solid grey; padding: 10px;">
        
        <div style="float: left; height: 200px; width: 20px; text-align: center; 
                    writing-mode: vertical-rl; transform: rotate(180deg)">
            {title}
        </div>
        <div style="float: left; background: linear-gradient(to top, {start}, {end}); 
                    height: 200px; width: 20px; margin: 0 5px;">
        </div>
        <div style="float: left; line-height: 18px; height: 200px;">
            <div style="position:fixed; height: 200px;">
                <div style="position: absolute; top: 0">{max_data}</div>
                <div style="position: absolute; bottom: 0">{min_data}</div>
            </div>
        </div>
        
    </div>
    """
    map.get_root().html.add_child(folium.Element(legend_html))


def _colormap_for(climate_type):
    if climate_type == "precip":
        return "Blues"
    if climate_type in ["temp_mean", "temp_max", "temp_min"]:
        return "coolwarm"
    print("Invalid climate_type")
    return None


def draw_multi_layers(start_date, end_date, climate_type):
    colormap = _colormap_for(climate_type)
    if colormap is None:
        return False
    dates = generate_dates(start_date=start_date, end_date=end_date)
    m = folium.Map(
        location=(0, 0),
        zoom_start=2,
        min_zoom=2,
        tiles="cartodb positron",
    )
    add_bounds(m)
    add_legend(m, climate_type)

    with weather_db() as con:
        for date in dates:
            strdate = date.strftime("%Y-%m-%d")
            strmonth = date.strftime("%Y-%m")
            lats, lons, data = fetch_data(SHAPE, strdate, climate_type, con=con)
            data_r = np.tile(data, (1, (2 * REPEAT + 1)))
            cm = colormaps[colormap]
            colored_data = cm(normalize_data(data_r, climate_type))

            folium.raster_layers.ImageOverlay(
                name=strmonth + "_" + climate_type,
                image=colored_data,
                bounds=[
                    [lats.min(), lons.min() - REPEAT * 360],
                    [lats.max(), lons.max() + REPEAT * 360],
                ],
                mercator_project=True,
                opacity=OPACITY,
            ).add_to(m)

    folium.LayerControl().add_to(m)
    m.save("static/weather_data/climate.html")


def draw_multi_maps(start_date, end_date, climate_type):
    colormap = _colormap_for(climate_type)
    if colormap is None:
        return False
    dates = generate_dates(start_date=start_date, end_date=end_date)

    with weather_db() as con:
        for date in dates:
            m = folium.Map(
                location=(0, 0),
                zoom_start=2,
                min_zoom=2,
                tiles="cartodb positron",
            )
            add_bounds(m)
            add_legend(m, climate_type)
            strdate = date.strftime("%Y-%m-%d")
            strmonth = date.strftime("%Y-%m")
            lats, lons, data = fetch_data(SHAPE, strdate, climate_type, con=con)
            data_r = np.tile(data, (1, (2 * REPEAT + 1)))
            cm = colormaps[colormap]
            colored_data = cm(normalize_data(data_r, climate_type))

            folium.raster_layers.ImageOverlay(
                name=strmonth + "_" + climate_type,
                image=colored_data,
                bounds=[
                    [lats.min(), lons.min() - REPEAT * 360],
                    [lats.max(), lons.max() + REPEAT * 360],
                ],
                mercator_project=True,
                opacity=OPACITY,
            ).add_to(m)

            folium.LayerControl().add_to(m)
            m.save("static/weather_data/" + strmonth + "_" + climate_type + ".html")


def fetch_data(shape=(91, 91), date="1950-01-01", climate_type="temp_mean", con=None):
    """Load one month of a climate variable onto the lat/lon grid with a single query."""
    if climate_type not in CLIMATE_TYPES:
        raise ValueError(f"Unsupported climate_type: {climate_type}")

    nlats, nlons = shape
    lats = np.linspace(-90, 90, nlats)
    lons = np.linspace(-180, 180, nlons)
    grid = np.full((nlats, nlons), np.nan)

    query = f"""
        SELECT l.lat, l.lon, d.{climate_type}
        FROM data AS d
        JOIN locations AS l ON l.loc_id = d.loc_id
        WHERE DATE(d.dates) = ?
    """
    try:
        with weather_db(con) as db:
            rows = db.execute(query, (date,)).fetchall()
    except sqlite3.Error as e:
        print(f"Error while fetching weather data: {e}")
        return lats, lons, grid

    if not rows:
        return lats, lons, grid

    row_lats = np.fromiter((row[0] for row in rows), dtype=float, count=len(rows))
    row_lons = np.fromiter((row[1] for row in rows), dtype=float, count=len(rows))
    values = np.fromiter(
        (np.nan if row[2] is None else row[2] for row in rows),
        dtype=float,
        count=len(rows),
    )

    dlat = (lats[-1] - lats[0]) / (nlats - 1) if nlats > 1 else 1.0
    dlon = (lons[-1] - lons[0]) / (nlons - 1) if nlons > 1 else 1.0
    i = np.rint((row_lats - lats[0]) / dlat).astype(int)
    j = np.rint((row_lons - lons[0]) / dlon).astype(int)
    on_grid = (i >= 0) & (i < nlats) & (j >= 0) & (j < nlons)
    grid[i[on_grid], j[on_grid]] = values[on_grid]
    return lats, lons, grid


def generate_dates(start_date, end_date):
    dates = pd.date_range(start=start_date, end=end_date, freq="MS")
    return dates


def normalize_data(data, climate_type):
    if climate_type == "precip":
        max_data = MAX_PRECIP
        min_data = MIN_PRECIP
    elif climate_type in ["temp_mean", "temp_max", "temp_min"]:
        max_data = MAX_TEMP
        min_data = MIN_TEMP
    else:
        return False
    norm = Normalize(vmin=min_data, vmax=max_data)
    return norm(data)


if __name__ == "__main__":
    draw_multi_maps("1950-01-01", "1950-01-01", "temp_max")
    draw_multi_maps("2023-01-01", "2023-01-01", "temp_max")
    draw_multi_maps("1950-07-01", "1950-07-01", "temp_max")
    draw_multi_maps("2023-07-01", "2023-07-01", "temp_max")
    draw_multi_layers("2023-01-01", "2023-07-01", "temp_mean")
