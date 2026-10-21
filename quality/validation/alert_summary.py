import os

import psycopg2

SQL = """
select alert_type, severity, count(*)
from alerts.alerts_all
group by 1, 2
order by 1, case severity when 'critical' then 1 when 'high' then 2 else 3 end
"""


def main():
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=5432,
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    try:
        with conn, conn.cursor() as cur:
            cur.execute(SQL)
            rows = cur.fetchall()
    finally:
        conn.close()

    print("===== ALERT SUMMARY =====")
    print(f"{'alert_type':18} {'severity':10} {'count':>7}")
    for alert_type, severity, count in rows:
        print(f"{alert_type:18} {severity:10} {count:>7,}")
    criticals = sum(c for _, s, c in rows if s == "critical")
    if criticals:
        print(f"\nATTENTION: {criticals} critical alert(s) need action today.")


if __name__ == "__main__":
    main()