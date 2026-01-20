# OpenMetadata basico (opcional)

## Objetivo

Mantener una integracion minima y no bloqueante con OpenMetadata para visualizar el catalogo resultante del pipeline. En esta fase no se implementan configuraciones avanzadas de DCAT-AP, solo una base funcional.

## Enfoque simple recomendado

- Usar el Docker Compose oficial de OpenMetadata en un directorio separado para evitar complejidad en este entorno.
- Iniciar OpenMetadata y verificar el acceso a la interfaz web.
- Cargar manualmente 3 a 5 datasets de prueba o usar una ingesta sencilla desde la fuente SQL.
- Validar que los datasets aparecen en el catalogo y que se pueden consultar.

## Relacion con DCAT-AP

- Esta fase solo prepara el catalogo base.
- Las extensiones de DCAT-AP se dejan para etapas posteriores del TFM.

## Referencias locales

- `OpenMetadata_documentacion/`
- `TFM/Guia de implementacion del modelo DCAT-AP en OpenMetadata.pdf`