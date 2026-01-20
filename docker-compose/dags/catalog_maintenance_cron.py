from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="catalog_maintenance_cron",
    description="Tarea de mantenimiento con programacion Cron",
    start_date=datetime(2025, 1, 1),
    schedule="0 */6 * * *",
    catchup=False,
    tags=["catalogo", "cron"],
) as dag:
    log_cron_window = BashOperator(
        task_id="log_cron_window",
        bash_command=(
            "echo cron_run={{ ts }} && "
            "echo data_interval_start={{ data_interval_start }} && "
            "echo data_interval_end={{ data_interval_end }}"
        ),
    )

    log_cron_window