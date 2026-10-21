import os
from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PROJECT = "/opt/airflow/project"
DBT = "/home/airflow/dbt_venv/bin/dbt"


def record_failure(context):
    """Runs when a task fails for good (after all its retries). Saves the failure to Postgres."""
    try:
        import psycopg2

        ti = context.get("task_instance") or context.get("ti")
        task_id = getattr(ti, "task_id", "unknown")
        run_id = str(context.get("run_id", "unknown"))
        error = str(context.get("exception", ""))[:500]

        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=5432,
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        )
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    "create table if not exists quality.pipeline_failures ("
                    "failed_at timestamptz default now(), dag_id text, "
                    "task_id text, run_id text, error text)"
                )
                cur.execute(
                    "insert into quality.pipeline_failures (dag_id, task_id, run_id, error) "
                    "values (%s, %s, %s, %s)",
                    ("supplychain360_pipeline", task_id, run_id, error),
                )
        finally:
            conn.close()
    except Exception as exc:  # the alerting itself must never crash the task handler
        print(f"Could not record failure: {exc}")


default_args = {
    "retries": 2,                                  # try again twice if a task fails
    "retry_delay": timedelta(minutes=1),           # wait a minute between tries
    "execution_timeout": timedelta(minutes=20),    # kill a task that hangs
    "on_failure_callback": record_failure,         # runs only after the last retry fails
}

with DAG(
    dag_id="supplychain360_pipeline",
    description="Bronze -> Silver -> PostgreSQL -> dbt Gold -> alerts",
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

    quality_to_postgres = BashOperator(
        task_id="quality_to_postgres",
        bash_command=f"cd {PROJECT} && python spark/jobs/quality_to_postgres.py",
    )

    # Builds staging -> intermediate -> gold -> quality -> alerts AND runs all tests.
    # One retry only: a failed data test won't fix itself by retrying.
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {PROJECT}/dbt && {DBT} build --profiles-dir .",
        retries=1,
    )

    alert_summary = BashOperator(
        task_id="alert_summary",
        bash_command=f"cd {PROJECT} && python quality/validation/alert_summary.py",
    )

    dbt_docs = BashOperator(
        task_id="dbt_docs",
        bash_command=f"cd {PROJECT}/dbt && {DBT} docs generate --static --profiles-dir .",
    )

    (ingest_to_bronze >> bronze_to_silver >> silver_to_postgres >> quality_to_postgres
     >> dbt_build >> alert_summary >> dbt_docs)