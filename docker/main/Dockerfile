FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y sqlite3 && \
    rm -rf /var/lib/apt/lists/*

# Create data and results directories and set permissions
RUN mkdir -p /data /results && \
    chmod 777 /data /results

# Copy requirements and install
COPY docker/main/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ /app/scripts/

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_SERVICE=http://database:8000
ENV TRANSFORM_SERVICE=http://transform:8001
ENV LOAD_SERVICE=http://load:8002
ENV RESULTS_DIR=/results
ENV DB_PATH=/data/census.sqlite
ENV CSV_PATH=/data/census.csv
ENV TRANSFORMED_DATA_PATH=/data/transformed_data.json

# Expose port
EXPOSE 8003

# Run FastAPI app
CMD ["python", "-m", "scripts.main"]