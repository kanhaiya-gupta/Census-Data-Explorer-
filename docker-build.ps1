# PowerShell script for building and loading Docker images into Kind cluster
$ErrorActionPreference = "Stop"

# Configuration
$CLUSTER_NAME = "etl-pipeline-cluster"
$REGISTRY_NAME = "kind-registry"
$REGISTRY_PORT = 5001
$SERVICES = @("database", "transform", "load", "main")

# Function to check if a command exists
function Test-CommandExists {
    param($command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $command) { return $true }
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $oldPreference
    }
}

# Check for required tools
$requiredTools = @("docker", "kind", "kubectl", "curl")
foreach ($tool in $requiredTools) {
    if (-not (Test-CommandExists $tool)) {
        Write-Error "Required tool '$tool' is not installed or not in PATH"
        exit 1
    }
}

# Check for required files/directories
$requiredPaths = @(
    "docker/database/Dockerfile",
    "docker/transform/Dockerfile",
    "docker/load/Dockerfile",
    "docker/main/Dockerfile",
    "scripts/database.py",
    "scripts/transform.py",
    "scripts/load.py",
    "scripts/main.py"
)

foreach ($path in $requiredPaths) {
    if (-not (Test-Path $path)) {
        Write-Error "Required file/directory '$path' not found"
        exit 1
    }
}

# Clean up existing cluster if requested
if ($args[0] -eq "--clean") {
    Write-Host "Cleaning up existing Kind cluster..."
    kind delete cluster --name $CLUSTER_NAME
    docker rm -f $REGISTRY_NAME
}

# Ensure Kind cluster exists
if (-not (kind get clusters | Select-String -Pattern $CLUSTER_NAME)) {
    Write-Host "Creating Kind cluster..."
    kind create cluster --name $CLUSTER_NAME --config kubernetes/kind-config.yaml
}

# Set up local Docker registry
Write-Host "Setting up local Docker registry..."
if (-not (docker ps -a | Select-String -Pattern $REGISTRY_NAME)) {
    docker run -d --restart=always -p "${REGISTRY_PORT}:5000" --name $REGISTRY_NAME registry:2
}

# Connect registry to cluster network
docker network connect kind $REGISTRY_NAME

# Verify registry is running
Write-Host "Verifying registry at http://localhost:${REGISTRY_PORT}/v2/..."
$maxRetries = 5
$retryCount = 0
$registryReady = $false

while (-not $registryReady -and $retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:${REGISTRY_PORT}/v2/" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $registryReady = $true
            Write-Host "Registry is responding."
        }
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "Registry not ready, retrying in 5 seconds... (Attempt $retryCount of $maxRetries)"
            Start-Sleep -Seconds 5
        } else {
            Write-Error "Registry failed to respond after $maxRetries attempts"
            exit 1
        }
    }
}

# Function to build and push an image
function Build-Image {
    param(
        [string]$service,
        [bool]$forceRebuild = $false
    )
    
    $imageName = "census-$service"
    $registryImage = "localhost:${REGISTRY_PORT}/$imageName`:latest"
    
    Write-Host "Processing $imageName..."
    
    # Always build the image
    Write-Host "Building $imageName..."
    docker build -t $imageName -f docker/$service/Dockerfile .
    
    # Tag and push to registry
    Write-Host "Tagging and pushing $imageName to registry..."
    docker tag $imageName $registryImage
    docker push $registryImage
    
    # Load into Kind cluster
    Write-Host "Loading $imageName into Kind cluster..."
    kind load docker-image $registryImage --name $CLUSTER_NAME
    
    Write-Host "$imageName processed successfully"
}

# Build and push images
Write-Host "Building and pushing Docker images..."
foreach ($service in $SERVICES) {
    Build-Image -service $service
}

Write-Host "All images have been built, pushed, and loaded successfully." 