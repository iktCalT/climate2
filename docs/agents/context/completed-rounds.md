# Completed implementation rounds

Index refreshed 2026-10-04 from main `ea5cd56` and agent handoffs. These are
completed tasks, not assignments. Product contracts remain in
[requirements](../../NEXT_REQUIREMENTS.md); current scope is on the
[task board](../../AGENT_TASKS.md). Python counts include the eight skipped
PostgreSQL integration tests in full runs; focused counts are listed separately.
No production database was used for these suites. Results below are historical,
not tests rerun during the documentation refresh.

- **DEPLOY-003 / DEPLOY-004 / UI-002:** hosting comparison, portable production
  config/private state/proxy trust, exact-file container context, numeric wheel
  guard. Initial Python 211: 202 passed/eight PG skips/one static hardlink failure;
  Node 20 passed. Corrections independently verified by 58 focused passes;
  review clear. Real image build, browser and hosting not verified or performed.
- **REGRESSION-002, tested base `083ead5`:** combined offline Python run on
  2026-10-02: 204 total, 196 passed/eight expected PostgreSQL skips/no failures;
  Node 18 passed. No production/test changes. Documentation evidence reviewed
  2026-10-03; browser/live deployment remain unverified.
- **DEPLOY-002, PR #78, `083ead5`:** terminal-only administrator creation with
  hidden input, private initialized storage and atomic user/profile inserts.
  CLI dispatch and public-symlink defects corrected; final 27 focused checks
  passed under QA and Reviewer. No real account creation or deployment.
- **UI-001 / DEPLOY-001 / COMMUNITY-001, PR #77, `1ed0b65`:** concise public
  pages, hosted registration closure, world map and opt-in local profiles/public
  pin comments. Feature defaults disabled pending private deployment config.
  Full Python 192: 182 passed/eight skipped/two errors, corrected community
  module nine passed; final path/portable-test follow-up 22 passed. Node 18
  passed; independent review clear. No browser or live deployment verification.
- **REGRESSION-001, PR #76, `7342c9e`:** corrected stale precipitation-copy
  assertion; affected module 10 passed. Original full batch 182 total,
  173 passed/eight skipped/one stale assertion; Node 13 passed. Full batch not
  repeated after correction; no production change.
- **README-DEMO-001, PR #75, `5b17b0d`:** owner-supplied NOAA comparison
  screenshot with caption, alt text and provenance. Original PNG checked;
  11 content tests passed. No runtime/data change.
- **HISTORY-002, PR #74, `50af280`:** editable requested coordinates on
  populated/empty Location results; Clear returns to blank entry. 57 focused
  route/content tests passed; review cleared.
- **HISTORY-001, PR #73, `a6491c1`:** seasonal contributing-month counts,
  explicit missing-year gaps, units and chart version v7. Existing means and
  winter assignment retained; 59 focused chart/route/content tests; review clear.
- **MAP-010, PR #72, `eab3e85`:** typed coordinates center synchronized maps
  and open linked readouts. Readiness/removal guards, unchanged manual scale;
  50 focused Python and 13 Node tests; review cleared.
- **COORD-005, PR #71, `69b6a04`:** shortened board, indexed completed work,
  reconciled handoffs. Five-file scope, 16 local links and 16 revisions checked.

- **MAP-009, PR #70, `ef5de20`:** manual per-panel saved-data retry, guarded
  against repeats, stale/aborted requests and removed panels. 48 focused Python
  and eight Node tests; explicit abort/late-success follow-up; review cleared.
- **MAP-008, PR #69, `0a5f5ef`:** readable metric labels/units, daily-rate and
  saved-grid wording; raw keys unchanged. 47 focused Python and eight Node tests.
- **MAP-007, PR #68, `f95d638`:** ordered months/metric survive map edit and
  resubmission; server-rendered values and validation retained. 45 focused
  Python and eight Node tests, including actual form round trip/removal.
- **MAP-006, PR #67, `d0bafd6`:** separate block rows for popup labels/values;
  safe text and numeric behavior unchanged. Seven Node tests; review cleared.
- **PAGES-002, PR #66, `60d4a92`:** awareness purpose, illustrative preview,
  coarse estimates and two-month trend caveat. 18 focused Python tests;
  both provider renderings and existing credits preserved; review cleared.
- **MAP-005, PR #65, `435129a`:** manual scales update initialized panels
  during source loading; no automatic scale changes. Full 162 Python tests
  (eight expected skips) and seven Node tests; review cleared.
- **MAP-004, PR #64, `89f4e15`:** bounded bilinear NOAA display with labelled
  estimates, null holes and consistent readouts. Full 160 Python tests (eight
  skips), six Node tests; 48 focused Python checks after finite-JSON correction.
  Synthetic raster inspected; user screenshot confirmed appearance, not live
  interaction coverage. Review cleared; no provider download changes.
- **COORD-004, PR #63, `5a557e0`:** compact board/Lead log and indexed context;
  25 local links, eight merge revisions and scoped diff checks passed. No
  application or cache changes.

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
`git show 5b17b0d:docs/AGENT_TASKS.md` and
`git show 5b17b0d:docs/agents/lead-log.md` (latest compacted scopes);
use revision `002223e` for earlier assignments.
