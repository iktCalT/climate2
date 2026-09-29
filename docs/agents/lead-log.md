# Lead / Architect log

Writer: Agent 1 only. Follow [SKILL.md](SKILL.md).

## 2026-09-29 | MAP-002 | signed map-value differences | done

- Result: first-month baseline differences, concise numbers, estimate/unavailable
  labels and accurate cached-value terminology; no requests or scale changes.
  Requirements/policy record batched verification. Sequential Luna specialists.
- Check: focused tests caught negative-zero and removed-panel errors; fixed.
  Three Node suites passed. One Python batch ran 155 tests (8 DB skips), found
  three stale copy assertions; after corrections, 40 affected tests passed.
  No repeated full suite. Reviewer's sole README wording issue was corrected.
  Browser unavailable; no live database/provider operations.
- Next: integrate reviewed change. Differences compare displayed coarse values,
  not exact observations or a climate trend.

## 2026-09-29 | PROVIDER-003 | NOAA public selector | done

- Result: startup public reads select `noaa_core`; CMIP6 writes stay isolated.
  Admin copy follows either provider; README/status docs explain restart and
  selector-only rollback. User requested economical models: all three sequential
  specialists used Luna/medium; Reviewer found no actionable issue.
- Check: 155 offline Python tests (8 PostgreSQL skips), three Node suites passed.
  Default propagation and query parameters tested with fake connections.
  Browser unavailable (no connected browser); no live DB/account/provider work.
- Next: publish reviewed change, then restart application workers to adopt it.
  No server deployment was performed; prior coverage audits remain dated evidence.

## 2026-09-29 | PROVIDER-002 | NOAA location/presentation readiness | done

- Result: fixed coordinate-wise NOAA grid sampling, disclosed distance and
  requested/sample coordinates, provider-aware chart identity/titles and copy.
  CMIP6 remains active; its exact lookup and January 1951 history start remain.
- Check: QA 152 Python tests (8 database skips), three Node suites passed.
  Reviewer requested precise rounding wording, not a geodesic-nearest claim.
  Browser unavailable (IAB disconnected); no live DB/provider operations.
- Next: integrate after wording recheck; actual NOAA activation remains separate.

## 2026-09-29 | PROVIDER-001 | source-write isolation | done

- Result: sequential Developer/QA/Reviewer completed immutable CMIP6 write,
  migration, checkpoint and comparison identities; optional fallbacks disabled
  under non-CMIP6 selection. Public reads remain provider-selected.
- Check: 142 offline Python tests (8 database skips), seven identity regressions;
  Reviewer no findings. No UI, dependencies, provider activation or live writes.
- Next: integrate; NOAA coordinate lookup policy and provider-aware labels remain
  separate activation work. Prior read-only 2026 validation is recorded below.

## 2026-09-28 | NOAA-READINESS | saved 2026 data audit | done

- Result: read-only checks found all 8,281 canonical rows for each of January–
  August 2026 complete and finite (66,248 rows); no range/order violations.
  Dateline endpoints match all four metrics exactly. Paired CMIP6 coverage is
  only 9 canonical points/month, 15 in August; not independent truth validation.
- Check: bounded read-only PostgreSQL transaction, no fetching or data changes.
- Next: Reviewer confirmed activation blockers. Do not flip the active provider:
  Open-Meteo acquisition writes currently inherit that setting, risking NOAA
  mislabelling/overwrite (also legacy migration). Arbitrary-coordinate history
  needs a grid policy; labels and comparison CLI require provider separation.
  See reviewer handoff. Validation is not activation approval.

## 2026-09-28 | PAGES-001 | Home / References clarity | done

- Result: current source, uneven coverage, units and linked comparison guidance
  made scannable; import checkpoints moved into dated historical disclosure.
  All 52 external citation URLs preserved, no new resources or data operations.
- Check: QA 5 focused tests; 135 full Python tests (8 skips). Reviewer no findings.
  Built-in browser verified desktop Home, 390px References and disclosure.
- Next: integrate `codex/page-clarity`. Preview uses standalone templates,
  not production accounts or climate databases. QA used Sol after Luna limit.

## 2026-09-28 | MAP-001 | linked map location readouts | done

- Result: coordinated frontend implementation, QA and review. Click selection
  uses each panel's own containing cell; explicit loading/missing/error states,
  safe text, shared close, and stale-response guards preserve honest comparison.
- Check: QA passed 133 Python tests (8 skips) and three Node suites. Built-in
  browser showed identical selected coordinates with distinct synthetic −2/7 °C
  values, and closing one cleared both. Native browser access was unavailable;
  built-in browser later connected. No real DB/provider used.
- Next: integrate reviewed changes; README/Maps guidance and MapLibre citations
  updated. Browser fixture was temporary and used synthetic values only.

## 2026-09-27 | SECURITY-001 | private accounts / sequential handoffs | done

- Result: coordinated Backend → QA → Reviewer, including two backup-name
  corrections. Shared account resolver defaults outside public assets; warned
  legacy fallback preserves accounts; Flask blocks private static downloads.
  Setup closes connections. Updated storage guidance and stdlib citations.
- Check: QA reports 133 Python tests (8 database skips), Node passed; Reviewer
  independently verified denial and normal assets with temporary fake files.
  No real account database opened, moved, or deleted; no live provider calls.
- Next: integrate on `codex/project-structure` using repository-local Meow-5.
  Separate static servers and arbitrarily renamed backups require private
  storage; see [account guidance](../USER_ROLES.md#private-account-storage).

## 2026-09-27 | LAYOUT-001 | project structure / climate package | done

- Result: based `codex/project-structure` on local main `cbeda44`; preserved
  artwork/coordination edits and a pre-layout recovery stash. Grouped code and
  SQL; updated commands, resource paths, docs, and fork assignments.
- Check: 123 Python tests (8 database skips), Node, resource/CLI checks, and
  HTTP smoke checks passed. Ten core modules preserve non-import ASTs; SQL is
  byte-identical. No connected browser for visual verification; no live data changes.
- Next: fork Backend/QA/Reviewer using [task prompts](../AGENT_TASKS.md).
  [Architecture](../ARCHITECTURE.md) supersedes old file paths; all agents must
  use the restructure checkpoint. Local checkpoint is the handoff; integration
  follows independent review.

## 2026-09-27 | COORD-003 | context lookup / development caches | done

- Result: added [lookup](CONTEXT_INDEX.md) and four concise topic notes;
  condensed finished board entries. Removed about 75 MiB of regenerable
  mypy/Python caches, Finder metadata, and an empty plotting-cache directory.
- Check: links, whitespace, exact target absence, retained data/environment,
  and other agents' unchanged logs verified. No runtime code changed.
- Next: consult [workspace context](context/workspace.md) before implementation:
  this dirty checkout predates local main. Changes remain uncommitted. Deleted
  caches have no backup but regenerate; see [recovery](context/maintenance.md).
  Internal chat state and global caches were not cleared.

## 2026-09-27 | COORD-002 | agent coordination / docs/agents | done

- Result: added shared skill and four owned logs; linked startup/handoff rules
  in `AGENTS.md`, role docs, and editor rule. Existing role assignments still
  apply. Changes are local and uncommitted; other worktrees need these files.
- Check: `git diff --check` and direct link/metadata/structure checks passed.
  Bundled skill validator unavailable: venv lacks PyYAML. No runtime changes.
- Next: all agents read [SKILL.md](SKILL.md) at startup and write only their
  own log. Preserve important decisions and prune stale notes safely; no cache
  cleanup performed. Policy: [shared memory](../PROJECT_DIRECTION.md#shared-agent-memory).
