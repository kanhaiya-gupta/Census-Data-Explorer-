# 🧮 Census ETL Pipeline

This project implements an ETL (Extract, Transform, Load) pipeline for analyzing U.S. Census data using Python, SQLAlchemy, Pandas, and Matplotlib. It extracts data from a CSV file, transforms it, loads it into a SQLite database, and generates a markdown report with visualizations.

## 📂 Project Structure

```
census-data-explorer/
├── data/
│   ├── census.csv
│   ├── census.sqlite
│   └── transformed_data.json
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── transform.py
│   ├── load.py
│   └── visualization.py
├── scripts/
│   ├── database.py
│   ├── load.py
│   ├── main.py
│   ├── transform.py
├── tests/
│   ├── test_database.py
│   ├── test_load.py
│   ├── test_transform.py
│   └── test_visualization.py
├── results/
│   ├── census_report.json
│   ├── census_report.md
│   └── pop_change_plot.png
├── notebooks/
│   ├── ETL_Pipeline.ipynb
│   └── others...
├── docker/
│   ├── database/
│   ├── load/
│   ├── main/
│   └── transform/
├── kubernetes/
│   ├── census-data-configmap.yaml
│   └── others...
├── docs/
│   ├── README.md
│   ├── README_Kubernetes.md
│   └── requirements.txt
├── requirements.txt
├── main_serial.py
├── docker-compose.yaml
├── LICENSE
└── various scripts (e.g., docker-build.sh, k8s-deploy.sh)
```

## 🚀 Running the Pipeline Serially

### Prerequisites

1. **Python 3.8+**:
   Verify installation:
   ```bash
   python --version
   ```

2. **Dependencies**:
   Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Data Files**:
   Ensure the following exist:
   - `data/census.csv`
   - `data/census.sqlite`

### Steps to Run

1. **Set Up Virtual Environment (Recommended)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute the Pipeline**:
   Run the main script:
   ```bash
   python main_serial.py
   ```
   This will:
   - Extract data from `data/census.csv`.
   - Transform data using Pandas and SQLAlchemy.
   - Load results into `data/census.sqlite`.
   - Generate outputs in `results/`:
     - `census_report.md`: Markdown report.
     - `pop_change_plot.png`: Population change visualization.
     - `census_report.json`: JSON summary.

4. **Run Tests (Optional)**:
   Validate the code:
   ```bash
   pytest tests/
   ```

### 📊 Output

- **Reports**: `results/census_report.md` and `results/census_report.json`.
- **Visualization**: `results/pop_change_plot.png` (bar chart of population changes).
- **Database**: Updated `data/census.sqlite` with transformed data.

Sample report contents:
- Average age by gender.
- Female population percentage by state.
- Top 10 states by population growth.

### 🚨 Error Handling

The pipeline handles:
- Missing files.
- Invalid database connections.
- Data formatting errors.

Logs are generated in the console for debugging.

---

### **README_Kubernetes.md**

# 🌐 Census ETL Pipeline - Kubernetes Deployment

This guide explains how to deploy the Census ETL Pipeline as a set of microservices on Kubernetes using Kind. The pipeline processes U.S. Census data through coordinated services.

## 🏗️ System Architecture

The application consists of four microservices:
1. **Database Service**: Manages the SQLite database (`census.sqlite`).
2. **Transform Service**: Cleans and processes census data.
3. **Load Service**: Loads transformed data and generates visualizations.
4. **Main Service**: Orchestrates the ETL pipeline as a job.

## 📋 Prerequisites

- **Docker**: For building images.
- **Kind**: For local Kubernetes clusters.
- **kubectl**: For interacting with Kubernetes.
- **bash or PowerShell**: For running scripts.

## 🛠️ Setup

### 1. Configure Execution Policy (PowerShell Users)

For Windows users running PowerShell scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Alternatively, bypass for single runs:
```powershell
powershell -ExecutionPolicy Bypass -File .\script.ps1
```

### 2. Verify Tools

Ensure Docker, Kind, and kubectl are installed:
```bash
docker --version
kind --version
kubectl version --client
```

## 🚀 Deployment Steps

### 1. Create Kind Cluster

Set up a local Kubernetes cluster:
```bash
kind create cluster --config kubernetes/kind-config.yaml
```

