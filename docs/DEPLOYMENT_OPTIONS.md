# Deployment options for climate2

Checked 2026-10-03. Assessment only: no provider selected or deployed.
The portable production foundation is documented in the
[deployment runbook](DEPLOYMENT.md); no provider has been provisioned.
Prices are USD/month before tax, domain registration and extra usage. Cost
examples are not workload measurements or maximum bills. Database size, traffic,
peak memory and import cost have not been measured in this assessment.

## Recommendation

Prefer **Render + managed PostgreSQL + a private app disk** for less management.
Choose **Railway** for flexible usage billing if you accept database upkeep.
Choose a **DigitalOcean VPS** if someone can maintain the server. All three can
retain local operation and the current Flask architecture. None removes comment
moderation duties.

Cloudflare can sit in front of any candidate with Full (strict) TLS and an
origin restricted to the expected proxy path. A Google Cloud VM with a
persistent disk is another self-managed option, requiring the same operating
work as a VPS; no price estimate or provider decision is recorded for it here.
Cloud Run's ephemeral writable filesystem cannot host the current durable
SQLite/session mode safely without a storage and jobs redesign.

## Render: least administration of these choices

- **Published rates:** app compute starts at $7/month (512 MB); a 2 GB app is
  $25. PostgreSQL compute starts at $6. App disks cost $0.25/GB/month; database
  storage is listed at $0.30/GB. [Official pricing](https://render.com/pricing).
- **Example budget:** roughly $15/month at the smallest tiers, or $33/month
  with the 2 GB app and the same smallest database, allowing about 5 GB database
  storage and 1 GB app disk. These are rounded estimates; check exact storage
  inclusions at checkout. Larger database compute, traffic and additional backup
  storage increase the total. The smallest app/database may be too small for
  climate queries or NOAA imports; these examples are not sizing recommendations.
- **Management:** low relative burden: managed app hosting and PostgreSQL.
  Application updates, SQLite backups/restore tests, secrets, billing alerts
  and moderation still need an owner.
- **Changes:** small-to-medium packaging/configuration work; no storage rewrite.
  Keep accounts/comments on a private disk and weather in PostgreSQL.
- **Limit:** disk-backed apps have brief deploy downtime and cannot use multiple
  instances. The disk is unavailable during builds/pre-deploy jobs: initialize
  private databases at runtime through an appropriate operator procedure.
  [Disk limitations](https://render.com/docs/disks).

Free Render is for trials here: no persistent app disk, and free PostgreSQL
expires after 30 days. [Free-service limits](https://render.com/docs/free).

## Railway: convenient platform, variable bill

- **Published rates:** Hobby costs at least $5/month, including $5 usage—not
  $5 added to all usage. Container resources cost $10/GB-month RAM,
  $20/vCPU-month CPU, $0.15/GB-month volume storage and $0.05/GB egress.
  [Official pricing](https://docs.railway.com/pricing/plans).
- **Example budget:** roughly $10–25/month for a lightly used app and database,
  before backup growth. For illustration, combined average usage of 1 GB RAM,
  0.1 vCPU, 5 GB storage and 10 GB egress gives
  $10 + $2 + $0.75 + $0.50 = **$13.25/month**. Not a measured forecast or cap;
  sustained memory, traffic and imports can increase the bill.
- **Management:** low for app deployment, medium for the database. Railway
  explicitly describes database templates as unmanaged: backup/recovery,
  security, monitoring and maintenance remain your responsibility.
  [Database responsibilities](https://docs.railway.com/databases).
- **Changes:** small-to-medium, much like Render. Separate app and PostgreSQL
  volumes; accounts/comments/sessions can share one private app mount.
- **Limit:** volume-backed services cannot use replicas and have brief deploy
  downtime. Check required volume sizes/plan limits and configure backups.
  [Volumes](https://docs.railway.com/volumes/reference),
  [backups](https://docs.railway.com/volumes/backups).

## DigitalOcean VPS: more control, most maintenance

- **Published rates:** regular Basic Droplet, 2 GiB RAM / 1 vCPU / 50 GiB SSD:
  $12/month. A 4 GiB / 2 vCPU / 80 GiB option is $24/month. App and self-managed
  PostgreSQL share the machine. [Pricing](https://www.digitalocean.com/pricing/droplets).
- **Example budget:** **$14.40 or $28.80/month**, respectively, with weekly
  percentage-based backups (20% extra). Off-machine database backups, extra
  traffic/storage and domains are additional. Server snapshots do not replace
  tested database-consistent backups/restores.
  [Backup pricing](https://docs.digitalocean.com/products/backups/details/pricing/).
- **Management:** high. We must configure and maintain OS updates, firewall,
  HTTPS/reverse proxy, process restarts, PostgreSQL, monitoring and recovery.
  The price excludes that labor.
- **Changes:** small-to-medium application work, more operational setup than
  the platforms above. Native services or containers work; keep databases and
  private files inaccessible from the public internet.
- **Limit:** one host is a failure boundary for both app and database. Imports
  compete with browsing for RAM/CPU. Profile before choosing its size.

## Keep one project working locally and online

No separate online fork or frontend/framework rewrite is needed. Use the same
source/schema with separate configuration and data. Production foundation is
implemented locally; hosting and operational verification remain open:

1. Retain `.venv`, local PostgreSQL and `./run.sh`. A separate production
   Gunicorn launch is provided: `run.sh` still uses Flask's
   development server, which must not serve the public deployment.
   [Flask deployment guidance](https://flask.palletsprojects.com/en/stable/deploying/).
2. Production now requires `DATABASE_URL`, a private state root, secret and
   allowed hosts; local HTTP defaults remain. Verify these settings on the
   selected host, including the platform's port and persistent mount.
3. SQLite accounts/comments, sessions, generated charts and profile images use
   the private state root in production. Verify file persistence after redeploy
   and keep separate PostgreSQL backups.
4. Start with one app instance. Local SQLite and filesystem sessions are not
   a multi-host design; shared storage redesign precedes horizontal scaling.
5. Configure only known trusted proxy peers/hops. Test HTTPS/origin checks, admin
   login, CSRF and client-IP rate limits through the real proxy; never blindly
   trust forwarding headers supplied by visitors.
6. Preserve resumable fetching. Admin imports currently use a daemon thread in
   the web process: restarts can interrupt a month, while committed months
   survive. Avoid redeploys during imports and test resumption. An independent
   durable worker is a later option, not included in these costs or scope.
7. An optional non-root Dockerfile and restricted build context are provided.
   A Compose setup is not included; native local startup remains valid.
   [Compose documentation](https://docs.docker.com/compose/) is background
   research only.

Effort ratings are architectural estimates based on `requirements.txt`, `run.sh`,
`climate/paths.py`, `climate/data/db.py`, `climate/web/app.py`,
`climate/web/helpers.py`, `climate/services/admin_import.py` and
[community setup](COMMUNITY.md), not tested deployments. Expect configuration,
packaging and focused verification, not a major feature rewrite.

## Before paying or publishing

- Measure database size including indexes, representative query memory/traffic
  and an isolated bounded import. Confirm PostgreSQL 18 support and restore
  compatibility on the selected plan.
- Keep local/online databases separate. Move climate data by deliberate private
  export/restore, never Git. Do not automatically copy accounts or sessions.
- Verify restart persistence, backups/restores, browser flows and cost alerts.
  Existing offline tests are not production load/security sign-off.
- Keep community disabled until administrator access, proxy protections and
  moderation are ready. One region can serve worldwide visitors; multi-region
  infrastructure is not required for launch.

Sources above are official provider/product webpages used as linked research,
not copied assets or newly installed dependencies. Hosting has its own terms;
no subscription or terms acceptance has occurred.
