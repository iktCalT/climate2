# Backend Developer log

Writer: Agent 2 only. Follow [SKILL.md](SKILL.md).

## 2026-10-02 | DEPLOY-002 | terminal administrator provisioning | done
- Result: `create-admin USERNAME` collects two hidden TTY passwords and rejects echo fallback, bad arguments/credentials, missing or unsafe account stores. Creation inserts the hashed administrator and default profile in one transaction; duplicate accounts remain unchanged. QA's `-- create-admin` dispatch issue and Reviewer's public symlink-to-private path issue now fail before any account change. Existing valid grant/revoke behavior remains intact. No real account was used.
- Check: syntax and diff checks passed. Isolated temporary-store smokes covered hash/profile, duplicate, rollback, input rejection and public symlink rejection with unchanged private DB. Focused bootstrap (10) and admin-role (16) tests passed offline after final path fix; full suite left to QA.
- Next: QA verifies path correction, then Reviewer inspects. Contract: [DEPLOY-002](../NEXT_REQUIREMENTS.md#terminal-only-administrator-provisioning).

## 2026-10-02 | COMMUNITY-001 | bounded storage-path validation | done
- Result: removed recursive static traversal. Resolved paths and bounded ancestor identity checks reject static/symlink/case aliases. Existing stores must be regular files with exactly one hard link; all hard-linked stores are rejected. Known account/climate paths retain resolved-path and filesystem-identity protection. Metadata/configuration failures return the same generic disabled-storage error.
- Check: all nine community tests passed with PostgreSQL flags disabled; AST and diff checks passed. Isolated smoke forbade `rglob`, verified safe missing/existing paths and rejected static paths, symlink aliases, actual case aliases, hard-linked files and directories. Existing legacy-path/SQLite ResourceWarnings persisted.
- Next: QA owns path regression assertions; Reviewer verifies correction; Lead updates deployment documentation. No other production/test files changed.

## 2026-10-02 | COMMUNITY-001 | QA moderation / Unicode corrections | done
- Result: administrator deletion bypasses public network/posting throttles; owner deletion retains its rate checks. Route authentication, same-origin and CSRF requirements remain unchanged. Strict UTF-8 text validation rejects surrogate characters with CommunityError 400 before opening/creating the store. Only service and own log changed; QA assertions untouched.
- Check: isolated `unittest discover -s tests -p test_community.py` passed all nine tests with PostgreSQL flags disabled; service AST and `git diff --check` passed. Existing legacy account-path warning and test SQLite ResourceWarnings appeared. No full-suite repetition, live database or deployment operations.
- Next: QA verifies corrections, then Reviewer audits final implementation.

## 2026-10-02 | COMMUNITY-001 | opt-in local profiles / public pins | done
- Result: separate private SQLite service; disabled unless enable flag, secret and limits validate. Atomic quota/IP throttles, retained deletion events, bounded paged public reads, private own-pin list and owner/admin removal. Maps/Registration share consent-only local storage; explicit placement/publication, plain-text marker comments, abort/generation guards, manual retry/load-more. Administrator CSRF needs no local profile. Static aliases protected; no dependencies, resources or live deployment.
- Check: Python/Jinja/Node syntax and diff checks passed. Temporary-store smokes cover quota races, retained cooldown, huge input bounds, public-field isolation, origin/body limits and admin-CSRF-only deletion. Storage smoke proves zero ordinary access, consent creation/forgetting and denied-storage handling.
- Next: QA full regressions and browser-module coverage; Reviewer security audit. Browser/deployment unverified; inherited test filesystem sessions remain.

## 2026-10-02 | UI-001 / DEPLOY-001 | concise pages, registration closure, world camera | done
- Result: preserved concise Home/Maps/Locations draft; restored all-state sampling/season help, visible Location units/source caveats and scoped fullscreen height preservation. Registration GET explains temporary closure/owner capacity, POST returns 403 without account/profile writes; existing login/admin untouched. Shared nav names closure. Maps constructor fits ±180°/±85° bounds, preserving zoom constraints and synchronization. No References edits, resources or dependencies.
- Check: five Jinja templates and Python AST valid; structural comparisons verified registration-only backend, nav-only layout, camera-only map-script, append-only CSS and untouched References. `git diff --check` passed. Full offline suites belong to QA; browser/live deployment unverified.
- Next: QA owns rendered-state, registration/no-write and world-camera regressions; Lead coordinates follow-on COMMUNITY-001.

## 2026-10-01 | HISTORY-002 | editable Location coordinates | done
- Result: one native GET coordinate form now precedes entry/result content, including empty coverage. Results prefill validated requested lat/lon without extra rounding; zero and negative decimals remain intact. Labels, bounds, required flags and guidance retained; result heading/button explain explicit submission. Clear links to blank entry. Provider provenance, coverage and seasonal guidance remain. README/References document editing; no new external resources.
- Check: Jinja compilation and six offline Flask entry/covered/empty renders across both providers passed, including precise decimal/zero prefills, form uniqueness/order and Clear URL; both References branches passed. `git diff --check` passed. No backend/test edits, live DB/network, browser, chart writes or Git mutations.
- Next: QA owns mocked route resubmission/validation and content regressions; branch `codex/edit-location-coordinates`, base `a6491c1`.

## 2026-10-01 | HISTORY-001 | seasonal chart coverage | done
- Result: seasonal aggregation preserves monthly means and winter assignment while adding per-metric non-null counts and explicit zero-count NaN seasons across the complete observed year span; empty histories stay empty. Hovers show x/3 months and °C or mm/day; precipitation axis now uses mm/day, chart version is v7, and Locations/README/References explain fixed Northern Hemisphere groups and coverage limits. Added official Plotly hover/customdata citations in both public references.
- Check: Python AST and Locations/References Jinja parses passed; in-memory chart smoke passed winter assignment, zero-count NaN, 16 traces, hover metadata, disabled gap connection, and precipitation axis. Follow-up sparse 1951–2026 and empty-history smokes passed. `git diff --check` passed. No live data/provider, persistent generated cache, browser or full test operations.
- Next: QA owns focused chart, route cache-version and content verification.

## 2026-10-01 | MAP-010 | keyboard coordinate selection | done
- Result: Open Maps now has labelled decimal latitude/longitude inputs, explicit submit and clear controls, range validation with a live status, and readiness gating across live panels. Valid submits recenter through one panel's existing synchronized movement lifecycle and open linked readouts; clear only closes readouts. Removed panels are skipped during synchronization. Readiness transitions now update the status and button through one shared helper while preserving messages when readiness is unchanged. README and References document the interaction and bounds.
- Check: `node --test tests/test_map_template.mjs` (2 passed before the readiness-helper correction); `node --test tests/test_map_selector.mjs` (1 passed); focused Maps Flask render and `git diff --check` passed after correction. QA will update the template harness for the shared helper. No live data or browser check; browser unavailable.
- Next: QA owns coordinate form binding, bounds, invalid input, readiness/removal, one/four-panel, and view/scale regressions.

## 2026-09-30 | MAP-009 | per-panel saved-data retry | done
- Result: Maps exposes an accessible month-labelled retry button only after a current request failure. Explicit retry cancels pending movement debounce and reuses the panel's generation-guarded cache request; movement, success/empty, invalid bounds and removal hide/reset it. README and References document error-only saved-cache behavior.
- Check: extracted viewport lifecycle functions compiled through Node; `git diff --check` passed. No focused behavior suite/browser run; QA owns the retry lifecycle matrix.
- Next: QA verifies retry success/failure, panel isolation, debounce, bounds, stale/aborted responses and removal.

## 2026-09-30 | MAP-008 | readable map metrics | done
- Result: Maps headings, ARIA names and selector text use clear unit-bearing labels while submitted values and JS metric keys stay internal. Selector and precipitation map context explain precipitation as a monthly average daily rate. NOAA guidance/status name the saved sampling grid; README and References document the labels and rate.
- Check: Jinja parse/render smoke for all four labels, raw selector/API key preservation and status wording passed; `git diff --check` passed. No suite/browser run; QA owns focused route/content and Node regressions.
- Next: QA verifies rendered copy and edit round trips; no known developer blockers.

## 2026-09-30 | MAP-007 | retain map selection | done
- Result: Change selection URL preserves ordered months and variable. Route validates explicit values before edit mode, skips availability for normal map renders, and keeps invalid/incomplete inputs at 400. Selector fields render selected rows server-side; existing add/remove behavior and limits remain, with no initial focus. README and References describe editing the comparison.
- Check: mocked Flask route smoke passed URL order, prefilled values, generic discovery failure, 400 cases, bare selector, and explicit-map discovery bypass. Python AST, Maps/References Jinja parsing and `git diff --check` passed. No full tests, browser, live data or provider calls; QA owns regressions.
- Next: QA updates/runs route and selector regressions, then Reviewer.

## 2026-09-30 | MAP-006 | popup row layout | done
- Result: `line()` now appends one block `div` per popup row, nesting `strong` for emphasized text and retaining `textContent`. README and References describe readable label/value rows. No data, arithmetic, links, scale or requests changed.
- Check: JS syntax, direct DOM-shape smoke, References Jinja parse and `git diff --check` passed. Existing Node test stops at its old direct-child text assertion (line 213); QA owns updating the fixture/assertion and adding structural regressions. No full suite, live DB, browser or commit.
- Next: QA updates and runs focused Node map tests, then Reviewer.

## 2026-09-30 | PAGES-002 | environmental-awareness copy | done
- Result: README, Home and References now state the awareness purpose; Home labels its preview illustrative, gives provider-aware readouts and a two-month trend caveat. NOAA smoothing is tied to the saved 2° × 4° sampling grid without claiming added accuracy. Credits, actions, units and cache gaps remain.
- Check: offline Jinja renders for Home and References under NOAA and CMIP6 passed; `git diff --check` passed. No full suite, live database, browser or commit; QA owns focused content tests.
- Next: QA verifies copy and preserved credits/actions, then Reviewer.

## 2026-09-30 | MAP-005 | scale synchronization during source loading | done
- Result: Maps tracks `styleReady` after layer initialization and clears it plus saved raster inputs on removal. Actual manual-scale handler and NOAA redraw use initialization rather than `isStyleLoaded()`; NOAA and CMIP6 update while basemap sources load. Pre-initialization choices remain the first-render scale. Added behavior guidance and official MapLibre v6.6.0 loading-source citations to README/References.
- Check: focused execution of actual handler/redraw passed both provider paths, mixed initialized/uninitialized states, cleared data, removed panel and rapid choices with full-loaded predicate false. Jinja/inline module syntax and whitespace passed. No full-suite/live checks or commits.
- Next: QA updates template harness initialized-panel fixtures (`styleReady: true`) and adds regression, then Reviewer.

## 2026-09-30 | MAP-004 review follow-up | strict NOAA JSON | done
- Result: confirmed canonical NaN broke strict response JSON through legacy GeoJSON. NOAA-only legacy bucketing/nearby lookup now exclude null/nonfinite values, while original rows retain interpolation null holes. Final NOAA feature guard excludes nonfinite aggregation results, including finite-input overflow; CMIP6 path unchanged.
- Check: targeted mocked `viewport_geojson` reproducer fails before fix and passes strict `json.dumps(..., allow_nan=False)` after fix for null, NaN, positive/negative infinity and finite-input aggregation overflow. Interpolation null holes, finite feature values, no-fetch assertion, Python AST and `git diff --check` passed. No live data or full-suite rerun.
- Next: QA adds strict-JSON regression; Reviewer rechecks the focused change.

## 2026-09-30 | MAP-004 | smooth NOAA map raster | done
- Result: resumed saved patch on `codex/smooth-noaa-display`; canonical NOAA halo grid feeds numeric bilinear raster/readouts, transparent holes, bounded Mercator canvas, local manual-scale redraw and stale clears. Fixed fill-opacity expression and concise NOAA-only status; clarified CMIP6 grid and layer-order copy. Legacy response fields and CMIP6 display remain compatible. MapLibre CanvasSource/style citations included.
- Check: Node syntax for interpolation/selection and inline Maps module, Python AST, Jinja parsing and `git diff --check` passed. No live operations or dependencies. Full offline regressions and synthetic raster verification deferred to QA/Lead; browser disconnected.
- Next: QA owns boundary, hole, scale-redraw and async regressions; Lead owns synthetic visual check. Contract: [requirements](../NEXT_REQUIREMENTS.md#smooth-estimated-noaa-map-display).

## 2026-09-29 | MAP-003 | map history links and coordinate form | done
- Result: valid selected map coordinates now link to saved Locations with round-trip numeric precision in ready/loading/missing readouts; popup and page guidance explain independent history sampling. Locations form has associated input IDs, responsive width, arbitrary precision and south/west guidance. No routes, data access, packages or citations changed.
- Check: `node --check static/map_selection.js`, Jinja syntax compilation for the three templates, and `git diff --check` passed. Regression suite/browser check not run; QA owns the batch pass.
- Next: hand off to Lead and QA; no known blockers.

## 2026-09-29 | MAP-002 review follow-up | README map terminology | done

- Result: changed README tile reuse wording from PostgreSQL “observations” to
  PostgreSQL-cached “values,” consistent with grid-cell provenance.
- Check: `git diff --check` passed; wording-only, no tests needed.
- Next: Lead continues integration; no remaining developer changes.

## 2026-09-29 | MAP-002 | signed map differences and cached-value wording | done

- Result: popups use the first month baseline, finite containing-cell values,
  estimate provenance, concise formatting and explicit unavailable reasons;
  single maps have no comparison section. Fixed rounded-negative-zero sign and
  deleted-panel handling; added coarse-grid/non-trend caveat to README/References.
- Check: `node --check static/map_selection.js`, focused
  `node --test tests/test_map_selection.mjs` (1 pass), and scoped diff check pass.
  Browser unavailable; QA owns the final batch.
- Next: hand off to Lead/QA; no open developer findings.

## 2026-09-29 | PROVIDER-003 | activate saved NOAA public reads | done

- Result: selected `noaa_core` for startup public reads; source writers remain pinned to CMIP6. Updated provider-aware admin copy, current README claims, and current PostgreSQL/evaluation status with restart and selector rollback. Historical evaluation decision is explicitly superseded; existing NOAA citations remain.
- Check: AST parse, selector/source identity assertions, Jinja compilation for admin and References templates, and `git diff --check` passed. No database, provider, browser, or test-suite access; QA owns regressions, and the browser inventory was empty.
- Next: hand off to QA; no production blockers found.

## 2026-09-29 | PROVIDER-002 review follow-up | grid-rounding wording | done

- Result: clarified that NOAA latitude and circular longitude round separately; the chosen fixed grid coordinate need not minimize great-circle distance. Sampling behavior is unchanged.
- Check: template parse, (89°, 2°) independent-rounding smoke, and `git diff --check` passed. Focused NOAA/content suite ran 15 tests with one expected failure: QA's new copy assertion still requires the removed “nearest” phrase. No browser or live data operation.
- Next: QA owns the assertion update in `tests/test_noaa_location_readiness.py`; Reviewer can verify wording.

## 2026-09-29 | PROVIDER-002 | NOAA location sampling and public copy | done

- Result: added pure finite-coordinate NOAA 2° × 4° sampling with deterministic circular ties, dateline and pole rules, and great-circle distance. Locations uses one fixed cache-only sample; request/sample/provider identify chart renders, whose initial and dropdown titles name the source. Home, Maps, Locations and References respond to the active provider while retaining credits and historical CMIP6 caveat. No activation or data write.
- Check: 40 focused Python tests passed; simulated NOAA coordinate, route and chart-title smokes passed; `git diff --check` passed. No live database/provider or browser check.
- Next: QA adds fake-provider boundary regressions, then Reviewer inspects.

## 2026-09-29 | PROVIDER-001 | immutable acquisition source | done

- Result: Open-Meteo writes and source checkpoints use fixed `open_meteo_cmip6`; SQLite migration and prefetch do likewise. Comparison loads explicit NOAA and CMIP6. Public history/map reads retain the active selector; opt-in Open-Meteo fallback returns cached gaps under another selector. No provider activation or live data operation.
- Check: focused offline weather, map/route, prefetch and comparison suites passed (62 tests, 4 database skips); mocked NOAA fallback smoke passed; `git diff --check` passed. No live database or provider request.
- Next: QA adds fake-database regressions for NOAA-selector writes, checkpoints, migration, comparison and public reads, then Reviewer inspects.

## 2026-09-28 | PAGES-001 | Home and References clarity | done

- Result: refreshed the public entry points, coverage/units/provider guidance, and linked comparison instructions. References now separates active CMIP6 from inactive NOAA and folds old import checkpoints into a dated disclosure. All existing external citation URLs remain.
- Check: offline Jinja render for both pages, citation URL set diff, and `git diff --check` passed. No live database, provider request, or browser check.
- Next: QA runs route regressions and browser review; Lead integrates.

## 2026-09-28 | MAP-001 review follow-up | Maps guidance | done

- Result: changed the readout guidance to say each month has its own value and data source, including labelled display estimates; no behavior changed.
- Check: Jinja template parse and `git diff --check` passed.
- Next: QA/Reviewer continue MAP-001 verification.

## 2026-09-28 | MAP-001 | linked map location readouts | done

- Result: added a dependency-free selection controller for each panel's accepted GeoJSON, safe popup text, per-month value/source and missing/loading/error states. Map clicks include gaps; viewport moves invalidate stale readouts immediately; stale responses cannot restore them. Template gives user guidance. No data API or scale change.
- Check: Node syntax and focused two-panel fake-popup smoke passed (zero, negative, loading, missing, close). Existing Node scale test, Jinja parse, and `git diff --check` passed. Browser and live data checks were not run.
- Next: QA add regression tests for controller and template lifecycle, then Reviewer inspect.

## 2026-09-27 | REVIEW-003 | database backup delimiters | done

- Result: recognized database extensions now match at filename end or before
  any non-ASCII-alphanumeric delimiter, including underscore and whitespace;
  `dbpedia.js` and `thing.dbpedia.js` remain allowed.
- Check: temporary fake-file requests passed for underscore, whitespace,
  punctuation, tilde, and sidecar backups plus allowed assets. Admin-role (16)
  and project-layout (3) suites passed; `git diff --check` is clean.
- Next: QA verify and add regressions; Lead integrate.

## 2026-09-27 | REVIEW-002 | database backup names | done

- Result: static guard now rejects recognized `.db`, `.sqlite`, and `.sqlite3`
  filename extensions followed by end, dot, hyphen, or tilde, case-insensitively.
  It conservatively blocks `library.db.js` while allowing `dbpedia.js`.
- Check: temporary fake-file requests passed for backup/sidecar suffixes and
  allowed ordinary assets; admin-role (16) and project-layout (3) suites passed.
  No real account DB was opened.
- Next: QA verify and add regression tests; Lead integrate.

## 2026-09-27 | BACKEND-002 | private account storage / static guard | done

- Result: shared resolver preserves explicit/env paths, warns while selecting
  existing `static/users.db`, and defaults to `instance/users.db`; static
  requests reject DB files/sidecars, configured account files and metadata
  identity aliases, hidden paths, and unsafe symlinks. Setup closes SQLite.
- Check: focused admin-role (16) and project-layout (3) tests passed. Temporary
  fake-data checks passed for resolver precedence, setup, and static denial
  while serving CSS, plus hard-link and symlink-loop checks. Local import
  reports the expected legacy-path warning;
  no real account DB was opened. No live data or provider calls.
- Next: QA verify/add lasting tests; Lead finish docs and integration.

## 2026-09-27 | BACKEND-001 | package imports / entry points / resources | done

- Result: reviewed checkpoint `9836be2`; no confirmed restructuring regressions
  and no production edits. Internal imports resolve; data/provider/service
  modules do not import web or CLI layers. Named role skills were unavailable.
- Check: `DATABASE_URL= PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest
  discover -s tests -p test_project_layout.py -v` passed all 3 tests;
  `bash -n run.sh` and `run.sh --help` from outside the repo passed.
- Next: Lead/QA should triage account initialization's unclosed SQLite
  connection in `climate/cli/setup_user_database.py`. Reproduced one
  `ResourceWarning`; the same connection-lifetime pattern exists at `cbeda44`,
  so it predates restructuring. No live database or provider calls.
