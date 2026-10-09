# Test / QA log

Writer: Agent 3 only. Follow [SKILL.md](SKILL.md).

## 2026-10-09 | LOCATION-FETCH-001 review correction | stream deadline and cross-sample refresh | done
- Result: Added fake-stream regressions for per-read remaining timeout, elapsed deadline, failed-transfer byte charging, incomplete range and byte cap. Tested singleton-row replacement after a first sample releases the shared lock. Browser tests now cover count-based refresh after another sample takes the job, ready/done transitions, and no duplicate reload. Route test matches the initial finite four-field count to service semantics. No production edits or confirmed remaining defect.
- Check: offline `tests.test_location_fetch tests.test_locations_route tests.test_noaa_core tests.test_provider_identity`: 80 passed, zero skips/failures; `node --test tests/test_location_fetch_browser.mjs`: six passed. `git diff --check` clean. Mock network/PG only; no real browser, live NOAA/PostgreSQL or full-suite repeat.
- Next: Reviewer verifies both corrections; Lead coordinates integration.

## 2026-10-09 | LOCATION-FETCH-001 | isolated service, route and browser QA | done
- Result: Added mocked PostgreSQL/provider tests for settings, completed/partial/future coverage, saved-value merge and final validation, bounded requests, shared lock, durable hourly limit, worker completion/failure, and consistent status counts. Added browser lifecycle tests for start/poll, progressive and final refresh, error/throttle retry, pagehide abort and no storage. Updated stale Location/content assertions and Docker runtime-file inventory. No production edits or confirmed defect.
- Check: offline focused Python batch (`test_location_fetch`, `test_locations_route`, `test_chart_rendering`, `test_noaa_location_readiness`, `test_content_pages`, `test_deployment`): 96 passed, zero skips/failures. Node location/map/community batch: 32 passed, zero skips/failures. `git diff --check` passed. PostgreSQL flags disabled; mocks only. No live database/provider, actual image build or real-browser visual check.
- Next: Reviewer audits LOCATION-FETCH-001; Lead coordinates any correction.

## 2026-10-08 | COMMUNITY-003 | unpublished pin preview browser checks | done
- Result: Added seven focused browser tests for profile-free preview, click/typed parity, invalid coordinates and blocked POST, one marker per ready map, late load/removal, public refresh/pan preservation, placement off, failed/successful publish and disabled mode. Existing public consent and anonymous-read checks remain passing. No production defect found.
- Check: `node --test tests/test_community*.mjs`: 15 passed, zero failed/skipped; `git diff --check` passed before final test-only adjustment. Fake DOM/map/network only; no browser UI, Python, live store or service run.
- Next: Reviewer audits COMMUNITY-003 marker lifecycle and posting/consent regressions; Lead integrates after review.

## 2026-10-08 | COMMUNITY-002 | local-profile forget confirmation | done
- Result: Browser harness stubs native confirmation. Added cancel checks for exact saved bytes, active profile, profile and pin controls, status, callback count, storage operations and network calls. Confirmed success and remove failure retain their prior inactive states; failure leaves saved bytes and reports the storage error. No production edits.
- Check: `node --test tests/test_community_browser.mjs`: eight passed, zero failed/skipped; scoped `git diff --check` passed. Initial run caught a reversed test expectation, corrected before final run. No Python/full suite, browser, live storage or network operation.
- Next: Reviewer audits COMMUNITY-002; no QA blocker.

## 2026-10-04 | DEPLOY-004 | image-context and runtime-mode review corrections | done
- Result: added regressions requiring a default-deny `.dockerignore` with literal existing regular-file exceptions, all Python/SQL/template runtime files, and effective exclusion of representative private descendants; invalid `CLIMATE_ENV` now tested against account setup/admin CLI with no database or parent-directory creation. Added two Moby URLs to exact References inventory. No production edits.
- Check: focused offline `tests.test_deployment tests.test_content_pages tests.test_private_account_storage tests.test_admin_bootstrap tests.test_admin_roles tests.test_user_database_setup`: 58 passed, zero skips/failures (final run). Initial focused run also passed before required-file coverage was expanded. Docker and Go unavailable; matcher assertions are static, not an actual image build. Existing mocked cleanup error log and legacy path warning are expected.
- Next: Reviewer rechecks both corrected blockers; no full Python or Node repeat.

