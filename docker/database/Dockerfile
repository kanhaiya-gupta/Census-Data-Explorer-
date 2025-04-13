FROM python:3.9-slim

WORKDIR /app
COPY scripts/database.py .
COPY docker/database/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "database:app", "--host", "0.0.0.0", "--port", "8000"]