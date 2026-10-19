import os
import sys
from functools import reduce

from pyspark.sql import DataFrame, functions as F
from pyspark.sql.types import DateType, StringType, StructField, StructType

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))
from spark_session import get_spark  # noqa: E402

BASE = "s3a://supplychain-data"
TABLES = ["suppliers", "products", "customers", "warehouses",
          "inventory", "orders", "order_items", "shipments"]

URL = (f"jdbc:postgresql://{os.environ.get('POSTGRES_HOST', 'host.docker.internal')}"
       f":5432/{os.environ['POSTGRES_DB']}")
PROPS = {
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
    "driver": "org.postgresql.Driver",
}

# Used when nothing at all was quarantined, so the table still exists
EMPTY_SCHEMA = StructType([
    StructField("source_table", StringType()),
    StructField("dq_errors", StringType()),
    StructField("record_json", StringType()),
    StructField("batch_id", StringType()),
    StructField("ingest_date", DateType()),
])


def write(df, table):
    # truncate=true: a rerun empties the table and reloads it (safe to repeat)
    df.write.mode("overwrite").option("truncate", "true").jdbc(URL, table, properties=PROPS)


def main():
    spark = get_spark("sc360-quality-to-postgres")

    # 1. Run statistics: one set of rows per pipeline day
    stats = spark.read.parquet(f"{BASE}/quality/run_stats/")
    write(stats, "quality.run_stats")
    print(f"{'quality.run_stats':30} {stats.count():>6,} rows")

    # 2. Every rejected record from every table, in ONE table:
    #    which table, why it failed, and the original record as JSON
    frames = []
    for table in TABLES:
        try:
            df = spark.read.parquet(f"{BASE}/quarantine/{table}/")
        except Exception:
            continue  # nothing was quarantined for this table
        business_cols = [c for c in df.columns if not c.startswith("_") and c != "ingest_date"]
        frames.append(df.select(
            F.lit(table).alias("source_table"),
            F.col("_dq_errors").alias("dq_errors"),
            F.to_json(F.struct(*business_cols)).alias("record_json"),
            F.col("_batch_id").alias("batch_id"),
            F.col("ingest_date"),
        ))
    rejected = (reduce(DataFrame.unionByName, frames) if frames
                else spark.createDataFrame([], EMPTY_SCHEMA))
    write(rejected, "quarantine.rejected_records")
    print(f"{'quarantine.rejected_records':30} {rejected.count():>6,} rows")


if __name__ == "__main__":
    main()