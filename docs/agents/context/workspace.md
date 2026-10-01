# Workspace and verification context

Snapshot 2026-10-01, main `ef5de20` (PR #70). Recheck Git before acting.

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
- Latest application check: MAP-009, 48 focused Flask/content and eight Node
  tests passed. Last full batch: MAP-005, 162 Python tests (eight expected
  isolated-database skips) and seven Node tests. These are recorded past runs.
  No connected built-in browser in the last check; no application restart or
  deployment was verified. No live data operations accompanied these rounds.
- Temporary scripts can disappear between sessions. Recreate only necessary
  safe helpers; never treat a missing temporary tool as a reason to skip secret
  checks. Preserve databases, environments, session files and recovery data.

Source: local Git worktree/status/stash inspection; [completed rounds](completed-rounds.md).
Full older notes: `git show ef5de20:docs/agents/context/workspace.md`.
