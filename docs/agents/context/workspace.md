# Workspace and verification context

Observed 2026-09-27 using local Git; recheck before relying on this snapshot.

- Active branch: `codex/project-structure`, based on local main `cbeda44`.
  The older `codex/original-error-artwork` checkout was brought forward using
  a local stash named `climate2 pre-layout working changes`. The stash is kept
  as a recovery copy; do not apply it over the reorganized tree blindly.
- Existing artwork/template/style/test changes, `run.sh`, and coordination
  notes were preserved. The new code paths are in
  [architecture](../../ARCHITECTURE.md). Check `git status` and the latest commit
  before editing. No remote freshness check was performed in this restructure.
- Fork agents from the restructure branch/checkpoint, not older main. Separate
  worktrees do not share uncommitted files; confirm the branch and task ownership
  before starting. The task board is not a lock.
- This checkout uses `.venv` and `requirements.txt`. Existing tests use
  `unittest`; role skill names do not authorize a pytest/SQLAlchemy migration.
  The skill validator previously could not import PyYAML in this venv; basic
  Markdown links, metadata, and structure were checked without installing it.

Sources: `git status --short`, `git worktree list`, `git rev-parse main`,
[task board](../../AGENT_TASKS.md), and [Lead log](../lead-log.md).
