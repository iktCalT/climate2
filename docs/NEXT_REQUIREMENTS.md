# Next requirements

## Fill missing location history from NOAA

**Status:** Implemented and reviewed 2026-10-09; LOCATION-FETCH-001.
Explicit database setup and application restart are required before local use;
live provider/PostgreSQL and real-browser verification have not been performed.

The Location chart currently leaves decades empty because public reads are
cache-only. After a visitor submits a location, read PostgreSQL first and
progressively retrieve missing completed months for that fixed NOAA sample.
This is an explicit exception to cache-only Locations and edge-window-only
acquisition; Maps and administrator import/cleanup behavior remain unchanged.
Never substitute CMIP6, interpolate across missing years, fetch future/current
incomplete months, or claim unavailable source data is complete.

Use background bounded work, not a decades-long HTTP request. Reuse NOAA's
validated four-field ingestion semantics but persist only the requested sample;
do not import full global months for one visitor. PostgreSQL is the resumable
checkpoint. Serialize against existing import/cleanup work, deduplicate concurrent
requests, limit anonymous starts/download work globally, and allow an operator
to disable automatic fetching. Browser polling/continuation must stop on errors,
throttling or page departure; show saved results and clear progress/retry states.
Completion rereads cached data and refreshes the chart. No profile, consent
cookie, credentials or third-party tracking is required. Write endpoints require
same-origin bounded JSON and validated coordinates, with no user-supplied URLs.

NOAA's historical archive offers global-field byte-range retrieval, not a point
API. Even one sample can require daily records to preserve monthly extrema;
large gaps therefore fill gradually, subject to limits, rather than immediately.
Document enablement/schema setup and this cost honestly. Update README and
References together, reusing existing NOAA/archive/ecCodes citations. Tests use
mock providers and isolated stores only; no live backfill or cloud provisioning.

## Preview an unpublished community pin

**Status:** Implemented and reviewed 2026-10-08; COMMUNITY-003, local map usability.

Placement currently updates only numeric fields, making the intended location
hard to check visually before publishing. Show a distinct, labelled draft marker
at valid selected coordinates on every ready comparison map while placement is
enabled. Both map clicks and typed coordinates update it; blank, non-finite or
out-of-range coordinates remove it rather than implying zero or clipping silently.
Use a visual treatment distinct from public comment markers, with accessible
text identifying the pin as not published, and keep preview markers non-interactive.

Turning placement off or completing publication clears the draft; failed
publication preserves it. Public-pin refresh/panning must not discard the draft,
and newly ready maps gain it while removed maps release their marker. Preview
needs no active profile, storage access or network call; publishing still requires
the existing local profile, explicit public consent and submit action. No server,
data, dependency, clustering or automatic posting changes. Update README and
concise map help; reuse the already credited MapLibre Marker implementation.

## Confirm forgetting a browser-local profile

**Status:** Implemented and reviewed 2026-10-08; COMMUNITY-002, local usability follow-up.

An accidental click on Forget this device currently destroys the local pin
ownership credential. Require explicit confirmation before removing local
storage or deactivating the profile. Explain that public pins remain and this
device will lose its ability to delete them. Cancellation must preserve both
stored and active profile, controls and callbacks; confirmation keeps existing
successful deletion and storage-error behavior. Do not read storage on ordinary
visits, delete public pins, add dependencies or change server authorization.
Use a native confirmation dialog, with focused browser-module regressions.
Keep README/user guidance aligned; References needs no new external citation.

## Google Cloud launch with a portable migration path

**Status:** Paused by owner 2026-10-08; continue local programming instead.
Retain provider-neutral production configuration and local startup. Do not
resume cloud login, provisioning, domain setup or DNS work until requested.
Preflight still needs account/billing verification and a confirmed hostname.

Deploy climate2 on Google Cloud behind Cloudflare for now, retaining local
operation and a practical exit before promotional credit expires. Proposed
starting topology is one modest Compute Engine VM with persistent storage and
self-managed PostgreSQL; verify capacity, billing eligibility and credit expiry
before provisioning. No Cloud Run/storage redesign or paid Cloudflare tier.

Keep application configuration provider-neutral. Prepare private, consistent
PostgreSQL and app-state backups, verify restoration on a replacement host, then
cut over the same hostname with rollback available. Do not copy local accounts,
sessions or personal uploads implicitly; select climate data for initial seeding
explicitly. Keep secrets and populated stores out of Git and deployment images.
Do not destroy the old host until restored data and the new site are verified.

Acceptance: HTTPS through Cloudflare, correct proxy/host handling, usable saved
climate maps, isolated admin access, persistent state across restart, tested
backup/restore and documented migration steps. Confirm the credit end date and
plan migration before it; no promise of automatic future monitoring or migration.
No resources or DNS records have been changed during initial preflight.

## Portable production foundation and numeric-wheel protection

**Status:** Implemented and reviewed 2026-10-04; DEPLOY-004 / UI-002.
Actual container build, hosted startup and browser checks remain open.

Prepare one source tree for local development and Cloudflare in front of Render,
Railway or Google Cloud, without choosing a provider or creating cloud resources.
Preserve native `.venv` / `./run.sh` development. Add production WSGI launch and
optional non-root container packaging with a default-deny build context so no
local secrets, databases, sessions, uploads, Git history or caches enter images.
No live database copying, provisioning, imports, paid actions or DNS changes.

Production must explicitly configure private persistent state, database URL,
secret and allowed hosts; fail closed on invalid configuration. Keep development
defaults compatible. Make account/community/session paths share a documented
private state root in production (CLI account setup must resolve the same path).
Persist optional profile images and permit rebuildable chart output without
exposing the state directory. Preserve existing public URL/behavior contracts.
Provide a lightweight health endpoint without DB/provider calls or secret output.

Trust forwarding headers only when an explicitly allowlisted immediate proxy
and configured hop counts justify them; defaults trust none. Do not blindly use
CF-Connecting-IP or enable unrestricted Gunicorn forwarding. Document origin
access restrictions, Cloudflare Full (strict), no private/API cache overrides,
single-instance SQLite limitations, backup/restore and interrupted import jobs.
Google Cloud VM + persistent disk is a candidate, not a decision. Cloud Run
remains unsupported for durable community/accounts until storage/jobs are adapted;
temporary disk or object-store mounts are not substitutes for safe SQLite storage.
The owner's reported cloud credit is not permission to spend or proof of eligibility.

Across all pages, prevent wheel events from incrementing/decrementing number
inputs, including dynamically added inputs. Preserve typed edits, keyboard arrows,
spinner buttons, form validation and map zoom. Do not globally suppress scrolling
or blur fields while the user is editing. Cancel only wheel default behavior on
the affected numeric control; normal scrolling elsewhere must stay intact.

Validate isolated development/production configuration, hostile forwarding/host
headers, private-path rejection, health checks, image-build exclusions and numeric
wheel behavior. Run one combined offline regression after implementation; no live
PostgreSQL/provider operations. Cite all new resources in README and References.

## Portable local and online deployment

**Status:** Options assessed 2026-10-03; portable production foundation implemented
2026-10-04. Provider selection and hosted verification remain pending.

Compare hosting costs, management burden and climate2-specific changes in
`docs/DEPLOYMENT_OPTIONS.md`. Preserve one codebase and the existing local
`.venv` / `./run.sh` workflow. Online deployment needs a production server,
explicit private persistent storage, environment-based configuration, tested
backup/restore and trusted-proxy handling; do not assume it is ready unchanged.
Do not buy hosting, provision accounts, move live data or enable community
posting during this assessment. Docker packaging is an option, not a new
dependency or requirement for local development. Keep published rates distinct
from workload estimates; retain source links and the date checked.

## Terminal-only administrator provisioning

**Status:** Implemented and reviewed 2026-10-02; DEPLOY-002.

Hosted registration is closed, but a fresh deployment still needs a moderator.
Add `python -m climate.cli.manage_users create-admin USERNAME` for the operator's
terminal only. Never expose a provisioning HTTP route or reopen registration.
Use the existing account-path resolver and password hashing library; require an
already initialized, regular private account database outside static (including
aliases), reject hard-linked store files, and never silently create a database.
Keep existing grant/revoke behavior unchanged. Create an admin and default profile
atomically; duplicate usernames must not overwrite, reset or promote accounts.

