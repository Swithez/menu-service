#!/bin/sh
set -e

echo "Running database migrations..."
flask db upgrade

echo "Starting Flask application..."
exec flask run --host 0.0.0.0 --port 8003
