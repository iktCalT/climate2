# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md), [architecture](ARCHITECTURE.md)
and [shared memory](agents/SKILL.md). Specialists run sequentially.

## Latest assignment (complete)

**REGRESSION-004 — combined offline checkpoint after PR #97.**
Lead owns board, documentation status and own log. QA owns one full Python
unittest discovery and Node test batch, disposable isolation runner and own log;
no production or test edits without an assigned finding. Use existing .venv and
test conventions. Explicitly isolate account/community/session/chart/image
paths before app import; disable PostgreSQL opt-ins and block real provider/DB
connections. Do not read .env, start imports, use live stores, launch browsers
or change cloud settings. Report exact totals/skips and any test contamination.
Do not rerun full suites after a scoped correction. Reviewer is needed only
if a correction is assigned; no new product behavior is part of this checkpoint.

Result (2026-10-15, base `669afb6`): Python 234 total, 226 passed, eight
expected PostgreSQL skips, no failures/errors; Node 45 passed. Lead audited
the disposable runner: chart/image environment overrides were not consumed
by development config, but relevant tests used temporary directories/mocks;
no generated project output changed. Mode/fetch-enabled settings were inherited,
not explicitly pinned. Account/community paths and session default were isolated;
real PostgreSQL/HTTP calls were blocked. No corrections or reruns required.

## Previous assignment (browser follow-up complete)

Browser access is available again on 2026-10-13. Resume COMMUNITY-008 with
the same ownership and exclusions: QA prepares a fresh disposable full-route
fixture with schema-compatible synthetic NOAA data; Lead checks linked map
readouts, popup and typed pin drafts, consented publication/owner deletion,
and narrow layout. No production edits without a separately recorded defect.
Reuse the completed finite API checks; do not rerun old suites.

Browser result (2026-10-13, resumed 2026-10-15): actual full Maps route with
synthetic NOAA data and temporary SQLite passed linked same-location readouts
(12/17 °C, +5 °C difference), popup and typed drafts on both maps, explicit
profile/public consent, blank-message publication, own listing and owner
deletion. Deletion cleared both public markers and the own list. At 390px the
popup action remained reachable; page width fit 390/320px without horizontal
overflow. This is a bounded layout check, not an exhaustive mobile audit.
Browser tab closed and viewport reset. No production code changed; live climate
data, native Forget and actual expiry timing remain outside this check.

**COMMUNITY-008 — full Maps route integration, isolated storage.**
Lead owns board, own log, browser checks and integration. QA owns a disposable
loopback fixture and own log only. Use real Maps route/template/scripts and real
community API/service against a fresh temporary SQLite store; temporary cwd,
account/session/chart paths and explicit fake fixture configuration before app
import. Replace climate reads with synthetic values; block PostgreSQL and
provider network calls. Allow only the tested routes/public assets. Prominent
simulation banner; no credential output, real posts, live stores or cloud work.
Verify linked readouts → Add pin here → draft, explicit consented profile/publish,
owner list/delete, and narrow layout. Basemap assets may use existing credited
providers; no new resources. Record fixture adaptations honestly. Do not repeat
full suites or change production code unless a defect is assigned. Stop listener
and close test tab afterward. Native Forget and actual expiry timing stay out
of this bounded check; their current evidence is in prior QA records.

Initial result (before the browser follow-up above): isolated Flask test-client
checks passed for the real rendered Maps
page, synthetic map-data response and real SQLite-backed community service:
empty-message publication, owner listing, wrong-owner deletion rejected (403),
owner deletion and empty public list afterward. No connected browser was
available; JavaScript interaction, interpolation and full-page narrow layout
remain pending. No production files or live stores changed. Own fixture listener
stopped; the disposable script/store stay outside Git. See QA log COMMUNITY-008.

## Previous assignment (complete)

**COMMUNITY-006 — browser follow-up for PR #94 (`dc49935`).**
Lead owns board, own log and browser verification. QA owns a disposable loopback
fixture and own log only: real community templates/modules and map-selection
module with MapLibre, synthetic maps/pins and in-memory API; no production app,
database, provider, credential output or real publication. Verify ordinary
location popup → Add pin here → focused draft controls, typed entry, optional
message publish and owner deletion with explicit consent. Check narrow layout
and 500/501 Unicode form validation where practical. Existing expiry tests are
evidence; do not pretend 30 days elapsed in a browser. Full Maps-page integration
and native Forget dialog remain separate limitations. No production edits or
repeated full suite without a discovered defect. Stop fixture and close tab.

Browser finding: desktop popup-to-draft and message-free simulated publish/delete
pass; 390px center-click popup clips its trailing Add pin here button. Correction
**COMMUNITY-007** is recorded first in NEXT_REQUIREMENTS: Backend owns only
map_selection.js + own log, moving action immediately after selected coordinates.
QA owns focused map-selection ordering test + own log; Reviewer audits; Lead
rechecks live fixture. Preserve readouts, callback/consent and all server behavior.
Correction now passes browser action checks at 1280/390/320px and three focused
selection/template tests. Popup/typed drafts, empty-message simulated publish
and owner deletion passed; 500 emoji valid, 501 invalid, blank clears validation.
No observed console warnings/errors. Independent review clear. Tab closed,
viewport reset and fixture stopped; final state: one simulated POST, one owner
DELETE, zero active pins. Screenshots remain temporary, outside Git.

