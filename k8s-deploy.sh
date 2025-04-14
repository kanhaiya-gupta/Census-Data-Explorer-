#!/bin/bash
set -e

# Configuration
CLUSTER_NAME="etl-pipeline-cluster"
REGISTRY_PORT=5000
REGISTRY_NAME="kind-registry"
NAMESPACE="census"

# Check if cluster exists
if ! kind get clusters | grep -q "$CLUSTER_NAME"; then
    echo "Error: Kind cluster '$CLUSTER_NAME' does not exist."
    echo "Please run docker-build.sh first to create the cluster and build images."
    exit 1
fi

# Create namespace if it doesn't exist
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "Creating namespace '$NAMESPACE'..."
    kubectl create namespace "$NAMESPACE"
fi

# Apply manifests in correct order
echo "Applying Kubernetes manifests..."

# 1. Storage
echo "Setting up storage..."
kubectl apply -f kubernetes/pv.yaml -n "$NAMESPACE"
kubectl apply -f kubernetes/pvc.yaml -n "$NAMESPACE"

# 2. Services
echo "Setting up services..."
kubectl apply -f kubernetes/service.yaml -n "$NAMESPACE"

# 3. Deployments
echo "Deploying services..."
kubectl apply -f kubernetes/database-deployment.yaml -n "$NAMESPACE"
kubectl apply -f kubernetes/transform-deployment.yaml -n "$NAMESPACE"
kubectl apply -f kubernetes/load-deployment.yaml -n "$NAMESPACE"

# 4. Main job
echo "Deploying main job..."
kubectl apply -f kubernetes/main-job.yaml -n "$NAMESPACE"

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/census-database -n "$NAMESPACE"
kubectl wait --for=condition=available --timeout=300s deployment/census-transform -n "$NAMESPACE"
kubectl wait --for=condition=available --timeout=300s deployment/census-load -n "$NAMESPACE"

# Get service URLs
echo "Service URLs:"
echo "Database: http://localhost:8000"
echo "Transform: http://localhost:8001"
echo "Load: http://localhost:8002"
echo "Main: http://localhost:8003"

# Set up port forwarding
echo "Setting up port forwarding..."
kubectl port-forward service/census-database 8000:8000 -n "$NAMESPACE" &
kubectl port-forward service/census-transform 8001:8001 -n "$NAMESPACE" &
kubectl port-forward service/census-load 8002:8002 -n "$NAMESPACE" &
kubectl port-forward service/census-main 8003:8003 -n "$NAMESPACE" &

echo "Kubernetes deployment completed successfully!"
echo "To run the ETL pipeline, send a POST request to:"
echo "curl -X POST http://localhost:8003/process"