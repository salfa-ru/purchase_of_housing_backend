#!/bin/sh
set -e

echo "Running cleanapp command..."
python manage.py cleanapp

echo "Starting Django Q2 cluster in the background..."
python manage.py qcluster &

echo "Starting Gunicorn..."
exec "$@"
