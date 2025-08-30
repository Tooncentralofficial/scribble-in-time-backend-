#!/bin/bash

# Start script for Scribble in Time Backend
echo "Starting Scribble in Time Backend with Gunicorn..."

# Set Django settings module
export DJANGO_SETTINGS_MODULE=scribbleintimeai.settings

# Start gunicorn with correct arguments
gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 3 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    scribbleintimeai.wsgi:application 