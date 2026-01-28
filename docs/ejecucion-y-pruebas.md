# Guia unica de ejecucion y pruebas (PMD + ASBD)

Este documento une `docs/ejecucion-local.md` y `docs/pruebas-pmd.md` en un flujo unico, desde cero, para levantar el entorno y validar los 3 pipelines PMD (batch SQL, batch CSV, streaming).

## 0) Requisitos previos

- Docker Desktop con soporte de Linux containers.
- Memoria recomendada: 8 GB o mas.
- Espacio libre: 10 GB o mas.

## 1) Arranque del entorno

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

## 2) Accesos utiles

- Airflow UI: http://localhost:8085 (airflow / airflow)
- Spark Master UI: http://localhost:8080
- MinIO Console: http://localhost:9001 (minioadmin / minioadmin123)
- Jupyter: http://localhost:8888
- Kafka externo: localhost:9094
- SQL Server: localhost:1433 (sa / Password1234%)
- OpenMetadata UI: http://localhost:8585 (admin@open-metadata.org / admin)

## 3) Conexion de Spark en Airflow (si ejecutas DAGs)

Crear una conexion llamada `spark_default`:

- Tipo: Spark
- Host: spark://spark-master:7077
- Extra: vacio

## 4) Datos CSV (batch semiestructurado)

El pipeline CSV usa un fichero local montado en Spark:

- Ruta local: `pipelines/data/csv/catalogo_dataset.csv`
- Ruta en contenedor: `file:/opt/spark-data/csv/catalogo_dataset.csv`

Puedes editar ese CSV para simular nuevos datasets.

## 5) Bucket de MinIO

Los pipelines usan el bucket `catalogo-datasets`. Si no existe:

1) Entrar a MinIO Console.
2) Crear bucket `catalogo-datasets`.

El contenedor `minio-mc` crea el bucket `spark` y tambien intenta crear `catalogo-datasets` al iniciar.

## 6) Preparar SQL Server (batch estructurado incremental)

1) Cargar el snapshot inicial:

```powershell
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "Password1234%" -i /opt/mssql-scripts/seed_dataset_snapshot.sql
```

2) Verificar el contenido:

```powershell
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "Password1234%" -Q "SELECT * FROM catalogo.dbo.dataset_snapshot;"
```

## 7) Preparar Kafka (streaming)

- El productor esta fuera de Airflow: el servicio `kafka-producer` publica automaticamente en el topic `dataset_updates`.
- El broker tiene `auto.create.topics.enable=true`, asi que el topic se crea al primer envio.

Arrancar productor (si no esta corriendo):

```powershell
docker compose up -d kafka-producer
```

## 8) Ejecutar batch estructurado (SQL Server) con Spark

Opcion A: desde Airflow

- Ejecutar el DAG `pmd_batch_snapshot_spark`.

Opcion B: desde el contenedor Spark

```powershell
docker exec spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_batch_snapshot.py
```

## 9) Ejecutar batch semiestructurado (CSV) con Spark

Opcion A: desde Airflow

- Ejecutar el DAG `pmd_csv_batch_medallion_spark`.

Opcion B: desde el contenedor Spark

```powershell
docker exec spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_csv_batch_medallion.py
```

## 10) Ejecutar streaming Kafka con Spark

Nota: primero ejecuta el batch SQL para que exista `silver/sqlserver/dataset_snapshot/` y el join funcione.

1) Lanzar el trabajo streaming (se queda en ejecucion):

```powershell
docker exec spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_streaming_updates.py
```

Opcion B (desde Airflow):
- Ejecutar el DAG `pmd_streaming_updates_spark` (se queda corriendo).

2) Confirmar que el productor esta enviando eventos:

```powershell
docker compose logs --tail 20 kafka-producer
```

## 11) Ver resultados en MinIO

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

## 12) Logs y comprobaciones rapidas

- Ver logs en Airflow: http://localhost:8085
- Logs del productor Kafka:

```powershell
docker compose logs --tail 50 kafka-producer
```

- Ver procesos streaming activos (opcional):

```powershell
docker exec spark-master ps -ef | findstr pmd_streaming_updates.py
```

## 13) Limpieza del entorno

Para parar y eliminar contenedores y volumenes:

```powershell
docker compose down -v
```

Si solo quieres parar el productor:

```powershell
docker compose stop kafka-producer
```
