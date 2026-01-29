import csv
import json
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, to_timestamp, count, max as spark_max, row_number
from pyspark.sql.window import Window


def build_spark() -> SparkSession:
    builder = (
        SparkSession.builder
        .appName("pmd_sqlserver_medallion")
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

def delta_exists(spark, path: str) -> bool:
    hadoop_conf = spark._jsc.hadoopConfiguration()
    uri = spark._jvm.java.net.URI(path)
    fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(uri, hadoop_conf)
    delta_log = spark._jvm.org.apache.hadoop.fs.Path(f"{path}/_delta_log")
    return fs.exists(delta_log)


spark = build_spark()

jdbc_url = (
    "jdbc:sqlserver://sqlserver:1433;"
    "databaseName=catalogo;"
    "encrypt=true;trustServerCertificate=true;"
)

bronze_path = "s3a://catalogo-datasets/bronze/sqlserver/dataset_snapshot"
silver_path = "s3a://catalogo-datasets/silver/sqlserver/dataset_snapshot"
gold_path = "s3a://catalogo-datasets/gold/sqlserver/datasets_by_owner"
preview_dir = "/opt/visualizaciones/gold_sqlserver_datasets_by_owner"

last_ts = None
silver_exists = delta_exists(spark, silver_path)
if silver_exists:
    last_ts = (
        spark.read.format("delta")
        .load(silver_path)
        .agg(spark_max("modified_at").alias("max_modified"))
        .collect()[0]["max_modified"]
    )

dbtable = "dbo.dataset_snapshot"
if last_ts:
    last_ts_str = last_ts.strftime("%Y-%m-%d %H:%M:%S")
    dbtable = (
        "(SELECT * FROM dbo.dataset_snapshot "
        f"WHERE modified_at > '{last_ts_str}') AS t"
    )

incremental_df = (
    spark.read.format("jdbc")
    .option("url", jdbc_url)
    .option("dbtable", dbtable)
    .option("user", "sa")
    .option("password", "Password1234%")
    .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver")
    .load()
)

if incremental_df.rdd.isEmpty():
    print("No new rows found in SQL Server for this run.")
else:
    incremental_df.write.format("delta").mode("append").save(bronze_path)

    clean_df = (
        incremental_df.select(
            trim(col("dataset_id")).alias("dataset_id"),
            trim(col("title")).alias("title"),
            trim(col("description")).alias("description"),
            trim(col("owner")).alias("owner"),
            trim(col("tags")).alias("tags"),
            trim(col("url")).alias("url"),
            to_timestamp(col("modified_at")).alias("modified_at"),
        )
        .dropDuplicates(["dataset_id"])
    )

    if silver_exists:
        existing_df = spark.read.format("delta").load(silver_path)
        combined_df = existing_df.unionByName(clean_df)
        window = Window.partitionBy("dataset_id").orderBy(col("modified_at").desc())
        latest_df = (
            combined_df.withColumn("rn", row_number().over(window))
            .filter(col("rn") == 1)
            .drop("rn")
        )
        latest_df.write.format("delta").mode("overwrite").save(silver_path)
    else:
        clean_df.write.format("delta").mode("overwrite").save(silver_path)
        silver_exists = True

if silver_exists:
    silver_df = spark.read.format("delta").load(silver_path)
    gold_df = (
        silver_df.groupBy("owner")
        .agg(
            count("dataset_id").alias("dataset_count"),
            spark_max("modified_at").alias("last_modified"),
        )
    )
    gold_df.write.format("delta").mode("overwrite").save(gold_path)
    write_preview(gold_df, preview_dir)

spark.stop()
