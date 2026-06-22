# AGENTS.md

## Objetivo

Mantener el catálogo Big Data reproducible mediante Docker Compose y navegable como evidencia documental gratuita.

## Reglas

- GitHub Pages solo publica documentación y previews; no simular que Airflow, Spark, Kafka o MinIO están activos.
- No duplicar el README; `index.md` lo reutiliza como fuente canónica.
- No versionar `.env`, credenciales ni datos generados voluminosos.
- Mantener coherentes `docs/portfolio_deployment.md` y `portfolio.json`.

## Verificación mínima

Validar `docker compose config` cuando se cambie infraestructura; para la publicación, comprobar el workflow `pages.yml` y los enlaces de documentación.
