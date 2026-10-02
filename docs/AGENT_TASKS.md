# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md),
[architecture](ARCHITECTURE.md) and [shared memory](agents/SKILL.md).
One specialist at a time: Developer → QA → Reviewer → Lead integration.
Only work on assigned files; write your own log and hand back when done.
Use the [economical model and batched checks policy](PROJECT_DIRECTION.md#sequential-managed-team).

## Current assignment

**README-DEMO-001 — user-supplied comparison screenshot (complete).**
Base `50af280` (PR #74), branch `codex/readme-demo-image`. Lead documentation
scope: README, new `docs/images/noaa-comparison-2026-1950.png`, website
References attribution, PROJECT_DIRECTION, this board and own log. No specialist
implementation task. Validate PNG/provenance/privacy, relative image link,
caption/alt text, References rendering, whitespace and publication secret scan.
No application behavior, dependencies, data or other assets changed.

Verified original PNG bytes, visual content, valid chunks/CRC and absence of
text/EXIF metadata; relative link and caption checked. All 11 content tests and
whitespace checks passed. Publication status is recorded in GitHub.

REGRESSION-001 is deferred for this explicit user request. Its three uncommitted
documentation files are preserved in the named stash
`climate2 REGRESSION-001 checkpoint before README demo request` on
`codex/offline-regression-checkpoint`. Full batch: 173 Python passes, eight skips,
one stale precipitation-copy assertion; Node 13 passed. Assertion correction is
not implemented: QA hit a usage limit. Recover selectively; do not blindly apply
its older task board over newer assignments. Keep the separate pre-layout stash.

## Previous application assignments

**HISTORY-002 — editable location coordinates (complete).** Base `a6491c1`
(PR #73), branch `codex/edit-location-coordinates`; contract atop requirements.
Lead owns board/requirements/log. Developer owns `templates/locations.html`,
README, References and backend log (bounded template exception). QA owns
`tests/test_locations_route.py`, `tests/test_content_pages.py` and own log.
Reviewer read-only/own log. Sequential Sol 6.1/medium fallback after previous
Luna quota and Sol stall. Native prefilled form, requested coordinate precision,
zero/negative values, empty coverage and existing cache-only validation preserved.
Focused mocked route/content tests; reuse unchanged chart/Node results. No
backend, DB, provider, dependency or unrelated edits.

QA passed 57 focused route/content tests; review cleared. Browser unavailable.
No live data or deployment operations. Publication status is recorded in GitHub;
no further specialist task assigned.

**HISTORY-001 — seasonal coverage readouts (complete).** Base `eab3e85`
(PR #72), branch `codex/seasonal-coverage-readouts`; contract atop requirements.
Lead owns board/requirements/log. Developer owns `climate/web/helpers.py`,
`climate/web/app.py` (chart version only), `templates/locations.html`, README,
References and backend log. QA owns `tests/test_chart_rendering.py`,
`tests/test_locations_route.py`, `tests/test_content_pages.py` and own log.
Reviewer read-only/own log. Sequential Luna/medium; Sol 6.1/medium finishes QA
and review after Luna's usage limit and an interrupted stalled Sol worker,
preserving saved test edits. Focused chart/route/content
tests, no Node rerun for Python/chart-only work. No DB/provider operations,
dependencies, map edits or unrelated refactors. Preserve mean calculations,
show monthly coverage and honest season/unit guidance; invalidate old chart
renders by version only. See requirements for acceptance matrix.

QA passed 59 focused chart/route/content tests; independent review cleared.
Sparse-year gap handling was corrected before QA. Browser unavailable; no live
data or generated-cache cleanup. Publication status is recorded in GitHub.

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

**HISTORY-001 merged in PR #73, main `a6491c1`.** Seasonal chart coverage
readouts; 59 focused chart/route/content tests passed, review cleared.
MAP-010's 13 Node tests also passed. Earlier full MAP-005 run: 162 Python tests (eight expected skips),
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
