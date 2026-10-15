import os

from pyspark.sql import SparkSession, functions as F

spark = (
    SparkSession.builder.appName("sc360-test")
    .master("local[2]")
    .config("spark.driver.memory", "2g")
    .config("spark.sql.shuffle.partitions", "8")
    .config("spark.hadoop.fs.s3a.endpoint", "http://host.docker.internal:9000")
    .config("spark.hadoop.fs.s3a.access.key", os.environ["MINIO_ROOT_USER"])
    .config("spark.hadoop.fs.s3a.secret.key", os.environ["MINIO_ROOT_PASSWORD"])
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

orders = spark.read.parquet("s3a://supplychain-data/bronze/orders/")

print("\n===== RESULTS =====")
print("rows:", orders.count())
print("duplicate order_ids:", orders.count() - orders.select("order_id").distinct().count())
print("null customer_id:", orders.filter(F.col("customer_id").isNull()).count())
orders.printSchema()
orders.show(5, truncate=False)