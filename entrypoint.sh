#!/bin/sh
set -e

python manage.py makemigrations plugins database_other database_data_types database_manga database_users processes frontend api
python manage.py migrate
python manage.py makemigrations plugins database_other database_data_types database_manga database_users processes frontend api
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py make-messages -a
django-admin compilemessages

exec supervisord -c /etc/supervisord.conf