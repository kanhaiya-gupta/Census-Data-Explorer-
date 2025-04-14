# Census Data Explorer - Kubernetes Deployment Guide

## Overview

This document provides comprehensive documentation for deploying and managing the Census Data Explorer application using Kubernetes. The application consists of several microservices that work together to process and analyze census data.

## System Architecture

The system is composed of the following components:

1. **Database Service**: Manages the SQLite database containing census data
2. **Transform Service**: Processes and transforms the census data
3. **Load Service**: Loads the transformed data and generates visualizations
4. **Main Service**: Orchestrates the ETL (Extract, Transform, Load) pipeline

## Prerequisites

- Docker
- Kubernetes (using Kind)
- kubectl
- PowerShell (for Windows users)

## PowerShell Setup

Before running the scripts, you need to configure PowerShell's execution policy:

1. **Check Current Policy**:
   ```powershell
   Get-ExecutionPolicy
   ```

2. **Set Execution Policy** (requires Administrator privileges):
   ```powershell
   # For current user only (recommended)
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   
   # Or for all users (requires Administrator PowerShell)
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
   ```

3. **Verify the Change**:
   ```powershell
   Get-ExecutionPolicy
   ```

The `RemoteSigned` policy allows you to run local scripts while still maintaining security by requiring downloaded scripts to be signed by a trusted publisher.

If you prefer not to change the execution policy, you can also run the script by typing its contents directly in PowerShell or using the following command:

```powershell
powershell -ExecutionPolicy Bypass -File .\docker-build.ps1
```

## Deployment Scripts

### docker-build.ps1

This script handles building and pushing Docker images to the local registry:

```powershell
# Run with execution policy bypass if needed
powershell -ExecutionPolicy Bypass -File .\docker-build.ps1
```

The script performs the following actions:
1. Checks for required tools (docker, kind, kubectl)
2. Sets up the local Docker registry
3. Builds and pushes images for all services:
   - census-database
   - census-transform
   - census-load
   - census-main

### k8s-deploy.ps1

This script handles the Kubernetes deployment:

```powershell
# Run with execution policy bypass if needed
powershell -ExecutionPolicy Bypass -File .\k8s-deploy.ps1
```

The script performs the following actions in sequence:

1. **Create Namespace**:
   ```powershell
   kubectl create namespace census
   ```

2. **Apply Configurations**:
   ```powershell
   # Apply persistent volume claims
   kubectl apply -f kubernetes/pvc.yaml -n census
   
   # Apply service definitions
   kubectl apply -f kubernetes/service.yaml -n census
   
   # Apply deployments
   kubectl apply -f kubernetes/database-deployment.yaml -n census
   kubectl apply -f kubernetes/transform-deployment.yaml -n census
   kubectl apply -f kubernetes/load-deployment.yaml -n census
   
   # Apply main job
   kubectl apply -f kubernetes/main-job.yaml -n census
   ```

3. **Wait for Resources**:
   ```powershell
   # Wait for pods to be ready
   kubectl wait --for=condition=Ready pod -l app=census -n census --timeout=300s
   
   # Wait for services to be available
   kubectl wait --for=condition=Available deployment -l app=census -n census --timeout=300s
   ```

4. **Verify Deployment**:
   ```powershell
   # Check pod status
   kubectl get pods -n census
   
   # Check service status
   kubectl get services -n census
   
   # Check persistent volume claims
   kubectl get pvc -n census
   ```

5. **Create External Access**:
   ```powershell
   # Create NodePort service for external access
   kubectl apply -f kubernetes/main-external-service.yaml -n census
   ```

Expected Output:
```powershell
PS> .\k8s-deploy.ps1
namespace/census created
persistentvolumeclaim/census-pvc created
service/census-database created
service/census-transform created
service/census-load created
service/census-main created
deployment.apps/census-database created
deployment.apps/census-transform created
deployment.apps/census-load created
job.batch/census-main created
pod/census-database-7b8f6c8c5-4xq2z condition met
pod/census-transform-6d8f7c9d-2w3x4 condition met
pod/census-load-5f8g9h2j-1y2z3 condition met
deployment.apps/census-database condition met
deployment.apps/census-transform condition met
deployment.apps/census-load condition met
NAME                              READY   STATUS    RESTARTS   AGE
census-database-7b8f6c8c5-4xq2z   1/1     Running   0          5m
census-transform-6d8f7c9d-2w3x4   1/1     Running   0          5m
census-load-5f8g9h2j-1y2z3       1/1     Running   0          5m
NAME                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
census-database     ClusterIP   10.96.123.45    <none>        8000/TCP   5m
census-transform    ClusterIP   10.96.234.56    <none>        8001/TCP   5m
census-load         ClusterIP   10.96.345.67    <none>        8002/TCP   5m
census-main         ClusterIP   10.96.456.78    <none>        8003/TCP   5m
NAME         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
census-pvc   Bound    pvc-12345678-90ab-cdef-0123-456789abcdef   1Gi        RWO            standard       5m
```

