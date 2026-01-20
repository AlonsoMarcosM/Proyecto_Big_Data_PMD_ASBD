# Propuesta de producto Big Data

## Introduccion

Este documento describe el producto Big Data propuesto y la arquitectura asociada para las asignaturas Procesamiento Masivo de Datos (PMD) y Arquitectura de Sistemas Big Data (ASBD). El objetivo es definir un proyecto sencillo, reproducible y facil de implementar que permita aplicar fundamentos de ingesta y procesamiento masivo, cumpliendo explicitamente los requisitos de la tarea "Describe tu producto Big Data":

- Variedad: usar fuentes de datos estructuradas y semiestructuradas.
- Velocidad: combinar procesamiento batch y procesamiento streaming.

La propuesta se alinea con el Trabajo Fin de Master (TFM) relacionado con OpenMetadata y DCAT-AP. En estas asignaturas se mantiene un alcance acotado para demostrar con claridad el pipeline y la arquitectura. OpenMetadata es opcional y se plantea como apoyo para el catalogo y el gobierno de datos.

## Arquitectura propuesta (vision general)

La arquitectura esta pensada para ejecutarse en local y ser reutilizable en ASBD mediante Docker Compose. Componentes minimos:

- Base de datos SQL (SQL Server) como fuente estructurada para el snapshot batch.
- Kafka como broker de eventos en streaming.
- Spark para procesamiento batch y streaming (Structured Streaming).
- Airflow para orquestacion del batch con planificacion diaria y control de estado.

OpenMetadata se contempla como componente opcional para centralizar y visualizar el catalogo resultante.

## Caso de uso

En organizaciones con multiples equipos y sistemas de datos, los metadatos de los datasets cambian con frecuencia (descripciones, etiquetas, enlaces, responsables). Mantener un inventario actualizado facilita gobernanza, localizacion de activos y trazabilidad.

El caso de uso es mantener un inventario vivo de datasets y sus metadatos combinando:

- Un snapshot completo del catalogo obtenido periodicamente (batch).
- Cambios incrementales sobre esos datasets conforme se producen (streaming).

## Retos del producto (preguntas claras y demostrables)

Los retos se definen para ser simples y demostrables con pocos datos (3 a 5 datasets) y pocos eventos (10 a 20). Todas las preguntas reflejan la relacion entre batch y streaming mediante el identificador `dataset_id`:

- R1. Que datasets han recibido al menos un evento de actualizacion en streaming desde la ultima ejecucion batch.
- R2. Cual es la ultima hora de actualizacion por dataset (ultimo `event_time`).
- R3. Que tipo de cambio es mas frecuente (cambios en `description`, `tags` o `url`).
- R4. Que datasets tenian metadatos incompletos en el snapshot batch (por ejemplo `description` vacia) y siguen incompletos tras aplicar el streaming.

## Conjuntos de datos (fuentes, variedad y detalle)

### Datos en batch (estructurados)

Los datos en batch son estructurados y se almacenan en una tabla relacional (SQL Server). Esta tabla representa el estado base del catalogo en el momento de la ejecucion batch.

Tabla propuesta: `dataset_snapshot`

- `dataset_id` (clave del dataset)
- `title`
- `description`
- `owner`
- `tags` (texto con separador coma)
- `url`
- `modified_at` (fecha y hora ISO-8601)

Volumen inicial (MVP): 3 a 5 datasets.

### Datos en streaming (eventos JSON simulados)

Los datos en streaming son eventos semiestructurados en JSON que simulan cambios incrementales sobre los datasets del snapshot batch. Cada evento referencia un `dataset_id` existente, lo que garantiza la relacion directa entre ambos flujos.

Evento propuesto: `dataset_updated`

- `event_time` (fecha y hora ISO-8601)
- `event_type` (valor fijo: `dataset_updated`)
- `dataset_id`
- `changed_field` (uno de: `description`, `tags`, `url`)
- `new_value` (nuevo valor del campo)

Ejemplo de evento:

```json
{
  "event_time": "2025-12-18T10:35:00Z",
  "event_type": "dataset_updated",
  "dataset_id": "ds_001",
  "changed_field": "tags",
  "new_value": "open,metadata,dcat-ap"
}
```

## Velocidad: batch y streaming (frecuencia explicita)

- Batch: ejecucion diaria (cada 24 horas). El batch recarga el snapshot desde SQL.
- Streaming: publicacion de eventos cada 5 a 10 segundos para simular un flujo continuo.

## Procesamiento y relacion entre ambos flujos

La combinacion batch y streaming es el nucleo del producto. El batch aporta el estado base (`dataset_snapshot`) y el streaming aplica cambios posteriores sobre el mismo dataset usando `dataset_id`. El estado actual se obtiene como snapshot batch mas actualizaciones en streaming desde la ultima ejecucion batch.

Procesamiento previsto (simple y demostrable):

- Normalizacion de textos (trim) y tratamiento de nulos.
- Validacion basica: `title` no vacio y `url` con formato correcto.
- Deduplicacion en batch por `dataset_id`.
- Validacion de eventos en streaming y aplicacion del cambio al dataset correspondiente.
- Calculo de salidas necesarias para R1 a R4 (listas y conteos).

## Evidencias

- Logs o capturas de la ejecucion batch leyendo SQL y cargando 3 a 5 datasets.
- Logs o capturas del streaming consumiendo y aplicando al menos 10 eventos.
- Salida final con resultados de R1 a R4 (conteos y listas).
- Para ASBD: captura de `docker compose up` con servicios levantados y DAGs en Airflow.
- Logs o capturas en OpenMetadata mostrando el catalogo cargado o actualizado, si se integra.

## Resumen

El producto propuesto mantiene un catalogo de metadatos de datasets combinando un snapshot batch diario desde SQL y una ingesta en streaming de eventos JSON que actualizan esos datasets. La propuesta cumple con los requisitos de variedad y velocidad exigidos en PMD, define retos claros y demostrables, y plantea una arquitectura reproducible con Docker Compose y orquestacion con Airflow, reutilizable para ASBD.