## 2026-10-03 | DEPLOY-004 / UI-002 | portable deployment and wheel guard | done
- Result: added temporary-state production config/proxy/static/health/container checks and Node VM tests for the real delegated wheel handler; mirrored ten new official URLs in exact References inventory. Initial test exposed arbitrary private-file hard-link leak through `static/`; Developer added production-only regular-file/single-link guard, and focused regression now passes. No QA production edits or live stores.
- Check: initial combined offline batch: Python 211 total, 202 passed, eight PostgreSQL skips, one failure (leak); Node 20 passed. After fix, `DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_deployment tests.test_content_pages tests.test_private_account_storage`: 29 passed, zero skips/failures. Docker/browser unavailable; static container checks only. Inherited session isolation remains.
- Next: Reviewer audits final implementation; no second full batch for narrow fix.

## 2026-10-03 | DEPLOY-003 | deployment References URL inventory | done
- Result: added the 11 official deployment research URLs cited by README and rendered References to the exact content-page inventory; preserved all existing URLs and assertions. Changed only the assigned test and this log.
- Check: offline `DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_content_pages`: 12 passed, zero failures/skips. Scoped `git diff --check` passed. Existing legacy account-path warning appeared; no live database or provider operations.
- Next: Lead integrates the documentation and QA update; no QA blocker.

## 2026-10-02 | REGRESSION-002 | combined offline checkpoint | done
- Result: At `083ead5`, PR #77 UI/community and PR #78 terminal-admin checks have no confirmed offline regression. Isolation review found temporary SQLite stores/mocks; PostgreSQL classes are opt-in. No production/test edits or live operations.
- Check: `DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests`: 204 total, 196 passed, eight skipped (three cleanup, one availability, four weather PostgreSQL integration checks). `node --test tests/test_map*.mjs tests/test_community*.mjs`: 18 passed, zero skipped/failed. Both exit zero, run once.
- Limits: inherited filesystem sessions are not fully isolated; legacy static account-path warning, SQLite ResourceWarnings, and expected mocked-failure error logs appeared. No browser, live PostgreSQL/provider/account, or deployment verification.
- Next: Lead; no QA blocker.

## 2026-10-02 | DEPLOY-002 | administrator bootstrap tests | done
- Result: added isolated temporary-SQLite tests for hashed creation/login, default profile, duplicates, rollback, path/input rejection, TTY prompts and argument secrecy. Regressions now cover `--` dispatch and a static symlink to an initialized private store, including a symlinked parent; rejected attempts preserve user/profile rows. No QA production edits.
- Check: offline `python -m unittest tests.test_admin_bootstrap tests.test_admin_roles` with PostgreSQL opt-ins zero: all 27 pass. `git diff --check` passed. Existing public registration 403 and admin-role checks pass. No live store, Node or full-suite run.
- Next: Reviewer inspects final implementation; no QA blocker.

## 2026-10-02 | COMMUNITY-001 / UI-001 | bounded paths and portable References checks | done
- Result: removed permanent Git-history dependency; rendered References rejects concise/community wrappers, added CSS block stays scoped, native details retained. Baseline byte equality remains earlier one-off evidence. Compact path test forbids recursive traversal and rejects public symlink aliases, hardlinks, directories and FIFOs; account case aliases checked when filesystem supports them.
- Check: offline `tests.test_content_pages tests.test_community`: 22 passed; whitespace clean. Initial fixture expectation corrected to resolved temporary path (`/var` alias). No production changes, full batch or Node repetition.
- Next: Reviewer verifies bounded path fix. Earlier batch and focused security evidence remain as recorded below; no live/browser/deployment verification.

