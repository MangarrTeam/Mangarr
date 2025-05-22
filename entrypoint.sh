#!/bin/sh
set -e

python manage.py makemigrations plugins database_other database_data_types database_manga database_users processes frontend api
python manage.py migrate
python manage.py makemigrations plugins database_other database_data_types database_manga database_users processes frontend api
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py make-messages -a
django-admin compilemessages
gunicorn --bind 0.0.0.0:8000 server.wsgi:application --workers 4 --threads 3 --reload &

nginx -g 'daemon off;'