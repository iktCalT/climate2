# Reviewer / Debugger log

Writer: Agent 4 only. Follow [SKILL.md](SKILL.md).

## 2026-09-29 | MAP-002 | numeric map differences | done
- Result: the P3 copy finding was resolved; README.md:28 now says
  “PostgreSQL-cached values.” No other confirmed defect in the scoped review.
- Check: verified the exact line and `git diff --check ee0e568`; wording-only
  correction, so tests were not rerun. Prior QA results: three Node suites and
  40 affected Python tests passed. No browser or live data access.
- Next: none; Lead integrates.

## 2026-09-29 | PROVIDER-003 | activate saved NOAA public reads | done

- Result: no actionable finding in the scoped activation diff. The startup
  selector propagates to Flask, public history/map queries and saved-month
  discovery; Open-Meteo writes and migration remain fixed to CMIP6; map/history
  fallbacks remain disabled for NOAA public reads. Conditional admin copy and
  current README/PostgreSQL/provider status match the selected provider, and
  dated evaluation conclusions are labeled historical. Test changes preserve
  CMIP6-only map-fetch coverage and add fake-SQL selector and no-fallback checks.
- Check: read-only diff and caller/test inspection; `git diff --check HEAD`
  passed. QA reports 155 Python tests (8 PostgreSQL skips) and three Node map
  suites passed; not rerun. No live DB/provider/network or browser check.
- Next: Lead integrates; browser verification remains unavailable this round.

## 2026-09-29 | PROVIDER-002 | NOAA location/presentation readiness | done

- Result: one P3 wording finding. `location_sampling.py:21` says “closest canonical grid point,” and Home/Locations call the coordinate-wise result “nearest”; independent latitude/longitude rounding need not minimize great-circle distance (for example, the 89°N, 2°E tie chooses 88°N, 0°E while the pole is closer). Describe coordinate-wise rounding in these labels; keep the agreed sampling rule. No other actionable issue found in fixed sampling, cache-only provider reads, chart identity/titles, two-mode copy, or citations. Public selector remains CMIP6.
- Check: read-only code/requirements/tests inspection. QA reports 152 Python tests (8 PostgreSQL skips) and three Node suites passed; not rerun. No browser, live database, provider, or network check.
- Recheck: helper docstring and Home/Locations now say latitude and circular longitude are rounded separately; the former explicitly distinguishes this from great-circle nearest. Sole finding resolved. QA reports 10 NOAA and 5 content-page focused tests passed; not rerun here.
- Next: Lead integrate. Browser remains unverified because IAB is disconnected.

## 2026-09-29 | PROVIDER-001 | immutable acquisition source | done

- Result: no actionable finding in the six production-file diff. Open-Meteo writes, source probes, prefetch checkpoints, and legacy migration use fixed CMIP6; comparison loads explicit NOAA and CMIP6; public map/history/cache reads still use the selected provider, and both optional fallback paths stop under NOAA. Caller search found no remaining writer keyed by the public selector. This does not establish NOAA activation readiness; coordinate policy and public labels remain separate.
- Check: reviewed diff, surrounding callers, seven fake-connection regressions, and `git diff --check`; focused tests passed (7). QA reports 142 Python tests (8 database skips); not rerun in full. No live data or network access.
- Next: Lead integrate PROVIDER-001; assign activation work separately.

## 2026-09-28 | NOAA-READINESS | public provider activation | done

- Result: activation by changing `ACTIVE_CLIMATE_PROVIDER` alone is unsafe. Open-Meteo acquisition and legacy migration write with that constant, so future writes could masquerade as or replace NOAA. Locations query exact coordinates while NOAA imports canonical grid points only; most user-entered locations would be empty. Public copy and map labels remain Open-Meteo-specific; the comparison CLI would compare NOAA with itself. Maps and saved-month discovery are cache-only/provider-scoped; footer has a NOAA branch. The first/last-five-year scope supersedes the older full-history prerequisite.
- Check: read-only code and requirements inspection; no database, network, provider request, or tests run.
- Next: Lead define activation contract; Backend separate source identities and location policy, then QA validate with isolated data and revised copy.

## 2026-09-28 | PAGES-001 | Home and References clarity | done

- Result: no concrete finding in the `a86172a` page refresh. Checked active CMIP6/inactive NOAA claims against provider and route code; coverage, °C and mean daily mm/day, cache-only browsing, linked comparisons, manual scales, dated history, semantic links/headings, responsive CSS, retained credits and external-link protection. Production changes stay within assigned page/CSS scope.
- Check: reviewed diff and surrounding code; `git diff --check a86172a` passed. QA reports 5 focused tests and 135 offline Python tests (8 database skips). Lead reports desktop Home and 390px References/disclosure browser checks; not independently rerun. No live data accessed.
- Next: Lead integrate; no Reviewer fix requested.

## 2026-09-28 | MAP-001 | linked comparison readouts | done

- Result: prior P3 Maps-page wording finding resolved. `templates/maps.html:24` now describes each panel's own value and source, explicitly including labelled display estimates; it no longer calls estimates saved values. No remaining finding in the bounded review of per-panel containment/value/source, loading and stale guards, safe text, popup close and cleanup, and citations.
- Check: all three Node map suites passed before the wording correction; `git diff --check` clean. QA reports 133 Python tests (8 skips), then a passing template Node check and Jinja parse after the correction; not rerun here. No live data or independent browser check; Lead reported synthetic browser verification.
- Next: Lead integrate; no further Reviewer action unless code changes.

## 2026-09-27 | REVIEW-003 / SECURITY-001 | private static storage | done

- Result: no remaining finding in the bounded requirement. The prior P2
  disclosures for `users.db.bak` and `users.db_backup` are fixed. Reviewed
  resolver precedence, static path/alias/sidecar denial, setup closure, tests,
  and updated docs. Arbitrarily renamed database copies require private storage;
  a separate static server needs its own guard.
- Check: independent temporary fake-file GET/HEAD check denied seven database
  names and served three normal assets; `git diff --check` passed. QA reports
  133 Python tests (8 skips) and Node pass; full suite not rerun. No real DB read.
- Next: Lead integrate; no further Reviewer action unless code changes.

## 2026-09-27 | REVIEW-001 | restructure / account storage exposure | done

- Result: no introduced regression confirmed in `cbeda44..9836be2`.
- **P1, pre-existing:** [app.py](../../../climate/web/app.py#L49), lines 49–54,
  serves static files while defaulting accounts to `static/users.db`. Anonymous
  `GET /static/users.db` returned HTTP 200 and a complete SQLite database in a
  temporary fake-data reproduction; real accounts were never read.
- Check: 16 admin tests passed; error HTML escapes markup; ten core modules
  unchanged except imports; schemas byte-identical; focused secret checks passed.
- Next: account exposure and the inherited connection warning were addressed
  by SECURITY-001; see the newer review and [QA log](qa-log.md). No production
  edits or live DB checks were made during REVIEW-001.