Passwords are collected twice with hidden interactive input, never via arguments,
environment or printed output. Reject non-interactive/echo-fallback input,
cancellation, mismatch, invalid Unicode/control characters and weak/oversized
passwords before database writes (15–128 characters; spaces allowed, no trimming).
Username uses existing 3–16 ASCII letter/digit/underscore/hyphen convention.
Hash with the existing Werkzeug helper and store only its result. Sanitize CLI
database errors; never print passwords, hashes or private database paths.
This round implements/tests the command using temporary stores only: no real
account creation, credential handling, deployment, new dependencies or resources.
References and public UI stay unchanged. Verify creation/login compatibility,
atomic rollback, duplicate preservation, path safety, input rejection, closed
registration and existing grant/revoke commands with focused offline tests.

## Low-maintenance public deployment and community pins

**Status:** Implemented and reviewed 2026-10-02. DEPLOY-001 closes registration and opens the
map globally; COMMUNITY-001 publication policy confirmed by the owner below.

Disable hosted self-registration on both frontend and backend. GET /register
explains that registration is temporarily closed because the owner has no time
to manage accounts; POST must fail without creating users or profiles. Keep
existing administrator login/access intact. Initial maps show a flat whole-world
overview rather than the US; manual navigation and synchronized views remain.

Offer an optional browser-local profile only after an explicit user request and
storage consent, with no registration cookie/storage prompt on ordinary visits.
Explain that nickname/preferences stay on that device, are lost when storage is
cleared, and are not a secure or recoverable hosted account. Do not store secrets
or personal account data in Git. Public map pins/comments necessarily need shared
server persistence, distinct from local profile storage, plus explicit notice
that submitted nickname, coordinates and comment will be public.

Initial configurable allowance: at most 10 active pins/comments per local identity;
administrator may lower it (e.g. 3) later without silently deleting existing pins.
Browser identity cannot guarantee a per-person cap: reset identities can bypass
it. Require bounded validated plain-text input, safe text rendering, atomic quota
checks, pagination/viewport bounds, abuse throttling, deletion/moderation controls,
and protection against cross-site writes before public deployment. The owner
confirmed immediate publication with rate limits and administrator removal.
Each pin carries one comment, revealed by clicking it; future clusters reveal
multiple constituent comments. Do not expose a write endpoint until these
protections are implemented.

Implementation contract: private ignored SQLite community store, separate from
climate/account databases, with transactional identity quota and write throttles.
Store only hashes of random browser ownership tokens and keyed IP digests for
short-lived throttling, never raw tokens/IPs in persisted rows or logs. Require
a deployment secret and an explicit enable flag; default disabled until configured.
No trusting forwarded IP headers unless a future deployment explicitly configures
trusted proxies. Default ten active pins per identity, bounded plain-text nickname
and comment, bounded world coordinates and body size. Server stores published
content; localStorage holds an opt-in nickname and random ownership credential.
Forget-device removes local storage, not already public posts; provide own-pin
deletion and explain loss of deletion credentials. Administrator deletion uses
existing authentication plus CSRF. Public reads are viewport-filtered and bounded;
load-more/limit notice prevents silently implying complete pin coverage.
No cookie consent banner for ordinary climate browsing. Handle denied storage
without publishing or silently creating an in-memory alternative identity.
QA requirements: authenticated, CSRF-checked administrator removal must remain
available when public posting rate limits are exhausted (especially shared proxy
addresses). Reject invalid Unicode/surrogate text with a clean validation error
before opening or creating the community database.
Storage validation must use bounded path/identity checks, not recursively scan
the static/chart-cache tree on each request. Reject public-directory aliases,
protected databases and multiply-linked community files; document unsupported
hard-linked store files. Reference-page baseline comparisons are one-time review
evidence, not permanent tests requiring historical Git objects or freezing future
unrelated styles/documentation.

Dense-pin clustering is explicitly deferred; later enable it when density or
rendering cost warrants it, expanding clusters on zoom. No clustering now.
Do not equate automated tests with a production security/deployment approval.

## Concise public frontend

**Status:** Implemented and reviewed 2026-10-02; UI-001, requested presentation simplification.

Home, Maps and Locations repeat guidance and place large explanation blocks
before the primary tools. Shorten copy and spacing, remove duplicate Home
sections, and use native keyboard-accessible details/summary for secondary
instructions. Keep main actions, map scale/legend and concise source, missing
coverage, interpolation and precipitation-unit caveats visible. Retain full
sampling, seasonal and comparison guidance in expandable help. Preserve linked
readouts, coordinate validation/editing, manual shared scales, provider-specific
warnings, saved-month controls, errors and retry controls. No data/route or map
JavaScript behavior changes. Keep environmental awareness and the warning that
two months do not establish a long-term trend.

Design clarification: optional typed map coordinates may sit in a named native
disclosure ("Map controls and coordinate selection"); keyboard access is retained.
The visible primary controls are date selection and the manual scale/legend, not
every optional form. This is intentional progressive disclosure for concision.

References is explicitly excluded: its template and existing CSS rules stay
unchanged. The later registration-closure request permits only its shared
navigation label to change; no References body/layout redesign. Add only
page-scoped styles used by the three edited pages;
no new external resources or dependencies. Account/admin pages remain unchanged.
Validate rendered states for both providers, accessible forms and disclosures,
References isolation, existing offline Python and Node tests. Browser visual
verification only if connected; report that limitation honestly otherwise.

## Edit coordinates while viewing saved location history

**Status:** Implemented and reviewed 2026-10-01; HISTORY-002, keep location exploration editable.

Location results currently hide the coordinate form; changing a location requires
Clear and retyping both values. Keep one labelled native GET coordinate form
visible on entry and result pages, including no-coverage results. Prefill result
fields with the validated requested latitude/longitude, never the NOAA sampled
point, without extra rounding; preserve zero and negative coordinates. Leave
entry fields empty. Place the edit control before the chart/empty-state content
so it is easy to find. Submitting uses the existing /locations route and existing
validation/cache-only reads; no JavaScript required. Clear still opens the blank
entry page and does not load history. Preserve decimal step=any, required flags,
latitude ±90 and longitude ±180 bounds, labels/guidance and unique field IDs.

Keep provider/sampling provenance, coverage counts, seasonal explanation, chart
and empty-state behavior. Use concise context-appropriate submit/heading text;
do not imply that typing inputs changes the displayed result before submitting.
No route, data, chart calculations, dependencies or external resources added.
Document editing in README and References. Validate rendered entry/populated/
empty-result forms, exact requested-versus-sampled values, zero/negative and
decimal preservation, parsed-form resubmission to another location, Clear with
no history read, invalid server input, and both-provider copy with mocked reads.

## Seasonal history coverage in chart readouts

**Status:** Implemented and reviewed 2026-10-01; HISTORY-001, explain incomplete seasonal means.

Location charts show means of available months but do not identify individual
partial seasons. Add a per-metric contributing-month count to each seasonal
point and its hover readout (for example, “2/3 months”). Count the same non-null
monthly values used in the existing mean; keep those means and the existing
December-to-next-year winter assignment unchanged. A group with no values
keeps a missing mean and count zero; missing years remain gaps, not interpolated
values. Explicitly keep Plotly line gap-connection disabled. No imputation,
weighting changes, extra queries, provider access or schema changes.

