#!/bin/bash
set -e

# Navigate to script's directory
cd "$(dirname "$0")"

# Configuration variables
CLUSTER_NAME="etl-pipeline-cluster"
REGISTRY_NAME="kind-registry"
REGISTRY_PORT="5000"
FORCE_REBUILD=${FORCE_REBUILD:-false}
CLEANUP_CLUSTER=${CLEANUP_CLUSTER:-false}
SERVICES=("database" "transform" "load" "main")
IMAGE_PREFIX="census"
IMAGE_TAG="latest"

# Check for required tools
for cmd in docker kind kubectl curl ss; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# Check for required files and directories
if [ ! -f "kubernetes/kind-config.yaml" ]; then
    echo "Error: kubernetes/kind-config.yaml not found in $(pwd)"
    exit 1
fi

if [ ! -d "docker" ]; then
    echo "Error: docker/ directory not found in $(pwd)"
    exit 1
fi

for service in "${SERVICES[@]}"; do
    if [ ! -f "docker/$service/Dockerfile" ]; then
        echo "Error: docker/$service/Dockerfile not found"
        exit 1
    fi
done

# Clean up existing cluster if requested
if [ "$CLEANUP_CLUSTER" = "true" ]; then
    if kind get clusters | grep -q "$CLUSTER_NAME"; then
        echo "Deleting existing Kind cluster '$CLUSTER_NAME'..."
        kind delete cluster --name "$CLUSTER_NAME"
    fi
fi

# Ensure Kind cluster exists
if ! kind get clusters | grep -q "$CLUSTER_NAME"; then
    echo "Creating Kind cluster '$CLUSTER_NAME'..."
    kind create cluster --name "$CLUSTER_NAME" --config kubernetes/kind-config.yaml
else
    echo "Kind cluster '$CLUSTER_NAME' already exists."
fi

# Set up local registry
if docker ps -a -q -f name="$REGISTRY_NAME" | grep -q .; then
    if ! docker ps -q -f name="$REGISTRY_NAME" | grep -q .; then
        echo "Removing non-running '$REGISTRY_NAME' container..."
        docker rm -f "$REGISTRY_NAME"
    fi
fi

if ! docker ps -q -f name="$REGISTRY_NAME" | grep -q .; then
    echo "Starting local registry on port $REGISTRY_PORT..."
    for attempt in {1..3}; do
        if docker run -d -p "$REGISTRY_PORT:$REGISTRY_PORT" --name "$REGISTRY_NAME" registry:2; then
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
    # Connect to Kind network
    if ! docker network connect kind "$REGISTRY_NAME" 2>/dev/null; then
        echo "Registry already connected to kind network."
    fi
else
    echo "Local registry '$REGISTRY_NAME' already running."
fi

# Verify registry
echo "Verifying registry at http://localhost:$REGISTRY_PORT/v2/..."
for attempt in {1..5}; do
    if curl -s -f http://localhost:$REGISTRY_PORT/v2/ > /dev/null; then
        echo "Registry is responding."
        break
    else
        echo "Attempt $attempt: Registry not responding. Retrying in 5 seconds..."
        sleep 5
    fi
    if [ $attempt -eq 5 ]; then
        echo "Error: Registry at localhost:$REGISTRY_PORT is not responding after $attempt attempts."
        exit 1
    fi
done

# Function to build and push images
build_image() {
    local service="$1"
    local dockerfile_path="docker/$service/Dockerfile"
    local image_name="${IMAGE_PREFIX}-${service}:${IMAGE_TAG}"
    local registry_image="localhost:${REGISTRY_PORT}/${image_name}"

    # Build image
    if [ "$FORCE_REBUILD" = "true" ] || ! docker image inspect "$registry_image" > /dev/null 2>&1; then
        echo "Building image: $registry_image"
        docker build -t "$registry_image" -f "$dockerfile_path" .
    else
        echo "Image $registry_image already exists, skipping build."
    fi

    # Push image
    echo "Pushing image: $registry_image"
    docker push "$registry_image"

    # Load into Kind
    echo "Loading image into Kind cluster: $registry_image"
    kind load docker-image "$registry_image" --name "$CLUSTER_NAME"
}

# Build and push all images
echo "Building and pushing Docker images..."
for service in "${SERVICES[@]}"; do
    build_image "$service"
done

echo "All images have been built, pushed, and loaded successfully!"