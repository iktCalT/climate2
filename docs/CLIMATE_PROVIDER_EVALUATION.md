# Climate provider evaluation

This document records the result of requirement 11 in
[`NEXT_REQUIREMENTS.md`](NEXT_REQUIREMENTS.md). Research was completed on
2026-09-23 using provider-owned documentation. It does not change the active
application provider.

## Decision

Use the **Copernicus Climate Data Store (CDS) ERA5 family** as the preferred
candidate for a future bulk-ingest path. Keep Open-Meteo active until the
project owner:

1. creates a free CDS account and accepts the ERA5 dataset licence in the CDS
   web interface;
2. provides the API token outside the repository;
3. approves replacing the current averaged CMIP6 climate projections with
   ERA5 reanalysis values; and
4. approves a sampled comparison showing that the new monthly aggregation and
   units are correct.

No API token, downloaded climate archive, or generated credential file belongs
in Git. PostgreSQL remains the durable checkpoint and public data source for
the application.

## Required data contract

The PostgreSQL cache stores one row per location and month with:

- `temp_mean`: mean of daily mean 2 m temperatures, in degrees Celsius;
- `temp_max`: maximum daily 2 m temperature observed during the month, in
  degrees Celsius;
- `temp_min`: minimum daily 2 m temperature observed during the month, in
  degrees Celsius; and
- `precip`: the current application uses the mean of daily precipitation sums,
  in millimetres per day, rather than the total precipitation for the month.

The wording above describes the existing `helpers_data.py` aggregation. A new
provider must preserve it unless a separately recorded schema and product
decision intentionally changes the meaning.

## Candidate assessment

### Copernicus CDS ERA5 — preferred

- **Owner and licence:** Copernicus Climate Change Service, operated by ECMWF
  on behalf of the European Union; CC BY.
- **Coverage:** global, regular latitude/longitude grid, 1940 to present.
- **Access model:** HTTPS downloads and the CDS API. Requests are queued rather
  than governed by Open-Meteo's point-request minute/hour/day quotas. The CDS
  documents a 100,000-field ceiling for one ERA5 monthly single-level request;
  limits may change with system load.
- **Mean temperature:** request monthly averaged `2m_temperature`, then convert
  Kelvin to Celsius with `C = K - 273.15`.
- **Maximum and minimum temperature:** the ERA5 monthly dataset explicitly has
  no monthly means for its forecast maximum/minimum parameters. Use the
  post-processed daily-statistics dataset with hourly `2m_temperature`, daily
  maximum and daily minimum aggregations at one-hour sampling, then take each
  month's maximum and minimum respectively. ECMWF recommends deriving longer
  extrema from analysed hourly 2 m temperature.
- **Precipitation:** monthly averaged `total_precipitation` has effective units
  of metres of water per day. Multiplying by 1,000 yields the application's
  millimetres-per-day value. Multiplying again by the number of days would
  produce a monthly total and would not match the current schema semantics.
- **Resolution:** the CDS ERA5 atmospheric product is supplied on a 0.25° grid;
  retrievals can be geographically subset and may be requested on another
  regular grid. The importer must map the canonical 2°×4° points explicitly
  and validate longitude conventions and pole handling.
- **Freshness:** the daily-statistics catalogue is updated daily with a stated
  six-day delay. Recent values may be ERA5T preliminary data before final ERA5
  replaces them.
- **Important difference:** ERA5 combines a weather model with observations to
  create reanalysis. The current Open-Meteo endpoint provides downscaled CMIP6
  climate-model output averaged across `MRI_AGCM3_2_S` and `EC_Earth3P_HR`.
  Mixing both products in the same columns without provenance would create
  artificial differences, so a migration needs one declared provider per
  comparison series or explicit source metadata.

ERA5 meets the requested safety, ownership, licensing, historical coverage,
global coverage, and bulk-capacity criteria. The requirement for a user
account, one-time licence acceptance, and an API token is the reason this
repository does not silently enable it.

### NASA POWER — safe, but incomplete for this project

NASA POWER provides a documented HTTPS API with analysis-ready monthly global
meteorological data. Its meteorological record begins in 1981, so it cannot
fill the required 1950–1980 period. Its documentation also cautions clients
against excessive synchronous requests. It is useful for validation or a
newer-period feature, not as the sole replacement.

### CRU TS — useful historical land dataset, not a complete replacement

The University of East Anglia Climatic Research Unit publishes monthly mean,
minimum, and maximum temperature plus precipitation from 1901 onward at 0.5°
under the UK Open Government Licence. CRU TS covers land areas except
Antarctica, is released periodically rather than near real time, and does not
provide the ocean cells used by the global map. It is a credible historical
land-only source, not a complete application provider.

## Staged integration plan

1. Add an optional, explicit ERA5 bulk-import command; do not change foreground
   cache-miss requests yet.
2. Read the CDS token from the user's standard configuration or an environment
   variable. Never accept a token as a command-line argument or write one into
   the project tree.
3. Request bounded date/area chunks, download into an ignored temporary
   directory, validate dimensions and units, then upsert one completed chunk at
   a time so PostgreSQL remains resumable.
4. Store or otherwise enforce provider provenance before ERA5 rows can coexist
   with Open-Meteo rows. Do not label mixed products as one continuous series.
5. Compare several land, ocean, polar, and dateline points across old and recent
   months. Verify temperature extrema, leap-year precipitation, missing values,
   coordinate selection, and reproducible reruns.
6. Only after owner approval, use ERA5 for the remaining 1950–1953 and
   2023–2026 bulk prefetch or run a documented one-provider migration.

## Primary sources

- [ERA5 monthly averaged data on single levels](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=overview)
- [ERA5 post-processed daily statistics on single levels](https://cds.climate.copernicus.eu/datasets/derived-era5-single-levels-daily-statistics?tab=overview)
- [ERA5 data documentation and parameter semantics](https://confluence.ecmwf.int/spaces/CKB/pages/239349091/ERA5%3A+data+documentation)
- [CDS documentation, access rules, and request limits](https://confluence.ecmwf.int/pages/viewpage.action?pageId=656872232)
- [CDS API setup](https://cds.climate.copernicus.eu/how-to-api)
- [NASA POWER monthly API](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/)
- [CRU high-resolution gridded datasets](https://crudata.uea.ac.uk/cru/data/hrg/)
