import os
import sys

from pyspark.sql import functions as F

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))
from spark_session import get_spark  # noqa: E402

BASE = "s3a://supplychain-data"
C = F.col

spark = get_spark("sc360-bronze-to-silver")  # start Spark BEFORE the rules below are built

# How to convert each raw text column into a proper type
CASTS = {
    "int": lambda c: C(c).cast("double").cast("long"),  # handles "383.0" and "383"
    "double": lambda c: C(c).cast("double"),
    "date": lambda c: F.to_date(F.substring(C(c), 1, 10), "yyyy-MM-dd"),  # handles both date styles
    "text": lambda c: F.trim(C(c)),
}

# For every table: key columns, column types, validity rules (True = row is OK),
# and optional derived columns that are added to the good rows.
SPECS = {
    "suppliers": dict(
        key=["supplier_id"],
        types={"supplier_id": "int", "supplier_name": "text", "location": "text",
               "category": "text", "rating": "double", "lead_time": "int",
               "contract_start_date": "date"},
        rules={"supplier_id_missing": C("supplier_id").isNotNull(),
               "rating_not_0_to_5": C("rating").between(0, 5),
               "lead_time_negative": C("lead_time") >= 0},
    ),
    "products": dict(
        key=["product_id"],
        types={"product_id": "int", "product_name": "text", "category": "text",
               "sub_category": "text", "supplier_id": "int", "unit_cost": "double",
               "selling_price": "double", "weight": "double"},
        rules={"product_id_missing": C("product_id").isNotNull(),
               "unit_cost_not_positive": C("unit_cost") > 0,
               "selling_price_not_positive": C("selling_price") > 0},
        derive=lambda d: d.withColumn("unit_margin", F.round(C("selling_price") - C("unit_cost"), 2)),
    ),
    "customers": dict(
        key=["customer_id"],
        types={"customer_id": "int", "customer_name": "text", "city": "text",
               "state": "text", "country": "text", "customer_segment": "text",
               "registration_date": "date"},
        rules={"customer_id_missing": C("customer_id").isNotNull(),
               "registration_date_invalid": C("registration_date").isNotNull()},
    ),
    "warehouses": dict(
        key=["warehouse_id"],
        types={"warehouse_id": "int", "warehouse_name": "text", "city": "text",
               "state": "text", "capacity": "int", "current_utilization": "double"},
        rules={"warehouse_id_missing": C("warehouse_id").isNotNull(),
               "capacity_not_positive": C("capacity") > 0,
               "utilization_negative": C("current_utilization") >= 0},
        derive=lambda d: d.withColumn("is_over_utilized", C("current_utilization") > 1.0),
    ),
    "inventory": dict(
        key=["warehouse_id", "product_id"],
        types={"warehouse_id": "int", "product_id": "int", "stock_quantity": "int",
               "reorder_level": "int", "last_updated": "date"},
        rules={"warehouse_id_missing": C("warehouse_id").isNotNull(),
               "product_id_missing": C("product_id").isNotNull(),
               "stock_negative": C("stock_quantity") >= 0,
               "reorder_level_negative": C("reorder_level") >= 0},
        derive=lambda d: d.withColumn("is_low_stock", C("stock_quantity") < C("reorder_level")),
    ),
    "orders": dict(
        key=["order_id"],
        types={"order_id": "int", "customer_id": "int", "order_date": "date",
               "order_status": "text", "payment_method": "text",
               "total_amount": "double", "shipping_address": "text"},
        rules={"order_id_missing": C("order_id").isNotNull(),
               "customer_id_missing": C("customer_id").isNotNull(),
               "order_date_invalid": C("order_date").isNotNull(),
               "total_amount_negative": C("total_amount") >= 0},
    ),
    "order_items": dict(
        key=["order_id", "product_id"],
        types={"order_id": "int", "product_id": "int", "quantity": "int",
               "unit_price": "double", "discount": "double", "total_price": "double"},
        rules={"order_id_missing": C("order_id").isNotNull(),
               "product_id_missing": C("product_id").isNotNull(),
               "quantity_not_positive": C("quantity") > 0,
               "unit_price_negative": C("unit_price") >= 0,
               "discount_not_0_to_1": C("discount").between(0, 1)},
        derive=lambda d: d.withColumn("gross_revenue", F.round(C("quantity") * C("unit_price"), 2)),
    ),
    "shipments": dict(
        key=["shipment_id"],
        types={"shipment_id": "int", "order_id": "int", "warehouse_id": "int",
               "carrier": "text", "shipping_date": "date", "expected_delivery": "date",
               "actual_delivery": "date", "shipping_cost": "double",
               "shipment_status": "text"},
        rules={"shipment_id_missing": C("shipment_id").isNotNull(),
               "order_id_missing": C("order_id").isNotNull(),
               "shipping_date_invalid": C("shipping_date").isNotNull(),
               "delivered_before_shipped": C("actual_delivery").isNull()
                                           | (C("actual_delivery") >= C("shipping_date")),
               "shipping_cost_negative": C("shipping_cost") >= 0},
        derive=lambda d: (
            d.withColumn("delivery_days", F.datediff("actual_delivery", "shipping_date"))
             .withColumn("expected_days", F.datediff("expected_delivery", "shipping_date"))
             .withColumn("is_delayed", F.when(C("actual_delivery").isNotNull(),
                                              C("actual_delivery") > C("expected_delivery")))
        ),
    ),
}


