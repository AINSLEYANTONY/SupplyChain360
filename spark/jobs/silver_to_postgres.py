import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))
from spark_session import get_spark  # noqa: E402

BASE = "s3a://supplychain-data"
TABLES = ["suppliers", "products", "customers", "warehouses",
          "inventory", "orders", "order_items", "shipments"]

URL = f"jdbc:postgresql://{os.environ.get('POSTGRES_HOST', 'host.docker.internal')}:5432/{os.environ['POSTGRES_DB']}"
PROPS = {
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
    "driver": "org.postgresql.Driver",
}


def main():
    spark = get_spark("sc360-silver-to-postgres")
    print(f"\n{'table':14} {'rows loaded':>12}")
    for table in TABLES:
        df = spark.read.parquet(f"{BASE}/silver/{table}/")
        # truncate=true: on a rerun, empty the table and reload it
        # (same result every time, so the job is safe to repeat)
        (df.write.mode("overwrite")
           .option("truncate", "true")
           .jdbc(URL, f"silver.{table}", properties=PROPS))
        print(f"{table:14} {df.count():>12,}")


if __name__ == "__main__":
    main()