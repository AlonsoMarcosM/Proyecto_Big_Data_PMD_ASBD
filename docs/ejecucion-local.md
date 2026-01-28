# Guia de ejecucion local

## Requisitos previos

- Docker Desktop con soporte de Linux containers.
- Memoria recomendada: 8 GB o mas.
- Espacio libre: 10 GB o mas.

## Arranque del entorno

1) Entrar al directorio del entorno:

```bash
cd docker-compose
```

2) Verificar el archivo `.env` (requisito de Airflow):

- Windows (PowerShell):

```powershell
"AIRFLOW_UID=1000" | Set-Content -NoNewline .env
```

- Linux o WSL:

```bash
echo "AIRFLOW_UID=$(id -u)" > .env
```

3) Construir y levantar servicios:

```bash
docker compose up -d --build
```

4) Verificar estado:

```bash
docker compose ps
```

## Accesos utiles

- Airflow UI: http://localhost:8085 (airflow / airflow)
- Spark Master UI: http://localhost:8080
- MinIO Console: http://localhost:9001 (minioadmin / minioadmin123)
- Jupyter: http://localhost:8888
- Kafka externo: localhost:9094
- SQL Server: localhost:1433 (sa / Password1234%)
- OpenMetadata UI: http://localhost:8585 (admin@open-metadata.org / admin)

## Conexion de Spark en Airflow

Para los DAGs Spark se requiere una conexion llamada `spark_default`:

- Tipo: Spark
- Host: spark://spark-master:7077
- Extra: puede dejarse vacio para esta prueba

## Datos CSV (batch semiestructurado)

El pipeline CSV usa un fichero local montado en Spark:

- Ruta local: `pipelines/data/csv/catalogo_dataset.csv`
- Ruta en contenedor: `file:/opt/spark-data/csv/catalogo_dataset.csv`

Puedes editar ese CSV para simular nuevos datasets.

## Bucket de MinIO para la prueba Spark

Los pipelines usan el bucket `catalogo-datasets`. Si no existe:

1) Entrar a MinIO Console.
2) Crear bucket `catalogo-datasets`.

El contenedor `minio-mc` crea el bucket `spark` y tambien intenta crear `catalogo-datasets` al iniciar.

## DAGs incluidos

- `catalog_batch_minutely_test`: snapshot batch cada minuto y disparo de DAG de streaming simulado.
- `catalog_streaming_events_test`: streaming simulado con sensor `ExternalTaskSensor`.
- `pmd_batch_snapshot_spark`: batch estructurado incremental desde SQL Server (Delta medallion).
- `pmd_csv_batch_medallion_spark`: batch semiestructurado desde CSV (Delta medallion).
- `pmd_streaming_updates_spark`: streaming Kafka con join batch (Delta medallion, manual).
- `catalog_maintenance_cron`: ejemplo Cron con macro temporal.
- `spark_medallion_test`: ejemplo de SparkSubmitOperator basado en el material del profesor.

## Productor Kafka (fuera de Airflow)

- Servicio docker-compose: `kafka-producer`
- Arrancar productor: `docker compose up -d kafka-producer`
- Parar productor: `docker compose stop kafka-producer`
- Si levantas todo con `docker compose up -d --build`, el productor tambien arranca.
- El intervalo se ajusta en `docker-compose.yml` con `PRODUCER_INTERVAL_SECONDS`.

## Consejos de ejecucion

- En Airflow, despausar los DAGs antes de ejecutarlos.
- Para pruebas rapidas, levanta el servicio `kafka-producer` (publica en Kafka) y luego revisa `pmd_streaming_updates_spark`.
- Para el streaming, ejecuta primero el batch SQL para que exista el dataset Silver de referencia.
- Para limpiar todo: `docker compose down -v` (esto elimina volumenes).
- Para pruebas PMD, ver `docs/pruebas-pmd.md`.

