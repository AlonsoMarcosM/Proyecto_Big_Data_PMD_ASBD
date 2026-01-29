# Visualizaciones locales

Esta carpeta se rellena con previews (CSV y JSONL) generados desde las salidas Gold
al final de cada pipeline principal.

Salidas esperadas (si existen datos):

- `gold_sqlserver_datasets_by_owner/preview.csv`
- `gold_sqlserver_datasets_by_owner/preview.jsonl`
- `gold_csv_datasets_by_category/preview.csv`
- `gold_csv_datasets_by_category/preview.jsonl`
- `gold_kafka_dataset_updates_agg/preview.csv`
- `gold_kafka_dataset_updates_agg/preview.jsonl`

Ejemplos de datos base (para comparar con Gold):

- `ejemplos/events.jsonl` (eventos Kafka de referencia)
- `ejemplos/seed_dataset_snapshot.sql` (seed SQL Server)
- `ejemplos/catalogo_dataset.csv` (CSV base)

Nota:
- La carpeta `gold_kafka_dataset_updates_agg/` solo aparece si se ejecuta el streaming.

Sugerencia para verlos en VS Code:

- CSV: extension "Rainbow CSV".
- JSONL: cualquier visor de JSON o abrir como texto.
