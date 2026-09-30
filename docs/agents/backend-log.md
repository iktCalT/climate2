# Backend Developer log

Writer: Agent 2 only. Follow [SKILL.md](SKILL.md).

## 2026-09-29 | MAP-003 | map history links and coordinate form | done
- Result: valid selected map coordinates now link to saved Locations with round-trip numeric precision in ready/loading/missing readouts; popup and page guidance explain independent history sampling. Locations form has associated input IDs, responsive width, arbitrary precision and south/west guidance. No routes, data access, packages or citations changed.
- Check: `node --check static/map_selection.js`, Jinja syntax compilation for the three templates, and `git diff --check` passed. Regression suite/browser check not run; QA owns the batch pass.
- Next: hand off to Lead and QA; no known blockers.

## 2026-09-29 | MAP-002 review follow-up | README map terminology | done

- Result: changed README tile reuse wording from PostgreSQL “observations” to
  PostgreSQL-cached “values,” consistent with grid-cell provenance.
- Check: `git diff --check` passed; wording-only, no tests needed.
- Next: Lead continues integration; no remaining developer changes.

## 2026-09-29 | MAP-002 | signed map differences and cached-value wording | done

- Result: popups use the first month baseline, finite containing-cell values,
  estimate provenance, concise formatting and explicit unavailable reasons;
  single maps have no comparison section. Fixed rounded-negative-zero sign and
  deleted-panel handling; added coarse-grid/non-trend caveat to README/References.
- Check: `node --check static/map_selection.js`, focused
  `node --test tests/test_map_selection.mjs` (1 pass), and scoped diff check pass.
  Browser unavailable; QA owns the final batch.
- Next: hand off to Lead/QA; no open developer findings.

## 2026-09-29 | PROVIDER-003 | activate saved NOAA public reads | done

- Result: selected `noaa_core` for startup public reads; source writers remain pinned to CMIP6. Updated provider-aware admin copy, current README claims, and current PostgreSQL/evaluation status with restart and selector rollback. Historical evaluation decision is explicitly superseded; existing NOAA citations remain.
- Check: AST parse, selector/source identity assertions, Jinja compilation for admin and References templates, and `git diff --check` passed. No database, provider, browser, or test-suite access; QA owns regressions, and the browser inventory was empty.
- Next: hand off to QA; no production blockers found.

## 2026-09-29 | PROVIDER-002 review follow-up | grid-rounding wording | done

- Result: clarified that NOAA latitude and circular longitude round separately; the chosen fixed grid coordinate need not minimize great-circle distance. Sampling behavior is unchanged.
- Check: template parse, (89°, 2°) independent-rounding smoke, and `git diff --check` passed. Focused NOAA/content suite ran 15 tests with one expected failure: QA's new copy assertion still requires the removed “nearest” phrase. No browser or live data operation.
- Next: QA owns the assertion update in `tests/test_noaa_location_readiness.py`; Reviewer can verify wording.

## 2026-09-29 | PROVIDER-002 | NOAA location sampling and public copy | done

- Result: added pure finite-coordinate NOAA 2° × 4° sampling with deterministic circular ties, dateline and pole rules, and great-circle distance. Locations uses one fixed cache-only sample; request/sample/provider identify chart renders, whose initial and dropdown titles name the source. Home, Maps, Locations and References respond to the active provider while retaining credits and historical CMIP6 caveat. No activation or data write.
- Check: 40 focused Python tests passed; simulated NOAA coordinate, route and chart-title smokes passed; `git diff --check` passed. No live database/provider or browser check.
- Next: QA adds fake-provider boundary regressions, then Reviewer inspects.

## 2026-09-29 | PROVIDER-001 | immutable acquisition source | done

- Result: Open-Meteo writes and source checkpoints use fixed `open_meteo_cmip6`; SQLite migration and prefetch do likewise. Comparison loads explicit NOAA and CMIP6. Public history/map reads retain the active selector; opt-in Open-Meteo fallback returns cached gaps under another selector. No provider activation or live data operation.
- Check: focused offline weather, map/route, prefetch and comparison suites passed (62 tests, 4 database skips); mocked NOAA fallback smoke passed; `git diff --check` passed. No live database or provider request.
- Next: QA adds fake-database regressions for NOAA-selector writes, checkpoints, migration, comparison and public reads, then Reviewer inspects.

