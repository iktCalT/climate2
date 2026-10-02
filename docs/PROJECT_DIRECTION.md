# Project direction and publication rules

This document records requirements added after the original refactor plan. It
supplements, but does not replace or edit, `docs/REFACTOR.md`.

## Purpose: environmental awareness

Confirmed by the user on 2026-09-30: climate2 aims to raise awareness of
environmental protection, not provide detailed, high-precision climate reporting.
Prioritize accessible explanations, clear visual comparisons and responsive
exploration. Coarse monthly data and explicitly labelled interpolation are
acceptable; finer resolution and exhaustive fetching are not goals in themselves.

Keep the presentation honest: cite sources, distinguish estimates from direct
observations, preserve missing-data gaps, and use shared manual comparison
scales. Do not present a pair of individual months as proof of a long-term
climate trend. This direction does not weaken data-integrity or security checks.

## Four-agent responsibilities and coordination

Status: implemented (shared instructions and task board; no agents launched).

Problem: multiple agents can duplicate work, edit overlapping files, or expand
their tasks beyond the user's request without explicit ownership.

Desired behavior: keep a shared four-role roster and handoff rules in
`docs/AGENT_ROLES.md`, referenced by root `AGENTS.md` and a repo-wide editor
rule. Keep explicit assignments and completion evidence in
`docs/AGENT_TASKS.md`, maintained by the Lead / Architect.

Constraints: work only in climate2; preserve unrelated edits; assign one writer
per file at a time; require a bounded task before implementation; keep review
read-only unless a fix is explicitly assigned. Skill names describe capabilities,
not permission to change frameworks, install tools, or expand scope. These
instructions do not create agents or authorize unrelated implementation work.

## Shared agent memory

Status: implemented in `docs/agents/`; linked from agent startup instructions.

Problem: agents need useful handoffs and durable decisions without reading
irrelevant history or overwriting each other's notes.

Desired behavior: `docs/agents/` contains one concise, owner-written log per
agent and a common `SKILL.md` that every agent reads and may improve. Search
task/topic/file headings first; read only relevant entries. Record important
findings before context is lost and summarize results at task completion.

Constraints: initialize empty logs once, then only their owners edit them;
coordinate shared-skill edits; retain unresolved issues and durable decisions
while pruning obsolete notes. Remove only verified disposable, inactive,
repo-local agent artifacts within scope, never another agent's active work,
private data, or global caches. No automatic cleanup job is introduced.

## Indexed context and local cache cleanup

Maintenance round COORD-005 (2026-10-01): implemented refresh after PR #70.
The board had accumulated completed assignments and stale publication handoffs.
Lead condensed it, indexed PRs #63–70, refreshed the dated workspace snapshot,
and reconciled the Lead log with verified merge revisions. Preserve test and
browser limitations and Git-based recovery. Scope is these coordination
documents only; no other agent logs, application code, caches or data. Validate
local links, commit ancestry, scope, whitespace and secrets; no application
test rerun or specialist implementation is needed for this documentation round.

Maintenance round COORD-004 (2026-09-30): shorten the active task board and
Lead-owned log, index concise completed-round records, and refresh stale workspace
and provider context. Preserve unresolved caveats and revision-based recovery.
Lead owns these documentation edits; other agents' logs, application files,
fixed REFACTOR plan, databases, environments and caches stay untouched. Validate
links, status/commit references and diff/secret checks, not application suites.

Status: implemented; cleanup and recovery recorded in
`docs/agents/context/maintenance.md`.

Problem: completed coordination details crowd startup context, while important
but inactive knowledge needs a discoverable home. Generated development caches
also occupy local space.

Desired behavior: keep `docs/agents/CONTEXT_INDEX.md` as a short lookup for
topic notes under `docs/agents/context/`. Load only relevant notes, identify
their source/revision, and condense completed task records without losing
unresolved work. This does not erase the conversation's internal context.

Cleanup scope: inspect and remove only the regenerable `.mypy_cache/`, root
and test `__pycache__/`, `.DS_Store`, and empty `.matplotlib/` in this checkout.
Preserve working changes, environments, application caches, sessions, databases,
other worktrees, and global agent state. Record what was removed and how it can
be regenerated; protect the context index and useful notes from cache cleanup.

## Agent-ready repository structure

Status: implemented on 2026-09-27; see `docs/ARCHITECTURE.md` and the task board.

The user assigned the Lead to restructure the project before forking the other
three agents. For this task, the Lead may move production modules, update their
imports and paths, and adapt tests/documentation as a scoped exception to the
normal planning-only role. Preserve uncommitted work when bringing this older
checkout onto the existing local main baseline. Record architecture and
non-overlapping follow-up tasks before handoff; do not launch the other agents.

## Sequential managed team

Status: implemented in the SECURITY-001 handoff cycle (user-approved on 2026-09-27).

