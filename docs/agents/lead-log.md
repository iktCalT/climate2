# Lead / Architect log

Writer: Agent 1 only. Follow [SKILL.md](SKILL.md).
Older results: [completed rounds](context/completed-rounds.md). Full evidence:
`git show 5b17b0d:docs/agents/lead-log.md`.

## 2026-10-04 | MAINT-001 | GitHub merged-branch cleanup | done

- Result: removed 69 obsolete climate2 remote task branches, each current tip
  matching its merged PR into main. Kept main and unmatched
  `codex/record-scale-compare-plans`; no local branches, worktrees, tags or stashes
  deleted. Repository automatic deletion setting unchanged.
- Check: full branch/PR inventory, dry run, exact-tip leases and atomic push;
  final remote inventory confirms the two retained refs. Merged PR head SHAs
  and retained local refs support branch recreation. No application tests needed.
- Next: publish this policy/handoff; no unfinished branch was assumed disposable.

## 2026-10-04 | DEPLOY-004 / UI-002 | portable deployment and wheel guard | done

- Result: sequential Developer/QA/Reviewer delivered opt-in production serving,
  private persistent state, explicit proxy/host trust and numeric wheel guard.
  Native local startup preserved; [runbook](../DEPLOYMENT.md) covers operator
  steps. Image context is an exact-file allowlist; CLI rejects invalid modes.
- Check: initial Python 211: 202 passes/eight PG skips/one hardlink failure;
  Node 20 passes. Corrected static guard and review findings independently
  verified by 58 focused passes; final review clear. No repeated full suite.
- Next: publish to climate2. Provider choice, real image build, browser and hosted
  verification remain open; no deployment, spending or live data operations.
  Recovery stashes preserved; repository-local Meow-5 identity verified.

## 2026-10-03 | DEPLOY-003 | hosting comparison | done

- Result: added [deployment options](../DEPLOYMENT_OPTIONS.md), comparing Render,
  Railway and a DigitalOcean VPS with dated official rates, cost assumptions,
  management duties and local/online portability. Linked from both indexes;
  mirrored all eleven research URLs in README and References without redesign.
- Check: inspected storage/session/import code; Jinja syntax, local comparison
  links, mirrored credits, arithmetic and whitespace pass. QA updated the exact
  source inventory; all 12 content-page tests pass. No production deployment,
  package installation, live data operation or GitHub publication this task.
- Next: owner chooses provider/budget. Persistent private SQLite, session/proxy
  configuration and production serving still need implementation/verification.
  Canvas omitted because its mandatory output path is outside climate2.

## 2026-10-03 | REGRESSION-002 | combined deployment checkpoint | done

- Result: reconciled current `083ead5`/PR #78 state with the pending checkpoint;
  administrator setup was already merged. Preserved existing documentation and
  QA handoff; cancelled a stale bootstrap review before any changes.
- Check: QA's 2026-10-02 batch: Python 204 total, 196 passed/eight expected PG
  skips/no failures; Node 18 passed. No production/test edits or repeated suites.
  Independent evidence review clear; browser/live deployment unverified.
- Next: publish the concise checkpoint. Hosting target remains
  unspecified; no configuration, accounts, live stores or caches changed.

## 2026-10-02 | DEPLOY-002 | terminal administrator setup | done

- Result: new terminal-only create-admin command closes the fresh-deployment
  moderator gap without reopening registration. Hidden double password entry,
  private initialized storage and atomic creation; no real account provisioned.
- Check: QA found and verified a CLI separator correction; Reviewer found and
  verified selected public-symlink rejection. Final 27 focused tests pass under
  QA and Reviewer, with no remaining blocker. No full/Node repetition.
- Next: integrate; operator instructions in
  [user roles](../USER_ROLES.md#first-administrator-on-a-new-deployment).
  References/UI and deployment configuration remain untouched.

## 2026-10-02 | UI-001 / DEPLOY-001 / COMMUNITY-001 | public launch features | done

- Result: concise public pages; hosted registration blocked; world camera;
  opt-in device profile/public pin service behind deployment enable/secret.
  Owner chose immediate comments with limits/admin removal; clustering deferred.
  References body/styles unchanged. Sequential Sol continued after Luna quota.
- Check: full offline Python 192: 182 passed, eight PostgreSQL skips, two
  defects. Admin throttle/Unicode corrections independently pass nine community
  tests. Node 18 passed; final path/test-portability corrections pass 22 focused
  tests and independent review. No browser/deployment verification.
- Next: publication. Private storage,
  existing admin provisioning, proxy limits and moderation documented in
  [community guide](../COMMUNITY.md). Recovery stashes untouched.

## 2026-10-02 | REGRESSION-001 | offline checkpoint recovery | done

- Result: recovered relevant stashed commands/evidence without overwriting
  newer work; QA corrected one stale precipitation-copy assertion, preserving
  units and non-total caveat for both providers. No production change.
- Check: original full Python batch: 182 total, 173 passes, eight expected
  PostgreSQL skips, one failure; Node 13 passed. Corrected module: 10 passed.
  Full batch not rerun. Browser/live integration unverified; inherited filesystem
  sessions limit isolation. Independent review cleared the correction/evidence.
- Next: publication status in GitHub for `codex/finish-offline-regression`, base `5b17b0d`.
  Both named recovery stashes retained; completed scopes indexed, board shortened.

## 2026-10-02 | README-DEMO-001 | comparison screenshot | done

- Result: user-provided NOAA August 2026/1950 comparison added near README top
  as an unchanged local PNG, with alt text, caveats and source credits. Website
  References records provenance. Branch `codex/readme-demo-image`, base `50af280`.
- Check: PNG 2878×1432, 2,372,661 bytes, valid CRCs and no text/EXIF metadata;
  visually inspected, original bytes preserved. Relative link/anchor and 11
  content tests passed. No runtime/data changes.
- Next: REGRESSION-001 remains deferred in its named stash (see board); one
  stale precipitation-copy assertion still needs correction after QA quota
  failure. No lost edits; separate pre-layout recovery stash retained.

## 2026-10-01 | HISTORY-002 | editable location coordinates | done

- Result: one native GET coordinate form stays above history and empty results,
  retaining requested coordinates without extra rounding or substituting NOAA's
  sample. Clear returns to blank entry without reading history. README and
  References explain editing. No backend, data, dependency or map changes.
- Check: 57 focused route/content tests passed; review cleared. Parsed-form
  resubmission, both providers, zero/negative values and Clear verified with
  mocked reads. No browser connection or live data/deployment operations.
- Next: publication status in GitHub for `codex/edit-location-coordinates`,
  base `a6491c1`; no further specialist task assigned.
