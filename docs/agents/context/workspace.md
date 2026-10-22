# Workspace and verification context

Snapshot 2026-10-10, integration base/main `1d548e3` (PR #88).
Recheck Git and runtime state before acting; this note does not prove a server
is still running. [Architecture](../../ARCHITECTURE.md) gives current commands.

## Browser access preference (owner reminder, 2026-10-19)

The owner permits opening ChatGPT desktop for its browser when browser work
is needed, including while the agent runs in Codex CLI. Check the available
browser connection and supported controls; CLI execution alone does not mean
browser access is unavailable. Respect tool access restrictions and report
specific connection/dialog limitations rather than assuming access works.

## Historical runtime snapshot

- Local development only: owner paused cloud/domain/VM work on 2026-10-08.
  Preserve portable production configuration; no cloud operations or credentials
  needed. Actual Docker build and hosted operation remain unverified.
- LOCATION-FETCH-001/002/003 merged in PRs #84–86. Bounded NOAA gap fetching
  exists; only its additive tracking schema was activated locally. One explicit
  live September 2026 sample for requested (10, 10), sampled (10, 8), passed
  download/readback/chart HTTP checks (coverage 272→273/909). This feature has no
  verified full-history or automatic live multi-month run. Maps remain cache-only.
- PR #87 recorded synthetic browser progress/refresh/throttle/Retry success,
  corrected narrow chart headings (cache v8), and removed Cursor duplicates.
  The updated title's real-browser confirmation remains pending. One prior
  unattributed browser MutationObserver error remains unisolated.
- PRs #82–83 added local-profile forget confirmation and unpublished pin preview;
  offline checks pass, real-browser verification remains pending. Community stays
  disabled until configured; no real administrator was provisioned.
- Latest combined checkpoint (PR #88): Python 230 total, 221 pass/eight expected
  integration skips/one stale assertion; corrected module three passes. Node 36
  pass. Full batches not repeated after correction. QA used temporary app state;
  ordinary commands are not thereby proven isolated. See QA log for evidence.

## Git and safety

- Main is checked out in another climate2 worktree. Do not switch this checkout
  to main. Verify clean status and the same climate2 origin before updating that
  worktree; begin new task branches from the current main ref.
- Use repository-local Meow-5 identity, existing .venv, requirements.txt,
  unittest and dependency-free Node suites. No framework/tool migration implied.
- Preserve both recovery stashes: `climate2 pre-layout working changes` and
  `climate2 REGRESSION-001 checkpoint before README demo request`.
- Temporary helpers may disappear. Recreate only required safe helpers; never
  skip secret checks or assume an ignored file is disposable. Preserve databases,
  environments, session data, other agents' files and recovery refs.
- Relevant history: [completed rounds](completed-rounds.md) and
  [cleanup/recovery](maintenance.md). Original detailed snapshot remains at
  `git show 1d548e3:docs/agents/context/workspace.md`.
