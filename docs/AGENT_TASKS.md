# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md), [architecture](ARCHITECTURE.md)
and [shared memory](agents/SKILL.md). Specialists run sequentially.

## Current assignment

**REGRESSION-002 — combined deployment-feature checkpoint (reviewed; Lead integration).**
Base `083ead5` (merged PR #78), branch `codex/deployment-regression-checkpoint`.

- QA: run the documented offline Python discovery and all map/community Node
  suites once; inspect isolation before running, report exact counts/skips and
  real regressions. Write only own log; no production/test edits unless Lead
  assigns a reproduced failure separately. No live database, provider or account
  operations. Existing tests use mocked/temporary data; do not enable PG opt-ins.
- Lead: board, own log, workspace/completed-rounds context and verification
  evidence. No feature implementation. Browser inventory is empty and native
  connection failed; listed browser skill file unavailable. Do not claim visual
  verification. Hosting target requested from owner, not assumed.
- Reviewer: inspect checkpoint evidence/documentation read-only except own log;
  do not repeat unchanged suites. Developer only if a confirmed fix is assigned.
- Acceptance: fresh combined results covering UI/community and terminal-admin
  rounds, accurate limitations, concise handoff. No app/References/dependency,
  deployment configuration or permission changes.

## Verification result

QA ran the documented offline batch once at `083ead5` on 2026-10-02:
Python **204 total: 196 passed, eight expected PostgreSQL skips**, no failures;
Node **18 passed**, none skipped or failed. The skips are three cleanup, one
availability and four weather integration tests. See the newest
[QA handoff](agents/qa-log.md) for exact commands and isolation limitations.

No production or test changes were needed. Legacy account-path warnings,
SQLite ResourceWarnings and expected mocked-failure logs appeared. Inherited
filesystem sessions remain incompletely isolated. These results do not establish
browser appearance, live PostgreSQL, proxy behavior or deployment readiness.
Lead is finishing the documentation checkpoint on 2026-10-03 without rerunning
unchanged suites.
Independent evidence review is clear; no remaining checkpoint blocker.

## Completed features

- DEPLOY-002, PR #78 (`083ead5`): terminal-only administrator provisioning,
  private storage, hidden input, atomic creation. Final 27 focused tests passed;
  independent review clear. No real administrator was created.
- UI-001 / DEPLOY-001 / COMMUNITY-001, PR #77 (`1ed0b65`): concise public pages,
  closed registration, world map, opt-in local profile/public pins. Previous
  batch 192 total: 182 passes/eight skips/two errors, both corrected. Latest
  focused 22 and Node 18 passed; the combined checkpoint above supersedes that
  earlier verification limitation.
- Contracts are in [requirements](NEXT_REQUIREMENTS.md), with deployment,
  moderator provisioning and remaining limits in [community](COMMUNITY.md).
  Community stays disabled until configured; clustering is deferred.

Earlier scopes/results: [completed rounds](agents/context/completed-rounds.md).
Full previous board: `git show 083ead5:docs/AGENT_TASKS.md`.

## Recovery and limitations

Retain both recovery stashes: `climate2 REGRESSION-001 checkpoint before README demo request`
and `climate2 pre-layout working changes`. Do not reapply blindly.
No caches, environments, databases or user data are scheduled for cleanup.
Read [workspace](agents/context/workspace.md) before branching. Browser,
deployment, live PostgreSQL and production load/security validation remain open.
