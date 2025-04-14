# Census Data Explorer - Docker & Kubernetes Deployment Guide

A comprehensive guide for deploying the Census Data Explorer application using Docker and Kubernetes.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Troubleshooting](#troubleshooting)
5. [Cleanup](#cleanup)

## Prerequisites

### For Docker Deployment
- Docker Engine
- Docker Compose
- Git

### For Kubernetes Deployment
- Docker Engine
- kubectl
- Kubernetes cluster (Minikube, Kind, or cloud provider)
- PowerShell (for Windows deployment)

## Docker Deployment

### 1. Clone the Repository
```bash
git clone <repository-url>
cd census-data-explorer
```

### 2. Build Docker Images
```bash
docker-compose build
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify Deployment
```bash
docker-compose ps
```

### 5. Access Services
- Database: http://localhost:8000
- Transform: http://localhost:8001
- Load: http://localhost:8002
- Main: http://localhost:8003

### 6. View Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs database
docker-compose logs transform
docker-compose logs load
docker-compose logs main
```

## Kubernetes Deployment

### 1. Build Docker Images
```bash
# Build all images
docker build -t census-database -f docker/database/Dockerfile .
docker build -t census-transform -f docker/transform/Dockerfile .
docker build -t census-load -f docker/load/Dockerfile .
docker build -t census-main -f docker/main/Dockerfile .
```

### 2. Deploy Using PowerShell Script
```powershell
.\deploy.ps1
```

### 3. Verify Deployment
```bash
# Check pods
kubectl get pods -n census

# Check services
kubectl get services -n census

# Check persistent volume claims
kubectl get pvc -n census
```

### 4. Access Services

#### Important Note on Port Forwarding
Due to PowerShell limitations and port conflicts, follow these steps carefully:

1. **Do not use the `&` operator** to combine port forwarding commands
2. **Use different local ports** (9000-9003) to avoid conflicts
3. **Run each command in a separate terminal window**

#### Open four separate terminal windows and run:

Window 1 (Database):
```bash
kubectl port-forward service/census-database -n census 9000:8000
```

Window 2 (Transform):
```bash
kubectl port-forward service/census-transform -n census 9001:8001
```

Window 3 (Load):
```bash
kubectl port-forward service/census-load -n census 9002:8002
```

Window 4 (Main):
```bash
kubectl port-forward service/census-main -n census 9003:8003
```

#### Access Services
- Database: http://localhost:9000
- Transform: http://localhost:9001
- Load: http://localhost:9002
- Main: http://localhost:9003

### 5. Monitor Deployment
```bash
# Watch pod status
kubectl get pods -n census -w

# View pod logs
kubectl logs -n census deployment/census-database
kubectl logs -n census deployment/census-transform
kubectl logs -n census deployment/census-load
kubectl logs -n census deployment/census-main
```

## Troubleshooting

### Common Issues and Solutions

1. **Port Forwarding Issues**
   - Error: "Only one usage of each socket address"
     - Solution: 
       - Kill any existing port forwarding processes
       - Use different local ports (9000-9003)
       - Run each port forward in a separate terminal
   - Error: "lost connection to pod"
     - Solution: 
       - Check if pod is still running: `kubectl get pods -n census`
       - Restart the port forwarding command
       - Verify pod status: `kubectl describe pod -n census <pod-name>`

2. **Pod Not Starting**
   - Check pod status: `kubectl describe pod -n census <pod-name>`
   - Check pod logs: `kubectl logs -n census <pod-name>`
   - Verify PVC is bound: `kubectl get pvc -n census`

3. **Database Connection Issues**
   - Verify database file permissions
   - Check database service logs
   - Ensure PVC is properly mounted

4. **Service Unavailable**
   - Check service status: `kubectl get services -n census`
   - Verify pod status: `kubectl get pods -n census`
   - Check service endpoints: `kubectl get endpoints -n census`

### Debugging Steps

1. **Check Cluster Status**
```bash
kubectl cluster-info
kubectl get nodes
```

2. **Check Resource Usage**
```bash
kubectl top nodes
kubectl top pods -n census
```

3. **Check Events**
```bash
kubectl get events -n census
```

4. **Check Persistent Volumes**
```bash
kubectl get pv
kubectl get pvc -n census
```

## Cleanup

### Docker Cleanup
```bash
# Stop and remove containers
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Kubernetes Cleanup
```bash
# Delete namespace (this will remove all resources)
kubectl delete namespace census

# Delete persistent volumes
kubectl delete pv census-data-pv

# Verify cleanup
kubectl get all -n census
kubectl get pv
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/) 