#!/bin/sh
set -e

python manage.py makemigrations database processes frontend api
python manage.py migrate
python manage.py makemigrations database processes frontend api
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py make-messages -a
django-admin compilemessages
gunicorn --bind 0.0.0.0:8000 server.wsgi:application --reload &

nginx -g 'daemon off;'