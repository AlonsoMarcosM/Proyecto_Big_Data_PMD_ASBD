from __future__ import annotations

import ast
from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.sensors.external_task import ExternalTaskSensor


def _external_execution_date_fn(execution_date, **context):
    dag_run = context.get("dag_run")
    run_date = None
    if dag_run and dag_run.conf:
        run_date = dag_run.conf.get("run_date")
    if run_date:
        return datetime.strptime(run_date, "%Y-%m-%d")
    return execution_date.replace(hour=0, minute=0, second=0, microsecond=0)


def _parse_incomplete_ids(raw_value) -> list[str]:
    if not raw_value:
        return []
    if isinstance(raw_value, list):
        return [str(item) for item in raw_value]
    try:
        parsed = ast.literal_eval(str(raw_value))
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except (SyntaxError, ValueError):
        pass
    return [item.strip() for item in str(raw_value).split(",") if item.strip()]


with DAG(
    dag_id="catalog_streaming_events_test",
    description="Streaming simulado de eventos de catalogo",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["catalogo", "streaming"],
) as dag:
    start = EmptyOperator(task_id="start")

    wait_for_snapshot = ExternalTaskSensor(
        task_id="wait_for_snapshot",
        external_dag_id="catalog_batch_minutely_test",
        external_task_id="snapshot_ready",
        execution_date_fn=_external_execution_date_fn,
        allowed_states=["success"],
        failed_states=["failed", "skipped"],
        mode="reschedule",
        poke_interval=30,
        timeout=60 * 30,
    )

    @task
    def consume_events() -> list[dict]:
        # Simula la lectura desde Kafka
        return [
            {
                "event_time": "2025-12-18T10:35:00Z",
                "event_type": "dataset_updated",
                "dataset_id": "ds_001",
                "changed_field": "description",
                "new_value": "descripcion actualizada",
            },
            {
                "event_time": "2025-12-18T10:36:00Z",
                "event_type": "dataset_updated",
                "dataset_id": "ds_002",
                "changed_field": "tags",
                "new_value": "dcat,open,metadata",
            },
            {
                "event_time": "2025-12-18T10:37:00Z",
                "event_type": "dataset_updated",
                "dataset_id": "ds_003",
                "changed_field": "url",
                "new_value": "https://example.org/c-new",
            },
        ]

    @task
    def summarize_events(events: list[dict], incomplete_ids_raw: str | None) -> dict:
        incomplete_ids = _parse_incomplete_ids(incomplete_ids_raw)
        updated_datasets = sorted({event["dataset_id"] for event in events})

        last_update = {}
        for event in events:
            dataset_id = event["dataset_id"]
            event_dt = datetime.fromisoformat(event["event_time"].replace("Z", "+00:00"))
            if dataset_id not in last_update or event_dt > last_update[dataset_id][0]:
                last_update[dataset_id] = (event_dt, event["event_time"])
        last_update_per_dataset = {
            dataset_id: payload[1] for dataset_id, payload in last_update.items()
        }

        change_counts = {}
        for event in events:
            field = event["changed_field"]
            change_counts[field] = change_counts.get(field, 0) + 1
        most_frequent_change = None
        if change_counts:
            most_frequent_change = max(change_counts, key=change_counts.get)

        still_incomplete = set(incomplete_ids)
        for event in events:
            if (
                event["dataset_id"] in still_incomplete
                and event["changed_field"] == "description"
                and event["new_value"].strip()
            ):
                still_incomplete.remove(event["dataset_id"])

        return {
            "r1_updated_datasets": updated_datasets,
            "r2_last_update_per_dataset": last_update_per_dataset,
            "r3_most_frequent_change": most_frequent_change,
            "r4_still_incomplete": sorted(still_incomplete),
            "event_count": len(events),
        }

    @task
    def log_results(summary: dict) -> None:
        print("R1 updated datasets:", summary["r1_updated_datasets"])
        print("R2 last update per dataset:", summary["r2_last_update_per_dataset"])
        print("R3 most frequent change:", summary["r3_most_frequent_change"])
        print("R4 still incomplete:", summary["r4_still_incomplete"])
        print("Event count:", summary["event_count"])

    end = EmptyOperator(task_id="end")

    events = consume_events()
    summary = summarize_events(events, "{{ dag_run.conf.get('incomplete_dataset_ids') if dag_run else '' }}")
    result = log_results(summary)

    start >> wait_for_snapshot >> events
    events >> summary >> result >> end
