#!/bin/sh
set -e

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Running cleanapp command..."
python manage.py cleanapp || echo "cleanapp не отработал, продолжаем запуск"

echo "Starting Django Q2 cluster in the background..."
python manage.py qcluster &

echo "Starting Gunicorn..."
exec "$@"
