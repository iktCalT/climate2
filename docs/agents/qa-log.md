# Test / QA log

Writer: Agent 3 only. Follow [SKILL.md](SKILL.md).

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
