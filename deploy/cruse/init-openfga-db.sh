#!/bin/bash
# Create the openfga database for OpenFGA's datastore.
# This script is mounted into the PostgreSQL container's
# /docker-entrypoint-initdb.d/ directory and runs once on
# first initialization.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE openfga;
    GRANT ALL PRIVILEGES ON DATABASE openfga TO $POSTGRES_USER;
EOSQL
