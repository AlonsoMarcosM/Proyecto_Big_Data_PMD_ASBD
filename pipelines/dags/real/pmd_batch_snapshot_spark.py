from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


with DAG(
    dag_id="pmd_batch_snapshot_spark",
    description="Batch estructurado incremental (SQL Server) con Delta medallion",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["pmd", "spark", "batch", "delta"],
) as dag:
    submit_batch_snapshot = SparkSubmitOperator(
        task_id="submit_batch_snapshot",
        conn_id="spark_default",
        application="/opt/spark-apps/pmd_batch_snapshot.py",
        name="pmd_sqlserver_medallion",
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

    submit_batch_snapshot
