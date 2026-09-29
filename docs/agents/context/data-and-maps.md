# Data and map decisions

Update 2026-09-29, `codex/activate-noaa-cache` based on `7211024`: PROVIDER-003
changes the startup public selector to `noaa_core`; restart is required. No live
server was deployed or data changed in this round. PRs #58–59 separated CMIP6
acquisition identities and added fixed NOAA location sampling/provider-aware
labels. Current requirements and task board supersede the older provider status
below. Validation limitations and dated coverage remain in the Lead log and
provider evaluation; do not infer complete history or scientific accuracy.

Snapshot: 2026-09-27, local `main` at `cbeda44`, inherited by the restructure
branch. This note summarizes existing repository
records, not a fresh database check or independent provider verification.

- User direction: concentrate acquisition on the first/last five years,
  **1950–1954 and 2022–2026**, completed months only, through administrator
  controls. This supersedes full-history and reverse 2016–2026 fetching.
- Local main documents NOAA CORe as the selected anonymous bulk source, with
  resumable PostgreSQL imports under `noaa_core`. Public reads still use
  `open_meteo_cmip6`; importing NOAA does not activate it. Footer attribution
  follows the actual active provider. Provider comparison/validation remains
  necessary before activation; inherited ocean-cache anomalies are unresolved.
- Climate rows are keyed by location, month, and provider. Temperatures use
  Celsius; precipitation is mean daily precipitation in mm/day, not a monthly
  total. Never silently combine provider families or mislabel these units.
- Public Maps/Locations use saved data; acquisition belongs to explicit admin
  tools. Missing values stay visible. Maps initially show the US; comparisons
  share one manually controlled scale across two to four dates. Scales do not
  change automatically. Saved-month discovery helps select available data.
- Administrator cleanup is explicit and bounded; development-file cleanup does
  not authorize removing climate rows. Recheck current coverage in the database
  when needed; historical counts are not live status.

Sources: on local `main`, `docs/NEXT_REQUIREMENTS.md` requirements 16–25,
`docs/CLIMATE_PROVIDER_EVALUATION.md`, and `README.md`. Read those versions with
`git show main:docs/NEXT_REQUIREMENTS.md` (or substitute another listed path).
Use the recorded revision above for historical evidence if the branch has
moved. Current [requirements](../../NEXT_REQUIREMENTS.md) and
[architecture](../../ARCHITECTURE.md) describe subsequent work.
