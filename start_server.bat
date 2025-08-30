@echo off
echo Starting Scribble in Time Backend with Gunicorn...

REM Set Django settings module
set DJANGO_SETTINGS_MODULE=scribbleintimeai.settings

REM Start gunicorn with correct arguments
gunicorn --bind 0.0.0.0:8080 --workers 3 --timeout 30 --access-logfile - --error-logfile - --log-level info scribbleintimeai.wsgi:application

pause 