#!/bin/bash
set -e

# Automatically create all required databases for the microservices on startup.
# This script executes in the official Postgres container directory '/docker-entrypoint-initdb.d/'.
# PostgreSQL will run this script automatically on the first container initialization.

databases=(
    "auth_db"
    "venue_db"
    "booking_db"
    "notification_db"
    "ai_db"
)

echo "=== Starting database initialization ==="

for db in "${databases[@]}"; do
    if psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$db"; then
        echo "Database '$db' already exists. Skipping."
    else
        echo "Creating database '$db'..."
        psql -U "$POSTGRES_USER" -c "CREATE DATABASE $db;"
        echo "Database '$db' created successfully."
    fi
done

echo "=== Database initialization completed ==="
