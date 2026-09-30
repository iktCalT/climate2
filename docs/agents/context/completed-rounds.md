# Completed implementation rounds

Index recorded 2026-09-30 from main `002223e` and agent handoffs. These are
completed tasks, not assignments. Product contracts remain in
[requirements](../../NEXT_REQUIREMENTS.md); current scope is on the
[task board](../../AGENT_TASKS.md). Python counts include the eight skipped
PostgreSQL integration tests; no production database was used for these suites.

- **MAP-003, PR #62, `002223e`:** explicit map-to-history links and accessible
  coordinate form. 156 Python tests; three Node suites; review cleared.
- **MAP-002, PR #61, `dfcab70`:** first-month signed differences and cached-value
  wording. Negative zero/removal bugs fixed. Python batch: 155 tests, three stale
  assertions corrected, 40 affected tests rechecked; three Node suites passed.
- **PROVIDER-003, PR #60, `ee0e568`:** NOAA startup public selector; immutable
  CMIP6 writes, conditional admin copy, restart/rollback docs. 155 Python tests,
  three Node suites; review cleared. No deployment/data operation performed.
- **PROVIDER-002, PR #59, `7211024`:** fixed NOAA location-grid sampling,
  provider-aware chart/cache identity and labels. 152 Python tests; three Node
  suites. Coordinate-wise rounding wording corrected (not geodesic nearest).
- **PROVIDER-001, PR #58, `5a2df92`:** immutable acquisition identities,
  provider-isolated fallback/comparison. 142 Python tests; three Node suites.
- **PAGES-001, PR #57, `380197d`:** Home/References clarity, retained credits.
  135 Python tests; desktop Home/narrow References synthetic browser check.
- **MAP-001, PR #56, `a86172a`:** linked readouts with stale-response protection.
  133 Python tests, three Node suites, synthetic linked-popup browser check.
- **LAYOUT-001 / SECURITY-001, PR #55, `04d0ac1`:** package restructure plus
  private account path/static-download protections and connection closure.
  Backend/QA/Review `*-001`, `*-002`, `REVIEW-003` assignments are complete.
  Final 133 Python tests and Node checks passed. No real account DB was moved.

Recent rounds after PAGES-001 had no connected browser; passing offline tests
does not establish visual behavior. See [data/map context](data-and-maps.md)
for preserved audit limitations and [coordination history](coordination-history.md)
for setup. Other agents retain ownership of their detailed logs.

Recover pre-compaction task scopes and Lead evidence without transcript copies:
`git show 002223e:docs/AGENT_TASKS.md` and
`git show 002223e:docs/agents/lead-log.md`.
