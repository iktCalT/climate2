# Reviewer / Debugger log

Writer: Agent 4 only. Follow [SKILL.md](SKILL.md).

## 2026-10-02 | COMMUNITY-001 / UI-001 | targeted fix verification | done
- Result: no remaining review blocker. `community.settings()` now uses resolved paths, ancestor inode checks, fixed protected paths and regular-file/single-link metadata; it no longer traverses static. The content test checks rendered References isolation and scoped added CSS without historical Git objects. Lead clarified the named native disclosure for optional typed coordinates is intentional and within the UI contract; the earlier third finding is closed as a design question, not a defect.
- Check: inspected targeted service/test/docs changes and `git diff --check` (clean). QA reports 22 focused Python tests passed after fixes; not rerun. No browser, live database or deployment check.
- Next: Lead integration. Earlier broad offline batch and targeted correction evidence remain separately recorded.

## 2026-10-02 | UI-001 / DEPLOY-001 / COMMUNITY-001 | independent review | done
- Result: two actionable findings and one design question on base `7342c9e`: enabled `community.settings()` rescans all static files on every API request and Maps/Register render (`community.py:55`), so growing chart caches make public traffic do unbounded filesystem work; the new content test requires `git show 7342c9e` and byte-identical References/CSS (`test_content_pages.py:139–143`), failing shallow/source checkouts and freezing later edits. The optional typed-coordinate form was placed inside a named disclosure; Lead subsequently confirmed this is intentional and allowed by the UI contract. The two defects are closed in the targeted verification entry above.
- Check: read-only route/service/JS/template/test diff review, `git diff 7342c9e --check` clean; References template hash matches base. QA reports 182 Python passes/eight skips/two pre-fix errors, corrected community module nine passes, Node 18 passes; not rerun. No browser, live database or deployment check.
- Next: see targeted fix verification above. No confirmed auth, XSS or quota bypass in reviewed paths.

## 2026-10-02 | REGRESSION-001 | stale precipitation copy assertion | done
- Result: no actionable finding in the resumed checkpoint at `5b17b0d`. The test separately asserts mean daily precipitation in mm/day and monthly average daily rate/not a monthly total inside each NOAA/CMIP6 iteration; `templates/references.html` contains both claims in both provider branches. No existing assertion was removed. README demo remains in the base; both named recovery stashes remain present.
- Check: reviewed working diff, surrounding provider loop/template copy, task evidence and `git diff --check` (clean). QA reports the corrected module passed 10 tests; not rerun. The prior 182-test batch had one stale-copy failure, eight expected PostgreSQL skips and 173 passes; Node 13 passed. This is not a fresh full-suite pass.
- Next: Lead may integrate. No browser, live database/provider, network or deployment check; inherited filesystem-session isolation limitation remains disclosed.

## 2026-10-01 | HISTORY-002 | editable Location coordinates | done
- Result: no actionable correctness, security, provenance or UX finding on `codex/edit-location-coordinates`, base `a6491c1`. One native GET form precedes covered/empty results; validated requested floats preserve decimal precision and signed zero independently of NOAA sampling. Bounds, labels, guidance, explicit submission, Clear, coverage and provider copy satisfy the contract. README/References document editing; no external resource added.
- Check: reviewed template, surrounding validation/history route, paired documentation and actual parsed-form regression assertions. QA reports 57 focused route/content tests passed; not rerun. No Git, browser, network, database, provider or production/test edits.
- Next: Lead integration; browser verification remains unavailable.

## 2026-10-01 | HISTORY-001 | seasonal coverage readouts | done
- Result: no actionable correctness or security finding on `codex/seasonal-coverage-readouts`, base `eab3e85`. Counts use the same non-null values as unchanged means; December remains assigned to the following winter year. Contiguous transformed-year seasons retain NaN/zero gaps with connection disabled; empty histories stay empty. Metric units, default/menu behavior, version-only cache invalidation, coverage guidance and paired Plotly citations satisfy the contract.
- Check: scoped diff, surrounding chart/cache/history code and focused test assertions reviewed; `git diff --check` passed. QA reports 59 focused chart/route/content tests passed; not rerun. No browser, network, live database or provider operations.
- Next: Lead integration; browser verification remains unavailable.

