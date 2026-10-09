# Workspace and verification context

Snapshot 2026-10-08, integration base/main `64e5cbf` (PR #82). Recheck Git before acting.

- Owner paused domain/VM/cloud deployment on 2026-10-08. Continue local
  programming with future portability; no cloud operations or credentials needed.
  DEPLOY-005 preflight notes are retained as paused context.
  COMMUNITY-002 merged in PR #82: explicit confirmation before forgetting local
  pin credentials, eight focused Node tests pass. COMMUNITY-003 adds an
  unpublished pin preview: 15 focused community Node tests pass, scoped review
  clear. Ready for Lead integration; real-browser appearance unverified.

- DEPLOY-003 / DEPLOY-004 / UI-002: hosting comparison, portable production
  foundation and numeric wheel guard merged in PR #80 (`29c3fd7`).
  See the current board and [runbook](../../DEPLOYMENT.md). No hosting selected,
  resource provisioning, live stores or spending. Optional container not built;
  browser connection unavailable. Cloud Run requires a separate storage redesign.

- `codex/private-admin-bootstrap` merged in PR #78: DEPLOY-002 adds an operator-only terminal
  command for a fresh deployment's administrator. No real account creation;
  tests use temporary stores. See current board for review/publication status.

- `codex/concise-public-pages` implements UI-001, DEPLOY-001, COMMUNITY-001:
  concise pages, closed hosted registration, world camera, consent-only local
  profiles and public pins. Community feature is disabled by default; see
  [deployment configuration](../../COMMUNITY.md) and current board for review
  status. No live database or deployment operations.

- Main is checked out in another climate2 worktree; do not switch this checkout
  to main or touch unrelated repositories. Verify the same climate2 origin and
  a clean worktree before fast-forwarding main. Create task branches from the
  updated main ref; do not reuse the old restructure checkpoint.
- The pre-layout recovery stash `climate2 pre-layout working changes` still
  exists. Keep it; do not apply it over the reorganized tree blindly.
- Use repository-local Meow-5 identity, existing `.venv`, `requirements.txt`,
  unittest and dependency-free Node tests. No framework/tool migration implied
  by role skill names. Canonical paths/commands are in
  [architecture](../../ARCHITECTURE.md).
- REGRESSION-002 combined batch at `083ead5` on 2026-10-02: Python 204 total,
  196 passed, eight expected PostgreSQL skips, no failures; Node 18 passed.
  No production/test correction needed. Inherited filesystem sessions remain
  an isolation limitation; browser, live data and deployment are unverified.
  Earlier counts are historical in the completed-rounds index and QA log.
- DEPLOY-004 initial batch: Python 211 total, 202 passed/eight PG skips/one
  static hardlink failure; Node 20 passed. After that fix and review corrections
  (exact image-file allowlist, strict CLI environment), all 58 focused tests
  pass. Full suite not repeated; see QA log for exact scope and limitations.
- The named stash `climate2 REGRESSION-001 checkpoint before README demo request`
  preserves the original documentation checkpoint. Commands/evidence have been
  selectively reconciled; retain for recovery, not blind reapplication.
- Temporary scripts can disappear between sessions. Recreate only necessary
  safe helpers; never treat a missing temporary tool as a reason to skip secret
  checks. Preserve databases, environments, session files and recovery data.

Source: local Git worktree/status/stash inspection; [completed rounds](completed-rounds.md).
Full older notes: `git show 5b17b0d:docs/agents/context/workspace.md`.
