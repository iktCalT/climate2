# Data and map decisions

Snapshot 2026-09-30, main `002223e`. Code/documentation evidence, not a fresh
database or production-server check.

- Public Maps, Locations and saved-month discovery select `noaa_core` on app
  startup (PR #60). Restart all workers to adopt a changed selector; no restart
  was verified. Open-Meteo acquisition remains fixed to `open_meteo_cmip6`.
  Never mix source families or relabel rows. Public browsing is cache-only.
- NOAA location history rounds latitude and circular longitude separately to
  one fixed 2° × 4° sample, with requested/sample coordinates and distance
  disclosed. It starts January 1951; map dates start January 1950.
- User's acquisition scope: **1950–1954 and 2022–2026**, completed months only,
  explicit admin batches. This supersedes full-history/reverse backfills.
  Cleanup remains explicit, bounded and destructive; development work does
  not authorize it. Previously saved middle years are not automatically removed.
- Temperatures are °C; precipitation is mean daily mm/day, not monthly totals.
  Maps start over the US. Two-to-four panels share a manually controlled scale,
  linked selections and first-month displayed-value differences. Popups link
  selected coordinates to history, whose own sampling may differ from the map.
  Estimates, gaps and loading remain labelled; these are not direct observations.
- Dated evidence: Sept 26 admin check found 60/60 and 56/56 edge-window months
  complete through August 2026. Sept 28 read-only audit found 8,281 finite,
  complete canonical rows for each Jan–Aug 2026 month (66,248 total), no tested
  physical/order violations, and equal dateline endpoints. Paired CMIP6 coverage
  was only 9 points/month, 15 in August. This does not establish ground truth,
  full history, current coverage or future availability.
- Inherited CMIP6 ocean-cache anomalies remain unresolved; activation does not
  repair them. Browser verification and live deployment of recent changes
  remain unverified.

Sources: [requirements](../../NEXT_REQUIREMENTS.md),
[provider evaluation](../../CLIMATE_PROVIDER_EVALUATION.md),
[completed rounds](completed-rounds.md). Original audit handoff:
`git show 002223e:docs/agents/lead-log.md` (NOAA-READINESS).
