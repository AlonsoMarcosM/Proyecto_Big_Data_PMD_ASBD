# Alineacion con el Trabajo Fin de Master

## Descripcion

Este Trabajo Fin de Master propone el diseno e implementacion de una configuracion de metadatos en OpenMetadata alineada con el estandar DCAT-AP (Data Catalog Vocabulary - Application Profile). El objetivo es garantizar interoperabilidad semantica y tecnica de catalogos de datos abiertos e institucionales, y facilitar integracion con portales como CKAN o data.europa.eu.

El trabajo parte del analisis del modelo DCAT-AP (Dataset, Distribution, Catalog, Publisher, etc.) y su correspondencia con las entidades del metamodelo de OpenMetadata (Data Assets, Schemas, Tags, Lineage, Owners). Se define una configuracion personalizada (custom metadata y taxonomy) que permita representar DCAT-AP dentro de OpenMetadata, favoreciendo la integracion con otras plataformas.

## Objetivo general

Disenar y desplegar una configuracion de metadatos en OpenMetadata alineada con DCAT-AP, que permita mejorar la interoperabilidad y la gestion semantica de catalogos de datos en entornos Big Data y de computacion en la nube.

## Alcance actual en este repositorio

Esta fase se centra en construir la base tecnica para el TFM y las asignaturas PMD y ASBD:

- Catalogo de datasets con snapshot batch y actualizaciones en streaming.
- Orquestacion en Airflow con DAGs simples y demostrables.
- Entorno reproducible con Docker Compose.
- OpenMetadata como componente opcional (sin configuraciones avanzadas).

## Logros posteriores posibles (no incluidos en esta fase)

- Analizar la estructura y los elementos del modelo DCAT-AP y sus extensiones (por ejemplo DCAT-AP for Health o GeoDCAT-AP).
- Mapear clases y propiedades de DCAT-AP con entidades equivalentes de OpenMetadata.
- Configurar taxonomias, tipos personalizados y relaciones en OpenMetadata.
- Implementar un pipeline de ingestion o sincronizacion de metadatos desde una fuente externa (por ejemplo CKAN).
- Validar la configuracion mediante exportacion o federacion en formato compatible con DCAT-AP.
- Evaluar beneficios y limitaciones de la configuracion propuesta en interoperabilidad, automatizacion y mantenimiento.

## Competencias relacionadas

- CN02: Conocer arquitecturas para tratamiento masivo de datos y tecnicas de almacenamiento, orquestacion y gestion de pipelines.
- CP03: Implementar marcos de trabajo de gobierno de datos y estrategias de aseguramiento de calidad.

## Documentacion de referencia

- `TFM/Guia de implementacion del modelo DCAT-AP en OpenMetadata.pdf`
- `TFM/Sistema_planificacion_TFM.docx`
- `TFM/ANTEPROYECTO DE TFM.pdf`