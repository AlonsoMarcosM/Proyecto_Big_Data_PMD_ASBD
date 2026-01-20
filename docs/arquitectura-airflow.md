# Orquestacion en Airflow para ASBD

## Objetivo

Implementar una orquestacion simple en Airflow que cumpla los requisitos de Arquitectura de Sistemas Big Data (ASBD):

- Tareas con distintas periodicidades, con al menos una macro temporal y al menos una programacion Cron.
- Pipeline con bifurcacion o tarea condicional.
- Compartir datos entre tareas mediante XCom o TaskFlow.
- Uso de al menos un sensor.
- Conexion entre dos DAG con mecanismo push o pull.

## DAGs incluidos

Los DAGs se encuentran en `docker-compose/dags`:

1) `catalog_batch_daily`
- Programacion: `@daily`.
- Macro temporal: la tarea `log_execution_date` imprime `{{ ds }}` y `{{ data_interval_end }}`.
- TaskFlow y XCom: `extract_snapshot` devuelve datos que consumen `normalize_snapshot` y `find_incomplete_metadata`.
- Bifurcacion: `branch_on_snapshot` decide si hay eventos y bifurca a `emit_streaming_events` o `skip_streaming_events`.
- Conexion a otro DAG: `trigger_streaming_dag` usa `TriggerDagRunOperator` para disparar `catalog_streaming_events` (push).

2) `catalog_streaming_events`
- Programacion: `None` (se ejecuta por disparo desde `catalog_batch_daily`).
- Sensor: `wait_for_snapshot` es un `ExternalTaskSensor` que espera a `snapshot_ready` del DAG `catalog_batch_daily`.
- Consumo de eventos y resumen: tareas simples en Python para simular streaming y calcular salidas de R1 a R4.

3) `catalog_maintenance_cron`
- Programacion Cron: `0 */6 * * *`.
- Tarea simple con macro temporal para registrar la ventana de ejecucion.

## Mapeo directo a requisitos

- Macro temporal: `catalog_batch_daily.log_execution_date` y `catalog_maintenance_cron.log_cron_window`.
- Cron: `catalog_maintenance_cron`.
- Bifurcacion: `catalog_batch_daily.branch_on_snapshot`.
- XCom o TaskFlow: retorno de datos en `catalog_batch_daily.extract_snapshot` y uso en tareas posteriores.
- Sensor: `catalog_streaming_events.wait_for_snapshot`.
- Conexion de DAGs: `catalog_batch_daily.trigger_streaming_dag`.

## Notas de simplicidad

- Las tareas simulan la lectura SQL y los eventos en streaming con datos pequenos en memoria.
- Se prioriza trazabilidad y demostracion sobre volumen real.
- Si se requiere procesamiento real con Spark, se incluye un DAG opcional `spark_medallion` basado en SparkSubmitOperator.