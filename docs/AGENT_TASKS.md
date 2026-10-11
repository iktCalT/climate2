# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md), [architecture](ARCHITECTURE.md)
and [shared memory](agents/SKILL.md). Specialists run sequentially.

## Current assignment

**COORD-007 — concise handoff checkpoint (Lead, base `1d548e3` / PR #88).**
Consolidate completed assignments and Lead notes into existing context files,
correct stale status, preserve outstanding checks and recovery details.
Allowed: this board, Lead log, workspace/completed-rounds notes, PROJECT_DIRECTION
and the error-artwork status in NEXT_REQUIREMENTS. No other agent logs, runtime
files, data, caches or fixed REFACTOR edits. Validate links, revisions and diff;
no repeated application tests. No new implementation specialist assigned.
Result: board and Lead log substantially shortened; six Markdown files, 23 local links
and 33 referenced commits validated. Diff whitespace clean; publication follows.

## Remaining verification

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