## 2026-09-28 | PAGES-001 | Home and References clarity | done

- Result: refreshed the public entry points, coverage/units/provider guidance, and linked comparison instructions. References now separates active CMIP6 from inactive NOAA and folds old import checkpoints into a dated disclosure. All existing external citation URLs remain.
- Check: offline Jinja render for both pages, citation URL set diff, and `git diff --check` passed. No live database, provider request, or browser check.
- Next: QA runs route regressions and browser review; Lead integrates.

## 2026-09-28 | MAP-001 review follow-up | Maps guidance | done

- Result: changed the readout guidance to say each month has its own value and data source, including labelled display estimates; no behavior changed.
- Check: Jinja template parse and `git diff --check` passed.
- Next: QA/Reviewer continue MAP-001 verification.

## 2026-09-28 | MAP-001 | linked map location readouts | done

- Result: added a dependency-free selection controller for each panel's accepted GeoJSON, safe popup text, per-month value/source and missing/loading/error states. Map clicks include gaps; viewport moves invalidate stale readouts immediately; stale responses cannot restore them. Template gives user guidance. No data API or scale change.
- Check: Node syntax and focused two-panel fake-popup smoke passed (zero, negative, loading, missing, close). Existing Node scale test, Jinja parse, and `git diff --check` passed. Browser and live data checks were not run.
- Next: QA add regression tests for controller and template lifecycle, then Reviewer inspect.

## 2026-09-27 | REVIEW-003 | database backup delimiters | done

- Result: recognized database extensions now match at filename end or before
  any non-ASCII-alphanumeric delimiter, including underscore and whitespace;
  `dbpedia.js` and `thing.dbpedia.js` remain allowed.
- Check: temporary fake-file requests passed for underscore, whitespace,
  punctuation, tilde, and sidecar backups plus allowed assets. Admin-role (16)
  and project-layout (3) suites passed; `git diff --check` is clean.
- Next: QA verify and add regressions; Lead integrate.

## 2026-09-27 | REVIEW-002 | database backup names | done

- Result: static guard now rejects recognized `.db`, `.sqlite`, and `.sqlite3`
  filename extensions followed by end, dot, hyphen, or tilde, case-insensitively.
  It conservatively blocks `library.db.js` while allowing `dbpedia.js`.
- Check: temporary fake-file requests passed for backup/sidecar suffixes and
  allowed ordinary assets; admin-role (16) and project-layout (3) suites passed.
  No real account DB was opened.
- Next: QA verify and add regression tests; Lead integrate.

## 2026-09-27 | BACKEND-002 | private account storage / static guard | done

- Result: shared resolver preserves explicit/env paths, warns while selecting
  existing `static/users.db`, and defaults to `instance/users.db`; static
  requests reject DB files/sidecars, configured account files and metadata
  identity aliases, hidden paths, and unsafe symlinks. Setup closes SQLite.
- Check: focused admin-role (16) and project-layout (3) tests passed. Temporary
  fake-data checks passed for resolver precedence, setup, and static denial
  while serving CSS, plus hard-link and symlink-loop checks. Local import
  reports the expected legacy-path warning;
  no real account DB was opened. No live data or provider calls.
- Next: QA verify/add lasting tests; Lead finish docs and integration.

## 2026-09-27 | BACKEND-001 | package imports / entry points / resources | done

- Result: reviewed checkpoint `9836be2`; no confirmed restructuring regressions
  and no production edits. Internal imports resolve; data/provider/service
  modules do not import web or CLI layers. Named role skills were unavailable.
- Check: `DATABASE_URL= PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest
  discover -s tests -p test_project_layout.py -v` passed all 3 tests;
  `bash -n run.sh` and `run.sh --help` from outside the repo passed.
- Next: Lead/QA should triage account initialization's unclosed SQLite
  connection in `climate/cli/setup_user_database.py`. Reproduced one
  `ResourceWarning`; the same connection-lifetime pattern exists at `cbeda44`,
  so it predates restructuring. No live database or provider calls.
