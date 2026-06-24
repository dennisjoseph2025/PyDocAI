#!/bin/sh
uv run python manage.py migrate --noinput 2>&1 || true
uv run python manage.py collectstatic --noinput 2>&1 || true
exec uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --worker-class gevent --workers 4
