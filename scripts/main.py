import logging
import os
import requests
from fastapi import FastAPI, HTTPException
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/run-pipeline")
async def run_pipeline():
    try:
        # Environment variables for service endpoints
        database_service = os.getenv("DATABASE_SERVICE", "http://database-service:8000")
        transform_service = os.getenv("TRANSFORM_SERVICE", "http://transform-service:8000")
        load_service = os.getenv("LOAD_SERVICE", "http://load-service:8000")

        # Validate URLs
        for service in [database_service, transform_service, load_service]:
            try:
                parsed = urlparse(service)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError(f"Invalid URL: {service}")
            except Exception as e:
                logger.error(f"Invalid service URL: {service}, error: {e}")
                raise HTTPException(status_code=500, detail=f"Invalid service URL: {service}")

        # Step 1: Connect to database
        logger.info("Connecting to database")
        db_response = requests.get(f"{database_service}/connect", timeout=10)
        if db_response.status_code != 200:
            raise Exception(f"Database connection failed: {db_response.text}")

        # Step 2: Transform data
        logger.info("Starting transformation")
        transform_response = requests.post(f"{transform_service}/transform", timeout=30)
        if transform_response.status_code != 200:
            raise Exception(f"Transformation failed: {transform_response.text}")

        # Step 3: Load data
        logger.info("Starting loading")
        load_response = requests.post(f"{load_service}/load", timeout=30)
        if load_response.status_code != 200:
            raise Exception(f"Loading failed: {load_response.text}")

        logger.info("ETL pipeline completed successfully")
        return {"status": "success", "message": "ETL pipeline completed"}
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)