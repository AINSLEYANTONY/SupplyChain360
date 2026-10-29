# Pipeline documentation

## Daily flow

The `supplychain360_pipeline` DAG runs at 06:00 UTC. Each task runs one script. Tasks retry twice, one minute apart (`dbt_build` once), and a task that fails for good is recorded in `quality.pipeline_failures`.

| Task | Script | What it does |
|---|---|---|
| ingest_to_bronze | `ingestion/ingest_to_bronze.py` | Reads CSV and JSON files, keeps every column as text, adds `_source_file`, `_ingested_at`, `_batch_id`, and writes Parquet to Bronze. |
| bronze_to_silver | `spark/jobs/bronze_to_silver.py` | Casts types, removes duplicates, applies validation rules, writes good rows to Silver and bad rows to quarantine, and saves run statistics. |
| silver_to_postgres | `spark/jobs/silver_to_postgres.py` | Loads the Silver tables into the `silver` schema. |
| quality_to_postgres | `spark/jobs/quality_to_postgres.py` | Loads quarantined rows and run statistics into Postgres. |
| dbt_build | `dbt build` | Builds staging, intermediate, gold, quality and alerts models and runs every test. |
| alert_summary | `quality/validation/alert_summary.py` | Prints alert counts by type and severity in the task log. |
| dbt_docs | `dbt docs generate` | Refreshes the documentation site. |

## Layers

| Layer | Location | Format |
|---|---|---|
| Bronze | MinIO `supplychain-data/bronze/<table>/ingest_date=<date>/` | Parquet, all text |
| Silver | MinIO `silver/<table>/` and Postgres `silver` | Parquet and tables, typed |
| Quarantine | MinIO `quarantine/<table>/` and Postgres `quarantine.rejected_records` | Rejected rows with reasons |
| Staging and intermediate | Postgres `staging`, `intermediate` | dbt views |
| Gold | Postgres `gold` | dbt tables (star schema) |
| Alerts and quality | Postgres `alerts`, `quality` | dbt tables |

## Data quality controls

| Where | Check | On failure |
|---|---|---|
| Spark | Required IDs not null, quantity above 0, money not negative, rating 0 to 5, delivery not before shipping | Row quarantined with the failed rule |
| Spark | Duplicates by business key | Removed and counted |
| dbt | Unique, not null, relationships, accepted values | Build fails |
| dbt | Orphan order lines and shipments (parent order quarantined) | Warning |
| dbt | Row counts reconcile (raw = duplicates + silver + quarantine) | Build fails |
| dbt | Order totals match their lines | Warning |
| Airflow | Task fails after retries | Recorded in `quality.pipeline_failures` |

## Idempotency

Every step overwrites its own output: Bronze files are keyed by ingest date, Silver and quarantine are overwritten, Postgres loads truncate and reload, and dbt rebuilds its tables. Running any task twice gives the same result as once, so retries and reruns are safe.

## Operations

| Task | Command |
|---|---|
| Start everything | `docker compose --env-file .env -f docker/docker-compose.yml up -d` |
| Stop (data is kept) | `docker compose --env-file .env -f docker/docker-compose.yml stop` |
| Recover a failed run | Fix the cause, then in the Airflow UI click the red task and choose **Clear Task** with **Downstream** ticked |
| Rebuild only the models | `run_dbt.bat build` |
| Change an alert threshold | Edit `vars` in `dbt/dbt_project.yml`, then run `run_dbt.bat build --select path:models/alerts` |
| Refresh the dashboard | Power BI **Home → Refresh** (Postgres must be running) |

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `apt-get` fails with "Not live until" | The Windows clock is wrong. Turn on **Set time automatically**, then run `wsl --shutdown` and restart Docker. |
| `password authentication failed` from Spark | The password stored in the volume differs from `.env`. Run `ALTER USER sc360 WITH PASSWORD 'sc360pass';`. |
| Tools reach the wrong Postgres | A second Postgres is using port 5432. This project publishes on 5433. |
| `pull access denied for minio/minio` | The official image was removed from Docker Hub. Use the mirror image in the compose file. |
| dbt docs show "unable to load manifest" | Serve the folder with `python -m http.server` instead of opening the file directly. |
| Power BI "Cannot find table" | Tables are loaded as `gold dim_date` and so on. Rename them to the plain names. |