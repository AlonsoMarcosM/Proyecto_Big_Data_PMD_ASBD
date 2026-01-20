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

- Linux o WSL:

```bash
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

- Windows (PowerShell):

```powershell
"AIRFLOW_UID=1000" | Set-Content -NoNewline .env
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

## Conexion de Spark en Airflow

Para el DAG `spark_medallion` se requiere una conexion llamada `spark_default`:

- Tipo: Spark
- Host: spark://spark-master:7077
- Extra: puede dejarse vacio para esta prueba

## Bucket de MinIO para la prueba Spark

El trabajo `spark_job.py` usa el bucket `hospital`. Si no existe:

1) Entrar a MinIO Console.
2) Crear bucket `hospital`.

El contenedor `minio-mc` crea el bucket `spark` y tambien intenta crear `hospital` al iniciar.

## DAGs incluidos

- `catalog_batch_daily`: snapshot batch diario, bifurcacion y disparo de DAG de streaming.
- `catalog_streaming_events`: streaming simulado con sensor `ExternalTaskSensor`.
- `catalog_maintenance_cron`: ejemplo Cron con macro temporal.
- `spark_medallion`: ejemplo de SparkSubmitOperator basado en el material del profesor.

## Consejos de ejecucion

- En Airflow, despausar los DAGs antes de ejecutarlos.
- Para pruebas rapidas, ejecute primero `catalog_batch_daily` y luego revise `catalog_streaming_events`.
- Para limpiar todo: `docker compose down -v` (esto elimina volumenes).