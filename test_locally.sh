#!/bin/bash

echo "Cleaning up existing processes on ports 8000, 8001, 8002, 8003..."

for port in 8000 8001 8002 8003; do
  pid=$(netstat -ano | grep ":$port" | grep LISTENING | awk '{print $5}' | head -n 1)
  if [ -n "$pid" ]; then
    echo "Killing process on port $port with PID $pid..."
    taskkill //PID $pid //F
  else
    echo "No process found on port $port"
  fi
done

# Set environment variables
export DB_PATH=data/census.sqlite
export CSV_PATH=data/census.csv
export RESULTS_DIR=results
export TRANSFORMED_DATA_PATH=data/transformed_data.json
export DATABASE_SERVICE=http://localhost:8000
export TRANSFORM_SERVICE=http://localhost:8001
export LOAD_SERVICE=http://localhost:8002

# Verify files
if [ ! -f "$DB_PATH" ]; then
    echo "Error: $DB_PATH not found"
    exit 1
fi
if [ ! -f "$CSV_PATH" ]; then
    echo "Error: $CSV_PATH not found"
    exit 1
fi

# Create directories
mkdir -p data results

# Start services
echo "Starting database service on port 8000..."
python scripts/database.py &
DATABASE_PID=$!
sleep 2

echo "Starting transform service on port 8001..."
python scripts/transform.py &
TRANSFORM_PID=$!
sleep 2

echo "Starting load service on port 8002..."
python scripts/load.py &
LOAD_PID=$!
sleep 2

echo "Starting main service on port 8003..."
python scripts/main.py &
MAIN_PID=$!
sleep 2

# Test endpoints
echo "Testing /connect..."
curl -s http://localhost:8000/connect || echo "Failed to connect to database service"

echo "Testing /transform..."
curl -s -X POST http://localhost:8001/transform || echo "Failed to connect to transform service"

echo "Testing /load..."
curl -s -X POST http://localhost:8002/load || echo "Failed to connect to load service"

echo "Testing /run-pipeline..."
curl -s -X POST http://localhost:8003/run-pipeline || echo "Failed to run pipeline"

# Clean up
echo "Stopping services..."
kill $DATABASE_PID $TRANSFORM_PID $LOAD_PID $MAIN_PID 2>/dev/null || true
wait $DATABASE_PID $TRANSFORM_PID $LOAD_PID $MAIN_PID 2>/dev/null || true
echo "Test completed."