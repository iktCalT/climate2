# User roles and manual climate prefetch

Visitors and normal registered users can browse Maps and Locations. They cannot
open or submit `/update`.

New accounts are created with `is_admin = false`, even though older local user
databases may have been created when the original project granted every account
administrator access. Existing administrators are retained deliberately so the
site owner does not lose access during this refactor.

To appoint or remove an administrator on your local machine, run one of:

```sh
.venv/bin/python manage_users.py grant-admin USERNAME
.venv/bin/python manage_users.py revoke-admin USERNAME
```

The command changes only the ignored local user database (`static/users.db`, or
the path supplied by `USER_DATABASE_PATH`). Do not commit that database.

Administrators use `/update` to pre-fetch Open-Meteo climate data into the
PostgreSQL cache. Each request is capped at 100 locations, uses dates from
January 1950 through today, and is validated on the server as well as in the
form. Break larger areas into several requests to stay within Open-Meteo usage
limits.
