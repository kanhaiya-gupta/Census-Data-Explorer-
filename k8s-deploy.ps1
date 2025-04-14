# PowerShell script for deploying the Census Data Explorer to Kubernetes
$ErrorActionPreference = "Stop"

# Configuration
$NAMESPACE = "census"
$TIMEOUT = 300  # seconds
$CHECK_INTERVAL = 10  # seconds

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

# Function to get pod status
function Get-PodStatus {
    param($namespace)
    $pods = kubectl get pods -n $namespace -o json | ConvertFrom-Json
    foreach ($pod in $pods.items) {
        $status = $pod.status.phase
        $ready = $pod.status.containerStatuses.ready
        $restarts = $pod.status.containerStatuses.restartCount
        Write-Host "Pod: $($pod.metadata.name) - Status: $status - Ready: $ready - Restarts: $restarts"
    }
}

# Function to wait for PVCs to be bound
function Wait-ForPVCs {
    param($namespace)
    $pvcNames = @("census-pvc", "census-results-pvc")
    $allBound = $false
    $startTime = Get-Date
    
    while (-not $allBound -and ((Get-Date) - $startTime).TotalSeconds -lt $TIMEOUT) {
        $allBound = $true
        foreach ($pvcName in $pvcNames) {
            $pvc = kubectl get pvc $pvcName -n $namespace -o json | ConvertFrom-Json
            if ($pvc.status.phase -ne "Bound") {
                $allBound = $false
                Write-Host "Waiting for PVC $pvcName to be bound..."
                break
            }
        }
        if (-not $allBound) {
            Start-Sleep -Seconds $CHECK_INTERVAL
        }
    }
    
    if (-not $allBound) {
        Write-Error "Timeout waiting for PVCs to be bound"
        exit 1
    }
}

# Check for required tools
$requiredTools = @("kubectl", "kind")
foreach ($tool in $requiredTools) {
    if (-not (Test-CommandExists $tool)) {
        Write-Error "Required tool '$tool' is not installed or not in PATH"
        exit 1
    }
}

# Check for required files
$requiredFiles = @(
    "kubernetes/storageclass.yaml",
    "kubernetes/pv.yaml",
    "kubernetes/pvc.yaml",
    "kubernetes/service.yaml",
    "kubernetes/database-deployment.yaml",
    "kubernetes/transform-deployment.yaml",
    "kubernetes/load-deployment.yaml",
    "kubernetes/main-job.yaml",
    "kubernetes/init-dirs.yaml",
    "kubernetes/configmap.yaml"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Error "Required file '$file' not found"
        exit 1
    }
}

# Create namespace if it doesn't exist
Write-Host "Creating namespace '$NAMESPACE'..."
kubectl create namespace $NAMESPACE 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Namespace '$NAMESPACE' already exists or could not be created."
    # Check if namespace exists
    $namespaceExists = kubectl get namespace $NAMESPACE 2>$null
    if (-not $namespaceExists) {
        Write-Error "Failed to create namespace '$NAMESPACE'"
        exit 1
    }
}

# Apply configurations
Write-Host "Applying Kubernetes configurations..."

# Create required directories using a temporary pod
Write-Host "Creating required directories using temporary pod..."
kubectl apply -f kubernetes/init-dirs.yaml

# Wait for the pod to be ready
Write-Host "Waiting for directory creation pod to be ready..."
$startTime = Get-Date
while (((Get-Date) - $startTime).TotalSeconds -lt $TIMEOUT) {
    $podStatus = kubectl get pod init-dirs -n $NAMESPACE -o json | ConvertFrom-Json
    if ($podStatus.status.phase -eq "Running") {
        Write-Host "Directories created successfully"
        break
    }
    Write-Host "Waiting for directory creation pod to be ready..."
    Start-Sleep -Seconds $CHECK_INTERVAL
}

# Delete the temporary pod
Write-Host "Cleaning up temporary pod..."
kubectl delete pod init-dirs -n $NAMESPACE

# Apply StorageClass
Write-Host "Creating storage class..."
kubectl apply -f kubernetes/storageclass.yaml

# Apply PVs
Write-Host "Creating persistent volumes..."
kubectl apply -f kubernetes/pv.yaml

# Apply PVCs
Write-Host "Creating persistent volume claims..."
kubectl apply -f kubernetes/pvc.yaml -n $NAMESPACE

# Wait for PVCs to be bound
Write-Host "Waiting for PVCs to be bound..."
Wait-ForPVCs -namespace $NAMESPACE

# Apply ConfigMap
Write-Host "Creating ConfigMap..."
kubectl apply -f kubernetes/configmap.yaml -n $NAMESPACE

# Apply services
Write-Host "Creating services..."
kubectl apply -f kubernetes/service.yaml -n $NAMESPACE

# Apply deployments
Write-Host "Creating deployments..."
kubectl apply -f kubernetes/database-deployment.yaml -n $NAMESPACE
kubectl apply -f kubernetes/transform-deployment.yaml -n $NAMESPACE
kubectl apply -f kubernetes/load-deployment.yaml -n $NAMESPACE

# Apply main job
Write-Host "Creating main job..."
kubectl apply -f kubernetes/main-job.yaml -n $NAMESPACE

# Wait for resources to be ready
Write-Host "Waiting for resources to be ready (timeout: ${TIMEOUT}s)..."

# Wait for pods with status updates
$startTime = Get-Date
$elapsedTime = 0

while ($elapsedTime -lt $TIMEOUT) {
    Write-Host "`nCurrent pod status (elapsed time: ${elapsedTime}s):"
    Get-PodStatus -namespace $NAMESPACE
    
    # Check if all pods are ready
    $allReady = $true
    $pods = kubectl get pods -n $NAMESPACE -o json | ConvertFrom-Json
    foreach ($pod in $pods.items) {
        if ($pod.status.phase -ne "Running" -or -not $pod.status.containerStatuses.ready) {
            $allReady = $false
            break
        }
    }
    
    if ($allReady) {
        Write-Host "`nAll pods are ready!"
        break
    }
    
    Write-Host "Waiting ${CHECK_INTERVAL}s before next check..."
    Start-Sleep -Seconds $CHECK_INTERVAL
    $elapsedTime = ((Get-Date) - $startTime).TotalSeconds
}

if ($elapsedTime -ge $TIMEOUT) {
    Write-Host "`nTimeout reached. Some pods may not be ready. Current status:"
    Get-PodStatus -namespace $NAMESPACE
    Write-Host "`nChecking pod events for more information..."
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'
    exit 1
}

# Wait for deployments
Write-Host "`nWaiting for deployments to be available..."
kubectl wait --for=condition=Available deployment -l app=census -n $NAMESPACE --timeout=${TIMEOUT}s

# Verify deployment
Write-Host "`nVerifying deployment..."

# Check pods
Write-Host "`nPods:"
kubectl get pods -n $NAMESPACE

# Check services
Write-Host "`nServices:"
kubectl get services -n $NAMESPACE

# Check PVCs
Write-Host "`nPersistent Volume Claims:"
kubectl get pvc -n $NAMESPACE

Write-Host "`nDeployment completed successfully!" 