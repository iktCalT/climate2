# Climate provider evaluation

This document records the result of requirements 11 and 16 in
[`NEXT_REQUIREMENTS.md`](NEXT_REQUIREMENTS.md). Research was updated on
2026-09-24 using provider-owned documentation and direct inspection of NOAA's
public file indexes. It does not change the active application provider.

## Decision

Use **NOAA Conventional Observation Reanalysis (CORe)** from the NOAA Open
Data Dissemination Program (NODD) as the preferred future bulk source. It is
operated by NOAA/NCEP, is available anonymously over HTTPS, and requires no
account, API key, private token, or click-through dataset-licence acceptance.
NOAA describes the analyses and retrieval program as public domain; NOAA's
open-data policy places eligible NOAA data in the public domain in the United
States and targets a CC0 dedication for data that may otherwise have rights.

CORe is global from 1950 to near real time and provides 3-hourly, daily, and
monthly ensemble-mean files. Its public archive is designed for indexed GRIB
record retrieval, so the importer can fetch only the fields it needs rather
than make one HTTP request per map point. This is a better match for the
project's deliberately coarse 2-degree by 4-degree grid than Open-Meteo's
point-by-point request model.

Open-Meteo remains the only active website provider while imported CORe values
are compared and reviewed. No archive, credential, generated data file, or
database export belongs in Git. PostgreSQL remains the durable checkpoint and
public data source for the application.

## Required data contract

The PostgreSQL cache stores one row per location, month, and provider with:

- `temp_mean`: mean of daily mean 2 m temperatures, in degrees Celsius;
- `temp_max`: maximum daily 2 m temperature during the month, in degrees
  Celsius;
- `temp_min`: minimum daily 2 m temperature during the month, in degrees
  Celsius; and
- `precip`: mean of daily precipitation sums, in millimetres per day, rather
  than the total precipitation for the month.

The wording above describes the existing `helpers_data.py` aggregation. CORe
must preserve it and use its own `noaa_core` provider family so reanalysis is
never silently mixed with the current `open_meteo_cmip6` CMIP6 model average.

## Selected-source assessment

### NOAA CORe — selected

- **Owner and access:** NOAA/NCEP, distributed through NODD on an official
  public Google Cloud bucket. Downloads use HTTPS without authentication.
- **Rights and attribution:** NOAA's CORe documentation marks the analyses and
  downloader public domain. The project will still credit NOAA, NCEP, CPC,
  PSL, and NODD so users can audit the source and limitations.
- **Coverage and freshness:** global coverage from January 1950 to near real
  time. NOAA states that the NODD archive is updated about one day after the
  real-time system; availability can still be delayed or interrupted.
- **Temporal products:** monthly, daily, and 3-hourly ensemble-mean `pgb` and
  `flx` GRIB files. The file indexes publish byte offsets, allowing a client to
  request only selected records.
- **Mean temperature:** use the monthly ensemble-mean `TMP` record at 2 m above
  ground and convert Kelvin to Celsius with `C = K - 273.15`.
- **Maximum and minimum temperature:** do not use the convenient monthly
  max/min records. NOAA defines them as averages of daily extrema, while this
  application stores the highest and lowest daily value in each month. Read
  the daily 2 m maximum/minimum records and aggregate the month's maximum and
  minimum respectively.
- **Precipitation:** use monthly surface `PRATE`, whose documented GRIB units
  are kilograms per square metre per second. Convert the mean rate to
  millimetres per day with `mm/day = kg/m2/s * 86,400`.
- **Resolution:** CORe output uses a 512 by 256 Gaussian grid, about 0.7
  degrees. The importer must inspect each GRIB grid, normalize longitude
  conventions, and map it explicitly to the canonical 2-degree by 4-degree
  application points. Retaining the native precision is unnecessary for this
  project.
- **Limitations:** CORe is a model-and-observation reanalysis, not a station
  measurement or the same product as the current downscaled CMIP6 average.
  NOAA provides the data without warranty and notes a free-download quota whose
  details may change. Indexed partial downloads, bounded chunks, and resumable
  PostgreSQL writes are required both for efficiency and respectful use.

