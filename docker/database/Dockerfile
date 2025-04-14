FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y sqlite3 && \
    rm -rf /var/lib/apt/lists/*

# Create data directory and set permissions
RUN mkdir -p /data && \
    chmod 777 /data

# Copy requirements and install
COPY docker/database/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ /app/scripts/

# Set environment variables
ENV PYTHONPATH=/app
ENV DB_PATH=/data/census.sqlite

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["python", "-m", "scripts.database"]