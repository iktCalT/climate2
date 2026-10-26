# Workspace and verification context

Snapshot 2026-10-26, integration base/main `a51e9b3` (PR #100).
Recheck Git and runtime state before acting; this note does not prove a server
is still running. [Architecture](../../ARCHITECTURE.md) gives current commands.

## Browser access preference (owner reminder, 2026-10-19)

The owner permits opening ChatGPT desktop for its browser when browser work
is needed, including while the agent runs in Codex CLI. Check the available
browser connection and supported controls; CLI execution alone does not mean
browser access is unavailable. Respect tool access restrictions and report
specific connection/dialog limitations rather than assuming access works.

## Current verification snapshot

- Local development only: owner paused cloud/domain/VM work on 2026-10-08.
  Preserve portable production configuration; no cloud operations or credentials
  needed. Actual Docker build and hosted operation remain unverified.
- LOCATION-FETCH-001/002/003 merged in PRs #84–86. Bounded NOAA gap fetching
  exists; only its additive tracking schema was activated locally. One explicit
  live September 2026 sample for requested (10, 10), sampled (10, 8), passed
  download/readback/chart HTTP checks (coverage 272→273/909). This feature has no
  verified full-history or automatic live multi-month run. Maps remain cache-only.
- Chart v9 layout passed all four metrics at desktop/390/320px in PR #92.
  Simulated location-fetch progress/refresh/throttle/Retry passed previously;
  one unattributed browser MutationObserver error remains unisolated.
- Community drafts, consented publication, own listing/deletion and full Maps
  integration passed with synthetic climate data/temporary SQLite (PRs #93–97).
  PR #100 fixes comment clipping; 320/390/1280px wrapping, scrolling and keyboard
  close checks passed. Native Forget Cancel/Confirm and actual elapsed 30-day
  expiry remain unverified in browser. Community stays disabled until configured;
  no real administrator was provisioned.
- Latest full checkpoint (PR #98): Python 234, 226 passed/eight expected PG skips;
  Node 45 passed. PR #99 introduced the reusable offline runner: 238 total,
  228 passed/eight skips/two fixture failures; scoped fixes passed Locations 50/50
  and runner lifecycle 4/4. PR #100 passed 27 Node + 14 content checks. These are
  historical results, not reruns; see [completed rounds](completed-rounds.md).

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
