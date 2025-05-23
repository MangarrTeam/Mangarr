# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set environment variables for Django settings
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (e.g., SQLite)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sqlite3 \
    nginx \
    gettext \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy the requirements file to the container and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Django project into the container
COPY ./mangarr /app/

# Expose the port the app will run on
EXPOSE 80

COPY supervisord.conf /etc/supervisord.conf

# Copy Nginx configuration file
COPY nginx.conf /etc/nginx/nginx.conf

COPY ./static /uploads/static/

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY monitor_gunicorn.sh /app/monitor_gunicorn.sh
RUN chmod +x /app/monitor_gunicorn.sh

COPY maintenance.html /mangarr_static/maintenance.html

RUN mkdir -p /manga/cache
RUN mkdir -p /manga/media

# Entry point to run migrations and start Django server with custom configurations
CMD ["/app/entrypoint.sh"]