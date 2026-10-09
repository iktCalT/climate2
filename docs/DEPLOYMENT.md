# Portable production operation

The same source runs locally with `./run.sh`. Production uses Gunicorn and an
existing dedicated persistent directory outside the source tree. No host has
been selected. The container image is optional; native Python can launch
`gunicorn --config gunicorn.conf.py app:app` after installing
`requirements-prod.txt`.

## Required environment

Set these as host secrets/settings, never in the repository:

- `CLIMATE_ENV=production` enables fail-closed production configuration.
- `CLIMATE_STATE_ROOT` is the absolute path to an existing private, writable,
  persistent app disk mount. Prepare it as mode 0700 and owned by the app user
  before startup. The
  app creates `sessions/`, `charts/`, and `images/` beneath it; `users.db` and
  `community.db` live at its top level. Do not mount a public directory.
- `DATABASE_URL` is the private PostgreSQL URL. Create its schema separately;
  startup does not migrate or fetch data.
  Use the selected provider's authenticated, TLS-validated connection settings
  whenever traffic leaves a trusted private network; do not publicly expose a
  self-managed PostgreSQL port as a deployment shortcut.
- `CLIMATE_SECRET_KEY` is an unpredictable secret of at least 32 characters.
  Keep it stable across restarts or signed sessions will be invalidated.
- `CLIMATE_ALLOWED_HOSTS` lists exact DNS names, separated by commas. Wildcards,
  ports and schemes are rejected.
- `PORT`, if set, is a decimal integer from 1 to 65535; default is 8000.
- `LOCATION_FETCH_ENABLED=1` opts production into bounded anonymous NOAA
  Location gap retrieval after explicit weather schema setup. Defaults to `0`
  in production. See [limits and restart behavior](POSTGRESQL.md#location-history-gap-fetching).

`USER_DATABASE_PATH` and `COMMUNITY_DATABASE_PATH` may be omitted in production;
if supplied, they must resolve to the respective files under the state root.
The account setup and administrator CLI resolve the same `users.db` when run
with the production environment. Run account schema setup and administrator
creation only as explicit operator steps. Existing local data is never moved.
Production session cookies are Secure, HttpOnly, SameSite=Lax and signed;
development HTTP cookies and native storage behavior are unchanged. Run one web
instance because SQLite and filesystem sessions are local to this mount.

## Reverse proxy and Cloudflare

By default no forwarded headers are trusted. `CLIMATE_TRUSTED_PROXY_CIDRS`
allowlists the immediate socket peer as comma-separated IPv4/IPv6 CIDRs. Set
`CLIMATE_PROXY_FOR_HOPS`, `CLIMATE_PROXY_PROTO_HOPS`, and
`CLIMATE_PROXY_HOST_HOPS` individually to the exact trusted trailing values
in the corresponding `X-Forwarded-*` lists (zero to eight). At least one hop
and one peer CIDR must be configured together. The upstream proxy must strip
visitor-supplied forwarded headers and append/set its own verified values.
Do not put visitor networks in the peer allowlist. Gunicorn itself trusts no
forwarded peers; Flask validates the final host against `CLIMATE_ALLOWED_HOSTS`.
Verify HTTPS request scheme and actual client IP through the chosen host's
proxy chain before enabling posting.

Restrict direct origin access to the expected proxy where the host supports it.
Use Cloudflare Full (strict) with a valid origin certificate. Do not cache
private pages or `/api/` responses at Cloudflare; application responses carry
no-store headers. `/healthz` is a plain liveness response and performs no
database or provider query. It does not establish storage or data readiness.

## Files, backups, and operations

Only named generated charts under `/static/location_data/` and profile images
under `/static/user_img/` are served from the private root in production. These
two subdirectories contain deliberately public outputs; arbitrary state files
cannot be downloaded through them. The default profile icon stays bundled.
Do not point a separate web server at the private root. The Docker build
context lists each required source, template, SQL and fixed public asset file
by exact name; it excludes uploads, generated charts, databases, sessions,
caches and Git metadata. New runtime files stay excluded until the operator
reviews them and adds an exact entry to `.dockerignore`. Review the effective
context before any image build.

Back up and restore-test PostgreSQL and the private app disk separately. Protect
SQLite consistency during account/community backups. Admin imports currently
run in a web-process daemon thread; a restart can interrupt a month. Committed
months remain resumable, but schedule imports away from deployment and rerun
them deliberately. No image build or hosted startup has been verified because
Docker and a deployment target are unavailable here.

Render and Railway need a persistent app disk/volume at `CLIMATE_STATE_ROOT`
plus private PostgreSQL. A Google Cloud VM can use a persistent disk with
equivalent process, TLS/origin and backup administration. Cloud Run's writable
filesystem is ephemeral, so durable account/community mode is unsupported
there until storage and background jobs are redesigned.
