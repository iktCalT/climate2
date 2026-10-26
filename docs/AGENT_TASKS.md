# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md), [architecture](ARCHITECTURE.md)
and [shared memory](agents/SKILL.md). Specialists run sequentially.

## Latest coordination round (complete)

**COORD-008 — reconcile completed handoffs (2026-10-26).** Lead owns this
four-file documentation round on base `a51e9b3`: this board, workspace context,
completed-round context and own log. Preserved unresolved limits, recovery refs
and other agents' logs. Validation: 19 local links and 44 cited revisions resolve;
scoped diff is clean. No repeated suites, browser, application edits, live data
or deployment.

No production implementation is currently assigned. Completed handoffs below
are evidence, not instructions to repeat work. Lead must define the next task's
owner, files and acceptance criteria before implementation.

## Latest completed work

- **COMMUNITY-010, PR #100, `a51e9b3`:** comment popups fit an 8px map inset;
  long content wraps/scrolls and close remains keyboard-accessible. QA 27 Node
  + 14 offline content checks; independent review clear. Isolated real Maps-page
  checks passed at 320/390/1280px, including the original message, 500-character
  unbroken/multiline comments, keyboard scrolling/close and reopening after resize.
  Original 320px case: map x=12–308, popup x=60–300. Test tab closed, viewport
  reset and disposable server stopped. No live posts/data or cloud changes.
- **TEST-TOOLS-001, PR #99, `79778d2`:** reusable offline Python runner.
  Full run: 238 total, 228 passed/eight expected PostgreSQL skips/two enabled-UI
  fixture failures. Scoped fixture fixes then passed Locations 50/50; runner
  lifecycle 4/4 passed. No full rerun; independent review clear.
- **REGRESSION-004, PR #98, `9fcd08a`, tested base `669afb6`:** Python
  234 total, 226 passed/eight expected PostgreSQL skips; Node 45 passed. No
  application/test edits. This is historical evidence, not a new test run.
- **COMMUNITY-008/009:** full Maps route with synthetic climate/temporary SQLite
  passed linked readouts, popup/typed drafts, consented publication, own listing
  and deletion. Keyboard/mobile follow-up found the clipping fixed in #100.
  Native Forget did not complete; see limits below.

Earlier tasks and merge revisions: [completed rounds](agents/context/completed-rounds.md).
Detailed results: [QA log](agents/qa-log.md), [reviewer log](agents/reviewer-log.md).
Full pre-compaction board and scopes: `git show a51e9b3:docs/AGENT_TASKS.md`.

## Remaining verification and limits

- **Native Forget:** real-browser Cancel/Confirm and post-forget public-pin
  survival remain unverified. Dialog automation stalled; Safari fallback was
  interrupted. Offline tests passed. Do not repeat the stalled attempts as part
  of another task; arrange a separately scoped dialog-capable/manual check.
- **Community:** synthetic full-page and bounded keyboard/mobile checks passed,
  not exhaustive accessibility, production security/load, live posts or actual
  elapsed 30-day browser expiry. Expiry has clock-controlled offline tests.
- **NOAA administrator page:** defaults/start/status and narrow layout passed
  with simulated responses; access controls/API passed offline. No live import
  or real administrator browser session exercised.
- **Locations:** v9 compact chart titles/legend passed all four metrics at
  desktop and 320/390px. Simulated gap-fetch progress/refresh/throttle/Retry
  passed. One unattributed MutationObserver browser error remains unisolated;
  do not call it an application defect without source evidence.
- Actual container build, hosted operation and opt-in PostgreSQL integration
  are not established by offline checks. No live DB, migration, data cleanup,
  provider fetch or cloud work is authorized by these verification gaps.

## Paused / deferred

**DEPLOY-005:** Google Cloud + Cloudflare hosting paused by owner on 2026-10-08.
Do not resume accounts, billing, domain, VM, DNS or transfers until requested.
Preserve local startup and portable production configuration. See
[deployment requirements](NEXT_REQUIREMENTS.md#google-cloud-launch-with-a-portable-migration-path).

Community clustering remains deferred until density/performance warrants it.
Public comments stay disabled until operator configuration; implementation
checks did not create a real administrator.

## Recovery and scope

Retain both stashes: `climate2 REGRESSION-001 checkpoint before README demo request`
and `climate2 pre-layout working changes`. Do not reapply blindly.
No caches, environments, databases or user data are scheduled for cleanup.
Read [workspace](agents/context/workspace.md) before branching; use repository-local
Meow-5 identity and climate2 only. Removed Cursor rules remain recoverable in
Git; guidance lives in root AGENTS.md and PROJECT_DIRECTION.
