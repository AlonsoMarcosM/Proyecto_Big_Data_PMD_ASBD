# Trabajo final PMD y ASBD - Catalogo de metadatos de datasets

Este repositorio implementa una propuesta sencilla y reproducible de producto Big Data para las asignaturas Procesamiento Masivo de Datos (PMD) y Arquitectura de Sistemas Big Data (ASBD). La propuesta se alinea con el Trabajo Fin de Master (TFM) sobre OpenMetadata y DCAT-AP, pero limita el alcance a un pipeline claro y demostrable.

La idea central es mantener un catalogo vivo de datasets con dos fuentes:
- Un snapshot diario desde una fuente estructurada (SQL Server).
- Un flujo de eventos en streaming (Kafka) que actualiza metadatos de esos mismos datasets.

## Estado y objetivos

- Cumple variedad y velocidad: datos estructurados en SQL y eventos JSON semiestructurados en streaming.
- Orquesta tareas en Airflow con cron, macros temporales, bifurcacion, XCom/TaskFlow, sensores y conexion entre DAGs.
- Mantiene OpenMetadata como componente opcional para catalogacion y gobierno, sin exigir funcionalidades avanzadas en esta fase.

## Ejecucion rapida (local)

1) Entrar al directorio de docker compose:

```bash
cd docker-compose
```

2) Verificar el archivo `.env` con el identificador de usuario de Airflow:

- En Linux o WSL:

```bash
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

- En Windows (PowerShell):

```powershell
"AIRFLOW_UID=1000" | Set-Content -NoNewline .env
```

3) Levantar servicios:

```bash
docker compose up -d --build
```

4) Accesos utiles:

- Airflow: http://localhost:8085 (usuario y clave: airflow / airflow)
- Spark Master UI: http://localhost:8080
- MinIO Console: http://localhost:9001 (minioadmin / minioadmin123)
- Jupyter: http://localhost:8888
- Kafka externo: localhost:9094
- SQL Server: localhost:1433 (usuario: sa, clave: Password1234%)

## Documentacion principal

- Propuesta de producto y requisitos PMD: `docs/propuesta-producto-big-data.md`
- Orquestacion en Airflow y requisitos ASBD: `docs/arquitectura-airflow.md`
- Guia de ejecucion local y notas del entorno: `docs/ejecucion-local.md`
- Alineacion con TFM y alcance actual: `docs/tfm-alineacion.md`
- OpenMetadata basico (opcional): `docs/openmetadata-basico.md`

## Estructura del repositorio

- `docker-compose/` Entorno reproducible con Airflow, Spark, Kafka, SQL Server y MinIO.
- `docker-compose/dags/` DAGs de ejemplo para cumplir los requisitos de orquestacion.
- `docker-compose/spark-apps/` Trabajos Spark de ejemplo para pruebas.
- `docs/` Documentacion funcional y tecnica del proyecto.
- `TFM/` Documentos de referencia del TFM.
- `OpenMetadata_documentacion/` Material de apoyo sobre OpenMetadata.
- `openmetadata_codigo/` Pruebas y ejemplos relacionados con OpenMetadata.

## Alcance actual del TFM (fase base)

El trabajo se centra en construir una base reproducible que permite avanzar en el TFM: catalogo de datasets, pipeline batch y streaming, y orquestacion con Airflow. Los objetivos mas avanzados de DCAT-AP se consideran logros futuros posibles y no forman parte del alcance de esta fase.

### Logros futuros posibles (fuera de alcance en esta fase)

- Analizar la estructura y los elementos del modelo DCAT-AP y sus extensiones.
- Mapear clases y propiedades de DCAT-AP con entidades equivalentes de OpenMetadata.
- Configurar taxonomias, tipos personalizados y relaciones en OpenMetadata.
- Implementar pipeline de ingestion desde una fuente externa (por ejemplo CKAN).
- Validar la configuracion mediante exportacion o federacion en formato compatible con DCAT-AP.
- Evaluar beneficios y limitaciones de la configuracion en interoperabilidad y mantenimiento.
