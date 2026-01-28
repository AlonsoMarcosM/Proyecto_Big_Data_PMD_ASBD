# OpenMetadata basico (opcional)

## Objetivo

Mantener una integracion minima y no bloqueante con OpenMetadata para visualizar el catalogo resultante del pipeline. En esta fase no se implementan configuraciones avanzadas de DCAT-AP, solo una base funcional.

## Enfoque simple recomendado

- OpenMetadata ya esta integrado en `docker-compose/docker-compose.yml` con una configuracion minima.
- Iniciar servicios y verificar acceso a la interfaz web.
- Cargar manualmente 3 a 5 datasets de prueba (sin ingestion automatica).
- Validar que los datasets aparecen en el catalogo y que se pueden consultar.

## Arranque y acceso

1) Arrancar servicios base:

```bash
cd docker-compose
docker compose up -d --build
```

2) Acceso a OpenMetadata:

- UI: http://localhost:8585
- Admin: admin / admin

## Servicios incluidos

- `openmetadata-mysql` (DB interna para OpenMetadata)
- `openmetadata-elasticsearch` (buscador)
- `openmetadata-migrate` (migraciones)
- `openmetadata-server` (API + UI)

## Alcance minimo en esta fase

- Sin ingesta automatica ni pipelines de harvesting.
- Sin configuraciones avanzadas de custom metadata o taxonomy.
- Uso basico del catalogo para evidencias del TFM.

## Relacion con DCAT-AP

- Esta fase solo prepara el catalogo base.
- Las extensiones de DCAT-AP se dejan para etapas posteriores del TFM.

## Referencias locales

- `OpenMetadata_documentacion/`
- `TFM/Guia de implementacion del modelo DCAT-AP en OpenMetadata.pdf`

