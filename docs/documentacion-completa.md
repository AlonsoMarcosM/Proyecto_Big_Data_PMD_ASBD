# Documentacion Completa del Proyecto (PMD + ASBD)

Este documento explica el proyecto de forma integral: arquitectura, servicios, datos, codigo y como ejecutar una demo end-to-end.
La intencion es que puedas entender que hace cada pieza sin leer todo el repositorio a ciegas.

---

## 0) Que es este proyecto

Este repositorio implementa un mini-producto Big Data reproducible con Docker Compose. El escenario es un catalogo de datasets que se mantiene vivo con tres pipelines y arquitectura Medallion (Delta Lake):

- Batch estructurado incremental (SQL Server).
- Batch semiestructurado (CSV).
- Streaming Kafka con join con batch.

Ademas, Airflow se usa para orquestacion (requisitos ASBD).

---

## 1) Estructura del repositorio (mapa rapido)

- `docker-compose/docker-compose.yml`: composicion de servicios (Airflow, Spark, Kafka, SQL Server, MinIO, etc.).
- `pipelines/dags/`: DAGs de Airflow (organizados en `real/`, `test/`, `maintenance/`).
- `pipelines/spark-apps/`: jobs Spark (batch y streaming, Delta Lake).
- `pipelines/data/`: datos locales (CSV) montados en Spark.
- `docker-compose/sql/`: scripts SQL (seed inicial del snapshot).
- `productores/kafka/`: productor Python y ejemplos de eventos en formato `.jsonl`.
- `docs/`: documentacion del proyecto (esta guia y el resto).

---

## 2) Servicios, nombres DNS internos y puertos

Cuando levantas el entorno con Docker Compose, hay dos mundos:

- Host (tu maquina): accedes por `localhost:PUERTO`.
- Red Docker (`spark-net`): los contenedores se ven por nombre de servicio/contenedor (ej. `kafka:9092`, `minio:9000`).

Puertos principales (host):

- Airflow UI (moderna, Airflow 3.x): `http://localhost:8085` (airflow / airflow)
- Spark Master UI: `http://localhost:8080`
- MinIO Console: `http://localhost:9001` (minioadmin / minioadmin123)
- MinIO S3 API: `http://localhost:9000`
- Kafka externo (host): `localhost:9094`
- SQL Server: `localhost:1433` (sa / Password1234%)

Conexiones internas (entre contenedores):

- Kafka interno: `kafka:9092`
- MinIO interno: `http://minio:9000`
- Spark Master interno: `spark://spark-master:7077`
- SQL Server interno (desde otros contenedores en la red): `sqlserver:1433`

---

## 3) Datos del proyecto: que existe y donde vive

### 3.1 SQL Server (batch estructurado incremental)

El estado inicial del catalogo vive en SQL Server.
El script `docker-compose/sql/seed_dataset_snapshot.sql` crea:

- Base de datos: `catalogo`
- Esquema: `dbo`
- Tabla: `dataset_snapshot`

Tabla completa:

- `catalogo.dbo.dataset_snapshot`

Columnas (resumen):

- `dataset_id` (PK)
- `title`
- `description`
- `owner`
- `tags`
- `url`
- `modified_at`

Este dataset se usa como fuente batch incremental.

### 3.2 CSV (batch semiestructurado)

El CSV local vive en:

- `pipelines/data/csv/catalogo_dataset.csv`

El fichero incluye una columna JSON (`extras_json`) para simular semiestructura.

### 3.3 Kafka (eventos streaming)

Kafka se usa como broker de eventos para cambios incrementales del catalogo.
El topic es:

- `dataset_updates`

El contrato minimo de evento (esquema) es:

- `event_time` (string ISO, UTC)
- `event_type` (string, por ejemplo `dataset_updated`)
- `dataset_id` (string)
- `changed_field` (string)
- `new_value` (string)

Nota importante:
- El batch y los eventos no tienen por que contener lo mismo.
- Lo obligatorio para correlacionar es que `dataset_id` coincida.

### 3.4 MinIO (almacenamiento)

MinIO actua como un S3 local. El bucket principal para el catalogo es:

- `catalogo-datasets`

Rutas usadas por los jobs (Bronze/Silver/Gold):

