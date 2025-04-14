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
COPY docker/transform/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ /app/scripts/

# Set environment variables
ENV PYTHONPATH=/app
ENV CSV_PATH=/data/census.csv
ENV TRANSFORMED_DATA_PATH=/data/transformed_data.json

# Expose port
EXPOSE 8001

# Run FastAPI app
CMD ["python", "-m", "scripts.transform"]