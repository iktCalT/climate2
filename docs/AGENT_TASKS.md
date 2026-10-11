# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md), [architecture](ARCHITECTURE.md)
and [shared memory](agents/SKILL.md). Specialists run sequentially.

## Current assignment

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
or authenticated browser sessions. Lead owns documentation publication.

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

- **ADMIN-UI-006/007:** NOAA admin-page visual/default checks passed with simulated
  responses; access-control and API checks passed offline in PR #90. No live
  import or real administrator browser session was exercised.
- **LOCATION-UI-005:** check the compact v8 chart at desktop and 320/390px widths,
  including all four metrics. Implemented/reviewed in PR #87; post-fix browser
  confirmation remains pending because the connection was absent.
- **COMMUNITY-002/003:** real-browser profile-forget confirmation and draft-pin
  appearance/lifecycle remain unverified; offline tests passed. Use synthetic
  profiles/pins only, never live publication merely to test the UI.
- **LOCATION-FETCH-004:** one unattributed MutationObserver browser error remains
  unisolated. No matching app call was found; do not call it an application bug
  without evidence. Simulated fetch progress/refresh/throttle/Retry passed.
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

**REGRESSION-003, PR #88 (`1d548e3`):** isolated Python discovery at `bdfbef9`
ran 230 tests: 221 passed, eight expected PostgreSQL skips, one stale setup-count
assertion failed. Corrected it to require all three SQL scripts and both
location-fetch tables; three affected tests then passed. All 36 Node tests passed.
Full batches were not repeated after correction; independent review clear.
No application change, live provider/database operation or new visual claim.

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
