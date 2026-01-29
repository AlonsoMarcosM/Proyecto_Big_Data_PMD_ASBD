import csv
import json
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    count,
    countDistinct,
    from_json,
    split,
    to_timestamp,
)
from pyspark.sql.types import StructField, StructType, StringType


def build_spark() -> SparkSession:
    builder = (
        SparkSession.builder
        .appName("pmd_csv_batch_medallion")
        .master("spark://spark-master:7077")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.warehouse.dir", "s3a://catalogo-datasets/")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin123")
    )
    return builder.getOrCreate()

def write_preview(df, out_dir, limit=20):
    rows = df.limit(limit).collect()
    if not rows:
        return

    try:
        os.makedirs(out_dir, exist_ok=True)
        columns = df.columns

        csv_path = os.path.join(out_dir, "preview.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([row[col] for col in columns])

        json_path = os.path.join(out_dir, "preview.jsonl")
        with open(json_path, "w", encoding="utf-8") as json_file:
            for row in rows:
                json_file.write(json.dumps(row.asDict(), default=str) + "\n")
    except OSError as exc:
        print(f"Preview not written: {exc}")


spark = build_spark()

input_path = "file:/opt/spark-data/csv/catalogo_dataset.csv"

bronze_path = "s3a://catalogo-datasets/bronze/csv/catalogo_dataset"
silver_path = "s3a://catalogo-datasets/silver/csv/catalogo_dataset"
gold_path = "s3a://catalogo-datasets/gold/csv/datasets_by_category"
preview_dir = "/opt/visualizaciones/gold_csv_datasets_by_category"

raw_df = (
    spark.read
    .option("header", True)
    .option("escape", "\"")
    .csv(input_path)
)

raw_df.write.format("delta").mode("overwrite").save(bronze_path)

extras_schema = StructType([
    StructField("license", StringType(), True),
    StructField("frequency", StringType(), True),
    StructField("format", StringType(), True),
])

silver_df = (
    raw_df
    .withColumn("extras", from_json(col("extras_json"), extras_schema))
    .withColumn("tags", split(col("tags"), ";"))
    .withColumn("modified_at", to_timestamp(col("modified_at"), "yyyy-MM-dd'T'HH:mm:ssX"))
    .select(
        col("dataset_id"),
        col("title"),
        col("category"),
        col("owner"),
        col("tags"),
        col("extras.license").alias("license"),
        col("extras.frequency").alias("frequency"),
        col("extras.format").alias("format"),
        col("modified_at"),
    )
    .dropDuplicates(["dataset_id"])
)

silver_df.write.format("delta").mode("overwrite").save(silver_path)

gold_df = (
    silver_df.groupBy("category")
    .agg(
        count("dataset_id").alias("dataset_count"),
        countDistinct("owner").alias("owners_count"),
    )
)

gold_df.write.format("delta").mode("overwrite").save(gold_path)
write_preview(gold_df, preview_dir)

spark.stop()
