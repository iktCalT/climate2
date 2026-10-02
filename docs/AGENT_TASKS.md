# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md),
[architecture](ARCHITECTURE.md) and [shared memory](agents/SKILL.md).
One specialist at a time: Developer → QA → Reviewer → Lead integration.
Use the [economical model and batched checks policy](PROJECT_DIRECTION.md#sequential-managed-team).

## Current assignment

**REGRESSION-001 — resumed offline checkpoint (complete).** Base
`5b17b0d` (PR #75), branch `codex/finish-offline-regression`.

- Lead: this board, architecture verification commands, workspace/completed
  context and own log. Preserve indexed history and recovery references.
- QA: only `tests/test_noaa_location_readiness.py` and own log. Correct stale
  precipitation copy while retaining daily-rate mm/day and not-monthly-total
  semantics for both providers. Rerun affected module; no full-suite repetition.
- Reviewer: read-only evidence/diff review and own log. Sequential Luna/medium.
- No product behavior, dependencies, live data, browser or deployment changes.

Original batch at `50af280`: Python 182 total (173 passed, eight expected
PostgreSQL skips, one stale copy assertion); Node 13 passed. After correction:
10 affected Python tests passed on 2026-10-02. Do not describe this as a fresh
all-green full run. Eight skips: four weather, three cleanup, one availability.
Provider/climate reads were mocked; inherited filesystem sessions remain a test
isolation limitation. No PostgreSQL integration or browser verification claimed.

Independent review cleared the assertion correction and checkpoint evidence.
No outstanding regression from this batch remains; publication status is in GitHub.

## Latest integration and prior work

README-DEMO-001 merged in PR #75 (`5b17b0d`); 11 content tests passed.
HISTORY-002 merged in PR #74 (`50af280`); 57 focused route/content tests passed.
See [completed rounds](agents/context/completed-rounds.md) for earlier outcomes.
Completed assignments are not active tasks; full prior scopes remain in
`git show 5b17b0d:docs/AGENT_TASKS.md`.

## Recovery and limitations

The named stash `climate2 REGRESSION-001 checkpoint before README demo request`
on `codex/offline-regression-checkpoint` retains the original three-file
documentation checkpoint. Its useful commands/evidence are now reconciled into
this branch; retain it as recovery, not an instruction to reapply older files.
The separate `climate2 pre-layout working changes` stash remains untouched.

NOAA is the startup public provider; no deployment/restart was verified.
See [data/map context](agents/context/data-and-maps.md) for dated coverage and
CMIP6 caveats, and [workspace](agents/context/workspace.md) before branching.
