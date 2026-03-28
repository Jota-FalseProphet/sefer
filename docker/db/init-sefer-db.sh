#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER sefer WITH PASSWORD 'sefer';
    CREATE DATABASE sefer OWNER sefer;
    GRANT ALL PRIVILEGES ON DATABASE sefer TO sefer;
EOSQL