## 2026-10-01 | MAP-010 | keyboard coordinate selection | done
- Result: no actionable correctness or security finding in the working-tree diff on `codex/map-coordinate-selection`, base `69b6a04`. The native form validates finite bounded values before map/selection changes, rechecks all-live-panel readiness, centers via the existing move synchronization path, and selects through the established popup model. Explicit same-center sync covers divergent peers; removed maps are skipped. Clear only clears popup state. Zoom, bearing, pitch and scale are preserved. README and References explain the behavior; no third-party resources were added. `coordinateReadiness` starts undefined intentionally so its first update initializes the status; this is not a defect.
- Check: read-only diff, surrounding movement/selection lifecycle and focused regression assertions reviewed. QA reports 50 focused Flask/content tests and 13 Node tests passed; not rerun. No browser, live database, provider, or network access.
- Next: Lead integration; no actionable findings. Browser verification remains unavailable.

## 2026-09-30 | MAP-009 | manual saved-data retry | done
- Result: no production blocker in the per-panel retry flow. Only current non-aborted failures expose retry; explicit clicks require a live initialized panel, disable repeat clicks, cancel that panel's debounce, and reuse the generation-guarded saved-data request. Success, empty coverage, invalid bounds, movement and removal hide/reset the control. Stale/removed work cannot publish status or clear a newer controller. Month/location/view/scale and other panels are not changed by retry. No API/provider fetch path was added.
- Check: inspected scoped diff and lifecycle/test assertions; scoped `git diff --check` passed. QA added actual `invalidateViewport` → `AbortError` rejection and late-success-after-abort assertions, including unchanged loading status, no acceptance, and hidden/disabled retry. QA reports 48 focused Flask tests and eight Node tests passed after that addition; not rerun here. No browser, database, or provider operations.
- Next: Lead may integrate; no findings remain. Browser verification remains unavailable.

## 2026-09-30 | MAP-008 | readable map metrics | done
- Result: no actionable production or test finding on `codex/readable-map-metrics`, base `f95d638`. The template-local mapping supplies unit-bearing headings, map accessible names and selector labels; form values, query/API keys and JS metric keys remain the existing identifiers. Precipitation is consistently described as a monthly average daily rate, not a monthly total. NOAA wording identifies the saved 2° × 4° sampling grid without calling it native NOAA resolution; CMIP6 guidance and existing references/credits remain intact.
- Check: reviewed scoped diff and surrounding route/template behavior; `git diff --check f95d638` passed. QA reports 47 focused Flask/content tests and eight Node map tests passed; not rerun. No browser or live-data checks.
- Next: Lead integrates and updates MAP-008 status in `NEXT_REQUIREMENTS.md`; no review findings.

## 2026-09-30 | MAP-007 | retain map selection | done
- Result: no production blocker on `codex/retain-map-selection`, base `d0bafd6`. Explicit selections validate before discovery/edit rendering; ordinary explicit maps skip availability reads. The edit URL retains ordered months and variable; required dates and selected variable render server-side. Existing and new rows support remove/renumber, with the four-month cap. No-JS GET submission preserves the map and baseline; discovery errors preserve entries and hide diagnostics. QA follow-up now asserts parsed-form submission returns the same ordered map and executes initialization/removal for a prefilled row, closing both coverage gaps.
- Check: read-only route/template/test review; scoped `git diff --check d0bafd6` passed. QA reports 45 focused Flask/content tests and eight Node selector/map tests passed; not rerun. No browser, live database, or network checks.
- Next: Lead publication/integration; no review findings.

## 2026-09-30 | MAP-006 | popup row layout | done
- Result: no actionable finding on `codex/map-popup-line-layout`, base `60d4a92`. `line()` creates a separate block row per entry, nests `strong` for emphasized text, and uses `textContent` for all strings. Popup values and comparison numbers retain their prior calculations, units, and provenance. README/References give the requested readability guidance. QA structural assertions cover month, baseline, value, difference rows, and nested user text.
- Check: read-only scoped diff and surrounding popup logic inspection; `git diff --check 60d4a92 -- static/map_selection.js README.md templates/references.html tests/test_map_selection.mjs` passed. QA reports all seven Node map tests passed; not rerun. No browser, live data, or network checks.
- Next: Lead integrates; no actionable findings.

## 2026-09-30 | PAGES-002 | environmental-awareness copy | done
- Result: no actionable finding on `codex/environment-awareness-copy`, base `435129a`. The three-page diff frames exploration as awareness, labels the preview illustrative, distinguishes NOAA interpolated estimates from CMIP6 cell readouts, and limits two-month interpretation. Saved sampling is not called NOAA's native grid; units, coverage caveats, actions, provider branches and existing credit URLs remain.
- Check: read-only scoped diff, surrounding copy and focused test inspection; `git diff --check 435129a` passed. QA reports eight content and ten NOAA-location tests passed with database reads guarded; not rerun. Prior MAP-005 full regression evidence reused. No browser or live data check.
- Next: Lead integrates; visual browser check remains unavailable.

