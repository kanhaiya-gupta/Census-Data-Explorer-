# Check if kubectl is installed
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Error "kubectl is not installed. Please install it first."
    exit 1
}

# Check if required manifest files exist
$requiredFiles = @("manifests/storage.yaml", "manifests/deployments.yaml", "manifests/configmap.yaml")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Error "Required file not found: $file"
        exit 1
    }
}

# Create required directories
$directories = @("/data", "/results", "/scripts")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created directory: $dir"
    }
}

# Create namespace
Write-Host "Creating namespace..."
kubectl create namespace census
if ($LASTEXITCODE -ne 0) {
    Write-Host "Namespace already exists, continuing..."
}

# Apply the manifests in the correct order
Write-Host "Applying Kubernetes manifests..."
kubectl apply -f manifests/storage.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to apply storage configuration"
    exit 1
}

kubectl apply -f manifests/configmap.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to apply configmap"
    exit 1
}

kubectl apply -f manifests/deployments.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to apply deployments"
    exit 1
}

# Wait for pods to be ready
Write-Host "Waiting for pods to be ready..."
$timeout = 300  # 5 minutes
$interval = 10  # 10 seconds
$elapsed = 0

while ($elapsed -lt $timeout) {
    $pods = kubectl get pods -n census -o json | ConvertFrom-Json
    $allReady = $true
    
    foreach ($pod in $pods.items) {
        if ($pod.status.phase -ne "Running") {
            $allReady = $false
            Write-Host "Pod $($pod.metadata.name) is not ready yet. Status: $($pod.status.phase)"
            break
        }
    }
    
    if ($allReady) {
        Write-Host "All pods are ready!"
        break
    }
    
    Write-Host "Waiting for pods to be ready... ($elapsed seconds elapsed)"
    Start-Sleep -Seconds $interval
    $elapsed += $interval
}

if ($elapsed -ge $timeout) {
    Write-Error "Timeout waiting for pods to be ready"
    exit 1
}

# Get pod status
Write-Host "Pod Status:"
kubectl get pods -n census

# Get service status
Write-Host "Service Status:"
kubectl get services -n census

Write-Host "Deployment completed successfully!"
Write-Host "You can now access the services using port forwarding:"
Write-Host "Database: kubectl port-forward service/census-database -n census 9000:8000"
Write-Host "Transform: kubectl port-forward service/census-transform -n census 9001:8001"
Write-Host "Load: kubectl port-forward service/census-load -n census 9002:8002"
Write-Host "Main: kubectl port-forward service/census-main -n census 9003:8003" 