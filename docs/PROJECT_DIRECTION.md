# Project direction and publication rules

This document records requirements added after the original refactor plan. It
supplements, but does not replace or edit, `docs/REFACTOR.md`.

## Publication and provenance

- The refactor is an **AI-assisted derivative** made with **OpenAI Codex
  (GPT-5)**.
- The original, purely human-authored project is
  [iktCalT/climate](https://github.com/iktCalT/climate).
- Zijian owns every remote, push, pull request, and merge. Codex must not run
  remote Git or GitHub operations unless explicitly asked.

## Progressive, data-driven maps

The fixed 91×91 global grid and pre-rendered Folium image overlays are not the
desired long-term map experience. After the location cache-miss work, replace
or substantially redesign the mapping layer so zooming in increases the
precision of displayed climate data.

### Required behavior

- At higher zoom levels, reduce the latitude/longitude step size and present
  more detailed values rather than enlarging the same coarse raster image.
- Fetch only data needed for the requested viewport, zoom level, variable, and
  date. Prefer Open-Meteo or another suitable open climate-data source over
  prefetching the world at every resolution.
- Cache fetched values in PostgreSQL. The database remains the source of truth;
  generated web assets are disposable render caches.
- Use bounded requests, deduplication, and Open-Meteo rate limits. Never make
  a request per pixel or blanket-fetch a high-resolution global grid because a
  visitor zoomed in.
- Keep map interactions responsive: loading or missing data should be shown
  explicitly instead of silently interpolating from unrelated locations.

### Technical direction to evaluate

Folium can be replaced if another library better supports an interactive,
progressive map. The leading option to evaluate is **MapLibre GL JS** in the
Flask frontend with JSON or tile-like endpoints served by Flask/PostgreSQL.
It supports zoom-aware rendering and viewport requests. Leaflet is an
acceptable lighter alternative; Folium may remain only if it can provide the
same zoom-aware data loading efficiently.

The implementation should define a small map-data API, such as a request for
`bounds`, `zoom`, `month`, and `climate_type`. The server should choose a safe
sampling resolution for that request, return existing PostgreSQL values, and
queue or fetch a bounded set of missing points from the open provider. The
exact provider, resolution policy, and client library will be selected during
the map-redesign phase and documented in the README when implemented.