### 2. Build Docker Images

Build and push images to the local registry:
```bash
./docker-build.sh  # Or .\docker-build.ps1 on Windows
```
This creates images:
- `census-database`
- `census-transform`
- `census-load`
- `census-main`

### 3. Deploy to Kubernetes

Apply configurations and deploy services:
```bash
./k8s-deploy.sh  # Or .\k8s-deploy.ps1 on Windows
```
This:
- Creates the `census` namespace.
- Sets up persistent volumes (`pvc.yaml`, `results-pvc.yaml`).
- Deploys services (`service.yaml`).
- Launches deployments (`database-deployment.yaml`, `transform-deployment.yaml`, `load-deployment.yaml`).
- Runs the main job (`main-job.yaml`).

### 4. Verify Deployment

Check pod status:
```bash
kubectl get pods -n census
```
Expected output:
```
NAME                              READY   STATUS    RESTARTS   AGE
census-database-7b8f6c8c5-4xq2z   1/1     Running   0          5m
census-transform-6d8f7c9d-2w3x4   1/1     Running   0          5m
census-load-5f8g9h2j-1y2z3       1/1     Running   0          5m
census-main-abc123456-xyz789      0/1     Completed 0          5m
```

Check services:
```bash
kubectl get services -n census
```
Expected output:
```
NAME                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
census-database     ClusterIP   10.96.123.45    <none>        8000/TCP   5m
census-transform    ClusterIP   10.96.234.56    <none>        8001/TCP   5m
census-load         ClusterIP   10.96.345.67    <none>        8002/TCP   5m
census-main         ClusterIP   10.96.456.78    <none>        8003/TCP   5m
```

### 5. Access Results

Forward ports to access services locally:
```bash
kubectl port-forward service/census-load -n census 8002:8002
```
Check results:
```bash
kubectl exec -n census deployment/census-load -- cat /results/census_report.json
```
Expected output:
```json
{"status": "success", "message": "ETL process completed", "year": 2020, "state": "California"}
```

View visualization:
```bash
kubectl cp census-load-5f8g9h2j-1y2z3:/results/pop_change_plot.png ./pop_change_plot.png -n census
```

### 6. Check Database

Verify database tables:
```bash
kubectl exec -n census deployment/census-database -- sqlite3 /data/census.sqlite ".tables"
```
Expected output:
```
census      state_fact
```

## 🛑 Cleanup

Remove resources:
```bash
kubectl delete namespace census
kind delete cluster
```

## 🔍 Troubleshooting

- **Pods Not Running**:
  ```bash
  kubectl describe pod -n census -l app=census
  kubectl logs -n census <pod-name>
  ```

- **PVC Issues**:
  ```bash
  kubectl get pvc -n census
  kubectl describe pvc -n census
  ```

- **Service Access**:
  Ensure ports are not in use:
  ```bash
  netstat -tulnp | grep 8000  # Linux
  netstat -aon | findstr 8000  # Windows
  ```

## ✅ Successful Deployment

A healthy deployment shows:
- All pods in `Running` or `Completed` (for main job) status.
- Services responding on ports 8000–8003.
- Persistent volumes bound.
- No errors in logs:
  ```bash
  kubectl logs -n census deployment/census-database
  ```
- Results generated in `/results/` (e.g., `census_report.md`, `pop_change_plot.png`).

## 📊 Output

Same as serial run, stored in Kubernetes persistent volume:
- `results/census_report.md`
- `results/census_report.json`
- `results/pop_change_plot.png`

---

### Notes on Changes

1. **Clarity and Conciseness**:
   - Removed redundant steps and simplified language.
   - Focused on essential commands and outputs.
   - Unified terminology (e.g., "main_serial.py" for serial run).

2. **Structure**:
   - Separated serial and Kubernetes instructions into distinct files for clarity.
   - Aligned project structure with the provided `ls -R` output.

3. **Accuracy**:
   - Updated paths (e.g., `requirements.txt` at root, not `docs/`).
   - Included all microservices and their roles.
   - Corrected script references (e.g., `main_serial.py` vs. `main.py`).

4. **User Experience**:
   - Added clear prerequisites and verification steps.
   - Included troubleshooting for common issues.
   - Streamlined deployment commands with expected outputs.
