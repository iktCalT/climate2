# Workspace and verification context

Snapshot 2026-10-02, main `5b17b0d` (PR #75). Recheck Git before acting.

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
- REGRESSION-001 full batch at `50af280`: Python 182 total, 173 passed, eight
  expected PostgreSQL skips, one stale precipitation-copy assertion; Node 13
  passed. Correction on `codex/finish-offline-regression` passed the 10 affected
  Python tests on 2026-10-02; the full suite was not rerun after correction.
  Provider/climate reads were mocked; inherited filesystem sessions remain an
  isolation limitation. No connected browser, live data or deployment check.
- The named stash `climate2 REGRESSION-001 checkpoint before README demo request`
  preserves the original documentation checkpoint. Commands/evidence have been
  selectively reconciled; retain for recovery, not blind reapplication.
- Temporary scripts can disappear between sessions. Recreate only necessary
  safe helpers; never treat a missing temporary tool as a reason to skip secret
  checks. Preserve databases, environments, session files and recovery data.

Source: local Git worktree/status/stash inspection; [completed rounds](completed-rounds.md).
Full older notes: `git show 5b17b0d:docs/agents/context/workspace.md`.
