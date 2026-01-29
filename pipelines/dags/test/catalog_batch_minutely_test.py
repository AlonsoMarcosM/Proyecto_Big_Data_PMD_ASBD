from __future__ import annotations

from datetime import datetime, timezone

from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, get_current_context
from airflow.operators.trigger_dagrun import TriggerDagRunOperator


with DAG(
    dag_id="catalog_batch_minutely_test",
    description="Snapshot frecuente del catalogo de datasets y disparo del streaming",
    start_date=datetime(2025, 1, 1),
    schedule="* * * * *",
    catchup=False,
    tags=["catalogo", "batch"],
) as dag:
    @task
    def extract_snapshot() -> dict:
        # Simula lectura desde SQL Server
        datasets = [
            {
                "dataset_id": "ds_001",
                "title": "catalogo_a",
                "description": "",
                "owner": "equipo_a",
                "tags": "open,metadata",
                "url": "https://example.org/a",
            },
            {
                "dataset_id": "ds_002",
                "title": "catalogo_b",
                "description": "metadatos basicos",
                "owner": "equipo_b",
                "tags": "dcat,open",
                "url": "https://example.org/b",
            },
            {
                "dataset_id": "ds_003",
                "title": "catalogo_c",
                "description": "metadatos base",
                "owner": "equipo_c",
                "tags": "catalogo",
                "url": "https://example.org/c",
            },
        ]
        return {"datasets": datasets, "dataset_count": len(datasets)}

    @task
    def normalize_snapshot(snapshot: dict) -> dict:
        normalized = []
        for item in snapshot["datasets"]:
            normalized.append(
                {
                    "dataset_id": item["dataset_id"].strip(),
                    "title": item["title"].strip(),
                    "description": item["description"].strip(),
                    "owner": item["owner"].strip(),
                    "tags": item["tags"].strip(),
                    "url": item["url"].strip(),
                }
            )
        return {"datasets": normalized, "dataset_count": len(normalized)}

    @task
    def find_incomplete_metadata(snapshot: dict) -> list[str]:
        return [
            item["dataset_id"]
            for item in snapshot["datasets"]
            if not item["description"]
        ]

    def branch_on_snapshot(**context) -> str:
        snapshot = context["ti"].xcom_pull(task_ids="normalize_snapshot")
        if snapshot and snapshot.get("dataset_count", 0) > 0:
            return "trigger_streaming_dag"
        return "skip_streaming_events"

    decide_branch = BranchPythonOperator(
        task_id="branch_on_snapshot",
        python_callable=branch_on_snapshot,
    )

    skip_streaming_events = EmptyOperator(task_id="skip_streaming_events")

    snapshot_ready = EmptyOperator(task_id="snapshot_ready")

    @task
    def build_trigger_conf(incomplete_ids: list[str]) -> dict:
        context = get_current_context()
        logical_date = context.get("logical_date") or context.get("data_interval_end")
        if logical_date:
            run_date = logical_date.isoformat()
        else:
            run_date = datetime.now(timezone.utc).isoformat()
        return {
            "run_date": run_date,
            "incomplete_dataset_ids": incomplete_ids,
        }

    end = EmptyOperator(task_id="end", trigger_rule="none_failed_min_one_success")

    snapshot = extract_snapshot()
    normalized = normalize_snapshot(snapshot)
    incomplete = find_incomplete_metadata(normalized)

    trigger_streaming_dag = TriggerDagRunOperator(
        task_id="trigger_streaming_dag",
        trigger_dag_id="catalog_streaming_events_test",
        conf=build_trigger_conf(incomplete),
        wait_for_completion=False,
    )

    snapshot >> normalized >> incomplete >> snapshot_ready
    snapshot_ready >> decide_branch

    decide_branch >> trigger_streaming_dag >> end
    decide_branch >> skip_streaming_events >> end
