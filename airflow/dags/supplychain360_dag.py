from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PROJECT = "/opt/airflow/project"
DBT = "/home/airflow/dbt_venv/bin/dbt"

default_args = {
    "retries": 2,                                  # try again twice if a task fails
    "retry_delay": timedelta(minutes=1),           # wait a minute between tries
    "execution_timeout": timedelta(minutes=20),    # kill a task that hangs
}

with DAG(
    dag_id="supplychain360_pipeline",
    description="Bronze -> Silver -> PostgreSQL -> dbt Gold",
    start_date=datetime(2026, 1, 1),
    schedule="0 6 * * *",   # every day at 06:00 UTC
    catchup=False,
    max_active_runs=1,      # never run two copies at once (protects your 8 GB)
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

    # Builds staging -> intermediate -> gold AND runs all tests.
    # One retry only: a failed data test won't fix itself by retrying.
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {PROJECT}/dbt && {DBT} build --profiles-dir .",
        retries=1,
    )

    dbt_docs = BashOperator(
        task_id="dbt_docs",
        bash_command=f"cd {PROJECT}/dbt && {DBT} docs generate --static --profiles-dir .",
    )

    ingest_to_bronze >> bronze_to_silver >> silver_to_postgres >> dbt_build >> dbt_docs