Direct index inspection confirmed that January 1950 contains the required
monthly mean 2 m temperature and surface precipitation-rate records, plus
daily 2 m minimum and maximum records. The monthly extrema records were also
confirmed to be daily-extrema averages, which is why they are excluded from
the importer contract.

## Implementation result

The optional `import_noaa_core.py` command now implements the staged retrieval
path with the Apache-2.0 [ECMWF ecCodes Python bindings](https://github.com/ecmwf/eccodes-python).
It reads NOAA `.idx` offsets, downloads only selected `.grb` byte ranges,
validates the encoded date, variable, statistic, unit, level, grid, missing
values, and physical bounds, then nearest-samples to the canonical 2-degree by
4-degree grid. One fully validated month is committed atomically under
`noaa_core`; PostgreSQL completion counts make reruns skip it.

Read-only live checks succeeded for January 1950 and August 2026. January 1950
was then written as 8,281 provider-scoped rows and an immediate dry run reported
the month complete without contacting NOAA. This verifies retrieval, decoding,
unit conversion, canonical dateline/pole sampling, transactional storage, and
the resume checkpoint.

The recorded edge-period import subsequently completed all 92 months across
1950–1953 and 2023–2026. May 2026 exercised the fail-closed archive-gap path:
NOAA's May 19 daily file omitted both 2 m extrema, so the importer required and
aggregated the exact minimum and maximum records from all eight official
3-hourly files. The month passed live no-write validation before its atomic
write. An explicit `1950-present` period now selects January 1950 through the
latest complete month while retaining the same bounded, resumable behavior;
the default remains limited to the two recorded edge periods. The first two
live full-history batches atomically committed every month of 1954 and 1955,
moving the local checkpoint from 92 of 920 to 116 of 920 complete months. The
next bounded batch begins with January 1956.

The read-only `compare_climate_providers.py` command now makes the activation
evidence reproducible without contacting a provider or modifying PostgreSQL. A
live January 1950 report found 8,281 complete canonical rows for each provider
and 8,281 paired rows. Across that grid, the CORe-minus-Open-Meteo signed mean
difference was -1.889 °C for monthly mean temperature, -2.456 °C for monthly
maximum temperature, -1.145 °C for monthly minimum temperature, and +0.341
mm/day for precipitation. Mean absolute differences were 3.652 °C, 3.919 °C,
4.037 °C, and 0.950 mm/day respectively. These are different climate products,
so those differences are evidence to review rather than pass/fail thresholds.

The representative review was completed on 2026-09-25. February 1952 exercises
a leap month and July 2023 exercises a recent complete year; both had 8,281
complete canonical rows from each provider. Their CORe-minus-Open-Meteo signed
mean differences were:

- February 1952: -1.752 °C mean, -2.067 °C maximum, -1.143 °C minimum, and
  +0.275 mm/day precipitation; mean absolute differences were 3.427 °C,
  3.929 °C, 3.668 °C, and 0.814 mm/day respectively.
- July 2023: -1.224 °C mean, -0.222 °C maximum, -1.915 °C minimum, and
  +0.434 mm/day precipitation; mean absolute differences were 3.032 °C,
  3.813 °C, 3.553 °C, and 1.146 mm/day respectively.

For newest complete month August 2026, CORe had the full canonical grid while
the existing Open-Meteo cache had only nine canonical rows. Six bounded
Open-Meteo requests filled the required New York-area land, central-Pacific
ocean, North Pole, South Pole, and both dateline-edge samples. The report then
showed every required representative value; it deliberately left global
coverage at 15 of 8,281 pairs rather than making thousands of comparison-only
API requests. The largest representative precipitation differences were
+9.202 mm/day in the central Pacific and about +4.3 mm/day at both dateline
edges. These are signals of product and aggregation differences to communicate,
not proof that either dataset is wrong.

## Activation decision

Keep `open_meteo_cmip6` as the active website provider. The field, unit,
coordinate, pole, dateline, historical, leap-month, recent-year, and newest-
month checks are sufficient to continue the resumable NOAA import, but not to
change live reads. All 92 recorded edge-period months are now complete under
`noaa_core`, but the middle decades are not; switching now would still leave
most of the advertised timeline unavailable. Mixing providers by month would
also make same-scale date comparisons scientifically confusing.

Use the explicit bounded full-history backfill under `noaa_core` rather than a
slow synchronous archive download during a visitor request. Revisit activation
only after January 1950 through the latest complete month is present and a
separate review defines foreground behavior without silently combining
reanalysis with the CMIP6 series. Any future switch remains an explicit,
separately recorded change.

## Alternatives not selected

### Copernicus CDS ERA5

ERA5 is authoritative, global, and technically suitable, but CDS requires an
account, one-time dataset-licence acceptance, and an API token for programmatic
retrieval. Anonymous mirrors do not remove the underlying Copernicus licence
or attribution obligations. It no longer matches the request for a source
that can be used without an account or licence-acceptance step.

### NCEP/NCAR Reanalysis 1

This older NOAA reanalysis covers the historical period and remains publicly
available, but operational updates ended in March 2026. NOAA positions CORe as
its replacement for climate monitoring, so starting a new importer on the
retired series would immediately create a freshness gap.

### NASA POWER

NASA POWER provides a documented HTTPS API with analysis-ready monthly global
meteorological data, but its meteorological record begins in 1981. It cannot
fill the required 1950–1980 period and its documentation asks clients to avoid
excessive synchronous requests.

### CRU TS

The University of East Anglia Climatic Research Unit publishes monthly mean,
minimum, and maximum temperature plus precipitation from 1901 onward at 0.5
degrees under the UK Open Government Licence. It covers land areas except
Antarctica and is released periodically, so it cannot supply the ocean cells
or near-real-time global coverage used by this map.

## Staged integration plan

1. Implement a small optional `noaa_core` importer; do not change foreground
   cache-miss requests or active site reads.
2. Retrieve only required GRIB records by parsing NOAA's public `.idx` byte
   offsets. Use bounded month chunks and an ignored temporary directory.
3. Decode each record with a reviewed, cited GRIB implementation. Validate the
   file's variable, level, timing, unit, dimensions, coordinates, and missing
   values before converting it.
4. Downsample deterministically to canonical points. Derive monthly extrema
   from daily records, combine them with monthly mean temperature and
   precipitation, and upsert only a complete validated month.
5. Use PostgreSQL as the resume checkpoint. A rerun must skip complete
   `noaa_core` rows and never infer completion from temporary files alone.
6. Use the read-only comparison report for representative land, ocean, polar,
   and dateline points across 1950, recent complete years, leap years, and the
   newest available month. Completed on 2026-09-25 with January 1950, February
   1952, July 2023, and August 2026.
7. Backfill January 1950 through the latest complete month with the explicit,
   bounded `1950-present` period; keep the two edge periods as the default.
8. Activate CORe only after full-history coverage and a separate review
   explicitly switches site reads from `open_meteo_cmip6` to `noaa_core`.

## Primary sources

- [NOAA CPC CORe overview](https://www.cpc.ncep.noaa.gov/products/CORe/index.html)
- [NOAA CPC CORe archive and NODD access](https://www.cpc.ncep.noaa.gov/products/CORe/archive.html)
- [NOAA CORe retrieval and field documentation](https://ftp.cpc.ncep.noaa.gov/CORe/get_core/get_core.txt)
- [NOAA CORe regridding guidance](https://www.cpc.ncep.noaa.gov/products/CORe/regridding.html)
- [NOAA PSL CORe overview](https://psl.noaa.gov/data/coreinfo.html)
- [NOAA CORe operational announcement](https://wpo.noaa.gov/ncep-introduces-operational-reanalysis-for-climate-monitoring-core/)
- [NOAA NCEI open-data policy](https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf)
- [NCEP/NCAR Reanalysis 1 update notice](https://psl.noaa.gov/news/2026/r1datanotice.html)
- [Copernicus CDS ERA5 monthly data](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=overview)
- [NASA POWER monthly API](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/)
- [CRU high-resolution gridded datasets](https://crudata.uea.ac.uk/cru/data/hrg/)
