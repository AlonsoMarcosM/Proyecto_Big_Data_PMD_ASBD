from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.operators.python import get_current_context


with DAG(
    dag_id="catalog_maintenance_cron",
    description="Tarea de mantenimiento con programacion Cron",
    start_date=datetime(2025, 1, 1),
    schedule="0 */6 * * *",
    catchup=False,
    tags=["catalogo", "cron"],
) as dag:
    @task
    def log_cron_window() -> None:
        context = get_current_context()
        print("cron_run:", context.get("logical_date"))
        print("data_interval_start:", context.get("data_interval_start"))
        print("data_interval_end:", context.get("data_interval_end"))

    log_cron_window()
