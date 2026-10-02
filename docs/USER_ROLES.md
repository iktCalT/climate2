# User roles and manual climate prefetch

Visitors and normal registered users can browse Maps and Locations. They cannot
open or submit `/update`.

Hosted self-registration is temporarily closed because the owner has no time to
manage accounts. `/register` explains the closure; POST requests are rejected
with 403 without creating users or profiles. Existing accounts and administrator
login are retained. Older local databases may have granted every account admin
access: audit those roles before public deployment.

To appoint or remove an administrator on your local machine, run one of:

```sh
.venv/bin/python -m climate.cli.manage_users grant-admin USERNAME
.venv/bin/python -m climate.cli.manage_users revoke-admin USERNAME
```

The command changes only the ignored local account database. Flask, account
initialization, and this command share the same path selection: explicit
`USER_DATABASE_PATH`, then an existing legacy `static/users.db` with a warning,
otherwise the private `instance/users.db`. Legacy selection takes precedence
even if both default files exist, so upgrading cannot silently switch accounts.
Do not commit either database.

## Private account storage

New installations keep accounts outside `static/`. Existing installations can
continue using their legacy file temporarily; Flask blocks database downloads,
recognizable database backup names, SQLite sidecars, hidden files, configured account files even with another
extension, and static paths/symlinks that escape the public root.

To relocate existing accounts deliberately, stop all application/account
writers, make a private SQLite-consistent backup, and restore it to a private
path such as `instance/users.db`. Do not overwrite an existing destination.
Set `USER_DATABASE_PATH` consistently for the app and account tools, restart,
and verify login and administrator access before retiring the legacy copy.
Keep backups outside the public directory and Git; filename checks cannot identify
arbitrarily renamed copies. The application never moves
or deletes account files automatically; pointing at an empty path does not
migrate existing accounts.

Flask's guard applies only to requests it serves. A reverse proxy or web server
serving `static/` directly must independently deny private files. Remove private
database copies from that public directory before exposing it through another
server; ignored Git files are not automatically private HTTP resources.

## Climate acquisition

Administrators use `/update` to pre-fetch Open-Meteo climate data into the
PostgreSQL cache. Each request is capped at 100 locations, uses dates from
January 1950 through today, and is validated on the server as well as in the
form. Break larger areas into several requests to stay within Open-Meteo usage
limits.
