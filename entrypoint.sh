#!/bin/sh
set -e

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  echo "Waiting for Postgres at $DB_HOST:$DB_PORT..."
  sleep 1
done

python manage.py migrate --noinput
python manage.py seed_demo_data

exec "$@"
