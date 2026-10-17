import os

from pyspark.sql import SparkSession


def get_spark(app_name: str) -> SparkSession:
    """Create a local Spark session connected to MinIO."""
    spark = (
        SparkSession.builder.appName(app_name)
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
    return spark