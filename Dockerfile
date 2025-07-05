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

# Copy .env.example to .env if .env doesn't exist
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Create non-root user for security
RUN groupadd -r devopin && useradd -r -g devopin devopin
RUN chown -R devopin:devopin /app
USER devopin

# Create volume for persistent data
VOLUME ["/app/data"]

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
# Create database if not exists\n\
if [ ! -f /app/data/devopin.db ]; then\n\
    echo "Creating database..."\n\
    touch /app/data/devopin.db\n\
    alembic upgrade head\n\
fi\n\
\n\
# Start application\n\
exec python -m app.main' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]