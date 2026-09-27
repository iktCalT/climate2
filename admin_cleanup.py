"""Explicit, bounded climate-cache pruning. Never called automatically."""

from admin_import import ImportBusy, LOCK_ID, _connect

MAX_CLEANUP_ROWS = 50_000
# Fixed half-open ranges preserve every date in both requested five-year windows.
OUTSIDE_WINDOWS = """NOT (
    (dates >= DATE '1950-01-01' AND dates < DATE '1955-01-01') OR
    (dates >= DATE '2022-01-01' AND dates < DATE '2027-01-01')
)"""


def cleanup_preview():
    """Count only; no provider requests or data mutations."""
    with _connect() as con, con.transaction():
        con.execute("SET LOCAL statement_timeout = '30s'")
        rows = con.execute(f"""
            SELECT provider, COUNT(*) FILTER (WHERE NOT ({OUTSIDE_WINDOWS})),
                   COUNT(*) FILTER (WHERE {OUTSIDE_WINDOWS})
            FROM data GROUP BY provider ORDER BY provider
        """).fetchall()
    providers = [dict(provider=name, kept=kept, removable=removable)
                 for name, kept, removable in rows]
    return {"providers": providers, "batch_limit": MAX_CLEANUP_ROWS,
            "removable": sum(row["removable"] for row in providers)}


def cleanup_batch():
    """Delete at most one batch atomically; callers must confirm separately.

    The transaction lock conflicts with both other cleanup requests and the
    admin importer. Row locks protect selected CTIDs within this one statement.
    CLI writers do not share the advisory lock and should be paused by the admin.
    """
    with _connect() as con, con.transaction():
        con.execute("SET LOCAL lock_timeout = '2s'")
        con.execute("SET LOCAL statement_timeout = '30s'")
        if not con.execute("SELECT pg_try_advisory_xact_lock(%s)", (LOCK_ID,)).fetchone()[0]:
            raise ImportBusy("An administrator data operation is running. Try again when it finishes.")
        cursor = con.execute(f"""
            WITH batch AS (
                SELECT ctid FROM data WHERE {OUTSIDE_WINDOWS}
                LIMIT %s FOR UPDATE
            )
            DELETE FROM data AS d USING batch WHERE d.ctid = batch.ctid
        """, (MAX_CLEANUP_ROWS,))
        deleted = cursor.rowcount
    return {"deleted": deleted, "batch_limit": MAX_CLEANUP_ROWS}
