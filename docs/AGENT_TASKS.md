# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md),
[architecture](ARCHITECTURE.md) and [shared memory](agents/SKILL.md).
One specialist at a time: Developer → QA → Reviewer → Lead integration.
Only work on the assigned files; write your own log and hand back when done.
Use the [economical model and batched checks policy](PROJECT_DIRECTION.md#sequential-managed-team).

## Current assignment

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

MAP-003 merged in PR #62, main `002223e`: map-to-history links and responsive,
labelled coordinate form. QA: 156 Python tests (8 PostgreSQL skips), three Node
suites passed. Review cleared; browser unavailable. No deployment/live data work.

## Prior work and open limitations

Use [completed rounds](agents/context/completed-rounds.md) for task IDs,
merge revisions and verification. Full old assignments are recoverable with
`git show 002223e:docs/AGENT_TASKS.md`; they are not active instructions.

NOAA is the startup public provider; deployment/restart has not been verified.
Browser verification remains unavailable. See [data/map context](agents/context/data-and-maps.md)
for dated coverage evidence and unresolved CMIP6 caveats, and
[workspace](agents/context/workspace.md) before starting a new branch.
