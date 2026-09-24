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

## 10. Rate-aware prefetch pacing and fail-fast behavior

**Status:** Implemented on 2026-09-02; recorded before implementation.

The first live 100-location prefetch reached Open-Meteo's weighted minutely
limit after roughly 15 successful requests. A location count alone is not an
adequate request budget because the Climate API also weighs the requested time
span, variables, and models.

Pace all provider requests in the command-line prefetch with a conservative
default delay shared across locations and periods. Stop the batch immediately
when any provider request fails instead of rapidly attempting the remaining
locations; already committed ranges remain resumable through PostgreSQL.
Allow an explicit delay override for controlled operation and tests, display
the pacing policy before a live batch, and keep expected provider-limit errors
concise instead of printing full tracebacks.

## 11. Research a higher-capacity monthly climate data provider

**Status:** Provider research completed on 2026-09-23; integration is deferred
until a CDS account accepts the dataset licence and the change from CMIP6
climate-model output to ERA5 reanalysis is explicitly approved.

Evaluate alternatives to the current Open-Meteo Climate API before committing
to the remaining global prefetch. The preferred provider must offer a genuinely
free tier with a materially higher usable request or data-volume limit, use
HTTPS, have clear ownership and licensing, publish dependable documentation,
and be suitable for a public student project without unsafe credential or data
handling.

Fine-grained daily or hourly data is not required when monthly values can be
obtained directly. Compare candidates on global coverage, the 1950-to-present
window, mean/minimum/maximum temperature and precipitation availability,
monthly aggregation semantics, spatial resolution, rate limits, attribution,
long-term reliability, and compatibility with the PostgreSQL cache. Do not
replace Open-Meteo until the selected source and any differences in modelled
values have been documented and verified.

The evaluation selected Copernicus Climate Data Store ERA5 as the preferred
bulk-source candidate. ERA5 is global, covers 1940 to the present, is licensed
under CC BY, and supports queued API retrievals that are much better suited to
bulk work than thousands of point-by-point HTTP calls. It is not a drop-in
replacement: monthly mean temperature and precipitation can come from the
monthly product, but each month's highest and lowest daily temperature must be
derived from daily statistics based on hourly 2 m temperature. ERA5 is
also a reanalysis rather than the current two-model CMIP6 average. See
[`CLIMATE_PROVIDER_EVALUATION.md`](CLIMATE_PROVIDER_EVALUATION.md) for the
candidate comparison, field definitions, conversions, safeguards, and staged
integration plan. Open-Meteo remains the only active provider.

## 12. User-controlled map color scales

**Status:** Implemented on 2026-09-23; recorded before implementation.

Allow users to choose a color scale independently for temperature and
precipitation maps. Provide several understandable presets, including a broad
global scale and narrower regional scales, and allow a custom scale with
validated value bounds and colors. Use the existing map colors and previously
defined temperature/precipitation stops as the starting reference when
designing the presets rather than inventing unrelated defaults.

Every rendered map must show the active units, numeric range, color stops, and
legend. Temperature and precipitation need metric-appropriate presets and
validation; a precipitation scale must not silently reuse temperature bounds.

The map now provides four temperature presets (global extremes, temperate,
cold, and warm) and three precipitation presets (global daily mean, dry, and
wet). Custom scales accept minimum and maximum values plus low, middle, and
high colors, with separate safe bounds for each measurement family. The active
range, units, and every color stop remain visible above the map.

## 13. Manual-only scale changes

**Status:** Implemented on 2026-09-23; recorded before implementation.

Never rescale colors automatically in response to panning, zooming, changing a
date, or loading new data. Keep the selected scale fixed until the user chooses
another preset or edits the custom scale. Preserve the choice while the user is
working so identical colors retain identical meanings and the map does not
become visually misleading.

Scale selection is stored separately for temperature and precipitation in the
browser. Map movement and data responses never write or recalculate it; only a
preset selection or a successful custom-scale submission changes the active
scale. The saved choice survives date changes and page reloads.

## 14. Same-scale multi-date comparison

**Status:** Implemented on 2026-09-24; recorded before implementation.

Add a comparison mode in which users select two or more months and view the
same temperature or precipitation metric side by side. Comparison panels must
share one user-selected color scale and legend; do not allow individual panels
to auto-scale or use different bounds. Keep viewports synchronized where
practical, label every date clearly, and preserve the existing distinction
between direct, nearby-cache, and pending/missing values so apparent
differences are not created by inconsistent rendering.

Limit one comparison to two through four distinct months. This keeps panels
readable on an ordinary screen and bounds the number of PostgreSQL and
Open-Meteo requests caused by a settled viewport. Each panel may load its own
month, but synchronized viewport movement must not create duplicate requests
for the same panel and position.

The Maps selector now lets users add up to three comparison months to the
primary month. The resulting two-to-four-panel view labels each date, uses one
shared preset or custom scale and legend, and synchronizes center, zoom,
bearing, and pitch from whichever panel the user moves. Every panel retains
its own load status and direct/nearby/estimated rendering, while debounced
per-panel requests prevent synchronized movement from repeatedly loading the
same final viewport.

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
10. Rate-aware pacing and fail-fast handling for the resumable prefetch.
11. Research and select a safe, free, higher-capacity monthly climate provider.
12. Add temperature and precipitation scale presets plus validated custom scales.
13. Keep color-scale changes entirely manual and stable across map interactions.
14. Add synchronized, same-scale side-by-side comparison for two or more dates.
