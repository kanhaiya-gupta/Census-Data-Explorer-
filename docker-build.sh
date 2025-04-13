#!/bin/bash
set -e

cd "$(dirname "$0")"

# Check for required files and directories
if [ ! -f "kubernetes/kind-config.yaml" ]; then
    echo "Error: kubernetes/kind-config.yaml not found in $(pwd)"
    exit 1
fi

if [ ! -d "docker" ]; then
    echo "Error: docker/ directory not found in $(pwd)"
    exit 1
fi

# Check for required Dockerfiles
for component in database transform load main; do
    if [ ! -f "docker/$component/Dockerfile" ]; then
        echo "Error: docker/$component/Dockerfile not found"
        exit 1
    fi
done

# Ensure Kind cluster exists
CLUSTER_NAME="etl-pipeline-cluster"
if ! kind get clusters | grep -q "$CLUSTER_NAME"; then
    echo "Creating kind cluster '$CLUSTER_NAME'..."
    kind create cluster --name "$CLUSTER_NAME" --config kubernetes/kind-config.yaml
else
    echo "Kind cluster '$CLUSTER_NAME' already exists."
fi

# Set up local registry
REGISTRY_NAME="kind-registry"
REGISTRY_PORT="5001"

# Check and remove any non-running kind-registry containers
if docker ps -a -q -f name="$REGISTRY_NAME" | grep -q .; then
    if ! docker ps -q -f name="$REGISTRY_NAME" | grep -q .; then
        echo "Removing non-running '$REGISTRY_NAME' container..."
        docker rm -f "$REGISTRY_NAME"
    fi
fi

# Start registry if not running
if ! docker ps -q -f name="$REGISTRY_NAME" | grep -q .; then
    echo "Starting local registry on port $REGISTRY_PORT..."
    # Retry up to 3 times to handle transient failures
    for attempt in {1..3}; do
        if docker run -d -p "$REGISTRY_PORT:5000" --name "$REGISTRY_NAME" --network kind registry:2; then
            echo "Registry started successfully."
            break
        else
            echo "Attempt $attempt: Failed to start registry. Retrying in 5 seconds..."
            sleep 5
        fi
        if [ $attempt -eq 3 ]; then
            echo "Error: Failed to start registry after $attempt attempts."
            exit 1
        fi
    done
    docker network connect kind "$REGISTRY_NAME" || echo "Already connected"
else
    echo "Local registry '$REGISTRY_NAME' already running."
fi

# Verify registry is accessible
if ! curl -s http://localhost:$REGISTRY_PORT/v2/ > /dev/null; then
    echo "Warning: Registry at localhost:$REGISTRY_PORT is not responding."
fi

# Function to build and push images
build_image() {
    local image_name="$1"
    local dockerfile_path="$2"
    local tag="localhost:$REGISTRY_PORT/$image_name"
    if ! docker image inspect "$tag" > /dev/null 2>&1; then
        echo "Building image: $tag"
        docker build -t "$tag" -f "$dockerfile_path" .
    else
        echo "Image $tag already exists, skipping build."
    fi
    echo "Pushing image: $tag"
    docker push "$tag"
}

# Build and push Docker images
echo "Building and pushing Docker images..."
build_image "etl-database:latest" "docker/database/Dockerfile"
build_image "etl-transform:latest" "docker/transform/Dockerfile"
build_image "etl-load:latest" "docker/load/Dockerfile"
build_image "etl-main:latest" "docker/main/Dockerfile"

# Load images into Kind cluster
echo "Loading images into Kind cluster '$CLUSTER_NAME'..."
kind load docker-image "localhost:$REGISTRY_PORT/etl-database:latest" --name "$CLUSTER_NAME"
kind load docker-image "localhost:$REGISTRY_PORT/etl-transform:latest" --name "$CLUSTER_NAME"
kind load docker-image "localhost:$REGISTRY_PORT/etl-load:latest" --name "$CLUSTER_NAME"
kind load docker-image "localhost:$REGISTRY_PORT/etl-main:latest" --name "$CLUSTER_NAME"

echo "All images have been built, pushed, and loaded successfully!"