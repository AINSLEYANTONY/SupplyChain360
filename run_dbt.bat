@echo off
docker exec sc360-airflow bash -c "cd /opt/airflow/project/dbt && /home/airflow/dbt_venv/bin/dbt %* --profiles-dir ."