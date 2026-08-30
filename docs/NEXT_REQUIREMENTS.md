# Next requirements

This document records the next agreed work after the current PostgreSQL and
MapLibre refactor. It supplements `docs/REFACTOR.md`; it does not replace it.

## 1. Correct and improve map tiles

The current MapLibre viewport tiles can render as separated vertical bands
(shown in the attached screenshot). Correct the grid geometry so adjacent
latitude and longitude cells form a tight two-dimensional mesh with no gaps or
overlaps. Do this before adding more map features.

The map must use a **flat** projection, not the current globe/sphere style.

At higher zoom, decrease tile size and request more climate samples for the
visible viewport. Keep the request budget bounded and show loading/missing
areas honestly rather than inventing values. The goal is genuinely more data
points, not merely enlarged tiles.

## 2. Location history

Keep and verify the location page flow: a visitor supplies latitude/longitude,
the app serves temperature history from **1951 through the current month**,
fetching missing Open-Meteo data and saving it in PostgreSQL first.

## 3. Current-month map support

Allow the Maps page to select the newest available month, through the current
month when Open-Meteo provides it. Do not keep the fixed 2023 end date. The UI
and server validation must use the same availability rule.

## 4. User roles and manual ingest

Maintain a user system in which normal visitors can browse climate data without
administrative access. Administrators can manually pre-fetch Open-Meteo data
for a selected area/date range into the local PostgreSQL climate cache. Define
and enforce an administrator role; do not make registration automatically grant
administrator privileges.

## 5. Later page refreshes

Refresh the **Home** and **References** pages after the map, location, current
month, and user-role work is complete. Treat this as a reminder, not current
implementation scope.

## 6. Neighbor-aware map cache reuse

**Status:** Implemented on 2026-08-30; recorded before implementation.

Reduce Open-Meteo usage by allowing a map tile to reuse a sufficiently nearby
PostgreSQL observation. A cached observation does not need to match the tile
center or the map's zooming center exactly.

The acceptable neighbor distance must shrink as zoom increases. Query a small
padded area around the viewport so edge tiles can reuse nearby cached points,
and distinguish reused/estimated values from direct observations in map
metadata. Only call Open-Meteo when no cached observation is close enough for
the current zoom level. Keep the existing bounded request budget.

## Delivery order

1. Tile-grid geometry and flat map.
2. Finer zoom sampling and location-history verification.
3. Newest-month support.
4. User roles and administrator ingest.
5. Home and References redesign.
6. Neighbor-aware cache reuse before further map API expansion.
