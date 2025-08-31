# Base image
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# ARG to detect architecture (used only for multi-stage)
ARG TARGETARCH

# ------------------------------
# AMD64 stage
# ------------------------------
FROM base AS amd64
RUN apt-get update && apt-get install -y --no-install-recommends \
        sqlite3 nginx gettext supervisor redis-server \
        chromium chromium-driver \
        fonts-liberation libasound2 libatk-bridge2.0-0 \
        libatk1.0-0 libcups2 libdrm2 libgbm1 libgtk-3-0 \
        libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
        libxrandr2 xdg-utils ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------
# ARM64 stage
# ------------------------------
FROM base AS arm64
RUN apt-get update && apt-get install -y --no-install-recommends \
        sqlite3 nginx gettext supervisor redis-server \
        chromium-browser chromium-chromedriver \
        fonts-liberation libasound2 libatk-bridge2.0-0 \
        libatk1.0-0 libcups2 libdrm2 libgbm1 libgtk-3-0 \
        libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
        libxrandr2 xdg-utils ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------
# Final stage: copy from correct architecture
# ------------------------------
FROM base AS final
ARG TARGETARCH
COPY --from=amd64 / /app
COPY --from=arm64 / /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY ./mangarr /app/

# Expose port
EXPOSE 80

# Supervisor and Nginx configs
COPY supervisord.conf /etc/supervisord.conf
COPY nginx.conf /etc/nginx/nginx.conf

# Static files
COPY ./static /uploads/static/

# Entrypoint scripts
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY monitor_gunicorn.sh /app/monitor_gunicorn.sh
RUN chmod +x /app/monitor_gunicorn.sh

# Maintenance page
COPY maintenance.html /mangarr_static/maintenance.html

# Media/cache directories
RUN mkdir -p /manga/cache /manga/media

# Start the application
CMD ["/app/entrypoint.sh"]
