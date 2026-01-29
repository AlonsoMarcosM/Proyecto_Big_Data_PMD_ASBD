from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


with DAG(
    dag_id="pmd_streaming_updates_spark",
    description="Streaming Kafka con join batch y Delta medallion",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["spark", "streaming", "kafka", "delta"],
) as dag:
    submit_streaming = SparkSubmitOperator(
        task_id="submit_streaming_updates",
        conn_id="spark_default",
        application="/opt/spark-apps/pmd_streaming_updates.py",
        name="pmd_kafka_streaming_medallion",
        conf={
            "spark.hadoop.fs.s3a.endpoint": "http://minio:9000",
            "spark.hadoop.fs.s3a.path.style.access": "true",
            "spark.hadoop.fs.s3a.connection.ssl.enabled": "false",
            "spark.hadoop.fs.s3a.access.key": "minioadmin",
            "spark.hadoop.fs.s3a.secret.key": "minioadmin123",
            "spark.pyspark.python": "python3.11",
            "spark.pyspark.driver.python": "python3.11",
        },
        verbose=True,
    )

    submit_streaming