## 2026-10-02 | UI-001 / DEPLOY-001 / COMMUNITY-001 | focused contracts and offline regression | done
- Result: new isolated SQLite service/API tests and five Node browser-module cases; semantic copy assertions preserve source, units, caveats, forms and readouts. Registration rejects writes; world bounds and References byte equality to `7342c9e`, append-only/scoped CSS verified.
- Check: offline Python discovery (empty DATABASE_URL, both PostgreSQL opt-ins zero): 192 total, 182 passed, eight expected skips, two errors. Node map/community: 18 passed. Diff whitespace clean.
- Post-fix: independently reran `tests.test_community` with the same offline flags: nine passed. Strict UTF-8 validation precedes SQLite access; administrator removal skips public throttles while owner removal retains them. Both formerly failing regressions pass. Full batch was not repeated.
- Next: Reviewer. No live data/network/browser checks; inherited filesystem sessions and existing account connection warnings remain limitations. Actual browser behavior, proxy IP trust and deployment remain unverified.

## 2026-10-02 | REGRESSION-001 | NOAA precipitation copy assertion | done
- Result: Replaced the stale combined assertion with separate checks for “mean daily precipitation in mm/day” and “monthly average daily rate, not a monthly total” in both provider iterations. Historical checkpoint batch: 173 Python passes, eight skips, one stale-copy failure; Node 13 passed. That batch is distinct from this correction.
- Check: `DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_noaa_location_readiness` passed (10 tests). No live database, network, browser, or unrelated tests.
- Next: Lead to integrate; no QA blocker.

## 2026-10-01 | HISTORY-002 | editable Location coordinates | done
- Result: extended the existing HTML parser to verify one native GET form, contained inputs/submit/Clear link, labels, bounds, required flags, unique IDs and blank entry. Both providers' covered/empty results preserve requested decimal and signed-zero values while reads use provider sampling. Parsed fields are edited and resubmitted to the route; Clear returns blank without history reads. Invalid/nonfinite/range inputs remain 400; incomplete requests retain blank-entry behavior. README/References editing guidance and existing provenance/coverage checks pass. Only assigned tests and this log changed on `codex/edit-location-coordinates` (base `a6491c1`).
- Check: `DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_locations_route tests.test_content_pages` passed 57 tests. No live DB/providers, browser, Node/chart/full-suite rerun or Git operations.
- Next: Lead dispatch Reviewer; no QA blockers.

## 2026-10-01 | HISTORY-001 | seasonal chart coverage | done
- Result: preserved inherited chart tests and added all-metric 0/1/2/3 coverage with unchanged means, all-null stored months, December–February winter assignment, contiguous sparse-year NaN gaps, empty traces, units and unchanged default/dropdown. Mocked route checks prove same-content v6 renders are replaced by v7 and v7 is reused. Locations/README/References checks cover season guidance, coverage limits and approved Plotly citations. Changed only three assigned test files and this log on `codex/seasonal-coverage-readouts` (base `eab3e85`).
- Check: `DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_chart_rendering tests.test_locations_route tests.test_content_pages` passed 59 tests. No production edits, live data, Node/full-suite or browser check; browser unavailable.
- Next: Lead dispatch Reviewer; no QA blockers.

## 2026-10-01 | MAP-010 | typed map coordinates | done
- Result: Added actual-template submit/clear and load/remove lifecycle coverage for invalid finite/range inputs, decimal endpoints, readiness transitions/rechecks, removed/all-removed panels, one/four-panel synchronization (including an already-centered source), retained view properties, and clear-without-pan/fetch. Rendered route tests check native labels/bounds/live status and selector absence; content tests check README/References wording. Updated scale lifecycle harness to bind the readiness helper. No production edits.
- Check: focused Flask route/content batch passed 50 tests; `node --test tests/test_map*.mjs` passed 13; scoped `git diff --check` passed. No live DB/provider access or browser connection.
- Next: Lead to review. Note: current `templates/maps.html` declares `let coordinateReadiness;`, while the backend handoff describes initialization to `false`; no exercised behavior defect, but reconcile before integration.

## 2026-09-30 | MAP-009 | manual saved-data retry | done
- Result: Node harness executes extracted viewport/load/retry functions and the template's actual click binding. Covers failure → single-panel retry → success, repeated click/failure, empty and invalid bounds, stale responses/controller finally, explicit AbortError after invalidation, late success after abort, movement debounce cancellation, removed/uninitialized panels, and native rendered per-month button/status semantics. References rendering asserts retry/cache-only caveats. No production edits.
- Check: `DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_locations_route tests.test_content_pages` passed (48; unchanged for follow-up). `node --test tests/test_map*.mjs` passed (8), rerun after abort cases. Scoped `git diff --check` passed. No live DB/provider operations or browser connection.
- Next: Reviewer; no QA blockers.

