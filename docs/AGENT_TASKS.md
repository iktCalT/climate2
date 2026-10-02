# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md),
[architecture](ARCHITECTURE.md) and [shared memory](agents/SKILL.md).
One specialist at a time: Developer → QA → Reviewer → Lead integration.
Use the [economical model and batched checks policy](PROJECT_DIRECTION.md#sequential-managed-team).

## Current round

**UI-001 / DEPLOY-001 / COMMUNITY-001 — reviewed; Lead integration.**
Base `7342c9e` (PR #76), branch `codex/concise-public-pages`.

- Lead: requirements, README/deployment guide, coordination and integration.
- Developer's bounded frontend/backend exception: Home/Maps/Locations, registration
  closure/nav label, world camera, community service/API/browser modules and
  partials, scoped CSS, own log. No climate pipeline, References body/style,
  dependencies, clustering or live deployment changes.
- QA: content/routes/registration/world camera and isolated community Python/Node
  tests, own log. Reviewer: read-only code/security review and own log.
- Contracts: [concise UI](NEXT_REQUIREMENTS.md#concise-public-frontend) and
  [community](NEXT_REQUIREMENTS.md#low-maintenance-public-deployment-and-community-pins).
  Owner confirmed immediate publication with rate limits/admin removal.
  Optional typed coordinates remain in a named native disclosure by design.
- Feature disabled until explicit enable flag/secret/private storage. Hosted
  registration is closed; existing administrator login remains. See
  [community deployment and privacy](COMMUNITY.md), including initial admin
  provisioning, proxy rate-limit limits and moderation responsibilities.

## Verification

Full offline Python batch: **192 total, 182 passed, eight expected PostgreSQL
skips, two errors**. Fixed both: exhausted public posting quotas no longer block
administrator deletion; invalid Unicode is rejected before storage. Independent
post-fix community module: **nine passed**. Node: **18 passed** (13 map, five community).

Review follow-ups replaced recursive static-tree scanning with bounded private
path checks and removed permanent historical-Git test dependencies. Latest focused
content/community run: **22 passed**. Full batch not repeated after corrections.
Independent final review cleared the fixes; no reviewer blocker remains.
References baseline byte-equality is recorded as one-time evidence; ongoing tests
verify rendered/style isolation without freezing future unrelated changes.

No browser connection, production database, provider fetch, deployment or live
security/load verification. Inherited filesystem test sessions remain an isolation
limitation. Sequential fallback models were used after usage-limit interruptions.

## Prior work and recovery

REGRESSION-001 merged in PR #76 (`7342c9e`); corrected module 10 passed.
See [completed rounds](agents/context/completed-rounds.md) for prior scopes/results.
Old task scopes remain in `git show 7342c9e:docs/AGENT_TASKS.md`.

Retain both recovery stashes: `climate2 REGRESSION-001 checkpoint before README demo request`
and `climate2 pre-layout working changes`. Their existence is not an instruction
to reapply older files. No user caches, environments or databases were cleaned.
See [workspace](agents/context/workspace.md) before branching.
