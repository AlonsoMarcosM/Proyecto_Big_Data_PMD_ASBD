# Orquestacion en Airflow para ASBD

## Objetivo

Implementar una orquestacion simple en Airflow que cumpla los requisitos de Arquitectura de Sistemas Big Data (ASBD):

- Tareas con distintas periodicidades, con al menos una macro temporal y al menos una programacion Cron.
- Pipeline con bifurcacion o tarea condicional.
- Compartir datos entre tareas mediante XCom o TaskFlow.
- Uso de al menos un sensor.
- Conexion entre dos DAG con mecanismo push o pull.

## DAGs incluidos

Los DAGs se encuentran en `pipelines/dags` (organizados por carpetas `test/`, `real/` y `maintenance/`):

1) `catalog_batch_minutely_test`
- Programacion: `* * * * *` (cada minuto, para demo de streaming).
- Macro temporal: la tarea `log_execution_date` imprime `{{ ds }}` y `{{ data_interval_end }}`.
- TaskFlow y XCom: `extract_snapshot` devuelve datos que consumen `normalize_snapshot` y `find_incomplete_metadata`.
- Bifurcacion: `branch_on_snapshot` decide si hay snapshot y bifurca a `trigger_streaming_dag` o `skip_streaming_events`.
- Conexion a otro DAG: `trigger_streaming_dag` usa `TriggerDagRunOperator` para disparar `catalog_streaming_events_test` (push).

2) `catalog_streaming_events_test`
- Programacion: `None` (se ejecuta por disparo desde `catalog_batch_minutely_test`).
- Sensor: `wait_for_snapshot` es un `ExternalTaskSensor` que espera a `snapshot_ready` del DAG `catalog_batch_minutely_test`.
- Consumo de eventos y resumen: tareas simples en Python para simular streaming y calcular salidas de R1 a R4.

3) `pmd_batch_snapshot_spark`
- Lanza el batch SQL incremental con Spark (Delta medallion).
- Programacion: `@daily` (puede ejecutarse manualmente para demo).

4) `pmd_csv_batch_medallion_spark`
- Lanza el batch CSV semiestructurado con Spark (Delta medallion).
- Programacion: `0 2 * * *`.

5) `pmd_streaming_updates_spark`
- Lanza el consumer real con Spark Structured Streaming (Kafka -> Delta medallion).
- Programacion: `None` (manual).
- Nota: el job queda corriendo mientras se consume streaming.

6) `catalog_maintenance_cron`
- Programacion Cron: `0 */6 * * *`.
- Tarea simple con macro temporal para registrar la ventana de ejecucion.

7) `spark_medallion_test`
- DAG opcional de ejemplo (Spark + Delta).

## Mapeo directo a requisitos

- Macro temporal: `catalog_batch_minutely_test.log_execution_date` y `catalog_maintenance_cron.log_cron_window`.
- Cron: `catalog_maintenance_cron`.
- Bifurcacion: `catalog_batch_minutely_test.branch_on_snapshot`.
- XCom o TaskFlow: retorno de datos en `catalog_batch_minutely_test.extract_snapshot` y uso en tareas posteriores.
- Sensor: `catalog_streaming_events_test.wait_for_snapshot`.
- Conexion de DAGs: `catalog_batch_minutely_test.trigger_streaming_dag`.
- DAGs reales con Spark: `pmd_batch_snapshot_spark`, `pmd_csv_batch_medallion_spark` y `pmd_streaming_updates_spark`.

## Notas de simplicidad

- Las tareas de pruebas simulan la lectura SQL en memoria; el productor Kafka es un servicio externo (`kafka-producer`) fuera de Airflow.
- Se prioriza trazabilidad y demostracion sobre volumen real.
- Si se requiere procesamiento real con Spark, se incluyen DAGs reales en `dags/real`.

