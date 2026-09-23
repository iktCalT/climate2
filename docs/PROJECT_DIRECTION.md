# Project direction and publication rules

This document records requirements added after the original refactor plan. It
supplements, but does not replace or edit, `docs/REFACTOR.md`.

## Publication and provenance

- The refactor is an **AI-assisted derivative** made with **OpenAI Codex
  (GPT-5)**.
- The original project, [iktCalT/climate](https://github.com/iktCalT/climate),
  was implemented by its human author as a CS50 final project with substantial
  guidance from ChatGPT.
- The user owns every remote, push, pull request, and merge. Codex may use
  remote Git or GitHub operations only for `iktCalT/climate2`, as explicitly
  authorized by the user.

## External-source attribution

Whenever the project uses or depends on an external package, API, webpage,
dataset, image, icon, font, code sample, media file, or other third-party
resource, cite it in both the repository `README.md` and the website's
References page. Add or update those citations in the same change that
introduces the external resource.

Prefer the original creator, provider, package documentation, or canonical
project page over an aggregator. Include a direct link, explain what the
resource contributes, and record its licence or required attribution when that
information is available. Do not present third-party data or assets as original
project work, and do not leave externally sourced material credited in only
one of the two required locations.

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

The implementation uses **MapLibre GL JS** in the Flask frontend with a
viewport JSON endpoint served by Flask/PostgreSQL. The legacy Folium renderer
has been removed.

The implementation should define a small map-data API, such as a request for
`bounds`, `zoom`, `month`, and `climate_type`. The server should choose a safe
sampling resolution for that request, return existing PostgreSQL values, and
queue or fetch a bounded set of missing points from the open provider. The
exact provider, resolution policy, and client library will be selected during
the map-redesign phase and documented in the README when implemented.
