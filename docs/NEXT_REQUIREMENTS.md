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

**Status:** Initial research completed on 2026-09-23 and updated on 2026-09-24.
The initial ERA5 choice is superseded by the anonymous NOAA CORe selection in
requirement 16; integration remains deferred pending importer validation.

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

The initial evaluation selected Copernicus Climate Data Store ERA5, but it
requires an account, dataset-licence acceptance, and private API token. The
2026-09-24 update instead selected NOAA CORe, an official global reanalysis
available anonymously over HTTPS from 1950 to near real time and documented by
NOAA as public domain. It is still not a drop-in replacement: temperature
extrema must be derived from daily records, units and Gaussian-grid coordinates
must be validated, and reanalysis values must remain separate from the current
two-model CMIP6 average. See [`CLIMATE_PROVIDER_EVALUATION.md`](CLIMATE_PROVIDER_EVALUATION.md)
for the candidate comparison, field definitions, conversions, safeguards, and
staged integration plan. Open-Meteo remains the only active provider.

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

## 15. Provider-scoped climate rows

**Status:** Implemented on 2026-09-24; recorded before implementation.

Prepare the PostgreSQL climate cache for a future reanalysis bulk-import path
without changing the active website provider. Every stored monthly climate row
must identify its provider and product family so NOAA CORe or another
reanalysis cannot be silently mixed with the existing Open-Meteo CMIP6 model
average.

Existing rows and every current Open-Meteo write must be labelled consistently.
All current website, map, location-history, administrator, migration, and
prefetch reads must explicitly select the active Open-Meteo provider. The
database key must permit two providers to store values for the same location
and month while preventing duplicate rows within one provider. Expose the
selected provider in map response metadata so the UI data contract remains
auditable.

This is schema and provenance groundwork only. Do not contact CDS, request or
store a token, import ERA5 files, replace Open-Meteo, or combine values from
different provider families. Existing installations must be upgraded
idempotently by the normal schema setup command, and fresh installations must
receive the same constraints and defaults.

The `data` table now uses `(loc_id, dates, provider)` as its primary key, with
legacy and current writes labelled `open_meteo_cmip6`. Location history, maps,
administrator ingestion, legacy migration, and resumable prefetch queries all
select that active family explicitly. Map JSON and the visible panel status
report the provider, while a database integration test verifies that a second
provider can coexist without affecting active-site results. The schema upgrade
was run twice successfully to verify repeatability; no CDS request, token, or
ERA5 value was introduced.

## 16. Anonymous NOAA CORe bulk source

**Status:** Implemented and live-validated on 2026-09-24. Open-Meteo remains
the active website provider pending a separate comparison and activation
decision.

Replace the deferred, account-gated ERA5 bulk-source plan with NOAA's
Conventional Observation Reanalysis (CORe) archive on the NOAA Open Data
Dissemination Program. The selected source must require no user account, API
key, private token, or click-through dataset-licence acceptance. Use only the
official NOAA HTTPS archive and document the dataset's public-domain status,
operational limitations, attribution, and retrieval behavior in both the
README and website References page.

CORe is suitable because its global reanalysis spans 1950 to near real time,
offers monthly and daily ensemble-mean products, and can be retrieved as
individual indexed GRIB records rather than thousands of point API calls. The
application does not need CORe's full native spatial precision: an importer
must explicitly map its Gaussian grid onto the existing canonical 2-degree by
4-degree points, validate longitude and pole handling, and avoid presenting
the downsampled result as station observations.

Preserve the existing four-metric monthly contract. Use monthly 2 m
temperature and surface precipitation-rate records for `temp_mean` and
`precip`. CORe's monthly high/low records are averages of daily extrema, not
the application's monthly highest and lowest daily values, so derive
`temp_max` and `temp_min` from the daily CORe extrema records before writing a
month. Convert and validate units explicitly, store rows under a new
`noaa_core` provider family, and never mix them with `open_meteo_cmip6` rows.

PostgreSQL remains the resumable checkpoint. Import bounded date chunks, use
NOAA index byte ranges to avoid downloading unrelated fields, commit only
validated complete months, and make reruns skip existing complete
provider-scoped rows. Do not activate CORe for foreground cache misses or site
reads until a separately reviewed sample confirms field selection, units,
coordinates, missing-value handling, and representative land, ocean, polar,
and dateline results.

The command-line importer now retrieves indexed byte ranges with bounded
retries, decodes GRIB2 with ECMWF ecCodes, validates metadata and values,
nearest-samples to all 8,281 canonical points, and atomically upserts one month
under `noaa_core`. Complete calendar months are selected in stable order, one
per run by default and at most 12; `--dry-run` never contacts NOAA and
`--validate-only` never writes PostgreSQL. Live validation succeeded for
January 1950 and August 2026. A January 1950 write followed by an immediate
dry run confirmed that PostgreSQL recognizes and skips the complete month.
Website reads remain explicitly scoped to `open_meteo_cmip6`.

## 17. Read-only provider comparison report

**Status:** Implemented on 2026-09-24; representative review completed on
2026-09-25. Activation is deliberately deferred.

Add a deterministic command-line report that compares provider-scoped NOAA
CORe and active Open-Meteo rows already present in PostgreSQL. The report must
not contact either provider, mutate the database, infer approval from a numeric
threshold, or change the website's active provider. It is evidence for a
separate human activation decision, not an automatic migration.

