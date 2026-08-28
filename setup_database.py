"""Create the local PostgreSQL weather schema.

Run after PostgreSQL is running and DATABASE_URL is configured:
    python setup_database.py
"""

from pathlib import Path

from db import weather_db


def main():
    schema = Path(__file__).with_name("schema.sql").read_text()
    with weather_db() as con:
        with con.cursor() as cur:
            cur.execute(schema)
    print("PostgreSQL weather schema is ready.")


if __name__ == "__main__":
    main()
