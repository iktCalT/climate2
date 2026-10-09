# Agent task board

Lead owns this board. Read [roles](AGENT_ROLES.md), [architecture](ARCHITECTURE.md)
and [shared memory](agents/SKILL.md). Specialists run sequentially.

## Current assignment

**COMMUNITY-003 — unpublished pin preview (complete; Lead integration).**

- Contract: first requirements entry. Lead owns plan, board and own log.
- Developer explicitly owns frontend implementation in `static/community_pins.js`,
  scoped CSS in `static/styles.css`, `templates/community_maps.html`, README and
  own backend log. Existing files only; no server/dependency/cloud/data work.
- QA next owns `tests/test_community_browser.mjs` and own log: valid/invalid
  coordinates, multi-map load/remove lifecycle, pan/refresh preservation,
  placement off, success/failure and no preview network/storage side effects.
- Reviewer follows QA read-only except own log; focus marker lifecycle and
  no posting/consent regression. Run focused Node checks, not full Python suite.
- Acceptance: explicit unpublished state, typed/click coordinate parity,
  distinct non-interactive markers on live maps, no hidden writes or downloads.
- QA: 15 focused community Node tests pass, zero failures/skips, including
  delayed readiness, invalid coordinates, lifecycle and explicit publication.
  Independent scoped review clear; real-browser appearance remains unverified.
  No new resources, backend changes or live-store/cloud operations. Lead owns
  publication; no additional implementation task assigned this round.

## Previous local improvement