For each explicitly requested complete month, report each provider's canonical
grid coverage, the count of coordinate/month pairs available from both, and
signed and absolute differences for all four monthly metrics. Include
representative canonical land, ocean, polar, and both sides of the dateline so
coordinate handling and missing samples remain visible. A missing provider,
month, metric, or representative row must appear as incomplete evidence rather
than being silently omitted.

Keep the comparison bounded to at most 12 months per run, use stable ordering
and machine-testable pure formatting/statistics helpers, and print Markdown to
standard output so a reviewer can save a report deliberately without adding
generated database contents to Git. The report must explain that CORe
reanalysis and the Open-Meteo two-model CMIP6 average are different products;
differences are expected and do not by themselves prove that either source is
incorrect. CORe activation still requires a separately recorded review and an
explicit provider switch.

The `compare_climate_providers.py` command now opens a read-only PostgreSQL
transaction, filters out non-canonical user locations, and prints deterministic
Markdown for up to 12 complete months. Coverage, per-metric signed and absolute
deltas, missing evidence, and land, ocean, polar, and dateline samples are all
visible. Live reports compared all 8,281 canonical rows for January 1950,
leap-month February 1952, and July 2023. August 2026 compared all six required
land, ocean, polar, and dateline samples without attempting an Open-Meteo
global refill.

The review confirms that retrieval, units, dates, cyclic coordinates, poles,
and representative values are coherent, but it does not justify an immediate
provider switch. CORe reanalysis and the active two-model CMIP6 average show
material expected differences, especially for precipitation and temperature
extrema. The resumable local import subsequently completed all 92 requested
months across 1950–1953 and 2023–2026, but coverage alone does not make these
different products interchangeable. Keep `open_meteo_cmip6` active and keep
the provider families separate until a new requirement explicitly decides how
foreground cache misses and provider activation should work.

## 18. Exact NOAA daily-extrema archive-gap fallback

**Status:** Implemented and live-validated on 2026-09-25 after the official
May 19, 2026 daily flux index was found to omit both 2 m temperature extrema.

Keep the NOAA CORe importer resumable when a daily aggregate file omits both
required temperature-extrema records but the official 3-hourly archive still
contains the corresponding 0–3 hour minimum and maximum fields. In that narrow
case, retrieve all eight official 3-hourly flux files for the affected UTC day,
decode their exact interval extrema with the same metadata and grid validation,
and reduce those fields to the daily minimum and maximum before continuing the
existing monthly aggregation. This is an archive-gap recovery path, not an
instantaneous-temperature approximation.

Use the fallback only when the daily index contains neither required extrema.
If only one daily field is missing, any 3-hourly file or extrema record is
missing, metadata or coordinates disagree, or a download fails, reject the
month and leave PostgreSQL unchanged. Do not skip the day, interpolate it, or
silently substitute the daily mean. Log the affected date so operators can
distinguish a verified archive gap from an ordinary failure. Cover both the
successful exact fallback and incomplete-fallback rejection with tests, then
live-validate May 2026 before resuming the bounded edge-period import.

The importer now checks the failed daily index and enters the fallback only
when both required records have a match count of zero. It downloads the exact
minimum and maximum interval records from all eight official 3-hourly files,
applies the existing date, statistic, unit, grid, coordinate, and missing-value
validation, and reduces them to one daily pair. Tests verify the complete path
and fail-closed behavior when an interval is unavailable. May 2026 passed a
live no-write validation through this path and was then committed atomically;
June and July followed normally. A final dry run reported all 92 requested
edge-period months complete.

## 19. Explicit NOAA full-history backfill

**Status:** Implemented on 2026-09-25 after the two recorded edge periods
reached 92 of 92 complete months.

Add an explicit importer period for every complete calendar month from January
1950 through the latest complete month. This is the next prerequisite for any
future NOAA activation because edge-period coverage alone cannot serve the
website's advertised middle decades, and filling missing months synchronously
during a visitor request would be too slow. The full-history selection must be
opt-in: keep the existing two edge periods as the default so an ordinary
rerun does not unexpectedly expand into a multi-year archive job.

Reuse the existing bounded batch limit, stable chronological ordering,
provider-scoped PostgreSQL completion checkpoint, month-atomic commits,
metadata validation, and exact daily-extrema fallback. The moving end of the
period must always be the latest complete month, with `--through` still able to
set an earlier stopping point. A dry run must report progress without
contacting NOAA or changing PostgreSQL. Document the command and the remaining
activation boundary in the README, provider evaluation, and website References
page. Do not switch active site reads or mix provider families as part of this
backfill capability.

The importer now accepts `--period 1950-present` and selects January 1950
through the latest complete month, or an earlier `--through` bound. It retains
the existing one-month default and 12-month maximum batch, while an invocation
without `--period` still selects only the two edge periods. Unit tests cover
the dynamic end, explicit opt-in, and earlier bound. README, provider review,
home-page status, and References copy describe the full-history prerequisite;
active reads remain `open_meteo_cmip6`. A live dry run reported 92 of 920
months complete and selected January–December 1954 as the first bounded batch.
All 12 months validated and committed atomically; the follow-up checkpoint is
104 of 920 complete months.

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
15. Scope every climate cache row and read to an explicit provider before reanalysis integration.
16. Add and validate a resumable NOAA CORe bulk importer without changing the active provider.
17. Generate a bounded, read-only CORe-versus-Open-Meteo comparison report before any activation decision.
18. Recover verified daily-extrema archive gaps from exact official 3-hourly extrema without approximation.
19. Add an explicit, bounded, resumable NOAA backfill for January 1950 through the latest complete month.
