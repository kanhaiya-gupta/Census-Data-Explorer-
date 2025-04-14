import logging
import os
import requests
import time
from fastapi import FastAPI, HTTPException
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Service URLs from environment variables
DATABASE_SERVICE = os.getenv("DATABASE_SERVICE", "http://database:8000")
TRANSFORM_SERVICE = os.getenv("TRANSFORM_SERVICE", "http://transform:8001")
LOAD_SERVICE = os.getenv("LOAD_SERVICE", "http://load:8002")

def wait_for_service(url, max_retries=30, retry_interval=2):
    """Wait for a service to become available."""
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{url}/health")
            if response.status_code == 200:
                logger.info(f"Service at {url} is available")
                return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries}: Service at {url} not ready: {e}")
        time.sleep(retry_interval)
    return False

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/process")
async def process_data():
    """Main endpoint to coordinate the data processing pipeline."""
    try:
        # Wait for all services to be available
        services = {
            "database": DATABASE_SERVICE,
            "transform": TRANSFORM_SERVICE,
            "load": LOAD_SERVICE
        }
        
        for service_name, url in services.items():
            if not wait_for_service(url):
                raise HTTPException(
                    status_code=503,
                    detail=f"Service {service_name} at {url} is not available"
                )

        # Step 1: Transform data
        logger.info("Starting data transformation")
        transform_response = requests.post(f"{TRANSFORM_SERVICE}/transform")
        if transform_response.status_code != 200:
            raise HTTPException(
                status_code=transform_response.status_code,
                detail=f"Transform service failed: {transform_response.text}"
            )
        logger.info("Data transformation completed")

        # Step 2: Load data
        logger.info("Starting data loading")
        load_response = requests.post(f"{LOAD_SERVICE}/load")
        if load_response.status_code != 200:
            raise HTTPException(
                status_code=load_response.status_code,
                detail=f"Load service failed: {load_response.text}"
            )
        logger.info("Data loading completed")

        # Read and return the final report
        results_dir = os.getenv("RESULTS_DIR", "/results")
        report_path = os.path.join(results_dir, "census_report.json")
        
        if not os.path.exists(report_path):
            raise HTTPException(
                status_code=500,
                detail="Report file not found after processing"
            )

        with open(report_path, "r") as f:
            report = json.load(f)

        return {
            "status": "success",
            "message": "Data processing completed successfully",
            "report": report
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)