Readouts include units: °C for temperature and mm/day for mean daily
precipitation. Correct the precipitation axis unit accordingly. Explain on
Locations, README and References the fixed groupings March–May, June–August,
September–November and December–February (winter labelled by January's year),
using Northern Hemisphere season names without implying local seasons everywhere.
Counts express stored-month coverage, not measurement accuracy. Preserve the
four-line metric selector and default mean-temperature view. Bump the chart
render version so unchanged data gets new chart HTML without deleting old files.

Use existing pandas/Plotly only. Cite consulted Plotly hover/customdata docs in
README and References. Validate figure counts, all four metrics, 1/2/3/zero
month groups, winter/year boundaries, unchanged means and NaN gaps, and route
cache-version behavior with mocked reads/writes and focused unittest checks.
No live data or generated chart cache cleanup; browser check only if connected.

## Keyboard-accessible map coordinate selection

**Status:** Implemented and reviewed 2026-10-01; MAP-010, bounded linked-readout usability.

Map readouts currently require a pointer click. Add an explicitly labelled
latitude/longitude form on open Maps pages with native decimal number inputs,
a “Show location on maps” submit button and a “Clear location” button. Latitude
is limited to −85 through 85 (the supported map viewport), longitude to −180
through 180. Explain south/west negative signs and that missing data remains
missing. Reject blank, nonfinite and out-of-range values without changing maps
or selection; retain entered text and give an accessible message. No navigation
or page reload on submission. Do not expose this form in the month selector.

A valid explicit submission centers synchronized maps at the coordinates using
the existing movement/load lifecycle and opens the existing linked readouts.
Keep zoom, bearing, pitch, dates, metric and shared manual scale unchanged.
Selection before map initialization must not construct premature popups or cause
style errors: disable submission until every live panel is initialized, retain
input and recheck readiness at submission. Removed panels must not receive map
operations. Clear closes all readouts without panning or fetching. Existing map
clicks and closing popups retain their current behavior. Form inputs represent
typed coordinates, not an automatically synchronized selected-location state.

Use existing dependencies and sampling logic; no geocoder, new data endpoint,
provider downloads, persistence or new external resources. Update README and
References. Validate actual submit/clear bindings, numeric boundaries and
invalid inputs, readiness/removal, one/four panels, shared selection and
unchanged scale/view properties with focused mocked Node and rendered Flask
tests. No live data operations; disclose unavailable browser verification.

## Retry a failed saved-map request manually

**Status:** Implemented 2026-09-30; MAP-009, bounded map error recovery.

A failed viewport request currently has no direct recovery control. Add a native
per-panel “Retry saved data” button, associated with that panel's status and
month. Show it only for a current non-aborted request failure. One explicit
click retries only that panel's current saved-data viewport request, keeping
months, metric, view, selected location and manual scale unchanged. No provider
downloads, automatic retries, polling or new dependencies/resources. Distinguish
errors from valid empty coverage: empty responses and out-of-world bounds do not
offer retry. Disable repeated clicks while a retry is running; hide/reset the
control on success, viewport invalidation and map removal. Ignore stale and
aborted responses, and never revive a removed/uninitialized panel. Cancel a
pending movement debounce when starting a manual retry to avoid duplicate reads.
Reuse existing loading/readout and generation protections. Document behavior
and cache-only limits in README/References. Test actual failure → click → success,
repeated clicks, repeated failure, empty/bounds results, stale responses, removal,
pending debounce and panel isolation with mocked requests; no live data access.

## Readable map metric labels and sampling context

**Status:** Implemented 2026-09-30; MAP-008, educational map clarity.

Maps exposes internal field keys in headings, accessible map names and the
variable selector. Present “Mean temperature (°C)”, “Maximum temperature (°C)”,
“Minimum temperature (°C)” and “Mean daily precipitation (mm/day)” instead,
using one template-local mapping. Keep option values, API/query keys, selection
order, validation, calculations and scales unchanged. Explicitly explain that
precipitation is a monthly average daily rate, not a monthly total. Match the
existing README distinction: the saved NOAA sampling grid is 2° × 4°, not a
claim of NOAA's native resolution. Update map guidance/status, README and
References; no new data claims, resources, dependencies or fetching. Validate
all four visible labels/ARIA names and unchanged form values/edit round trips,
plus provider-specific sampling guidance and existing Node map checks.

## Retain the comparison when changing selection

**Status:** Implemented 2026-09-30; MAP-007, continuing comparison usability.

“Change selection” currently discards all chosen months and the variable. Carry
the validated ordered months and variable into the selector URL and prefill its
editable fields. Preserve the first month as the baseline, including dates with
no saved coverage; availability suggestions must not replace entered values.
Render prefilled fields server-side so submitting without JavaScript preserves
the comparison. Existing add/remove controls must work with prefilled rows and
the four-month limit. A bare `select=1` still opens an empty selector; explicit
invalid dates, variables, duplicate/excessive months or incomplete selections
remain HTTP 400, even in edit mode. Discovery failures keep the prefilled form
usable and reveal no diagnostics. Ordinary explicit map requests still skip
availability discovery. Do not change scales, data values, provider calls or
stored state. No dependencies or new external resources; document the workflow
in README and References. Validate URL round trips, form order/selection,
failure paths and selector controls with offline Flask/Node checks.

## Separate popup labels and values into readable rows

**Status:** Implemented and reviewed 2026-09-30; MAP-006 follows the user's comparison screenshot.

The readout helper creates bold entries as adjacent inline `strong` elements,
joining the date to “Baseline” and the difference label to its numeric value.
Wrap each line in a block container while retaining nested semantic emphasis and
safe `textContent`. Keep values, units, provenance, differences, history links,
selection lifecycle, scale behavior and network activity unchanged. No new CSS,
dependencies or external resources. Describe the readable layout in README and
References. Add DOM-structure regressions: the existing fake text collector
inserts newlines itself and cannot detect this bug. Run focused Node map tests;
browser if connected, otherwise disclose that limitation.

## Public environmental-awareness purpose

**Status:** Implemented and reviewed 2026-09-30; PAGES-002 follows the user's confirmed purpose
in PROJECT_DIRECTION.

Explain in Home, README and References that climate2 encourages environmental
awareness through accessible exploration, not detailed high-precision reporting.
Keep source names, units, saved-data/missing-coverage caveats and navigation.
Explain coarse NOAA interpolation without implying extra accuracy; make Home's
comparison-readout wording provider-aware. Label the decorative preview as
illustrative, not live data. A two-month comparison is not proof of a long-term
trend. Use concise, welcoming language, without alarmist claims or new scientific
statistics. No fetching, new resources, routes, styling system or behavior change.

Validate rendered Home/References for both providers and preserve existing credit
URLs and actions. Run focused content tests; reuse MAP-005's full regression
evidence because application behavior is unchanged. Browser check if connected.

## Keep manual scales synchronized during source loading

**Status:** Implemented and reviewed 2026-09-30; MAP-005 follow-up to the smooth NOAA display.

The current scale handler saves/renders a new legend but skips updating panels
when `isStyleLoaded()` is false. MapLibre's full-loaded predicate includes source
loading, not just whether the style can be edited, so an initialized panel can
retain old colors indefinitely. A deterministic handler reproduction confirms
zero redraws in this state.

Track panel initialization/removal explicitly. Apply manual scales to initialized
NOAA rasters and legacy CMIP6 layers without waiting for unrelated source loads.
Before initialization, remember the selection for the first render; after removal,
never touch that map. Cleared/error/loading viewport data must not be resurrected.
Keep shared scales manual, data/readouts unchanged, no new requests, timers or
polling loops. Record the behavior and MapLibre loading-semantics source in README
and References. Verify the actual scale handler with mixed panel states and rapid
successive selections, plus existing stale-response tests; browser if connected.

## Smooth estimated NOAA map display

**Status:** Implemented and reviewed 2026-09-30; user explicitly chose smooth interpolation after
reporting blocky maps and darker direct-cache squares.

For active NOAA Maps, replace zoom-subdivided nearest-value polygons with a
bounded raster of bilinearly interpolated numeric values from the saved canonical
2° × 4° nodes. Do not interpolate colors first, download data, store interpolated
rows or claim added resolution/accuracy. Query one source-grid halo around the
viewport in the existing provider-scoped batched read; include a bounded regular
grid (null for missing/nonfinite/noncanonical nodes) as an additive response field.
Require finite surrounding nodes for interpolation: no distant nearest fill,
extrapolation, cross-provider fallback or filling missing months. Exact grid
points/edges may use only nodes with nonzero interpolation weights.

Render at most 512 × 512 pixels with Mercator-correct latitude placement. Use
uniform opaque climate colors, a neutral basemap and borders/labels above the
raster, removing the opacity checkerboard and political-fill color contamination.
Use the existing manually chosen scale, including clipping/custom stops; changing
it redraws locally without fetching. Missing samples remain transparent/unavailable.
No continuous canvas animation. Clear stale raster/readouts on viewport changes,
errors and empty results; preserve request-generation guards and bounded requests.

Show “Smooth display — interpolated estimate” and original source spacing in
status/guidance. Click values and date differences must use the same numeric
interpolator and be labelled interpolated/estimate-based, not direct cache values
or fabricated grid centers. Preserve linked selections/history links. CMIP6's
existing polygon path remains unchanged. Keep legacy GeoJSON fields compatible;
add tests for interpolation, holes, boundaries/dateline, Mercator placement, scale
redraw, async stale results and no-fetch/no-write behavior. Cite MapLibre's Canvas
Source documentation in README and References. Browser check if available;
otherwise verify a generated synthetic raster and explicitly report the UI limit.

## Map-to-history navigation and coordinate form usability

**Status:** Implemented and reviewed 2026-09-29; follow-up to linked map readouts.

Add a normal same-site “View saved location history” link to every selected map
popup, including missing/loading cells. Use the selected coordinates, not a grid
center, with their existing precision. Only offer a URL for finite coordinates
in the Locations domain (latitude −90…90, longitude −180…180); never construct
a link from provider strings or feature metadata. Selection itself must not
fetch or navigate. Explain that history uses its own provider sampling rule and
may differ from a displayed map estimate. Preserve comparison values/differences,
safe DOM text and shared close behavior. No new routes, provider calls or assets.

Improve the existing Locations entry form with explicit input-label IDs,
responsive full width capped at a readable maximum, no fixed decimal input step
(`step="any"`) within unchanged coordinate ranges, and concise negative-coordinate
guidance. Preserve server validation and normal GET behavior; do not add a place
search/geocoder, geolocation permissions or data downloads. Update README and
References descriptions while preserving citations. Batch both edits before
one regression pass; verify safe links/coordinate precision, missing/invalid
selections, one/four panels, and form semantics without live databases.

## Numeric differences in linked map readouts

**Status:** Implemented 2026-09-29 as a comparison-usability follow-up.

For two-to-four maps, use the first selected month as the labelled baseline.
Each other selected-location popup shows its displayed value minus the baseline
value, with an explicit signed difference and the same °C or mm/day unit. This
compares displayed coarse samples, not exact observations or a climate trend.
Only calculate when both containing cells have finite numeric values in accepted
current responses. Baseline loading, errors or missing coverage must instead
show why a difference is unavailable; clear stale differences immediately on
viewport movement. If either input is a display-only estimate, label the
difference as estimate-based. Keep each popup's own source and grid-center detail.

Replace misleading PostgreSQL “observation” labels with cached-value wording.
Single-map readouts remain ordinary values with no baseline/difference section.
Use concise numeric display (up to two decimal places, no negative zero); calculate
differences from unrounded values. Keep safe DOM text, shared-close behavior,
manual scales and existing no-click-network behavior. No provider/backend/data
changes, new dependencies, or assets. Document in README and Maps/References.
Batch these related UI edits before one QA pass; test sign/units, zero, estimates,
missing/nonfinite inputs, asynchronous invalidation and one/four panels.

## Activate saved NOAA public reads

**Status:** Implemented and reviewed 2026-09-29, continuing the selected-provider rollout after
the source-isolation and location-sampling prerequisites (PRs #58–59).

Select `noaa_core` for public Maps, Locations and saved-month discovery on
application startup. Keep acquisition identities fixed and public browsing
cache-only. Preserve stored CMIP6 rows, comparison tooling, missing-data states,
manual shared scales, US map view and existing date ranges. Update current
README/provider/admin descriptions and preserve citations and historical notes.
Activation is a code default requiring an application restart, not a database
migration or a running-server deployment. No fetching, cleanup, schema change,
new dependency or live account access. Rollback is the public selector plus a
restart; it must never relabel or rewrite source data.

Validate default provider propagation, provider-scoped queries, no cross-source
fallback, sampled Locations, page/footer/admin copy and existing offline suites.
Prior dated coverage/physical-range checks are evidence, not proof of scientific
accuracy or a promise of complete history. Browser smoke-check if available.

## NOAA location-grid and presentation readiness

**Status:** Implemented 2026-09-29; follows source-isolation prerequisite.

Prepare, but do not activate, NOAA public reads. For NOAA Location history,
snap validated input to the closest canonical latitude and circular longitude
coordinates on the imported 2° × 4° grid; deterministic ties, equivalent ±180°
and pole handling. Keep one fixed sample for the whole history, never search
farther to fill missing dates or combine providers. Show requested and sampled
coordinates and approximate great-circle distance; identify values as a coarse
grid sample, not exact-location observations. CMIP6 exact-coordinate behavior
and the existing January 1951 history start remain unchanged.

Chart cache identity includes provider and requested/sampled coordinates; chart
title and public Home/Maps/Locations/References copy distinguish NOAA reanalysis
from CMIP6 model output. Preserve source credits and caveats. Public reads remain
cache-only, missing values explicit, manual scales unchanged. Tests simulate both
providers with fake data, including dateline, poles, ties and missing grid samples.
No live writes, imports, dependencies or provider activation in this task.

## Immutable acquisition-source identities

**Status:** Implemented and reviewed 2026-09-29 following NOAA readiness review.

Separate the public-read provider selector from immutable acquisition identities.
Open-Meteo writes, legacy CMIP6 migration, and Open-Meteo prefetch checkpoint/read
logic must always use `open_meteo_cmip6`, even if public reads later select NOAA.
Keep public cache-only reads provider-selected. Disable source-specific fallback
under another public provider, including the
opt-in map and history helpers. The comparison tool must always
compare NOAA against explicit CMIP6, never NOAA against itself. Verify normal
and force-update writes, migrations, prefetch and comparison with fake database
tests under a simulated NOAA public selector. No live data changes, fetching,
activation, new dependencies, or arbitrary-coordinate policy change in this task.

## Home and References clarity refresh

**Status:** Implemented and reviewed 2026-09-28; user-approved.

Refresh existing pages with scannable coverage/provider/limitations guidance,
clear Maps and Locations actions, and concise instructions for linked comparison
readouts and manual scales. Explain Celsius and precipitation in mm/day (not
monthly totals), cache-only public browsing, incomplete coverage and estimates.
Keep current CMIP6 and inactive NOAA roles honest; no provider switch or new
fetching. Move historical import counts out of prominent current-state copy:
they are dated checkpoints, not live coverage. Preserve all existing credits,
links and provenance caveats; no new external assets/dependencies. Use existing
styles with minimal responsive additions, semantic headings and keyboard links.
Verify rendered pages/tests without live databases or provider requests.

## Linked comparison-map location readouts

**Status:** Implemented on 2026-09-28; user-requested. Verified with fake-data
Node controller/async tests and a two-panel built-in-browser check.

Clicking a geographic location on any map selects that same longitude/latitude
in all one-to-four date panels. Each panel shows its own month, value and unit,
and direct/nearby/display-estimate provenance; never copy one month's value to
another. Match the containing rectangular cell in each panel's loaded GeoJSON,
not a nearest unrelated cell or a rendered pixel. Label selected coordinates
separately from the grid-cell center. Missing/loading/failed coverage stays
explicit. Selecting another point replaces all readouts; closing one clears all.

Retain selection during viewport reloads but clear old values immediately when
the viewport changes, and refresh only from accepted current responses. Ignore
stale success/error responses. Single maps continue to work; no extra HTTP
requests, downloads, API/schema changes, dependencies, or automatic scale changes.
Use text-safe popup content and no more than one popup per panel. Document the
interaction in README and the Maps page; retain MapLibre attribution.

## Private account storage and safe static serving

**Status:** Implemented and independently reviewed on 2026-09-27, following
BACKEND-001/QA-001/REVIEW-001 findings. Offline suite: 133 Python tests
(8 database skips) and Node scale check passed; no live data was accessed.

The inherited default `static/users.db` is downloadable through Flask's static
route. A separate inherited setup helper leaves its SQLite connection open.
Use one shared account-path resolver for Flask, initialization, and role tools.
New installations default to ignored `instance/users.db`, outside public assets.
Preserve explicit configuration. Existing legacy accounts must not be silently
replaced: permit a clearly warned transitional legacy fallback while protecting
its download, and document deliberate relocation outside the static directory.

Static serving must deny SQLite/database files and sidecars, hidden files,
configured account storage regardless of filename, and paths/symlinks escaping
the static root. Keep normal CSS/JS/images and generated charts available.
Close setup connections on success and failure. Tests use temporary fake data,
cover unauthenticated denial and legitimate assets, and verify consistent path
selection and connection closure. Do not open, copy, move, or delete real user
databases, fetch climate data, or change dependencies in this task. A separate
web server serving static files needs equivalent restrictions; documentation
must not claim the Flask guard protects that server.

Review follow-up: also deny recognizable database backup names such as
`users.db.bak`, including compound suffixes and sidecar backups. Match database
extensions at filename boundaries (end or any non-ASCII-alphanumeric delimiter,
including underscore, spaces, parentheses, or trailing tilde), without reading
file contents on HTTP requests. Arbitrarily renamed copies cannot be reliably
classified by filename; all backups must remain outside public directories.

## Project layout and agent-ready architecture

**Status:** Implemented on 2026-09-27; recorded before implementation.

The flat repository mixes web code, providers, administrator services, CLI
tools, and SQL. Group Python code by responsibility in a `climate/` package,
put schemas in `sql/`, retain a small root Flask entry point, and document
canonical command-line entry points. Preserve routes, provider selection,
data contracts, local data paths, and existing working changes. Do not add a
framework, dependency, data migration, or feature during this reorganization.
Verify existing behavior before and after moving modules. Provide a concise
architecture guide and bounded Backend, QA, and Reviewer startup assignments.

Implemented on `codex/project-structure` from local main `cbeda44`, preserving
existing artwork and coordination changes. Python modules now live in `web`,
`services`, `providers`, `data`, and `cli` packages; SQL lives in `sql/`.
See [architecture](ARCHITECTURE.md) for migrated commands and compatibility.
Offline verification ran 123 Python tests (8 database tests skipped), the Node
scale check, resource/CLI checks, and HTTP smoke checks. No live data changes.

This document records the next agreed work after the current PostgreSQL and
MapLibre refactor. It supplements `docs/REFACTOR.md`; it does not replace it.

## 1. Correct and improve map tiles

The current MapLibre viewport tiles can render as separated vertical bands
(shown in the attached screenshot). Correct the grid geometry so adjacent
latitude and longitude cells form a tight two-dimensional mesh with no gaps or
overlaps. Do this before adding more map features.

The map must use a **flat** projection, not the current globe/sphere style.

At higher zoom, decrease tile size and request more climate samples for the
visible viewport. Keep the request budget bounded and show loading/missing
areas honestly rather than inventing values. The goal is genuinely more data
points, not merely enlarged tiles.

## 2. Location history

Keep and verify the location page flow: a visitor supplies latitude/longitude,
the app serves temperature history from **1951 through the current month**,
fetching missing Open-Meteo data and saving it in PostgreSQL first.

## 3. Current-month map support

Allow the Maps page to select the newest available month, through the current
month when Open-Meteo provides it. Do not keep the fixed 2023 end date. The UI
and server validation must use the same availability rule.

## 4. User roles and manual ingest

Maintain a user system in which normal visitors can browse climate data without
administrative access. Administrators can manually pre-fetch Open-Meteo data
for a selected area/date range into the local PostgreSQL climate cache. Define
and enforce an administrator role; do not make registration automatically grant
administrator privileges.

## 5. Later page refreshes

Refresh the **Home** and **References** pages after the map, location, current
month, and user-role work is complete. Treat this as a reminder, not current
implementation scope.

## 6. Neighbor-aware map cache reuse

**Status:** Implemented on 2026-08-30; recorded before implementation.

Reduce Open-Meteo usage by allowing a map tile to reuse a sufficiently nearby
PostgreSQL observation. A cached observation does not need to match the tile
center or the map's zooming center exactly.

The acceptable neighbor distance must shrink as zoom increases. Query a small
padded area around the viewport so edge tiles can reuse nearby cached points,
and distinguish reused/estimated values from direct observations in map
metadata. Only call Open-Meteo when no cached observation is close enough for
the current zoom level. Keep the existing bounded request budget.

## 7. Dense viewport grid and city-scale zoom limit

**Status:** Implemented on 2026-08-30; recorded before implementation.

The current safety cap can enlarge map cells until a typical viewport contains
only a few dozen rows and columns. Instead, render at least **90 latitude rows
by 90 longitude columns** for every normal visible viewport so the climate
surface remains visually fine-grained before and after zooming.

Keep PostgreSQL and nearby-cache reuse as the primary data sources. Increasing
the display grid must not cause thousands of Open-Meteo calls: retain the
existing maximum of 12 cache-miss fetches per settled viewport, and use chunked
NumPy nearest-neighbor work so an 8,100-plus-cell response does not allocate an
unbounded distance matrix. Distribute that bounded fetch batch across the
missing viewport cells instead of taking 12 adjacent row-major cells from one
edge, so each provider call improves a different part of the visible map.

Cap both the browser map and API at zoom level 10. This keeps a large-city area,
such as New York City, within roughly two ordinary map screens while still
allowing the adaptive 90-by-90 grid to provide small cells at the closest
supported scale.

## 8. Bounded map resolution and faster foreground fetches

**Status:** Implemented on 2026-08-30; recorded before implementation.

This requirement corrects and supersedes the always-dense 90-by-90 behavior in
requirement 7. Use 2-degree latitude by 4-degree longitude cells at overview
scale. Across the entire globe, that produces 90 latitude rows by 90 longitude
columns, staying within the 91-by-91 ceiling without distorting cell size.

As the user zooms in, use a smooth rectangular-cell resolution curve instead
of preserving 90 rows and columns. Reduce both dimensions by a factor of 1.5
per added zoom level while the geographic viewport shrinks by roughly a factor
of 2, and stop permanently at 0.5-degree latitude by 1-degree longitude cells.
This preserves the 1:2 latitude/longitude grid aspect and makes the number of
visible cells trend downward at every zoom level. Keep the city-scale maximum
zoom of 10.

The measured response delay is dominated by synchronous Open-Meteo cache-miss
work, not PostgreSQL grid generation. Reduce the foreground cache-miss batch
from 12 to at most 4 distributed locations per settled viewport. Continue to
cache every fetched metric in PostgreSQL; larger intentional cache population
belongs in the administrator pre-fetch flow.

## 9. Resumable edge-period PostgreSQL prefetch

**Status:** Implemented on 2026-09-02; recorded before implementation.

Populate the canonical 91-by-91 global map grid for the edge periods
**1950–1953** and **2023–2026** without refetching already complete climate
months. PostgreSQL must be the durable checkpoint: each run determines which
locations and months already contain all four metrics, fetches only missing
contiguous ranges, and commits successful ranges independently so an
interruption does not discard earlier progress.

Provide a command-line prefetch job with a conservative per-run location cap,
stable traversal order, progress reporting, and a dry-run mode. Re-running the
same command must safely resume from PostgreSQL, including after a provider
failure. Keep the canonical 2-degree latitude by 4-degree longitude grid and
the existing Open-Meteo model/metric choices; do not store a separate mutable
checkpoint file or contact Open-Meteo for complete locations.

## 10. Rate-aware prefetch pacing and fail-fast behavior

**Status:** Implemented on 2026-09-02; recorded before implementation.

The first live 100-location prefetch reached Open-Meteo's weighted minutely
limit after roughly 15 successful requests. A location count alone is not an
adequate request budget because the Climate API also weighs the requested time
span, variables, and models.

Pace all provider requests in the command-line prefetch with a conservative
default delay shared across locations and periods. Stop the batch immediately
when any provider request fails instead of rapidly attempting the remaining
locations; already committed ranges remain resumable through PostgreSQL.
Allow an explicit delay override for controlled operation and tests, display
the pacing policy before a live batch, and keep expected provider-limit errors
concise instead of printing full tracebacks.

## 11. Research a higher-capacity monthly climate data provider

**Status:** Initial research completed on 2026-09-23 and updated on 2026-09-24.
The initial ERA5 choice is superseded by the anonymous NOAA CORe selection in
requirement 16; integration remains deferred pending importer validation.

Evaluate alternatives to the current Open-Meteo Climate API before committing
to the remaining global prefetch. The preferred provider must offer a genuinely
free tier with a materially higher usable request or data-volume limit, use
HTTPS, have clear ownership and licensing, publish dependable documentation,
and be suitable for a public student project without unsafe credential or data
handling.

Fine-grained daily or hourly data is not required when monthly values can be
obtained directly. Compare candidates on global coverage, the 1950-to-present
window, mean/minimum/maximum temperature and precipitation availability,
monthly aggregation semantics, spatial resolution, rate limits, attribution,
long-term reliability, and compatibility with the PostgreSQL cache. Do not
replace Open-Meteo until the selected source and any differences in modelled
values have been documented and verified.

The initial evaluation selected Copernicus Climate Data Store ERA5, but it
requires an account, dataset-licence acceptance, and private API token. The
2026-09-24 update instead selected NOAA CORe, an official global reanalysis
available anonymously over HTTPS from 1950 to near real time and documented by
NOAA as public domain. It is still not a drop-in replacement: temperature
extrema must be derived from daily records, units and Gaussian-grid coordinates
must be validated, and reanalysis values must remain separate from the current
two-model CMIP6 average. See [`CLIMATE_PROVIDER_EVALUATION.md`](CLIMATE_PROVIDER_EVALUATION.md)
for the candidate comparison, field definitions, conversions, safeguards, and
staged integration plan. Open-Meteo remains the only active provider.

## 12. User-controlled map color scales

**Status:** Implemented on 2026-09-23; recorded before implementation.

Allow users to choose a color scale independently for temperature and
precipitation maps. Provide several understandable presets, including a broad
global scale and narrower regional scales, and allow a custom scale with
validated value bounds and colors. Use the existing map colors and previously
defined temperature/precipitation stops as the starting reference when
designing the presets rather than inventing unrelated defaults.

Every rendered map must show the active units, numeric range, color stops, and
legend. Temperature and precipitation need metric-appropriate presets and
validation; a precipitation scale must not silently reuse temperature bounds.

The map now provides four temperature presets (global extremes, temperate,
cold, and warm) and three precipitation presets (global daily mean, dry, and
wet). Custom scales accept minimum and maximum values plus low, middle, and
high colors, with separate safe bounds for each measurement family. The active
range, units, and every color stop remain visible above the map.

## 13. Manual-only scale changes

**Status:** Implemented on 2026-09-23; recorded before implementation.

Never rescale colors automatically in response to panning, zooming, changing a
date, or loading new data. Keep the selected scale fixed until the user chooses
another preset or edits the custom scale. Preserve the choice while the user is
working so identical colors retain identical meanings and the map does not
become visually misleading.

Scale selection is stored separately for temperature and precipitation in the
browser. Map movement and data responses never write or recalculate it; only a
preset selection or a successful custom-scale submission changes the active
scale. The saved choice survives date changes and page reloads.

## 14. Same-scale multi-date comparison

**Status:** Implemented on 2026-09-24; recorded before implementation.

Add a comparison mode in which users select two or more months and view the
same temperature or precipitation metric side by side. Comparison panels must
share one user-selected color scale and legend; do not allow individual panels
to auto-scale or use different bounds. Keep viewports synchronized where
practical, label every date clearly, and preserve the existing distinction
between direct, nearby-cache, and pending/missing values so apparent
differences are not created by inconsistent rendering.

Limit one comparison to two through four distinct months. This keeps panels
readable on an ordinary screen and bounds the number of PostgreSQL and
Open-Meteo requests caused by a settled viewport. Each panel may load its own
month, but synchronized viewport movement must not create duplicate requests
for the same panel and position.

The Maps selector now lets users add up to three comparison months to the
primary month. The resulting two-to-four-panel view labels each date, uses one
shared preset or custom scale and legend, and synchronizes center, zoom,
bearing, and pitch from whichever panel the user moves. Every panel retains
its own load status and direct/nearby/estimated rendering, while debounced
per-panel requests prevent synchronized movement from repeatedly loading the
same final viewport.

## 15. Provider-scoped climate rows

**Status:** Implemented on 2026-09-24; recorded before implementation.

Prepare the PostgreSQL climate cache for a future reanalysis bulk-import path
without changing the active website provider. Every stored monthly climate row
must identify its provider and product family so NOAA CORe or another
reanalysis cannot be silently mixed with the existing Open-Meteo CMIP6 model
average.

Existing rows and every current Open-Meteo write must be labelled consistently.
All current website, map, location-history, administrator, migration, and
prefetch reads must explicitly select the active Open-Meteo provider. The
database key must permit two providers to store values for the same location
and month while preventing duplicate rows within one provider. Expose the
selected provider in map response metadata so the UI data contract remains
auditable.

This is schema and provenance groundwork only. Do not contact CDS, request or
store a token, import ERA5 files, replace Open-Meteo, or combine values from
different provider families. Existing installations must be upgraded
idempotently by the normal schema setup command, and fresh installations must
receive the same constraints and defaults.

The `data` table now uses `(loc_id, dates, provider)` as its primary key, with
legacy and current writes labelled `open_meteo_cmip6`. Location history, maps,
administrator ingestion, legacy migration, and resumable prefetch queries all
select that active family explicitly. Map JSON and the visible panel status
report the provider, while a database integration test verifies that a second
provider can coexist without affecting active-site results. The schema upgrade
was run twice successfully to verify repeatability; no CDS request, token, or
ERA5 value was introduced.

## 16. Anonymous NOAA CORe bulk source

**Status:** Implemented and live-validated on 2026-09-24. Open-Meteo remains
the active website provider pending a separate comparison and activation
decision.

Replace the deferred, account-gated ERA5 bulk-source plan with NOAA's
Conventional Observation Reanalysis (CORe) archive on the NOAA Open Data
Dissemination Program. The selected source must require no user account, API
key, private token, or click-through dataset-licence acceptance. Use only the
official NOAA HTTPS archive and document the dataset's public-domain status,
operational limitations, attribution, and retrieval behavior in both the
README and website References page.

CORe is suitable because its global reanalysis spans 1950 to near real time,
offers monthly and daily ensemble-mean products, and can be retrieved as
individual indexed GRIB records rather than thousands of point API calls. The
application does not need CORe's full native spatial precision: an importer
must explicitly map its Gaussian grid onto the existing canonical 2-degree by
4-degree points, validate longitude and pole handling, and avoid presenting
the downsampled result as station observations.

Preserve the existing four-metric monthly contract. Use monthly 2 m
temperature and surface precipitation-rate records for `temp_mean` and
`precip`. CORe's monthly high/low records are averages of daily extrema, not
the application's monthly highest and lowest daily values, so derive
`temp_max` and `temp_min` from the daily CORe extrema records before writing a
month. Convert and validate units explicitly, store rows under a new
`noaa_core` provider family, and never mix them with `open_meteo_cmip6` rows.

PostgreSQL remains the resumable checkpoint. Import bounded date chunks, use
NOAA index byte ranges to avoid downloading unrelated fields, commit only
validated complete months, and make reruns skip existing complete
provider-scoped rows. Do not activate CORe for foreground cache misses or site
reads until a separately reviewed sample confirms field selection, units,
coordinates, missing-value handling, and representative land, ocean, polar,
and dateline results.

The command-line importer now retrieves indexed byte ranges with bounded
retries, decodes GRIB2 with ECMWF ecCodes, validates metadata and values,
nearest-samples to all 8,281 canonical points, and atomically upserts one month
under `noaa_core`. Complete calendar months are selected in stable order, one
per run by default and at most 12; `--dry-run` never contacts NOAA and
`--validate-only` never writes PostgreSQL. Live validation succeeded for
January 1950 and August 2026. A January 1950 write followed by an immediate
dry run confirmed that PostgreSQL recognizes and skips the complete month.
Website reads remain explicitly scoped to `open_meteo_cmip6`.

## 17. Read-only provider comparison report

**Status:** Implemented on 2026-09-24; representative review completed on
2026-09-25. Activation is deliberately deferred.

Add a deterministic command-line report that compares provider-scoped NOAA
CORe and active Open-Meteo rows already present in PostgreSQL. The report must
not contact either provider, mutate the database, infer approval from a numeric
threshold, or change the website's active provider. It is evidence for a
separate human activation decision, not an automatic migration.

For each explicitly requested complete month, report each provider's canonical
grid coverage, the count of coordinate/month pairs available from both, and
signed and absolute differences for all four monthly metrics. Include
representative canonical land, ocean, polar, and both sides of the dateline so
coordinate handling and missing samples remain visible. A missing provider,
month, metric, or representative row must appear as incomplete evidence rather
than being silently omitted.

Keep the comparison bounded to at most 12 months per run, use stable ordering
and machine-testable pure formatting/statistics helpers, and print Markdown to
standard output so a reviewer can save a report deliberately without adding
generated database contents to Git. The report must explain that CORe
reanalysis and the Open-Meteo two-model CMIP6 average are different products;
differences are expected and do not by themselves prove that either source is
incorrect. CORe activation still requires a separately recorded review and an
explicit provider switch.

The `compare_climate_providers.py` command now opens a read-only PostgreSQL
transaction, filters out non-canonical user locations, and prints deterministic
Markdown for up to 12 complete months. Coverage, per-metric signed and absolute
deltas, missing evidence, and land, ocean, polar, and dateline samples are all
visible. Live reports compared all 8,281 canonical rows for January 1950,
leap-month February 1952, and July 2023. August 2026 compared all six required
land, ocean, polar, and dateline samples without attempting an Open-Meteo
global refill.

The review confirms that retrieval, units, dates, cyclic coordinates, poles,
and representative values are coherent, but it does not justify an immediate
provider switch. CORe reanalysis and the active two-model CMIP6 average show
material expected differences, especially for precipitation and temperature
extrema. The resumable local import subsequently completed all 92 requested
months across 1950–1953 and 2023–2026, but coverage alone does not make these
different products interchangeable. Keep `open_meteo_cmip6` active and keep
the provider families separate until a new requirement explicitly decides how
foreground cache misses and provider activation should work.

## 18. Exact NOAA daily-extrema archive-gap fallback

**Status:** Implemented and live-validated on 2026-09-25 after the official
May 19, 2026 daily flux index was found to omit both 2 m temperature extrema.

Keep the NOAA CORe importer resumable when a daily aggregate file omits both
required temperature-extrema records but the official 3-hourly archive still
contains the corresponding 0–3 hour minimum and maximum fields. In that narrow
case, retrieve all eight official 3-hourly flux files for the affected UTC day,
decode their exact interval extrema with the same metadata and grid validation,
and reduce those fields to the daily minimum and maximum before continuing the
existing monthly aggregation. This is an archive-gap recovery path, not an
instantaneous-temperature approximation.

Use the fallback only when the daily index contains neither required extrema.
If only one daily field is missing, any 3-hourly file or extrema record is
missing, metadata or coordinates disagree, or a download fails, reject the
month and leave PostgreSQL unchanged. Do not skip the day, interpolate it, or
silently substitute the daily mean. Log the affected date so operators can
distinguish a verified archive gap from an ordinary failure. Cover both the
successful exact fallback and incomplete-fallback rejection with tests, then
live-validate May 2026 before resuming the bounded edge-period import.

The importer now checks the failed daily index and enters the fallback only
when both required records have a match count of zero. It downloads the exact
minimum and maximum interval records from all eight official 3-hourly files,
applies the existing date, statistic, unit, grid, coordinate, and missing-value
validation, and reduces them to one daily pair. Tests verify the complete path
and fail-closed behavior when an interval is unavailable. May 2026 passed a
live no-write validation through this path and was then committed atomically;
June and July followed normally. A final dry run reported all 92 requested
edge-period months complete.

## 19. Explicit NOAA full-history backfill

**Status:** Implemented on 2026-09-25 after the two recorded edge periods
reached 92 of 92 complete months.

Add an explicit importer period for every complete calendar month from January
1950 through the latest complete month. This is the next prerequisite for any
future NOAA activation because edge-period coverage alone cannot serve the
website's advertised middle decades, and filling missing months synchronously
during a visitor request would be too slow. The full-history selection must be
opt-in: keep the existing two edge periods as the default so an ordinary
rerun does not unexpectedly expand into a multi-year archive job.

Reuse the existing bounded batch limit, stable chronological ordering,
provider-scoped PostgreSQL completion checkpoint, month-atomic commits,
metadata validation, and exact daily-extrema fallback. The moving end of the
period must always be the latest complete month, with `--through` still able to
set an earlier stopping point. A dry run must report progress without
contacting NOAA or changing PostgreSQL. Document the command and the remaining
activation boundary in the README, provider evaluation, and website References
page. Do not switch active site reads or mix provider families as part of this
backfill capability.

The importer now accepts `--period 1950-present` and selects January 1950
through the latest complete month, or an earlier `--through` bound. It retains
the existing one-month default and 12-month maximum batch, while an invocation
without `--period` still selects only the two edge periods. Unit tests cover
the dynamic end, explicit opt-in, and earlier bound. README, provider review,
home-page status, and References copy describe the full-history prerequisite;
active reads remain `open_meteo_cmip6`. A live dry run reported 92 of 920
months complete and selected January–December 1954 as the first bounded batch.
All 12 months validated and committed atomically; the follow-up checkpoint is
104 of 920 complete months. A second bounded live run validated and atomically
committed January–December 1955. The checkpoint is now 116 of 920 complete
months. A third bounded live run validated and atomically committed
January–December 1956. The checkpoint is now 128 of 920 complete months. A
fourth bounded live run validated and atomically committed January–December
1957. The checkpoint is now 140 of 920 complete months. A fifth bounded live
run validated and atomically committed January–December 1958. The checkpoint
is now 152 of 920 complete months. A sixth bounded live run validated and
atomically committed January–December 1959. The checkpoint is now 164 of 920
complete months. A seventh bounded live run validated and atomically committed
January–December 1960. The checkpoint is now 176 of 920 complete months, and
the next resumable batch is January–December 1961. An eighth bounded live run
validated and atomically committed January–December 1961. The checkpoint is
now 188 of 920 complete months. On 2026-09-26, a ninth bounded live run
validated and atomically committed January–December 1962. A follow-up dry run
confirmed 200 of 920 complete months and selected January–December 1963 as
the next resumable batch. A tenth bounded live run on 2026-09-26 validated
and atomically committed January–December 1963. A follow-up dry run confirmed
212 of 920 complete months and selected January–December 1964 as the next
resumable batch. An eleventh bounded live run on 2026-09-26 validated and
atomically committed January–December 1964. A follow-up dry run confirmed
224 of 920 complete months and selected January–December 1965 as the next
resumable batch. A twelfth bounded live run on 2026-09-26 validated and
atomically committed January–December 1965. A follow-up dry run confirmed
236 of 920 complete months and selected January–December 1966 as the next
resumable batch. A thirteenth bounded live run on 2026-09-26 validated and
atomically committed January–December 1966. A follow-up dry run confirmed
248 of 920 complete months and selected January–December 1967 as the next
resumable batch.

## 20. United States default map view and provider-accurate footer

**Status:** Implemented on 2026-09-25. NOAA remains inactive, so the current
footer still truthfully displays Open-Meteo and CMIP6.

Open the interactive map over the contiguous United States instead of the
current whole-world, zero-longitude view. Use one stable initial center and
zoom for every map and comparison panel, while preserving the existing shared
viewport synchronization, manual color scale, city-scale maximum zoom, and
user-controlled pan and zoom behavior.

Keep the footer attribution truthful to the provider used for live website
reads. It must continue to identify Open-Meteo and CMIP6 while
`open_meteo_cmip6` is active, but it must change to NOAA CORe when a separately
recorded activation change switches the active provider to `noaa_core`. Reuse
the NOAA source already cited in the README and References page; do not claim
that NOAA powers the website before that provider switch is complete.

All map and comparison panels now start at longitude -98.5, latitude 39.5,
and zoom 3.25, framing the contiguous United States while retaining full
pan/zoom freedom. Flask injects the active provider into the shared layout;
the footer renders the existing NOAA CORe source link when that value is
`noaa_core` and otherwise keeps the current Open-Meteo and CMIP6 attribution.
Tests cover both the U.S. viewport constants and the conditional NOAA footer.

## 21. Newest-first NOAA backfill for 2016–2026

**Status:** Implemented on 2026-09-26 at the owner's request; reverse backfill
is in progress.

Prioritize recent history instead of continuing the oldest-first middle-decade
backfill. Add an explicit `2016-2026` period and opt-in `--newest-first` order
so pending months run from the latest complete month of 2026 backward through
January 2016. Skip already-complete PostgreSQL months before applying the batch
limit. Keep chronological order and the two edge periods as the defaults,
deduplicate overlapping selections, honor `--through`, and exclude incomplete
or future months. Retain the one-month default, 12-month maximum, month-atomic
writes, fail-fast validation, no-write dry runs, and unchanged active provider.

The existing 2023–2026 checkpoint is already complete through August 2026, so
the first missing reverse batch is expected to be December–January 2022.
Record verified progress in the README and website; do not claim that the
entire 2016–2026 range is complete until PostgreSQL confirms it. Reuse the
existing NOAA citations and never publish database contents or credentials.

The importer now supports the explicit period and ordering flag. Tests cover
complete-month and period bounds, deduplication, the unchanged default order,
skipping completed months before the limit, resume order, and a no-write CLI
dry run. A live dry run confirmed 44 of 128 requested months complete and
selected December–January 2022 as the first reverse batch.

All 12 months of that batch validated and committed atomically in descending
order. Follow-up dry runs confirmed 56 of 128 complete months in the requested
2016–2026 window and 260 of 920 complete months overall. At that checkpoint,
the next prioritized batch was December–January 2021. On 2026-09-26, a second
reverse batch validated and atomically committed all 12 months of 2021 in
descending order. Follow-up dry runs confirmed 68 of 128 recent-window months
and 272 of 920 full-history months complete. On 2026-09-26, a third reverse
batch validated and atomically committed December–January 2020, including
leap-month February. Follow-up dry runs confirmed 80 of 128 recent-window
months and 284 of 920 full-history months complete. December–January 2019 is
next; 2016–2019 remains pending. The original oldest-first selection still
begins at January 1967 when explicitly used.

## 22. Administrator-owned edge-window fetching and finer temperature scales

**Status:** Implemented on 2026-09-26 at the owner's request. Supersedes the
full-history and 2016–2026 backfill priorities above; preserve all saved rows.

Stop spending development turns on manual year-by-year imports. Limit the
current acquisition scope to the first and last five calendar years of the
1950–2026 project: 1950–1954 and 2022–2026, through the latest complete month.
Expose the existing NOAA fetching/validation functions through a reusable
bounded service and an administrator-only frontend. An explicit click starts
1–12 missing months in a background batch, not a long blocking HTTP request.
Use a PostgreSQL advisory lock to reject overlapping administrator batches,
persist safe job status, show coverage and progress, and allow a restart to
resume from committed months after a failure or server restart. Require a
session-bound CSRF token and check current administrator rights on every
start/status request. Do not expose provider credentials or raw exceptions.
Do not launch any real downloads merely to test the interface.

Add manual 2°C-detail temperature presets over narrow 20°C ranges, retain
existing presets/custom bounds and saved selections, and keep one shared
scale across comparison maps. Explain clipping and that narrower colors do
not increase measurement accuracy or repair the inherited suspicious ocean
cache. Keep the active provider unchanged pending a separate validated switch;
full-history completion is no longer an acquisition prerequisite. Shorten
public-facing operational history into a clear data-status/limitations note.
Keep broader saved history available; do not delete data or silently change
date availability. Cite reused NOAA/software resources in README and References.

Implemented `/admin/data` and its role-checked, CSRF-protected start/status API,
reusing the NOAA monthly importer behind a PostgreSQL-locked background batch.
The additive job-status table records safe progress; an unlocked stale running
job is reported as interrupted and can resume manually. Existing CLI tools are
retained, but must not run concurrently with the admin worker. Browser checks
used an isolated account and disabled map fetching. Live read-only coverage
checks confirmed 60/60 months for 1950–1954 and 56/56 for 2022–August 2026;
neither window needed downloads. Tests cover lock conflicts, bounded selection,
failure/resume status, authorization, CSRF, and saved manual scale persistence.
Three narrow temperature presets now offer 2°C stops; comparisons still share
one manually selected scale. Homepage and map copy explain the changed scope
and the unresolved inherited ocean-cache limitation.

## 23. Explicit administrator cleanup outside the two five-year windows

Status: Implemented.

Problem: accumulated climate cache history increases storage and maintenance
work. The owner wants a small working dataset and responsive queries.
Keep all providers' rows dated 1950–1954 or 2022–2026; offer an administrator
preview of retained/removable counts by provider, followed by an explicitly
confirmed cleanup of at most 50,000 climate rows per request. Repeating a batch
resumes safely. Do not delete accounts, profiles, location definitions, files,
or rows in the retained windows. No automatic cleanup or live-data deletion
during implementation. A backup is required for exact recovery; re-fetching
may yield revised source values. Share the admin-import lock, enforce admin
authorization and CSRF, use transaction/lock timeouts, and roll back failures.
Document that this is manual cache pruning, not a retention firewall: visiting
other dates or running import tools can refill removed rows. Smaller storage
alone does not guarantee faster indexed queries or immediately shrink database
files; PostgreSQL vacuum maintenance and query measurements remain relevant.
Use existing dependencies and cite PostgreSQL cleanup/maintenance documentation
in README and References. Do not run disruptive VACUUM FULL from the website.

Implemented `admin_cleanup.py`, a role-checked/CSRF-protected preview and delete
API, and a clearly separated cleanup section on Admin → Data. Preview grants
a session-bound, ten-minute confirmation token that is consumed on submission;
each request deletes at most 50,000 rows. Both providers and date boundaries
were tested using PostgreSQL temporary tables, including repeated batches,
rollback and conflicts with the import lock. Browser verification used a
disposable account with deletion disabled and verified live read-only counts
and disabled deletion before confirmation. No application data was removed.

## 24. Cache-only public browsing without hidden provider waits

Status: Implemented.

Problem: map requests still fetch missing cells synchronously, and location
requests can download decades of missing history. This delays visitors and can
silently refill data removed by cleanup. Following the owner's move to
administrator-controlled acquisition, make public Maps and Locations read only
the existing active-provider PostgreSQL cache. Keep administrator and CLI
fetching available and keep provider identity and manual comparison scales
unchanged. Do not restrict access to already saved historical dates or switch
to NOAA as part of this change. Missing data must remain visibly unavailable,
not queued for an automatic fetch; spatial display estimates remain labelled.

Locations should show missing-month coverage and an empty-state message rather
than fetching or displaying an old cached chart. Key rendered chart files to
their current data content so an import or cleanup cannot leave a stale chart
on the next page request. Do not remove old files or climate rows. Seasonal
means still use available months; explicitly disclose incomplete seasons.
Update README and website descriptions/citations and test that public requests
never invoke acquisition, including empty caches and caller-supplied fetch flags.
This removes provider-network waits, not a promise of constant query latency.

Public routes now enforce cache-only reads regardless of caller fetch flags.
The reusable history helper retains explicit acquisition support for non-public
tools. Location pages report any-value/all-field monthly coverage, never render
a stale chart for empty data, and use SHA-256 content-keyed render names. Updated
map status replaces misleading pending-download wording. The active provider,
US initial view, and shared manual scales are unchanged. Full regression tests
ran in a disposable PostgreSQL schema, not the application tables. Read-only
local map/populated-location/empty-location requests took roughly 13–89 ms in
one smoke check with acquisition blocked; this is not a general benchmark.
No application climate rows were deleted or downloaded during this change.

## 25. Discover saved months before opening a map

Status: Implemented.

Problem: cache-only browsing still opens the current calendar month even when
it has no stored active-provider values, and users cannot see which dates are
available. On an unqualified Maps visit, choose the newest saved mean-temperature
month no later than the existing stable-month bound. Never replace an explicitly
requested date or comparison. If nothing is saved or availability cannot be
checked, show the selector with a clear explanation, not a misleading map.

Add a saved-month picker with per-variable finite-value point counts and actions
to use a month or add it to comparison. Counts are global availability, not a
claim of full coverage in the US or any viewport. Preserve manual date input,
up-to-four distinct comparisons, saved manual color scales, and provider isolation.
Read PostgreSQL only, bound the query time, and make no downloads or deletions.
Use existing dependencies; document the new default and attribution in README
and the website. Keep docs/REFACTOR.md unchanged.

Implemented a provider-scoped, read-only availability query with three-second
statement and 500 ms lock timeouts. Default Maps visits choose the newest saved
mean-temperature month within the stable-date limit; explicit requests bypass
discovery. Selector controls use metric-specific counts, prevent duplicate
saved-date additions, and preserve entered dates when the variable changes.
Tests cover empty/error states, explicit-date preservation, stable-date bounds,
inactive providers, null/nonfinite values, date bounds, and monthly-date rules.
Browser checks verified saved-date assignment, adding a comparison, duplicate
protection, changing to precipitation without changing dates, and opening the
requested two-date comparison. No data was downloaded or deleted.

## 26. Original, publication-safe error artwork

**Status:** Planned on 2026-09-24; recorded before implementation.

Replace the remote Memegen/Grumpy Cat error image because the inherited
background's original-image licence is not established. Error pages must use a
project-local, original climate-themed illustration and render the server's
existing error message and status code as accessible HTML rather than baking
changing text into the image.

The replacement must remove the runtime dependency on Memegen, Imgur, and the
Grumpy Cat cultural reference. It must remain readable on narrow screens, have
meaningful alternative text, and require no visitor data or error text to be
sent to a third-party image service. Credit the image-generation tool in both
the README and website References page, following the repository's attribution
policy, while clearly describing the resulting artwork as project-specific.

## Delivery order

1. Tile-grid geometry and flat map.
2. Finer zoom sampling and location-history verification.
3. Newest-month support.
4. User roles and administrator ingest.
5. Home and References redesign.
6. Neighbor-aware cache reuse before further map API expansion.
7. Dense 90-by-90 viewport grid with a city-scale zoom limit.
8. Bounded 2°×4° to 0.5°×1° map resolution and faster foreground fetches.
9. Resumable PostgreSQL prefetch for the 1950–1953 and 2023–2026 edge periods.
10. Rate-aware pacing and fail-fast handling for the resumable prefetch.
11. Research and select a safe, free, higher-capacity monthly climate provider.
12. Add temperature and precipitation scale presets plus validated custom scales.
13. Keep color-scale changes entirely manual and stable across map interactions.
14. Add synchronized, same-scale side-by-side comparison for two or more dates.
15. Scope every climate cache row and read to an explicit provider before reanalysis integration.
16. Add and validate a resumable NOAA CORe bulk importer without changing the active provider.
17. Generate a bounded, read-only CORe-versus-Open-Meteo comparison report before any activation decision.
18. Recover verified daily-extrema archive gaps from exact official 3-hourly extrema without approximation.
19. Add an explicit, bounded, resumable NOAA backfill for January 1950 through the latest complete month.
20. Open maps over the contiguous United States and make footer attribution follow the active provider.
21. Prioritize NOAA backfill newest-first from 2026 through 2016, skipping complete months.
22. Replace manual backfill work with administrator-owned five-year edge-window batches and improve manual temperature-scale detail and website clarity.
23. Add previewable, explicitly confirmed administrator cleanup outside the retained five-year windows.
24. Remove hidden climate-provider downloads from public browsing and make missing/stale-data states explicit.
25. Add saved-month discovery and open a useful cached month by default without overriding explicit choices.
26. Replace the inherited error image with original, locally served artwork.
