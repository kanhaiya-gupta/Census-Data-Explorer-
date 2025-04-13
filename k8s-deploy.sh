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

if [ ! -d "kubernetes" ]; then
    echo "Error: kubernetes/ directory not found in $(pwd)"
    exit 1
fi

# Check for required Dockerfiles
for component in database transform load main; do
    if [ ! -f "docker/$component/Dockerfile" ]; then
        echo "Error: docker/$component/Dockerfile not found"
        exit 1
    fi
done

# Check for required Kubernetes manifests
for manifest in pvc.yaml database-deployment.yaml transform-deployment.yaml load-deployment.yaml service.yaml main-job.yaml; do
    if [ ! -f "kubernetes/$manifest" ]; then
        echo "Error: kubernetes/$manifest not found"
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

# Check if port is in use
if lsof -i :"$REGISTRY_PORT" > /dev/null 2>&1; then
    echo "Error: Port $REGISTRY_PORT is already in use."
    echo "Run 'lsof -i :$REGISTRY_PORT' or 'docker ps -a --format \"{{.ID}}\t{{.Names}}\t{{.Ports}}\" | grep $REGISTRY_PORT' to identify the process."
    exit 1
fi

# Clean up any existing kind-registry containers
if docker ps -a -q -f name="$REGISTRY_NAME" | grep -q .; then
    echo "Removing existing '$REGISTRY_NAME' containers..."
    docker rm -f "$REGISTRY_NAME"
fi

# Start registry
echo "Starting local registry on port $REGISTRY_PORT..."
for attempt in {1..3}; do
    if docker run -d -p "$REGISTRY_PORT:5000" --name "$REGISTRY_NAME" --network kind registry:2 > /dev/null; then
        echo "Registry started successfully (attempt $attempt)."
        break
    else
        echo "Attempt $attempt: Failed to start registry."
        docker rm -f "$REGISTRY_NAME" > /dev/null 2>&1 || true
        sleep 5
        if [ $attempt -eq 3 ]; then
            echo "Error: Failed to start registry after $attempt attempts."
            echo "Check Docker status with 'docker info' or port conflicts with 'lsof -i :$REGISTRY_PORT'."
            exit 1
        fi
    fi
done

# Connect to kind network
docker network connect kind "$REGISTRY_NAME" || echo "Already connected"

# Verify registry
if curl -s http://localhost:$REGISTRY_PORT/v2/ > /dev/null; then
    echo "Registry at localhost:$REGISTRY_PORT is accessible."
else
    echo "Warning: Registry at localhost:$REGISTRY_PORT is not responding."
    echo "Continuing, but this may cause issues."
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
    docker push "$tag" || {
        echo "Error: Failed to push $tag. Check registry status."
        exit 1
    }
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

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f kubernetes/pvc.yaml
kubectl apply -f kubernetes/database-deployment.yaml
kubectl apply -f kubernetes/transform-deployment.yaml
kubectl apply -f kubernetes/load-deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/main-job.yaml

# Initialize data in PVC (if data files exist)
if [ -f "data/census.sqlite" ] && [ -f "data/census.csv" ]; then
    echo "Initializing data in PVC..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: data-init
spec:
  containers:
  - name: data-init
    image: busybox
    command: ["sh", "-c", "cp /tmp/census.sqlite /tmp/census.csv /data/ && sleep 3600"]
    volumeMounts:
    - name: data-volume
      mountPath: /data
    - name: tmp-volume
      mountPath: /tmp
  volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: etl-data-pvc
  - name: tmp-volume
    hostPath:
      path: /mnt/c/Users/kanha/Independent_Research/Census Data Explorer/data
EOF
    echo "Data initialization pod created. Check status with 'kubectl get pods data-init'."
else
    echo "Warning: data/census.sqlite or data/census.csv not found. Skipping data initialization."
fi

echo "Kubernetes deployment completed successfully!"