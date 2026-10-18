from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PROJECT = "/opt/airflow/project"

default_args = {
    "retries": 2,                                  # try again twice if a task fails
    "retry_delay": timedelta(minutes=1),           # wait a minute between tries
    "execution_timeout": timedelta(minutes=20),    # kill a task that hangs
}

with DAG(
    dag_id="supplychain360_pipeline",
    description="Bronze -> Silver -> PostgreSQL star schema",
    start_date=datetime(2026, 1, 1),
    schedule="30 12 * * *",   # every day at 06:00 UTC
    catchup=False,
    max_active_runs=1,    # never run two copies at once (protects your 8 GB)
    default_args=default_args,
    tags=["supplychain360"],
) as dag:

    ingest_to_bronze = BashOperator(
        task_id="ingest_to_bronze",
        bash_command=f"cd {PROJECT} && python ingestion/ingest_to_bronze.py",
    )

    bronze_to_silver = BashOperator(
        task_id="bronze_to_silver",
        bash_command=f"cd {PROJECT} && python spark/jobs/bronze_to_silver.py",
    )

    silver_to_postgres = BashOperator(
        task_id="silver_to_postgres",
        bash_command=f"cd {PROJECT} && python spark/jobs/silver_to_postgres.py",
    )

    build_star_schema = BashOperator(
        task_id="build_star_schema",
        bash_command=f"cd {PROJECT} && python warehouse/build_star_schema.py",
    )

    ingest_to_bronze >> bronze_to_silver >> silver_to_postgres >> build_star_schema