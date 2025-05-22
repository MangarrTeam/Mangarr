#!/bin/bash

# Check interval in seconds
CHECK_INTERVAL=10

while true; do
    # Get Gunicorn status from supervisorctl
    STATUS=$(supervisorctl status gunicorn | awk '{print $2}')

    if [ "$STATUS" != "RUNNING" ]; then
        echo "$(date): Gunicorn is not running (status: $STATUS). Restarting..."
        supervisorctl restart gunicorn
    fi

    sleep $CHECK_INTERVAL
done
