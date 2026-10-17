import os
from pathlib import Path

import psycopg2

SQL_FILE = Path(__file__).parent / "schemas" / "star_schema.sql"


def main():
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=5432,
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    try:
        with conn, conn.cursor() as cur:  # one transaction: all or nothing
            cur.execute(SQL_FILE.read_text(encoding="utf-8"))
            rows = cur.fetchall()  # the row-count table at the end of the SQL file
    finally:
        conn.close()

    print(f"{'table':16} {'rows':>8}")
    for name, count in rows:
        print(f"{name:16} {count:>8,}")


if __name__ == "__main__":
    main()