#!/bin/sh
set -e

# Run database migrations
python manage.py migrate --noinput

# Collect static files (can be skipped with COLLECTSTATIC=0)
if [ "${COLLECTSTATIC:-1}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

# Start WSGI server
exec waitress-serve --port="${PORT:-8000}" --threads="${WEB_CONCURRENCY:-4}" meal_tracker.wsgi:application
