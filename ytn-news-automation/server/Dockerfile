FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy config and environment files
COPY config/ /app/config/
# COPY .env /app/.env

# Copy server code
COPY server/ /app/server/

RUN pip install --no-cache-dir -r /app/server/requirements.txt

ENV FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID} \
    FIRESTORE_COLLECTION=news

                                                 ## Prefer ADC on Cloud Run; do not force GOOGLE_APPLICATION_CREDENTIALS

EXPOSE 8080

# Use Cloud Run-provided PORT if available
CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8080}"]





                               