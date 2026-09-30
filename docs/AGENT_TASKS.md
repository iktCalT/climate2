# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md),
[architecture](ARCHITECTURE.md) and [shared memory](agents/SKILL.md).
One specialist at a time: Developer → QA → Reviewer → Lead integration.
Only work on the assigned files; write your own log and hand back when done.
Use the [economical model and batched checks policy](PROJECT_DIRECTION.md#sequential-managed-team).

## Current assignment

**MAP-005 — scale synchronization during source loading (complete).** Base
`89f4e15` (PR #64), branch `codex/map-scale-loading-sync`; contract atop
NEXT_REQUIREMENTS. Lead owns requirements/board/log. Developer owns
`templates/maps.html`, README, References and backend log (frontend exception).
QA owns `tests/test_map_template.mjs` and QA log; Reviewer read-only/own log.
Lead also records the user's environmental-awareness purpose in PROJECT_DIRECTION;
coarse, honestly labelled data is sufficient, not a mandate for finer acquisition.
Sequential Sol/medium fallback after Luna's usage failure. Reproduce, fix,
one offline regression batch, then review; no live data, dependencies, source
acquisition, new controls, automatic scales or unrelated refactoring.
QA passed 162 Python tests (8 expected skips) and seven Node tests. Review
cleared; saved verdict recovered after a model quota interruption. User screenshot
confirms MAP-004 appearance; live interaction for MAP-005 remains unverified.

**MAP-004 — smooth NOAA estimated maps (complete).** Base `5a557e0`, branch
`codex/smooth-noaa-display`; contract atop NEXT_REQUIREMENTS.
Lead owns design/docs coordination. Developer owns `climate/services/map_data.py`,
new `static/map_interpolation.js`, `static/map_selection.js`, Maps/References
templates, README and backend log (frontend exception). QA owns tests/QA log;
Reviewer read-only/own log. Sequential specialists; batch tests after implementation.
Luna reached its usage limit mid-implementation; Sol/medium resumes the saved
patch and remaining verification without expanding scope.
Implementation/syntax checks complete. QA passed 160 Python tests (8 expected
database skips) and six Node tests. Lead inspected the synthetic smooth raster
and transparent gap. Review's nonfinite legacy-JSON finding was fixed with
NOAA-only sanitization and an overflow guard; 48 affected checks passed,
including new strict-JSON regressions. Review cleared. Live browser remains
disconnected; no live data/account operations or deployment verification.
No live DB/provider/account operations, acquisition changes, dependencies or
automatic scale changes. Check synthetic raster, offline regressions and browser
if connected. Report API design deviations before implementing.

**COORD-004 — compact shared context (Lead, complete).**
Base main `002223e`; branch `codex/compact-agent-context`.

- Scope: this board, PROJECT_DIRECTION, context index/topic notes and Lead log.
- Deliver: short active board; indexed completed-round summaries; current
  workspace/provider facts; preserve caveats and recovery references.
- Exclude: other agents' logs, runtime code, REFACTOR, live data and local caches.
- Check: local links, recorded Git revisions, unchanged out-of-scope files,
  whitespace and secret scan. No application test run for documentation only.
- No implementation assignment for Developer/QA/Reviewer this round.

Checks passed: 25 local links, eight merge revisions, unchanged out-of-scope
files and whitespace. Board/Lead log reduced from 2,701 to about 600 words;
older full records remain in Git. No application or cache changes.

## Latest application integration

MAP-004 merged in PR #64, main `89f4e15`: smooth NOAA estimates, transparent
holes and matched linked readouts. QA: 160 Python tests (8 skips), six Node
tests; after the finite-JSON fix, 48 targeted checks passed. Review cleared;
synthetic raster inspected, live browser unavailable. No deployment/live data work.

## Prior work and open limitations

Use [completed rounds](agents/context/completed-rounds.md) for task IDs,
merge revisions and verification. Full old assignments are recoverable with
`git show 002223e:docs/AGENT_TASKS.md`; they are not active instructions.

NOAA is the startup public provider; deployment/restart has not been verified.
Browser verification remains unavailable. See [data/map context](agents/context/data-and-maps.md)
for dated coverage evidence and unresolved CMIP6 caveats, and
[workspace](agents/context/workspace.md) before starting a new branch.