## 2026-09-30 | MAP-008 | readable map metric labels | done
- Result: Added rendered route coverage for all four readable labels in single/comparison headings, map ARIA names and selector captions. Kept raw option values, API `climate_type` keys, JS keys and one/four-month edit round trips asserted. Added provider-specific NOAA/CMIP6 and precipitation-rate copy checks; updated the Node status assertion to saved-grid wording. Updated References assertions for metric units, monthly average daily rate and the non-total caveat in both provider branches.
- Check: `DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_locations_route tests.test_content_pages` passed (47). `node --test tests/test_map*.mjs` passed (8, prior run; JS unchanged). No live database or browser.
- Next: Reviewer; no QA blockers.

## 2026-09-30 | MAP-007 | retained map selection | done
- Result: Route regressions submit actual parsed edit-form values and selected variable back to the ordinary map for one and four months, checking order, unavailable dates and no rediscovery; also cover precipitation, empty bare selector, generic discovery failure and pre-discovery 400 validation. Node executes the template's prefilled-row remove listener, add/renumber helpers, focus behavior, four-month cap and date-preserving suggestions.
- Check: `DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest tests.test_locations_route tests.test_content_pages` passed (45 tests). `node --test tests/test_map*.mjs` passed (8 tests, 0 failures). No browser/live data.
- Next: Reviewer; no QA blockers.

## 2026-09-30 | MAP-006 | popup row layout | done
- Result: updated the month XSS assertion for nested `strong`; added DOM checks
  that month and baseline have separate strong-only rows, the value has its own
  row, and the difference heading and number are separate rows.
- Check: `node --test tests/test_map*.mjs` passed (7); scoped
  `git diff --check -- tests/test_map_selection.mjs` passed. No browser check.
- Next: Reviewer; no QA blockers.

## 2026-09-30 | PAGES-002 | awareness copy | done
- Result: Updated stale Home assertions and added mocked, rendered NOAA/CMIP6 checks for awareness purpose, illustrative preview, provider-specific readouts, NOAA smoothing limits, and two-month trend caveat. Both References modes preserve the exact pre-change external URL set, units, cache gaps, and existing actions. No production edits.
- Check: `test_content_pages.py` passed 8; `test_noaa_location_readiness.py` passed 10; scoped `git diff --check` passed. Database reads fail if called. No browser, live data, full suite, or Node rerun.
- Next: Reviewer; no QA blockers.

## 2026-09-30 | MAP-005 | manual scale synchronization | done
- Result: `test_map_template.mjs` executes actual scale/redraw/render and
  load/remove handlers for both providers with full-loaded predicate false.
  Rapid preset/custom choices align ready rendering, saved scale and legend;
  pre-load choices govern first render. Uninitialized/removed panels remain
  untouched; cleared NOAA data stays absent. Existing async stale harness passes.
- Check: on `codex/map-scale-loading-sync` (base `89f4e15`), one offline unittest
  batch: 162 tests, eight expected skips (`DATABASE_URL=`; cleanup/availability
  flags zero; bytecode off). `node --test tests/test_map*.mjs`: seven passed.
  `git diff --check`: passed. No production edits or live operations.
- Next: Reviewer. Browser disconnected; user screenshot confirms MAP-004
  appearance, not this loading interaction. No QA blockers found.

## 2026-09-30 | MAP-004 review follow-up | finite legacy JSON | done
- Result: added canonical None/NaN/±Infinity and finite aggregation-overflow
  regressions in `test_map_interpolation.py`. Strict JSON serialization succeeds;
  interpolation holes and remaining finite nodes survive; legacy feature values
  stay finite. Developer's NOAA-only filtering/guard passes without production
  edits by QA.
- Check: offline unittest discovery restricted to `test_map_interpolation.py`
  (six passed), `test_locations_route.py` (34 passed), and
  `test_provider_identity.py` (eight passed); same disabled-live environment as
  below. Whitespace check passed. Full suite/Node were not repeated: JS unchanged.
