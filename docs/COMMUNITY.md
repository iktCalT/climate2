# Local profiles and public map comments

Implementation is present; verification status is on the agent task board. This
guide is not production sign-off. Hosted registration stays closed; existing
administrator accounts remain.

## Privacy and ownership

Ordinary climate browsing does not require a local profile or prompt for storage.
Choosing the local-profile feature offers explicit consent to store a nickname,
a random ownership token and its fixed expiry in this browser's localStorage for
30 days. Reopening an unexpired profile does not extend that period. Explicitly
reusing a valid older profile adds the expiry while preserving its token; an
expired profile is removed only when the user explicitly reuses the device.
While a page remains open, expiry deactivates the profile without a storage write.
After expiry, this browser cannot delete those pins, but they remain public and
administrators can still remove them. The server continues to authorize by token
hash; browser expiry is convenience behavior, not server-side revocation. No email
or password is needed. This is not an authenticated personal account. Blocked
storage must produce an error, not silently create another identity.

Publishing deliberately sends a nickname, coordinates and an optional plain-text
message of up to 500 trimmed characters to the site; blank messages are allowed.
Everyone can read the pin and any message by opening it. Do not post private
information. Server storage is necessary for public visibility: localStorage alone
cannot share pins with other visitors. Clearing or expiring this browser's profile
does not delete public pins and loses its deletion credential. Delete your pins
first if that is your intention. Administrators can remove public pins.
On Maps, clicking a climate location keeps its usual readouts and offers an
enabled-only **Add pin here** action. That action selects coordinates and opens the
draft controls; it does not read storage or publish. Typing coordinates is also
available. Both paths require a separate submit and explicit public consent.

## Limits and abuse controls

The initial allowance is ten active pins per browser identity, configurable by
the operator. Lowering it (for example to three) prevents new posts above the new
limit without deleting existing ones. Clearing storage can create another
identity, so this is not a reliable per-person limit. Transactional checks and
IP/identity write throttles reduce abuse, but do not prevent determined attackers.
Each pin has at most one optional message; clustering is deferred, with grouped
messages required when clusters are eventually added.

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
  A fresh empty account database has no administrator. Use the terminal-only
  [first administrator setup](USER_ROLES.md#first-administrator-on-a-new-deployment)
  or securely restore an existing private account database before enabling
  comments; never reopen public registration or publish account data to do this.
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
