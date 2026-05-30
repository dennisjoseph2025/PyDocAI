#!/bin/bash
set -e
uv run python manage.py migrate --noinput
uv run python manage.py collectstatic --noinput
exec uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --worker-class gevent --workers 4