- Next: Reviewer verify P2 fix, then Lead integration. Lead inspected prior
  synthetic PNG: smooth gradient and transparent missing-data gap confirmed.

## 2026-09-30 | MAP-004 | NOAA numeric raster / async readouts | done
- Result: on `codex/smooth-noaa-display` (base `5a557e0`), added focused fake-SQL,
  bilinear/color, holes, boundaries/dateline, Mercator, size-cap, popup and async
  source lifecycle tests. Updated template mocks for the additive raster path;
  local scale redraw recreates static sources without fetching. No defects found.
- Check: full offline `python -m unittest discover -s tests`: 160 tests, eight
  expected skips (`DATABASE_URL=`; cleanup/availability flags zero; bytecode off).
  `node --test tests/test_map*.mjs`: six passed. `git diff --check`: passed.
  Actual JS raster plus Node PNG encoder produced disposable
  `climate2-smooth-noaa.png`: 512 × 384, 10,396 transparent hole pixels.
- Next: Lead visual artifact check and Reviewer. Browser disconnected; no live
  database/provider/account operations, new dependencies or production edits.

## 2026-09-29 | MAP-003 | history links and coordinate form | done
- Result: Added fake-popup checks for selected-coordinate URL precision, distinct
  feature centers, zero/negative/inclusive endpoints, out-of-range omission,
  missing/loading/error links, and identical four-panel destinations. Added a
  rendered GET form semantics check with DB reads patched to fail.
- Check: Offline Python suite: 156 passed, 8 PostgreSQL skips. `node --test
  tests/test_map*.mjs`: all 3 suites passed. `git diff --check` passed. No
  browser or live data access.
- Next: Send results to Lead for review/integration; no QA blockers.

## 2026-09-29 | MAP-002 | numeric comparison readouts | done
- Result: added fake-Popup regressions for one/four panels, baseline, °C/mm/day,
  raw precision, estimate provenance, loading/missing/error/nonfinite/overflow,
  no negative zero, and panel removal. Updated stale cached-value wording tests.
- Check: full offline Python batch ran 155 tests and found three stale copy
  assertions; updated them and the affected 40 content/location tests passed.
  All three Node map suites passed, including async stale-response checks. Per
  batch instruction, the full Python suite was not rerun after these test-only
  corrections. No live database/provider calls; browser unavailable.
- Next: Lead integration; no unresolved QA findings.

## 2026-09-29 | PROVIDER-003 | activate saved NOAA public reads | done

- Result: updated current Home/References expectations for NOAA, asserted default propagation through public modules/app config, fake SQL provider parameters for history/map/saved dates, and admin copy in both modes. Existing CMIP6 map-fetch behavior tests now select CMIP6 explicitly. No production defect found.
- Check: offline Python suite passed 155 tests (8 PostgreSQL skips); three Node map suites passed; `git diff --check` clean. No live database/provider calls; browser unavailable.
- Next: Reviewer inspection; Lead integrates.

## 2026-09-29 | PROVIDER-002 | NOAA sampling and public copy | done

- Result: added ten offline regressions for finite/range validation, coordinate ties, dateline/poles/distance, NOAA fixed-sample versus exact CMIP6 history, cache-only missing sample, provider/request/sample/value chart identities and metric titles, and Home/Maps/Locations/References/footer copy in both modes with identical external citation URLs. No production defect found.
- Check: full offline unittest suite passed 152 tests (8 PostgreSQL skips); all three Node map suites passed; `git diff --check` clean. Fake data only; no live database/provider or browser check.
- Recheck: after reviewer wording correction, NOAA (10) and content-page (5) focused tests passed; assertions now describe separate latitude/circular-longitude rounding.
- Next: Reviewer inspects PROVIDER-002; Lead owns browser verification and integration.

## 2026-09-29 | PROVIDER-001 | immutable acquisition source | done