Troubleshooting the Deployment Script:

1. **If Namespace Creation Fails**:
   ```powershell
   # Check if namespace already exists
   kubectl get namespace census
   
   # Delete and recreate if needed
   kubectl delete namespace census
   kubectl create namespace census
   ```

2. **If PVC Creation Fails**:
   ```powershell
   # Check storage class
   kubectl get storageclass
   
   # Check existing PVCs
   kubectl get pvc -n census
   ```

3. **If Deployments Fail**:
   ```powershell
   # Check deployment status
   kubectl describe deployment -n census
   
   # Check pod events
   kubectl describe pod -n census -l app=census
   ```

4. **If Services Fail**:
   ```powershell
   # Check service status
   kubectl describe service -n census
   
   # Check endpoints
   kubectl get endpoints -n census
   ```

## Configuration Files

The following configuration files are used:

- `kubernetes/service.yaml`: Defines the services
- `kubernetes/database-deployment.yaml`: Database service deployment
- `kubernetes/transform-deployment.yaml`: Transform service deployment
- `kubernetes/load-deployment.yaml`: Load service deployment
- `kubernetes/main-job.yaml`: Main service job configuration
- `kubernetes/pvc.yaml`: Persistent volume claims
- `kubernetes/database-schema-init.yaml`: Database schema initialization

## Deployment Steps

1. **Create Kind Cluster**:
   ```powershell
   kind create cluster --config kubernetes/kind-config.yaml
   ```

2. **Build and Push Docker Images**:
   ```powershell
   ./docker-build.ps1
   ```

3. **Apply Kubernetes Configurations**:
   ```powershell
   ./k8s-deploy.ps1
   ```

4. **Verify Deployment**:
   ```powershell
   kubectl get pods -n census
   kubectl get services -n census
   ```

## Example Run

Here's an example of a complete deployment and verification process:

### 1. Deploy the Application

```powershell
# Create Kind cluster
kind create cluster --config kubernetes/kind-config.yaml

# Build and push Docker images
./docker-build.ps1

# Deploy to Kubernetes
./k8s-deploy.ps1
```

Expected output:
```powershell
Creating namespace 'census'...
namespace/census created
Applying Kubernetes configurations...
Creating required directories using temporary pod...
pod/init-dirs created
Waiting for directory creation pod to be ready...
Directories created successfully
Cleaning up temporary pod...
pod "init-dirs" deleted
Creating storage class...
storageclass.storage.k8s.io/census-storage unchanged
Creating persistent volumes...
persistentvolume/census-pv created
persistentvolume/census-results-pv created
Creating persistent volume claims...
persistentvolumeclaim/census-pvc created
persistentvolumeclaim/census-results-pvc created
Waiting for PVCs to be bound...
Creating ConfigMap...
configmap/census-scripts created
configmap/census-data created
Creating services...
service/census-database created
service/census-transform created
service/census-load created
service/census-main created
Creating deployments...
deployment.apps/census-database created
deployment.apps/census-transform created
deployment.apps/census-load created
Creating main job...
deployment.apps/census-main created
Waiting for resources to be ready (timeout: 300s)...
```

### 2. Verify Pod Status

```powershell
kubectl get pods -n census
```

Expected output:
```powershell
NAME                                READY   STATUS    RESTARTS   AGE
census-database-789445dd5c-xrkvq    1/1     Running   0          5m40s
census-load-7b76f87b97-vb2bq        1/1     Running   0          5m39s
census-main-d77dbcd88-26mbj         1/1     Running   0          5m39s
census-transform-54546b7bbb-wdq9h   1/1     Running   0          5m39s
```

### 3. Check Results

```powershell
# List files in results directory
kubectl exec -n census deployment/census-load -- ls -l /results
```

Expected output:
```powershell
total 8
-rw-r--r-- 1 root root 107 Apr 14 13:39 etl_results.json
-rw-r--r-- 1 root root  60 Apr 14 13:39 load_results.json
```

### 4. View Results Content

