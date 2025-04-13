#!/bin/bash

IMAGES=(
  "localhost:5001/etl-database:latest"
  "localhost:5001/etl-load:latest"
  "localhost:5001/etl-main:latest"
  "localhost:5001/etl-transform:latest"
)

echo "Deleting local Docker images..."

for IMAGE in "${IMAGES[@]}"; do
  echo "Removing $IMAGE"
  docker rmi "$IMAGE"
done

echo "Done."
