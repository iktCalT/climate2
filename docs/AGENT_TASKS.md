# Agent task board

The Lead owns this board. Read [roles](AGENT_ROLES.md),
[architecture](ARCHITECTURE.md), and [shared memory](agents/SKILL.md).
The Lead dispatches managed specialists sequentially. Only one specialist works
at a time; do not spawn more agents. Report in your own log and stop. Failed
checks return to Backend, then QA and Reviewer recheck the affected change.

## Current assignments

### MAP-003 — map-to-history navigation and coordinate form (active)

Base main `dfcab70`; branch `codex/map-history-navigation`. Contract atop
NEXT_REQUIREMENTS. Lead owns planning/coordination and integration. Developer
frontend exception: `static/map_selection.js`, `templates/locations.html`,
Maps/References templates and README, own backend log. Batch popup links and
coordinate form improvements; no backend/provider/data/dependency changes.
QA owns focused tests/QA log and one final offline Python/Node run; Reviewer
read-only/own log. Sequential Luna/medium. No live data or account access.
Acceptance: selected-coordinate safe same-site links with no automatic requests,
truthful sampling caveat, accessible responsive form, unchanged comparison state.
Developer and QA complete (156 Python tests, 8 PostgreSQL skips; three Node
suites passed). Lead assigned a copy-only exception in README/Locations to
describe removal of the decimal-step restriction, not unlimited numeric precision.
Reviewer found no actionable issues after the copy clarification. Lead integrating.
Browser unavailable (no connected browser); no live data or deployment performed.

### MAP-002 — numeric comparison differences (completed, PR #61)

Base main `ee0e568`; branch `codex/map-value-differences`. Top NEXT_REQUIREMENTS
defines acceptance. Lead owns requirements/policy/board and integration.
Developer has frontend/documentation exception: `static/map_selection.js`,
Maps/References templates, README, own backend log only. Batch numeric differences
and provenance-wording edits before QA. QA owns relevant tests and QA log;
Reviewer read-only/own log. Sequential Luna/medium, no extra agents. No backend,
provider, live DB, fetching, dependency or scale changes. Run one final offline
Python/Node pass before merge; targeted reruns only for any corrections.
Developer and QA complete. Two focused defects (negative zero and removed-panel
selection) fixed before the batch run. Three Node suites passed; the 155-test
Python run found three stale copy assertions, corrected with 40 affected tests
passing. Full suite not repeated after test-only corrections. Review found one
README wording issue, corrected and rechecked; merged as `dfcab70`. Browser
unavailable; no live data operations.

### PROVIDER-003 — activate saved NOAA public reads (completed, PR #60)

Base main `7211024`; branch `codex/activate-noaa-cache`. Contract: top of
NEXT_REQUIREMENTS. Lead owns planning/status docs and integration. Developer
owns `climate/data/db.py`, `templates/admin_data.html`, README and current-status
sections of provider evaluation/PostgreSQL docs, plus backend log (documentation
and template exception assigned). Report any other required production edits.
QA owns tests/QA log; Reviewer read-only/reviewer log. One specialist at a time,
Luna/medium by user preference; escalate only for demonstrated need. Tests use
fake data, no live imports/cleanup/account access. Acceptance: NOAA startup
selection propagated consistently, immutable CMIP6 acquisition, cache-only
reads, truthful current copy, offline regressions and browser check if available.
Developer, QA and Reviewer complete; no remaining findings. Offline suite:
155 Python tests (8 PostgreSQL skips), three Node suites passed. Browser
unavailable (no connected browser). Merged as `ee0e568`; no deployment or live data
operations performed.

### PROVIDER-002 — NOAA location/presentation readiness (completed, PR #59)

