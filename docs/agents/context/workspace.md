# Workspace and verification context

Snapshot 2026-09-30, main `002223e` (PR #62). Recheck Git before acting.

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
- Latest application check: MAP-003, 156 Python tests (8 isolated-database-only
  checks skipped), three Node suites passed. No connected built-in browser in
  the last check; no application restart/deployment was verified.
- Temporary scripts can disappear between sessions. Recreate only necessary
  safe helpers; never treat a missing temporary tool as a reason to skip secret
  checks. Preserve databases, environments, session files and recovery data.

Source: local Git worktree/status/stash inspection; [completed rounds](completed-rounds.md).
Full older notes: `git show 002223e:docs/agents/context/workspace.md`.