- Result: added seven fake-connection regressions under simulated NOAA public selection. They cover CMIP6 insert/update and migration rows, prefetch checkpoint and stale NOAA-only cache gaps, source-specific probes, distinct comparison inputs, NOAA public history/map reads, and disabled opt-in Open-Meteo fallbacks. No production defect found.
- Check: `DATABASE_URL= CLIMATE_CLEANUP_PG_TEST=0 CLIMATE_AVAILABILITY_PG_TEST=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests` passed 142 tests (8 PostgreSQL skips); `git diff --check` clean. No live database or provider calls.
- Next: Reviewer inspects PROVIDER-001; Lead integrates. Tests do not exercise a live database or actual provider responses.

## 2026-09-28 | PAGES-001 | Home and References clarity | done

- Result: replaced stale page-copy assertions with offline route checks for active CMIP6/inactive NOAA, date selection versus uneven coverage, °C and mean daily mm/day, linked comparison/manual scales, dated historical checkpoints, navigation/heading anchors, and all pre-refresh References citation URLs. Static page requests fail if they touch mocked climate data paths.
- Check: focused page suite passed (5 tests); full offline unittest suite passed (135, 8 PostgreSQL skips); `git diff --check` passed. No live database or provider requests.
- Next: Lead integrates and owns browser verification; no QA defect found.

## 2026-09-28 | MAP-001 | linked comparison map readouts | done

- Result: added fake-Popup coverage for single/four panels, independent values
  and units, zero/negative values, shared click coordinates, containing-cell
  matching, missing/loading/error, safe text, repeat selection, close, and
  removal. Template test executes the actual async load functions with deferred
  fake responses for stale success/failure and immediate loading. Updated the
  route assertion for popup labels moved to the external script.
- Check: requested offline unittest suite passed (133 tests, 8 skips); Node
  map tests passed (3), including template async checks; `git diff --check`
  clean. Fake data only; browser unavailable (no browser connector/permission).
- Recheck: after the instructional sentence clarified labelled display
  estimates, `node --test tests/test_map_template.mjs` passed (1 test).
- Next: Lead integration; no defects found in QA scope.

## 2026-09-27 | REVIEW-003 | database backup delimiters | done

- Result: expanded temporary-file GET/HEAD regressions for underscores,
  spaces, parentheses, punctuation, and sidecar backup delimiters; confirmed
  `dbpedia.js` and `thing.dbpedia.js` remain available.
- Check: full offline unittest suite passed (133 tests, 8 skips); Node map-scale
  test passed. No real account DB or provider was accessed.
- Next: Reviewer can continue; no defect found.

## 2026-09-27 | REVIEW-002 | database backup static denial | done

- Result: added anonymous GET/HEAD regressions for compound, sidecar, uppercase,
  tilde, and hyphen backup names; verified `dbpedia.js` remains available.
  Fixtures are temporary fake files only.
- Check: full offline unittest suite passed (133 tests, 8 skips); Node map-scale
  test passed. No real account DB or provider was accessed.
- Next: Lead integrates; no backend defect found.

## 2026-09-27 | QA-002 / SECURITY-001 | private account storage | done

- Result: added `test_private_account_storage.py` for resolver precedence and
  environment consumers, anonymous GET/HEAD static denials and asset access,
  aliases/traversal/loops, and setup connection closure on success/error. All
  fixtures use temporary fake files and SQLite only; no real database opened.
- Check: focused tests passed (9); full unittest suite passed (132, 8 skips);
  Node map-scale test passed. Import emitted the expected legacy-path warning.
- Next: Lead integrates; no test findings sent to Backend.

## 2026-09-27 | QA-001 | restructure regressions / climate package | done

- Result: independently reviewed the package entry points/resources. Existing
  `test_project_layout.py` covers Flask export, off-root SQL/template/static
  loading, and four safe CLI help commands; no test gap justified another test.
- Check: offline unittest suite passed 123 tests (8 PostgreSQL/integration
  skips); Node scale check, `bash -n run.sh`, and `run.sh --help` from `/private/tmp`
  passed. No live database/provider used.
- Next: reproduced `ResourceWarning: unclosed database` in
  `climate.cli.setup_user_database.initialize_user_database` with a temporary
  DB and `-W always::ResourceWarning`. The same code is present at base
  `cbeda44`, so it predates the restructure; send to Backend for a bounded fix.
  No production/test changes made. Checkpoint `9836be2` remains the base.