Base main `5a2df92`; branch `codex/noaa-location-readiness`. Lead owns docs.
Developer owns new `climate/data/location_sampling.py`, `climate/web/app.py`,
`climate/web/helpers.py` if needed, templates index/maps/locations/references and
own backend log. Frontend exception assigned. Keep source writers unchanged;
sample NOAA at web boundary, use existing cache-only helper. QA owns tests/log;
Reviewer read-only/log, sequential. Acceptance is top NEXT_REQUIREMENTS contract.
No activation, live data or new packages. Developer/QA/Reviewer complete;
rounding-description finding resolved (algorithm unchanged). Merged as `7211024`.
QA: 152 Python tests (8 database skips), all three Node suites passed.
Browser check unavailable: built-in browser disconnected this turn.

### PROVIDER-001 — immutable source identity (completed, PR #58)

Base main `380197d`; branch `codex/provider-write-isolation`. Lead owns docs.
Developer owns `climate/data/db.py`, `climate/providers/open_meteo.py`,
`climate/cli/{prefetch_climate,migrate_weather_sqlite,compare_climate_providers}.py`
and own log. QA owns tests/own log; Reviewer read-only + own log. Sequential.
Scope extension: Developer also owns `climate/services/map_data.py` solely to
disable its opt-in Open-Meteo fallback under non-CMIP6 public selection.
Acceptance: source writers/checkpoints isolated from public selector, comparison
uses distinct providers, public cache reads unchanged; fake DB regression tests.
No live data, activation, dependencies or unrelated refactor. Developer and QA
complete (142 Python tests, 8 database skips); Reviewer found no defects.
Merged as `5a2df92`. NOAA activation remains separate.

### PAGES-001 — Home and References clarity (completed, PR #57)

Base main `a86172a`; branch `codex/page-clarity`. Requirement is recorded atop
NEXT_REQUIREMENTS.md. Lead owns README/requirements/coordination and integration.
Developer assigned frontend exception: `templates/index.html`,
`templates/references.html`, scoped `static/styles.css`, own backend log.
QA owns tests/own log; Reviewer read-only + own log. Sequential workflow.
Acceptance: accurate current provider/coverage/units, linked comparison guidance,
no new resources or fetching, preserved citations, responsive accessible layout,
offline route regressions and browser check. All three specialists complete;
Reviewer found no defects. Merged as `380197d`.
QA: 135 Python tests (8 database skips); browser verified desktop Home, narrow
References and historical disclosure using a standalone no-database preview.

### MAP-001 — linked comparison readouts (completed, PR #56)

