# Arquitectura PMD (pipeline y flujo de datos)

## Objetivo

Describir la arquitectura de PMD con 3 pipelines de ingesta (batch estructurado, batch semiestructurado y streaming) y una arquitectura Medallion (Bronze/Silver/Gold) sobre Delta Lake.

## Componentes

- SQL Server: fuente estructurada para el batch incremental.
- CSV local: fuente semiestructurada para batch.
- Kafka: broker de eventos JSON para streaming.
- Productor Kafka: servicio Python fuera de Airflow (`kafka-producer`).
- Spark: motor de procesamiento batch y streaming con Delta Lake.
- MinIO: almacenamiento S3 local para Bronze/Silver/Gold.
- Airflow: orquestacion de los pipelines (detalle en `docs/arquitectura-airflow.md`).

Codigo base en `docker-compose/`:

- SQL seed: `docker-compose/sql/seed_dataset_snapshot.sql`.
- CSV: `pipelines/data/csv/catalogo_dataset.csv`.
- Productor Kafka: `productores/kafka/producer_kafka.py`.
- Spark batch SQL: `pipelines/spark-apps/pmd_batch_snapshot.py`.
- Spark batch CSV: `pipelines/spark-apps/pmd_csv_batch_medallion.py`.
- Spark streaming Kafka: `pipelines/spark-apps/pmd_streaming_updates.py`.
- DAGs Spark: `pipelines/dags/real/`.

## Pipeline 1: Batch estructurado incremental (SQL Server)

- Bronze: ingesta incremental desde `catalogo.dbo.dataset_snapshot`.
- Silver: limpieza y upsert por `dataset_id`.
- Gold: agregado por `owner` con conteos y ultima modificacion.

Rutas:
- `s3a://catalogo-datasets/bronze/sqlserver/dataset_snapshot/`
- `s3a://catalogo-datasets/silver/sqlserver/dataset_snapshot/`
- `s3a://catalogo-datasets/gold/sqlserver/datasets_by_owner/`

## Pipeline 2: Batch semiestructurado (CSV)

- Bronze: CSV crudo.
- Silver: parseo de JSON embebido (`extras_json`), tags a array, limpieza.
- Gold: agregado por `category` y conteo de owners.

Rutas:
- `s3a://catalogo-datasets/bronze/csv/catalogo_dataset/`
- `s3a://catalogo-datasets/silver/csv/catalogo_dataset/`
- `s3a://catalogo-datasets/gold/csv/datasets_by_category/`

## Pipeline 3: Streaming Kafka + join con batch

- Bronze: eventos crudos de Kafka.
- Silver: eventos parseados y normalizados.
- Gold: agregacion por ventana (1 minuto) con watermark y join con batch (SQL Silver).

Rutas:
- `s3a://catalogo-datasets/bronze/kafka/dataset_updates/`
- `s3a://catalogo-datasets/silver/kafka/dataset_updates/`
- `s3a://catalogo-datasets/gold/kafka/dataset_updates_agg/`
- `s3a://catalogo-datasets/checkpoints/`

## Planificacion de ejecucion

- Batch SQL: `@daily` (demo, puede ejecutarse manualmente).
- Batch CSV: cron `0 2 * * *`.
- Streaming Kafka: manual (job continuo) y productor con intervalo configurable.

## Notas clave

- Delta Lake se usa en todas las capas (Bronze/Silver/Gold).
- El streaming usa ventanas de 1 minuto y watermark de 5 minutos.
- El streaming enriquece eventos con datos batch (join con Silver SQL).

