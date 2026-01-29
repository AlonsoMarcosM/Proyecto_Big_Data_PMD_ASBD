# Guia unica de ejecucion y pruebas (PMD + ASBD)

Este documento une `docs/ejecucion-local.md` y `docs/pruebas-pmd.md` en un flujo unico, desde cero, para levantar el entorno y validar los 3 pipelines PMD (batch SQL, batch CSV, streaming).

## 0) Requisitos previos

- Docker Desktop con soporte de Linux containers.
- Memoria recomendada: 8 GB o mas.
- Espacio libre: 10 GB o mas.

## 1) Arranque del entorno

Si vienes de una ejecucion anterior, limpia primero el stack:

```powershell
docker compose down -v
```

Nota: si Docker responde con error 500 en PowerShell, reinicia Docker Desktop y vuelve a ejecutar el comando.
Si aparecen contenedores huerfanos (por ejemplo, de versiones anteriores), usa:

```powershell
docker compose down -v --remove-orphans
```

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

Verificar que el topic existe:

```powershell
docker exec -i kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list
```

## 8) Ejecutar batch estructurado (SQL Server) con Spark

Recomendacion: ejecutar los jobs de Spark uno a uno (no simultaneos) para evitar picos de CPU/RAM.
Flujo sugerido por pipeline: **ejecucion -> test -> visualizacion -> apagado -> siguiente pipeline**.


### Bloques rapidos por pipeline

Batch SQL (Spark):

```powershell
docker exec spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_batch_snapshot.py
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "Password1234%" -Q "SELECT COUNT(*) FROM catalogo.dbo.dataset_snapshot;"
docker exec -i minio-mc mc ls local/catalogo-datasets/gold/sqlserver/
```

Batch CSV (Spark):

```powershell
docker exec spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_csv_batch_medallion.py
docker exec -i minio-mc mc ls local/catalogo-datasets/gold/csv/
```

Streaming Kafka (Spark):

```powershell
docker exec spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_streaming_updates.py
docker exec -i kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic dataset_updates --from-beginning --max-messages 5
docker exec -i minio-mc mc ls local/catalogo-datasets/gold/kafka/
```

Opcion A: desde Airflow

- Ejecutar el DAG `pmd_batch_snapshot_spark`.

Opcion B: desde el contenedor Spark

```powershell
docker exec spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_batch_snapshot.py
```

Test rapido (opcional):

```powershell
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "Password1234%" -Q "SELECT COUNT(*) FROM catalogo.dbo.dataset_snapshot;"
```

Visualizacion (MinIO):

1) Ir a http://localhost:9001
2) Bucket `catalogo-datasets`
3) Prefijos:

- `bronze/sqlserver/dataset_snapshot/`
- `silver/sqlserver/dataset_snapshot/`
- `gold/sqlserver/datasets_by_owner/`

Apagado del job:

- Si se lanzo desde Airflow, marcar como terminado cuando acabe.
- Si se lanzo desde `spark-submit`, el job termina solo.

## 9) Ejecutar batch semiestructurado (CSV) con Spark

Opcion A: desde Airflow

- Ejecutar el DAG `pmd_csv_batch_medallion_spark`.

Opcion B: desde el contenedor Spark

```powershell
docker exec spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_csv_batch_medallion.py
```

Test rapido (opcional):

```powershell
docker exec -i spark-master ls -la /opt/spark-data/csv
```

Visualizacion (MinIO):

- `bronze/csv/catalogo_dataset/`
- `silver/csv/catalogo_dataset/`
- `gold/csv/datasets_by_category/`

Apagado del job:

- Si se lanzo desde Airflow, marcar como terminado cuando acabe.
- Si se lanzo desde `spark-submit`, el job termina solo.

## 10) Ejecutar streaming Kafka con Spark

Nota: primero ejecuta el batch SQL para que exista `silver/sqlserver/dataset_snapshot/` y el join funcione.
El streaming tiene limites de carga (offsets por micro-batch y particiones) para reducir consumo.

1) Lanzar el trabajo streaming (se queda en ejecucion):

```powershell
docker exec spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_streaming_updates.py
```

Opcion B (desde Airflow):
- Ejecutar el DAG `pmd_streaming_updates_spark` (se queda corriendo).

2) Confirmar que el productor esta enviando eventos:

```powershell
docker exec -i kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic dataset_updates --from-beginning --max-messages 5
```

3) Visualizacion (MinIO):

- `bronze/kafka/dataset_updates/`
- `silver/kafka/dataset_updates/`
- `gold/kafka/dataset_updates_agg/`
- `checkpoints/` (streaming)

Apagado del job streaming:

```powershell
docker exec spark-master pkill -f pmd_streaming_updates.py
```

Si no se detiene, puedes parar Spark:

```powershell
docker compose stop spark-master spark-worker-1 spark-worker-2
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

## 11.1) Previews locales (visualizacion rapida)

Al terminar cada pipeline, se generan previews automaticamente en
`docs/visualizaciones/` (CSV y JSONL) con las salidas Gold.
Puedes abrirlos en VS Code con extensiones tipo "Rainbow CSV".

## 12) Logs y comprobaciones rapidas

- Ver logs en Airflow: http://localhost:8085
- Logs del productor Kafka:

```powershell
docker compose logs --tail 50 kafka-producer
```

- Ver procesos streaming activos (opcional):

```powershell
docker exec spark-master ps -ef | grep pmd_streaming_updates.py
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
