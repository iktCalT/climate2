"""Pure coordinate selection for public NOAA CORe location histories."""

import math
from dataclasses import dataclass


EARTH_RADIUS_KM = 6371.0
NOAA_LATITUDES = tuple(range(-90, 91, 2))
# +180 is the same meridian as -180; use one stable cache identity.
NOAA_LONGITUDES = tuple(range(-180, 180, 4))


@dataclass(frozen=True)
class LocationSample:
    latitude: float
    longitude: float
    distance_km: float


def sample_noaa_location(latitude, longitude):
    """Round each coordinate to the canonical grid and return its distance.

    Latitude and circular longitude are rounded independently, so the chosen
    point need not be the nearest by great-circle distance. Ties choose the
    numerically smaller coordinate. A sampled pole uses 0° longitude because
    all meridians meet there.
    """
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Invalid latitude/longitude") from error
    if not math.isfinite(latitude) or not math.isfinite(longitude):
        raise ValueError("Latitude/longitude must be finite")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Latitude/longitude out of range")

    sampled_lat = min(NOAA_LATITUDES, key=lambda value: (abs(value - latitude), value))
    if abs(sampled_lat) == 90:
        sampled_lon = 0
    else:
        sampled_lon = min(
            NOAA_LONGITUDES,
            key=lambda value: (abs((longitude - value + 180) % 360 - 180), value),
        )

    lat_delta = math.radians(sampled_lat - latitude)
    lon_delta = math.radians((sampled_lon - longitude + 180) % 360 - 180)
    haversine = (
        math.sin(lat_delta / 2) ** 2
        + math.cos(math.radians(latitude))
        * math.cos(math.radians(sampled_lat))
        * math.sin(lon_delta / 2) ** 2
    )
    distance_km = 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, max(0.0, haversine))))
    return LocationSample(float(sampled_lat), float(sampled_lon), distance_km)
