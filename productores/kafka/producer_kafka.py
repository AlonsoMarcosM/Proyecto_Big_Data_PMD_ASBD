import json
import os
import time
from datetime import datetime, timezone

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable


def _base_datasets() -> list[dict]:
    return [
        {
            "dataset_id": "ds_001",
            "title": "catalogo_a",
            "description": "",
            "tags": "open,metadata",
            "url": "https://example.org/a",
        },
        {
            "dataset_id": "ds_002",
            "title": "catalogo_b",
            "description": "metadatos basicos",
            "tags": "dcat,open",
            "url": "https://example.org/b",
        },
        {
            "dataset_id": "ds_003",
            "title": "catalogo_c",
            "description": "metadatos base",
            "tags": "catalogo",
            "url": "https://example.org/c",
        },
    ]


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> None:
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic = os.getenv("KAFKA_TOPIC", "dataset_updates")
    interval_seconds = float(os.getenv("PRODUCER_INTERVAL_SECONDS", "10"))

    producer = None
    while producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda payload: json.dumps(payload).encode("utf-8"),
            )
        except NoBrokersAvailable:
            print("[producer] Kafka no disponible, reintentando en 3s...")
            time.sleep(3)

    datasets = _base_datasets()
    cycle = 0
    print(
        f"[producer] starting -> servers={bootstrap_servers} "
        f"topic={topic} every={interval_seconds}s"
    )

    try:
        while True:
            event_time = _now_utc_iso()
            events = []
            for item in datasets:
                if cycle % 3 == 0:
                    changed_field = "description"
                    new_value = "descripcion actualizada"
                elif cycle % 3 == 1:
                    changed_field = "tags"
                    new_value = f"{item['tags']},metadata"
                else:
                    changed_field = "url"
                    new_value = f"{item['url']}?v={cycle}"

                event = {
                    "event_time": event_time,
                    "event_type": "dataset_updated",
                    "dataset_id": item["dataset_id"],
                    "changed_field": changed_field,
                    "new_value": new_value,
                }
                producer.send(topic, value=event)
                events.append(event)

            producer.flush()
            print(f"[producer] sent {len(events)} events at {event_time}")
            cycle += 1
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("[producer] stopping...")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
