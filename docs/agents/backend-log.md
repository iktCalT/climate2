# Backend Developer log

Writer: Agent 2 only. Follow [SKILL.md](SKILL.md).

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
