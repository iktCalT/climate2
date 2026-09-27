# Agent roles and handoffs

These are the four roles for climate2. Root [AGENTS.md](../AGENTS.md) remains
the shared workflow entry point. The user or Lead assigns each agent a role
and a bounded task; a role alone is not an instruction to start implementation.

## 1. Lead / Architect

Responsibilities: understand the repository, design changes, decompose tasks,
and review architecture.

Skills: `repo-understanding`, `architecture`, `api-design`, `database-design`,
`security-review`.

- Inspect structure, entry points, dependencies, relevant code, and project
  requirements before designing changes.
- Record new requirements in the appropriate project document before
  implementation; leave `REFACTOR.md` unchanged.
- Define API/data contracts, constraints, acceptance criteria, dependencies,
  file ownership, and verification for each task.
- Maintain [AGENT_TASKS.md](AGENT_TASKS.md), resolve ownership conflicts, review
  architectural impact, and coordinate integration and authorized publication.
- Default edit scope is planning and coordination documentation. Delegate
  production implementation and test authoring to their respective owners.
  Record any explicitly assigned cross-role exception before editing.

## 2. Backend Developer

Responsibilities: main Flask/Python implementation.

Skills: `python-project`, `flask-backend`, `sqlalchemy`, `api-design`, `debugging`.

- Implement the assigned routes, services, data access, and related code within
  the agreed contracts and file boundaries.
- Reproduce relevant bugs, inspect logs safely, and verify fixes with focused
  development checks. Running tests is part of implementation ownership.
- Coordinate test cases with QA; edit shared test files only when assigned.
- Report required API/schema changes to the Lead before changing the design.
- Do not independently start frontend redesigns, data backfills, database
  cleanup, dependency migrations, or unrelated refactors.

## 3. Test / QA Agent

Responsibilities: write tests, reproduce bugs, and run regressions.

Skills: `pytest`, `flask-testing`, `debugging`, `test-authoring`.

- Translate acceptance criteria and bug reports into focused tests, including
  invalid input, authorization, failure paths, and regressions where relevant.
- Own assigned tests, fixtures, and reproducible bug reports. Use isolated test
  databases and mock external services; never mutate production data.
- Use pytest-oriented practices where applicable, while preserving the existing
  test runner and conventions unless a migration is explicitly assigned.
- Report commands, pass/fail results, reproduction steps, and coverage gaps.
- Send production-code defects to Backend and design gaps to the Lead; do not
  patch application code or weaken assertions simply to make a suite pass.

## 4. Reviewer / Debugger

Responsibilities: review completed changes and hunt for correctness and
security problems.

Skills: `code-review`, `debugging`, `security-review-web`, `database-debugging`,
`refactor-safely`.

- Review diffs and relevant surrounding code for correctness, edge cases,
  regressions, maintainability, security, database behavior, and test coverage.
- Use safe, non-mutating diagnostics to test hypotheses. Report severity,
  affected file/line, evidence, impact, and a concrete fix recommendation.
- Verify fixes and identify remaining risks; distinguish confirmed defects
  from hypotheses and optional improvements.
- Default to read-only review. Do not implement fixes, refactor code, edit tests,
  or merge independently unless a bounded task explicitly assigns that action.
  Maintaining your own handoff log and the common memory skill is permitted.

## Shared boundaries

- Skill lists express intended expertise. They do not imply that those skills
  are installed, or require adopting a package such as SQLAlchemy or pytest.
  Report unavailable skills and use the existing project conventions.
- Only work on the assigned task and allowed files. Necessary scope changes go
  to the Lead first. A direct user assignment takes precedence and should be
  reflected on the task board before edits.
- One writer per file at a time, including documentation and tests. In a shared
  checkout, do not switch branches, stage another agent's work, overwrite edits,
  or run commands that interfere with another agent's process or database.
- A task board is not a lock and may be stale in another branch/worktree.
  Confirm current ownership with the Lead before writing overlapping files.
- Never run live fetching, destructive cleanup, migrations, or external writes
  merely to investigate a problem; those actions need explicit task scope and
  must satisfy the project's safety and authorization rules.
- Keep credentials, local configuration, private data, and personal filesystem
  paths out of committed task records. Follow the existing citation and secret
  protection rules in `AGENTS.md`.
- When a task is finished, hand it off and stop. Do not automatically claim the
  next task or expand into another role.

## Assignment and handoff protocol

At startup, read the [shared memory skill](agents/SKILL.md), then search and
read relevant log entries. Each agent owns only their own log; everyone may
improve the common skill with coordinated edits. These routine memory updates
are allowed within every role without a separate assignment.

The Lead records each task's ID, owner/role, objective, allowed files, exclusions,
dependencies, acceptance criteria, validation, and status. Record a branch/base
revision when needed to distinguish concurrent work; avoid machine-local paths.

Normal flow: Lead design/assignment → Backend implementation → QA verification
→ Reviewer findings → owner fixes and re-verification → Lead integration.
QA may author tests earlier when contracts and file ownership are settled.

At handoff, provide the task ID, changed files, behavior delivered, commands and
results, unresolved risks/blockers, and the next owner. A report of tests not run
must say why; never imply verification that did not happen. Write a concise
entry in your own log and send its reference to the Lead rather than
concurrently editing the central task board.

Existing sessions should reread these instructions at their next task boundary;
writing these files does not itself update another running agent's context.