- SQL Server:
  - `s3a://catalogo-datasets/bronze/sqlserver/dataset_snapshot/`
  - `s3a://catalogo-datasets/silver/sqlserver/dataset_snapshot/`
  - `s3a://catalogo-datasets/gold/sqlserver/datasets_by_owner/`
- CSV:
  - `s3a://catalogo-datasets/bronze/csv/catalogo_dataset/`
  - `s3a://catalogo-datasets/silver/csv/catalogo_dataset/`
  - `s3a://catalogo-datasets/gold/csv/datasets_by_category/`
- Kafka:
  - `s3a://catalogo-datasets/bronze/kafka/dataset_updates/`
  - `s3a://catalogo-datasets/silver/kafka/dataset_updates/`
  - `s3a://catalogo-datasets/gold/kafka/dataset_updates_agg/`
- Checkpoints:
  - `s3a://catalogo-datasets/checkpoints/`

Ademas existe un bucket `spark` para ejemplos (y es configurado en `minio-mc`).

---

## 4) Jobs Spark: que hacen y como estan implementados

Los jobs Spark estan en `pipelines/spark-apps/`.

### 4.1 Configuracion comun (S3A hacia MinIO)

Tanto batch como streaming configuran:

- Endpoint S3A: `http://minio:9000`
- Credenciales: `minioadmin` / `minioadmin123`
- `path.style.access=true` y `ssl.enabled=false` (tipico para MinIO local)
- Delta Lake con `spark.sql.extensions` y `spark.sql.catalog.spark_catalog`

### 4.2 Batch SQL incremental: `pipelines/spark-apps/pmd_batch_snapshot.py`

Objetivo:
- Leer `catalogo.dbo.dataset_snapshot` desde SQL Server de forma incremental y escribir Bronze/Silver/Gold en Delta.

Claves:
- Bronze: append del incremental.
- Silver: upsert por `dataset_id`.
- Gold: agregacion por `owner`.

### 4.3 Batch CSV semiestructurado: `pipelines/spark-apps/pmd_csv_batch_medallion.py`

Objetivo:
- Leer CSV local, parsear JSON embebido y escribir Bronze/Silver/Gold en Delta.

Claves:
- Bronze: CSV crudo.
- Silver: parseo de `extras_json`, tags a array y limpieza.
- Gold: agregacion por `category`.

### 4.4 Streaming Kafka: `pipelines/spark-apps/pmd_streaming_updates.py`

Objetivo:
- Consumir mensajes Kafka, escribir Bronze/Silver en Delta y generar Gold con ventanas.

Claves:
- Bronze: payload crudo.
- Silver: eventos parseados.
- Gold: agregacion por ventana (1 min) con watermark (5 min).
- Join con datos batch (Silver SQL) para enriquecer eventos.
Nota:
- Ejecuta primero el batch SQL para que exista `silver/sqlserver/dataset_snapshot/`.

### 4.5 Job extra (material / ejemplo): `pipelines/spark-apps/spark_job_test.py`

Este job es de ejemplo (Delta/medallion) y tambien usa el bucket `catalogo-datasets`.
No es necesario para la demo PMD, pero queda como material adicional.
Se ejecuta desde el DAG `spark_medallion_test`.

---

## 5) Airflow: DAGs y responsabilidades

Los DAGs estan en `pipelines/dags/`. Importante:

- Airflow 3.x separa componentes; en este compose la UI sale por el servicio `airflow-apiserver` (host `localhost:8085`).
- Por defecto los DAGs se crean pausados; hay que despausarlos en la UI.
- Los DAGs estan organizados en subcarpetas: `dags/real`, `dags/test` y `dags/maintenance`.

### 5.1 Productor real de eventos Kafka (fuera de Airflow)

Archivo:
- `productores/kafka/producer_kafka.py`

Servicio docker-compose:
- `kafka-producer` (usa `docker-compose/dockerfile-producer`)

Que hace:
- Publica eventos en Kafka topic `dataset_updates` de forma continua (intervalo configurable).
- El intervalo se controla con `PRODUCER_INTERVAL_SECONDS` (default 10s).

Por que asi:
- El productor queda fuera de Airflow (mas realista).
- Airflow se centra en orquestar batch/consumo y no en generar eventos.

### 5.2 DAG batch + disparo de streaming simulado: `catalog_batch_minutely_test`