Base: main `04d0ac1`, branch `codex/linked-map-readouts`.
Contract: [linked readouts](NEXT_REQUIREMENTS.md#linked-comparison-map-location-readouts).
Lead owns design, README/references, coordination docs and integration.
Developer (Agent 2) has an assigned frontend exception: own `templates/maps.html`,
new `static/map_selection.js` and backend log only; no backend/data changes.
QA owns tests and QA log: fake-data Node controller/template checks and offline
Python regressions. Reviewer owns read-only review and reviewer log after QA.
Developer, QA and Reviewer complete; no remaining findings. Lead integrates.
No parallel specialists or extra agents.
QA: 133 Python tests (8 skips), three Node map suites passed. Lead verified
linked values/coordinates and shared close in the built-in browser with synthetic
data; no real database access.

Acceptance: shared coordinates but distinct monthly values/provenance,
loading/missing/error states, stale-response immunity, repeated clicks/close,
one/four panels, zero/negative values and precipitation units, unchanged scale,
no click-driven requests, safe text content, no popup accumulation.

### Previous round (complete, not active assignments)

LAYOUT-001/SECURITY-001 merged in PR #55, main `04d0ac1`.

- **Lead — SECURITY-001:** implementation round complete; integrating reviewed changes.
- **Backend — BACKEND-002:** complete including delimiter correction;
  setup connection closure. Own `climate/` and `backend-log.md` only.
- **QA — QA-002:** complete including delimiter regression; 133 Python tests (8 skips), Node passed.
- **Reviewer — REVIEW-002/003:** complete; backup findings resolved, no remaining
  findings within the bounded requirement. See reviewer log for limitations.

Acceptance for SECURITY-001: meet the recorded private-account requirement in
`NEXT_REQUIREMENTS.md`; no live data operations; verify temporary-data denial
and normal assets, legacy/configured path compatibility, connection lifetime,
and existing offline regressions. Lead owns `README.md`, `.env.example`, agent
coordination docs, operating guides, and required References citations. Default models: Backend Sol/medium,
QA Luna/medium, Reviewer Sol/high. The three `*-001` reviews below are complete;
use their existing findings rather than repeat the restructure review.

Backend Sol hit a usage limit before editing; Backend Luna/medium completed
the scoped implementation. QA should cover configured-file aliases by inode
as well as pathname, sidecars, symlink escapes/loops, normal assets, resolver
precedence, and connection closure on success/error using temporary fake data.

## LAYOUT-001 — Lead / Architect

Status: complete. User-authorized exception permits the Lead to move code
and update paths/tests before the other agents are forked. Baseline is local
main `cbeda44`, with existing artwork and coordination work preserved.

Scope: `climate/`, root `app.py`/`run.sh`, `sql/`, import/path updates in tests,
project documentation, and the Lead log. Acceptance: logical package layout,
preserved application behavior, documented command migration, passing offline
checks, and non-overlapping fork assignments. No provider activation, live
imports, database cleanup/migration, or framework changes.

Verification: 123 Python tests (8 database skips), Node scale test, CLI/resource
checks, unchanged core behavior/SQL checks, and local HTTP 200 smoke checks.
Visual browser verification was unavailable (no connected browser). Fork from
the checkpoint on `codex/project-structure`; Lead owns integration after review.

## BACKEND-001 — Agent 2

Inspect the new module boundaries, Flask entry point, CLI entry points, and
resource resolution. Fix only confirmed restructuring regressions in `climate/`,
`app.py`, or `run.sh`. No planned feature work. Run relevant checks; send test
requests to QA and documentation corrections to Lead. Write `backend-log.md`.
Acceptance: report reviewed paths, defects/fixes, commands/results, and remaining
issues. Coordinate any edit to a file another agent is inspecting.

Fork prompt: “You are Agent 2, Backend Developer. Read AGENTS.md and perform
BACKEND-001 in docs/AGENT_TASKS.md. Do not inherit the Lead role.”

## QA-001 — Agent 3

Run the documented offline Python and Node suites; check CLI help, SQL resource
resolution, templates/static serving, and preserved public/admin behavior.
Add focused missing tests only in `tests/`; report production defects to Backend.
Use temporary data and mocks; existing PostgreSQL tests must remain skipped
unless an isolated test database is explicitly set up for the task. Do not
introduce pytest or change dependency management. Write `qa-log.md`.
Acceptance: reproducible results and useful coverage, with skip reasons stated.

Fork prompt: “You are Agent 3, Test / QA. Read AGENTS.md and perform QA-001 in
docs/AGENT_TASKS.md. Own tests, not production code.”

## REVIEW-001 — Agent 4

Review the completed restructure relative to baseline `cbeda44`. Existing
artwork changes were preserved alongside module moves; account for both.
Inspect imports, paths, provider identity, authentication/CSRF, SQL boundaries,
secret handling, tests, and documentation. Read-only code review; write only
`reviewer-log.md` (shared-skill improvements remain permitted). Report findings
with severity, file/line, evidence, and requested owner; do not implement fixes.
Acceptance: actionable findings or an explicit no-findings report with limits.

Fork prompt: “You are Agent 4, Reviewer / Debugger. Read AGENTS.md and perform
REVIEW-001 in docs/AGENT_TASKS.md. Review first; do not patch code.”

## Completed coordination

COORD-001/002: [roles and memory setup](agents/context/coordination-history.md).
COORD-003: [indexed context and local cache cleanup](agents/context/maintenance.md).
The Lead handles integration after the three handoffs; agents do not merge or
start another task independently.