```powershell
# View ETL results
kubectl exec -n census deployment/census-load -- cat /results/etl_results.json
```

Expected output:
```powershell
{"status": "success", "message": "ETL process completed successfully", "year": 2020, "state": "California"}
```

### 5. Check Database Contents

```powershell
# List tables
kubectl exec -n census deployment/census-database -- sqlite3 /data/census.sqlite ".tables"
```

Expected output:
```powershell
census      state_fact
```

### 6. Access Services

```powershell
# Forward ports for all services
kubectl port-forward service/census-database -n census 8000:8000
kubectl port-forward service/census-transform -n census 8001:8001
kubectl port-forward service/census-load -n census 8002:8002
kubectl port-forward service/census-main -n census 8003:8003
```

Expected output for each service:
```powershell
Forwarding from 127.0.0.1:8000 -> 8000
Forwarding from [::1]:8000 -> 8000
```

### 7. Test API Endpoints

```powershell
# Check service health
Invoke-WebRequest -Uri http://localhost:8003/health

# Get transformed data
Invoke-WebRequest -Uri http://localhost:8003/results | ConvertFrom-Json
```

Expected output:
```powershell
StatusCode        : 200
StatusDescription : OK
Content           : {"status": "success", "message": "ETL process completed successfully", "year": 2020, "state": "California"}
```

### 8. Troubleshooting Example

If you encounter port forwarding issues:

```powershell
# Check if port is already in use
Get-Process | Where-Object { $_.ProcessName -like "*kubectl*" } | Stop-Process

# Try with a different port
kubectl port-forward service/census-database -n census 8004:8000
```

Expected output:
```powershell
Forwarding from 127.0.0.1:8004 -> 8000
Forwarding from [::1]:8004 -> 8000
```

### 9. Cleanup Example

```powershell
# Delete the namespace (this will remove all resources)
kubectl delete namespace census

# Delete the Kind cluster
kind delete cluster
```

Expected output:
```powershell
namespace "census" deleted
Deleting cluster "kind" ...
```

## Successful Deployment State

When the application is running perfectly, you should see the following indicators:

1. **Port Forwarding Active**:
   ```powershell
   PS> kubectl port-forward service/census-main-external -n census 8003:8003
   Forwarding from 127.0.0.1:8003 -> 8003
   Forwarding from [::1]:8003 -> 8003
   Handling connection for 8003
   ```

2. **All Services Running**:
   ```powershell
   PS> kubectl get pods -n census
   NAME                              READY   STATUS    RESTARTS   AGE
   census-database-7b8f6c8c5-4xq2z   1/1     Running   0          5m
   census-transform-6d8f7c9d-2w3x4   1/1     Running   0          5m
   census-load-5f8g9h2j-1y2z3       1/1     Running   0          5m
   ```

3. **Services Accessible**:
   - Database Service: `http://localhost:8000` - Responds with health check
   - Transform Service: `http://localhost:8001` - Ready for data transformation
   - Load Service: `http://localhost:8002` - Ready to generate visualizations
   - Main Service: `http://localhost:8003` - Ready to orchestrate ETL pipeline

4. **Database Initialized**:
   ```powershell
   PS> kubectl get jobs -n census
   NAME                    COMPLETIONS   DURATION   AGE
   database-schema-init    1/1           4s         10s
   ```

5. **Volume Mounts Working**:
   ```powershell
   PS> kubectl get pvc -n census
   NAME         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
   census-pvc   Bound    pvc-12345678-90ab-cdef-0123-456789abcdef   1Gi        RWO            standard       5m
   ```

6. **Network Connectivity**:
   - All services can communicate with each other
   - External access is properly configured
   - Port forwarding is active and stable

7. **Log Output**:
   - No error messages in any service logs
   - Regular heartbeat messages from services
   - Successful connection messages
   - Proper initialization sequences

8. **Resource Usage**:
   - CPU and memory usage within expected ranges
   - No resource throttling or eviction events
   - Stable pod states

To verify the system is in this state:

```powershell
# Check all components
kubectl get all -n census

# Check logs for errors
kubectl logs -n census deployment/census-database
kubectl logs -n census deployment/census-transform
kubectl logs -n census deployment/census-load

# Verify service health
Invoke-WebRequest -Uri http://localhost:8000/health
Invoke-WebRequest -Uri http://localhost:8001/health
Invoke-WebRequest -Uri http://localhost:8002/health
Invoke-WebRequest -Uri http://localhost:8003/health
```

If all these checks pass, the system is in a healthy state and ready to process census data through the ETL pipeline. 