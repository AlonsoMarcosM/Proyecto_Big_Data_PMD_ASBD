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
    .option("startingOffsets", "earliest")
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
    enriched.withWatermark("event_time", "5 minutes")
    .groupBy(
        window(col("event_time"), "1 minute"),
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

gold_query = (
    agg.writeStream.format("delta")
    .option("path", gold_path)
    .option("checkpointLocation", gold_checkpoint)
    .outputMode("append")
    .trigger(processingTime="30 seconds")
    .start()
)

spark.streams.awaitAnyTermination()
