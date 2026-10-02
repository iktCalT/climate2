# Local profiles and public map comments

Implementation is present; verification status is on the agent task board. This
guide is not production sign-off. Hosted registration stays closed; existing
administrator accounts remain.

## Privacy and ownership

Ordinary climate browsing does not require a local profile or prompt for storage.
Choosing the local-profile feature offers explicit consent to store a nickname
and a random ownership token in this browser's localStorage. No email or password
is needed. This is device-local convenience, not an authenticated personal account.
Blocked storage must produce an error, not silently create another identity.

Publishing deliberately sends a nickname, one plain-text comment and coordinates
to the site; everyone can read them by opening its pin. Do not post private
information. Server storage is necessary for public visibility: localStorage alone
cannot share comments with other visitors. Clearing this browser's profile does
not delete public comments and loses its deletion credential. Delete your pins
first if that is your intention. Administrators can remove public pins.

## Limits and abuse controls

The initial allowance is ten active pins per browser identity, configurable by
the operator. Lowering it (for example to three) prevents new posts above the new
limit without deleting existing ones. Clearing storage can create another
identity, so this is not a reliable per-person limit. Transactional checks and
IP/identity write throttles reduce abuse, but do not prevent determined attackers.
Each pin has one comment; clustering is deferred, with grouped comments required
when clusters are eventually added.

Published text must be length-limited and rendered as text, never HTML. Write
requests require same-origin JSON and the appropriate ownership token or admin
session/CSRF. Public reads are bounded by viewport and pagination. Community data
is stored separately from climate data and hosted accounts in an ignored private
SQLite database. Only token hashes and short-lived keyed IP digests are persisted,
not raw tokens or IP addresses. Reverse-proxy access logs are separate: configure
their retention/privacy policy before deployment.

## Deployment checklist

- Keep the feature disabled until its enable flag, strong private secret and
  persistent private storage are configured. Never commit those values or the
  populated database. The secret must be consistent across workers/restarts.
- Use HTTPS; put storage outside the web/static root, restrict filesystem access,
  back it up privately and ensure the deployment volume survives restarts.
- Review existing administrator roles and verify login/removal before opening
  comments. Hosted registration is blocked, not a complete authentication audit.
  A fresh empty account database has no administrator: the existing `manage_users`
  command grants roles to existing accounts only. Securely provision/restore an
  administrator account outside Git before enabling comments; never temporarily
  reopen public registration or publish the account database to do this.
- Do not trust arbitrary forwarded-IP headers. Without explicitly configured
  trusted-proxy handling, a proxy may make visitors share a rate-limit bucket.
  Multi-host deployment needs shared transactional persistence, not independent
  SQLite copies. SQLite is intended for a small single-host deployment here.
- Set retention, takedown/contact and moderation procedures before publication.
  Immediate public comments still require occasional abuse review; automated
  checks do not remove that responsibility. A feature kill switch is required.
- Verify actual desktop/mobile rendering and browser storage behavior. Automated
  checks alone do not establish accessibility, production security or capacity.

## Configuration

Set these through the deployment environment, not tracked files:

- `COMMUNITY_ENABLED=1`: explicitly enable the feature; omit or set to `0` to
  disable both reading and writing community data.
- `COMMUNITY_SECRET`: a strong random secret of at least 32 characters, kept
  private and stable. Used to key network-rate identifiers, never sent to clients.
- `COMMUNITY_DATABASE_PATH`: private persistent SQLite path, default
  `instance/community.db`; never use a climate or account database. Public-path
  aliases and hard-linked store files are rejected; use a regular private file.
- `COMMUNITY_MAX_ACTIVE`: active pins per browser identity, default `10`.
- `COMMUNITY_HOURLY_LIMIT` / `COMMUNITY_DAILY_LIMIT`: network change limits,
  default `20` / `100`.
- `COMMUNITY_COOLDOWN_SECONDS`: delay between one identity's posts, default `10`.

Invalid configuration fails closed. Rate limits share the SQLite store across
workers on the same host. IP digests are retained for rate-limit windows and
expired during subsequent successful writes; this is not a scheduled retention
job. Disabling the feature does not erase stored public content.

No deployment, public data import or live database mutation is part of this
code round. Verification status is recorded on the agent task board.