**COMMUNITY-002 — confirm forgetting a local profile (merged in PR #82).**

- Lead owns requirements, board and own log. Developer owns only
  `static/community_profile.js`, necessary copy in `templates/community_profile.html`,
  README and own backend log; frontend scope explicitly assigned.
- QA follows Developer: own focused Node profile tests and own log, cancel and
  accept cases including failure behavior; no production edits or live stores.
- Reviewer follows QA: scoped read-only review except own log. No full suite
  repeat for this small browser-only change; no new dependency or cloud action.
- Acceptance: cancellation has no storage/active-state side effects; confirmation
  preserves prior success/failure behavior and warns public pins remain. Native
  keyboard-accessible confirmation; provider-neutral, no server behavior change.
- QA: eight focused community Node tests pass, no failures/skips; final scoped
  review clear. No full-suite repeat, cloud action or live-store access. No
  additional task assigned; future hosting remains paused.

## Paused deployment

**DEPLOY-005 — Google Cloud + Cloudflare launch (paused by owner 2026-10-08).**

- Owner: Lead for account/project/hostname discovery, architecture and planning
  documents; no implementation specialist assigned until deployment inputs are
  known. Scope remains climate2 only; no other repositories or cloud workloads.
- Contract: Google Cloud launch entry in [requirements](NEXT_REQUIREMENTS.md). User chose
  Google Cloud temporarily and requested a later portable migration.
- Check: CLI exists and lists a saved account/project, but the first remote
  project read fails because reauthentication is required. Billing/credit not
  verified; no cloud resources, data transfers or DNS changes performed.
- Next: no action until owner resumes. Keep future deployment in mind during
  local programming; preserve production configuration and native startup.

## Previous maintenance

**MAINT-001 — merged GitHub branch cleanup (Lead, complete).**

- Owner/scope: Lead verifies climate2 remote refs and merged PRs, deletes only
  matching unprotected task tips with explicit leases, updates direction/board
  and own log. No application changes or specialist work needed.
- Preserve `main`, open-PR branches, unmatched/changed tips, local worktrees,
  branches, tags and recovery stashes. Acceptance: remote inventory confirms
  only verified obsolete refs removed; no application test rerun needed.
- DEPLOY-004 below was published in PR #80 (`29c3fd7`); its handoffs are historical.
- Result: removed 69 matching merged task branches with an atomic, leased push.
  Verified remaining refs: `main` and unmatched `codex/record-scale-compare-plans`.
  Local branches/worktrees/stashes/tags unchanged; merged PR heads preserve
  recovery information. No repository settings or application behavior changed.

## Previous implementation

**DEPLOY-004 / UI-002 — portable production foundation and numeric wheel guard (reviewed; Lead publication).**

- Contract: first entry in [requirements](NEXT_REQUIREMENTS.md). Preserve all
  pending DEPLOY-003 documentation, citation and QA changes in this checkout.
- Developer owns production configuration/launch/container files, `climate/paths.py`,
  narrowly necessary `climate/web/` integrations, shared numeric-input JS and
  layout, plus operational docs/README/References citations and own log. No
  data/provider algorithms, schema migrations, account redesign or hosting actions.
- Lead owns requirements, board, architecture decisions and own log. Developer
  may propose scope changes, not silently expand. No model/agent fan-out.
- QA owns new deployment/number-input tests, necessary existing test updates and
  own log after Developer hands off; tests before fixes, isolated temporary stores.
  Run combined offline Python and Node once, focused reruns for corrections.
- Reviewer follows QA: read-only correctness/security review except own log.
  Focus production default-deny paths/image context, proxy spoofing, host validation,
  no local regression, persistent state and accessible wheel handling.
- Acceptance: local startup retained; production config/container assets provided
  without claiming deployment/build/browser tests that weren't possible. No
  credentials or live stores touched. Provider choice remains open.
- Developer handoff: production/private-state/proxy settings, optional container,
  stable generated asset URLs and number wheel guard implemented. Focused
  isolated smokes pass; Docker and real-browser verification unavailable. QA
  now owns `tests/test_deployment.py`, `tests/test_number_wheel_guard.mjs`, exact
  source inventory in `tests/test_content_pages.py`, only necessary existing
  assertion updates and own log; no production edits.
- QA batch: Python 211 total, 202 passed/eight PG skips/one failure; Node 20
  passed. Temporary private file hard-linked into general static was downloadable.
  Developer now owns only the narrow production static-file guard correction and
  own log; preserve development assets and all QA assertions. QA reruns focused
  deployment/content/private-storage tests afterwards, then Reviewer audits.
- Correction verified: all 29 deployment/content/private-storage tests pass,
  no skips; production static requires single-link regular files. The combined
  batch was not repeated; prior Node 20 remains valid. Reviewer now owns review
  only plus own log, no production/test edits or repeated full tests.
- Review blockers (2026-10-04): unknown `CLIMATE_ENV` values still select local
  account storage in CLI resolution; broad negated parent directories in
  `.dockerignore` re-include private descendants. Nothing has been built/pushed.
  Require shared strict mode validation and an auditable exact-file image-context
  allowlist, followed by regression tests for effective inclusion/exclusion.
- Corrections implemented: 64 literal runtime-file exceptions, no directory or
  wildcard exceptions; shared mode validation precedes CLI path selection. QA
  now owns focused allowlist/CLI regressions and the two Moby citation inventory
  additions; no production edits or full-suite repeat. Reviewer verifies next.
- Final correction QA: 58 focused deployment/content/private-storage/account CLI
  tests pass, zero failures/skips. Effective literal allowlist and invalid-mode
  no-write regressions included; final independent review in progress. Actual
  image build and hosted/browser checks remain unavailable, not implied passes.
- Reviewer cleared both corrections without a new blocker. Lead owns only final
  documentation, secret scanning and authorized climate2 publication. All
  specialists have handed off; no other backlog work is assigned this round.

## Prior assessment

**DEPLOY-003 — hosting options assessment (complete locally; provider decision pending).**

- Owner: Lead / Architect. Compare official pricing, operations burden and
  required changes while preserving native local development.
- Allowed files: deployment comparison, documentation index, requirements,
  this board, Lead log and README. Citation-only addition to References is an
  explicit documentation exception; no redesign or application behavior edits.
- Acceptance: dated source-backed options; estimates distinguished from prices;
  private SQLite/PostgreSQL persistence, sessions, proxy and import constraints;
  no provider selected, purchases, deployment or live data operations.
- Validation: source/evidence consistency, local links, template parsing and
  whitespace checks. No repeat full regression for this documentation task.
- QA follow-up: own only `tests/test_content_pages.py` and own QA log. Add the
  eleven newly cited official deployment URLs to the exact reference inventory
  (preserve existing URLs/assertions), then run the offline content-page suite.
  No app/database/provider operations or unrelated edits. Hand back to Lead.
- Result: [comparison](DEPLOYMENT_OPTIONS.md) saved and linked. Eleven official
  research URLs mirrored in README/References; QA updated the exact inventory.
  All 12 focused content-page tests pass, with no skips. Jinja syntax, local
  links, credit parity, example arithmetic and whitespace checks pass. No full
  regression repeat, deployment, purchases or GitHub publication this round.

## Previous checkpoint

**REGRESSION-002 — combined deployment-feature checkpoint (reviewed; Lead integration).**
Base `083ead5` (merged PR #78), branch `codex/deployment-regression-checkpoint`.

- QA: run the documented offline Python discovery and all map/community Node
  suites once; inspect isolation before running, report exact counts/skips and
  real regressions. Write only own log; no production/test edits unless Lead
  assigns a reproduced failure separately. No live database, provider or account
  operations. Existing tests use mocked/temporary data; do not enable PG opt-ins.
- Lead: board, own log, workspace/completed-rounds context and verification
  evidence. No feature implementation. Browser inventory is empty and native
  connection failed; listed browser skill file unavailable. Do not claim visual
  verification. Hosting target requested from owner, not assumed.
- Reviewer: inspect checkpoint evidence/documentation read-only except own log;
  do not repeat unchanged suites. Developer only if a confirmed fix is assigned.
- Acceptance: fresh combined results covering UI/community and terminal-admin
  rounds, accurate limitations, concise handoff. No app/References/dependency,
  deployment configuration or permission changes.

## Verification result

QA ran the documented offline batch once at `083ead5` on 2026-10-02:
Python **204 total: 196 passed, eight expected PostgreSQL skips**, no failures;
Node **18 passed**, none skipped or failed. The skips are three cleanup, one
availability and four weather integration tests. See the newest
[QA handoff](agents/qa-log.md) for exact commands and isolation limitations.

No production or test changes were needed. Legacy account-path warnings,
SQLite ResourceWarnings and expected mocked-failure logs appeared. Inherited
filesystem sessions remain incompletely isolated. These results do not establish
browser appearance, live PostgreSQL, proxy behavior or deployment readiness.
Lead is finishing the documentation checkpoint on 2026-10-03 without rerunning
unchanged suites.
Independent evidence review is clear; no remaining checkpoint blocker.

## Completed features

- DEPLOY-002, PR #78 (`083ead5`): terminal-only administrator provisioning,
  private storage, hidden input, atomic creation. Final 27 focused tests passed;
  independent review clear. No real administrator was created.
- UI-001 / DEPLOY-001 / COMMUNITY-001, PR #77 (`1ed0b65`): concise public pages,
  closed registration, world map, opt-in local profile/public pins. Previous
  batch 192 total: 182 passes/eight skips/two errors, both corrected. Latest
  focused 22 and Node 18 passed; the combined checkpoint above supersedes that
  earlier verification limitation.
- Contracts are in [requirements](NEXT_REQUIREMENTS.md), with deployment,
  moderator provisioning and remaining limits in [community](COMMUNITY.md).
  Community stays disabled until configured; clustering is deferred.

Earlier scopes/results: [completed rounds](agents/context/completed-rounds.md).
Full previous board: `git show 083ead5:docs/AGENT_TASKS.md`.

## Recovery and limitations

Retain both recovery stashes: `climate2 REGRESSION-001 checkpoint before README demo request`
and `climate2 pre-layout working changes`. Do not reapply blindly.
No caches, environments, databases or user data are scheduled for cleanup.
Read [workspace](agents/context/workspace.md) before branching. Browser,
deployment, live PostgreSQL and production load/security validation remain open.
