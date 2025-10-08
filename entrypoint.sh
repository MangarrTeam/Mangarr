#!/bin/sh
set -e

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py make-messages -a
django-admin compilemessages

exec supervisord -c /etc/supervisord.conf