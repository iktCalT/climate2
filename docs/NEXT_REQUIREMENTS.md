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

## 7. Dense viewport grid and city-scale zoom limit

**Status:** Implemented on 2026-08-30; recorded before implementation.

The current safety cap can enlarge map cells until a typical viewport contains
only a few dozen rows and columns. Instead, render at least **90 latitude rows
by 90 longitude columns** for every normal visible viewport so the climate
surface remains visually fine-grained before and after zooming.

Keep PostgreSQL and nearby-cache reuse as the primary data sources. Increasing
the display grid must not cause thousands of Open-Meteo calls: retain the
existing maximum of 12 cache-miss fetches per settled viewport, and use chunked
NumPy nearest-neighbor work so an 8,100-plus-cell response does not allocate an
unbounded distance matrix. Distribute that bounded fetch batch across the
missing viewport cells instead of taking 12 adjacent row-major cells from one
edge, so each provider call improves a different part of the visible map.

Cap both the browser map and API at zoom level 10. This keeps a large-city area,
such as New York City, within roughly two ordinary map screens while still
allowing the adaptive 90-by-90 grid to provide small cells at the closest
supported scale.

## 8. Bounded map resolution and faster foreground fetches

**Status:** Implemented on 2026-08-30; recorded before implementation.

This requirement corrects and supersedes the always-dense 90-by-90 behavior in
requirement 7. Use 2-degree latitude by 4-degree longitude cells at overview
scale. Across the entire globe, that produces 90 latitude rows by 90 longitude
columns, staying within the 91-by-91 ceiling without distorting cell size.

As the user zooms in, use a smooth rectangular-cell resolution curve instead
of preserving 90 rows and columns. Reduce both dimensions by a factor of 1.5
per added zoom level while the geographic viewport shrinks by roughly a factor
of 2, and stop permanently at 0.5-degree latitude by 1-degree longitude cells.
This preserves the 1:2 latitude/longitude grid aspect and makes the number of
visible cells trend downward at every zoom level. Keep the city-scale maximum
zoom of 10.

The measured response delay is dominated by synchronous Open-Meteo cache-miss
work, not PostgreSQL grid generation. Reduce the foreground cache-miss batch
from 12 to at most 4 distributed locations per settled viewport. Continue to
cache every fetched metric in PostgreSQL; larger intentional cache population
belongs in the administrator pre-fetch flow.

## 9. Resumable edge-period PostgreSQL prefetch

**Status:** Implemented on 2026-09-02; recorded before implementation.

Populate the canonical 91-by-91 global map grid for the edge periods
**1950–1953** and **2023–2026** without refetching already complete climate
months. PostgreSQL must be the durable checkpoint: each run determines which
locations and months already contain all four metrics, fetches only missing
contiguous ranges, and commits successful ranges independently so an
interruption does not discard earlier progress.

Provide a command-line prefetch job with a conservative per-run location cap,
stable traversal order, progress reporting, and a dry-run mode. Re-running the
same command must safely resume from PostgreSQL, including after a provider
failure. Keep the canonical 2-degree latitude by 4-degree longitude grid and
the existing Open-Meteo model/metric choices; do not store a separate mutable
checkpoint file or contact Open-Meteo for complete locations.

## Delivery order

1. Tile-grid geometry and flat map.
2. Finer zoom sampling and location-history verification.
3. Newest-month support.
4. User roles and administrator ingest.
5. Home and References redesign.
6. Neighbor-aware cache reuse before further map API expansion.
7. Dense 90-by-90 viewport grid with a city-scale zoom limit.
8. Bounded 2°×4° to 0.5°×1° map resolution and faster foreground fetches.
9. Resumable PostgreSQL prefetch for the 1950–1953 and 2023–2026 edge periods.
