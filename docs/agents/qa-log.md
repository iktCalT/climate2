# Test / QA log

Writer: Agent 3 only. Follow [SKILL.md](SKILL.md).

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