## Previous assignment (complete)

**COMMUNITY-005 — optional messages, popup entry and 30-day local ownership.**
Contract: first NEXT_REQUIREMENTS entry. Lead owns requirement, board and own
log; implementation → QA → review runs sequentially. No live stores or posts.
Implementation and focused QA complete: 12 community + 14 content Python
checks passed; initial combined Node run found one stale-consent issue, fixed
and verified with 23 community passes. Review found Unicode length mismatch,
corrected with 27 community/selection/template passes. Final review clear;
new popup/expiry behavior has no real-browser visual verification this round.

- Backend owns `climate/services/community.py`, `static/community_profile.js`,
  `static/community_pins.js`, `static/map_selection.js`, `templates/maps.html`,
  community templates, narrowly necessary CSS, README, References, COMMUNITY
  guide and own log. Preserve all server authorization/rate controls and existing
  map readouts. Add optional selection callback rather than coupling climate
  selection to community storage. No new dependencies or schema changes.
- QA owns focused community Python/Node, map-selection/template and content
  tests plus own log. Use isolated temporary stores and mock network only.
  Cover blank/omitted/invalid messages, draft-only popup action, disabled mode,
  coordinate entry, fixed expiry/legacy reuse/storage failures, own-only delete,
  stale active expiry and existing consent/marker/selection regressions.
- Reviewer is read-only except own log; audit security, integration/lifecycle,
  expiry semantics and documentation parity. Report fixes to Lead/Backend.
- Acceptance: both entry paths lead to the same explicit draft/publish flow;
  optional messages survive reads/deletes; temporary identity preserves owner
  checks and consent, never leaks credentials to public APIs. Focused tests and
  review required before integration; real-browser coverage reported separately.

## Previous assignment (verification round complete)

**COMMUNITY-004 — browser verification of profile forgetting and draft pins.**
Lead owns board, own log, browser checks and integration. QA owns only a disposable
loopback fixture and own log: real community templates/JS and MapLibre markers,
synthetic pins and in-memory APIs, no production app/database/provider imports.
Use a fresh test origin and synthetic local profile only. Verify consent on
profile creation, forget cancel/confirm, linked unpublished marker placement,
movement, cancellation and simulated publication. No live pin publication or
real user data. No new application behavior or repeated full suite; report any
defect before implementation. Stop fixture and close the test tab afterward.

Result (2026-10-12): linked draft placement/movement/clearing, explicit storage
and publication consent, simulated publication/comment popup and explicit profile
restore passed. One simulated POST, zero DELETEs. Native Forget confirmation
remains unverified because browser dialog automation stalled. This was a two-map
fixture, not full Maps-page integration or server security testing. Test tab
closed and fixture stopped; synthetic profile storage left on its fresh origin.

## Previous chart assignment (complete)

**LOCATION-UI-006 — compact location-chart browser confirmation.**
Lead owns board, own log and browser checks. QA owns only a disposable loopback
fixture and own log: real Locations template/chart helper, labelled synthetic
values, temporary chart output, no application/DB/account/provider imports or
live fetching. Check four metrics at desktop and 390/320px, readable compact
titles/context and metric switching. Do not repeat prior suites or edit production
code; report defects for assignment. Reset viewport and stop fixture afterward.

Browser finding: compact titles fit, but the season legend wraps upward into
them at 390/320px. LOCATION-UI-007 now owns this bounded correction: Backend
may edit chart layout in `climate/web/helpers.py`, chart cache version only in
`climate/web/app.py`, README/References description if needed, and own log.
Preserve calculations/source/fetch behavior. QA follows with focused chart/cache
tests (temporary outputs only), then Reviewer audits; Lead repeats browser
checks. Record: first NEXT_REQUIREMENTS entry. No new dependencies or live data.
Current result: v9 layout passes all four metrics at 1280/390/320px in the
synthetic browser fixture; QA's 56 focused offline tests pass. Independent review
clear; merged in PR #92 (`b1b1483`). Test tab closed and viewport reset; no listener
remained on fixture port 5012 at the final check.

## Previous browser assignment (complete)

**ADMIN-UI-007 — isolated browser confirmation of PR #90 (`8c8bb90`).**
Lead owns this board and own log, browser checks and integration. QA owns a
temporary loopback fixture and own log only: render real admin template/JS with
labelled synthetic responses, no production app import, accounts, PostgreSQL,
provider calls or real jobs. Verify defaults, explicit simulated start/status
and desktop/narrow layout. No application changes or repeated offline suite.
Remove no user artifacts; stop the fixture and reset browser overrides afterward.
Result: connected in-app browser passed defaults, explicit simulated start,
running/completed state and 1280/390/320px layout. Exactly one `last`/1 POST;
opening made only a status GET. No console warnings/errors or horizontal overflow.
This validates real templates/JS with synthetic responses, not live acquisition
or authenticated browser sessions. Published in PR #91 (`8347909`).

