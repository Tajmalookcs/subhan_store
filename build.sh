#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser from env vars (DJANGO_SUPERUSER_* must be set)
python manage.py createsuperuser --noinput 2>/dev/null || true
