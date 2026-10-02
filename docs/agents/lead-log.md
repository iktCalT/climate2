# Lead / Architect log

Writer: Agent 1 only. Follow [SKILL.md](SKILL.md).
Older results: [completed rounds](context/completed-rounds.md). Full evidence:
`git show ef5de20:docs/agents/lead-log.md`.

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

## 2026-10-01 | HISTORY-001 | seasonal coverage readouts | done

- Result: chart hover metadata reports per-metric contributing months and units;
  existing means/winter labels retained. Explicit missing years remain gaps;
  v7 render identity replaces stale HTML without deleting old files. Locations,
  README and References explain fixed groups, partial coverage and sources.
- Check: 59 focused chart/route/content tests passed; review cleared. Luna
  quota failure and stalled Sol QA required sequential replacement, preserving
  partial tests. No live data or browser; no map/dependency changes.
- Next: publication status in GitHub for `codex/seasonal-coverage-readouts`,
  base `eab3e85`; no further specialist task assigned.

## 2026-10-01 | MAP-010 | keyboard map coordinate selection | done

- Result: typed coordinates center synchronized maps and open linked readouts;
  clear closes them without movement or fetching. Readiness, bounds and removed
  panels are guarded; dates, metric and manual scale stay unchanged. README and
  References updated. Branch `codex/map-coordinate-selection`, base `69b6a04`.
- Check: 50 focused Flask/content and 13 Node tests passed; review cleared.
  Lead corrected readiness status and required same-center synchronization
  evidence. Initially undefined readiness is intentional, not a defect. No live
  browser, database, provider or deployment operations.
- Next: publication status in GitHub; no additional specialist task assigned.

## 2026-10-01 | COORD-005 | concise current handoffs | done

- Result: archived completed board scopes into the existing completed-rounds
  index; refreshed workspace snapshot and reconciled prior publication status.
  Base `ef5de20`, branch `codex/refresh-agent-handoffs`. Other agents' logs,
  application code, data, environments and caches untouched; no files deleted.
- Check: five-file scope, 16 local links, 16 ancestor revisions and whitespace
  passed. Board reduced from 1,066 to about 300 words. Prior application results
  retained, not rerun for this docs-only round.
- Next: no specialist or application assignment; publication status is in GitHub.
