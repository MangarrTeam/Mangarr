# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set environment variables for Django settings
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        sqlite3 \
        nginx \
        gettext \
        supervisor \
        redis-server \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcups2 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        xdg-utils \
        ca-certificates && \
    if [ "$ARCH" = "arm64" ]; then \
        apt-get install -y --no-install-recommends chromium-browser chromium-chromedriver; \
    else \
        apt-get install -y --no-install-recommends chromium chromium-driver; \
    fi && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy Python dependencies and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY ./mangarr /app/

# Expose port
EXPOSE 80

# Copy configuration files
COPY supervisord.conf /etc/supervisord.conf
COPY nginx.conf /etc/nginx/nginx.conf
COPY ./static /uploads/static/
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
COPY monitor_gunicorn.sh /app/monitor_gunicorn.sh
RUN chmod +x /app/monitor_gunicorn.sh
COPY maintenance.html /mangarr_static/maintenance.html

# Create necessary directories
RUN mkdir -p /manga/cache /manga/media

# Default entrypoint
CMD ["/app/entrypoint.sh"]