## 2026-09-30 | MAP-005 | manual scale / panel readiness | done
- Result: no actionable finding on `codex/map-scale-loading-sync`, base `89f4e15`. Explicit readiness gates both provider paths after layer initialization; removal clears readiness/raster inputs. Pre-load selections reach first render; cleared NOAA data cannot redraw, and existing generation/abort guards prevent stale restoration. No new requests/timers. README/References citations and environmental-awareness direction match scope.
- Check: read-only diff, lifecycle and actual-handler regression inspection; `git diff --check` passed. QA reports 162 Python tests/eight expected skips and seven Node passes; not rerun. Browser disconnected; prior user screenshot verifies MAP-004 appearance only.
- Next: Lead integrates; live scale interaction remains unverified.

## 2026-09-30 | MAP-004 | smooth NOAA raster / JSON hole handling | done
- Result: P2 resolved on `codex/smooth-noaa-display`, base `5a557e0`. NOAA-only finite legacy inputs and final aggregation guard prevent invalid JSON; raw grid rows preserve explicit null holes. CMIP6 remains unchanged. No remaining actionable interpolation, lifecycle, scale, provenance or security finding.
- Check: read-only fix/regression inspection and `git diff --check` passed. QA reports six interpolation, 34 map/route and eight provider-identity tests passed after correction; earlier full batch had 160 Python/eight skips and six Node passes. Not rerun. Browser disconnected; no live/network operations.
- Next: Lead integrates; browser behavior remains unverified.

## 2026-09-29 | MAP-003 | map history links and coordinate form | done
- Result: no actionable finding in the scoped diff against `dfcab70`. Popup links use the finite selected numeric coordinates and preserve JavaScript round-trip precision; they are root-relative, rendered in all popup states, and use text content. Selection has no link-triggered request/navigation. The Locations GET form retains its action/ranges, adds explicit label IDs, `step="any"`, shared guidance and capped full width. README/Maps/References copy explains differing history sampling; existing References citations are unchanged.
- Check: read-only surrounding-code/diff review and `git diff --check dfcab70` passed. QA reports 156 Python tests (8 PostgreSQL skips) and three Node suites passed; not rerun. No live data, network, or browser access.
- Next: Lead integrates; no findings.

## 2026-09-29 | MAP-002 | numeric map differences | done
- Result: the P3 copy finding was resolved; README.md:28 now says
  “PostgreSQL-cached values.” No other confirmed defect in the scoped review.
- Check: verified the exact line and `git diff --check ee0e568`; wording-only
  correction, so tests were not rerun. Prior QA results: three Node suites and
  40 affected Python tests passed. No browser or live data access.
- Next: none; Lead integrates.

## 2026-09-29 | PROVIDER-003 | activate saved NOAA public reads | done

- Result: no actionable finding in the scoped activation diff. The startup
  selector propagates to Flask, public history/map queries and saved-month
  discovery; Open-Meteo writes and migration remain fixed to CMIP6; map/history
  fallbacks remain disabled for NOAA public reads. Conditional admin copy and
  current README/PostgreSQL/provider status match the selected provider, and
  dated evaluation conclusions are labeled historical. Test changes preserve
  CMIP6-only map-fetch coverage and add fake-SQL selector and no-fallback checks.
- Check: read-only diff and caller/test inspection; `git diff --check HEAD`
  passed. QA reports 155 Python tests (8 PostgreSQL skips) and three Node map
  suites passed; not rerun. No live DB/provider/network or browser check.
- Next: Lead integrates; browser verification remains unavailable this round.

## 2026-09-29 | PROVIDER-002 | NOAA location/presentation readiness | done

- Result: one P3 wording finding. `location_sampling.py:21` says “closest canonical grid point,” and Home/Locations call the coordinate-wise result “nearest”; independent latitude/longitude rounding need not minimize great-circle distance (for example, the 89°N, 2°E tie chooses 88°N, 0°E while the pole is closer). Describe coordinate-wise rounding in these labels; keep the agreed sampling rule. No other actionable issue found in fixed sampling, cache-only provider reads, chart identity/titles, two-mode copy, or citations. Public selector remains CMIP6.
- Check: read-only code/requirements/tests inspection. QA reports 152 Python tests (8 PostgreSQL skips) and three Node suites passed; not rerun. No browser, live database, provider, or network check.
- Recheck: helper docstring and Home/Locations now say latitude and circular longitude are rounded separately; the former explicitly distinguishes this from great-circle nearest. Sole finding resolved. QA reports 10 NOAA and 5 content-page focused tests passed; not rerun here.
- Next: Lead integrate. Browser remains unverified because IAB is disconnected.

