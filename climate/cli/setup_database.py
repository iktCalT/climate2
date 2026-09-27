"""Create the local PostgreSQL weather schema.

Run after PostgreSQL is running and DATABASE_URL is configured:
    python -m climate.cli.setup_database
"""

from climate.paths import SQL_DIRECTORY

from climate.data.db import weather_db


def main():
    schema = (SQL_DIRECTORY / "schema.sql").read_text()
    with weather_db() as con:
        with con.cursor() as cur:
            cur.execute(schema)
            cur.execute((SQL_DIRECTORY / "admin_import.sql").read_text())
    print("PostgreSQL weather schema is ready.")


if __name__ == "__main__":
    main()
