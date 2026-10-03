# Workspace and verification context

Snapshot 2026-10-03, task base/main `083ead5` (PR #78). Recheck Git before acting.

- `codex/deployment-regression-checkpoint`: REGRESSION-002 combined offline
  verification after UI/community and administrator setup. See current board
  for fresh evidence. Browser inventory was empty/native connection failed and
  the listed browser skill file was absent; no visual verification claimed.
  Hosting target remains an owner choice; no deployment configuration changed.

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
- The named stash `climate2 REGRESSION-001 checkpoint before README demo request`
  preserves the original documentation checkpoint. Commands/evidence have been
  selectively reconciled; retain for recovery, not blind reapplication.
- Temporary scripts can disappear between sessions. Recreate only necessary
  safe helpers; never treat a missing temporary tool as a reason to skip secret
  checks. Preserve databases, environments, session files and recovery data.

Source: local Git worktree/status/stash inspection; [completed rounds](completed-rounds.md).
Full older notes: `git show 5b17b0d:docs/agents/context/workspace.md`.