Archivo:
- `pipelines/dags/test/catalog_batch_minutely_test.py`

Que hace:
- Corre cada minuto (modo demo) y simula un snapshot (en memoria) para cumplir requisitos ASBD:
  - Macro temporal (`{{ ds }}` y `{{ data_interval_end }}`)
  - TaskFlow / XCom
  - Bifurcacion (BranchPythonOperator)
  - Trigger de otro DAG (push)

### 5.3 DAG streaming simulado: `catalog_streaming_events_test`

Archivo:
- `pipelines/dags/test/catalog_streaming_events_test.py`

Que hace:
- Se ejecuta solo por trigger (no tiene schedule).
- Incluye un `ExternalTaskSensor` que espera una tarea del DAG `catalog_batch_minutely_test`.
- Consume una lista de eventos simulados (en memoria) y calcula resultados R1-R4.

### 5.4 DAG cron ejemplo: `catalog_maintenance_cron`

Archivo:
- `pipelines/dags/maintenance/catalog_maintenance_cron.py`

Que hace:
- Ejemplo de schedule cron (cada 6 horas) para cumplir requisito de cron.

### 5.5 DAG batch SQL (medallion): `pmd_batch_snapshot_spark`

Archivo:
- `pipelines/dags/real/pmd_batch_snapshot_spark.py`

Que hace:
- Ejecuta el batch SQL incremental (`pmd_batch_snapshot.py`) con SparkSubmitOperator.

### 5.6 DAG batch CSV (medallion): `pmd_csv_batch_medallion_spark`

Archivo:
- `pipelines/dags/real/pmd_csv_batch_medallion_spark.py`

Que hace:
- Ejecuta el batch CSV (`pmd_csv_batch_medallion.py`) con SparkSubmitOperator.

### 5.7 DAG streaming Kafka (medallion): `pmd_streaming_updates_spark`

Archivo:
- `pipelines/dags/real/pmd_streaming_updates_spark.py`

Que hace:
- Lanza el consumer streaming (`pmd_streaming_updates.py`) con SparkSubmitOperator.
- El job queda corriendo mientras haya streaming.

---

## 6) Como ejecutar la demo (paso a paso)

### 6.1 Levantar todo

En PowerShell:

```powershell
cd docker-compose
"AIRFLOW_UID=1000" | Set-Content -NoNewline .env
docker compose up -d --build
```

### 6.2 Preparar SQL Server (seed)

IMPORTANTE:
- En SQL Server 2022 container, `sqlcmd` esta en `/opt/mssql-tools18/bin/sqlcmd`.
- Con `sqlcmd` 18, usa `-C` para confiar en el certificado.

Ejecutar seed:

```powershell
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd `
  -C -S localhost -U sa -P "Password1234%" `
  -i /opt/mssql-scripts/seed_dataset_snapshot.sql
```

Verificar:

```powershell
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd `
  -C -S localhost -U sa -P "Password1234%" `
  -Q "SELECT * FROM catalogo.dbo.dataset_snapshot;"
```

### 6.3 Ejecutar batch SQL (medallion) con Spark

Opcion A (directo en contenedor Spark):

```powershell
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_batch_snapshot.py
```

Opcion B (desde Airflow):
- Ejecutar el DAG `pmd_batch_snapshot_spark`.

### 6.4 Ejecutar batch CSV (medallion) con Spark

Opcion A (directo en contenedor Spark):

```powershell
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_csv_batch_medallion.py
```

Opcion B (desde Airflow):
- Ejecutar el DAG `pmd_csv_batch_medallion_spark`.

### 6.5 Ejecutar streaming (consumer) con Spark

Este job se queda corriendo:

```powershell
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark-apps/pmd_streaming_updates.py
```

Opcion alternativa (desde Airflow):
- Ejecutar el DAG `pmd_streaming_updates_spark` (queda corriendo).

### 6.6 Ejecutar el productor automatico (fuera de Airflow)

Arrancar el servicio productor:

```powershell
docker compose up -d kafka-producer
```

Si ya levantaste todo el stack, el productor puede estar corriendo. Para pararlo:

```powershell
docker compose stop kafka-producer
```

### 6.7 Ver resultados en MinIO

En MinIO Console (`http://localhost:9001`):

