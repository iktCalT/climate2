"""Read-only discovery of saved active-provider map months."""

from climate.data.db import ACTIVE_CLIMATE_PROVIDER, CLIMATE_TYPES, weather_db


def saved_map_months(start, end):
    """Return descending months and finite-value point counts per metric.

    Maps query the first day of a month, so non-monthly dates are not advertised.
    Counts describe global saved points, not geographic coverage or data quality.
    All SQL identifiers come from the application's fixed metric allowlist.
    """
    finite = {field: f"({field} > '-Infinity'::float8 AND {field} < 'Infinity'::float8)"
              for field in CLIMATE_TYPES}
    counts = ", ".join(f"COUNT(*) FILTER (WHERE {finite[field]})" for field in CLIMATE_TYPES)
    with weather_db() as con:
        with con.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute("SET LOCAL statement_timeout = '3s'")
            cur.execute("SET LOCAL lock_timeout = '500ms'")
            cur.execute(f"""
                SELECT dates, {counts}
                FROM data
                WHERE provider = %s AND dates BETWEEN %s AND %s
                  AND EXTRACT(DAY FROM dates) = 1
                  AND ({' OR '.join(finite.values())})
                GROUP BY dates ORDER BY dates DESC
            """, (ACTIVE_CLIMATE_PROVIDER, f"{start}-01", f"{end}-01"))
            rows = cur.fetchall()
    return [{"month": row[0].strftime("%Y-%m"),
             "counts": dict(zip(CLIMATE_TYPES, row[1:]))} for row in rows]
