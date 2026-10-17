@echo off
docker run --rm --env-file .env -e POSTGRES_HOST=sc360-postgres --network docker_default -v "%cd%":/app sc360-spark python %*