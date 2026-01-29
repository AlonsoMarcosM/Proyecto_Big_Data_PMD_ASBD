# Productores de entrada (referencia)

Esta carpeta contiene las fuentes de datos base que alimentan los pipelines.

- `csv/catalogo_dataset.csv`: CSV base usado por el pipeline batch CSV.
- `sql/seed_dataset_snapshot.sql`: script seed que carga SQL Server para el batch estructurado.

Nota: las rutas activas de ingesta siguen siendo:
- CSV: `pipelines/data/csv/catalogo_dataset.csv`
- SQL: `docker-compose/sql/seed_dataset_snapshot.sql`