- Bucket: `catalogo-datasets`
- Prefijos:
  - `bronze/sqlserver/dataset_snapshot/`
  - `silver/sqlserver/dataset_snapshot/`
  - `gold/sqlserver/datasets_by_owner/`
  - `bronze/csv/catalogo_dataset/`
  - `silver/csv/catalogo_dataset/`
  - `gold/csv/datasets_by_category/`
  - `bronze/kafka/dataset_updates/`
  - `silver/kafka/dataset_updates/`
  - `gold/kafka/dataset_updates_agg/`
  - `checkpoints/`

---

## 7) SQL Server desde VSCode (extension)

Si prefieres la extension MSSQL en VSCode:

- Server: `localhost,1433`
- Authentication: SQL Login
- User: `sa`
- Password: `Password1234%`
- Database: puedes elegir `catalogo` (o conectarte primero y luego seleccionar DB)

Luego puedes ejecutar queries como:

```sql
SELECT * FROM catalogo.dbo.dataset_snapshot;
```

Si todavia no existe la DB/tabla, primero ejecuta el seed (seccion 6.2).

---

## 8) Sobre logs y git

Se ignora la carpeta de logs de Airflow:

- `.gitignore` incluye `docker-compose/logs/`

La idea es que el repo no se llene de artefactos de ejecucion.

---

## 9) Troubleshooting (problemas tipicos)

### 10.1 `sqlcmd` no existe

Sintoma:
- `stat /opt/mssql-tools/bin/sqlcmd: no such file or directory`

Solucion:
- Usa `/opt/mssql-tools18/bin/sqlcmd` (seccion 6.2).

### 10.2 El script SQL no aparece en `/opt/mssql-scripts/`

Sintoma:
- `Invalid filename` al ejecutar `-i /opt/mssql-scripts/...`

Causa:
- Contenedor `sqlserver` se creo antes de montar `./sql:/opt/mssql-scripts` o se quedo viejo.

Solucion:
- Recrear el servicio:
  - `docker compose up -d --build sqlserver`

### 10.3 Kafka no produce/consume como esperas

Checklist:
- El contenedor `kafka` esta Up (no reiniciando).
- El servicio `kafka-producer` esta levantado (`docker compose up -d kafka-producer`).
- El job `pmd_streaming_updates.py` esta corriendo.
- Mira outputs en MinIO (si hay checkpoints y gold, el streaming esta funcionando).

---

## 10) Referencias de codigo (por archivo)

Batch SQL:
- `docker-compose/sql/seed_dataset_snapshot.sql`: crea `catalogo.dbo.dataset_snapshot` y mete 3 filas.
- `pipelines/spark-apps/pmd_batch_snapshot.py`: batch SQL incremental con Delta medallion.
- `pipelines/dags/real/pmd_batch_snapshot_spark.py`: lanza el batch SQL via Airflow.

Batch CSV:
- `pipelines/data/csv/catalogo_dataset.csv`: datos CSV de entrada.
- `pipelines/spark-apps/pmd_csv_batch_medallion.py`: batch CSV con Delta medallion.
- `pipelines/dags/real/pmd_csv_batch_medallion_spark.py`: lanza el batch CSV via Airflow.

Streaming:
- `productores/kafka/producer_kafka.py`: productor real a Kafka (servicio `kafka-producer`).
- `pipelines/spark-apps/pmd_streaming_updates.py`: consumer streaming con Delta medallion y join batch.
- `pipelines/dags/real/pmd_streaming_updates_spark.py`: lanza el consumer via Airflow.

Orquestacion ASBD:
- `pipelines/dags/test/catalog_batch_minutely_test.py`: macros, branch, XCom, trigger entre DAGs.
- `pipelines/dags/test/catalog_streaming_events_test.py`: sensor y streaming simulado.
- `pipelines/dags/maintenance/catalog_maintenance_cron.py`: ejemplo cron.
- `pipelines/dags/test/spark_medallion_test.py`: DAG de ejemplo (Spark + Delta).
- `pipelines/spark-apps/spark_job_test.py`: job de ejemplo usado por `spark_medallion_test`.

Infra:
- `docker-compose/docker-compose.yml`: define servicios, redes, volumenes, puertos, buckets MinIO, etc.

