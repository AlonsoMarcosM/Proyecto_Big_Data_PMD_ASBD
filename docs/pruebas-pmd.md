# Pruebas y validacion del pipeline PMD

## Preparar SQL Server (batch estructurado incremental)

1) Entrar al directorio del entorno:

```powershell
cd docker-compose
```

2) Cargar el snapshot inicial en SQL Server:

```powershell
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "Password1234%" -i /opt/mssql-scripts/seed_dataset_snapshot.sql
```

3) Verificar el contenido:

```powershell
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "Password1234%" -Q "SELECT * FROM catalogo.dbo.dataset_snapshot;"
```

## Preparar CSV (batch semiestructurado)

- El fichero de entrada es `pipelines/data/csv/catalogo_dataset.csv`.
- Puedes editarlo para simular nuevos datasets (cada ejecucion reescribe bronze/silver/gold).

## Preparar Kafka (streaming)

- El productor esta fuera de Airflow: el servicio `kafka-producer` publica automaticamente en el topic `dataset_updates`.
- El broker tiene `auto.create.topics.enable=true`, asi que el topic se crea al primer envio.

## Ejecutar batch estructurado (SQL Server) con Spark

Opcion A: desde Airflow

- Crear la conexion `spark_default` si no existe (host `spark://spark-master:7077`).
- Ejecutar el DAG `pmd_batch_snapshot_spark`.

Opcion B: desde el contenedor Spark

```powershell
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_batch_snapshot.py
```

## Ejecutar batch semiestructurado (CSV) con Spark

Opcion A: desde Airflow

- Ejecutar el DAG `pmd_csv_batch_medallion_spark`.

Opcion B: desde el contenedor Spark

```powershell
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_csv_batch_medallion.py
```

## Ejecutar streaming Kafka con Spark

Nota: primero ejecuta el batch SQL para que exista `silver/sqlserver/dataset_snapshot/` y el join funcione.

1) Lanzar el trabajo streaming (se queda en ejecucion):

```powershell
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_streaming_updates.py
```

Opcion B (desde Airflow):
- Ejecutar el DAG `pmd_streaming_updates_spark` (se queda corriendo).

2) Arrancar el servicio `kafka-producer` para que publique eventos automaticamente:

```powershell
docker compose up -d kafka-producer
```

Si ya levantaste todo el stack, el productor puede estar corriendo.

## Ver resultados en MinIO

1) Abrir MinIO Console: http://localhost:9001
2) Entrar con `minioadmin / minioadmin123`.
3) Ver los prefijos del bucket `catalogo-datasets`:

- `bronze/sqlserver/dataset_snapshot/`
- `silver/sqlserver/dataset_snapshot/`
- `gold/sqlserver/datasets_by_owner/`
- `bronze/csv/catalogo_dataset/`
- `silver/csv/catalogo_dataset/`
- `gold/csv/datasets_by_category/`
- `bronze/kafka/dataset_updates/`
- `silver/kafka/dataset_updates/`
- `gold/kafka/dataset_updates_agg/`
- `checkpoints/` (subcarpetas de streaming)

## Ver logs en Airflow

- Airflow UI: http://localhost:8085
- Logs de los DAGs `pmd_batch_snapshot_spark`, `pmd_csv_batch_medallion_spark` y `pmd_streaming_updates_spark`.