def process(spark, table, spec):
    # Read the newest Bronze load of this table
    raw = spark.read.parquet(f"{BASE}/bronze/{table}/")
    latest = raw.agg(F.max("ingest_date")).first()[0]
    df = raw.filter(C("ingest_date") == latest)
    n_raw = df.count()

    # 1. Fix types
    for col, kind in spec["types"].items():
        df = df.withColumn(col, CASTS[kind](col))

    # 2. Remove duplicates (one row per key)
    deduped = df.dropDuplicates(spec["key"]).cache()
    n_dedup = deduped.count()

    # 3. Validate: list the rules each row breaks (an empty list means the row is good)
    checks = [F.when(cond, F.lit(None).cast("string")).otherwise(F.lit(name))
              for name, cond in spec["rules"].items()]
    flagged = deduped.withColumn("_dq_errors", F.filter(F.array(*checks), lambda x: x.isNotNull()))

    good = flagged.filter(F.size("_dq_errors") == 0).drop("_dq_errors")
    bad = (flagged.filter(F.size("_dq_errors") > 0)
           .withColumn("_dq_errors", F.concat_ws(",", C("_dq_errors"))))

    # 4. Derived columns, only on good rows
    if "derive" in spec:
        good = spec["derive"](good)
    good = good.withColumn("_silver_at", F.current_timestamp())

    # 5. Write good rows to silver, bad rows to quarantine
    good.write.mode("overwrite").parquet(f"{BASE}/silver/{table}/")
    bad.write.mode("overwrite").parquet(f"{BASE}/quarantine/{table}/")

    n_bad = bad.count()
    if n_bad:
        print(f"--- {table}: why rows were quarantined ---")
        bad.groupBy("_dq_errors").count().show(truncate=False)
    deduped.unpersist()
    return n_raw, n_raw - n_dedup, n_dedup - n_bad, n_bad


def main():
    spark = get_spark("sc360-bronze-to-silver")
    summary = []
    for table, spec in SPECS.items():
        print(f"Processing {table} ...")
        summary.append((table, *process(spark, table, spec)))

    print("\n===== SUMMARY =====")
    print(f"{'table':12} {'raw':>7} {'dups_removed':>13} {'silver':>7} {'quarantined':>12}")
    for t, raw, dups, ok, bad in summary:
        print(f"{t:12} {raw:>7,} {dups:>13,} {ok:>7,} {bad:>12,}")


if __name__ == "__main__":
    main()