## 2026-09-29 | PROVIDER-001 | immutable acquisition source | done

- Result: no actionable finding in the six production-file diff. Open-Meteo writes, source probes, prefetch checkpoints, and legacy migration use fixed CMIP6; comparison loads explicit NOAA and CMIP6; public map/history/cache reads still use the selected provider, and both optional fallback paths stop under NOAA. Caller search found no remaining writer keyed by the public selector. This does not establish NOAA activation readiness; coordinate policy and public labels remain separate.
- Check: reviewed diff, surrounding callers, seven fake-connection regressions, and `git diff --check`; focused tests passed (7). QA reports 142 Python tests (8 database skips); not rerun in full. No live data or network access.
- Next: Lead integrate PROVIDER-001; assign activation work separately.

## 2026-09-28 | NOAA-READINESS | public provider activation | done

- Result: activation by changing `ACTIVE_CLIMATE_PROVIDER` alone is unsafe. Open-Meteo acquisition and legacy migration write with that constant, so future writes could masquerade as or replace NOAA. Locations query exact coordinates while NOAA imports canonical grid points only; most user-entered locations would be empty. Public copy and map labels remain Open-Meteo-specific; the comparison CLI would compare NOAA with itself. Maps and saved-month discovery are cache-only/provider-scoped; footer has a NOAA branch. The first/last-five-year scope supersedes the older full-history prerequisite.
- Check: read-only code and requirements inspection; no database, network, provider request, or tests run.
- Next: Lead define activation contract; Backend separate source identities and location policy, then QA validate with isolated data and revised copy.

## 2026-09-28 | PAGES-001 | Home and References clarity | done

- Result: no concrete finding in the `a86172a` page refresh. Checked active CMIP6/inactive NOAA claims against provider and route code; coverage, °C and mean daily mm/day, cache-only browsing, linked comparisons, manual scales, dated history, semantic links/headings, responsive CSS, retained credits and external-link protection. Production changes stay within assigned page/CSS scope.
- Check: reviewed diff and surrounding code; `git diff --check a86172a` passed. QA reports 5 focused tests and 135 offline Python tests (8 database skips). Lead reports desktop Home and 390px References/disclosure browser checks; not independently rerun. No live data accessed.
- Next: Lead integrate; no Reviewer fix requested.

## 2026-09-28 | MAP-001 | linked comparison readouts | done

- Result: prior P3 Maps-page wording finding resolved. `templates/maps.html:24` now describes each panel's own value and source, explicitly including labelled display estimates; it no longer calls estimates saved values. No remaining finding in the bounded review of per-panel containment/value/source, loading and stale guards, safe text, popup close and cleanup, and citations.
- Check: all three Node map suites passed before the wording correction; `git diff --check` clean. QA reports 133 Python tests (8 skips), then a passing template Node check and Jinja parse after the correction; not rerun here. No live data or independent browser check; Lead reported synthetic browser verification.
- Next: Lead integrate; no further Reviewer action unless code changes.

## 2026-09-27 | REVIEW-003 / SECURITY-001 | private static storage | done

- Result: no remaining finding in the bounded requirement. The prior P2
  disclosures for `users.db.bak` and `users.db_backup` are fixed. Reviewed
  resolver precedence, static path/alias/sidecar denial, setup closure, tests,
  and updated docs. Arbitrarily renamed database copies require private storage;
  a separate static server needs its own guard.
- Check: independent temporary fake-file GET/HEAD check denied seven database
  names and served three normal assets; `git diff --check` passed. QA reports
  133 Python tests (8 skips) and Node pass; full suite not rerun. No real DB read.
- Next: Lead integrate; no further Reviewer action unless code changes.

## 2026-09-27 | REVIEW-001 | restructure / account storage exposure | done

- Result: no introduced regression confirmed in `cbeda44..9836be2`.
- **P1, pre-existing:** [app.py](../../../climate/web/app.py#L49), lines 49–54,
  serves static files while defaulting accounts to `static/users.db`. Anonymous
  `GET /static/users.db` returned HTTP 200 and a complete SQLite database in a
  temporary fake-data reproduction; real accounts were never read.
- Check: 16 admin tests passed; error HTML escapes markup; ten core modules
  unchanged except imports; schemas byte-identical; focused secret checks passed.
- Next: account exposure and the inherited connection warning were addressed
  by SECURITY-001; see the newer review and [QA log](qa-log.md). No production
  edits or live DB checks were made during REVIEW-001.