The user communicates primarily with the Lead. The Lead starts or resumes one
specialist at a time: Backend → QA → Reviewer. Failed verification returns to
Backend, then QA and Reviewer repeat only affected checks. No parallel specialist
work and no additional agents spawned by specialists. Existing completed logs
are evidence to reuse, not tasks to redo.

Default models (user updated 2026-09-29): Luna/medium for scoped Backend, QA and
Reviewer tasks; Lead handles architecture. Use stronger models only when a
task demonstrates a need, keeping handoffs and context concise. Subscription changes or paid API use are
not authorized by these model preferences. Each specialist writes only their
own log; the Lead maintains assignments and integrates reviewed changes.
Continue through the full round without requesting confirmation at each handoff;
stop when the round finishes or a material decision needs the user's input.

Verification cadence (user updated 2026-09-29): batch related low-risk edits
across implementation cycles, then run the offline regression suites once before
merging. Use targeted checks for bug fixes and risky changes; after a correction,
rerun affected checks rather than automatically repeating the entire suite.
Do not duplicate QA's completed runs during review without a specific concern.

## Publication and provenance

README-DEMO-001 (2026-10-02), implemented: publish the project owner's supplied
comparison screenshot as a repository-local README demo. Preserve visible
source attribution, add descriptive alt text and a caption identifying August
2026 versus August 1950 as an illustrative saved-data comparison, not proof of
a trend. Credit screenshot provenance and NOAA/MapLibre in README and website
References. Do not imply the screenshot records current database coverage or
exact-location observations. No generated substitute, image editing, runtime
behavior changes or unrelated assets. Inspect image metadata before publication.

- The refactor is an **AI-assisted derivative** made with **OpenAI Codex
  (GPT-5)**.
- The original project, [iktCalT/climate](https://github.com/iktCalT/climate),
  was implemented by its human author as a CS50 final project with substantial
  guidance from ChatGPT.
- The user owns every remote, push, pull request, and merge. Codex may use
  remote Git or GitHub operations only for `iktCalT/climate2`, as explicitly
  authorized by the user.

## External-source attribution

Whenever the project uses or depends on an external package, API, webpage,
dataset, image, icon, font, code sample, media file, or other third-party
resource, cite it in both the repository `README.md` and the website's
References page. Add or update those citations in the same change that
introduces the external resource.

Prefer the original creator, provider, package documentation, or canonical
project page over an aggregator. Include a direct link, explain what the
resource contributes, and record its licence or required attribution when that
information is available. Do not present third-party data or assets as original
project work, and do not leave externally sourced material credited in only
one of the two required locations.

## Secret and private-data protection

Never commit or push credentials, secrets, private keys, authentication tokens,
passwords, populated databases, personal account data, or machine-specific
configuration to GitHub. This includes `.env` variants, PostgreSQL connection
strings containing passwords, CDS or other API tokens, SSH/TLS private keys,
cloud service credentials, session files, and SQLite/PostgreSQL data exports.

Keep sensitive values outside the repository and load them from ignored local
configuration or environment variables. Provide only clearly fake,
non-functional placeholders in documented example files. Before every commit
and push, inspect the staged file list and scan staged content for likely
secrets; stop and remove or rotate any exposed credential before publication.
Ignore common secret and database filename patterns as a backstop, while
recognizing that `.gitignore` does not make an already tracked or staged secret
safe.

## Progressive, data-driven maps

Historical direction, superseded where it calls for finer fetched data by the
environmental-awareness purpose above and the cache-only smooth NOAA display
in [NEXT_REQUIREMENTS](NEXT_REQUIREMENTS.md#smooth-estimated-noaa-map-display).

The fixed 91×91 global grid and pre-rendered Folium image overlays are not the
desired long-term map experience. After the location cache-miss work, replace
or substantially redesign the mapping layer so zooming in increases the
precision of displayed climate data.

### Required behavior

- At higher zoom levels, reduce the latitude/longitude step size and present
  more detailed values rather than enlarging the same coarse raster image.
- Fetch only data needed for the requested viewport, zoom level, variable, and
  date. Prefer Open-Meteo or another suitable open climate-data source over
  prefetching the world at every resolution.
- Cache fetched values in PostgreSQL. The database remains the source of truth;
  generated web assets are disposable render caches.
- Use bounded requests, deduplication, and Open-Meteo rate limits. Never make
  a request per pixel or blanket-fetch a high-resolution global grid because a
  visitor zoomed in.
- Keep map interactions responsive: loading or missing data should be shown
  explicitly instead of silently interpolating from unrelated locations.

### Technical direction to evaluate

The implementation uses **MapLibre GL JS** in the Flask frontend with a
viewport JSON endpoint served by Flask/PostgreSQL. The legacy Folium renderer
has been removed.

The implementation should define a small map-data API, such as a request for
`bounds`, `zoom`, `month`, and `climate_type`. The server should choose a safe
sampling resolution for that request, return existing PostgreSQL values, and
queue or fetch a bounded set of missing points from the open provider. The
exact provider, resolution policy, and client library will be selected during
the map-redesign phase and documented in the README when implemented.
