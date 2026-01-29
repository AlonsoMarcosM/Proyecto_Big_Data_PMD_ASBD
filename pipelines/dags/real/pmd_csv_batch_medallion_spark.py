from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


with DAG(
    dag_id="pmd_csv_batch_medallion_spark",
    description="Batch CSV semiestructurado con Delta medallion",
    start_date=datetime(2025, 1, 1),
    schedule="0 2 * * *",
    catchup=False,
    tags=["pmd", "spark", "batch", "csv", "delta"],
) as dag:
    submit_csv_batch = SparkSubmitOperator(
        task_id="submit_csv_batch",
        conn_id="spark_default",
        application="/opt/spark-apps/pmd_csv_batch_medallion.py",
        name="pmd_csv_batch_medallion",
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

    submit_csv_batch