## Previous assignment (complete)

**ADMIN-UI-006 — NOAA Update-page workflow and defaults.**
Owner chose the existing monthly importer. Contract: first NEXT_REQUIREMENTS entry.
Implementation, 56 focused offline tests and independent review are complete
(2026-10-11); merged in PR #90 (`8c8bb90`). No live imports were started.

- Lead owns requirement/board and own log. Backend owns only `/update` route and
  dead imports/constants in app.py, old update template removal, admin_data and
  layout templates, Docker exact-file allowlist, README/References/USER_ROLES and
  own log. Keep `/admin/data` security, import service and cleanup unchanged.
- QA then owns admin-role/import/content and narrowly affected tests plus own
  log. Verify both GET/POST access controls, safe redirect, legacy POST rejection
  with no acquisition, selected recent window/one-month default, existing CSRF
  API behavior and removed-template inventory. Temporary app/account/session
  state and mocked downloads only. No test weakening or production edits.
- Reviewer follows read-only except own log: source identity, no accidental
  downloads, authentication/CSRF, documentation/defaults parity.
- No live data/cloud operations or new dependencies. Existing browser connection
  absent; report missing visual verification rather than claiming a pass.

Previous COORD-007 handoff cleanup merged in PR #89 (`3cc6534`); historical
evidence remains indexed, no repeat needed.

## Remaining verification

- **COMMUNITY-008:** finite API checks and bounded full-page browser integration
  now pass with synthetic climate data and temporary SQLite (see above). No
  live provider/data verification, exhaustive mobile audit, native Forget or
  elapsed 30-day browser-expiry claim. Earlier component-only limitations remain
  historical, not a reason to repeat completed checks.
- **ADMIN-UI-006/007:** NOAA admin-page visual/default checks passed with simulated
  responses; access-control and API checks passed offline in PR #90. No live
  import or real administrator browser session was exercised.
- **LOCATION-UI-005/006/007:** compact titles and the corrected v9 legend pass
  desktop and 320/390px browser checks for all four metrics with synthetic data.
- **COMMUNITY-002:** real-browser profile-forget confirm/cancel remains unverified;
  dialog automation stalled. Offline confirmation tests passed previously.
- **COMMUNITY-003/004:** draft appearance/lifecycle and consent-gated simulated
  publication passed with real community JS and MapLibre in a two-map fixture.
  Full Maps-page integration and live server security were not exercised.
  Use synthetic profiles/pins only, never live publication merely to test UI.
- **COMMUNITY-005/006/007:** new popup/typed entry, optional-message simulated
  publication/deletion and Unicode form bounds passed in the isolated browser
  fixture. Corrected button works at desktop and phone widths. The fixture uses
  real modules/templates/map sizing, not the entire Maps route; actual 30-day
  expiry remains covered by offline clock-controlled tests, not elapsed browser time.
- **LOCATION-FETCH-004:** one unattributed MutationObserver browser error remains
  unisolated. No matching app call was found; do not call it an application bug
  without evidence. It recurred during LOCATION-UI-006, without a source URL.
  Simulated fetch progress/refresh/throttle/Retry passed.
- Actual container build, hosted operation, production load/security and opt-in
  PostgreSQL integration tests are not established by offline checks.
  These limitations are not permission to deploy or use live stores.

## Paused / deferred

**DEPLOY-005:** Google Cloud + Cloudflare hosting paused by owner on 2026-10-08.
Do not resume cloud account, billing, domain, VM, DNS or data-transfer work until
the owner resumes it. Prior authentication and billing/project verification were
incomplete. Preserve local startup and portable production configuration.
See [deployment requirements](NEXT_REQUIREMENTS.md#google-cloud-launch-with-a-portable-migration-path).

Community clustering remains deferred until density/performance warrants it.
Public comments stay disabled until operator configuration; implementation
checks did not create a real administrator.

## Latest completed checkpoint

**REGRESSION-004, base `669afb6` (2026-10-15):** Python discovery ran 234
tests: 226 passed, eight expected PostgreSQL skips, zero failures/errors.
All 45 Node tests passed. Isolation details and limitations are recorded above
and in the QA log. No application/test edits, live provider/database operation,
or new browser claim; no repeated batches after this checkpoint.
Prior REGRESSION-003 remains in the indexed historical handoff.

Details: [completed rounds](agents/context/completed-rounds.md),
[QA log](agents/qa-log.md), [reviewer log](agents/reviewer-log.md).
Completed handoffs are history, not instructions to redo the work.

## Recovery and scope

Retain both stashes: `climate2 REGRESSION-001 checkpoint before README demo request`
and `climate2 pre-layout working changes`. Do not reapply blindly.
No caches, environments, databases or user data are scheduled for cleanup.
Read [workspace](agents/context/workspace.md) before branching; use local Meow-5
identity and climate2 only. Removed Cursor rules remain recoverable in Git;
guidance lives in root AGENTS.md and PROJECT_DIRECTION.
Full prior board: `git show 1d548e3:docs/AGENT_TASKS.md`.
