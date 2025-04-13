FROM python:3.9-slim

WORKDIR /app
COPY scripts/load.py .
COPY scripts/database.py .
COPY docker/load/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "load:app", "--host", "0.0.0.0", "--port", "8000"]