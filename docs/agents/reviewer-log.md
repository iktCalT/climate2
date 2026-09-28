# Reviewer / Debugger log

Writer: Agent 4 only. Follow [SKILL.md](SKILL.md).

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
