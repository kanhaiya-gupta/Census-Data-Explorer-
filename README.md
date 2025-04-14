# Census Data Explorer

A distributed application for processing and analyzing census data using multiple microservices.

## Architecture

The application consists of four main services:
1. **Database Service** (Port 8000): Manages SQLite database operations
2. **Transform Service** (Port 8001): Handles data transformation
3. **Load Service** (Port 8002): Manages data loading operations
4. **Main Service** (Port 8003): Orchestrates the overall workflow

## Prerequisites

- Docker
- Docker Compose
- Kubernetes (for Kubernetes deployment)
- kubectl
- PowerShell (for Windows deployment)

## Deployment Options

### Option 1: Docker Compose Deployment

1. Build the Docker images:
```bash
docker-compose build
```

2. Start the services:
```bash
docker-compose up -d
```

3. Verify the services are running:
```bash
docker-compose ps
```

4. Access the services:
- Database: http://localhost:8000
- Transform: http://localhost:8001
- Load: http://localhost:8002
- Main: http://localhost:8003

### Option 2: Kubernetes Deployment

1. Ensure you have a Kubernetes cluster running (e.g., Minikube, Kind, or a cloud provider)

2. Build and push the Docker images to your registry:
```bash
docker build -t census-database -f docker/database/Dockerfile .
docker build -t census-transform -f docker/transform/Dockerfile .
docker build -t census-load -f docker/load/Dockerfile .
docker build -t census-main -f docker/main/Dockerfile .
```

3. Deploy using the provided PowerShell script:
```powershell
.\deploy.ps1
```

4. Verify the deployment:
```bash
kubectl get pods -n census
kubectl get services -n census
```

5. Access the services using port forwarding:
```bash
# Database Service
kubectl port-forward service/census-database -n census 9000:8000

# Transform Service
kubectl port-forward service/census-transform -n census 9001:8001

# Load Service
kubectl port-forward service/census-load -n census 9002:8002

# Main Service
kubectl port-forward service/census-main -n census 9003:8003
```

6. Access the services:
- Database: http://localhost:9000
- Transform: http://localhost:9001
- Load: http://localhost:9002
- Main: http://localhost:9003

## Directory Structure

```
.
├── data/               # Data files
├── results/            # Results directory
├── scripts/            # Python scripts
├── docker/             # Docker configurations
│   ├── database/       # Database service
│   ├── transform/      # Transform service
│   ├── load/          # Load service
│   └── main/          # Main service
├── manifests/          # Kubernetes manifests
│   ├── deployments.yaml
│   ├── storage.yaml
│   └── configmap.yaml
└── deploy.ps1         # Deployment script
```

## Environment Variables

### Database Service
- `DB_PATH`: Path to SQLite database file

### Transform Service
- `DB_PATH`: Path to SQLite database file
- `CSV_PATH`: Path to input CSV file
- `TRANSFORMED_DATA_PATH`: Path to store transformed data

### Load Service
- `DB_PATH`: Path to SQLite database file
- `TRANSFORMED_DATA_PATH`: Path to transformed data file
- `RESULTS_DIR`: Directory to store results

### Main Service
- `DATABASE_SERVICE`: URL of database service
- `TRANSFORM_SERVICE`: URL of transform service
- `LOAD_SERVICE`: URL of load service
- `RESULTS_DIR`: Directory to store results
- `DB_PATH`: Path to SQLite database file
- `CSV_PATH`: Path to input CSV file
- `TRANSFORMED_DATA_PATH`: Path to transformed data file

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   - If you encounter port conflicts, try using different local ports in the port forwarding commands
   - Example: `kubectl port-forward service/census-database -n census 9000:8000`

2. **Pod Not Starting**
   - Check pod logs: `kubectl logs -n census <pod-name>`
   - Check pod status: `kubectl describe pod -n census <pod-name>`

3. **Database Connection Issues**
   - Verify the database file exists and has correct permissions
   - Check database service logs for connection errors

4. **Service Unavailable**
   - Ensure all pods are running: `kubectl get pods -n census`
   - Check service status: `kubectl get services -n census`
   - Verify port forwarding is active

### Cleanup

To remove the deployment:
```bash
# Docker Compose
docker-compose down

# Kubernetes
kubectl delete namespace census
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 