# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data

# Always copy .env.example to .env for Docker
RUN cp .env.example .env

# Create non-root user for security
RUN groupadd -r devopin && useradd -r -g devopin devopin

# Create volume for persistent data
VOLUME ["/app/data"]

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Create startup script that runs as root first, then switches to devopin
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting Devopin Community Backend..."\n\
\n\
# Run as root to fix permissions\n\
if [ "$(id -u)" = "0" ]; then\n\
    echo "Running as root, fixing permissions..."\n\
    mkdir -p /app/data\n\
    chown -R devopin:devopin /app/data\n\
    chmod -R 755 /app/data\n\
    \n\
    # Fix socket permissions if exists\n\
    if [ -S /run/devopin-agent.sock ]; then\n\
        echo "Fixing socket permissions..."\n\
        chmod 666 /run/devopin-agent.sock\n\
    fi\n\
    \n\
    # Switch to devopin user and re-exec script\n\
    exec su devopin -c "$0"\n\
fi\n\
\n\
# Now running as devopin user\n\
echo "Running as user: $(whoami)"\n\
\n\
# Ensure .env exists\n\
if [ ! -f /app/.env ]; then\n\
    echo "Copying .env.example to .env..."\n\
    cp /app/.env.example /app/.env\n\
fi\n\
\n\
# Check if database exists and run migrations\n\
if [ ! -f /app/data/devopin.db ]; then\n\
    echo "Creating new database..."\n\
    touch /app/data/devopin.db\n\
    echo "Running initial migrations..."\n\
    alembic upgrade head\n\
else\n\
    echo "Database exists, running migrations..."\n\
    alembic upgrade head\n\
fi\n\
\n\
echo "Database setup complete!"\n\
echo "Starting application..."\n\
\n\
# Start application\n\
exec python -m app.main' > /app/start.sh && chmod +x /app/start.sh

# Fix initial permissions
RUN chown -R devopin:devopin /app

# Run the application
CMD ["/app/start.sh"]