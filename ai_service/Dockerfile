FROM python:3.11-slim

WORKDIR /app

# Install OpenCV system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ai_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_service /app/ai_service
COPY backend /app/backend

ENV PYTHONPATH=/app/ai_service:/app

EXPOSE 8001

CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
