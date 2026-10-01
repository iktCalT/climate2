# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md),
[architecture](ARCHITECTURE.md) and [shared memory](agents/SKILL.md).
One specialist at a time: Developer → QA → Reviewer → Lead integration.
Only work on assigned files; write your own log and hand back when done.
Use the [economical model and batched checks policy](PROJECT_DIRECTION.md#sequential-managed-team).

## Current assignment

**MAP-010 — keyboard coordinate selection (complete).** Base `69b6a04`
(PR #71), branch `codex/map-coordinate-selection`; contract atop requirements.
Lead owns requirements/board/log. Developer owns `templates/maps.html`, optional
new `static/map_coordinates.js`, README, References and backend log (bounded
frontend exception). QA owns coordinate/template Node tests,
`tests/test_locations_route.py`, `tests/test_content_pages.py` and QA log.
Reviewer read-only except own log. Sequential Luna/medium. Acceptance: validated
typed coordinates center live initialized panels and reuse linked readouts;
manual scales and existing lifecycle remain intact. No providers, DB, new
dependencies or unrelated edits. Focused offline Node/Flask batch, then review.

QA passed 50 focused Flask/content and 13 Node map tests; review cleared.
Lead's readiness-message correction and same-center test gap were resolved.
Browser unavailable; no live data or deployment operations. Publication status
is recorded in GitHub; no further specialist task is assigned.

## Latest coordination round

**COORD-005 — refresh concise handoffs (Lead, documentation complete).** Base `ef5de20`
(PR #70), branch `codex/refresh-agent-handoffs`.

- Scope: this board, PROJECT_DIRECTION, completed-rounds/workspace context
  notes and Lead log only. No specialist implementation assignment this round.
- Deliver: archive completed scopes as concise indexed outcomes, reconcile
  publication status and refresh dated verification evidence.
- Preserve: unresolved limitations, recovery stash and revision-based history.
  Other agents' logs, application code, REFACTOR, caches and data are excluded.
- Validate: local links, recorded commit ancestry, allowed-file diff, whitespace
  and secrets. Application tests are not rerun for documentation-only changes.

Checks passed: five allowed files, 16 local links, 16 ancestor revisions and
whitespace. Board reduced from 1,066 to about 300 words. Full earlier scopes
remain recoverable in Git; no physical files or caches removed.

## Latest application integration

**MAP-009 merged in PR #70, main `ef5de20`.** Failed panels offer manual
saved-data retry; 48 focused Flask/content and eight Node tests passed, review
cleared. Earlier full MAP-005 run: 162 Python tests (eight expected skips),
seven Node tests. These are prior results, not new runs in this round.

## Prior work and open limitations

Use [completed rounds](agents/context/completed-rounds.md) for task IDs,
merge revisions and verification. Completed MAP-004–009, PAGES-002 and COORD-004
assignments are not active work. Full old scopes and Lead evidence remain in
`git show ef5de20:docs/AGENT_TASKS.md` and
`git show ef5de20:docs/agents/lead-log.md`.

NOAA is the startup public provider; deployment/restart has not been verified.
Automated browser verification remains unavailable in the latest handoff.
See [data/map context](agents/context/data-and-maps.md) for dated coverage and
unresolved CMIP6 caveats, and [workspace](agents/context/workspace.md) before
starting a new branch. COORD-005 merged in PR #71 (`69b6a04`).
