# Cleanup and recovery

Completed 2026-09-27 under COORD-003, in the current climate2 checkout only.

- Removed `.mypy_cache/`, root `__pycache__/`, and `tests/__pycache__/`:
  1,838 generated cache files in total. Also removed `.DS_Store` and the empty
  `.matplotlib/` directory. Prior allocated size was approximately 75 MiB.
- Checked ignored/untracked status, exact targets, absence of symlinks, and
  process/open-file information first. No host Python/type-checking task was
  listed; open handles belonged to the virtualization service.
- Deleted files have no backup, but Python bytecode and type-checker caches
  regenerate when their tools run. Finder metadata and plotting cache folders
  can also regenerate. The next type check may be slower.
- Retained `.venv`, `.cache.sqlite`, Flask sessions, local databases, generated
  application assets, unrelated working changes, and other worktrees. An
  application cache can affect requests and is not interchangeable with a
  development-tool cache. Global agent/chat caches were not touched.
- Internal conversation context cannot be cleared by deleting repo files.
  Use the [lookup](../CONTEXT_INDEX.md) to load only relevant durable notes;
  those notes are project memory, not disposable cache payloads.

For another cleanup, recheck targets and active use; this dated inventory is
not authorization to repeat deletion blindly. See [shared skill](../SKILL.md).
