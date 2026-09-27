# Agent task board

The Lead owns this board. Read [roles](AGENT_ROLES.md),
[architecture](ARCHITECTURE.md), and [shared memory](agents/SKILL.md).
Agents 2–4 start their assignment when the user forks them; none were launched
by the Lead. Report results in your own log and stop at the task boundary.

## Current assignments

- **Agent 1 — LAYOUT-001:** Lead restructure, validation, and fork handoff.
- **Agent 2 — BACKEND-001:** review package entry points and correct confirmed
  restructuring defects. Ready for the Backend fork.
- **Agent 3 — QA-001:** independent regressions and missing layout coverage.
  Ready for the QA fork.
- **Agent 4 — REVIEW-001:** independent correctness/security review.
  Ready for the Reviewer fork.

## LAYOUT-001 — Lead / Architect

Status: complete. User-authorized exception permits the Lead to move code
and update paths/tests before the other agents are forked. Baseline is local
main `cbeda44`, with existing artwork and coordination work preserved.

Scope: `climate/`, root `app.py`/`run.sh`, `sql/`, import/path updates in tests,
project documentation, and the Lead log. Acceptance: logical package layout,
preserved application behavior, documented command migration, passing offline
checks, and non-overlapping fork assignments. No provider activation, live
imports, database cleanup/migration, or framework changes.

Verification: 123 Python tests (8 database skips), Node scale test, CLI/resource
checks, unchanged core behavior/SQL checks, and local HTTP 200 smoke checks.
Visual browser verification was unavailable (no connected browser). Fork from
the checkpoint on `codex/project-structure`; Lead owns integration after review.

## BACKEND-001 — Agent 2

Inspect the new module boundaries, Flask entry point, CLI entry points, and
resource resolution. Fix only confirmed restructuring regressions in `climate/`,
`app.py`, or `run.sh`. No planned feature work. Run relevant checks; send test
requests to QA and documentation corrections to Lead. Write `backend-log.md`.
Acceptance: report reviewed paths, defects/fixes, commands/results, and remaining
issues. Coordinate any edit to a file another agent is inspecting.

Fork prompt: “You are Agent 2, Backend Developer. Read AGENTS.md and perform
BACKEND-001 in docs/AGENT_TASKS.md. Do not inherit the Lead role.”

## QA-001 — Agent 3

Run the documented offline Python and Node suites; check CLI help, SQL resource
resolution, templates/static serving, and preserved public/admin behavior.
Add focused missing tests only in `tests/`; report production defects to Backend.
Use temporary data and mocks; existing PostgreSQL tests must remain skipped
unless an isolated test database is explicitly set up for the task. Do not
introduce pytest or change dependency management. Write `qa-log.md`.
Acceptance: reproducible results and useful coverage, with skip reasons stated.

Fork prompt: “You are Agent 3, Test / QA. Read AGENTS.md and perform QA-001 in
docs/AGENT_TASKS.md. Own tests, not production code.”

## REVIEW-001 — Agent 4

Review the completed restructure relative to baseline `cbeda44`. Existing
artwork changes were preserved alongside module moves; account for both.
Inspect imports, paths, provider identity, authentication/CSRF, SQL boundaries,
secret handling, tests, and documentation. Read-only code review; write only
`reviewer-log.md` (shared-skill improvements remain permitted). Report findings
with severity, file/line, evidence, and requested owner; do not implement fixes.
Acceptance: actionable findings or an explicit no-findings report with limits.

Fork prompt: “You are Agent 4, Reviewer / Debugger. Read AGENTS.md and perform
REVIEW-001 in docs/AGENT_TASKS.md. Review first; do not patch code.”

## Completed coordination

COORD-001/002: [roles and memory setup](agents/context/coordination-history.md).
COORD-003: [indexed context and local cache cleanup](agents/context/maintenance.md).
The Lead handles integration after the three handoffs; agents do not merge or
start another task independently.
