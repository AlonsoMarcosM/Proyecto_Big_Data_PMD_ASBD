import csv
import json
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    coalesce,
    count,
    current_timestamp,
    from_json,
    lit,
    try_to_timestamp,
    window,
)
from pyspark.sql.types import StructField, StructType, StringType


def build_spark() -> SparkSession:
    builder = (
        SparkSession.builder
        .appName("pmd_kafka_streaming_medallion")
        .master("spark://spark-master:7077")
        .config("spark.submit.deployMode", "client")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.warehouse.dir", "s3a://catalogo-datasets/")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin123")
        .config("spark.sql.shuffle.partitions", "4")
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

schema = StructType([
    StructField("event_time", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("dataset_id", StringType(), True),
    StructField("changed_field", StringType(), True),
    StructField("new_value", StringType(), True),
])

raw_events = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "dataset_updates")
    .option("startingOffsets", "latest")
    .option("failOnDataLoss", "false")
    .option("maxOffsetsPerTrigger", "200")
    .load()
)

bronze_events = raw_events.selectExpr(
    "CAST(value AS STRING) as payload",
    "timestamp as kafka_time",
)

bronze_path = "s3a://catalogo-datasets/bronze/kafka/dataset_updates"
bronze_checkpoint = "s3a://catalogo-datasets/checkpoints/bronze/kafka_dataset_updates"

bronze_query = (
    bronze_events.writeStream.format("delta")
    .option("path", bronze_path)
    .option("checkpointLocation", bronze_checkpoint)
    .outputMode("append")
    .start()
)

parsed_events = (
    bronze_events.select(from_json(col("payload"), schema).alias("event"))
    .select("event.*")
    .withColumn(
        "event_time",
        coalesce(
            try_to_timestamp(col("event_time"), lit("yyyy-MM-dd'T'HH:mm:ss.SSSSSSX")),
            try_to_timestamp(col("event_time"), lit("yyyy-MM-dd'T'HH:mm:ssX")),
        ),
    )
    .withColumn("processing_time", current_timestamp())
    .where(col("event_time").isNotNull())
)

silver_path = "s3a://catalogo-datasets/silver/kafka/dataset_updates"
silver_checkpoint = "s3a://catalogo-datasets/checkpoints/silver/kafka_dataset_updates"

silver_query = (
    parsed_events.writeStream.format("delta")
    .option("path", silver_path)
    .option("checkpointLocation", silver_checkpoint)
    .outputMode("append")
    .start()
)

batch_silver_path = "s3a://catalogo-datasets/silver/sqlserver/dataset_snapshot"
batch_silver = spark.read.format("delta").load(batch_silver_path)

enriched = parsed_events.join(batch_silver, "dataset_id", "left")

agg = (
    enriched.withWatermark("event_time", "1 minute")
    .groupBy(
        window(col("event_time"), "30 seconds"),
        col("dataset_id"),
        col("event_type"),
        col("owner"),
    )
    .agg(count("dataset_id").alias("events_count"))
    .select(
        col("dataset_id"),
        col("event_type"),
        col("owner"),
        col("events_count"),
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
    )
)

gold_path = "s3a://catalogo-datasets/gold/kafka/dataset_updates_agg"
gold_checkpoint = "s3a://catalogo-datasets/checkpoints/gold/kafka_dataset_updates_agg"
preview_dir = "/opt/visualizaciones/gold_kafka_dataset_updates_agg"

def write_gold_and_preview(batch_df, _batch_id):
    batch_df.write.format("delta").mode("append").save(gold_path)
    write_preview(batch_df, preview_dir)

gold_query = (
    agg.writeStream.foreachBatch(write_gold_and_preview)
    .option("checkpointLocation", gold_checkpoint)
    .outputMode("update")
    .trigger(processingTime="30 seconds")
    .start()
)

spark.streams.awaitAnyTermination()
